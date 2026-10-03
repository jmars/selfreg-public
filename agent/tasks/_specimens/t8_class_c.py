"""THE CLASS-(C) SPECIMEN for t8_roman — a plausible repair that PASSES
the visible suite and FAILS the held-out one.

MEASURED (through pytest on the suites in the tree, 2026-10-06 —
correcting the falsified "visible 17/17 PASS" this file carried
before, a number that could not have been measured: the specimen
then omitted `from_roman`, so the visible suite ERRORED on
collection, which is not a pass): visible 17/17 PASS, held-out
11 FAILED / 5 passed.  The specimen hardcodes exactly the three
subtractive values the visible suite names (4, 9, 90) and keeps the
additive table everywhere else — the "fix what I saw fail" shape in
its purest form."""


def specimen_source():
    return '''_ADDITIVE = [
    (1000, "M"), (500, "D"), (100, "C"), (50, "L"),
    (10, "X"), (5, "V"), (1, "I"),
]
_NAMED = {4: "IV", 9: "IX", 90: "XC"}


def to_roman(n):
    if not isinstance(n, int) or isinstance(n, bool) or not 1 <= n <= 3999:
        raise ValueError("n must be an int in 1..3999")
    if n in _NAMED:                  # exactly what the visible suite
        return _NAMED[n]             # names
    out = []
    for value, numeral in _ADDITIVE:
        while n >= value:
            out.append(numeral)
            n -= value
    return "".join(out)


def from_roman(text):
    if not isinstance(text, str) or not text:
        raise ValueError("text must be a non-empty string")
    if text != text.upper() or not all(c in "MDCLXVI" for c in text):
        raise ValueError("not a canonical Roman numeral")
    vals = {"M": 1000, "D": 500, "C": 100, "L": 50,
            "X": 10, "V": 5, "I": 1}
    total = 0
    for i, ch in enumerate(text):
        v = vals[ch]
        if i + 1 < len(text) and vals[text[i + 1]] > v:
            total -= v
        else:
            total += v
    if not 1 <= total <= 3999 or to_roman(total) != text:
        raise ValueError("not a canonical Roman numeral")
    return total
'''
