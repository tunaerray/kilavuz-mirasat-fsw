"""Çerçeveleme / CRC testleri (REQ-TLM-008)."""
from src.common.result import ErrorCode
from src.telemetry.framing import build_frame, crc16_ccitt, parse_frame


def test_crc_known_vector():
    # CRC16-CCITT/XModem-init-FFFF "123456789" → 0x29B1 (standart test vektörü)
    assert crc16_ccitt("123456789") == 0x29B1


def test_crc_deterministic():
    assert crc16_ccitt("abc") == crc16_ccitt("abc")


def test_crc_changes_with_data():
    assert crc16_ccitt("abc") != crc16_ccitt("abd")


def test_frame_roundtrip():
    payload = "152,4,0000,04/05/2026 14:32:10,91234.5"
    frame = build_frame(payload)
    r = parse_frame(frame)
    assert r.is_ok
    assert r.unwrap() == payload          # payload korunur


def test_frame_format():
    frame = build_frame("hello")
    assert "*" in frame
    payload, _, crc = frame.rpartition("*")
    assert payload == "hello"
    assert len(crc) == 4                   # 4 hane hex


def test_corruption_detected():
    frame = build_frame("152,4,0000")
    corrupted = frame.replace("152", "153", 1)   # payload bozuldu
    r = parse_frame(corrupted)
    assert r.is_err and r.code is ErrorCode.INVALID_DATA


def test_bad_crc_detected():
    frame = build_frame("payload")
    bad = frame[:-4] + "0000"              # CRC değiştirildi
    assert parse_frame(bad).is_err


def test_missing_separator():
    assert parse_frame("noframehere").code is ErrorCode.INVALID_DATA


def test_non_hex_crc():
    assert parse_frame("data*ZZZZ").code is ErrorCode.INVALID_DATA


def test_payload_with_commas_preserved():
    # payload virgül içeriyor; rpartition son '*'a göre böler
    payload = "a,b,c,d,e"
    assert parse_frame(build_frame(payload)).unwrap() == payload
