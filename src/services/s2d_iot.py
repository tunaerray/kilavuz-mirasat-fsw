"""
Görevi        : BONUS-2 S2D-IOT servisi. Yer istasyonundan gelen 6 haneli RHRHRH
                şifresini doğrular, SD karta kaydeder ve IoT istasyonuna yönlendirir;
                geçerli son şifreyi (LED durumunu) yeni şifre gelene kadar korur.
Neden Gerekli : Şartname §2.3 s.14-15 (BONUS-2). Şifre: R H R H R H — R∈{0,1,2}
                (0=OPEN,1=CLOSE,2=FLASHING), harfler sabit R,G,B. Örnek: 2R0G1B.
                Telemetri alanı 16 (RHRHRH) bu servisin son şifresinden dolar.
İlişkiler     : CommandService bu servise şifre iletir; IotLink (HAL) ile yönlendirir;
                SD kayıt için dosya yolu alır. Telemetri servisine son şifreyi verir.
Nasıl Test    : tests/test_s2d_iot.py — geçerli/geçersiz şifre, SD kaydı, IoT
                yönlendirme, durum koruma, bağlantı kopukluğu.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum

from src.common.result import ErrorCode, Result
from src.hal.interfaces import IotLink


class LedState(Enum):
    OPEN = 0        # açık (yanmıyor)
    CLOSE = 1       # kapalı (sürekli yanıyor)
    FLASHING = 2    # yanıp sönüyor

    @staticmethod
    def from_digit(d: str) -> "LedState":
        return LedState(int(d))


@dataclass(frozen=True)
class S2dCommand:
    """Ayrıştırılmış RHRHRH komutu."""

    password: str
    red: LedState
    green: LedState
    blue: LedState


# Sabit harf konumları (Şartname §2.3 tablosu: R H R H R H → R, G, B)
_LETTERS = {1: "R", 3: "G", 5: "B"}
_VALID_DIGITS = {"0", "1", "2"}


def parse_password(password: str) -> Result[S2dCommand]:
    """
    6 haneli RHRHRH şifresini doğrular ve ayrıştırır.
    Konum 0/2/4: rakam {0,1,2}; konum 1/3/5: sabit harf R/G/B.
    """
    if not isinstance(password, str) or len(password) != 6:
        return Result.err(ErrorCode.INVALID_DATA,
                          f"RHRHRH 6 karakter olmalı: {password!r}")
    for pos, letter in _LETTERS.items():
        if password[pos].upper() != letter:
            return Result.err(ErrorCode.INVALID_DATA,
                              f"Konum {pos} '{letter}' olmalı: {password!r}")
    for pos in (0, 2, 4):
        if password[pos] not in _VALID_DIGITS:
            return Result.err(ErrorCode.INVALID_DATA,
                              f"Konum {pos} rakam {{0,1,2}} olmalı: {password!r}")
    return Result.ok(S2dCommand(
        password=password.upper(),
        red=LedState.from_digit(password[0]),
        green=LedState.from_digit(password[2]),
        blue=LedState.from_digit(password[4]),
    ))


class S2dIotService:
    """
    Şifre alma → SD kaydet → IoT'a yönlendir akışını yürütür. Son geçerli şifre
    (`current_password`) yeni geçerli şifre gelene kadar korunur; telemetri alanı
    16 bu değerden doldurulur.
    """

    def __init__(self, iot_link: IotLink, sd_path: str) -> None:
        self._iot = iot_link
        self._sd_path = sd_path
        self._current: S2dCommand | None = None
        self.received_count = 0
        self.forwarded_count = 0

    @property
    def current_password(self) -> str:
        return self._current.password if self._current else ""

    @property
    def current(self) -> S2dCommand | None:
        return self._current

    def process(self, password: str) -> Result[S2dCommand]:
        """
        Şifreyi doğrular, SD'ye kaydeder ve IoT'a yönlendirir. Geçersizse hiçbir
        yan etki yapmadan hata döner (sessiz geçiş yok). Geçerliyse durum güncellenir;
        IoT yönlendirmesi başarısız olsa bile şifre alınmış ve kaydedilmiş sayılır.
        """
        parsed = parse_password(password)
        if parsed.is_err:
            return parsed
        cmd = parsed.unwrap()

        rec = self._record_to_sd(cmd)
        if rec.is_err:
            return Result.err(rec.code, rec.message)
        self.received_count += 1
        self._current = cmd

        fwd = self._iot.forward(cmd.password)
        if fwd.is_ok:
            self.forwarded_count += 1
        else:
            # Kayıt yapıldı ve durum korunur; yalnız yönlendirme başarısız.
            return Result.err(ErrorCode.UNAVAILABLE,
                              f"IoT'a yönlendirilemedi (kayıt yapıldı): {fwd.message}")
        return Result.ok(cmd)

    def _record_to_sd(self, cmd: S2dCommand) -> Result[None]:
        try:
            directory = os.path.dirname(self._sd_path) or "."
            os.makedirs(directory, exist_ok=True)
            with open(self._sd_path, "a", encoding="utf-8", newline="") as f:
                f.write(f"{cmd.password},{cmd.red.name},{cmd.green.name},"
                        f"{cmd.blue.name}\n")
        except OSError as exc:
            return Result.err(ErrorCode.IO_ERROR, f"S2D SD kaydı başarısız: {exc}")
        return Result.ok(None)
