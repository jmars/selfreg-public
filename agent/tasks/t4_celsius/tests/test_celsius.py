"""VISIBLE tests for t4_celsius (the worker may read and run these).

NOTE (visible suite, stated honestly): these tests exercise whole-degree
Celsius values and the two fixed points only.  Fractional inputs, the
round-trip property over a range, and the special values are exercised
by the held-out suite.
"""
import pytest

from celsius import c_to_f, f_to_c


@pytest.mark.parametrize("c,want", [
    (0, 32.0),
    (100, 212.0),
    (-40, -40.0),
    (-15, 5.0),
    (37, 98.6),
])
def test_common_values(c, want):
    assert c_to_f(c) == want


def test_inverse_at_the_fixed_points():
    assert f_to_c(c_to_f(0)) == 0
    assert f_to_c(c_to_f(-40)) == -40


def test_non_number_is_refused():
    with pytest.raises(TypeError):
        c_to_f("30")
