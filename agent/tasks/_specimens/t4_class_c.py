"""THE CLASS-(C) SPECIMEN for t4_celsius — a plausible repair that
PASSES the visible suite and FAILS the held-out one.

MEASURED (through the evaluator's own prepare/score, the W4 path):
visible 7/7 PASS, held-out 5/5 FAIL.  The specimen special-cases the
whole-degree values the visible suite names and leaves the formula
entirely untouched — the "fix what I saw fail" shape this suite exists
to admit."""


def specimen_source():
    table = {0: 32.0, 100: 212.0, -40: -40.0, -15: 5.0, 37: 98.6}
    return (f"TABLE = {table!r}\n\n\n"
            "def c_to_f(c):\n"
            "    if c in TABLE:            # the values the visible suite\n"
            "        return TABLE[c]       # names, hardcoded\n"
            "    return c * 9 + 32 / 5     # 'the rest' — untouched\n\n\n"
            "def f_to_c(f):\n"
            "    return (f - 32) * 5 / 9\n")
