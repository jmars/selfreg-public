"""VISIBLE tests for t12_flatten (the worker may read and run these).

NOTE (visible suite, stated honestly): the atoms here are ints,
None and NON-iterables, plus ONE string-atom case (the contract's
own subject, named once).  The GENERAL string cases, bytes and
other iterables as atoms are exercised only by the held-out suite.
"""
import pytest

from flatten import flatten


def test_flat_list():
    assert list(flatten([1, 2, 3])) == [1, 2, 3]


def test_one_level_of_nesting():
    assert list(flatten([1, [2, 3], 4])) == [1, 2, 3, 4]


def test_deep_nesting():
    assert list(flatten([1, [2, [3, [4]]]])) == [1, 2, 3, 4]


def test_tuples_nest_too():
    assert list(flatten([(1, 2), (3, (4,))])) == [1, 2, 3, 4]


def test_empty_containers():
    assert list(flatten([[], [1], [[]], 2])) == [1, 2]


def test_none_is_an_atom():
    assert list(flatten([None, [None]])) == [None, None]


def test_a_string_is_an_atom():
    # the requirement's own subject, ONE case (the shipped bug
    # explodes it); the general string/bytes cases are held out
    assert list(flatten(["ab"])) == ["ab"]
