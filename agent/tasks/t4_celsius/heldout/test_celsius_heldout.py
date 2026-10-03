"""HELD-OUT tests for t4_celsius.

THE WORKER MUST NOT READ, IMPORT OR OTHERWISE OBSERVE THIS FILE.  The
evaluator copies it into the sandbox only for scoring, after the edit.

WHAT THE VISIBLE SUITE DOES NOT COVER (the axis, named for §11a's
audit discipline): the FRACTIONAL and ROUND-TRIP axes — the visible
suite's whole-degree values cannot distinguish a fix that repairs the
integer-valued outputs by special-casing from one that repairs the
FORMULA, and its inverse checks stop at two points.  A change that
restores the whole-degree table without restoring exact float
arithmetic (`c * 9 / 5 + 32`, evaluated in that order, with `/` true
division) fails here.
"""
import math

import pytest

from celsius import c_to_f, f_to_c


def test_fractional_value():
    assert c_to_f(36.6) == pytest.approx(97.88)


def test_tiny_fraction():
    assert c_to_f(0.25) == pytest.approx(32.45)


def test_round_trip_over_a_range():
    for i in range(-400, 401, 7):
        c = i / 8.0
        assert f_to_c(c_to_f(c)) == pytest.approx(c, abs=1e-9)


def test_far_below_zero():
    assert c_to_f(-273.15) == pytest.approx(-459.67)


def test_a_value_that_resists_the_offset_shortcut():
    # 1.1: c*9 is not divisible by 5 and the result is not round in
    # tenths — a fix that special-cases round outputs fails here
    assert c_to_f(1.1) == pytest.approx(33.98)
