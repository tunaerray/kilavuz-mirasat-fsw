"""
Görevi        : Kalıcı depo. Görev zamanı ve telemetri paket sayacını işlemci
                yeniden başlasa bile korur; paket no 1'den başlar, her pakette
                artar, restart'ta KALDIĞI YERDEN devam eder.
Neden Gerekli : Şartname Gereksinim-17 (görev zamanı) ve Gereksinim-18 (paket
                sayacı) s.12 — restart dayanımı zorunludur.
İlişkiler     : main döngüsü her telemetri paketinden önce next_packet_number()
                çağırır; TelemetryPacket görev zamanını buradan alır. Clock
                enjekte edilir (test edilebilirlik).
Nasıl Test    : tests/test_persistence.py — sayaç artışı, atomik yazma ve
                RESTART senaryosu (yeni store aynı dosyadan kaldığı yerden devam).
"""
from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass

from src.common.clock import Clock
from src.common.result import ErrorCode, Result


@dataclass
class PersistentState:
    """Diske yazılan kalıcı durum."""

    packet_number: int = 0
    # Görev başlangıcının monoton referansı korunamaz (restart'ta sıfırlanır),
    # bu yüzden görev süresini kümülatif saniye olarak saklarız.
    mission_elapsed_s: float = 0.0
    boot_count: int = 0
    # İlk kalkışta barometre sıfırlama referansı (0 m yüksekliği için).
    altitude_zero_ref_m: float | None = None


class PersistenceStore:
    """
    Atomik dosya tabanlı kalıcı depo. Her değişiklik tmp dosyaya yazılıp
    os.replace ile yerine konur (yarı-yazılmış dosya riski yok).
    """

    def __init__(self, path: str, clock: Clock) -> None:
        self._path = path
        self._clock = clock
        self._state = PersistentState()
        self._loaded = False
        # Görev süresi ölçümü için bu oturumun monoton başlangıcı.
        self._session_start_mono = clock.now_monotonic()
        # Bu oturuma girildiğindeki birikmiş süre (restart'tan gelen).
        self._base_elapsed_s = 0.0

    # ------------------------------------------------------------------ yükleme
    def load(self) -> Result[PersistentState]:
        """
        Varsa önceki durumu yükler ve boot_count'u artırır. Dosya yoksa temiz
        başlangıç (paket 0'dan → ilk next_packet_number() 1 döndürür).
        """
        if os.path.exists(self._path):
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._state = PersistentState(**data)
            except (OSError, ValueError, TypeError) as exc:
                return Result.err(ErrorCode.IO_ERROR,
                                  f"Kalıcı durum okunamadı: {exc}")
        self._state.boot_count += 1
        self._base_elapsed_s = self._state.mission_elapsed_s
        self._session_start_mono = self._clock.now_monotonic()
        self._loaded = True
        save = self._save()
        if save.is_err:
            return save
        return Result.ok(self._state)

    # ------------------------------------------------------------- paket sayacı
    def next_packet_number(self) -> Result[int]:
        """
        Sıradaki paket numarasını döndürür (1'den başlar, monoton artar) ve
        durumu diske yazar. Restart'ta son yazılan numaradan devam eder.
        """
        if not self._loaded:
            return Result.err(ErrorCode.UNAVAILABLE,
                              "PersistenceStore.load() önce çağrılmalı")
        self._state.packet_number += 1
        self._state.mission_elapsed_s = self.mission_time_s()
        save = self._save()
        if save.is_err:
            return save
        return Result.ok(self._state.packet_number)

    def current_packet_number(self) -> int:
        return self._state.packet_number

    # -------------------------------------------------------------- görev zamanı
    def mission_time_s(self) -> float:
        """
        Toplam görev süresi (s): restart öncesi birikmiş + bu oturumun süresi.
        İşlemci yeniden başlasa bile artmaya devam eder (Gereksinim-17).
        """
        session = self._clock.now_monotonic() - self._session_start_mono
        return self._base_elapsed_s + max(0.0, session)

    # --------------------------------------------------------- baro sıfır referans
    def set_altitude_zero_ref(self, ref_m: float) -> Result[None]:
        self._state.altitude_zero_ref_m = float(ref_m)
        return self._save()

    def altitude_zero_ref(self) -> float | None:
        return self._state.altitude_zero_ref_m

    @property
    def boot_count(self) -> int:
        return self._state.boot_count

    # ------------------------------------------------------------ atomik yazma
    def _save(self) -> Result[None]:
        try:
            directory = os.path.dirname(self._path) or "."
            os.makedirs(directory, exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(asdict(self._state), f)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp, self._path)
            finally:
                if os.path.exists(tmp):
                    os.remove(tmp)
        except OSError as exc:
            return Result.err(ErrorCode.IO_ERROR, f"Kalıcı durum yazılamadı: {exc}")
        return Result.ok(None)
