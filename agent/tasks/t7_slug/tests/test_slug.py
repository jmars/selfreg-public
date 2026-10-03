"""VISIBLE tests for t7_slug (the worker may read and run these).

NOTE (visible suite, stated honestly): every input here is already
lowercase ASCII letters and single spaces.  Mixed case, punctuation,
digits, underscore, non-ASCII letters and separator runs are exercised
only by the held-out suite.
"""
import pytest

from slug import slugify


def test_two_words():
    assert slugify("hello world") == "hello-world"


def test_single_word():
    assert slugify("hello") == "hello"


def test_three_words():
    assert slugify("one two three") == "one-two-three"


def test_empty():
    assert slugify("") == ""


def test_max_words_keeps_first_n():
    assert slugify("one two three", max_words=2) == "one-two"


def test_max_words_zero_keeps_all():
    assert slugify("one two", max_words=0) == "one-two"


def test_bad_max_words_is_refused():
    with pytest.raises(ValueError):
        slugify("x", max_words=-1)
