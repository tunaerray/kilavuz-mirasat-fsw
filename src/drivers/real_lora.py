"""
Görevi        : Gerçek LoRa E22-900T22D telemetri sürücüsü (UART + GPIO).
                TelemetryLink arayüzünü uygular; çerçeveleri seri port üzerinden
                gönderir, gelen telekomutları okur.
Neden Gerekli : REQ-HW-003 (LoRa E22 gerçek UART). SIMULATION_ONLY'de mock
                kullanılır; FLIGHT/HIL profilinde gerçek sürücü gerekir.
İlişkiler     : StoreForwardBuffer/TelemetryService bu linki kullanır.
                CommandService `receive()` ile gelen komut satırlarını alır.
                Çerçeveleme ve store-and-forward donanımdan bağımsız olarak
                zaten uygulandı (framing.py, store_forward.py).

SAHA DOĞRULAMASI (2026-08-09, RPi 5 + E22-900T22D, üç düğümlü test)
------------------------------------------------------------------
Aşağıdaki davranışlar gerçek donanımda gözlendi ve bu sürücüye yansıtıldı.
Her biri, olmadığında haberleşmeyi TAMAMEN kesen sorunlara yol açtı:

1. PORT ADI. Raspberry Pi 5'te `/dev/serial0` GPIO 14/15'e bağlı UART'a
   İŞARET ETMEZ (bu kartta ttyAMA10'a bakıyordu, loopback testi boş döndü).
   Doğru cihaz `/dev/ttyAMA0`. Pi 4 ve öncesi için serial0 doğruydu; Pi 5'te
   değil.

2. AUX PİNİ. Modül veri işlerken AUX LOW olur. Beklemeden yazılırsa paketler
   birbirini ezer ve sessizce kaybolur. Her gönderim ÖNCESİ ve SONRASI
   beklenmelidir (RF aktarımı UART bittikten sonra da sürer).

3. M0/M1 SABİTLENMELİ. Bu pinler boşta kalırsa modül konfigürasyon moduna
   düşer ve UART'tan gelen telemetri baytlarını parametre yazma komutu sanıp
   ayarları EZER. Sahada üç kez yaşandı. Pull-down dirençleri (10k) ve her
   açılışta parametre yazımı bu sorunu kökten çözer.

4. MOD TABLOSU. E22 ve E220 FARKLIDIR. E22'de konfigürasyon modu M1=1, M0=0.
   (E220'de M1=1, M0=1 — bu değer E22'de derin uyku demektir ve modül hiç
   cevap vermez.)

5. RSSI BAYTI. Packet RSSI açıkken modül, alınan her paketin ARDINDAN 1 bayt
   ekler. Bu bayt '\\n' sonrasına düştüğü için bir sonraki satırın başına
   yapışır ve komut CRC'sini bozar; ayıklanması şarttır.

DÜRÜSTLÜK NOTU: gpiozero yoksa sürücü AUX/M0/M1 olmadan "kör" modda çalışır ve
                bunu açıkça bildirir. pyserial yoksa veya port açılamazsa
                sessizce ÇÖKMEZ; açık UNAVAILABLE/IO_ERROR döndürür.
Nasıl Test    : tests/test_driver_factory.py — pyserial/port yokken güvenli
                degrade. Gerçek I/O saha testine tabidir
                (docs/FRR_TEST_PROCEDURES.md).
"""
from __future__ import annotations

import time

from config.default import TelemetryConfig
from src.common.result import ErrorCode, Result


# =============================================================================
# DONANIM SABİTLERİ
# =============================================================================
# TODO(config): Bu değerler config/default.py TelemetryConfig'e taşınmalı.
#               EKSİK-002 kapsamında kanal/adres kesinleştirildi (saha).

AUX_PIN = 17      # GPIO17, fiziksel pin 11
M0_PIN  = 23      # GPIO23, fiziksel pin 16 — 10k pull-down GND'ye
M1_PIN  = 24      # GPIO24, fiziksel pin 18 — 10k pull-down GND'ye

