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
        self._hover_start_s: float | None = None   # BONUS-1 askı başlangıç zamanı
        self._hover_complete = False
        self._ground_since_s: float | None = None   # yer teması onay zamanlayıcısı
        self._faulted_after_separation = False

    @property
    def phase(self) -> FlightPhase:
        return self._phase

    @property
    def hover_complete(self) -> bool:
        return self._hover_complete

    def hover_elapsed_s(self, mission_time_s: float) -> float:
        """Askı fazındaki geçen süre (askıya girilmediyse 0)."""
        if self._hover_start_s is None:
            return 0.0
        return max(0.0, mission_time_s - self._hover_start_s)

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
            # BONUS-1: askı henüz yapılmadıysa ve 200 m'ye ulaşıldıysa askıya geç.
            if not self._hover_complete and not self._hover_entered and \
                    abs(ctx.altitude_m - m.hovering_altitude_m) <= 5.0:
                self._phase = FlightPhase.HOVERING
                self._hover_entered = True
                self._hover_start_s = ctx.mission_time_s
            elif ctx.altitude_m <= m.final_approach_altitude_m:
                self._phase = FlightPhase.FINAL_APPROACH

        elif self._phase is FlightPhase.HOVERING:
            # BONUS-1: konfigüre süre (10 sn) boyunca askıda kal, sonra inişe devam.
            elapsed = ctx.mission_time_s - (self._hover_start_s or ctx.mission_time_s)
            if elapsed >= m.hovering_duration_s:
                self._hover_complete = True
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
        """
        Yer teması tespiti. Temiz sinyalde hızlı yol (düşük hız → anında);
        gürültülü hızda süre-tutmalı onay (irtifa `landed_confirm_s` boyunca yerde
        kalırsa iniş kabul edilir). Böylece titreşim gürültüsü LANDED geçişini
        engellemez.
        """
        m = self._cfg
        low_speed = abs(ctx.descent_speed_mps) <= m.landed_speed_mps
        # Hızlı/kesin yol: temiz sinyalde kesin yerde ve düşük hız → anında.
        if ctx.altitude_m <= m.landed_altitude_m and low_speed:
            self._ground_since_s = ctx.mission_time_s
            return True
        # Süre-tutmalı yol: kestirilen irtifa gürültü bandı içinde sürekli kalış.
        if ctx.altitude_m <= m.landed_confirm_altitude_m:
            if self._ground_since_s is None:
                self._ground_since_s = ctx.mission_time_s
            return (ctx.mission_time_s - self._ground_since_s) >= m.landed_confirm_s
        self._ground_since_s = None
        return False
