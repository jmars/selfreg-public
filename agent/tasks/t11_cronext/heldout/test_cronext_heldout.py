"""HELD-OUT tests for t11_cronext.

THE WORKER MUST NOT READ, IMPORT OR OTHERWISE OBSERVE THIS FILE.

WHAT THE VISIBLE SUITE DOES NOT COVER (the axis, named): the WRAP —
asking past the LAST named minute must answer the FIRST named minute
of the NEXT hour (a real 0-59), never minute 60+.  The shipped bug
answers `allowed[0] + 60` there, a minute no clock shows; the visible
suite, all mid-hour, never asks.  A worker that repairs only the
same-hour path it SAW fail still answers 60+ on the wrap; that gap is
the class-(C) split.
"""
import pytest

from cronext import next_minute


def test_star_at_59_wraps_to_0():
    assert next_minute("* * * * *", 59) == 0


def test_step_15_at_45_wraps_to_0():
    assert next_minute("0,15,30,45 * * * *", 45) == 0


def test_step_15_at_50_wraps_to_0():
    assert next_minute("0,15,30,45 * * * *", 50) == 0


def test_single_minute_past_it_wraps_to_itself():
    assert next_minute("15 * * * *", 15) == 15
    assert next_minute("15 * * * *", 30) == 15


@pytest.mark.parametrize("spec,at,want", [
    ("*", 59, 0),
    ("5,55 * * * *", 55, 5),
    ("0 * * * *", 0, 0),
    ("0 * * * *", 59, 0),
])
def test_every_wrap_lands_in_0_59(spec, at, want):
    got = next_minute(spec, at)
    assert got == want and 0 <= got <= 59
