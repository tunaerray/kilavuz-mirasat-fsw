"""
Görevi        : Durum kestirici (sensör füzyonu). Barometreden AGL irtifa,
                filtrelenmiş dikey hız ve IMU'dan yönelim üretir; baro ile GPS
                dikey hareketini karşılaştırarak çoklu-sensör tutarlılığı ve aykırı
                ölçüm reddi sağlar.
Neden Gerekli : REQ-CTRL-001 — kontrol ve APAM kararları tek ham sensöre değil,
                filtrelenmiş ve çapraz-doğrulanmış kestirime dayanmalı (APAM
                false-trigger önlemi; ANA_PROMPT APAM konsepti).
İlişkiler     : HAL sensör okumalarını (baro/imu/gps) girdi alır; DescentController
                ve FailsafeManager EstimatorOutput'u tüketir. flight_profile'ın
                barometrik dönüşümünü kullanır. Sabitler ControlConfig'ten gelir.
Nasıl Test    : tests/test_estimator.py — irtifa/hız kestirimi, aykırı reddi,
                baro-GPS tutarlılık, filtre yumuşatma, bayat/timeout davranışı.
"""
from __future__ import annotations

from dataclasses import dataclass

from config.default import ControlConfig
from src.common.result import Result
from src.drivers.flight_profile import pressure_to_altitude
from src.hal.interfaces import BarometerReading, GpsReading, ImuReading


@dataclass
class EstimatorOutput:
    """Bir çevrimin füzyon çıktısı."""

    altitude_m: float               # AGL (kalkış = 0), baro esaslı
    vertical_speed_mps: float       # filtreli; pozitif = iniş
    pitch_deg: float
    roll_deg: float
    yaw_deg: float
    altitude_valid: bool
    attitude_valid: bool
    gps_valid: bool
    speed_consistent: bool          # baro vs GPS dikey hız uyumu (APAM güveni)


class StateEstimator:
    """
    Tamamlayıcı (complementary) düşük-geçiren filtre tabanlı kestirici.
    - İrtifa: baro basıncından, kalkış referansına göre AGL. Aykırı/timeout ise
      son geçerli irtifa korunur ve `altitude_valid=False`.
    - Dikey hız: baro irtifasının sonlu farkı, düşük-geçiren filtreden geçirilir.
    - Tutarlılık: GPS irtifasından türetilen dikey hız ile baro hızı toleransta
      uyuşuyorsa `speed_consistent=True`.
    """

    def __init__(self, config: ControlConfig, zero_ref_pressure_pa: float) -> None:
        self._c = config
        self._p0 = zero_ref_pressure_pa
        self._alt0 = pressure_to_altitude(zero_ref_pressure_pa)
        self._last_alt: float | None = None
        self._last_gps_alt: float | None = None
        self._filt_vspeed = 0.0
        self._last_attitude = (0.0, 0.0, 0.0)

    def _plausible_alt(self, alt: float) -> bool:
        return self._c.plausible_altitude_min_m <= alt <= self._c.plausible_altitude_max_m

    def _plausible_att(self, *angles: float) -> bool:
        limit = self._c.plausible_attitude_deg
        return all(-limit <= a <= limit for a in angles)

    def update(self, baro: Result[BarometerReading], imu: Result[ImuReading],
               gps: Result[GpsReading], dt: float) -> EstimatorOutput:
        c = self._c

        # --- İrtifa (baro) ---
        altitude_valid = False
        if baro.is_ok:
            raw_alt = pressure_to_altitude(baro.unwrap().pressure_pa) - self._alt0
            if self._plausible_alt(raw_alt):
                altitude = raw_alt
                altitude_valid = True
            else:
                altitude = self._last_alt if self._last_alt is not None else 0.0
        else:
            altitude = self._last_alt if self._last_alt is not None else 0.0

        # --- Dikey hız (baro sonlu fark + filtre) ---
        if self._last_alt is None or dt <= 0.0 or not altitude_valid:
            raw_vspeed = self._filt_vspeed if self._last_alt is not None else 0.0
        else:
            raw_vspeed = -(altitude - self._last_alt) / dt   # pozitif = iniş
        # düşük-geçiren filtre
        a = c.vspeed_filter_alpha
        self._filt_vspeed = a * self._filt_vspeed + (1.0 - a) * raw_vspeed
        if altitude_valid:
            self._last_alt = altitude

        # --- GPS dikey hızı (tutarlılık için) ---
        speed_consistent = False
        gps_valid = gps.is_ok and gps.unwrap().fix_valid
        if gps_valid:
            gps_alt = gps.unwrap().altitude_m
            if self._last_gps_alt is not None and dt > 0.0:
                gps_vspeed = -(gps_alt - self._last_gps_alt) / dt
                if abs(gps_vspeed - self._filt_vspeed) <= c.consistency_tolerance_mps:
                    speed_consistent = True
            self._last_gps_alt = gps_alt

        # --- Yönelim (IMU) ---
        attitude_valid = False
        if imu.is_ok:
            r = imu.unwrap()
            if self._plausible_att(r.pitch_deg, r.roll_deg, r.yaw_deg):
                self._last_attitude = (r.pitch_deg, r.roll_deg, r.yaw_deg)
                attitude_valid = True
        pitch, roll, yaw = self._last_attitude

        return EstimatorOutput(
            altitude_m=altitude,
            vertical_speed_mps=self._filt_vspeed,
            pitch_deg=pitch, roll_deg=roll, yaw_deg=yaw,
            altitude_valid=altitude_valid,
            attitude_valid=attitude_valid,
            gps_valid=gps_valid,
            speed_consistent=speed_consistent,
        )
