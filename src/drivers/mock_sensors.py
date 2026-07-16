"""
Görevi        : Mock sensör sürücüleri (barometre, IMU, GPS, batarya, telemetri
                linki). FlightProfile'dan beslenir; nominal/aykırı/timeout modları
                üretebilir. SIMULATION_ONLY'de gerçek donanıma erişmez.
Neden Gerekli : ANA_PROMPT F.7 — mock sensörler nominal, aykırı ve zaman aşımı
                verisi üretebilmeli. Sağlık izleme ve failsafe bu modlarla test
                edilir.
İlişkiler     : HAL arayüzlerini (Barometer/Imu/Gps/Battery/TelemetryLink) uygular;
                app döngüsü okur; health/failsafe tüketir.
Nasıl Test    : tests/test_mock_sensors.py — mod değişimi, timeout, aykırı değer.
"""
from __future__ import annotations

import math
from enum import Enum

from src.common.clock import Clock
from src.common.result import ErrorCode, Result
from src.drivers.flight_profile import FlightProfile
from src.hal.interfaces import (
    BarometerReading,
    BatteryReading,
    GpsReading,
    ImuReading,
)

# FRR §4.2 titreşim testi analoğu: yüksek frekanslı (150–200 Hz) titreşim, döngü
# örnekleme hızında aliaslanır; deterministik sinüs ile bounded gürültü modellenir.
_VIBRATION_FREQ_HZ = 175.0


class SensorMode(Enum):
    NOMINAL = "NOMINAL"
    OUTLIER = "OUTLIER"     # fiziksel olarak imkânsız/aykırı değer
    TIMEOUT = "TIMEOUT"     # sensör yanıt vermiyor


class _Base:
    """Ortak mod yönetimi ve zaman/görev-zamanı erişimi."""

    def __init__(self, clock: Clock, profile: FlightProfile,
                 mission_time) -> None:
        self._clock = clock
        self._profile = profile
        self._mission_time = mission_time   # çağrılabilir: () -> float
        self.mode = SensorMode.NOMINAL
        self.vibration = 0.0                 # titreşim şiddeti ölçeği (0 = yok)

    def _truth(self):
        return self._profile.sample(self._mission_time())

    def _vib(self, amplitude: float, phase: float = 0.0) -> float:
        """Deterministik titreşim gürültüsü (bounded, sıfır ortalamalı)."""
        if self.vibration <= 0.0:
            return 0.0
        t = self._mission_time()
        return (self.vibration * amplitude
                * math.sin(2.0 * math.pi * _VIBRATION_FREQ_HZ * t + phase))


class MockBarometer(_Base):
    def read(self) -> Result[BarometerReading]:
        if self.mode is SensorMode.TIMEOUT:
            return Result.err(ErrorCode.TIMEOUT, "barometre yanıt vermedi")
        tr = self._truth()
        # Titreşim → basınçta ±~60 Pa gürültü (~5 m irtifa dalgalanması).
        pressure = tr.pressure_pa + self._vib(60.0)
        temp = tr.temperature_c
        if self.mode is SensorMode.OUTLIER:
            pressure = -1.0            # imkânsız basınç
        return Result.ok(BarometerReading(
            pressure_pa=pressure, temperature_c=temp,
            timestamp_s=self._clock.now_monotonic()))


class MockImu(_Base):
    def read(self) -> Result[ImuReading]:
        if self.mode is SensorMode.TIMEOUT:
            return Result.err(ErrorCode.TIMEOUT, "IMU yanıt vermedi")
        tr = self._truth()
        # Titreşim → açılarda ±~3° gürültü.
        pitch = tr.pitch_deg + self._vib(3.0)
        roll = tr.roll_deg + self._vib(3.0, phase=1.0)
        yaw = tr.yaw_deg + self._vib(3.0, phase=2.0)
        if self.mode is SensorMode.OUTLIER:
            pitch = 9999.0             # imkânsız açı
        return Result.ok(ImuReading(
            pitch_deg=pitch, roll_deg=roll, yaw_deg=yaw,
            accel_z_mps2=9.81, timestamp_s=self._clock.now_monotonic()))


class MockGps(_Base):
    def read(self) -> Result[GpsReading]:
        if self.mode is SensorMode.TIMEOUT:
            return Result.err(ErrorCode.TIMEOUT, "GPS yanıt vermedi")
        tr = self._truth()
        sats = 8                       # ASSUMPTION-007: nominal 6+ kilit
        fix = True
        if self.mode is SensorMode.OUTLIER:
            sats = 0
            fix = False                # konum kilidi yok → ARAS Bit-2
        return Result.ok(GpsReading(
            latitude=tr.latitude, longitude=tr.longitude,
            altitude_m=tr.gps_altitude_m, satellites=sats, fix_valid=fix,
            timestamp_s=self._clock.now_monotonic()))


class MockBattery(_Base):
    def __init__(self, clock, profile, mission_time,
                 start_voltage_v: float = 16.4) -> None:
        super().__init__(clock, profile, mission_time)
        self._v = start_voltage_v      # 4S dolu ~16.4 V

    def read(self) -> Result[BatteryReading]:
        if self.mode is SensorMode.TIMEOUT:
            return Result.err(ErrorCode.TIMEOUT, "batarya ADC yanıt vermedi")
        # Görev boyunca hafif deşarj (deterministik).
        v = self._v - 0.01 * self._mission_time()
        if self.mode is SensorMode.OUTLIER:
            v = 3.0                    # imkânsız düşük
        return Result.ok(BatteryReading(
            voltage_v=v, timestamp_s=self._clock.now_monotonic()))


class MockTelemetryLink:
    """LoRa E22 mock. Gönderileni tamponlar; bağlantı durumu kontrol edilebilir."""

    def __init__(self) -> None:
        self.sent: list[str] = []
        self._connected = True

    def set_connected(self, value: bool) -> None:
        self._connected = value

    def is_connected(self) -> bool:
        return self._connected

    def send(self, line: str) -> Result[None]:
        if not self._connected:
            # Link loss: gönderilemez ama bu TEK BAŞINA APAM tetiklemez.
            return Result.err(ErrorCode.UNAVAILABLE, "telemetri linki kopuk")
        self.sent.append(line)
        return Result.ok(None)


class MockIotLink:
    """BONUS-2 IoT istasyonu bağı mock. Yönlendirilen şifreleri tamponlar."""

    def __init__(self) -> None:
        self.forwarded: list[str] = []
        self._connected = True

    def set_connected(self, value: bool) -> None:
        self._connected = value

    def is_connected(self) -> bool:
        return self._connected

    def forward(self, password: str) -> Result[None]:
        if not self._connected:
            return Result.err(ErrorCode.UNAVAILABLE, "IoT istasyonu bağlantısı kopuk")
        self.forwarded.append(password)
        return Result.ok(None)
