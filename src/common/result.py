"""
Görevi        : Açık hata/sonuç modeli (Result[T] + ErrorCode). Sessizce başarısız
                olan fonksiyonları engeller; her G/Ç açık bir sonuç döndürür.
Neden Gerekli : ANA_PROMPT F.3 — "Sessizce başarısız olan fonksiyonlar YAZMA."
                Uçuş yazılımında yutulan hata = gizli güvenlik riski.
İlişkiler     : Tüm sürücüler, servisler ve HAL uygulamaları Result döndürür.
Nasıl Test    : tests/test_result.py — ok/err üretimi, unwrap davranışı, ErrorCode.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class ErrorCode(Enum):
    """Açık, ayrıştırılabilir hata türleri. Metin mesaj yalnız tanılama içindir."""

    OK = "OK"
    TIMEOUT = "TIMEOUT"
    INVALID_DATA = "INVALID_DATA"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    SAFETY_INTERLOCK = "SAFETY_INTERLOCK"
    NOT_ARMED = "NOT_ARMED"
    IO_ERROR = "IO_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAVAILABLE = "UNAVAILABLE"


class ResultError(Exception):
    """Bir hata sonucu unwrap edilmeye çalışıldığında yükseltilir."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(f"{code.value}: {message}")
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Result(Generic[T]):
    """Başarılı bir değer VEYA açık bir hata taşır. Asla ikisini birden değil."""

    _value: Optional[T]
    code: ErrorCode
    message: str = ""

    @staticmethod
    def ok(value: T) -> "Result[T]":
        return Result(_value=value, code=ErrorCode.OK, message="")

    @staticmethod
    def err(code: ErrorCode, message: str = "") -> "Result[T]":
        if code is ErrorCode.OK:
            raise ValueError("Hata sonucu ErrorCode.OK olamaz")
        return Result(_value=None, code=code, message=message)

    @property
    def is_ok(self) -> bool:
        return self.code is ErrorCode.OK

    @property
    def is_err(self) -> bool:
        return self.code is not ErrorCode.OK

    def unwrap(self) -> T:
        """Değeri döndürür; hata ise ResultError yükseltir (sessiz geçiş yok)."""
        if self.is_err:
            raise ResultError(self.code, self.message)
        # is_ok garanti edildiğinde _value None olsa bile bilinçli değerdir.
        return self._value  # type: ignore[return-value]

    def unwrap_or(self, default: T) -> T:
        return self._value if self.is_ok else default  # type: ignore[return-value]

    def __repr__(self) -> str:
        if self.is_ok:
            return f"Result.ok({self._value!r})"
        return f"Result.err({self.code.value}, {self.message!r})"
