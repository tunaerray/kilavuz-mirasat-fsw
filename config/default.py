"""
Görevi        : Merkezi yapılandırma. Tüm eşikler, birimler, dosya yolları ve
                çalışma profili (varsayılan SIMULATION_ONLY) parametre olarak
                burada tutulur; sabitler koda GÖMÜLMEZ.
Neden Gerekli : ANA_PROMPT F.1 / coding standards — APAM eşikleri, telemetri
                frekansı, hata kodu hane sayısı (CONFLICT-003), iniş sonrası TLM
                süresi (CONFLICT-001), takım no (947450) config'ten gelir.
İlişkiler     : main, persistence, telemetry, failsafe, health, drivers hepsi
                AppConfig alır. Profil adına göre get_config() döner.
Nasıl Test    : tests/test_config.py — varsayılan SIMULATION, eşik değerleri,
                bilinmeyen profil hatası.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum


class RunProfile(Enum):
    """Çalışma profili. Varsayılan güvenli: SIMULATION_ONLY."""

    SIMULATION_ONLY = "SIMULATION_ONLY"
    HARDWARE_IN_THE_LOOP = "HARDWARE_IN_THE_LOOP"  # Aşama 5'te etkinleşir
    FLIGHT = "FLIGHT"  # Aşama 5'te etkinleşir


@dataclass(frozen=True)
class ApamConfig:
    """APAM tetikleme parametreleri — Şartname Gereksinim-10 s.11 (DOĞRULANMIŞ)."""

    trigger_speed_mps: float = 16.0        # bu hızın ÜZERİ
    trigger_duration_s: float = 10.0       # KESİNTİSİZ süre
    min_deploy_altitude_m: float = 100.0   # paraşüt yalnız bu irtifanın ÜZERİNDE
    # Hız güvenli sayılırsa sayaç sıfırlanır; güvenli üst sınır:
    safe_speed_reset_mps: float = 16.0


@dataclass(frozen=True)
class TelemetryConfig:
    """Telemetri format ve gönderim parametreleri — Şartname §2.4."""

    rate_hz: float = 1.0                   # Gereksinim-16: 1 Hz
    error_code_digits: int = 4             # CONFLICT-003: varsayılan 4, 5'e açık
    field_separator: str = ","
    decimal_places: int = 1                # örnek pakete uygun ondalık
    # LoRa E22 (EKSİK-002 / ASSUMPTION-002) — mock'ta kullanılır:
    lora_baud: int = 9600
    lora_air_rate: str = "2.4k"


@dataclass(frozen=True)
class HealthConfig:
    """Sağlık izleme eşikleri (ASSUMPTION-005/009)."""

    max_sensor_age_s: float = 0.5
    low_voltage_v: float = 14.0            # 4S ~3.5 V/hücre
    critical_voltage_v: float = 13.2       # 4S ~3.3 V/hücre
    link_timeout_s: float = 3.0
    loop_overrun_tolerance: float = 0.25   # periyodun %25 üzeri = aşım


@dataclass(frozen=True)
class MissionConfig:
    """Görev profili eşikleri — Şartname (DOĞRULANMIŞ) + varsayımlar."""

    separation_altitude_m: float = 1000.0          # Gereksinim-6
    separation_tolerance_m: float = 10.0           # ±10 m
    target_descent_speed_range: tuple = (8.0, 10.0)  # Gereksinim-9 (GY)
    # CONFLICT-004: taşıyıcı+GY pasif iniş; toleranslı üst sınır 16
    carrier_descent_speed_range: tuple = (12.0, 16.0)
    hovering_altitude_m: float = 200.0             # BONUS-1 (AGL)
    hovering_duration_s: float = 10.0
    hovering_speed_tolerance_mps: float = 1.0      # 0–1 m/s
    final_approach_altitude_m: float = 50.0        # Gereksinim-14
    # CONFLICT-001: varsayılan 10 sn (Gereksinim-27); 60'a çekilebilir
    post_landing_telemetry_s: float = 10.0
    landed_altitude_m: float = 2.0                 # ASSUMPTION-008
    landed_speed_mps: float = 1.0
    release_altitude_m: float = 1600.0             # ~bırakma irtifası (sim)


@dataclass(frozen=True)
class ControlConfig:
    """
    Aşama 2 kontrol/navigasyon parametreleri — kestirim, PID ve motor modeli.
    Tüm değerler makul mühendislik varsayımlarıdır (ASSUMPTION); saha
    kalibrasyonunda ayarlanır. Gerçek uçuşta gains uçuş kontrol kartında da
    doğrulanmalıdır.
    """

    # Hedef kontrollü alçalma hızı (Gereksinim-9: 8–10 m/s bandının ortası)
    target_descent_speed_mps: float = 9.0
    # Askı (BONUS-1) hedef hızı (0 m/s) ve tahmini gaz konumu (PDR ~%70)
    hover_throttle_estimate: float = 0.70
    # Son 50 m'de RPM artışı için hedef hızı düşürme çarpanı (Gereksinim-14)
    final_approach_speed_mps: float = 6.0

    # Alçalma PID kazançları (hız hatası → throttle). Pozitif hata (çok hızlı
    # iniyor) daha yüksek throttle ister → yukarı itiş artar.
    descent_kp: float = 0.05
    descent_ki: float = 0.01
    descent_kd: float = 0.005
    descent_integral_min: float = -5.0
    descent_integral_max: float = 5.0
    throttle_min: float = 0.0
    throttle_max: float = 1.0

    # Kestirim (state estimator)
    vspeed_filter_alpha: float = 0.6        # düşük geçiren filtre (0=ham, 1=çok yumuşak)
    consistency_tolerance_mps: float = 4.0  # baro vs GPS dikey hız uyum toleransı
    plausible_altitude_min_m: float = -100.0
    plausible_altitude_max_m: float = 5000.0
    plausible_attitude_deg: float = 180.0   # |açı| bu değerden büyükse aykırı

    # Motor RPM modeli ve arıza tespiti (REQ-SAFE-010)
    motor_max_rpm: float = 26000.0          # ~1700KV * ~15.4 V (4S nominal)
    motor_rpm_tolerance: float = 0.35       # beklenen RPM'in %35 altı → tutarsız
    motor_fault_persist_s: float = 1.0      # tutarsızlık bu süre sürerse arıza


@dataclass(frozen=True)
class PathsConfig:
    """Çalışma zamanı dosya yolları (SD kart karşılığı)."""

    run_dir: str = "run_data"
    persistence_file: str = "run_data/state.json"
    telemetry_csv: str = "run_data/TMUY2026_947450_TLM.csv"
    event_log: str = "run_data/events.log"


@dataclass(frozen=True)
class AppConfig:
    """Tüm alt yapılandırmaları bir araya getiren kök yapılandırma."""

    profile: RunProfile = RunProfile.SIMULATION_ONLY
    team_number: int = 947450                       # PDR: DOĞRULANMIŞ
    loop_hz: float = 20.0                            # ASSUMPTION-003: kontrol döngüsü
    apam: ApamConfig = field(default_factory=ApamConfig)
    telemetry: TelemetryConfig = field(default_factory=TelemetryConfig)
    health: HealthConfig = field(default_factory=HealthConfig)
    mission: MissionConfig = field(default_factory=MissionConfig)
    control: ControlConfig = field(default_factory=ControlConfig)
    paths: PathsConfig = field(default_factory=PathsConfig)

    @property
    def loop_period_s(self) -> float:
        return 1.0 / self.loop_hz

    @property
    def telemetry_period_s(self) -> float:
        return 1.0 / self.telemetry.rate_hz

    @property
    def is_simulation(self) -> bool:
        return self.profile is RunProfile.SIMULATION_ONLY


# Varsayılan profil: her zaman SIMULATION_ONLY (güvenlik).
SIMULATION = AppConfig()

_PROFILES = {
    "simulation": SIMULATION,
    "sim": SIMULATION,
    "SIMULATION_ONLY": SIMULATION,
}


def get_config(name: str = "simulation") -> AppConfig:
    """
    Profil adına göre AppConfig döner. Bilinmeyen profil sessizce varsayılana
    DÜŞMEZ; açık hata verir (yanlış profil = güvenlik riski).
    HIL/FLIGHT profilleri Aşama 5'e kadar bilinçli olarak devre dışıdır.
    """
    key = name.strip()
    if key not in _PROFILES:
        raise ValueError(
            f"Bilinmeyen profil: {name!r}. Geçerli: {sorted(_PROFILES)}. "
            "HARDWARE/FLIGHT profilleri Aşama 5'te etkinleşecektir."
        )
    return _PROFILES[key]


def with_overrides(base: AppConfig, **kwargs) -> AppConfig:
    """Test/araç amaçlı sığ override (immutable kopya)."""
    return replace(base, **kwargs)
