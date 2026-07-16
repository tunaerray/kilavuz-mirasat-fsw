"""Kalıcılık testleri: sayaç + RESTART senaryosu (REQ-TLM-003/004, REQ-TEST-002)."""
from src.common.clock import FakeClock
from src.services.persistence import PersistenceStore


def _store(tmp_path, clock):
    return PersistenceStore(str(tmp_path / "state.json"), clock)


def test_counter_starts_at_one(tmp_path):
    clock = FakeClock()
    s = _store(tmp_path, clock)
    s.load().unwrap()
    assert s.next_packet_number().unwrap() == 1
    assert s.next_packet_number().unwrap() == 2
    assert s.next_packet_number().unwrap() == 3


def test_next_before_load_errors(tmp_path):
    s = _store(tmp_path, FakeClock())
    assert s.next_packet_number().is_err


def test_restart_resumes_counter(tmp_path):
    """İşlemci yeniden başlarsa paket no kaldığı yerden devam eder (G-18)."""
    path = tmp_path / "state.json"
    c1 = FakeClock()
    s1 = PersistenceStore(str(path), c1)
    s1.load().unwrap()
    for _ in range(5):
        s1.next_packet_number().unwrap()
    assert s1.current_packet_number() == 5

    # --- yeniden başlatma: yeni store, yeni saat, AYNI dosya ---
    c2 = FakeClock()
    s2 = PersistenceStore(str(path), c2)
    s2.load().unwrap()
    assert s2.current_packet_number() == 5           # kaldığı yerden
    assert s2.next_packet_number().unwrap() == 6      # 6'dan devam
    assert s2.boot_count == 2


def test_mission_time_survives_restart(tmp_path):
    """Görev zamanı restart'a dayanır ve artmaya devam eder (G-17)."""
    path = tmp_path / "state.json"
    c1 = FakeClock()
    s1 = PersistenceStore(str(path), c1)
    s1.load().unwrap()
    c1.advance(30.0)
    s1.next_packet_number().unwrap()   # elapsed'i diske işler
    assert s1.mission_time_s() == 30.0

    # restart
    c2 = FakeClock()
    s2 = PersistenceStore(str(path), c2)
    s2.load().unwrap()
    assert s2.mission_time_s() == 30.0     # kaldığı yerden (birikmiş 30 s)
    c2.advance(10.0)
    assert s2.mission_time_s() == 40.0     # artmaya devam eder


def test_altitude_zero_ref_persists(tmp_path):
    path = tmp_path / "state.json"
    s1 = PersistenceStore(str(path), FakeClock())
    s1.load().unwrap()
    s1.set_altitude_zero_ref(101325.0)
    s2 = PersistenceStore(str(path), FakeClock())
    s2.load().unwrap()
    assert s2.altitude_zero_ref() == 101325.0


def test_atomic_file_written(tmp_path):
    path = tmp_path / "state.json"
    s = PersistenceStore(str(path), FakeClock())
    s.load().unwrap()
    s.next_packet_number().unwrap()
    assert path.exists()
    # geçici dosya kalmamalı
    assert not list(tmp_path.glob("*.tmp"))