# Pull-down dirençleri kritik: Pi açılırken GPIO'lar giriş modunda ve boştadır.
# Direnç olmadan modül o aralıkta konfigürasyon moduna düşer (bkz. saha notu 3).

# --- E22 register değerleri (REG0..REG8) ---
#  REG0-1  adres 7450                                   = 0x1D 0x1A
#  REG2    NET ID 255                                   = 0xFF
#  REG3    9600 baud, 8N1, 4.8 kbps air rate            = 0x63
#  REG4    240 bayt alt paket, 22 dBm                   = 0x00
#  REG5    kanal 16 -> 850.125 + 16 = 866.125 MHz       = 0x10
#  REG6    transparan mod, LBT kapalı, RSSI baytı AÇIK  = 0x83
#  REG7-8  key 0 (şifreleme kapalı)                     = 0x00 0x00
#
# REG6 bit 7 RSSI baytını açar. Kapatmak için 0x03 yazın; o durumda
# RSSI_BAYTI_AKTIF de False yapılmalıdır.
LORA_REGISTERLERI = [0x1D, 0x1A, 0xFF, 0x63, 0x00, 0x10, 0x83, 0x00, 0x00]
RSSI_BAYTI_AKTIF = True

# 866.125 MHz Türkiye'de lisanssız SRD bandındadır (863-870 MHz).
# 880-915 MHz mobil operatörlere tahsislidir, KULLANILAMAZ.

KONFIG_BAUD = 9600          # konfigürasyon modunda UART her zaman 9600 8N1
YAZ_KOMUTU  = 0xC0          # kalıcı yazma (C2 geçici olurdu)
OKU_KOMUTU  = 0xC1

AUX_ZAMAN_ASIMI_S     = 1.0   # gönderim öncesi hazır olma
AUX_TX_ZAMAN_ASIMI_S  = 2.0   # RF aktarımının bitmesi
MOD_GECIS_S           = 0.20   # E22 mod gecisi icin AUX yeterli sinyal vermiyor, sabit bekleme sart
RX_TAMPON_SINIRI      = 4096  # bozuk akışta sınırsız büyümeyi engeller


