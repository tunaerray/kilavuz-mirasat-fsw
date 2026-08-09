"""
Görevi        : Telemetri paket üretici. Şartname §2.4'teki 17 alanı TAM sırayla,
                doğru birimlerle CSV satırı olarak üretir; ARAS hata kodunu üretir
                ve uydu statüsü (0..5) kodlarını tanımlar.
Neden Gerekli : Şartname §2.4 s.15-16 (17 alan), §2.2 s.13-14 (ARAS hata kodu).
                Sıra/başlık/birim yanlışsa %2 uçuş puanı kesintisi.
İlişkiler     : main döngüsü FlightControllerLink/sensör verileri + persistence
                paket no + state machine statü kodu ile TelemetryFields doldurur.
                TelemetryService bu satırı SD/CSV'ye yazar ve RF ile gönderir.
Nasıl Test    : tests/test_telemetry_packet.py (format/örnek paket),
                tests/test_error_code.py (ARAS bitleri).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum


class SatelliteStatus(IntEnum):
    """
    UYDU STATÜSÜ kodları — Şartname §2.4 s.16 (BAĞLAYICI).
    CONFLICT-002: PDR s.62'de 2/3 ters; ŞARTNAME esas alınmıştır.
    """

    READY = 0            # Uçuşa Hazır
    ASCENT = 1           # Yükselme
    CARRIER_DESCENT = 2  # Model Uydu İniş
    SEPARATION = 3       # Ayrılma
    PAYLOAD_DESCENT = 4  # Görev Yükü İniş
    RECOVERY = 5         # Kurtarma (yere temas)


@dataclass(frozen=True)
class ArasInputs:
    """ARAS hata kodu bit kararları için gerekli girdiler (Şartname §2.2)."""

    descent_speed_mps: float          # görev yükü iniş hızı
    speed_check_active: bool          # yalnız GY iniş fazında 8-10 denetlenir
    gps_valid: bool                   # konum verisi alınıyor mu
    separation_done: bool             # taşıyıcıdan ayrıldı mı
    apam_active: bool                 # APAM aktif mi
    target_speed_min: float = 8.0
    target_speed_max: float = 10.0


def compute_error_code(inp: ArasInputs, digits: int = 4) -> str:
    """
    ARAS hata kodunu üretir — Şartname §2.2 s.13-14 (DOĞRULANMIŞ):
      Bit-1: iniş hızı 8-10 m/s DIŞINDA → 1
      Bit-2: konum verisi ALINAMIYOR → 1
      Bit-3: taşıyıcıdan AYRILMADI → 1
      Bit-4: APAM AKTİF → 1
    Bit sırası soldan sağa Bit-1..Bit-4. CONFLICT-003: `digits` config'ten gelir
    (varsayılan 4); 5 haneye kadar sol sıfır dolgu yapılır.
    """
    # Bit-1: hız denetimi yalnız aktifken (GY aktif iniş) anlamlı; değilse 0.
    if inp.speed_check_active:
        bit1 = 0 if inp.target_speed_min <= inp.descent_speed_mps <= inp.target_speed_max else 1
    else:
        bit1 = 0
    bit2 = 0 if inp.gps_valid else 1
    bit3 = 0 if inp.separation_done else 1
    bit4 = 1 if inp.apam_active else 0

    core = f"{bit1}{bit2}{bit3}{bit4}"
    if digits < len(core):
        raise ValueError(f"error_code_digits ({digits}) < tanımlı bit sayısı (4)")
    return core.rjust(digits, "0")


# Telemetri alan başlıkları ve birimleri (Şartname §2.4 — TAM SIRA).
FIELD_HEADERS = [
    "PAKET_NUMARASI", "UYDU_STATUSU", "HATA_KODU", "GONDERME_SAATI",
    "BASINC", "YUKSEKLIK", "INIS_HIZI", "SICAKLIK", "PIL_GERILIMI",
    "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE",
    "PITCH", "ROLL", "YAW", "RHRHRH", "TAKIM_NO",
]
FIELD_UNITS = [
    "-", "-", "-", "GG/AA/YYYY SS:DD:ss",
    "Pa", "m", "m/s", "C", "V",
    "derece", "derece", "m",
    "derece", "derece", "derece", "-", "-",
]
TIME_FORMAT = "%d/%m/%Y %H:%M:%S"


@dataclass(frozen=True)
class TelemetryFields:
    """Bir telemetri paketinin 17 alanı (ham değerler)."""

    packet_number: int
    status: SatelliteStatus
    error_code: str
    send_time: datetime
    pressure_pa: float
    altitude_m: float
    descent_speed_mps: float
    temperature_c: float
    battery_v: float
    gps_lat: float
    gps_lon: float
    gps_alt_m: float
    pitch_deg: float
    roll_deg: float
    yaw_deg: float
    rhrhrh: str
    team_number: int


class TelemetryPacketBuilder:
    """17 alanı şartname sırasına göre CSV satırına dönüştürür."""

    def __init__(self, decimal_places: int = 1, separator: str = ",") -> None:
        self._dp = decimal_places
        self._sep = separator

    def _f(self, value: float) -> str:
        return f"{value:.{self._dp}f}"

    def csv_header(self) -> str:
        return self._sep.join(FIELD_HEADERS)

    def csv_units(self) -> str:
        return self._sep.join(FIELD_UNITS)

    def build(self, f: TelemetryFields) -> str:
        """Şartname §2.4 sırasıyla tek bir telemetri satırı (CSV) üretir."""
        # GPS lat/lon 6 ondalık (~11 cm). 4 ondalık ~11 m olur ve kurtarma icin yetersiz.
        fields = [
            str(f.packet_number),
            str(int(f.status)),
            f.error_code,
            f.send_time.strftime(TIME_FORMAT),
            self._f(f.pressure_pa),
            self._f(f.altitude_m),
            self._f(f.descent_speed_mps),
            self._f(f.temperature_c),
            self._f(f.battery_v),
            f"{f.gps_lat:.6f}",
            f"{f.gps_lon:.6f}",
            self._f(f.gps_alt_m),
            self._f(f.pitch_deg),
            self._f(f.roll_deg),
            self._f(f.yaw_deg),
            f.rhrhrh if f.rhrhrh else "------",
            str(f.team_number),
        ]
        if len(fields) != 17:
            raise AssertionError("Telemetri paketi 17 alan olmalıdır")
        return self._sep.join(fields)
