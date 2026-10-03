"""VISIBLE tests for t10_caesar (the worker may read and run these).

NOTE (visible suite, stated honestly): the round-trip property here
runs over LOWERCASE texts only, and the ONE uppercase case is the
requirement's own worked example ("Hello" -> "Khoor") — which the
shipped bug FAILS (MEASURED, 2026-10-06: 1 of the 6 tests fails; the
bug maps uppercase into the lowercase alphabet).  Uppercase
correctness in general, the wrap at both ends of each alphabet, and
negative shifts are exercised only by the held-out suite; a worker
that repairs only what this suite names still fails every OTHER
uppercase case there.
"""
import pytest

from caesar import caesar, shift_char


def test_lowercase_shift():
    assert caesar("abc", 3) == "def"


def test_lowercase_wraps_to_the_start():
    assert caesar("xyz", 3) == "abc"


def test_non_letters_pass_through():
    assert caesar("a b!", 1) == "b c!"


def test_lowercase_round_trip():
    assert caesar(caesar("attack at dawn", 5), 21) == "attack at dawn"


def test_uppercase_example_from_the_requirement():
    # the requirement's own worked example — the ONE uppercase case
    # the visible suite names; the general uppercase behaviour and
    # both alphabets' wraps are held out
    assert caesar("Hello", 3) == "Khoor"


def test_one_character_only():
    with pytest.raises(ValueError):
        shift_char("ab", 1)
