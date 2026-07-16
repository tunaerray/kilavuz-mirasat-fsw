"""Durum kestirici testleri (REQ-CTRL-001)."""
from config.default import ControlConfig
from src.common.result import ErrorCode, Result
from src.drivers.flight_profile import altitude_to_pressure
from src.hal.interfaces import BarometerReading, GpsReading, ImuReading


from src.control.estimator import StateEstimator

P0 = 101325.0   # deniz seviyesi = kalkış referansı (alt 0)


def _baro(alt_m, ts=0.0):
    return Result.ok(BarometerReading(pressure_pa=altitude_to_pressure(alt_m),
                                      temperature_c=25.0, timestamp_s=ts))


def _imu(pitch=1.0, roll=2.0, yaw=3.0, ts=0.0):
    return Result.ok(ImuReading(pitch_deg=pitch, roll_deg=roll, yaw_deg=yaw,
                                accel_z_mps2=9.81, timestamp_s=ts))


def _gps(alt_m, valid=True, ts=0.0):
    return Result.ok(GpsReading(latitude=39.0, longitude=32.0, altitude_m=alt_m,
                                satellites=8, fix_valid=valid, timestamp_s=ts))


def _est(alpha=0.0):
    # alpha=0 → filtre yok (ham hız), deterministik test için
    cfg = ControlConfig(vspeed_filter_alpha=alpha)
    return StateEstimator(cfg, P0)


def test_altitude_from_pressure():
    est = _est()
    out = est.update(_baro(500.0), _imu(), _gps(515.0), dt=0.1)
    assert abs(out.altitude_m - 500.0) < 1.0
    assert out.altitude_valid


def test_vertical_speed_finite_difference():
    est = _est(alpha=0.0)
    est.update(_baro(1000.0), _imu(), _gps(1015.0), dt=1.0)   # ilk: hız 0
    out = est.update(_baro(991.0), _imu(), _gps(1006.0), dt=1.0)  # 9 m düştü
    assert abs(out.vertical_speed_mps - 9.0) < 0.5


def test_filter_smooths_speed():
    est = _est(alpha=0.8)   # ağır filtre
    est.update(_baro(1000.0), _imu(), _gps(1015.0), dt=1.0)
    out = est.update(_baro(980.0), _imu(), _gps(995.0), dt=1.0)  # 20 m/s ani
    # filtre nedeniyle ham 20'nin çok altında
    assert out.vertical_speed_mps < 10.0


def test_baro_outlier_rejected():
    est = _est(alpha=0.0)
    est.update(_baro(500.0), _imu(), _gps(515.0), dt=1.0)
    # aykırı basınç → imkânsız irtifa
    bad = Result.ok(BarometerReading(pressure_pa=-1.0, temperature_c=25.0,
                                     timestamp_s=1.0))
    out = est.update(bad, _imu(), _gps(510.0), dt=1.0)
    assert not out.altitude_valid
    assert abs(out.altitude_m - 500.0) < 1.0    # son geçerli korunur


def test_baro_timeout_holds_last():
    est = _est(alpha=0.0)
    est.update(_baro(300.0), _imu(), _gps(315.0), dt=1.0)
    to = Result.err(ErrorCode.TIMEOUT, "baro yok")
    out = est.update(to, _imu(), _gps(310.0), dt=1.0)
    assert not out.altitude_valid
    assert abs(out.altitude_m - 300.0) < 1.0


def test_speed_consistency_true_when_agree():
    est = _est(alpha=0.0)
    est.update(_baro(1000.0), _imu(), _gps(1015.0), dt=1.0)
    # baro 9 m/s, gps 9 m/s → tutarlı
    out = est.update(_baro(991.0), _imu(), _gps(1006.0), dt=1.0)
    assert out.speed_consistent


def test_speed_consistency_false_when_disagree():
    est = _est(alpha=0.0)
    est.update(_baro(1000.0), _imu(), _gps(1015.0), dt=1.0)
    # baro 9 m/s ama gps neredeyse sabit → tutarsız
    out = est.update(_baro(991.0), _imu(), _gps(1014.5), dt=1.0)
    assert not out.speed_consistent


def test_attitude_outlier_rejected():
    est = _est()
    est.update(_baro(500.0), _imu(pitch=5.0), _gps(515.0), dt=1.0)
    out = est.update(_baro(500.0), _imu(pitch=9999.0), _gps(515.0), dt=1.0)
    assert not out.attitude_valid
    assert out.pitch_deg == 5.0     # son geçerli korunur


def test_gps_invalid_flag():
    est = _est()
    out = est.update(_baro(500.0), _imu(), _gps(515.0, valid=False), dt=1.0)
    assert not out.gps_valid
