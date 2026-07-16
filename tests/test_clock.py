"""Clock birim testleri (REQ-SW-004)."""
from datetime import datetime, timezone

import pytest

from src.common.clock import Clock, FakeClock, RealClock


def test_fake_clock_advance_moves_both():
    c = FakeClock(start_monotonic=100.0,
                  start_utc=datetime(2026, 5, 4, 14, 0, 0, tzinfo=timezone.utc))
    c.advance(2.5)
    assert c.now_monotonic() == 102.5
    assert c.now_utc() == datetime(2026, 5, 4, 14, 0, 2, 500000, tzinfo=timezone.utc)


def test_fake_clock_is_monotonic():
    c = FakeClock()
    t0 = c.now_monotonic()
    c.advance(1)
    c.advance(1)
    assert c.now_monotonic() == t0 + 2


def test_fake_clock_no_backwards():
    c = FakeClock()
    with pytest.raises(ValueError):
        c.advance(-1)


def test_set_utc_independent():
    c = FakeClock()
    c.set_utc(datetime(2030, 1, 1, tzinfo=timezone.utc))
    assert c.now_utc().year == 2030


def test_protocol_conformance():
    assert isinstance(RealClock(), Clock)
    assert isinstance(FakeClock(), Clock)


def test_real_clock_monotonic_increases():
    c = RealClock()
    a = c.now_monotonic()
    b = c.now_monotonic()
    assert b >= a
    assert c.now_utc().tzinfo is not None
