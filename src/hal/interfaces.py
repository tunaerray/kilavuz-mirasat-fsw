"""
Görevi        : Donanım Soyutlama Katmanı (HAL) arayüzleri. Sensör, aktüatör,
                telemetri linki ve uçuş kontrol kartı bağlantısı için somut
                donanımdan bağımsız sözleşmeler tanımlar.
Neden Gerekli : Donanım fiziksel olarak yok; masaüstü simülasyon ve mock sürücüler
                bu arayüzleri uygular. Üst katmanlar somut sürücülere değil bu
                arayüzlere bağlanır (Dependency Inversion). EKSİK-001: RPi↔PixMin
                protokolü soyut FlightControllerLink olarak modellendi.
İlişkiler     : src/drivers/* bu arayüzleri uygular; main bağımlılıkları enjekte
                eder; health/failsafe/telemetry bu tiplerle çalışır.
Nasıl Test    : Arayüzler mock uygulamalarla test edilir (test_mock_sensors,
                test_actuators). Protocol'ler runtime_checkable.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable

from src.common.result import Result


# --------------------------------------------------------------------- sensörler
@dataclass(frozen=True)
class BarometerReading:
    pressure_pa: float
    temperature_c: float
    timestamp_s: float          # okuma anının monoton zamanı (veri yaşı için)


@dataclass(frozen=True)
class ImuReading:
    pitch_deg: float
    roll_deg: float
    yaw_deg: float
    accel_z_mps2: float
    timestamp_s: float


@dataclass(frozen=True)
class GpsReading:
    latitude: float
    longitude: float
    altitude_m: float
    satellites: int             # açık alan min 6 kilit test kriteri
    fix_valid: bool
    timestamp_s: float


@dataclass(frozen=True)
class BatteryReading:
    voltage_v: float
    timestamp_s: float


@runtime_checkable
class Barometer(Protocol):
    def read(self) -> Result[BarometerReading]: ...


@runtime_checkable
class Imu(Protocol):
    def read(self) -> Result[ImuReading]: ...


@runtime_checkable
class Gps(Protocol):
    def read(self) -> Result[GpsReading]: ...


@runtime_checkable
class Battery(Protocol):
    def read(self) -> Result[BatteryReading]: ...


@runtime_checkable
class TelemetryLink(Protocol):
    """LoRa E22 karşılığı. Aşama 1'de mock; yalnız gönderim durumu döner."""

    def send(self, line: str) -> Result[None]: ...

    def is_connected(self) -> bool: ...


# --------------------------------------------------------------------- aktüatörler
class ArmState(Enum):
    DISARMED = "DISARMED"
    ARMED = "ARMED"


class ServoPosition(Enum):
    """Servo güvenli/aktif konumları (somut açı sürücüde eşlenir)."""

    LOCKED = "LOCKED"        # güvenli/kilitli
    CLOSED = "CLOSED"        # kapak kapalı
    OPEN = "OPEN"            # kapak/paraşüt açık
    DEPLOYED = "DEPLOYED"    # kol açılmış


@runtime_checkable
class MotorGroup(Protocol):
    """4× fırçasız motor grubu (SİGMA). Throttle 0..1. Arm olmadan çalışmaz."""

    def arm(self) -> Result[None]: ...

    def disarm(self) -> Result[None]: ...

    def set_throttle(self, throttle: float) -> Result[None]: ...

    def kill(self) -> Result[None]: ...

    @property
    def arm_state(self) -> ArmState: ...

    @property
    def throttle(self) -> float: ...


@runtime_checkable
class Servo(Protocol):
    """Tekil servo (ayrılma / APAM paraşüt kapağı / kol)."""

    def move_to(self, position: ServoPosition) -> Result[None]: ...

    def to_safe(self) -> Result[None]: ...

    @property
    def position(self) -> ServoPosition: ...


# ------------------------------------------------------- uçuş kontrol kartı bağı
@dataclass(frozen=True)
class FlightControllerTelemetry:
    """PixMin/STM32'den gelen üst seviye durum (EKSİK-001, ASSUMPTION-001)."""

    pitch_deg: float
    roll_deg: float
    yaw_deg: float
    motor_rpm: tuple            # 4 motorun RPM geri bildirimi
    healthy: bool
    timestamp_s: float


@runtime_checkable
class FlightControllerLink(Protocol):
    """
    RPi 5 ↔ PixMin arası soyut bağ. Protokol PDR'de belirtilmemiş (EKSİK-001);
    MAVLink önerilir (ASSUMPTION-001). Somut implementasyon Aşama 2'de.
    """

    def read_telemetry(self) -> Result[FlightControllerTelemetry]: ...

    def send_setpoint(self, throttle: float, target_alt_m: float | None) -> Result[None]: ...

    def is_connected(self) -> bool: ...
