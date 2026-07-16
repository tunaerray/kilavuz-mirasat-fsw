"""
Görevi        : Alçalma kontrolcüsü. Faz ve kestirilen dikey hıza göre hedef iniş
                hızını seçer ve PID ile motor throttle komutu üretir; aktif iniş
                (8–10 m/s), askı (BONUS-1, 0 m/s) ve son yaklaşma (son 50 m, daha
                yavaş + RPM artışı) modlarını yönetir.
Neden Gerekli : REQ-CTRL-002 (kontrollü 8–10 m/s), REQ-CTRL-005 (motor komut
                üretimi + endpoint limiti), Gereksinim-14 (son 50 m'de RPM artışı).
İlişkiler     : PidController kullanır; StateEstimator çıktısını okur; ürettiği
                ControlCommand ana döngü tarafından motorlara ve FlightControllerLink'e
                uygulanır (arm interlock ile). Sabitler ControlConfig'ten gelir.
Nasıl Test    : tests/test_descent_controller.py — hedef hız seçimi, hızlı inişte
                daha çok throttle, askıda hedef 0, son yaklaşma boost, pasif fazda
                pasiflik ve PID reset.
"""
from __future__ import annotations

from dataclasses import dataclass

from config.default import ControlConfig, MissionConfig
from src.control.pid import PidController, PidGains
from src.state_machine.flight_state_machine import FlightPhase

# Motor throttle'ın uygulanacağı aktif kontrol fazları.
_ACTIVE_PHASES = (
    FlightPhase.ACTIVE_DESCENT,
    FlightPhase.HOVERING,
    FlightPhase.FINAL_APPROACH,
)


@dataclass
class ControlCommand:
    """Bir çevrimin kontrol çıktısı (ana döngü uygular)."""

    active: bool            # motorlar arm edilip throttle uygulanmalı mı
    throttle: float         # 0..1
    target_speed_mps: float  # hedef iniş hızı (pozitif = iniş)
    boost: bool             # son yaklaşma RPM artışı devrede mi


class DescentController:
    """
    Dikey hız regülatörü. Fiziksel plant negatif kazançlıdır (throttle ↑ → iniş
    hızı ↓); bu yüzden hata, tırmanma hızı (=-iniş hızı) üzerinden tanımlanır ve
    PID çıkışı hover throttle etrafında bir delta olarak eklenir.
    """

    def __init__(self, control: ControlConfig, mission: MissionConfig) -> None:
        self._c = control
        self._m = mission
        self._pid = PidController(PidGains(
            kp=control.descent_kp, ki=control.descent_ki, kd=control.descent_kd,
            output_min=control.throttle_min - control.hover_throttle_estimate,
            output_max=control.throttle_max - control.hover_throttle_estimate,
            integral_min=control.descent_integral_min,
            integral_max=control.descent_integral_max,
        ))

    def _target_speed(self, phase: FlightPhase, altitude_m: float) -> tuple:
        """Faza (ve irtifaya) göre hedef iniş hızı ve boost bayrağı döndürür."""
        if phase is FlightPhase.HOVERING:
            return 0.0, False
        if phase is FlightPhase.FINAL_APPROACH or altitude_m <= self._m.final_approach_altitude_m:
            # Son 50 m: hasarsız iniş için daha yavaş hedef + RPM artışı.
            return self._c.final_approach_speed_mps, True
        return self._c.target_descent_speed_mps, False

    def reset(self) -> None:
        self._pid.reset()

    def compute(self, phase: FlightPhase, vertical_speed_mps: float,
                altitude_m: float, dt: float) -> ControlCommand:
        if phase not in _ACTIVE_PHASES:
            # Pasif fazlarda kontrol yok; motorlar Safe State'te kalır.
            self._pid.reset()
            return ControlCommand(active=False, throttle=0.0,
                                  target_speed_mps=0.0, boost=False)

        target, boost = self._target_speed(phase, altitude_m)

        # Negatif plant kazancı için tırmanma-hızı (climb) çerçevesinde regüle et:
        #   measurement' = -iniş hızı, setpoint' = -hedef hızı
        #   error' = descent_speed - target  (çok hızlı inişte pozitif → +throttle)
        delta = self._pid.update(setpoint=-target,
                                 measurement=-vertical_speed_mps, dt=dt)
        throttle = self._c.hover_throttle_estimate + delta
        throttle = min(self._c.throttle_max, max(self._c.throttle_min, throttle))

        return ControlCommand(active=True, throttle=throttle,
                              target_speed_mps=target, boost=boost)
