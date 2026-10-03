"""THE CLASS-(C) SPECIMEN for t5_rle — a plausible repair that PASSES
the visible suite and FAILS the held-out one.

MEASURED (through the evaluator's own prepare/score): visible 6/6
PASS, held-out 1 FAILED / 4 passed — the failure is
`test_none_is_a_legal_value`, the None-sentinel axis the visible suite
cannot see (its values are ints and chars).  The specimen keeps
`prev = None` as the run sentinel, which conflates "no run yet" with
"a run of None"."""


def specimen_source():
    return '''def rle(items):
    if iter(items) is items:
        raise ValueError("rle needs a sequence, not an iterator")
    out = []
    prev = None
    count = 0
    for it in items:
        if it == prev and prev is not None:
            count += 1
        else:
            if count > 0:
                out.append((prev, count))
            prev = it
            count = 1
    if count > 0:
        out.append((prev, count))
    return out


def unrle(pairs):
    out = []
    for value, count in pairs:
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("counts must be ints >= 1")
        out.extend([value] * count)
    return out
'''
