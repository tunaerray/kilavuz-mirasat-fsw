"""
Görevi        : Uçuşa hazırlık (preflight) go/no-go kontrolü. Sensörlerin okunabilir
                olduğunu, bataryanın dolu, GPS kilidinin yeterli (≥6 uydu),
                aktüatörlerin Safe State'te ve kalıcılığın yüklü olduğunu denetler.
Neden Gerekli : FRR (Şartname §4.2) — model uydu uçuşa uygunluk kontrolü. Uçuş
                yazılımı, "Uçuşa Hazır" (statü 0) fazına geçmeden önce bu kapıdan
                geçmelidir. No-go durumunda uçuşa izin verilmez.
İlişkiler     : Sensör/aktüatör/persistence bileşenlerini okur; ana döngü BOOT'ta
                bir kez çağırır. Sonuç loglanır ve rapora yansır.
Nasıl Test    : tests/test_preflight.py — tüm-go, her bir no-go koşulu (düşük
                batarya, GPS kilidi yok, sensör timeout, aktüatör arm), sıralama.
"""
from __future__ import annotations

from dataclasses import dataclass

from config.default import HealthConfig
from src.drivers.mock_actuators import ActuatorSuite
from src.hal.interfaces import ArmState, ServoPosition


@dataclass(frozen=True)
class CheckItem:
    name: str
    passed: bool
    detail: str


@dataclass
class PreflightReport:
    items: list
    is_go: bool

    def failed(self) -> list:
        return [i for i in self.items if not i.passed]


class PreflightCheck:
    def __init__(self, config: HealthConfig) -> None:
        self._c = config

    def run(self, baro, imu, gps, battery, actuators: ActuatorSuite,
            persistence) -> PreflightReport:
        items: list[CheckItem] = []

        # 1. Sensörler okunabilir mi
        for name, sensor in (("Barometre", baro), ("IMU", imu), ("GPS", gps),
                             ("Batarya", battery)):
            r = sensor.read()
            items.append(CheckItem(f"{name} okunabilir", r.is_ok,
                                   "OK" if r.is_ok else r.message))

        # 2. Batarya dolu mu
        vr = battery.read()
        if vr.is_ok:
            v = vr.unwrap().voltage_v
            ok = v >= self._c.preflight_min_voltage_v
            items.append(CheckItem("Batarya dolu",
                                   ok, f"{v:.1f} V (min {self._c.preflight_min_voltage_v})"))
        else:
            items.append(CheckItem("Batarya dolu", False, "batarya okunamadı"))

        # 3. GPS kilidi ≥6 uydu
        gr = gps.read()
        if gr.is_ok:
            g = gr.unwrap()
            ok = g.fix_valid and g.satellites >= self._c.preflight_min_satellites
            items.append(CheckItem("GPS kilidi",
                                   ok, f"fix={g.fix_valid}, uydu={g.satellites}"))
        else:
            items.append(CheckItem("GPS kilidi", False, "GPS okunamadı"))

        # 4. Aktüatörler Safe State'te
        safe = (actuators.motors.arm_state is ArmState.DISARMED
                and actuators.motors.throttle == 0.0
                and actuators.apam_servo.position is ServoPosition.CLOSED
                and actuators.separation_servo.position is ServoPosition.LOCKED
                and actuators.arms.locked)
        items.append(CheckItem("Aktüatörler Safe State", safe,
                               "disarm/kilitli" if safe else "GÜVENSİZ konum"))

        # 5. Kalıcılık yüklü (paket sayacı erişilebilir)
        loaded = getattr(persistence, "boot_count", 0) >= 1
        items.append(CheckItem("Kalıcılık yüklü", loaded,
                               f"boot #{getattr(persistence, 'boot_count', 0)}"))

        is_go = all(i.passed for i in items)
        return PreflightReport(items=items, is_go=is_go)
