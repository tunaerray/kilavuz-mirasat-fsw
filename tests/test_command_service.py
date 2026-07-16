"""Komut servisi testleri (Gereksinim-7/10, BONUS-2 yönlendirme)."""
import pytest

from src.common.result import ErrorCode
from src.drivers.mock_sensors import MockIotLink
from src.services.command_service import CommandKind, CommandService
from src.services.s2d_iot import S2dIotService


@pytest.fixture
def svc(tmp_path):
    iot = MockIotLink()
    s2d = S2dIotService(iot, str(tmp_path / "s2d.csv"))
    return CommandService(s2d), iot


def test_manual_separation_latches(svc):
    cs, _ = svc
    assert not cs.manual_separation_requested
    r = cs.handle("SEP")
    assert r.is_ok and r.unwrap().kind is CommandKind.MANUAL_SEPARATION
    assert cs.manual_separation_requested


def test_manual_apam_latches(svc):
    cs, _ = svc
    r = cs.handle("MANUAL_APAM")
    assert r.is_ok and r.unwrap().kind is CommandKind.MANUAL_APAM
    assert cs.manual_apam_requested


def test_latch_persists(svc):
    cs, _ = svc
    cs.handle("SEP")
    cs.handle("2R0G1B")            # araya başka komut
    assert cs.manual_separation_requested   # latch kalıcı


def test_rhrhrh_routed_to_s2d(svc):
    cs, iot = svc
    r = cs.handle("2R0G1B")
    assert r.is_ok and r.unwrap().kind is CommandKind.S2D_IOT
    assert iot.forwarded == ["2R0G1B"]


def test_invalid_rhrhrh_rejected(svc):
    cs, iot = svc
    r = cs.handle("2X0G1B")       # 6 karakter ama geçersiz
    assert r.is_err and r.code is ErrorCode.INVALID_DATA
    assert iot.forwarded == []


def test_unknown_command_errors(svc):
    cs, _ = svc
    assert cs.handle("LAUNCH").code is ErrorCode.INVALID_DATA
    assert cs.handle("").code is ErrorCode.INVALID_DATA


def test_case_insensitive(svc):
    cs, _ = svc
    assert cs.handle("sep").is_ok
    assert cs.manual_separation_requested


def test_handled_count(svc):
    cs, _ = svc
    cs.handle("SEP")
    cs.handle("APAM")
    cs.handle("2R0G1B")
    assert cs.handled_count == 3
