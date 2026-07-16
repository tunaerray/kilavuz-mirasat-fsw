"""PID kontrolcü testleri (REQ-CTRL-002 temeli)."""
import pytest

from src.control.pid import PidController, PidGains


def _gains(kp=1.0, ki=0.0, kd=0.0, omin=0.0, omax=1.0, imin=-10.0, imax=10.0):
    return PidGains(kp=kp, ki=ki, kd=kd, output_min=omin, output_max=omax,
                    integral_min=imin, integral_max=imax)


def test_proportional_only():
    pid = PidController(_gains(kp=0.1, omin=-100, omax=100))
    # hata = 10 - 0 = 10 → çıkış 1.0
    assert pid.update(setpoint=10.0, measurement=0.0, dt=0.1) == pytest.approx(1.0)


def test_output_clamped():
    pid = PidController(_gains(kp=1.0, omin=0.0, omax=1.0))
    # hata 10 → ham 10 → 1.0'a kırpılır
    assert pid.update(10.0, 0.0, 0.1) == 1.0
    # negatif hata → 0.0'a kırpılır
    assert pid.update(-10.0, 0.0, 0.1) == 0.0


def test_integral_accumulates():
    pid = PidController(_gains(kp=0.0, ki=1.0, omin=-100, omax=100))
    pid.update(1.0, 0.0, 1.0)   # integral += 1
    out = pid.update(1.0, 0.0, 1.0)   # integral += 1 → 2
    assert out == pytest.approx(2.0)


def test_integral_clamped_antiwindup():
    pid = PidController(_gains(kp=0.0, ki=1.0, omin=-100, omax=100, imin=-2, imax=2))
    for _ in range(10):
        pid.update(5.0, 0.0, 1.0)
    # integral 2'de sınırlanır
    assert pid.integral <= 2.0 + 1e-9


def test_no_windup_when_output_saturated():
    # Çıkış 0..1 doymuş; integral sürekli pozitif hatada şişmemeli
    pid = PidController(_gains(kp=1.0, ki=1.0, omin=0.0, omax=1.0, imin=-100, imax=100))
    for _ in range(50):
        pid.update(10.0, 0.0, 1.0)
    integ_after_sat = pid.integral
    # şimdi hata işareti tersine dönsün; çıkış hızlıca düşebilmeli (windup yok)
    out = pid.update(-10.0, 0.0, 1.0)
    assert out == 0.0
    assert integ_after_sat < 50.0    # integral kontrolsüz şişmedi


def test_derivative_on_measurement_no_setpoint_kick():
    # Setpoint adım değişiminde türev sıçraması OLMAMALI (ölçüm sabit)
    pid = PidController(_gains(kp=0.0, kd=1.0, omin=-100, omax=100))
    pid.update(0.0, 0.0, 1.0)          # ölçüm 0
    out = pid.update(100.0, 0.0, 1.0)  # setpoint sıçradı ama ölçüm hâlâ 0
    assert out == pytest.approx(0.0)   # türev katkısı yok


def test_derivative_responds_to_measurement_change():
    pid = PidController(_gains(kp=0.0, kd=1.0, omin=-100, omax=100))
    pid.update(0.0, 0.0, 1.0)
    out = pid.update(0.0, 5.0, 1.0)    # ölçüm 0→5, d_meas=5 → çıkış -5
    assert out == pytest.approx(-5.0)


def test_reset_clears_state():
    pid = PidController(_gains(kp=0.0, ki=1.0, omin=-100, omax=100))
    pid.update(1.0, 0.0, 1.0)
    pid.reset()
    assert pid.integral == 0.0
    out = pid.update(1.0, 0.0, 1.0)
    assert out == pytest.approx(1.0)   # sıfırdan başladı


def test_zero_dt_safe():
    pid = PidController(_gains(kp=1.0, ki=1.0, kd=1.0, omin=-100, omax=100))
    out = pid.update(5.0, 0.0, 0.0)    # dt=0 → türev/integral eklenmez, P kalır
    assert out == pytest.approx(5.0)
