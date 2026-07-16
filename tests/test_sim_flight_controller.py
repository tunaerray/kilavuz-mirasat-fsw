"""Simüle FlightControllerLink testleri (EKSİK-001, REQ-SAFE-010 temeli)."""
from config.default import ControlConfig
from src.common.clock import FakeClock
from src.common.result import ErrorCode
from src.drivers.sim_flight_controller import SimulatedFlightControllerLink
from src.hal.interfaces import FlightControllerLink


def _fc(attitude_fn=None):
    return SimulatedFlightControllerLink(ControlConfig(), FakeClock(), attitude_fn)


def test_implements_hal_protocol():
    assert isinstance(_fc(), FlightControllerLink)


def test_setpoint_stored():
    fc = _fc()
    assert fc.send_setpoint(0.6, 200.0).is_ok
    assert fc.commanded_throttle == 0.6
    assert fc.target_altitude_m == 200.0


def test_setpoint_out_of_range():
    fc = _fc()
    assert fc.send_setpoint(1.5, None).code is ErrorCode.OUT_OF_RANGE


def test_rpm_proportional_to_throttle():
    fc = _fc()
    fc.send_setpoint(0.5, None).unwrap()
    tlm = fc.read_telemetry().unwrap()
    expected = 0.5 * ControlConfig().motor_max_rpm
    assert all(abs(r - expected) < 1e-6 for r in tlm.motor_rpm)
    assert tlm.healthy


def test_motor_fault_drops_rpm():
    fc = _fc()
    fc.send_setpoint(0.8, None).unwrap()
    fc.set_motor_fault(0.3)          # %70 kaldırma kaybı
    tlm = fc.read_telemetry().unwrap()
    expected_healthy = 0.8 * ControlConfig().motor_max_rpm
    assert tlm.motor_rpm[0] < expected_healthy * 0.5
    assert not tlm.healthy
    # beklenen (arızasız) RPM referansı değişmez
    assert abs(fc.expected_rpm() - expected_healthy) < 1e-6


def test_disconnected_blocks_io():
    fc = _fc()
    fc.set_connected(False)
    assert fc.send_setpoint(0.5, None).code is ErrorCode.UNAVAILABLE
    assert fc.read_telemetry().code is ErrorCode.UNAVAILABLE
    assert not fc.is_connected()


def test_attitude_from_source():
    fc = _fc(attitude_fn=lambda: (5.0, -3.0, 90.0))
    tlm = fc.read_telemetry().unwrap()
    assert (tlm.pitch_deg, tlm.roll_deg, tlm.yaw_deg) == (5.0, -3.0, 90.0)
