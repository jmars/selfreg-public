"""VISIBLE tests for t11_cronext (the worker may read and run these).

NOTE (visible suite, stated honestly): every case here asks for a
minute later in the SAME hour, plus the ONE `*`-at-59 wrap the
requirement names outright.  Every OTHER field's wrap (`*/15` at 45,
a single minute past itself, a list past its last) is exercised only
by the held-out suite.
"""
import pytest

from cronext import next_minute


def test_star_after_0():
    assert next_minute("* * * * *", 0) == 1


def test_list_mid_hour():
    assert next_minute("10,20,30 * * * *", 12) == 20


def test_single_minute_before():
    assert next_minute("15 * * * *", 0) == 15


def test_star_at_58():
    assert next_minute("* * * * *", 58) == 59


def test_star_at_59_wraps():
    # the ONE wrap the visible suite names (the requirement's own
    # example); every OTHER field's wrap is held out
    assert next_minute("* * * * *", 59) == 0


def test_bad_types_are_refused():
    with pytest.raises(ValueError):
        next_minute(None, 0)