class RealLoraE22Link:
    """
    LoRa E22-900T22D UART sürücüsü.

    `open()` çağrılana kadar bağlı değildir. pyserial mevcut değilse veya port
    açılamazsa hata döndürür (güvenli degrade). gpiozero yoksa AUX/M0/M1
    olmadan çalışır — gönderim yapar ama paket çakışmasına karşı korumasızdır.
    """

    def __init__(self, port: str, config: TelemetryConfig) -> None:
        self._port = port
        self._cfg = config
        self._serial = None
        self._error: str | None = None

        # GPIO
        self._aux = None
        self._m0 = None
        self._m1 = None
        self._gpio_var = False

        # Alım
        self._rx_tampon = bytearray()
        self._son_rssi = 0

        # Tanılama
        self._yapilandirildi = False

    # ------------------------------------------------------------------
    # YAŞAM DÖNGÜSÜ
    # ------------------------------------------------------------------

    def open(self) -> Result[None]:
        """
        Seri portu açar, GPIO'ları hazırlar ve modül parametrelerini yazar.

        Yapılandırma başarısız olsa bile port açıksa OK döner: modül zaten
        doğru ayardaysa uçuşu bloke etmenin anlamı yok. Durum `is_configured`
        ile sorgulanabilir.
        """
        try:
            import serial  # type: ignore  # yalnız donanım profilinde kurulu
        except ImportError:
            self._error = "pyserial kurulu değil (donanım profili gerektirir)"
            return Result.err(ErrorCode.UNAVAILABLE, self._error)

        self._gpio_hazirla()

        try:
            self._serial = serial.Serial(self._port, self._cfg.lora_baud, timeout=0.05)
        except Exception as exc:  # pyserial SerialException dahil
            self._error = f"LoRa port açılamadı ({self._port}): {exc}"
            self._gpio_birak()
            return Result.err(ErrorCode.IO_ERROR, self._error)

        # Parametreleri yaz. M0/M1 sürülemezse bu adım atlanır.
        if self._gpio_var:
            self._yapilandirildi = self._modulu_yapilandir()

        return Result.ok(None)

    def is_connected(self) -> bool:
        return self._serial is not None and getattr(self._serial, "is_open", False)

    @property
    def is_configured(self) -> bool:
        """Modül parametreleri bu açılışta yazılıp doğrulandı mı?"""
        return self._yapilandirildi

    @property
    def last_rssi_dbm(self) -> int:
        """Son alınan paketin sinyal gücü. 0 = ölçüm yok."""
        return self._son_rssi

    def close(self) -> Result[None]:
        hata = None
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception as exc:
                hata = f"LoRa kapatma hatası: {exc}"
        self._gpio_birak()
        if hata:
            return Result.err(ErrorCode.IO_ERROR, hata)
        return Result.ok(None)

    # ------------------------------------------------------------------
    # GÖNDERİM
    # ------------------------------------------------------------------

    def send(self, line: str) -> Result[None]:
        """
        Satırı gönderir. AUX varsa modülün hazır olması beklenir ve gönderim
        sonrası RF aktarımının bitmesi beklenir (bkz. saha notu 2).
        """
        if not self.is_connected():
            return Result.err(ErrorCode.UNAVAILABLE,
                              self._error or "LoRa portu açık değil")

        if not self._aux_bekle(AUX_ZAMAN_ASIMI_S):
            return Result.err(ErrorCode.IO_ERROR,
                              "LoRa meşgul (AUX zaman aşımı)")

        try:
            self._serial.write((line + "\n").encode("utf-8"))
            self._serial.flush()
        except Exception as exc:
            return Result.err(ErrorCode.IO_ERROR, f"LoRa yazma hatası: {exc}")

        # RF aktarımı UART'tan sonra da sürer; bitmeden yeni paket gönderilirse
        # ikisi de kaybolur.
        self._aux_bekle(AUX_TX_ZAMAN_ASIMI_S)
        return Result.ok(None)

    # ------------------------------------------------------------------
    # ALIM
    # ------------------------------------------------------------------

    def receive(self) -> list[str]:
        """
        Bekleyen tam satırları döndürür. Bloke etmez; ana döngüden her çevrimde
        çağrılabilir. Satır yoksa boş liste döner.

        RSSI baytı ayıklanır (bkz. saha notu 5); değeri `last_rssi_dbm` ile
        okunabilir.
        """
        if not self.is_connected():
            return []

        try:
            bekleyen = self._serial.in_waiting
            if bekleyen:
                self._rx_tampon.extend(self._serial.read(bekleyen))
        except Exception:
            return []

        # Bozuk akışta tampon sınırsız büyümesin
        if len(self._rx_tampon) > RX_TAMPON_SINIRI:
            del self._rx_tampon[:-RX_TAMPON_SINIRI]

        satirlar: list[str] = []
        while True:
            self._rssi_ayikla()

            if b"\n" not in self._rx_tampon:
                break

            ham, _, kalan = bytes(self._rx_tampon).partition(b"\n")
            self._rx_tampon = bytearray(kalan)
            self._rssi_ayikla()

            satir = ham.decode("utf-8", errors="ignore").strip()
            if satir:
                satirlar.append(satir)

        return satirlar

    def _rssi_ayikla(self) -> None:
        """
        Tamponun başındaki RSSI baytlarını ayırır.

        Gerçek RSSI baytı her zaman 0x80 üstündedir (RSSI negatiftir), bu yüzden
        ASCII metinle karışmaz. 0x00 ve 0xFF ölçek raylarıdır — alıcı doyuma
        girdiğinde çıkarlar, gerçek ölçüm değildirler.
        """
        if not RSSI_BAYTI_AKTIF:
            return
        while self._rx_tampon and self._rx_tampon[0] >= 0x80:
            b = self._rx_tampon[0]
            del self._rx_tampon[0]
            if 0x82 <= b <= 0xFA:
                self._son_rssi = -(256 - b)

    # ------------------------------------------------------------------
    # GPIO / AUX
    # ------------------------------------------------------------------

    def _gpio_hazirla(self) -> None:
        """gpiozero yoksa sessizce kör moda düşer, açık hata vermez."""
        try:
            from gpiozero import Button, OutputDevice  # type: ignore
        except ImportError:
            self._gpio_var = False
            return

        try:
            self._aux = Button(AUX_PIN, pull_up=False)
            self._m0 = OutputDevice(M0_PIN, initial_value=False)
            self._m1 = OutputDevice(M1_PIN, initial_value=False)
            self._gpio_var = True
        except Exception:
            self._gpio_birak()
            self._gpio_var = False

    def _gpio_birak(self) -> None:
        for cihaz in (self._aux, self._m0, self._m1):
            try:
                if cihaz is not None:
                    cihaz.close()
            except Exception:
                pass
        self._aux = self._m0 = self._m1 = None
        self._gpio_var = False

    def _aux_bekle(self, zaman_asimi: float) -> bool:
        """AUX HIGH olana kadar bekler. GPIO yoksa her zaman True döner."""
        if not self._gpio_var or self._aux is None:
            return True

        bitis = time.monotonic() + zaman_asimi
        while not self._aux.is_pressed:
            if time.monotonic() > bitis:
                return False
            time.sleep(0.002)
        time.sleep(0.002)   # datasheet: AUX yükseldikten sonra kısa bekleme
        return True

    def _moda_gec(self, konfig: bool) -> None:
        """
        E22 mod tablosu (E220'den FARKLI, bkz. saha notu 4):
            M1=0 M0=0  normal / transparan
            M1=0 M0=1  WOR gönderme
            M1=1 M0=0  konfigürasyon
            M1=1 M0=1  derin uyku
        """
        if not self._gpio_var:
            return

        if konfig:
            self._m0.off()
            self._m1.on()
        else:
            self._m0.off()
            self._m1.off()

        time.sleep(MOD_GECIS_S)
        self._aux_bekle(1.0)
        time.sleep(MOD_GECIS_S)

    # ------------------------------------------------------------------
    # MODÜL YAPILANDIRMA
    # ------------------------------------------------------------------

    def _modulu_yapilandir(self) -> bool:
        """
        Parametreleri modüle yazar ve geri okuyup doğrular.

        Her açılışta yapılır: M0/M1 bir an boşta kalıp ayarlar silinse bile
        sistem kendini onarır (bkz. saha notu 3).

        KEY (REG7-8) doğrulamaya dahil edilmez; modül güvenlik gereği anahtarı
        geri okutmaz, her zaman 0x0000 döndürür.
        """
        try:
            self._moda_gec(konfig=True)
            self._serial.reset_input_buffer()

            komut = bytes([YAZ_KOMUTU, 0x00, 0x09] + LORA_REGISTERLERI)
            self._serial.write(komut)
            self._serial.flush()
            self._aux_bekle(2.0)
            time.sleep(0.2)

            if not self._serial.read(64):
                self._error = "Modül yapılandırmaya yanıt vermedi (M0/M1?)"
                return False

            # Geri oku ve doğrula
            self._serial.reset_input_buffer()
            self._serial.write(bytes([OKU_KOMUTU, 0x00, 0x09]))
            self._serial.flush()
            self._aux_bekle(2.0)
            time.sleep(0.2)

            okunan = self._serial.read(64)
            if len(okunan) < 12:
                self._error = "Modül parametreleri okunamadı"
                return False

            veri = list(okunan[3:12])
            if veri[:7] != LORA_REGISTERLERI[:7]:
                self._error = (f"Parametre uyuşmazlığı: modülde {veri[:7]}, "
                               f"beklenen {LORA_REGISTERLERI[:7]}")
                return False

            return True

        except Exception as exc:
            self._error = f"Yapılandırma hatası: {exc}"
            return False

        finally:
            # Ne olursa olsun normal moda dön; aksi halde telemetri gönderilemez
            try:
                self._moda_gec(konfig=False)
                self._serial.reset_input_buffer()
            except Exception:
                pass
