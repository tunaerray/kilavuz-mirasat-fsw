"""Güvenli aktüatör testleri (REQ-SAFE-001/002)."""
from src.common.result import ErrorCode
from src.drivers.mock_actuators import ActuatorSuite, MockMotorGroup
from src.hal.interfaces import ArmState, ServoPosition


def test_motor_starts_disarmed_zero():
    m = MockMotorGroup()
    assert m.arm_state is ArmState.DISARMED
    assert m.throttle == 0.0


def test_no_throttle_without_arm():
    m = MockMotorGroup()
    r = m.set_throttle(0.5)
    assert r.is_err and r.code is ErrorCode.NOT_ARMED
    assert m.throttle == 0.0        # hareket etmedi


def test_throttle_after_arm():
    m = MockMotorGroup()
    m.arm().unwrap()
    assert m.set_throttle(0.7).is_ok
    assert m.throttle == 0.7


def test_throttle_out_of_range_rejected():
    m = MockMotorGroup()
    m.arm().unwrap()
    assert m.set_throttle(1.5).code is ErrorCode.OUT_OF_RANGE
    assert m.set_throttle(-0.1).code is ErrorCode.OUT_OF_RANGE


def test_kill_disarms_and_zeros():
    m = MockMotorGroup()
    m.arm().unwrap()
    m.set_throttle(0.8).unwrap()
    m.kill().unwrap()
    assert m.throttle == 0.0 and m.arm_state is ArmState.DISARMED
    # kill sonrası tekrar gaz verilemez (yeniden arm gerekir)
    assert m.set_throttle(0.5).code is ErrorCode.NOT_ARMED


def test_suite_safe_state():
    s = ActuatorSuite()
    s.motors.arm().unwrap()
    s.motors.set_throttle(0.6).unwrap()
    s.apam_servo.move_to(ServoPosition.OPEN).unwrap()
    s.enter_safe_state().unwrap()
    assert s.motors.arm_state is ArmState.DISARMED
    assert s.motors.throttle == 0.0
    # Safe State APAM'ı YANLIŞLIKLA açık bırakmaz → CLOSED
    assert s.apam_servo.position is ServoPosition.CLOSED
    assert s.separation_servo.position is ServoPosition.LOCKED
    assert s.arms.locked is True


def test_arm_mechanism_deploy_and_lock():
    s = ActuatorSuite()
    assert s.arms.deployed is False and s.arms.locked is True
    s.arms.deploy_and_lock().unwrap()
    assert s.arms.deployed is True and s.arms.locked is True
