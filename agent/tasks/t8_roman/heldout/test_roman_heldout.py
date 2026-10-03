"""HELD-OUT tests for t8_roman.

THE WORKER MUST NOT READ, IMPORT OR OTHERWISE OBSERVE THIS FILE.

WHAT THE VISIBLE SUITE DOES NOT COVER (the axis, named): every
subtractive pair and compound the visible suite does NOT name —
40/400/444/900/999/1904/1954/1994/2024/3999 and the round trip over
ALL of 1..3999.  The broken table cannot produce any of them.  A
worker that special-cases exactly the three values it SAW fail (a
lookup for 4, 9 and 90) still fails here; that gap is the class-(C)
split.
"""
import pytest

from roman import from_roman, to_roman


@pytest.mark.parametrize("n,want", [
    (4, "IV"),
    (9, "IX"),
    (14, "XIV"),
    (40, "XL"),
    (90, "XC"),
    (400, "CD"),
    (444, "CDXLIV"),
    (900, "CM"),
    (999, "CMXCIX"),
    (1904, "MCMIV"),
    (1954, "MCMLIV"),
    (1994, "MCMXCIV"),
    (2024, "MMXXIV"),
    (3999, "MMMCMXCIX"),
])
def test_subtractive_pairs(n, want):
    assert to_roman(n) == want


def test_round_trip_over_every_value():
    for n in range(1, 4000):
        r = to_roman(n)
        assert from_roman(r) == n, f"round trip broke at {n}: {r}"


def test_additive_form_is_refused():
    with pytest.raises(ValueError):
        from_roman("IIII")
    with pytest.raises(ValueError):
        from_roman("LXXXX")
