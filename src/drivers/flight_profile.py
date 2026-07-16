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
    Zaman tabanlı senaryo. Varsayılan "nominal_descent" profili tüm fazları
    hızlandırılmış biçimde içerir; ayrıca APAM'ı test etmek için
    "runaway_descent" profili vardır (16 m/s üzeri sürekli iniş).
    """

    def __init__(self, name: str = "nominal_descent",
                 release_altitude_m: float = 1600.0) -> None:
        self._name = name
        self._release_alt = release_altitude_m
        # Referans konum (Ankara civarı, PDR örneğine yakın).
        self._lat0 = 39.9255
        self._lon0 = 32.8662

    @property
    def name(self) -> str:
        return self._name

    def sample(self, t: float) -> TruthState:
        if self._name == "runaway_descent":
            return self._runaway(t)
        return self._nominal(t)

    # ----------------------------------------------------------- nominal profil
    def _nominal(self, t: float) -> TruthState:
        """
        Hızlandırılmış senaryo (sim saniyeleri):
          0-5   s : yükselme (0 → release_alt)
          5-25  s : taşıyıcı pasif iniş ~14 m/s (release → ~1000 m)
          25    s : ayrılma (~1000 m)
          25-45 s : aktif iniş ~9 m/s (1000 → ~200 m)
          45-55 s : hovering (200 m, ~0 m/s)  [BONUS-1]
          55-75 s : aktif iniş ~9 m/s (200 → 0)
          >75   s : yerde (0 m, 0 m/s)
        """
        release = self._release_alt
        if t < 5.0:
            frac = t / 5.0
            alt = release * frac
            vs = -release / 5.0                # yükseliyor (negatif iniş hızı)
            asc, sep = True, False
        elif t < 25.0:
            alt = release - 14.0 * (t - 5.0)
            vs = 14.0
            asc, sep = False, False
        elif t < 45.0:
            alt = 1000.0 - 9.0 * (t - 25.0) * (800.0 / 180.0)  # ~1000→200
            vs = 9.0
            asc, sep = False, True
        elif t < 55.0:
            alt = 200.0
            vs = 0.3                            # ~askı (0-1 m/s bandı)
            asc, sep = False, True
        elif t < 75.0:
            alt = 200.0 - 9.0 * (t - 55.0) * (200.0 / 180.0)
            vs = 9.0
            asc, sep = False, True
        else:
            alt = 0.0
            vs = 0.0
            asc, sep = False, True
        alt = max(alt, 0.0)
        return self._make(t, alt, vs, asc, sep)

    # ----------------------------------------------------------- runaway profil
    def _runaway(self, t: float) -> TruthState:
        """Ayrılma sonrası motor arızası: sürekli ~20 m/s iniş (APAM testi)."""
        if t < 5.0:
            frac = t / 5.0
            return self._make(t, self._release_alt * frac,
                              -self._release_alt / 5.0, True, False)
        # ayrılmış say ve 1000 m'den 20 m/s ile düş
        alt = max(1000.0 - 20.0 * (t - 5.0), 0.0)
        return self._make(t, alt, 20.0, False, True)

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
