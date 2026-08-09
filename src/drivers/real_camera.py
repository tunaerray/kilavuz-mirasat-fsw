"""
Görevi        : Gerçek kamera sürücüsü. `rpicam-vid`'i alt süreç olarak yönetir;
                görüntüyü aynı anda SD karta kaydeder ve TCP üzerinden yayınlar.
                Camera ve VideoStreamLink arayüzlerini uygular.
Neden Gerekli : REQ-TLM-010 / Gereksinim-20,21,22. SIMULATION_ONLY'de MockCamera
                kullanılır; FLIGHT/HIL profilinde gerçek kamera gerekir.
İlişkiler     : CameraService bu sürücüyü `start/capture/stop` ile sürer.
                Yer istasyonu yayına `tcp://<pi-ip>:8554` ile bağlanır.

SAHA DOĞRULAMASI (2026-08-09, RPi 5 + Camera Module 2)
------------------------------------------------------
1. Pi 5'te DONANIMSAL H.264 KODLAYICI YOK. BCM2712'de eski kodek blokları
   kaldırıldı; kodlama libav ile YAZILIMDA yapılır. 720p25 sorunsuz çalışır
   ama CPU ve dolayısıyla güç tüketir. Güç bütçesinde hesaba katılmalı.

2. HAM H.264 AKIŞI VLC'DE AÇILMIYOR. Modern VLC sürümleri kapsayıcısız H.264
   akışını düzgün oynatmıyor. MPEG-TS kapsayıcısı şart (--libav-format mpegts).

3. CAM0 PORTU TIMEOUT VERDİ, CAM1 ÇALIŞTI. Aynı kablo ve kamerayla CAM/DISP0'da
   "Camera frontend has timed out" alındı, CAM/DISP1'de sorunsuz çalıştı.
   Sınırda bir bağlantı olabilir; titreşim testi öncesi tekrar değerlendirilmeli.

4. Pi 5'in kamera konnektörü 22 pin; Camera Module 2 kablosu 15 pin.
   22->15 pin adaptör kablo gerekir, Pi 5 ile birlikte gelmez.

DÜRÜSTLÜK NOTU: `rpicam-vid` yoksa veya süreç başlatılamazsa sürücü sessizce
                ÇÖKMEZ; açık UNAVAILABLE/IO_ERROR döndürür. Kare sayısı gerçek
                kodlayıcıdan değil, geçen süre × fps ile KESTİRİLİR — rpicam-vid
                kare başına geri bildirim vermez. Süreç canlılığı her `capture()`
                çağrısında denetlenir, dolayısıyla kamera ölürse fark edilir.
"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import time

from config.default import PathsConfig, VideoConfig
from src.common.result import ErrorCode, Result


# TODO(config): Bu değerler config/default.py VideoConfig'e taşınmalı.
YAYIN_PORTU = 8554
YAYIN_ADRESI = "0.0.0.0"

# Süreç kapanırken SIGTERM'e yanıt için tanınan süre; sonrasında SIGKILL.
KAPANMA_TOLERANSI_S = 3.0


class RpicamVidCamera:
    """
    `rpicam-vid` tabanlı kamera sürücüsü.

    Tek bir boru hattı hem SD kaydını hem canlı yayını besler:

        rpicam-vid -o -  |  tee <sd_dosyasi>  |  socat - TCP-LISTEN:<port>

    Kayıt yayından bağımsızdır: yer istasyonu bağlantısı kopsa bile SD'ye
    yazma sürer (Gereksinim-20). Bu, şartnamenin istediği davranıştır.
    """

    def __init__(self, video: VideoConfig, paths: PathsConfig) -> None:
        self._video = video
        self._paths = paths
        self._proc: subprocess.Popen | None = None
        self._baslangic: float = 0.0
        self._error: str | None = None

    # ------------------------------------------------------------------
    # Camera arayüzü
    # ------------------------------------------------------------------

    def start(self, width: int, height: int) -> Result[None]:
        if self.is_recording:
            return Result.ok(None)

        eksik = [a for a in ("rpicam-vid", "tee", "socat") if shutil.which(a) is None]
        if eksik:
            self._error = (f"Gerekli araçlar bulunamadı: {', '.join(eksik)}. "
                           f"Kurulum: sudo apt install socat")
            return Result.err(ErrorCode.UNAVAILABLE, self._error)

        # SD kaydı MPEG-TS akışıdır; uzantı .ts olmalı (config .h264 diyorsa düzelt).
        sd_yolu = self._paths.video_sd
        if sd_yolu.endswith(".h264"):
            sd_yolu = sd_yolu[:-5] + ".ts"

        try:
            os.makedirs(os.path.dirname(sd_yolu) or ".", exist_ok=True)
        except OSError as exc:
            self._error = f"Video dizini oluşturulamadı: {exc}"
            return Result.err(ErrorCode.IO_ERROR, self._error)

        komut = (
            f"rpicam-vid -t 0 -n "
            f"--width {width} --height {height} "
            f"--framerate {self._video.fps} "
            f"--codec libav --libav-format mpegts -o - "
            f"| tee {sd_yolu} "
            f"| socat - TCP-LISTEN:{YAYIN_PORTU},reuseaddr,fork"
        )

        try:
            # start_new_session: alt süreçler kendi grup kimliğini alır.
            # Boru hattındaki üç süreci birden öldürebilmek için gerekli;
            # yalnız kabuk öldürülürse rpicam-vid arkada kalır ve kamerayı
            # kilitler, sonraki başlatma "device busy" ile başarısız olur.
            self._proc = subprocess.Popen(
                komut,
                shell=True,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            self._error = f"Kamera süreci başlatılamadı: {exc}"
            self._proc = None
            return Result.err(ErrorCode.IO_ERROR, self._error)

        # Kamera açılışı ~1 sn sürer; hemen ölürse bunu şimdi görelim.
        time.sleep(1.0)
        if self._proc.poll() is not None:
            self._error = ("Kamera süreci hemen sonlandı — kablo, CAM portu veya "
                           "başka bir sürecin kamerayı tutması olabilir")
            self._proc = None
            return Result.err(ErrorCode.IO_ERROR, self._error)

        self._baslangic = time.monotonic()
        return Result.ok(None)

    def capture(self) -> Result[int]:
        """
        Güncel kare indeksini döndürür.

        rpicam-vid kare başına geri bildirim vermediği için indeks geçen
        süreden kestirilir. Asıl değeri süreç canlılığını denetlemesidir:
        kamera ölürse bir sonraki çağrı hata döndürür ve CameraService bunu
        telemetriye yansıtabilir.
        """
        if not self.is_recording:
            return Result.err(ErrorCode.UNAVAILABLE,
                              self._error or "Kamera çalışmıyor")

        gecen = time.monotonic() - self._baslangic
        return Result.ok(int(gecen * self._video.fps))

    def stop(self) -> Result[None]:
        if self._proc is None:
            return Result.ok(None)

        proc, self._proc = self._proc, None

        try:
            grup = os.getpgid(proc.pid)
            os.killpg(grup, signal.SIGTERM)
            try:
                proc.wait(timeout=KAPANMA_TOLERANSI_S)
            except subprocess.TimeoutExpired:
                # SIGTERM'e yanıt vermedi; kamerayı serbest bırakmak için zorla.
                os.killpg(grup, signal.SIGKILL)
                proc.wait(timeout=2.0)
        except ProcessLookupError:
            pass    # zaten ölmüş
        except Exception as exc:
            return Result.err(ErrorCode.IO_ERROR, f"Kamera durdurulamadı: {exc}")

        return Result.ok(None)

    @property
    def is_recording(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    @property
    def resolution(self) -> tuple:
        return (self._video.width, self._video.height)


class RpicamVidStreamLink:
    """
    VideoStreamLink arayüzü. Yayın, kamera boru hattının kendisi tarafından
    yapıldığı için burada ayrı bir aktarım yoktur; bu sınıf yalnız yayının
    ayakta olup olmadığını bildirir.
    """

    def __init__(self, camera: RpicamVidCamera) -> None:
        self._camera = camera

    def is_connected(self) -> bool:
        return self._camera.is_recording

    def stream_frame(self, frame_index: int) -> Result[None]:
        if not self._camera.is_recording:
            return Result.err(ErrorCode.UNAVAILABLE, "Video yayını kapalı")
        return Result.ok(None)
