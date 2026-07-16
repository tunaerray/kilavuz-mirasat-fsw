"""ARAS hata kodu testleri — Şartname §2.2 (REQ-TLM-011..015, CONFLICT-003)."""
import pytest

from src.telemetry.packet import ArasInputs, compute_error_code


def _inp(**kw):
    base = dict(descent_speed_mps=9.0, speed_check_active=True,
                gps_valid=True, separation_done=True, apam_active=False)
    base.update(kw)
    return ArasInputs(**base)


def test_all_nominal_is_0000():
    assert compute_error_code(_inp()) == "0000"


def test_position_lost_is_0100():
    # Şartname örneği: <0100> konum verisi iletilememesi
    assert compute_error_code(_inp(gps_valid=False)) == "0100"


def test_apam_active_is_0001():
    # Şartname örneği: <0001> APAM aktif
    assert compute_error_code(_inp(apam_active=True)) == "0001"


def test_speed_out_of_range_sets_bit1():
    assert compute_error_code(_inp(descent_speed_mps=12.0)) == "1000"
    assert compute_error_code(_inp(descent_speed_mps=7.0)) == "1000"


def test_speed_check_inactive_gives_bit1_zero():
    # Aktif iniş fazı dışında hız denetimi yapılmaz → bit1=0
    assert compute_error_code(_inp(descent_speed_mps=30.0,
                                   speed_check_active=False)) == "0000"


def test_not_separated_sets_bit3():
    assert compute_error_code(_inp(separation_done=False)) == "0010"


def test_multiple_faults():
    code = compute_error_code(_inp(descent_speed_mps=20.0, gps_valid=False,
                                   separation_done=False, apam_active=True))
    assert code == "1111"


def test_digits_config_padding():
    # CONFLICT-003: 5 haneye genişletilebilir (sol sıfır dolgu)
    assert compute_error_code(_inp(gps_valid=False), digits=5) == "00100"


def test_digits_too_small_raises():
    with pytest.raises(ValueError):
        compute_error_code(_inp(), digits=3)
