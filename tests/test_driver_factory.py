"""Sürücü fabrikası ve gerçek LoRa degrade testleri (REQ-HW-003, profil gate)."""
from config.default import AppConfig, RunProfile, TelemetryConfig, get_config
from src.common.clock import FakeClock
from src.common.result import ErrorCode
from src.drivers.factory import (
    check_profile_runnable,
    create_flight_controller,
    create_mavlink_source,
    create_sensors,
    create_telemetry_link,
    hardware_libs_available,
)
from src.drivers.mavlink_source import (
    MavlinkBarometer,
    MavlinkBattery,
    MavlinkFlightControllerLink,
    MavlinkGps,
    MavlinkImu,
    MavlinkSource,
)
from src.drivers.mock_sensors import (
    MockBarometer,
    MockBattery,
    MockGps,
    MockImu,
    MockTelemetryLink,
)
from src.drivers.real_lora import RealLoraE22Link
from src.drivers.sim_flight_controller import SimulatedFlightControllerLink


def test_simulation_returns_mock():
    link = create_telemetry_link(get_config())   # SIMULATION_ONLY
    assert isinstance(link, MockTelemetryLink)


def test_flight_returns_real_link():
    cfg = AppConfig(profile=RunProfile.FLIGHT)
    link = create_telemetry_link(cfg)
    assert isinstance(link, RealLoraE22Link)


def test_simulation_always_runnable():
    assert check_profile_runnable(get_config()).is_ok


def test_flight_gate_without_hardware():
    cfg = AppConfig(profile=RunProfile.FLIGHT)
    r = check_profile_runnable(cfg)
    if hardware_libs_available():
        assert r.is_ok                       # pyserial kuruluysa geçer
    else:
        assert r.is_err and r.code is ErrorCode.UNAVAILABLE


def test_real_lora_safe_degrade_without_open():
    link = RealLoraE22Link("/dev/ttyAMA0", TelemetryConfig())
    assert not link.is_connected()           # açılmadı
    r = link.send("data")
    assert r.is_err and r.code is ErrorCode.UNAVAILABLE   # çökme yok, açık hata


def test_real_lora_open_reports_missing_dependency_or_port():
    link = RealLoraE22Link("/nonexistent/port", TelemetryConfig())
    r = link.open()
    # pyserial yoksa UNAVAILABLE; varsa geçersiz port → IO_ERROR. Her hâlde hata.
    assert r.is_err
    assert r.code in (ErrorCode.UNAVAILABLE, ErrorCode.IO_ERROR)


# ------------------------------------------ MAVLink kaynak/sensör/FC fabrikası (EKSİK-001)
def _noop(*_):   # sahte mission_time / profile yer tutucusu
    return 0.0


def test_simulation_source_is_none():
    assert create_mavlink_source(get_config(), FakeClock()) is None


def test_flight_source_is_mavlink():
    cfg = AppConfig(profile=RunProfile.FLIGHT)
    src = create_mavlink_source(cfg, FakeClock(), connect_fn=lambda p, b: object())
    assert isinstance(src, MavlinkSource)


def test_simulation_sensors_are_mock():
    baro, imu, gps, batt = create_sensors(get_config(), FakeClock(), None, _noop)
    assert isinstance(baro, MockBarometer)
    assert isinstance(imu, MockImu)
    assert isinstance(gps, MockGps)
    assert isinstance(batt, MockBattery)


def test_flight_sensors_are_mavlink():
    cfg = AppConfig(profile=RunProfile.FLIGHT)
    src = create_mavlink_source(cfg, FakeClock(), connect_fn=lambda p, b: object())
    baro, imu, gps, batt = create_sensors(cfg, FakeClock(), None, _noop, src)
    assert isinstance(baro, MavlinkBarometer)
    assert isinstance(imu, MavlinkImu)
    assert isinstance(gps, MavlinkGps)
    assert isinstance(batt, MavlinkBattery)


def test_flight_sensors_require_source():
    cfg = AppConfig(profile=RunProfile.FLIGHT)
    try:
        create_sensors(cfg, FakeClock(), None, _noop, None)
        assert False, "source=None ile ValueError beklenirdi"
    except ValueError:
        pass


def test_flight_controller_factory_by_profile():
    sim_fc = create_flight_controller(get_config(), FakeClock(),
                                      attitude_fn=lambda: (0.0, 0.0, 0.0))
    assert isinstance(sim_fc, SimulatedFlightControllerLink)
    cfg = AppConfig(profile=RunProfile.FLIGHT)
    src = create_mavlink_source(cfg, FakeClock(), connect_fn=lambda p, b: object())
    fc = create_flight_controller(cfg, FakeClock(), source=src)
    assert isinstance(fc, MavlinkFlightControllerLink)
