"""
Görevi        : Saha baro kalibrasyonu. Kalkışta birden çok basınç örneği toplayıp
                aykırıları eleyerek 0 m yükseklik referans basıncını sağlam biçimde
                belirler (tek örnek yerine medyan tabanlı ortalama).
Neden Gerekli : Şartname §2.4 (kalkış = 0 m) + PDR s.90 (barometre başlangıçta
                sıfırlanır) + EKSİK-003. Tek örnekli sıfırlama gürültüye açıktır;
                saha prosedürü çoklu örnek ister.
İlişkiler     : Ana döngü/preflight kalkışta örnek toplar; sonuç PersistenceStore'a
                kalıcı referans olarak yazılır (restart tutarlılığı). StateEstimator
                bu referansı kullanır.
Nasıl Test    : tests/test_calibration.py — ortalama, aykırı reddi, yetersiz örnek,
                gürültülü örneklerde kararlılık.
"""
from __future__ import annotations

from statistics import median

from src.common.result import ErrorCode, Result


class BaroCalibrator:
    """
    Basınç örneklerini toplar; medyandan `outlier_tolerance_pa` kadar sapan
    örnekleri eler; kalan örneklerin ortalamasını referans basınç olarak döndürür.
    En az `min_samples` GEÇERLİ örnek gerekir; aksi halde açık hata.
    """

    def __init__(self, sample_count: int = 20, min_samples: int = 5,
                 outlier_tolerance_pa: float = 200.0) -> None:
        self._target = sample_count
        self._min = min_samples
        self._tol = outlier_tolerance_pa
        self._samples: list[float] = []

    def add_sample(self, pressure_pa: float) -> None:
        if pressure_pa > 0.0:                 # fiziksel olarak anlamlı örnekler
            self._samples.append(float(pressure_pa))

    @property
    def sample_count(self) -> int:
        return len(self._samples)

    @property
    def ready(self) -> bool:
        return len(self._samples) >= self._target

    def calibrate(self) -> Result[float]:
        """Toplanan örneklerden referans basıncı hesaplar (medyan tabanlı filtre)."""
        if len(self._samples) < self._min:
            return Result.err(ErrorCode.INVALID_DATA,
                              f"kalibrasyon için yetersiz örnek: "
                              f"{len(self._samples)}/{self._min}")
        med = median(self._samples)
        accepted = [s for s in self._samples if abs(s - med) <= self._tol]
        if len(accepted) < self._min:
            return Result.err(ErrorCode.INVALID_DATA,
                              f"aykırı elemeden sonra yetersiz örnek: "
                              f"{len(accepted)}/{self._min}")
        reference = sum(accepted) / len(accepted)
        return Result.ok(reference)

    def reset(self) -> None:
        self._samples.clear()
