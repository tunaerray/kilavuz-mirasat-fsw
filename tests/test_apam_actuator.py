"""
APAM aktüatörü testleri — EMERGENCY_APAM'a geçişte Pixhawk'a MAV_CMD_DO_PARACHUTE
(param1=2 RELEASE) gönderimi. Gerçek donanım/pymavlink OLMADAN, sahte (fake)
mavlink bağlantısıyla test edilir (REQ-SAFE / EKSİK-001).
"""
from config.default import AppConfig, RunProfile
from src.common.result import ErrorCode
from src.drivers.apam_actuator import (
    MAV_CMD_DO_PARACHUTE,
    MAV_RESULT_ACCEPTED,
    PARACHUTE_RELEASE,
    ApamActuator,
)
from src.state_machine.flight_state_machine import FlightPhase


class _FakeMav:
    """mavutil bağlantısının `.mav` alanı; command_long_send çağrılarını kaydeder."""

    def __init__(self) -> None:
        self.sent: list[tuple] = []

    def command_long_send(self, target_system, target_component, command,
                          confirmation, p1, p2, p3, p4, p5, p6, p7) -> None:
        self.sent.append((command, confirmation, p1, p2, p3, p4, p5, p6, p7))


class _FakeAck:
    def __init__(self, result: int) -> None:
        self.result = result


class FakeMavlinkConnection:
    """
    mavutil.mavlink_connection karşılığı sahte bağlantı. command_long_send
    argümanlarını `mav.sent` içinde tutar; recv_match önceden kurulmuş ACK'i döner
    (None → zaman aşımı simülasyonu).
    """

    def __init__(self, ack_result: int | None = MAV_RESULT_ACCEPTED) -> None:
        self.mav = _FakeMav()
        self.target_system = 1
        self.target_component = 1
        self._ack_result = ack_result
        self.recv_calls = 0

    def recv_match(self, type=None, blocking=False, timeout=None):
        self.recv_calls += 1
        if self._ack_result is None:
            return None                      # ACK gelmedi → zaman aşımı
        return _FakeAck(self._ack_result)


def _flight_config() -> AppConfig:
    """Gerçek komut yolunu test etmek için FLIGHT profili (sim değil)."""
    return AppConfig(profile=RunProfile.FLIGHT)


def _sim_config() -> AppConfig:
    return AppConfig()   # SIMULATION_ONLY (varsayılan)


def _drive_to_apam(act: ApamActuator) -> None:
    """Fazı normal akıştan EMERGENCY_APAM'a getirir (geçiş kenarı üretir)."""
    act.update(FlightPhase.ACTIVE_DESCENT)
    act.update(FlightPhase.EMERGENCY_APAM)


# ----------------------------------------------------------------- gerçek yol (FLIGHT)
def test_sends_do_parachute_on_apam_entry():
    conn = FakeMavlinkConnection()
    logs: list[str] = []
    act = ApamActuator(_flight_config(), log=logs.append,
                       connect_fn=lambda port, baud: conn)
    _drive_to_apam(act)

    assert len(conn.mav.sent) == 1           # tam bir kez gönderildi
    command, _conf, p1, *_ = conn.mav.sent[0]
    assert command == MAV_CMD_DO_PARACHUTE
    assert p1 == PARACHUTE_RELEASE           # param1=2 (RELEASE)
    assert act.fired


def test_command_sent_only_once_across_cycles():
    conn = FakeMavlinkConnection()
    act = ApamActuator(_flight_config(), connect_fn=lambda port, baud: conn)
    _drive_to_apam(act)
    # APAM fazında kalmaya devam → tekrar GÖNDERİLMEMELİ (latch)
    for _ in range(5):
        assert act.update(FlightPhase.EMERGENCY_APAM) is None
    assert len(conn.mav.sent) == 1


def test_no_command_without_apam_transition():
    conn = FakeMavlinkConnection()
    act = ApamActuator(_flight_config(), connect_fn=lambda port, baud: conn)
    for phase in (FlightPhase.BOOT, FlightPhase.ASCENT, FlightPhase.ACTIVE_DESCENT,
                  FlightPhase.FINAL_APPROACH, FlightPhase.LANDED):
        assert act.update(phase) is None
    assert conn.mav.sent == []
    assert not act.fired


def test_ack_accepted_returns_ok():
    conn = FakeMavlinkConnection(ack_result=MAV_RESULT_ACCEPTED)
    logs: list[str] = []
    act = ApamActuator(_flight_config(), log=logs.append,
                       connect_fn=lambda port, baud: conn)
    act.update(FlightPhase.ACTIVE_DESCENT)
    res = act.update(FlightPhase.EMERGENCY_APAM)
    assert res is not None and res.is_ok
    assert any("ACCEPTED" in line for line in logs)


def test_ack_failed_returns_error():
    conn = FakeMavlinkConnection(ack_result=1)   # != ACCEPTED
    logs: list[str] = []
    act = ApamActuator(_flight_config(), log=logs.append,
                       connect_fn=lambda port, baud: conn)
    act.update(FlightPhase.ACTIVE_DESCENT)
    res = act.update(FlightPhase.EMERGENCY_APAM)
    assert res is not None and res.is_err and res.code is ErrorCode.IO_ERROR
    assert any("REDDEDİLDİ" in line for line in logs)


def test_ack_timeout_returns_error():
    conn = FakeMavlinkConnection(ack_result=None)   # ACK hiç gelmez
    logs: list[str] = []
    act = ApamActuator(_flight_config(), log=logs.append,
                       connect_fn=lambda port, baud: conn)
    act.update(FlightPhase.ACTIVE_DESCENT)
    res = act.update(FlightPhase.EMERGENCY_APAM)
    assert res is not None and res.is_err and res.code is ErrorCode.TIMEOUT
    assert any("zaman aşımı" in line for line in logs)


def test_connection_failure_is_explicit_not_crash():
    def _boom(port, baud):
        raise RuntimeError("port yok")

    logs: list[str] = []
    act = ApamActuator(_flight_config(), log=logs.append, connect_fn=_boom)
    act.update(FlightPhase.ACTIVE_DESCENT)
    res = act.update(FlightPhase.EMERGENCY_APAM)
    assert res is not None and res.is_err and res.code is ErrorCode.IO_ERROR
    assert act.fired            # latch: hata olsa da tekrar denenmez


# ---------------------------------------------------------------------- sim yolu
def test_simulation_does_not_send_real_command():
    conn = FakeMavlinkConnection()
    logs: list[str] = []
    act = ApamActuator(_sim_config(), log=logs.append,
                       connect_fn=lambda port, baud: conn)
    act.update(FlightPhase.ACTIVE_DESCENT)
    res = act.update(FlightPhase.EMERGENCY_APAM)

    assert res is not None and res.is_ok
    assert conn.mav.sent == []                       # donanıma dokunulmadı
    assert act.fired
    assert any("SIM" in line for line in logs)
