"""
Görevi        : Uçuş durum makinesi. Görev fazlarını (BOOT..RECOVERY, EMERGENCY_
                APAM, SAFE_MODE, FAULT) ve geçiş kurallarını tanımlar; her iç
                durumu şartname UYDU STATÜSÜ (0..5) koduna eşler.
Neden Gerekli : ANA_PROMPT F.4 + Şartname §2.4. Telemetri statü alanı bu makineden
                gelir; faz bilgisi failsafe (iniş fazı kontrolü) için gereklidir.
İlişkiler     : FlightContext okur; SatelliteStatus (telemetry.packet) döndürür;
                app döngüsü her çevrim update() çağırır.
Nasıl Test    : tests/test_state_machine.py — faz geçişleri, 0..5 eşlemesi,
                CONFLICT-002 (şartname esas), APAM/SAFE geçişleri.
"""
from __future__ import annotations

from enum import Enum

from config.default import MissionConfig
from src.mission.context import FlightContext
from src.telemetry.packet import SatelliteStatus


class FlightPhase(Enum):
    BOOT = "BOOT"
    READY_TO_FLY = "READY_TO_FLY"
    ASCENT = "ASCENT"
    CARRIER_DESCENT = "CARRIER_DESCENT"
    SEPARATION = "SEPARATION"
    ARM_DEPLOY = "ARM_DEPLOY"
    ACTIVE_DESCENT = "ACTIVE_DESCENT"
    HOVERING = "HOVERING"
    FINAL_APPROACH = "FINAL_APPROACH"
    LANDED = "LANDED"
    RECOVERY = "RECOVERY"
    EMERGENCY_APAM = "EMERGENCY_APAM"
    SAFE_MODE = "SAFE_MODE"
    FAULT = "FAULT"


# İç faz → şartname UYDU STATÜSÜ (0..5) eşlemesi (Şartname §2.4, CONFLICT-002).
_STATUS_MAP = {
    FlightPhase.BOOT: SatelliteStatus.READY,
    FlightPhase.READY_TO_FLY: SatelliteStatus.READY,
    FlightPhase.ASCENT: SatelliteStatus.ASCENT,
    FlightPhase.CARRIER_DESCENT: SatelliteStatus.CARRIER_DESCENT,   # 2
    FlightPhase.SEPARATION: SatelliteStatus.SEPARATION,             # 3
    FlightPhase.ARM_DEPLOY: SatelliteStatus.SEPARATION,             # 3
    FlightPhase.ACTIVE_DESCENT: SatelliteStatus.PAYLOAD_DESCENT,    # 4
    FlightPhase.HOVERING: SatelliteStatus.PAYLOAD_DESCENT,          # 4
    FlightPhase.FINAL_APPROACH: SatelliteStatus.PAYLOAD_DESCENT,    # 4
    FlightPhase.EMERGENCY_APAM: SatelliteStatus.PAYLOAD_DESCENT,    # 4 (hâlâ iniyor)
    FlightPhase.LANDED: SatelliteStatus.RECOVERY,                   # 5
    FlightPhase.RECOVERY: SatelliteStatus.RECOVERY,                 # 5
}


class FlightStateMachine:
    """
    İleri yönlü (geri dönüşsüz ana akış) durum makinesi. EMERGENCY_APAM ve
    SAFE_MODE/FAULT yalnızca ana akıştan İLERİ (güvenli) yönde girilir; ayrılma
    öncesi FAULT statüsü mevcut fazın koduna göre raporlanır.
    """

    def __init__(self, config: MissionConfig) -> None:
        self._cfg = config
        self._phase = FlightPhase.BOOT
        self._ascent_seen = False
        self._hover_entered = False
        self._faulted_after_separation = False

    @property
    def phase(self) -> FlightPhase:
        return self._phase

    def status_code(self) -> SatelliteStatus:
        """Şartname 0..5 kodu. FAULT/SAFE_MODE için ayrılma durumuna göre eşle."""
        if self._phase in (FlightPhase.SAFE_MODE, FlightPhase.FAULT):
            # Ayrılma sonrası fault → 4 (görev yükü iniş); öncesi → 0/1.
            return (SatelliteStatus.PAYLOAD_DESCENT
                    if self._faulted_after_separation
                    else SatelliteStatus.READY)
        return _STATUS_MAP[self._phase]

    def update(self, ctx: FlightContext) -> FlightPhase:
        """Bağlama göre bir geçiş adımı uygular ve yeni fazı döndürür."""
        m = self._cfg

        # --- En yüksek öncelik: APAM aktifse acil faza geç (ana akıştan) ---
        if ctx.apam_active and self._phase not in (
            FlightPhase.LANDED, FlightPhase.RECOVERY,
        ):
            self._phase = FlightPhase.EMERGENCY_APAM

        if self._phase is FlightPhase.EMERGENCY_APAM:
            if self._is_landed(ctx):
                self._phase = FlightPhase.LANDED
            return self._phase

        # --- Ana akış geçişleri ---
        if self._phase is FlightPhase.BOOT:
            self._phase = FlightPhase.READY_TO_FLY

        elif self._phase is FlightPhase.READY_TO_FLY:
            if ctx.ascending and ctx.altitude_m > 5.0:
                self._phase = FlightPhase.ASCENT
                self._ascent_seen = True

        elif self._phase is FlightPhase.ASCENT:
            if not ctx.ascending and ctx.descent_speed_mps > 0.0:
                self._phase = FlightPhase.CARRIER_DESCENT

        elif self._phase is FlightPhase.CARRIER_DESCENT:
            near_sep = abs(ctx.altitude_m - m.separation_altitude_m) <= m.separation_tolerance_m
            if ctx.separation_confirmed or ctx.manual_separation_cmd or \
                    (near_sep and ctx.altitude_m <= m.separation_altitude_m):
                self._phase = FlightPhase.SEPARATION

        elif self._phase is FlightPhase.SEPARATION:
            if ctx.separation_confirmed:
                self._phase = FlightPhase.ARM_DEPLOY

        elif self._phase is FlightPhase.ARM_DEPLOY:
            if ctx.arms_deployed:
                self._phase = FlightPhase.ACTIVE_DESCENT

        elif self._phase is FlightPhase.ACTIVE_DESCENT:
            if not self._hover_entered and \
                    abs(ctx.altitude_m - m.hovering_altitude_m) <= 5.0:
                self._phase = FlightPhase.HOVERING
                self._hover_entered = True
            elif ctx.altitude_m <= m.final_approach_altitude_m:
                self._phase = FlightPhase.FINAL_APPROACH

        elif self._phase is FlightPhase.HOVERING:
            # Askı sonrası tekrar alçalmaya başlayınca aktif inişe döner.
            if ctx.altitude_m < m.hovering_altitude_m - 5.0:
                self._phase = FlightPhase.ACTIVE_DESCENT

        elif self._phase is FlightPhase.FINAL_APPROACH:
            if self._is_landed(ctx):
                self._phase = FlightPhase.LANDED

        elif self._phase is FlightPhase.LANDED:
            self._phase = FlightPhase.RECOVERY

        return self._phase

    def to_fault(self, ctx: FlightContext) -> None:
        """Kritik arıza: FAULT fazına geç (statü mevcut ayrılma durumuna göre)."""
        self._faulted_after_separation = ctx.separation_confirmed
        self._phase = FlightPhase.FAULT

    def _is_landed(self, ctx: FlightContext) -> bool:
        m = self._cfg
        return (ctx.altitude_m <= m.landed_altitude_m
                and abs(ctx.descent_speed_mps) <= m.landed_speed_mps)
