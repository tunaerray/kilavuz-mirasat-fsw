"""
Görevi        : Taşıyıcı→görev yükü AYRILMA koreografisi. İki zıt yönlü servoyu
                komutla EŞZAMANLI açar, mekanik ayrılma süresini modeller ve ayrılma
                geri bildirimini (mikroswitch) doğrulayarak ayrılmanın gerçekleştiğini
                onaylar; onaylanana kadar SEPARATION→ARM_DEPLOY geçişi yapılmaz.
Neden Gerekli : Fiziksel kurulum 2 zıt ayrılma servosu + geri bildirim içerir; FSW
                daha önce tek servo modelliyor ve "komut = onay" varsayıyordu. Ayrılma
                gerçekleşmeden kolların/kanatların açılması güvenlik riskidir; bu yüzden
                kol mekanizmasındaki kilit doğrulaması gibi geri bildirimli bir dizi şart.
İlişkiler     : CARRIER_DESCENT/SEPARATION fazında ana döngü her çevrim update() çağırır;
                complete olana dek separation_confirmed=True yapılmaz. MockSeparationMechanism'i sürer.
Nasıl Test    : tests/test_separation_sequencer.py — eşzamanlı komut, süre, geri
                bildirim doğrulama, timeout FAULT, idempotent tamamlama.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from config.default import ControlConfig
from src.drivers.mock_actuators import MockSeparationMechanism


class SeparationState(Enum):
    IDLE = "IDLE"
    RELEASING = "RELEASING"    # komut verildi, mekanik ayrılma sürüyor
    RELEASED = "RELEASED"      # ayrıldı ve geri bildirim doğrulandı (tamam)
    FAULT = "FAULT"            # zaman aşımında ayrılma doğrulanamadı


@dataclass
class SeparationStatus:
    state: SeparationState
    complete: bool
    elapsed_s: float


class SeparationSequencer:
    """
    Ayrılma alt-durum makinesi. İlk update'te iki servoyu EŞZAMANLI açar (komut);
    `separation_duration_s` boyunca RELEASING kalır; süre dolunca ayrılma geri
    bildirimini doğrular. Geri bildirim yoksa `separation_timeout_s` sonunda FAULT'a
    düşer (kollar açılmaz, iniş fazına geçilmez).
    """

    def __init__(self, config: ControlConfig) -> None:
        self._c = config
        self._state = SeparationState.IDLE
        self._start_s: float | None = None

    @property
    def state(self) -> SeparationState:
        return self._state

    @property
    def complete(self) -> bool:
        return self._state is SeparationState.RELEASED

    @property
    def faulted(self) -> bool:
        return self._state is SeparationState.FAULT

    def update(self, mission_time_s: float,
               separation: MockSeparationMechanism) -> SeparationStatus:
        c = self._c

        if self._state is SeparationState.IDLE:
            separation.release()              # iki zıt servoyu EŞZAMANLI aç
            self._start_s = mission_time_s
            self._state = SeparationState.RELEASING

        elapsed = 0.0 if self._start_s is None else max(0.0, mission_time_s - self._start_s)

        if self._state is SeparationState.RELEASING:
            if elapsed >= c.separation_duration_s and separation.released:
                self._state = SeparationState.RELEASED
            elif elapsed >= c.separation_timeout_s:
                # Süre doldu ve ayrılma geri bildirimi yok → güvenli FAULT.
                self._state = SeparationState.FAULT

        return SeparationStatus(state=self._state, complete=self.complete,
                                elapsed_s=elapsed)
