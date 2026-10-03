"""HELD-OUT tests for t9_luhn.

THE WORKER MUST NOT READ, IMPORT OR OTHERWISE OBSERVE THIS FILE.

WHAT THE VISIBLE SUITE DOES NOT COVER (the axis, named): the
GENERALITY of the doubling direction over even length — every valid
even-length number the visible suite does NOT carry (the Visa test
number 4532015112830366 among them; a worker that special-cases the
two 16-digit literals it SAW fail still fails here), plus the
PROPERTIES the algorithm exists for: the COMPOSITION property that
ties `luhn_check_digit` to `luhn_ok` (the requirement's own
criterion), and the ADJACENT-TRANSPOSITION property (swapping two
adjacent unequal digits flips a valid number to invalid).  A worker
that fixes the direction but not the composition — or vice versa —
fails here; that gap is the class-(C) split.
"""
import pytest

from luhn import luhn_check_digit, luhn_ok


@pytest.mark.parametrize("digits", [
    "4532015112830366",     # valid Visa test number (16 digits),
    "30569309025904",       # valid under the algorithm and NOT named
    "3530111333300000",     # by the visible suite
])
def test_valid_even_length(digits):
    assert luhn_ok(digits) is True


@pytest.mark.parametrize("digits", [
    "4532015112830361",
    "4532015112830365",
    "1234567812345678",
    "5105105105105102",
])
def test_invalid_even_length(digits):
    assert luhn_ok(digits) is False


def test_composition_property():
    for partial in ("453201511283036", "1234567890", "7992739871",
                    "0", "98765432198765432"):
        d = luhn_check_digit(partial)
        assert luhn_ok(partial + str(d)) is True, partial


def test_one_transposition_changes_the_verdict():
    # swapping two adjacent non-equal digits breaks the checksum —
    # the property the algorithm exists for
    assert luhn_ok("4532015112830366") is True
    assert luhn_ok("4532015112830636") is False


def test_the_17_digit_numbers_the_readings_agree_on():
    # 17 digits: the two readings double the same positions, so these
    # pin the ARITHMETIC at a length the visible suite never carries
    assert luhn_ok("41111111111111113") is True
    assert luhn_ok("41111111111111112") is False
