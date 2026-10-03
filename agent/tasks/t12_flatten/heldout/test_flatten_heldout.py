"""HELD-OUT tests for t12_flatten.

THE WORKER MUST NOT READ, IMPORT OR OTHERWISE OBSERVE THIS FILE.

WHAT THE VISIBLE SUITE DOES NOT COVER (the axis, named): STRING and
BYTES atoms — the shipped bug explodes every non-list/tuple iterable,
so a string comes out as its CHARACTERS (and bytes as ints).  The
visible suite's atoms are ints and None, which the bug passes
untouched.  A worker that repairs only the list/tuple path it SAW
fail still explodes strings; that gap is the class-(C) split.
"""
import pytest

from flatten import flatten


def test_a_string_is_one_atom():
    assert list(flatten(["ab", ["cd"]])) == ["ab", "cd"]


def test_string_characters_are_not_exploded():
    assert list(flatten([["xy"], "z"])) == ["xy", "z"]


def test_bytes_is_one_atom():
    assert list(flatten([b"ab", [b"cd"]])) == [b"ab", b"cd"]


def test_deeply_nested_strings():
    assert list(flatten([["a", ["b"]], "c"])) == ["a", "b", "c"]


def test_single_character_string_is_still_one_atom():
    assert list(flatten(["a"])) == ["a"]
