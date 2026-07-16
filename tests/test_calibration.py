"""Saha baro kalibrasyonu testleri (EKSİK-003, PDR s.90)."""
from src.common.result import ErrorCode
from src.services.calibration import BaroCalibrator


def test_average_of_clean_samples():
    cal = BaroCalibrator(sample_count=5, min_samples=3)
    for p in (101300, 101310, 101320, 101305, 101315):
        cal.add_sample(p)
    ref = cal.calibrate().unwrap()
    assert abs(ref - 101310) < 1.0


def test_ready_flag():
    cal = BaroCalibrator(sample_count=3, min_samples=2)
    cal.add_sample(101300)
    assert not cal.ready
    cal.add_sample(101300); cal.add_sample(101300)
    assert cal.ready


def test_outlier_rejected():
    cal = BaroCalibrator(sample_count=5, min_samples=3, outlier_tolerance_pa=200)
    for p in (101300, 101310, 101320, 101305, 150000):  # son değer aykırı
        cal.add_sample(p)
    ref = cal.calibrate().unwrap()
    # aykırı 150000 elenmeli → referans ~101309
    assert abs(ref - 101309) < 5.0


def test_insufficient_samples():
    cal = BaroCalibrator(sample_count=20, min_samples=5)
    cal.add_sample(101300); cal.add_sample(101305)
    r = cal.calibrate()
    assert r.is_err and r.code is ErrorCode.INVALID_DATA


def test_negative_pressure_ignored():
    cal = BaroCalibrator(sample_count=5, min_samples=3)
    for p in (101300, -1, 101310, 0, 101320):   # -1 ve 0 atılır
        cal.add_sample(p)
    assert cal.sample_count == 3
    assert cal.calibrate().is_ok


def test_stable_under_noise():
    cal = BaroCalibrator(sample_count=21, min_samples=5, outlier_tolerance_pa=100)
    # 101325 etrafında ±30 gürültü (deterministik salınım)
    base = 101325
    for i in range(21):
        cal.add_sample(base + (i % 7 - 3) * 10)
    ref = cal.calibrate().unwrap()
    assert abs(ref - base) < 15.0


def test_reset_clears():
    cal = BaroCalibrator(sample_count=3, min_samples=2)
    cal.add_sample(101300); cal.add_sample(101300)
    cal.reset()
    assert cal.sample_count == 0
