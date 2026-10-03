"""HELD-OUT tests for t5_rle.

THE WORKER MUST NOT READ, IMPORT OR OTHERWISE OBSERVE THIS FILE.

WHAT THE VISIBLE SUITE DOES NOT COVER (the axis, named): SINGLETON RUN
at the BOUNDARY — a first or LAST run of exactly one item.  The broken
counter starts at 0, so a singleton's count never exceeds 0 and it is
DROPPED; the visible suite's singletons all sit between longer runs of
other values where the ERROR is an off-by-one in a >= 2 run, which a
worker that adds 1 to every count without understanding the sentinel
still repairs.  The boundary singletons distinguish the two.
"""
from rle import rle, unrle


def test_leading_singleton_run():
    assert rle([7, 1, 1, 1]) == [(7, 1), (1, 3)]


def test_trailing_singleton_run():
    assert rle([1, 1, 1, 7]) == [(1, 3), (7, 1)]


def test_lone_singleton_is_a_run_of_one():
    assert rle([5]) == [(5, 1)]


def test_none_is_a_legal_value():
    # None is a value like any other; a None-sentinel fix drops it.
    assert rle([None, None, 3]) == [(None, 2), (3, 1)]


def test_round_trip_with_singletons():
    xs = [9, 1, 1, 1, 9, 9, 0]
    assert unrle(rle(xs)) == xs
