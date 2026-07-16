"""
Görevi        : Gerçek LoRa E22 900T22D telemetri sürücüsü (UART). TelemetryLink
                arayüzünü uygular; çerçeveleri seri port üzerinden gönderir.
Neden Gerekli : REQ-HW-003 (LoRa E22 gerçek UART). SIMULATION_ONLY'de mock kullanılır;
                FLIGHT/HIL profilinde gerçek sürücü gerekir.
İlişkiler     : StoreForwardBuffer/TelemetryService bu linki kullanır. Çerçeveleme
                ve store-and-forward donanımdan bağımsız olarak zaten uygulandı ve
                test edildi (framing.py, store_forward.py); burada YALNIZ fiziksel
                taşıma katmanı vardır.
DÜRÜSTLÜK NOTU: Seri G/Ç fiziksel donanım ve `pyserial` gerektirir. Bu ortamda
                gerçek cihaz YOKTUR; bu sürücünün seri okuma/yazma yolu donanımda
                doğrulanmalıdır (Aşama 5, saha). `pyserial` yoksa veya port
                açılamazsa sürücü sessizce ÇÖKMEZ; açık UNAVAILABLE döndürür.
Nasıl Test    : tests/test_driver_factory.py — pyserial/port yokken güvenli
                degrade (is_connected False, send UNAVAILABLE). Gerçek I/O saha
                testine tabidir (docs/FRR_TEST_PROCEDURES.md).
"""
from __future__ import annotations

from config.default import TelemetryConfig
from src.common.result import ErrorCode, Result


class RealLoraE22Link:
    """
    LoRa E22 900T22D UART sürücüsü. `open()` çağrılana kadar bağlı değildir.
    pyserial mevcut değilse veya port açılamazsa hata döndürür (güvenli degrade).
    """

    def __init__(self, port: str, config: TelemetryConfig) -> None:
        self._port = port
        self._cfg = config
        self._serial = None
        self._error: str | None = None

    def open(self) -> Result[None]:
        """Seri portu açar. pyserial/port yoksa açık hata döndürür (çökme yok)."""
        try:
            import serial  # type: ignore  # yalnız donanım profilinde kurulu
        except ImportError:
            self._error = "pyserial kurulu değil (donanım profili gerektirir)"
            return Result.err(ErrorCode.UNAVAILABLE, self._error)
        try:
            self._serial = serial.Serial(self._port, self._cfg.lora_baud, timeout=1)
        except Exception as exc:  # pyserial SerialException dahil
            self._error = f"LoRa port açılamadı ({self._port}): {exc}"
            return Result.err(ErrorCode.IO_ERROR, self._error)
        return Result.ok(None)

    def is_connected(self) -> bool:
        return self._serial is not None and getattr(self._serial, "is_open", False)

    def send(self, line: str) -> Result[None]:
        if not self.is_connected():
            return Result.err(ErrorCode.UNAVAILABLE,
                              self._error or "LoRa portu açık değil")
        try:
            self._serial.write((line + "\n").encode("utf-8"))
        except Exception as exc:
            return Result.err(ErrorCode.IO_ERROR, f"LoRa yazma hatası: {exc}")
        return Result.ok(None)

    def close(self) -> Result[None]:
        if self._serial is not None:
            try:
                self._serial.close()
            except Exception as exc:
                return Result.err(ErrorCode.IO_ERROR, f"LoRa kapatma hatası: {exc}")
        return Result.ok(None)
