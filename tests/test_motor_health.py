"""Motor sağlık / arıza tespiti testleri (REQ-SAFE-010)."""
from config.default import ControlConfig
from src.services.motor_health import MotorHealthMonitor

MAXRPM = ControlConfig().motor_max_rpm


def _mon():
    return MotorHealthMonitor(ControlConfig())


def test_consistent_when_rpm_matches():
    m = _mon()
    r = m.update(commanded_throttle=0.7, actual_rpm=0.7 * MAXRPM, dt=0.1)
    assert r.consistent and not r.fault


def test_mismatch_accumulates_then_faults():
    m = _mon()
    # throttle 0.7 komut ama RPM neredeyse 0 (motor ölü)
    r = None
    for _ in range(20):   # 20 * 0.1 = 2 s > persist 1 s
        r = m.update(0.7, 0.05 * MAXRPM, dt=0.1)
    assert r.fault
    assert r.mismatch_timer_s >= ControlConfig().motor_fault_persist_s


def test_brief_mismatch_no_fault():
    m = _mon()
    for _ in range(5):    # 0.5 s < 1 s persist
        m.update(0.7, 0.05 * MAXRPM, dt=0.1)
    assert not m.fault


def test_low_throttle_not_checked():
    m = _mon()
    # rölanti altı: RPM 0 olsa bile arıza sayılmaz
    for _ in range(30):
        r = m.update(0.05, 0.0, dt=0.1)
    assert not r.fault and r.consistent


def test_recovery_resets_timer_before_fault():
    m = _mon()
    for _ in range(8):    # 0.8 s tutarsız (< 1 s)
        m.update(0.7, 0.05 * MAXRPM, dt=0.1)
    # RPM düzelir → sayaç sıfırlanır
    r = m.update(0.7, 0.7 * MAXRPM, dt=0.1)
    assert r.consistent and r.mismatch_timer_s == 0.0
    assert not m.fault


def test_fault_latches():
    m = _mon()
    for _ in range(20):
        m.update(0.7, 0.0, dt=0.1)
    assert m.fault
    # RPM düzelse bile arıza latch'lenir (güvenli taraf)
    r = m.update(0.7, 0.7 * MAXRPM, dt=0.1)
    assert r.fault


def test_within_tolerance_is_consistent():
    m = _mon()
    # %35 tolerans: beklenenin %70'i hâlâ tutarlı (0.65 eşiği)
    r = m.update(0.8, 0.7 * (0.8 * MAXRPM), dt=0.1)
    assert r.consistent and not r.fault
