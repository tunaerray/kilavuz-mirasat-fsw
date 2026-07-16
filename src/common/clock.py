"""
Görevi        : Zaman soyutlaması. Monoton döngü zamanı ve UTC duvar saati için
                gerçek (RealClock) ve deterministik sahte (FakeClock) uygulamalar.
Neden Gerekli : ANA_PROMPT F.2 — sistem saatine bağımlı olmayan test edilebilir
                zaman. Testlerde time.sleep yerine FakeClock kullanılır (hızlı,
                deterministik). Görev zamanı ve GÖNDERME SAATİ bu katmandan gelir.
İlişkiler     : PersistenceStore, HealthMonitor, FailsafeManager, main döngüsü ve
                telemetri paketi Clock kullanır.
Nasıl Test    : tests/test_clock.py — FakeClock ilerletme, monotonluk, UTC ayarı.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Protocol, runtime_checkable


@runtime_checkable
class Clock(Protocol):
    """Zaman kaynağı sözleşmesi."""

    def now_monotonic(self) -> float:
        """Saniye cinsinden monoton artan süre (döngü zamanlaması için)."""
        ...

    def now_utc(self) -> datetime:
        """Gerçek zamanlı UTC (telemetri GÖNDERME SAATİ için)."""
        ...


class RealClock:
    """Üretim saati: OS monoton sayacı + UTC duvar saati."""

    def now_monotonic(self) -> float:
        return time.monotonic()

    def now_utc(self) -> datetime:
        return datetime.now(timezone.utc)


class FakeClock:
    """
    Deterministik test saati. Gerçek zaman beklemesi yok; testler `advance()` ile
    zamanı ilerletir. Monoton ve UTC bağımsız olarak kontrol edilebilir.
    """

    def __init__(
        self,
        start_monotonic: float = 0.0,
        start_utc: datetime | None = None,
    ) -> None:
        self._mono = float(start_monotonic)
        self._utc = start_utc or datetime(2026, 5, 4, 14, 32, 10, tzinfo=timezone.utc)

    def now_monotonic(self) -> float:
        return self._mono

    def now_utc(self) -> datetime:
        return self._utc

    def advance(self, seconds: float) -> None:
        """Hem monoton hem UTC saati ileri alır (normal zaman akışı)."""
        if seconds < 0:
            raise ValueError("Saat geriye alınamaz (monotonluk)")
        self._mono += seconds
        self._utc += timedelta(seconds=seconds)

    def set_utc(self, when: datetime) -> None:
        """UTC'yi bağımsız ayarlar (ör. GPS/UTC senkronizasyonu simülasyonu)."""
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        self._utc = when
