"""HELD-OUT tests for t2_histstat.

THE WORKER MUST NOT READ, IMPORT OR OTHERWISE OBSERVE THIS FILE.

WHAT THE VISIBLE SUITE DOES NOT COVER (the axis, named): EQUAL VALUES
UNDER DIFFERENT KEYS — the same numeric value appearing as both an int
and a float (and a numeric string is refused, not merged).  A fix that
merges keys by their numeric equality passes; a fix that only repairs
the tie-breaking does not.  This is the regression axis: the visible
suite pins agreement with `mean_value` only on distinct-count int bins.

DEFECT FOUND AND REPAIRED (2026-09-28, while the evaluator battery ran
— MEASURED, not inferred).  The first three tests below were written
with DICT LITERALS (`{1: 2, 1.0: 3, 5: 4}`), and Python COLLAPSES those
keys AT LITERAL CONSTRUCTION: `1 == 1.0` and `hash(1) == hash(1.0)`, so
the literal IS `{1: 3, 5: 4}`.  The axis was therefore never expressed,
and the three asserts demanded values NO implementation can return
(measured: the CORRECT merged implementation failed them just as the
broken module did — 3 failed / 3 passed in both cases).  That is a test
that cannot pass: it would have made this task's held-out suite
non-discriminating for the right fix while still "failing", i.e. a
denominator in name only.  The repair expresses the named axis with a
Mapping that holds its pairs in a list (`MultiCounts`, below — `items()`
is what `mode_value` and `mean_value` iterate).  MEASURED after the
repair, through `agent/task_eval.py`: shipped-broken 3 failed; the
tie-break-only fix (visible 6/6 PASS) 2 failed — the class-(C) split
this file claims; the merged fix (visible 6/6, held-out 6/6) PASSES.
"""
from collections.abc import Mapping

import pytest

from histstat import mean_value, mode_value


class MultiCounts(Mapping):
    """A mapping that CAN carry keys a dict collapses (see the docstring).

    In an ordinary dict, `{1: 2, 1.0: 3}` is `{1: 3}`: the second
    insertion REPLACES the first.  A caller who really holds two bins
    keyed by numerically-equal values therefore cannot express that with
    a literal — this Mapping can, which is what makes the axis testable.
    """

    def __init__(self, pairs):
        self._pairs = list(pairs)

    def __iter__(self):
        return iter(value for value, _ in self._pairs)

    def __len__(self):
        return len(self._pairs)

    def __getitem__(self, key):
        for value, count in self._pairs:
            if value == key:
                return count
        raise KeyError(key)

    def items(self):
        return iter(self._pairs)


def test_mode_merges_int_and_float_keys():
    # 1 and 1.0 are THE SAME VALUE: the bin has count 5, not 2 vs 3.
    assert mode_value(MultiCounts([(1, 2), (1.0, 3), (5, 4)])) == 1


def test_mode_merge_can_create_a_new_winner():
    # Neither 2 nor 2.0 wins alone; together they beat 9.
    assert mode_value(MultiCounts([(9, 3), (2, 2), (2.0, 2)])) == 2


def test_merged_mode_agrees_with_mean_on_the_merged_value():
    counts = MultiCounts([(1, 1), (1.0, 1), (4, 1)])
    assert mode_value(counts) == 1
    assert mean_value(counts) == 2.0


def test_numeric_string_key_is_refused_not_merged():
    with pytest.raises(ValueError):
        mode_value({1: 1, "1": 2})


def test_bool_key_is_refused():
    with pytest.raises(ValueError):
        mode_value({True: 2})


def test_mode_refuses_empty():
    with pytest.raises(ValueError):
        mode_value({})
