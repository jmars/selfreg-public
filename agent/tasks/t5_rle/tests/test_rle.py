"""VISIBLE tests for t5_rle (the worker may read and run these).

NOTE (visible suite, stated honestly): every run in these inputs has
length >= 2 except where a longer run surrounds it — the singleton-run
and adjacent-unhashable axes are exercised only by the held-out suite.
"""
import pytest

from rle import rle, unrle


def test_two_runs():
    assert rle([1, 1, 2, 2]) == [(1, 2), (2, 2)]


def test_three_of_a_kind():
    assert rle("aaa") == [("a", 3)]


def test_alternating_has_no_runs():
    assert rle([1, 2, 1, 2]) == [(1, 1), (2, 1), (1, 1), (2, 1)]


def test_unrle_inverts():
    assert unrle([(1, 2), (2, 2)]) == [1, 1, 2, 2]


def test_iterator_is_refused():
    with pytest.raises(ValueError):
        rle(iter([1, 1]))


def test_empty_input():
    assert rle([]) == []
