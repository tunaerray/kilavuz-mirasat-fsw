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
        s2d_csv=str(tmp_path / "TMUY2026_947450_S2D.csv"),
        zirh_spill=str(tmp_path / "TMUY2026_947450_ZIRH.txt"),
        video_sd=str(tmp_path / "TMUY2026_947450_VIDEO.h264"),
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


def test_short_run_no_parachute(tmp_path):
    cfg = _cfg(tmp_path)
    assert cfg.is_simulation
    s = build_and_run(cfg, max_cycles=100, duration_s=None, clock=SimClock())
    # kısa nominal koşuda (henüz ayrılma yok) paraşüt açılmamalı
    assert not s.parachute_deployed


# --- Aşama 2: kontrol & navigasyon entegrasyonu ---

def test_active_descent_arms_motors_and_applies_throttle(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=4000, duration_s=180.0, clock=SimClock())
    assert s.motors_ever_armed          # aktif iniş fazında motorlar arm edildi
    assert s.max_throttle > 0.0         # throttle uygulandı
    assert not s.motor_fault_detected   # sağlıklı motorlarda arıza yok


def test_motor_fault_injection_detected(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=4000, duration_s=180.0, clock=SimClock(),
                      motor_fault_factor=0.2)
    assert s.motor_fault_detected       # düşük RPM → motor arıza tespiti (REQ-SAFE-010)


def test_nominal_no_false_apam_with_fusion(tmp_path):
    # Füzyon tabanlı kestirim nominal profilde APAM'ı yanlış tetiklememeli
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=4000, duration_s=180.0, clock=SimClock())
    assert not s.apam_triggered
    assert s.final_phase in (FlightPhase.LANDED, FlightPhase.RECOVERY)


def test_pitch_roll_yaw_in_telemetry_from_fusion(tmp_path):
    # Telemetri yönelim alanları füzyon kestiriminden dolar (0 değil)
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=200, duration_s=None, clock=SimClock())
    parts = s.last_telemetry.split(",")
    yaw = float(parts[14])
    assert yaw != 0.0


# --- Aşama 3: görev & bonus servisleri ---

def test_hover_completes_in_nominal(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=4000, duration_s=200.0, clock=SimClock())
    assert s.hover_completed              # BONUS-1 askı yapıldı ve tamamlandı


def test_buzzer_on_and_telemetry_terminates_after_landing(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=4000, duration_s=200.0, clock=SimClock())
    assert s.final_phase in (FlightPhase.LANDED, FlightPhase.RECOVERY)
    assert s.buzzer_on                    # Gereksinim-28
    assert s.telemetry_terminated         # iniş sonrası pencere kapandı


def test_s2d_command_records_and_telemetry_field(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=4000, duration_s=120.0, clock=SimClock(),
                      commands=[(60.0, "2R0G1B")])
    assert s.commands_handled == 1
    assert s.rhrhrh_last == "2R0G1B"
    # SD kaydı oluştu
    sd = (tmp_path / "TMUY2026_947450_S2D.csv").read_text(encoding="utf-8")
    assert "2R0G1B" in sd
    # telemetri alanı 16 (0-indeks 15) RHRHRH ile dolu
    assert s.last_telemetry.split(",")[15] == "2R0G1B"


def test_manual_apam_command_triggers_apam(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=4000, duration_s=200.0, clock=SimClock(),
                      commands=[(100.0, "APAM")])   # ~600 m'de manuel APAM
    assert s.apam_triggered
    assert s.parachute_deployed


def test_invalid_command_ignored_run_continues(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=300, duration_s=None, clock=SimClock(),
                      commands=[(2.0, "LAUNCH")])   # bilinmeyen komut
    assert s.commands_handled == 0                  # işlenmedi ama koşu sürdü
    assert s.cycles == 300


# --- Aşama 4: haberleşme & kayıt ---

def test_zirh_buffers_then_forwards_after_jam(tmp_path):
    """Karıştırma bölgesinde tamponla, çıkınca geri-aktar; kayıp yok (BONUS-3)."""
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=4000, duration_s=200.0, clock=SimClock(),
                      jam_window=(80.0, 110.0))
    assert s.zirh_buffered > 0            # kesinti sırasında tamponlandı
    assert s.zirh_backlog == 0            # bölgeden çıkınca tamamen boşaldı
    assert s.zirh_sent == s.packets       # üretilen tüm paketler iletildi (kayıp yok)
    # SD spill dosyası oluştu ve CRC çerçeveli satır içeriyor
    spill = (tmp_path / "TMUY2026_947450_ZIRH.txt").read_text(encoding="utf-8")
    assert "*" in spill                   # CRC çerçevesi


def test_no_jam_no_buffering(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=300, duration_s=None, clock=SimClock())
    assert s.zirh_buffered == 0           # link hep açık → tamponlamaya gerek yok
    assert s.zirh_backlog == 0


def test_video_records_and_streams(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=200, duration_s=None, clock=SimClock())
    # 200 çevrim * 0.05 s = 10 s → 30 fps ile ~300 kare
    assert s.video_recorded > 0
    assert s.video_streamed == s.video_recorded   # jamming yok → hepsi akıtıldı
    assert s.video_dropped_stream == 0


def test_video_recording_continues_during_jam(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=4000, duration_s=200.0, clock=SimClock(),
                      jam_window=(80.0, 110.0))
    assert s.video_dropped_stream > 0     # karıştırma sırasında akış düştü
    # kayıt akış düşse bile sürdü: kaydedilen > akıtılan
    assert s.video_recorded > s.video_streamed


# --- Aşama 5: preflight & FRR ---

def test_preflight_go_in_nominal(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=10, duration_s=None, clock=SimClock())
    assert s.preflight_go                 # nominal simülasyonda uçuşa hazır (GO)
