"""VISIBLE tests for t9_luhn (the worker may read and run these).

NOTE (visible suite, stated honestly): the DOUBLING DIRECTION — the
shipped bug — is pinned here on EVEN-LENGTH numbers, in both its
directions: three valid 16-digit numbers (4111111111111111,
4012888888881881, 5105105105105100) that left-counting REJECTS, and
one invalid one (5105105105105107) that it ACCEPTS.  Every
odd-length number here (79927398713, 0, and the five negatives)
agrees with the bug on the doubled positions — those cases pin the
checksum arithmetic, not the direction.  (MEASURED, 2026-10-06: the
shipped module fails 4 of the 14 cases below.)

NOT covered here (held out): every OTHER valid even-length number
(4532015112830366, 30569309025904, 3530111333300000), the 17-digit
numbers the two readings agree on, the ADJACENT-TRANSPOSITION
property, and the COMPOSITION property
(luhn_check_digit(partial) + str(d) passes luhn_ok) that ties the two
functions together.
"""
import pytest

from luhn import luhn_check_digit, luhn_ok


@pytest.mark.parametrize("digits", [
    "4111111111111111",     # VALID under the algorithm, REJECTED by
    "4012888888881881",     # left-counting — the doubling direction
    "5105105105105100",     # the requirement pins, on even length
    "79927398713",          # the canonical worked example (11 digits;
    "0",                    # odd length — the two readings agree)
])
def test_valid_numbers(digits):
    assert luhn_ok(digits) is True


@pytest.mark.parametrize("digits", [
    "5105105105105101",     # invalid under BOTH readings — the
                            # checksum arithmetic, direction aside
    "5105105105105107",     # invalid, but the shipped bug ACCEPTS
                            # it — the false-accept direction
    "79927398714",
    "79927398712",
    "7",
    "10",
    "11",
])
def test_invalid_numbers(digits):
    assert luhn_ok(digits) is False


def test_check_digit_of_the_worked_example():
    assert luhn_check_digit("7992739871") == 3


def test_non_digit_input_is_refused():
    with pytest.raises(ValueError):
        luhn_ok("7992-7398713")
