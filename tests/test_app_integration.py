"""Ana döngü entegrasyon testleri (REQ-SW-003/006, REQ-TLM-005)."""
from config.default import get_config, with_overrides
from src.app.main import SimClock, build_and_run
from src.state_machine.flight_state_machine import FlightPhase


def _cfg(tmp_path):
    base = get_config()
    paths = base.paths.__class__(
        run_dir=str(tmp_path),
        persistence_file=str(tmp_path / "state.json"),
        telemetry_csv=str(tmp_path / "tlm.csv"),
        event_log=str(tmp_path / "events.log"),
    )
    return with_overrides(base, paths=paths)


def test_bounded_run_respects_max_cycles(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=50, duration_s=None, clock=SimClock())
    assert s.cycles == 50


def test_run_produces_packets_and_csv(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=100, duration_s=None, clock=SimClock())
    assert s.packets > 0
    csv = (tmp_path / "tlm.csv").read_text(encoding="utf-8").splitlines()
    # başlık + birim + en az 1 veri satırı
    assert csv[0].startswith("PAKET_NUMARASI")
    assert csv[1].split(",")[4] == "Pa"
    assert len(csv) >= 3
    # her veri satırı 17 alan
    assert len(csv[2].split(",")) == 17


def test_telemetry_is_1hz(tmp_path):
    # 20 Hz döngü, 1 Hz telemetri: ~100 çevrim (5 s) → ~5-6 paket
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=100, duration_s=None, clock=SimClock())
    assert 4 <= s.packets <= 7


def test_deterministic_repeatable(tmp_path):
    cfg1 = _cfg(tmp_path / "a")
    cfg2 = _cfg(tmp_path / "b")
    s1 = build_and_run(cfg1, max_cycles=200, duration_s=None, clock=SimClock())
    s2 = build_and_run(cfg2, max_cycles=200, duration_s=None, clock=SimClock())
    assert s1.last_telemetry == s2.last_telemetry
    assert s1.final_status == s2.final_status


def test_nominal_reaches_descent_or_landing(tmp_path):
    cfg = _cfg(tmp_path)
    # Nominal profil t≈172 s'de yere iner. 20 Hz → ~3600 çevrim.
    s = build_and_run(cfg, max_cycles=4000, duration_s=180.0, clock=SimClock())
    assert s.final_phase in (FlightPhase.LANDED, FlightPhase.RECOVERY,
                             FlightPhase.FINAL_APPROACH, FlightPhase.ACTIVE_DESCENT)
    assert not s.apam_triggered      # nominal profilde APAM yok


def test_runaway_profile_triggers_apam(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=2000, duration_s=60.0, clock=SimClock(),
                      profile_name="runaway_descent")
    assert s.apam_triggered
    assert s.parachute_deployed


def test_safe_state_no_motor_output_in_simulation(tmp_path):
    # SIMULATION_ONLY: koşu boyunca motorlar hiç arm edilmez (Aşama 1'de kontrol yok)
    cfg = _cfg(tmp_path)
    assert cfg.is_simulation
    s = build_and_run(cfg, max_cycles=100, duration_s=None, clock=SimClock())
    # nominal koşuda paraşüt açılmamalı
    assert not s.parachute_deployed
