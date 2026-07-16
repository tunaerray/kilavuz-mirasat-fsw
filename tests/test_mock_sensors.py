"""Mock sensör testleri (REQ-FUNC-001)."""
from src.common.clock import FakeClock
from src.common.result import ErrorCode
from src.drivers.flight_profile import FlightProfile
from src.drivers.mock_sensors import (
    MockBarometer,
    MockBattery,
    MockGps,
    MockImu,
    MockTelemetryLink,
    SensorMode,
)


def _rig():
    clock = FakeClock()
    profile = FlightProfile("nominal_descent")
    t = [30.0]                       # görev zamanı (aktif iniş fazı)
    return clock, profile, (lambda: t[0]), t


def test_barometer_nominal():
    clock, profile, mt, _ = _rig()
    baro = MockBarometer(clock, profile, mt)
    r = baro.read()
    assert r.is_ok
    assert 50000 < r.unwrap().pressure_pa < 105000


def test_barometer_timeout():
    clock, profile, mt, _ = _rig()
    baro = MockBarometer(clock, profile, mt)
    baro.mode = SensorMode.TIMEOUT
    r = baro.read()
    assert r.is_err and r.code is ErrorCode.TIMEOUT


def test_barometer_outlier():
    clock, profile, mt, _ = _rig()
    baro = MockBarometer(clock, profile, mt)
    baro.mode = SensorMode.OUTLIER
    assert baro.read().unwrap().pressure_pa < 0     # aykırı değer üretildi


def test_imu_modes():
    clock, profile, mt, _ = _rig()
    imu = MockImu(clock, profile, mt)
    assert imu.read().is_ok
    imu.mode = SensorMode.OUTLIER
    assert imu.read().unwrap().pitch_deg == 9999.0
    imu.mode = SensorMode.TIMEOUT
    assert imu.read().is_err


def test_gps_nominal_has_fix():
    clock, profile, mt, _ = _rig()
    gps = MockGps(clock, profile, mt)
    r = gps.read().unwrap()
    assert r.fix_valid and r.satellites >= 6


def test_gps_outlier_no_fix():
    clock, profile, mt, _ = _rig()
    gps = MockGps(clock, profile, mt)
    gps.mode = SensorMode.OUTLIER
    r = gps.read().unwrap()
    assert not r.fix_valid and r.satellites == 0


def test_battery_discharges_over_time():
    clock, profile, mt, t = _rig()
    batt = MockBattery(clock, profile, mt, start_voltage_v=16.4)
    t[0] = 0.0
    v0 = batt.read().unwrap().voltage_v
    t[0] = 100.0
    v1 = batt.read().unwrap().voltage_v
    assert v1 < v0


def test_link_loss_send_fails_but_is_reported():
    link = MockTelemetryLink()
    assert link.send("x").is_ok
    link.set_connected(False)
    r = link.send("y")
    assert r.is_err and r.code is ErrorCode.UNAVAILABLE
    assert link.sent == ["x"]        # kopukken tampona yazmadı
