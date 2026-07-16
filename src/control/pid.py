"""
Görevi        : Genel amaçlı PID kontrolcü. Anti-windup (integral clamp), çıkış
                doygunluğu (output clamp) ve türev-ölçüm-üzerinden (derivative on
                measurement) desteği ile deterministik, dt-güdümlü.
Neden Gerekli : REQ-CTRL-002 — 8–10 m/s kontrollü alçalma için throttle üreten
                kontrolcünün çekirdeği. Hovering (BONUS-1, Aşama 3) de aynı PID'i
                farklı setpoint ile kullanır.
İlişkiler     : DescentController tarafından kullanılır. Clock'a bağlı değildir;
                dt dışarıdan verilir (test edilebilirlik). Sabitler config'ten gelir.
Nasıl Test    : tests/test_pid.py — P/I/D katkıları, anti-windup, çıkış limiti,
                türev sıçraması yok (setpoint değişiminde), reset.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PidGains:
    """PID kazançları ve limitleri (config'ten beslenir)."""

    kp: float
    ki: float
    kd: float
    output_min: float
    output_max: float
    # Integral terimi bu mutlak sınırlar içinde tutulur (anti-windup).
    integral_min: float
    integral_max: float


class PidController:
    """
    Tek girişli PID. Türev, ÖLÇÜM üzerinden alınır (setpoint adımında türev
    sıçraması olmaz). Integral, hem kendi sınırlarıyla hem de çıkış doygunluğunda
    dondurularak (conditional integration) windup'a karşı korunur.
    """

    def __init__(self, gains: PidGains) -> None:
        self._g = gains
        self._integral = 0.0
        self._prev_measurement: float | None = None
        self.last_p = 0.0
        self.last_i = 0.0
        self.last_d = 0.0

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_measurement = None
        self.last_p = self.last_i = self.last_d = 0.0

    @property
    def integral(self) -> float:
        return self._integral

    def update(self, setpoint: float, measurement: float, dt: float) -> float:
        """
        Bir kontrol adımı. `dt` saniye (> 0). Çıkışı [output_min, output_max]
        aralığında döndürür. dt<=0 ise güvenli biçimde son P-benzeri çıkışı verir.
        """
        g = self._g
        error = setpoint - measurement

        # Orantısal
        p = g.kp * error

        # Türev (ölçüm üzerinden; işaret negatif çünkü hata = sp - meas)
        if self._prev_measurement is None or dt <= 0.0:
            d = 0.0
        else:
            d_meas = (measurement - self._prev_measurement) / dt
            d = -g.kd * d_meas
        self._prev_measurement = measurement

        # Integral (koşullu: çıkış doymuşsa ve hata doygunluğu artırıyorsa ekleme)
        candidate_integral = self._integral
        if dt > 0.0:
            candidate_integral = self._integral + error * dt
        candidate_integral = _clamp(candidate_integral, g.integral_min, g.integral_max)
        i = g.ki * candidate_integral

        raw = p + i + d
        clamped = _clamp(raw, g.output_min, g.output_max)

        # Anti-windup: çıkış doymuşsa ve integral doygunluğu daha da artırıyorsa,
        # integral güncellemesini geri al (conditional integration).
        saturated = raw != clamped
        pushing_further = (raw > clamped and error > 0) or (raw < clamped and error < 0)
        if not (saturated and pushing_further):
            self._integral = candidate_integral
        # aksi halde integral eski değerinde kalır

        self.last_p, self.last_i, self.last_d = p, g.ki * self._integral, d
        return clamped


def _clamp(x: float, lo: float, hi: float) -> float:
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
