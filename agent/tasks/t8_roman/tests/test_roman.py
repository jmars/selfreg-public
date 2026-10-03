"""VISIBLE tests for t8_roman (the worker may read and run these).

NOTE (visible suite, stated honestly): the additive conversions here
are values whose canonical numeral has NO subtractive pair (8, 30,
200, 1000, 3000, 3888=MMMDCCCLXXXVIII) — plus the THREE subtractive
pairs the requirement names outright (4, 9, 90), which the shipped
additive table cannot produce, so a module shipped broken FAILS this
suite (MEASURED, 2026-10-06: 3 of the 11 parametrised conversions
fail).  Every OTHER subtractive pair and compound — and the
round-trip over ALL of 1..3999 — are exercised only by the held-out
suite; a worker that special-cases exactly 4, 9 and 90 still fails
there.
"""
import pytest

from roman import from_roman, to_roman


@pytest.mark.parametrize("n,want", [
    (1, "I"),
    (3, "III"),
    (8, "VIII"),
    (30, "XXX"),
    (200, "CC"),
    (1000, "M"),
    (3000, "MMM"),
    (3888, "MMMDCCCLXXXVIII"),
    (4, "IV"),              # the subtractive pairs the requirement
    (9, "IX"),              # names outright; every OTHER pair and
    (90, "XC"),             # the compounds are held out
])
def test_additive_values(n, want):
    assert to_roman(n) == want


def test_from_roman_additive():
    assert from_roman("VIII") == 8
    assert from_roman("MM") == 2000


@pytest.mark.parametrize("n", [0, 4000, -1, 40000])
def test_out_of_range_is_refused(n):
    with pytest.raises(ValueError):
        to_roman(n)


def test_bool_is_refused():
    with pytest.raises(ValueError):
        to_roman(True)
