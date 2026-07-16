"""
Görevi        : Telemetri çerçeveleme ve CRC bütünlük katmanı. RF üzerinden
                gönderilen her telemetri satırına CRC16-CCITT sağlaması ekler ve
                alıcı tarafta doğrular.
Neden Gerekli : REQ-TLM-008 + PDR test planı (CRC kontrolü). Gürültülü/karıştırmalı
                RF ortamında bozuk paketlerin tespiti gerekir (Z.I.R.H ile birlikte).
İlişkiler     : TelemetryService/StoreForwardBuffer gönderim öncesi build_frame ile
                çerçeveler; yer istasyonu parse_frame ile doğrular. Şartname §2.4
                telemetri satırı (payload) değiştirilmeden korunur; CRC ayrı bir sonek.
Nasıl Test    : tests/test_framing.py — bilinen CRC, round-trip, bozulma tespiti,
                biçim hataları, payload'ın korunması.
"""
from __future__ import annotations

from src.common.result import ErrorCode, Result

# Çerçeve biçimi:  <payload>*<CRC16 4-hane HEX>
# '*' ayracı şartname örnek paketindeki '#####' checksum alanıyla karışmaması için
# yalnız RF taşıma katmanında kullanılır (CSV/SD payload'ı etkilenmez).
FRAME_SEPARATOR = "*"


def crc16_ccitt(data: str, poly: int = 0x1021, init: int = 0xFFFF) -> int:
    """
    CRC16-CCITT (XModem varyantı, init=0xFFFF). Metni UTF-8 bayta çevirip hesaplar.
    Deterministik ve bağımlılıksız (stdlib bile gerekmez).
    """
    crc = init
    for byte in data.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ poly) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc & 0xFFFF


def build_frame(payload: str) -> str:
    """Payload'a CRC ekleyip RF çerçevesi üretir: '<payload>*<CRC hex>'."""
    crc = crc16_ccitt(payload)
    return f"{payload}{FRAME_SEPARATOR}{crc:04X}"


def parse_frame(frame: str) -> Result[str]:
    """
    Çerçeveyi ayrıştırır ve CRC'yi doğrular. Başarılıysa payload'ı döndürür;
    CRC uyuşmazsa/biçim bozuksa açık hata (sessiz geçiş yok).
    """
    if not isinstance(frame, str) or FRAME_SEPARATOR not in frame:
        return Result.err(ErrorCode.INVALID_DATA, "çerçeve ayracı yok")
    payload, _, crc_str = frame.rpartition(FRAME_SEPARATOR)
    if len(crc_str) != 4:
        return Result.err(ErrorCode.INVALID_DATA, f"CRC alanı hatalı: {crc_str!r}")
    try:
        received = int(crc_str, 16)
    except ValueError:
        return Result.err(ErrorCode.INVALID_DATA, f"CRC hex değil: {crc_str!r}")
    expected = crc16_ccitt(payload)
    if received != expected:
        return Result.err(ErrorCode.INVALID_DATA,
                          f"CRC uyuşmazlığı: beklenen {expected:04X}, gelen {crc_str}")
    return Result.ok(payload)
