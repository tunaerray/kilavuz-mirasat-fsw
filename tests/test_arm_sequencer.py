"""SİGMA kol açma koreografisi testleri (REQ-CTRL-003)."""
from config.default import ControlConfig
from src.control.arm_sequencer import ArmDeploySequencer, ArmDeployState
from src.drivers.mock_actuators import MockArmMechanism


def _seq(duration=1.5, timeout=3.0):
    return ArmDeploySequencer(ControlConfig(arm_deploy_duration_s=duration,
                                            arm_deploy_timeout_s=timeout))


def test_first_update_commands_deploy():
    seq = _seq()
    arms = MockArmMechanism()
    st = seq.update(100.0, arms)
    assert st.state is ArmDeployState.DEPLOYING
    assert "DEPLOY_AND_LOCK" in arms.command_log      # komut verildi
    assert not st.complete


def test_completes_after_duration_when_locked():
    seq = _seq(duration=1.5)
    arms = MockArmMechanism()
    seq.update(100.0, arms)
    st = seq.update(101.0, arms)          # süre dolmadı
    assert st.state is ArmDeployState.DEPLOYING
    st = seq.update(101.6, arms)          # 1.6 s > 1.5 s ve kilitli
    assert st.state is ArmDeployState.LOCKED
    assert st.complete


def test_not_complete_before_duration():
    seq = _seq(duration=2.0)
    arms = MockArmMechanism()
    seq.update(100.0, arms)
    assert not seq.update(101.0, arms).complete


def test_timeout_faults_when_not_locked():
    seq = _seq(duration=1.5, timeout=3.0)
    arms = MockArmMechanism()
    seq.update(100.0, arms)
    # kilit geri bildirimini boz: mekanizma kilitlenmedi
    arms._locked = False
    st = seq.update(103.5, arms)          # 3.5 s > timeout, kilit yok
    assert st.state is ArmDeployState.FAULT
    assert seq.faulted and not seq.complete


def test_locked_state_is_stable():
    seq = _seq(duration=1.0)
    arms = MockArmMechanism()
    seq.update(100.0, arms)
    seq.update(101.5, arms)               # LOCKED
    st = seq.update(105.0, arms)          # sonraki çağrılar LOCKED kalır
    assert st.state is ArmDeployState.LOCKED and st.complete


def test_deploy_command_issued_once():
    seq = _seq()
    arms = MockArmMechanism()
    seq.update(100.0, arms)
    seq.update(101.0, arms)
    seq.update(101.6, arms)
    assert arms.command_log.count("DEPLOY_AND_LOCK") == 1   # tek komut
