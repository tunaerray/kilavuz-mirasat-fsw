"""
Görevi        : Kurtarma yöneticisi. İniş sonrası buzzer'ı çalıştırır ve iniş
                sonrası telemetri penceresini yönetir; pencere dolunca telemetri
                iletimini otomatik sonlandırır.
Neden Gerekli : Gereksinim-28 (kurtarma sesli ikazı) + Gereksinim-27/§1.3
                (iniş sonrası telemetri). CONFLICT-001: pencere süresi config'ten
                gelir (varsayılan 10 sn; 60 sn'ye çekilebilir).
İlişkiler     : Ana döngü her çevrim update() çağırır; buzzer (HAL) inişte açılır;
                telemetry_active bayrağı telemetri gönderimini kontrol eder. Faz
                bilgisini FlightStateMachine'den (LANDED/RECOVERY) alır.
Nasıl Test    : tests/test_recovery.py — iniş algılama, buzzer açma, pencere sonu
                telemetri durdurma, iniş öncesi davranış.
"""
from __future__ import annotations

from dataclasses import dataclass

from config.default import MissionConfig
from src.hal.interfaces import Buzzer
from src.state_machine.flight_state_machine import FlightPhase

_LANDED_PHASES = (FlightPhase.LANDED, FlightPhase.RECOVERY)


@dataclass
class RecoveryStatus:
    landed: bool
    buzzer_on: bool
    telemetry_active: bool
    seconds_since_landing: float


class RecoveryManager:
    """
    İniş sonrası davranışı yönetir. İlk iniş anını kaydeder; buzzer'ı açar ve
    kurtarılana kadar (sim'de koşu sonuna kadar) açık tutar. Telemetri, iniş
    anından itibaren `post_landing_telemetry_s` boyunca aktif kalır, sonra durur.
    """

    def __init__(self, mission: MissionConfig) -> None:
        self._m = mission
        self._landing_time_s: float | None = None

    @property
    def landed(self) -> bool:
        return self._landing_time_s is not None

    def update(self, phase: FlightPhase, mission_time_s: float,
               buzzer: Buzzer) -> RecoveryStatus:
        # İniş fazına ilk giriş anını kilitle.
        if self._landing_time_s is None and phase in _LANDED_PHASES:
            self._landing_time_s = mission_time_s

        if self._landing_time_s is None:
            # Henüz inilmedi: buzzer kapalı, telemetri aktif.
            return RecoveryStatus(landed=False, buzzer_on=False,
                                  telemetry_active=True, seconds_since_landing=0.0)

        elapsed = max(0.0, mission_time_s - self._landing_time_s)
        # Kurtarma ikazı: iniş sonrası çalmaya devam eder (Gereksinim-28).
        buzzer.on()
        # İniş sonrası telemetri penceresi (CONFLICT-001).
        telemetry_active = elapsed <= self._m.post_landing_telemetry_s
        return RecoveryStatus(landed=True, buzzer_on=buzzer.is_on,
                              telemetry_active=telemetry_active,
                              seconds_since_landing=elapsed)
