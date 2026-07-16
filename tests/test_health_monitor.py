"""Sağlık izleyici testleri (REQ-SAFE-009)."""
from config.default import HealthConfig
from src.services.health_monitor import HealthInputs, HealthMonitor


def _inp(**kw):
    base = dict(now_s=10.0, newest_sensor_timestamp_s=10.0, any_sensor_valid=True,
                battery_v=16.0, last_link_ok_s=10.0, loop_duration_s=0.01,
                loop_period_s=0.05)
    base.update(kw)
    return HealthInputs(**base)


def _hm():
    return HealthMonitor(HealthConfig())


def test_all_nominal_no_flags():
    f = _hm().evaluate(_inp())
    assert not any([f.stale_sensor, f.low_battery, f.critical_battery,
                    f.link_loss, f.loop_overrun])


def test_stale_sensor_by_age():
    f = _hm().evaluate(_inp(newest_sensor_timestamp_s=9.0))  # 1 s eski > 0.5
    assert f.stale_sensor


def test_stale_sensor_when_none_valid():
    f = _hm().evaluate(_inp(any_sensor_valid=False))
    assert f.stale_sensor


def test_low_battery():
    f = _hm().evaluate(_inp(battery_v=13.8))
    assert f.low_battery and not f.critical_battery


def test_critical_battery():
    f = _hm().evaluate(_inp(battery_v=13.0))
    assert f.critical_battery and f.low_battery


def test_link_loss():
    f = _hm().evaluate(_inp(last_link_ok_s=5.0))     # 5 s > 3 s timeout
    assert f.link_loss


def test_loop_overrun():
    f = _hm().evaluate(_inp(loop_duration_s=0.09))   # > 0.05*1.25
    assert f.loop_overrun


def test_any_fault_only_critical():
    f = _hm().evaluate(_inp(battery_v=13.0))
    assert f.any_fault()
    f2 = _hm().evaluate(_inp(last_link_ok_s=0.0))     # sadece link loss
    assert not f2.any_fault()
