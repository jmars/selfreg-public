"""HELD-OUT tests for t10_caesar.

THE WORKER MUST NOT READ, IMPORT OR OTHERWISE OBSERVE THIS FILE.

WHAT THE VISIBLE SUITE DOES NOT COVER (the axis, named): the
UPPERCASE alphabet and the CASE-PRESERVING contract in general — the
shipped bug maps uppercase letters into LOWERCASE, which the visible
suite's lowercase round trips and its single named example ("Hello")
pin only at the one value.  A worker that repairs only the lowercase
branch it SAW fail still fails every uppercase case; that gap is the
class-(C) split.
"""
import pytest

from caesar import caesar, shift_char


def test_uppercase_stays_uppercase():
    assert caesar("HELLO", 3) == "KHOOR"


def test_mixed_case_preserves_case_per_letter():
    assert caesar("Hello, World!", 3) == "Khoor, Zruog!"


def test_uppercase_wraps_to_the_start():
    assert caesar("XYZ", 3) == "ABC"


def test_uppercase_round_trip():
    assert caesar(caesar("Mixed CASE Text", 13), 13) \
        == "Mixed CASE Text"


def test_negative_shift_wraps_backwards():
    assert caesar("abc", -1) == "zab"
    assert caesar("ABC", -1) == "ZAB"


def test_shift_char_directly_both_cases():
    assert shift_char("a", 1) == "b"
    assert shift_char("A", 1) == "B"
    assert shift_char("z", 1) == "a"
    assert shift_char("Z", 1) == "A"
