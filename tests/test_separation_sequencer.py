"""Taşıyıcı→görev yükü ayrılma koreografisi testleri (2 zıt servo + geri bildirim)."""
from config.default import ControlConfig
from src.control.separation_sequencer import SeparationSequencer, SeparationState
from src.drivers.mock_actuators import MockSeparationMechanism


def _seq(duration=1.0, timeout=2.5):
    return SeparationSequencer(ControlConfig(separation_duration_s=duration,
                                             separation_timeout_s=timeout))


def test_first_update_commands_release_both_servos():
    seq = _seq()
    sep = MockSeparationMechanism()
    st = seq.update(50.0, sep)
    assert st.state is SeparationState.RELEASING
    assert "RELEASE" in sep.command_log         # iki servoya eşzamanlı komut verildi
    assert sep.left.position.name == "OPEN" and sep.right.position.name == "OPEN"
    assert not st.complete


def test_completes_after_duration_with_feedback():
    seq = _seq(duration=1.0)
    sep = MockSeparationMechanism()
    seq.update(50.0, sep)
    st = seq.update(50.5, sep)                   # süre dolmadı
    assert st.state is SeparationState.RELEASING
    st = seq.update(51.1, sep)                   # 1.1 s > 1.0 s ve geri bildirim var
    assert st.state is SeparationState.RELEASED
    assert st.complete


def test_not_complete_before_duration():
    seq = _seq(duration=2.0)
    sep = MockSeparationMechanism()
    seq.update(50.0, sep)
    assert not seq.update(51.0, sep).complete


def test_timeout_faults_when_no_feedback():
    seq = _seq(duration=1.0, timeout=2.5)
    sep = MockSeparationMechanism()
    seq.update(50.0, sep)
    # ayrılma geri bildirimini boz: mikroswitch onayı gelmedi
    sep._released = False
    st = seq.update(52.6, sep)                   # 2.6 s > timeout, geri bildirim yok
    assert st.state is SeparationState.FAULT
    assert seq.faulted and not seq.complete


def test_released_state_is_stable():
    seq = _seq(duration=1.0)
    sep = MockSeparationMechanism()
    seq.update(50.0, sep)
    seq.update(51.1, sep)                        # RELEASED
    st = seq.update(55.0, sep)                   # sonraki çağrılar RELEASED kalır
    assert st.state is SeparationState.RELEASED and st.complete


def test_release_command_issued_once():
    seq = _seq()
    sep = MockSeparationMechanism()
    seq.update(50.0, sep)
    seq.update(50.5, sep)
    seq.update(51.1, sep)
    assert sep.command_log.count("RELEASE") == 1   # tek komut (idempotent)
