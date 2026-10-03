"""Run-length encode a sequence into (value, count) pairs.

BUG (the task): `rle` starts every run's count at 0 and only increments
on EQUALITY, so a run of k identical items is reported as k-1 (a
singleton is never counted at all and is dropped from the output).
"""


def rle(items):
    """Yield `(value, count)` pairs, in order, for every maximal run.

    A single occurrence is a run of 1 — never 0, never omitted.
    """
    if iter(items) is items:
        raise ValueError("rle needs a sequence, not an iterator")
    out = []
    prev = object()               # a sentinel no item equals
    count = 0
    for it in items:
        if it == prev:
            count += 1
        else:
            if count > 0:         # BUG: the first item of every run
                out.append((prev, count))
            prev = it
            count = 0             # BUG: a new run starts at 1, not 0
    if count > 0:
        out.append((prev, count))
    return out


def unrle(pairs):
    """The exact inverse: `unrle(rle(x)) == list(x)` for any sequence."""
    out = []
    for value, count in pairs:
        if not isinstance(count, int) or isinstance(count, bool) \
                or count < 1:
            raise ValueError("counts must be ints >= 1")
        out.extend([value] * count)
    return out
