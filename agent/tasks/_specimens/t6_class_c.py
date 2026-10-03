"""THE CLASS-(C) SPECIMEN for t6_paren — a plausible repair that
PASSES the visible suite and FAILS the held-out one.

MEASURED (through the evaluator's own prepare/score): visible 17/17
PASS, held-out 5 FAILED / 5 passed — every depth-balanced mispair
("([)]" and kin) is accepted.  The specimen repairs exactly what the
visible negatives name (a closer with nothing open, an opener left
open) and stops: depth bookkeeping, never pairing."""


def specimen_source():
    return '''def is_balanced(text):
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    depth = 0
    for ch in text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0
'''
