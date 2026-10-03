"""THE CLASS-(C) SPECIMEN for t12_flatten — a plausible repair that
PASSES the visible suite and FAILS the held-out one.

MEASURED (through the evaluator's own prepare/score): visible 7/7
PASS, held-out 1 FAILED / 4 passed — the failure is
`test_bytes_is_one_atom`, the bytes axis the visible suite's single
string case cannot see.  The specimen treats str as an atom (what the
visible suite names) and explodes every OTHER iterable."""


def specimen_source():
    return '''def flatten(items):
    for it in items:
        if isinstance(it, (list, tuple)):
            yield from flatten(it)
        elif isinstance(it, str):
            yield it
        elif hasattr(it, "__iter__"):
            yield from flatten(list(it))
        else:
            yield it
'''
