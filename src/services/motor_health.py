"""
Görevi        : Motor sağlık izleyici. Komut edilen throttle'dan beklenen RPM ile
                uçuş kontrol kartından gelen gerçek RPM'i karşılaştırır; kalıcı
                tutarsızlığı motor arızası olarak işaretler.
Neden Gerekli : REQ-SAFE-010 + ANA_PROMPT APAM konsepti — "Motor PWM komutları ile
                RPM geri bildirimleri karşılaştırılır; motorlar hızı düşüremiyorsa
                APAM devreye girer." Motor arızası, APAM için CORROBORATING kanıttır
                (tek başına tetiklemez; 16 m/s × 10 sn kuralı esas kalır).
İlişkiler     : SimulatedFlightControllerLink'ten RPM okur; DescentController'ın
                komut throttle'ını alır; çıktısı FlightContext'e ve failsafe'e girer.
Nasıl Test    : tests/test_motor_health.py — tutarlı/tutarsız, kalıcılık zamanı,
                düşük throttle'da denetim yok, sıfırlama.
"""
from __future__ import annotations

from dataclasses import dataclass

from config.default import ControlConfig


@dataclass
class MotorHealthReport:
    consistent: bool
    fault: bool
    expected_rpm: float
    actual_rpm: float
    mismatch_timer_s: float


class MotorHealthMonitor:
    """
    Deterministik motor tutarlılık izleyici. dt görev zamanı deltası olarak
    dışarıdan verilir. Yalnız throttle anlamlı (rölanti üstü) iken denetler:
    rölantide RPM doğal olarak düşüktür, yanlış pozitif üretmemek için.
    """

    _THROTTLE_FLOOR = 0.15   # bu throttle altında RPM denetimi yapılmaz

    def __init__(self, config: ControlConfig) -> None:
        self._c = config
        self._mismatch_timer_s = 0.0
        self._fault_latched = False

    @property
    def fault(self) -> bool:
        return self._fault_latched

    @property
    def mismatch_timer_s(self) -> float:
        return self._mismatch_timer_s

    def reset(self) -> None:
        self._mismatch_timer_s = 0.0
        self._fault_latched = False

    def update(self, commanded_throttle: float, actual_rpm: float,
               dt: float) -> MotorHealthReport:
        c = self._c
        expected = commanded_throttle * c.motor_max_rpm
        threshold = expected * (1.0 - c.motor_rpm_tolerance)

        if commanded_throttle < self._THROTTLE_FLOOR:
            # Rölanti/kapalı: denetim yok, sayaç yavaşça sıfırlanır.
            consistent = True
            self._mismatch_timer_s = 0.0
        else:
            consistent = actual_rpm >= threshold
            if consistent:
                self._mismatch_timer_s = 0.0
            else:
                self._mismatch_timer_s += max(0.0, dt)

        if self._mismatch_timer_s >= c.motor_fault_persist_s:
            self._fault_latched = True   # latch: bir kez arıza görülünce kalır

        return MotorHealthReport(
            consistent=consistent,
            fault=self._fault_latched,
            expected_rpm=expected,
            actual_rpm=actual_rpm,
            mismatch_timer_s=self._mismatch_timer_s,
        )
