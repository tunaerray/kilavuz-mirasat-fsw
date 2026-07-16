"""Preflight go/no-go testleri (FRR, Şartname §4.2)."""
from config.default import HealthConfig
from src.common.clock import FakeClock
from src.drivers.flight_profile import FlightProfile
from src.drivers.mock_actuators import ActuatorSuite
from src.drivers.mock_sensors import (
    MockBarometer,
    MockBattery,
    MockGps,
    MockImu,
    SensorMode,
)
from src.services.preflight import PreflightCheck


class _FakePersistence:
    def __init__(self, boot_count=1):
        self.boot_count = boot_count


def _rig(boot_count=1, start_v=16.4):
    clk = FakeClock()
    prof = FlightProfile("nominal_descent")
    mt = lambda: 0.0
    baro = MockBarometer(clk, prof, mt)
    imu = MockImu(clk, prof, mt)
    gps = MockGps(clk, prof, mt)
    batt = MockBattery(clk, prof, mt, start_voltage_v=start_v)
    act = ActuatorSuite()
    act.enter_safe_state()
    return baro, imu, gps, batt, act, _FakePersistence(boot_count)


def test_all_go_nominal():
    baro, imu, gps, batt, act, per = _rig()
    rep = PreflightCheck(HealthConfig()).run(baro, imu, gps, batt, act, per)
    assert rep.is_go
    assert rep.failed() == []


def test_low_battery_no_go():
    baro, imu, gps, batt, act, per = _rig(start_v=14.5)   # 15.0 altı
    rep = PreflightCheck(HealthConfig()).run(baro, imu, gps, batt, act, per)
    assert not rep.is_go
    assert any("Batarya dolu" in f.name for f in rep.failed())


def test_gps_no_lock_no_go():
    baro, imu, gps, batt, act, per = _rig()
    gps.mode = SensorMode.OUTLIER          # fix yok, 0 uydu
    rep = PreflightCheck(HealthConfig()).run(baro, imu, gps, batt, act, per)
    assert not rep.is_go
    assert any("GPS" in f.name for f in rep.failed())


def test_sensor_timeout_no_go():
    baro, imu, gps, batt, act, per = _rig()
    baro.mode = SensorMode.TIMEOUT
    rep = PreflightCheck(HealthConfig()).run(baro, imu, gps, batt, act, per)
    assert not rep.is_go
    assert any("Barometre" in f.name for f in rep.failed())


def test_armed_motor_no_go():
    baro, imu, gps, batt, act, per = _rig()
    act.motors.arm()                       # güvensiz: arm edilmiş
    rep = PreflightCheck(HealthConfig()).run(baro, imu, gps, batt, act, per)
    assert not rep.is_go
    assert any("Safe State" in f.name for f in rep.failed())


def test_apam_open_no_go():
    from src.hal.interfaces import ServoPosition
    baro, imu, gps, batt, act, per = _rig()
    act.apam_servo.move_to(ServoPosition.OPEN)   # paraşüt açık = güvensiz
    rep = PreflightCheck(HealthConfig()).run(baro, imu, gps, batt, act, per)
    assert not rep.is_go


def test_persistence_not_loaded_no_go():
    baro, imu, gps, batt, act, per = _rig(boot_count=0)
    rep = PreflightCheck(HealthConfig()).run(baro, imu, gps, batt, act, per)
    assert not rep.is_go
    assert any("Kalıcılık" in f.name for f in rep.failed())


def test_report_has_all_items():
    baro, imu, gps, batt, act, per = _rig()
    rep = PreflightCheck(HealthConfig()).run(baro, imu, gps, batt, act, per)
    names = [i.name for i in rep.items]
    assert "GPS kilidi" in names
    assert "Aktüatörler Safe State" in names
    assert len(rep.items) >= 7
