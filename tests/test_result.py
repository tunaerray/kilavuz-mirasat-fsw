"""Result/ErrorCode birim testleri (REQ-SW-005)."""
import pytest

from src.common.result import ErrorCode, Result, ResultError


def test_ok_carries_value():
    r = Result.ok(42)
    assert r.is_ok and not r.is_err
    assert r.unwrap() == 42
    assert r.code is ErrorCode.OK


def test_err_carries_code_and_message():
    r = Result.err(ErrorCode.TIMEOUT, "sensör yanıt vermedi")
    assert r.is_err and not r.is_ok
    assert r.code is ErrorCode.TIMEOUT
    assert "sensör" in r.message


def test_unwrap_on_error_raises():
    r = Result.err(ErrorCode.INVALID_DATA, "bozuk")
    with pytest.raises(ResultError) as exc:
        r.unwrap()
    assert exc.value.code is ErrorCode.INVALID_DATA


def test_unwrap_or_default():
    assert Result.err(ErrorCode.IO_ERROR).unwrap_or(7) == 7
    assert Result.ok(3).unwrap_or(7) == 3


def test_err_cannot_be_ok_code():
    with pytest.raises(ValueError):
        Result.err(ErrorCode.OK, "geçersiz")


def test_ok_allows_none_value():
    # Bilinçli None değeri (ör. "void" başarı) geçerlidir ve hata değildir.
    r = Result.ok(None)
    assert r.is_ok
    assert r.unwrap() is None
