"""
Görevi        : Simüle uçuş kontrol kartı bağı (FlightControllerLink). RPi 5 ↔
                PixMin/STM32 arası soyut bağın SIMULATION_ONLY implementasyonu.
                Komut edilen throttle'dan motor RPM geri bildirimi üretir; yönelim
                sağlar; motor arızası ve bağlantı kopukluğu enjeksiyonu destekler.
Neden Gerekli : EKSİK-001 — gerçek protokol (MAVLink, ASSUMPTION-001) PDR'de yok
                ve donanım bu oturumda yok. RPM geri bildirimi, motor PWM/RPM
                tutarlılık (REQ-SAFE-010) ve APAM motor-arıza mantığı için gerekir.
İlişkiler     : HAL FlightControllerLink arayüzünü uygular; DescentController
                setpoint gönderir; MotorHealthMonitor RPM geri bildirimini okur.
                Gerçek MAVLink implementasyonu Aşama 5'e ertelenmiştir (TASK_TRACKER).
Nasıl Test    : tests/test_sim_flight_controller.py — throttle→RPM, arıza faktörü,
                bağlantı kopukluğu, yönelim geçişi, setpoint saklama.
"""
from __future__ import annotations

from typing import Callable

from config.default import ControlConfig
from src.common.clock import Clock
from src.common.result import ErrorCode, Result
from src.hal.interfaces import FlightControllerTelemetry

AttitudeFn = Callable[[], "tuple[float, float, float]"]


class SimulatedFlightControllerLink:
    """
    HAL FlightControllerLink somut sim implementasyonu.
    Motor RPM = throttle * motor_max_rpm * fault_factor (4 motor için de aynı,
    tek arıza faktörü). Gerçek FC, PID stabilizasyonunu kendi üstünde çalıştırır;
    bu sim yalnız üst seviye sözleşmeyi (setpoint gönder / telemetri al) modeller.
    """

    def __init__(self, config: ControlConfig, clock: Clock,
                 attitude_fn: AttitudeFn | None = None) -> None:
        self._c = config
        self._clock = clock
        self._attitude_fn = attitude_fn or (lambda: (0.0, 0.0, 0.0))
        self._throttle = 0.0
        self._target_alt_m: float | None = None
        self._fault_factor = 1.0     # 1.0 sağlıklı, 0.0 tüm motorlar ölü
        self._connected = True

    # ------------------------------------------------------------- test/enjeksiyon
    def set_motor_fault(self, factor: float) -> None:
        """Motor verimini düşür (0..1). 1.0 nominal; <1 kaldırma kaybı (arıza)."""
        self._fault_factor = max(0.0, min(1.0, factor))

    def set_connected(self, value: bool) -> None:
        self._connected = value

    @property
    def commanded_throttle(self) -> float:
        return self._throttle

    @property
    def target_altitude_m(self) -> float | None:
        return self._target_alt_m

    def expected_rpm(self) -> float:
        """Komut edilen throttle için arızasız beklenen RPM."""
        return self._throttle * self._c.motor_max_rpm

    # -------------------------------------------------------------- HAL sözleşmesi
    def is_connected(self) -> bool:
        return self._connected

    def send_setpoint(self, throttle: float, target_alt_m: float | None) -> Result[None]:
        if not self._connected:
            return Result.err(ErrorCode.UNAVAILABLE, "FC bağlantısı kopuk")
        if not (0.0 <= throttle <= 1.0):
            return Result.err(ErrorCode.OUT_OF_RANGE, f"throttle 0..1 dışında: {throttle}")
        self._throttle = throttle
        self._target_alt_m = target_alt_m
        return Result.ok(None)

    def read_telemetry(self) -> Result[FlightControllerTelemetry]:
        if not self._connected:
            return Result.err(ErrorCode.UNAVAILABLE, "FC bağlantısı kopuk")
        rpm = self._throttle * self._c.motor_max_rpm * self._fault_factor
        pitch, roll, yaw = self._attitude_fn()
        return Result.ok(FlightControllerTelemetry(
            pitch_deg=pitch, roll_deg=roll, yaw_deg=yaw,
            motor_rpm=(rpm, rpm, rpm, rpm),
            healthy=self._fault_factor >= 0.999,
            timestamp_s=self._clock.now_monotonic(),
        ))
