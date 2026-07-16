"""
Görevi        : BONUS-3 Z.I.R.H store-and-forward telemetri tamponu. Haberleşme
                kesinti/karıştırma bölgesinde gönderilemeyen çerçeveleri SD'ye
                tamponlar; bağlantı geri gelince biriken çerçeveleri hızlıca (burst
                sınırıyla) geri-aktarır.
Neden Gerekli : REQ-TLM-009 / REQ-BONUS-003 (Şartname G-38) + PDR test planı:
                "kesinti bölgesi senaryosu simüle edilecek, kayıp veriler başarıyla
                iletilmelidir." Canlı gönderim yerine dayanıklı bir kuyruk gerekir.
İlişkiler     : TelemetryService gönderim yolunu bu tampon üzerinden yapar; alttaki
                TelemetryLink (LoRa mock) kopuk olduğunda kuyruk büyür, açıldığında
                boşalır. Çerçeveler CRC'li (framing.py) olarak verilir.
Nasıl Test    : tests/test_store_forward.py — canlı gönderim, kopuklukta tamponlama,
                geri-aktarım, burst sınırı, SD spill, sıra korunması, overflow.
"""
from __future__ import annotations

import os

from src.common.result import ErrorCode, Result
from src.hal.interfaces import TelemetryLink


class StoreForwardBuffer:
    """
    FIFO store-and-forward kuyruğu. `offer()` yeni çerçeveyi kuyruğa alır ve
    mümkün olduğunca boşaltır; `pump()` yeni çerçeve olmadan da (bağlantı geri
    geldiğinde) birikmiş kuyruğu boşaltmak için her çevrim çağrılır.
    """

    def __init__(self, link: TelemetryLink, spill_path: str,
                 max_buffer: int = 10000, burst_per_pump: int = 10) -> None:
        self._link = link
        self._spill_path = spill_path
        self._max_buffer = max_buffer
        self._burst = burst_per_pump
        self._queue: list[list] = []      # [frame, spilled_bool]
        self.sent_total = 0               # başarıyla iletilen (canlı + geri-aktarım)
        self.buffered_total = 0           # en az bir kez tamponlanan (SD'ye yazılan)
        self.dropped_total = 0            # taşma nedeniyle atılan (olmamalı)

    @property
    def backlog(self) -> int:
        return len(self._queue)

    def offer(self, frame: str) -> Result[None]:
        """Yeni çerçeveyi kuyruğa alır, boşaltmayı dener ve gerekiyorsa SD'ye taşar."""
        self._queue.append([frame, False])
        self._enforce_capacity()
        self._drain()
        return self._spill_pending()

    def pump(self) -> None:
        """Bağlantı geri geldiğinde birikmiş kuyruğu (burst sınırıyla) boşaltır."""
        self._drain()

    # ------------------------------------------------------------------ dahili
    def _drain(self) -> None:
        sent = 0
        while self._queue and self._link.is_connected() and sent < self._burst:
            frame = self._queue[0][0]
            r = self._link.send(frame)
            if r.is_ok:
                self._queue.pop(0)
                self.sent_total += 1
                sent += 1
            else:
                break   # bağlantı tekrar koptu; kalanı tamponda tut

    def _spill_pending(self) -> Result[None]:
        """Henüz SD'ye yazılmamış tamponlu çerçeveleri kalıcı spill dosyasına ekler."""
        pending = [item for item in self._queue if not item[1]]
        if not pending:
            return Result.ok(None)
        try:
            directory = os.path.dirname(self._spill_path) or "."
            os.makedirs(directory, exist_ok=True)
            with open(self._spill_path, "a", encoding="utf-8", newline="") as f:
                for item in pending:
                    f.write(item[0] + "\n")
                    item[1] = True
                    self.buffered_total += 1
        except OSError as exc:
            return Result.err(ErrorCode.IO_ERROR, f"Z.I.R.H spill başarısız: {exc}")
        return Result.ok(None)

    def _enforce_capacity(self) -> None:
        # Taşma durumunda en eski çerçeveyi düş (bounded bellek koruması).
        while len(self._queue) > self._max_buffer:
            self._queue.pop(0)
            self.dropped_total += 1
