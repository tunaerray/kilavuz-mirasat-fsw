"""
Görevi        : Güvenli mock aktüatörler (4× motor grubu, ayrılma servosu, APAM
                servosu, SİGMA kol mekanizması). SIMULATION_ONLY'de fiziksel PWM
                üretmez; yalnız komutları loglar. Arm edilmeden hareket etmez ve
                Safe State'e geçebilir.
Neden Gerekli : ANA_PROMPT F.8 + safety — ilk aşamada gerçek motor/servo/APAM
                çalıştıran kod ASLA aktif olmamalı. Safe State ve arm interlock
                zorunlu.
İlişkiler     : HAL MotorGroup/Servo arayüzlerini uygular; failsafe motor kill ve
                paraşüt açma sıralamasını bunlar üzerinden yürütür.
Nasıl Test    : tests/test_actuators.py — arm olmadan reddetme, safe state,
                komut logu, throttle sınırları.
"""
from __future__ import annotations

from src.common.result import ErrorCode, Result
from src.hal.interfaces import ArmState, ServoPosition


class MockMotorGroup:
    """4× fırçasız motor. Throttle 0..1. Arm interlock ve kill destekli."""

    def __init__(self, name: str = "sigma_motors") -> None:
        self._name = name
        self._arm = ArmState.DISARMED
        self._throttle = 0.0
        self.command_log: list[str] = []

    @property
    def arm_state(self) -> ArmState:
        return self._arm

    @property
    def throttle(self) -> float:
        return self._throttle

    def arm(self) -> Result[None]:
        self._arm = ArmState.ARMED
        self.command_log.append("ARM")
        return Result.ok(None)

    def disarm(self) -> Result[None]:
        self._arm = ArmState.DISARMED
        self._throttle = 0.0
        self.command_log.append("DISARM")
        return Result.ok(None)

    def set_throttle(self, throttle: float) -> Result[None]:
        # Arm interlock: arm edilmeden gaz verilemez (güvenlik).
        if self._arm is not ArmState.ARMED:
            return Result.err(ErrorCode.NOT_ARMED,
                              "motorlar arm edilmeden throttle reddedildi")
        if not (0.0 <= throttle <= 1.0):
            return Result.err(ErrorCode.OUT_OF_RANGE,
                              f"throttle 0..1 dışında: {throttle}")
        self._throttle = throttle
        self.command_log.append(f"THROTTLE {throttle:.2f}")
        return Result.ok(None)

    def kill(self) -> Result[None]:
        """Motor kill: gaz 0 + disarm. Paraşüt açılmadan HEMEN ÖNCE çağrılır."""
        self._throttle = 0.0
        self._arm = ArmState.DISARMED
        self.command_log.append("KILL")
        return Result.ok(None)


class MockServo:
    """Ayrılma / APAM paraşüt kapağı / kol servosu. Güvenli konuma geçebilir."""

    def __init__(self, name: str, safe_position: ServoPosition) -> None:
        self._name = name
        self._safe = safe_position
        self._pos = safe_position
        self.command_log: list[str] = []

    @property
    def position(self) -> ServoPosition:
        return self._pos

    def move_to(self, position: ServoPosition) -> Result[None]:
        self._pos = position
        self.command_log.append(f"MOVE {position.value}")
        return Result.ok(None)

    def to_safe(self) -> Result[None]:
        self._pos = self._safe
        self.command_log.append("SAFE")
        return Result.ok(None)


class MockArmMechanism:
    """
    SİGMA kol açma/kilitleme mekanizması. Başlangıçta gövde içinde KAPALI/kilitli;
    ayrılma sonrası açılır ve kilitlenir. Aşama 1'de durum makinesi için modellenir.
    """

    def __init__(self) -> None:
        self._deployed = False
        self._locked = True         # başlangıçta kilitli (güvenli)
        self.command_log: list[str] = []

    @property
    def deployed(self) -> bool:
        return self._deployed

    @property
    def locked(self) -> bool:
        return self._locked

    def deploy_and_lock(self) -> Result[None]:
        """Kolları 90° açar ve kilitler (ayrılma → aktif iniş arası)."""
        self._deployed = True
        self._locked = True
        self.command_log.append("DEPLOY_AND_LOCK")
        return Result.ok(None)

    def to_safe(self) -> Result[None]:
        """Safe State: mevcut konumda kilitli kalır (kolları geri katlamaz)."""
        self._locked = True
        self.command_log.append("SAFE(locked-in-place)")
        return Result.ok(None)


class ActuatorSuite:
    """Tüm aktüatörleri bir arada tutar ve topluca Safe State'e alır."""

    def __init__(self) -> None:
        self.motors = MockMotorGroup()
        self.separation_servo = MockServo("separation", ServoPosition.LOCKED)
        self.apam_servo = MockServo("apam", ServoPosition.CLOSED)
        self.arms = MockArmMechanism()

    def enter_safe_state(self) -> Result[None]:
        """
        Safe State: motorlar disarm/0, servolar güvenli konum, kollar kilitli.
        Başlangıçta, FAULT'ta, SAFE_MODE'da ve kapanışta çağrılır.
        Not: APAM servosu YANLIŞLIKLA açılmaz — safe = CLOSED.
        """
        self.motors.kill()
        self.separation_servo.to_safe()
        self.apam_servo.to_safe()
        self.arms.to_safe()
        return Result.ok(None)
