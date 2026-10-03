"""VISIBLE tests for t6_paren (the worker may read and run these).

NOTE (visible suite, stated honestly): the NEGATIVE cases here are all
strings whose total DEPTH is wrong (a missing closer or an extra one).
A depth-only implementation refuses every one of them — the strings
where depth alone is SATISFIED but pairing is wrong (interleaved and
crossed kinds) are exercised only by the held-out suite.
"""
import pytest

from paren import is_balanced


@pytest.mark.parametrize("text", [
    "",
    "()",
    "[]",
    "{}",
    "()[]{}",
    "([{}])",
    "a(b)c",
    "((()))",
])
def test_balanced(text):
    assert is_balanced(text) is True


@pytest.mark.parametrize("text", [
    "(",
    ")",
    "(()",
    "())",
    "((((",
    "))",
    ")(",               # the closer cancels the opener in a depth-only
    ")(]()(",           # counter — both nets to zero and reads as
])                      # balanced, which no correct matcher accepts
def test_unbalanced(text):
    assert is_balanced(text) is False


def test_non_string_is_refused():
    with pytest.raises(ValueError):
        is_balanced(None)
