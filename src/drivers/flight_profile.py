"""
Görevi        : Deterministik uçuş profili (yer gerçekliği). Görev zamanına göre
                irtifa, dikey hız, sıcaklık, konum ve yönelim üretir. Mock
                sensörler bu profilden beslenir.
Neden Gerekli : Fiziksel donanım ve gerçek uçuş yok. Durum makinesi, failsafe ve
                telemetriyi anlamlı ve TEKRARLANABİLİR verilerle sürmek gerekir.
                Rastgelelik yok → testler deterministik.
İlişkiler     : mock_sensors bu profili örnekler; app döngüsü görev zamanını verir.
Nasıl Test    : test_mock_sensors.py dolaylı; profil sınırları burada net.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Uluslararası standart atmosfer (basitleştirilmiş) — basınç<->irtifa dönüşümü.
_SEA_LEVEL_PA = 101325.0
_LAPSE = 0.0065
_T0 = 288.15
_EXP = 5.255


def altitude_to_pressure(alt_m: float) -> float:
    """Barometrik formül (kalkış = deniz seviyesi kabulü, sim için yeterli)."""
    alt_m = max(alt_m, -500.0)
    return _SEA_LEVEL_PA * (1.0 - (_LAPSE * alt_m) / _T0) ** _EXP


def pressure_to_altitude(pressure_pa: float) -> float:
    """altitude_to_pressure'ın tersi. FSW irtifayı basınçtan bu formülle kestirir."""
    pressure_pa = max(pressure_pa, 1.0)
    return (_T0 / _LAPSE) * (1.0 - (pressure_pa / _SEA_LEVEL_PA) ** (1.0 / _EXP))


@dataclass(frozen=True)
class TruthState:
    """Belirli bir görev zamanındaki gerçek (simüle) durum."""

    altitude_m: float
    vertical_speed_mps: float     # pozitif = iniş hızı
    pressure_pa: float
    temperature_c: float
    latitude: float
    longitude: float
    gps_altitude_m: float
    pitch_deg: float
    roll_deg: float
    yaw_deg: float
    separated: bool
    ascending: bool


class FlightProfile:
    """
    Zaman tabanlı senaryo. Anahtar kareler (keyframe) arasında irtifa DOĞRUSAL
    interpolasyonla üretilir; böylece irtifa süreklidir ve dikey hız her
    segmentte sabit eğime eşittir (sınır sıçraması / sahte hız yok).
      nominal_descent : tüm fazlar, iniş hızları şartname sınırlarında (≤14 / ~9).
      runaway_descent : ayrılma sonrası ~20 m/s sürekli iniş (APAM testi).
    Ayrılma, 1000 m'ye ulaşıldığı keyframe zamanında gerçekleşir.
    """

    # (t_saniye, irtifa_m) — irtifa sürekli; hız = segment eğimi.
    _NOMINAL_KF = [
        (0.0, 0.0),        # kalkış
        (5.0, 1600.0),     # ~bırakma irtifası (yükselme)
        (51.0, 1000.0),    # taşıyıcı pasif iniş ~13 m/s → ayrılma irtifası
        (140.0, 200.0),    # aktif iniş ~9 m/s → hovering irtifası (BONUS-1)
        (150.0, 200.0),    # 200 m'de ~10 sn askı
        (172.0, 0.0),      # aktif iniş ~9 m/s → yer
    ]
    _RUNAWAY_KF = [
        (0.0, 0.0),
        (5.0, 1000.0),     # kısa yükselme
        (54.75, 0.0),      # ayrılma sonrası ~20 m/s kesintisiz iniş
    ]
    _SEPARATION_ALT = 1000.0

    def __init__(self, name: str = "nominal_descent",
                 release_altitude_m: float = 1600.0) -> None:
        self._name = name
        self._release_alt = release_altitude_m
        self._lat0 = 39.9255      # referans konum (Ankara civarı)
        self._lon0 = 32.8662
        self._kf = self._RUNAWAY_KF if name == "runaway_descent" else self._NOMINAL_KF
        # Ayrılma zamanı: irtifanın 1000 m'ye indiği ilk keyframe.
        self._sep_time = self._time_at_altitude_descending(self._SEPARATION_ALT)

    @property
    def name(self) -> str:
        return self._name

    def sample(self, t: float) -> TruthState:
        alt, vs = self._interp(t)
        ascending = vs < -0.5
        separated = t >= self._sep_time
        return self._make(t, max(alt, 0.0), vs, ascending, separated)

    # ---------------------------------------------------- keyframe interpolasyon
    def _interp(self, t: float):
        kf = self._kf
        if t <= kf[0][0]:
            return kf[0][1], 0.0
        if t >= kf[-1][0]:
            return kf[-1][1], 0.0
        for (ta, aa), (tb, ab) in zip(kf, kf[1:]):
            if ta <= t <= tb:
                frac = (t - ta) / (tb - ta)
                alt = aa + (ab - aa) * frac
                vs = (aa - ab) / (tb - ta)      # pozitif = iniş
                return alt, vs
        return kf[-1][1], 0.0

    def _time_at_altitude_descending(self, target_alt: float) -> float:
        """İrtifanın alçalırken target_alt'a ulaştığı ilk zaman (ayrılma anı)."""
        kf = self._kf
        for (ta, aa), (tb, ab) in zip(kf, kf[1:]):
            if aa > ab and ab <= target_alt <= aa:      # alçalan segment
                frac = (aa - target_alt) / (aa - ab)
                return ta + (tb - ta) * frac
        return float("inf")

    # ------------------------------------------------------------------- yardımcı
    def _make(self, t: float, alt: float, vs: float,
              asc: bool, sep: bool) -> TruthState:
        # Yönelim: küçük deterministik salınım (sabit değil, gerçekçi).
        pitch = 3.0 * math.sin(t * 0.7)
        roll = 2.0 * math.cos(t * 0.5)
        yaw = (t * 12.0) % 360.0
        temp = 28.0 - 0.006 * alt          # irtifa ile hafif düşüş
        return TruthState(
            altitude_m=alt,
            vertical_speed_mps=vs,
            pressure_pa=altitude_to_pressure(alt),
            temperature_c=temp,
            latitude=self._lat0 + 0.0001 * math.sin(t * 0.1),
            longitude=self._lon0 + 0.0001 * math.cos(t * 0.1),
            gps_altitude_m=alt + 15.0,     # GPS alt kalkış noktası ofsetli
            pitch_deg=pitch,
            roll_deg=roll,
            yaw_deg=yaw,
            separated=sep,
            ascending=asc,
        )
