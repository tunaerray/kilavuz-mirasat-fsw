"""
Görevi        : SİGMA kol açma/kilitleme koreografisi. Ayrılma sonrası kolları
                komutla açar, mekanik hareket süresini modeller ve kilit geri
                bildirimini doğrulayarak aktif inişe geçişi bu tamamlanana kadar
                geciktirir.
Neden Gerekli : REQ-CTRL-003 + PDR SİGMA — kollar başlangıçta gövde içinde kapalı;
                ayrılma sonrası 90° açılıp kilitlenmeli. Tek-adımlık komut yerine
                zamanlı ve GERİ BİLDİRİMLİ bir dizi güvenlik açısından gereklidir
                (kilitlenmeyen kol = motor çalıştırma öncesi FAULT).
İlişkiler     : ARM_DEPLOY fazında ana döngü her çevrim update() çağırır; complete
                olana kadar ACTIVE_DESCENT'e geçiş yapılmaz. MockArmMechanism'i sürer.
Nasıl Test    : tests/test_arm_sequencer.py — komut, süre, kilit doğrulama, timeout
                FAULT, idempotent tamamlama.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from config.default import ControlConfig
from src.drivers.mock_actuators import MockArmMechanism


class ArmDeployState(Enum):
    IDLE = "IDLE"
    DEPLOYING = "DEPLOYING"    # komut verildi, mekanik hareket sürüyor
    LOCKED = "LOCKED"          # açıldı ve kilitlendi (tamam)
    FAULT = "FAULT"            # zaman aşımında kilitlenmedi


@dataclass
class ArmDeployStatus:
    state: ArmDeployState
    complete: bool
    elapsed_s: float


class ArmDeploySequencer:
    """
    Kol açma alt-durum makinesi. İlk update'te komutu verir; `arm_deploy_duration_s`
    boyunca DEPLOYING kalır; süre dolunca kilit geri bildirimini doğrular. Kilit
    yoksa `arm_deploy_timeout_s` sonunda FAULT'a düşer (motorlar çalıştırılmaz).
    """

    def __init__(self, config: ControlConfig) -> None:
        self._c = config
        self._state = ArmDeployState.IDLE
        self._start_s: float | None = None

    @property
    def state(self) -> ArmDeployState:
        return self._state

    @property
    def complete(self) -> bool:
        return self._state is ArmDeployState.LOCKED

    @property
    def faulted(self) -> bool:
        return self._state is ArmDeployState.FAULT

    def update(self, mission_time_s: float,
               arms: MockArmMechanism) -> ArmDeployStatus:
        c = self._c

        if self._state is ArmDeployState.IDLE:
            arms.deploy_and_lock()            # komutu ver (mekanik hareket başlar)
            self._start_s = mission_time_s
            self._state = ArmDeployState.DEPLOYING

        elapsed = 0.0 if self._start_s is None else max(0.0, mission_time_s - self._start_s)

        if self._state is ArmDeployState.DEPLOYING:
            if elapsed >= c.arm_deploy_duration_s and arms.deployed and arms.locked:
                self._state = ArmDeployState.LOCKED
            elif elapsed >= c.arm_deploy_timeout_s:
                # Süre doldu ve kilit doğrulanamadı → güvenli FAULT.
                self._state = ArmDeployState.FAULT

        return ArmDeployStatus(state=self._state, complete=self.complete,
                               elapsed_s=elapsed)
