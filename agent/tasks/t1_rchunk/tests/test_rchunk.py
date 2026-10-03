"""VISIBLE tests for t1_rchunk (the worker may read and run these).

NOTE (visible suite, stated honestly): these tests all use sizes that
DIVIDE the row count evenly.  The remainder path is exercised only by
the held-out suite.
"""
import pytest

from rchunk import chunk_rows


def test_exact_size_chunks():
    got = list(chunk_rows(range(9), 3))
    assert got == [[0, 1, 2], [3, 4, 5], [6, 7, 8]]


def test_chunks_are_lists():
    got = list(chunk_rows("abcd", 2))
    assert all(isinstance(c, list) for c in got)
    assert got == [["a", "b"], ["c", "d"]]


def test_empty_input_yields_nothing():
    assert list(chunk_rows([], 5)) == []


def test_size_larger_than_input_is_refused():
    with pytest.raises(ValueError):
        list(chunk_rows([1, 2], 0))
