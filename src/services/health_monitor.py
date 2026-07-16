"""
Görevi        : Sağlık izleme temeli. Sensör veri yaşı, batarya gerilimi, telemetri
                bağlantı kaybı ve kontrol döngüsü gecikmesini denetler; bayrak üretir.
Neden Gerekli : ANA_PROMPT F.9 + REQ-SAFE-009. Failsafe kararları ve operatör
                farkındalığı için sistem sağlığı sürekli izlenmelidir.
İlişkiler     : Sensör okumaları + döngü süresi + link durumu alır; HealthFlags
                döndürür. Failsafe ve app döngüsü tüketir. Link loss TEK BAŞINA
                APAM tetiklemez (yalnız bayrak).
Nasıl Test    : tests/test_health_monitor.py — her bayrak için eşik senaryoları.
"""
from __future__ import annotations

from dataclasses import dataclass

from config.default import HealthConfig
from src.mission.context import HealthFlags


@dataclass(frozen=True)
class HealthInputs:
    """Sağlık değerlendirmesi girdileri (bir çevrim)."""

    now_s: float
    newest_sensor_timestamp_s: float   # en güncel geçerli sensör okuması zamanı
    any_sensor_valid: bool
    battery_v: float
    last_link_ok_s: float              # linkin en son sağlıklı olduğu zaman
    loop_duration_s: float
    loop_period_s: float


class HealthMonitor:
    def __init__(self, config: HealthConfig) -> None:
        self._cfg = config

    def evaluate(self, inp: HealthInputs) -> HealthFlags:
        c = self._cfg
        flags = HealthFlags()

        # Veri yaşı: hiç geçerli sensör yoksa veya en güncel okuma çok eskiyse.
        age = inp.now_s - inp.newest_sensor_timestamp_s
        if (not inp.any_sensor_valid) or age > c.max_sensor_age_s:
            flags.stale_sensor = True

        # Batarya
        if inp.battery_v < c.critical_voltage_v:
            flags.critical_battery = True
            flags.low_battery = True
        elif inp.battery_v < c.low_voltage_v:
            flags.low_battery = True

        # Link loss (tek başına APAM tetiklemez)
        if (inp.now_s - inp.last_link_ok_s) > c.link_timeout_s:
            flags.link_loss = True

        # Döngü gecikmesi
        if inp.loop_duration_s > inp.loop_period_s * (1.0 + c.loop_overrun_tolerance):
            flags.loop_overrun = True

        return flags
