"""Sürücü fabrikası ve gerçek LoRa degrade testleri (REQ-HW-003, profil gate)."""
from config.default import AppConfig, RunProfile, TelemetryConfig, get_config
from src.common.result import ErrorCode
from src.drivers.factory import (
    check_profile_runnable,
    create_telemetry_link,
    hardware_libs_available,
)
from src.drivers.mock_sensors import MockTelemetryLink
from src.drivers.real_lora import RealLoraE22Link


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
