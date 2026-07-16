"""Alçalma kontrolcüsü testleri (REQ-CTRL-002/005, Gereksinim-14)."""
from config.default import ControlConfig, MissionConfig
from src.control.descent_controller import DescentController
from src.state_machine.flight_state_machine import FlightPhase

HOVER = ControlConfig().hover_throttle_estimate   # 0.70


def _ctrl():
    return DescentController(ControlConfig(), MissionConfig())


def test_on_target_holds_hover_throttle():
    c = _ctrl()
    # aktif iniş, hız tam hedefte (9 m/s) → throttle ~ hover
    cmd = c.compute(FlightPhase.ACTIVE_DESCENT, vertical_speed_mps=9.0,
                    altitude_m=500.0, dt=0.05)
    assert cmd.active
    assert abs(cmd.throttle - HOVER) < 0.02
    assert cmd.target_speed_mps == 9.0


def test_too_fast_increases_throttle():
    c = _ctrl()
    cmd = c.compute(FlightPhase.ACTIVE_DESCENT, vertical_speed_mps=15.0,
                    altitude_m=500.0, dt=0.05)
    assert cmd.throttle > HOVER      # daha fazla itiş → inişi yavaşlat


def test_too_slow_decreases_throttle():
    c = _ctrl()
    cmd = c.compute(FlightPhase.ACTIVE_DESCENT, vertical_speed_mps=3.0,
                    altitude_m=500.0, dt=0.05)
    assert cmd.throttle < HOVER


def test_throttle_clamped_0_1():
    c = _ctrl()
    fast = c.compute(FlightPhase.ACTIVE_DESCENT, 100.0, 500.0, 0.05)
    slow = c.compute(FlightPhase.ACTIVE_DESCENT, -100.0, 500.0, 0.05)
    assert 0.0 <= fast.throttle <= 1.0
    assert 0.0 <= slow.throttle <= 1.0


def test_hovering_target_zero():
    c = _ctrl()
    cmd = c.compute(FlightPhase.HOVERING, vertical_speed_mps=0.3,
                    altitude_m=200.0, dt=0.05)
    assert cmd.active
    assert cmd.target_speed_mps == 0.0
    assert not cmd.boost


def test_final_approach_boost_and_slower_target():
    c = _ctrl()
    cmd = c.compute(FlightPhase.FINAL_APPROACH, vertical_speed_mps=9.0,
                    altitude_m=40.0, dt=0.05)
    assert cmd.boost
    assert cmd.target_speed_mps == ControlConfig().final_approach_speed_mps
    # hedef daha yavaş, mevcut daha hızlı → daha çok throttle
    assert cmd.throttle > HOVER


def test_low_altitude_forces_final_target_even_in_active():
    c = _ctrl()
    # ACTIVE_DESCENT ama irtifa < 50 m → son yaklaşma hedefine geç
    cmd = c.compute(FlightPhase.ACTIVE_DESCENT, vertical_speed_mps=9.0,
                    altitude_m=30.0, dt=0.05)
    assert cmd.boost
    assert cmd.target_speed_mps == ControlConfig().final_approach_speed_mps


def test_passive_phase_inactive():
    c = _ctrl()
    for ph in (FlightPhase.CARRIER_DESCENT, FlightPhase.SEPARATION,
               FlightPhase.READY_TO_FLY, FlightPhase.EMERGENCY_APAM):
        cmd = c.compute(ph, vertical_speed_mps=14.0, altitude_m=800.0, dt=0.05)
        assert not cmd.active
        assert cmd.throttle == 0.0


def test_pid_state_resets_on_passive():
    c = _ctrl()
    # aktifken integral biriktir
    for _ in range(10):
        c.compute(FlightPhase.ACTIVE_DESCENT, 20.0, 500.0, 0.05)
    # pasif faz → reset
    c.compute(FlightPhase.CARRIER_DESCENT, 14.0, 800.0, 0.05)
    # tekrar aktif, on-target → throttle hover'a yakın (birikim yok)
    cmd = c.compute(FlightPhase.ACTIVE_DESCENT, 9.0, 500.0, 0.05)
    assert abs(cmd.throttle - HOVER) < 0.05
