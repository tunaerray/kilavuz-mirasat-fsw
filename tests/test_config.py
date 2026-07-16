"""Config birim testleri (REQ-SW-002, CONFLICT-001/003 varsayılanları)."""
import pytest

from config.default import AppConfig, RunProfile, get_config, with_overrides


def test_default_profile_is_simulation_only():
    cfg = get_config()
    assert cfg.profile is RunProfile.SIMULATION_ONLY
    assert cfg.is_simulation is True


def test_team_number_verified():
    assert get_config().team_number == 947450


def test_apam_thresholds_from_spec():
    a = get_config().apam
    assert a.trigger_speed_mps == 16.0
    assert a.trigger_duration_s == 10.0
    assert a.min_deploy_altitude_m == 100.0


def test_conflict_defaults():
    cfg = get_config()
    assert cfg.telemetry.error_code_digits == 4          # CONFLICT-003 varsayılan
    assert cfg.mission.post_landing_telemetry_s == 10.0  # CONFLICT-001 varsayılan
    assert cfg.mission.carrier_descent_speed_range == (12.0, 16.0)  # CONFLICT-004


def test_telemetry_rate_is_1hz():
    cfg = get_config()
    assert cfg.telemetry.rate_hz == 1.0
    assert cfg.telemetry_period_s == 1.0


def test_loop_period():
    cfg = with_overrides(AppConfig(), loop_hz=20.0)
    assert cfg.loop_period_s == pytest.approx(0.05)


def test_unknown_profile_raises():
    with pytest.raises(ValueError):
        get_config("flight_now")


def test_config_is_immutable():
    cfg = get_config()
    with pytest.raises(Exception):
        cfg.team_number = 0  # frozen dataclass
