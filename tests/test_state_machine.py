"""Durum makinesi testleri — faz geçişleri + statü 0..5 (REQ-TLM-007, CONFLICT-002)."""
from config.default import MissionConfig
from src.mission.context import FlightContext
from src.state_machine.flight_state_machine import FlightPhase, FlightStateMachine


def _ctx(**kw):
    base = dict(mission_time_s=0.0, altitude_m=0.0, descent_speed_mps=0.0,
                ascending=False, gps_valid=True)
    base.update(kw)
    return FlightContext(**base)


def _sm():
    return FlightStateMachine(MissionConfig())


def test_status_code_mapping_matches_spec():
    # CONFLICT-002: Şartname esas — 2=Model Uydu İniş, 3=Ayrılma
    sm = _sm()
    mapping = {
        FlightPhase.READY_TO_FLY: 0,
        FlightPhase.ASCENT: 1,
        FlightPhase.CARRIER_DESCENT: 2,
        FlightPhase.SEPARATION: 3,
        FlightPhase.ARM_DEPLOY: 3,
        FlightPhase.ACTIVE_DESCENT: 4,
        FlightPhase.HOVERING: 4,
        FlightPhase.FINAL_APPROACH: 4,
        FlightPhase.LANDED: 5,
        FlightPhase.RECOVERY: 5,
    }
    for phase, code in mapping.items():
        sm._phase = phase
        assert int(sm.status_code()) == code


def test_boot_to_ready():
    sm = _sm()
    assert sm.phase is FlightPhase.BOOT
    sm.update(_ctx())
    assert sm.phase is FlightPhase.READY_TO_FLY


def test_full_nominal_sequence():
    sm = _sm()
    sm.update(_ctx())                                    # BOOT->READY
    sm.update(_ctx(ascending=True, altitude_m=100))      # READY->ASCENT
    assert sm.phase is FlightPhase.ASCENT
    sm.update(_ctx(ascending=False, altitude_m=1500, descent_speed_mps=14))
    assert sm.phase is FlightPhase.CARRIER_DESCENT
    assert int(sm.status_code()) == 2
    sm.update(_ctx(altitude_m=1000, descent_speed_mps=14))  # ~1000m -> SEPARATION
    assert sm.phase is FlightPhase.SEPARATION
    assert int(sm.status_code()) == 3
    sm.update(_ctx(altitude_m=995, separation_confirmed=True))
    assert sm.phase is FlightPhase.ARM_DEPLOY
    sm.update(_ctx(altitude_m=990, separation_confirmed=True, arms_deployed=True))
    assert sm.phase is FlightPhase.ACTIVE_DESCENT
    assert int(sm.status_code()) == 4


def test_hovering_holds_for_duration_then_resumes():
    """BONUS-1: 200 m'de yaklaşık 10 sn askı, sonra inişe devam (zamanlayıcı)."""
    sm = _sm()
    sm._phase = FlightPhase.ACTIVE_DESCENT
    # 200 m'ye ulaş → HOVERING (t=100)
    sm.update(_ctx(mission_time_s=100.0, altitude_m=200, separation_confirmed=True,
                   arms_deployed=True, descent_speed_mps=0.3))
    assert sm.phase is FlightPhase.HOVERING
    # süre dolmadan askıda kalır (irtifa ~200 sabit, hız ~0)
    sm.update(_ctx(mission_time_s=105.0, altitude_m=200, separation_confirmed=True,
                   descent_speed_mps=0.2))
    assert sm.phase is FlightPhase.HOVERING
    assert abs(sm.hover_elapsed_s(105.0) - 5.0) < 1e-6
    # 10 sn dolunca inişe devam
    sm.update(_ctx(mission_time_s=110.5, altitude_m=200, separation_confirmed=True,
                   descent_speed_mps=0.2))
    assert sm.phase is FlightPhase.ACTIVE_DESCENT
    assert sm.hover_complete


def test_hovering_not_reentered_after_complete():
    sm = _sm()
    sm._phase = FlightPhase.ACTIVE_DESCENT
    sm.update(_ctx(mission_time_s=100.0, altitude_m=200, separation_confirmed=True,
                   arms_deployed=True, descent_speed_mps=0.3))
    sm.update(_ctx(mission_time_s=111.0, altitude_m=200, separation_confirmed=True,
                   descent_speed_mps=0.2))
    assert sm.phase is FlightPhase.ACTIVE_DESCENT
    # tekrar 200 m civarında olsa bile yeniden askıya girmez
    sm.update(_ctx(mission_time_s=112.0, altitude_m=200, separation_confirmed=True,
                   descent_speed_mps=0.2))
    assert sm.phase is FlightPhase.ACTIVE_DESCENT


def test_final_approach_and_land():
    sm = _sm()
    sm._phase = FlightPhase.ACTIVE_DESCENT
    sm._hover_complete = True    # askı tamamlanmış varsay
    sm.update(_ctx(altitude_m=40, separation_confirmed=True, descent_speed_mps=9))
    assert sm.phase is FlightPhase.FINAL_APPROACH
    sm.update(_ctx(altitude_m=1.0, separation_confirmed=True, descent_speed_mps=0.2))
    assert sm.phase is FlightPhase.LANDED
    assert int(sm.status_code()) == 5
    sm.update(_ctx(altitude_m=0.0))
    assert sm.phase is FlightPhase.RECOVERY


def test_apam_forces_emergency_phase():
    sm = _sm()
    sm._phase = FlightPhase.ACTIVE_DESCENT
    sm.update(_ctx(altitude_m=300, separation_confirmed=True, apam_active=True,
                   descent_speed_mps=20))
    assert sm.phase is FlightPhase.EMERGENCY_APAM
    assert int(sm.status_code()) == 4       # hâlâ görev yükü iniş


def test_fault_status_before_separation_is_ready():
    sm = _sm()
    sm._phase = FlightPhase.ASCENT
    sm.to_fault(_ctx(separation_confirmed=False))
    assert sm.phase is FlightPhase.FAULT
    assert int(sm.status_code()) == 0


def test_manual_separation_command_transitions():
    sm = _sm()
    sm._phase = FlightPhase.CARRIER_DESCENT
    sm.update(_ctx(altitude_m=1050, manual_separation_cmd=True, descent_speed_mps=13))
    assert sm.phase is FlightPhase.SEPARATION
