"""Titreşim/gürültü dayanıklılığı — FRR §4.2 yazılım analoğu (REQ-TEST-005 sim).

NOT: Gerçek 10G şok / 150–200 Hz titreşim masası testi FİZİKSEL ekipman gerektirir
ve bu ortamda çalıştırılamaz (bkz. docs/FRR_TEST_PROCEDURES.md). Bu testler,
şartname §4.2'nin YAZILIM gereksinimini doğrular: "titreşim testi sırasında veri
iletimi KESİNTİSİZ sürmelidir." Ölçülen sistem özellikleri:
  1. Gürültü altında telemetri üretimi kesintisiz sürer (1 Hz korunur).
  2. APAM YANLIŞ tetiklenmez (16 m/s × 10 sn kesintisiz kuralı gürültüye bağışık).
  3. Görev tamamlanır (RECOVERY'ye ulaşır).
  4. Yönelim kestirimi makul aralıkta kalır.
"""
from config.default import ControlConfig, get_config, with_overrides
from src.app.main import SimClock, build_and_run
from src.common.clock import FakeClock
from src.control.estimator import StateEstimator
from src.drivers.flight_profile import FlightProfile
from src.drivers.mock_sensors import MockBarometer, MockGps, MockImu
from src.state_machine.flight_state_machine import FlightPhase

P0 = 101325.0


def _cfg(tmp_path):
    base = get_config()
    paths = base.paths.__class__(
        run_dir=str(tmp_path),
        persistence_file=str(tmp_path / "state.json"),
        telemetry_csv=str(tmp_path / "tlm.csv"),
        s2d_csv=str(tmp_path / "s2d.csv"),
        zirh_spill=str(tmp_path / "zirh.txt"),
        video_sd=str(tmp_path / "v.h264"),
        event_log=str(tmp_path / "e.log"),
    )
    return with_overrides(base, paths=paths)


def test_vibration_injects_noise():
    clk = FakeClock()
    prof = FlightProfile("nominal_descent")
    t = [30.0]
    baro = MockBarometer(clk, prof, lambda: t[0])
    baro.vibration = 1.0
    p_vib = baro.read().unwrap().pressure_pa
    baro.vibration = 0.0
    assert p_vib != baro.read().unwrap().pressure_pa   # gürültü gerçekten ekleniyor


def test_telemetry_continuous_under_vibration(tmp_path):
    """FRR §4.2: titreşim altında telemetri kesintisiz (1 Hz) üretilmeli."""
    cfg = _cfg(tmp_path)
    clean = build_and_run(cfg, max_cycles=4000, duration_s=180.0, clock=SimClock())
    cfg2 = _cfg(tmp_path / "vib")
    vib = build_and_run(cfg2, max_cycles=4000, duration_s=180.0, clock=SimClock(),
                        vibration=1.0)
    # titreşimli koşu, temiz koşuyla aynı paket sayısını üretir (kesinti yok)
    assert vib.packets == clean.packets
    assert vib.packets > 100


def test_no_false_apam_under_vibration(tmp_path):
    cfg = _cfg(tmp_path)
    s = build_and_run(cfg, max_cycles=4000, duration_s=180.0, clock=SimClock(),
                      vibration=1.0)
    assert not s.apam_triggered                 # gürültü APAM'ı tetiklemez (güvenlik)
    # Süre-tutmalı iniş tespiti sayesinde gürültü altında da görevi tamamlar.
    assert s.final_phase in (FlightPhase.LANDED, FlightPhase.RECOVERY)


def test_attitude_plausible_under_vibration():
    clk = FakeClock()
    prof = FlightProfile("nominal_descent")
    t = [0.0]
    baro = MockBarometer(clk, prof, lambda: t[0]); baro.vibration = 1.0
    imu = MockImu(clk, prof, lambda: t[0]); imu.vibration = 1.0
    gps = MockGps(clk, prof, lambda: t[0])
    est = StateEstimator(ControlConfig(), P0)
    for i in range(50):
        t[0] = 10.0 + i * 0.05
        out = est.update(baro.read(), imu.read(), gps.read(), dt=0.05)
        assert out.attitude_valid and abs(out.pitch_deg) < 180.0
