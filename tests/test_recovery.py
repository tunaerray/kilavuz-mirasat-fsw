"""Kurtarma yöneticisi testleri (Gereksinim-27/28, CONFLICT-001)."""
from config.default import MissionConfig
from src.drivers.mock_actuators import MockBuzzer
from src.services.recovery import RecoveryManager
from src.state_machine.flight_state_machine import FlightPhase


def _rm(post_s=10.0):
    return RecoveryManager(MissionConfig(post_landing_telemetry_s=post_s)), MockBuzzer()


def test_before_landing_buzzer_off_telemetry_on():
    rm, bz = _rm()
    st = rm.update(FlightPhase.ACTIVE_DESCENT, mission_time_s=50.0, buzzer=bz)
    assert not st.landed
    assert not st.buzzer_on and not bz.is_on
    assert st.telemetry_active


def test_landing_turns_buzzer_on():
    rm, bz = _rm()
    st = rm.update(FlightPhase.RECOVERY, mission_time_s=100.0, buzzer=bz)
    assert st.landed and st.buzzer_on and bz.is_on


def test_telemetry_active_within_window():
    rm, bz = _rm(post_s=10.0)
    rm.update(FlightPhase.RECOVERY, 100.0, bz)          # iniş t=100
    st = rm.update(FlightPhase.RECOVERY, 108.0, bz)     # +8 s
    assert st.telemetry_active
    assert abs(st.seconds_since_landing - 8.0) < 1e-6


def test_telemetry_stops_after_window():
    rm, bz = _rm(post_s=10.0)
    rm.update(FlightPhase.RECOVERY, 100.0, bz)
    st = rm.update(FlightPhase.RECOVERY, 111.0, bz)     # +11 s > 10
    assert not st.telemetry_active
    assert bz.is_on                                      # buzzer çalmaya devam


def test_landing_time_latched_at_first_entry():
    rm, bz = _rm()
    rm.update(FlightPhase.LANDED, 100.0, bz)
    # sonraki çevrimlerde iniş anı değişmez
    st = rm.update(FlightPhase.RECOVERY, 105.0, bz)
    assert abs(st.seconds_since_landing - 5.0) < 1e-6


def test_configurable_window_60s():
    rm, bz = _rm(post_s=60.0)
    rm.update(FlightPhase.RECOVERY, 100.0, bz)
    st = rm.update(FlightPhase.RECOVERY, 155.0, bz)     # +55 s < 60
    assert st.telemetry_active
