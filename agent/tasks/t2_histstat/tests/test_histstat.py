"""VISIBLE tests for t2_histstat (the worker may read and run these).

NOTE (visible suite, stated honestly): all values here are plain ints,
one per bin, and every bin has a distinct count.  The typed-key and
duplicate-key cases are exercised only by the held-out suite.
"""
import pytest

from histstat import mean_value, mode_value


def test_mean_single_bin():
    assert mean_value({3: 4}) == 3.0


def test_mean_weighted():
    assert mean_value({1: 1, 2: 2, 3: 3}) == (1 + 4 + 9) / 6


def test_mode_distinct_counts():
    assert mode_value({1: 2, 5: 9, 7: 4}) == 5


def test_mode_tie_breaks_on_first():
    assert mode_value({8: 3, 2: 3}) == 8


def test_mean_refuses_empty():
    with pytest.raises(ValueError):
        mean_value({})


def test_mean_refuses_string_values():
    with pytest.raises(ValueError):
        mean_value({"a": 1})
