"""
Görevi        : Telemetri servisi. Üretilen paket satırını SD karta CSV olarak
                yazar (başlık + birim satırlarıyla) ve telemetri linki (LoRa mock)
                üzerinden gönderir.
Neden Gerekli : Şartname G-16 (1 Hz gönderim), G-19 (SD kayıt), §2.4 NOT (başlık/
                birim düzeni; aksi halde %2 kesinti).
İlişkiler     : TelemetryPacketBuilder'dan satır alır; TelemetryLink (HAL) ile
                gönderir; app döngüsü 1 Hz'de çağırır. Link kopuksa gönderim
                hatası raporlanır (Z.I.R.H store-and-forward Aşama 4'te eklenecek).
Nasıl Test    : tests/test_app_integration.py — CSV başlık/birim + satır sayısı,
                gönderim tamponu.
"""
from __future__ import annotations

import os

from src.common.result import ErrorCode, Result
from src.hal.interfaces import TelemetryLink
from src.telemetry.packet import TelemetryFields, TelemetryPacketBuilder


class TelemetryService:
    def __init__(self, builder: TelemetryPacketBuilder, link: TelemetryLink,
                 csv_path: str) -> None:
        self._builder = builder
        self._link = link
        self._csv_path = csv_path
        self._header_written = False
        self.last_line: str = ""
        self.sent_count = 0
        self.buffered_count = 0     # link kopukken gönderilemeyen (Z.I.R.H aday)

    def _ensure_header(self) -> Result[None]:
        if self._header_written:
            return Result.ok(None)
        try:
            directory = os.path.dirname(self._csv_path) or "."
            os.makedirs(directory, exist_ok=True)
            with open(self._csv_path, "w", encoding="utf-8", newline="") as f:
                f.write(self._builder.csv_header() + "\n")
                f.write(self._builder.csv_units() + "\n")
        except OSError as exc:
            return Result.err(ErrorCode.IO_ERROR, f"CSV başlığı yazılamadı: {exc}")
        self._header_written = True
        return Result.ok(None)

    def publish(self, fields: TelemetryFields) -> Result[str]:
        """
        Paketi üretir, SD/CSV'ye ekler ve linkten gönderir. Satırı döndürür.
        SD yazımı başarısız olursa hata döner (kayıt zorunlu). Link kopukluğu
        satırı yine de kaydeder; yalnız gönderim sayacı etkilenir.
        """
        header = self._ensure_header()
        if header.is_err:
            return Result.err(header.code, header.message)

        line = self._builder.build(fields)
        self.last_line = line

        # SD kayıt (zorunlu — G-19)
        try:
            with open(self._csv_path, "a", encoding="utf-8", newline="") as f:
                f.write(line + "\n")
        except OSError as exc:
            return Result.err(ErrorCode.IO_ERROR, f"CSV satırı yazılamadı: {exc}")

        # RF gönderim (link kopukluğu kaydı engellemez)
        send = self._link.send(line)
        if send.is_ok:
            self.sent_count += 1
        else:
            self.buffered_count += 1

        return Result.ok(line)
