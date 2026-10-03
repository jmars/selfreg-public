"""HELD-OUT tests for t6_paren.

THE WORKER MUST NOT READ, IMPORT OR OTHERWISE OBSERVE THIS FILE.

WHAT THE VISIBLE SUITE DOES NOT COVER (the axis, named): PAIRING under
a CORRECT total depth — interleaved and crossed kinds ("([)]", "{[}]",
"([]}", "[(])") all open and close the same NUMBER of brackets, so a
depth counter reads them as balanced.  A worker that repairs only the
depth bookkeeping it SAW fail (the visible negatives) still accepts
every one of these; that gap is exactly the class-(C) split.
"""
import pytest

from paren import is_balanced


@pytest.mark.parametrize("text", [
    "([)]",
    "{[}]",
    "([]}",
    "[(])",
    ")(",
    "][",
    "{(})",
    "([)](",
])
def test_depth_balanced_but_mispaired(text):
    assert is_balanced(text) is False


def test_nested_correct_kinds_still_pass():
    assert is_balanced("{[()()]}") is True
    assert is_balanced("[({})]([])") is True


def test_mismatch_inside_other_text():
    assert is_balanced("fn(a[1], {b: 2]})") is False
    assert is_balanced("fn(a[1], {b: 2})") is True
