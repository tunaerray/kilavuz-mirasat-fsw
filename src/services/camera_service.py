"""
Görevi        : Kamera servisi. Sistem açılışından itibaren kamerayı başlatır,
                her çevrimde fps'e göre kare yakalar, SD'ye kaydeder ve canlı akışa
                iletir; akış bağı kopuksa kare yine kaydedilir, yalnız akış düşer.
Neden Gerekli : Gereksinim-20/21/22 — kayıt tüm uçuş boyunca SD'ye, canlı akış
                sistem çalıştığı andan itibaren. Kayıt akış kopukluğunda dahi sürer.
İlişkiler     : HAL Camera + VideoStreamLink kullanır; ana döngü boot'ta start(),
                her çevrim tick(dt) çağırır. Video SD yolu ve çözünürlük config'ten.
Nasıl Test    : tests/test_camera.py — başlatma/çözünürlük, fps'e göre kare üretimi,
                akış kopukluğunda kaydın sürmesi, akış geri gelince devam.
"""
from __future__ import annotations

from dataclasses import dataclass

from config.default import VideoConfig
from src.common.result import Result
from src.hal.interfaces import Camera, VideoStreamLink


@dataclass
class VideoStatus:
    recording: bool
    streaming: bool
    frames_recorded: int
    frames_streamed: int
    frames_dropped_stream: int


class CameraService:
    """
    Kayıt her zaman önceliklidir (SD'ye kesintisiz); canlı akış en iyi çabadır.
    tick() zaman biriktirir ve fps'e göre gereken sayıda kare yakalar (deterministik).
    """

    def __init__(self, camera: Camera, stream: VideoStreamLink,
                 config: VideoConfig) -> None:
        self._cam = camera
        self._stream = stream
        self._cfg = config
        self._accum_s = 0.0
        self.frames_recorded = 0
        self.frames_streamed = 0
        self.frames_dropped_stream = 0

    def start(self) -> Result[None]:
        """Boot'ta kamerayı başlatır (çözünürlük doğrulaması dahil)."""
        return self._cam.start(self._cfg.width, self._cfg.height)

    def tick(self, dt: float) -> VideoStatus:
        """dt kadar süre için gereken kareleri yakalar, kaydeder ve akıtır."""
        if not self._cam.is_recording:
            return self._status()
        self._accum_s += max(0.0, dt)
        frame_interval = 1.0 / self._cfg.fps
        while self._accum_s >= frame_interval:
            self._accum_s -= frame_interval
            cap = self._cam.capture()
            if cap.is_err:
                break
            idx = cap.unwrap()
            self.frames_recorded += 1          # SD kaydı (her zaman)
            if self._stream.stream_frame(idx).is_ok:
                self.frames_streamed += 1
            else:
                self.frames_dropped_stream += 1  # akış kopuk; kayıt yine de yapıldı
        return self._status()

    def stop(self) -> Result[None]:
        return self._cam.stop()

    def _status(self) -> VideoStatus:
        return VideoStatus(
            recording=self._cam.is_recording,
            streaming=self._stream.is_connected(),
            frames_recorded=self.frames_recorded,
            frames_streamed=self.frames_streamed,
            frames_dropped_stream=self.frames_dropped_stream,
        )
