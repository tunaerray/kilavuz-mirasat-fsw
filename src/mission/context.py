"""
Görevi        : Uçuş bağlamı (FlightContext). Bir çevrimde kestirilen/ölçülen
                durumu; irtifa, iniş hızı, faz bayrakları ve sağlık bayraklarını
                taşır. Durum makinesi, sağlık izleyici ve failsafe bunu tüketir.
Neden Gerekli : Katmanlar arası tek yönlü, açık veri sözleşmesi. Global değişken
                yerine değer nesnesi (test edilebilirlik, determinizm).
İlişkiler     : app döngüsü sensör okumalarından FlightContext üretir; state
                machine / failsafe / health bunu okur.
Nasıl Test    : Dolaylı olarak test_state_machine / test_failsafe_apam içinde.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HealthFlags:
    """Sağlık izleyici çıktısı (bayraklar)."""

    stale_sensor: bool = False
    low_battery: bool = False
    critical_battery: bool = False
    link_loss: bool = False
    loop_overrun: bool = False

    def any_fault(self) -> bool:
        return self.stale_sensor or self.critical_battery


@dataclass
class FlightContext:
    """Bir kontrol çevriminin karar girdileri."""

    mission_time_s: float
    altitude_m: float                 # kalkış noktasına göre (0 m referans)
    descent_speed_mps: float          # pozitif = iniş
    ascending: bool
    gps_valid: bool
    separation_confirmed: bool = False
    arms_deployed: bool = False
    apam_active: bool = False
    manual_separation_cmd: bool = False
    manual_apam_cmd: bool = False
    health: HealthFlags = field(default_factory=HealthFlags)
