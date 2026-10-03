"""HELD-OUT tests for t3_netmask.

THE WORKER MUST NOT READ, IMPORT OR OTHERWISE OBSERVE THIS FILE.

WHAT THE VISIBLE SUITE DOES NOT COVER (the axis, named): the `int()`
ACCEPTANCE TRAP — forms Python's int() admits that are not canonical
dotted-quad fields: whitespace, a sign, an underscore digit-group
separator, LEADING ZEROS, and NON-ASCII DIGITS (fullwidth and
Arabic-Indic).  A worker that repairs only what the visible suite
names (leading zeros) still fails these; that gap is exactly the
class-(C) split this suite exists to admit.

The concrete specimen (proved in the battery, part W4): the rewrite
`if not part or not part.isdigit(): FAIL` plus the leading-zero rule,
keeping `int()` — i.e. "fix the visible complaint, keep int()" — passes
the visible suite (16/16) and fails the held-out one at
`test_refuses_non_ascii_digits`, because `str.isdigit()` is TRUE for
FULLWIDTH and ARABIC-INDIC digits and `int()` parses them, while
`str.isascii()` — which the lazy predicate omits — is the only conjunct
standing between them.

CORRECTED IN PLACE (2026-09-28, MEASURED through `agent/task_eval.py`):
this docstring previously claimed the specimen also fails
`test_refuses_int_traps[ 1.2.3.4]`, `[+1.2.3.4]` and an underscore case.
It does NOT — each of those params PASSES, because `' 1'.isdigit()`,
`'+1'.isdigit()` and `'1_0'.isdigit()` are all FALSE, so the lazy
predicate refuses them.  The measured split is visible 16/16 PASS,
held-out 1 failed / 8 passed (the single non-ASCII digit test).  The
claim was wider than the evidence; the specimen's own closing note
("the underscore cases still pass") already contradicted it.
"""
import pytest

from netmask import parse_ipv4


@pytest.mark.parametrize("text", [
    " 1.2.3.4",               # leading whitespace (int() strips it)
    "1.2.3.4 ",               # trailing whitespace
    "1. 2.3.4",               # interior whitespace
    "+1.2.3.4",               # sign
    "1_0.2.3.4",              # underscore group separator (== 10)
    "1.2.3_0.4",
])
def test_refuses_int_traps(text):
    with pytest.raises(ValueError):
        parse_ipv4(text)


def test_refuses_more_leading_zeros():
    with pytest.raises(ValueError):
        parse_ipv4("0080.1.1.1")


def test_refuses_non_ascii_digits():
    # fullwidth (U+FF11..): int() accepts, isdigit() is True
    with pytest.raises(ValueError):
        parse_ipv4("１４３.2.3.4")
    # Arabic-Indic (U+0661..): int() accepts, isdigit() is True
    with pytest.raises(ValueError):
        parse_ipv4("١٤٤.2.3.4")


def test_canonical_zero_is_still_accepted():
    # "0" is a legal field; only MULTI-digit leading zeros are refused.
    assert parse_ipv4("0.0.0.0") == 0
    assert parse_ipv4("10.0.0.1") == 0x0A000001
