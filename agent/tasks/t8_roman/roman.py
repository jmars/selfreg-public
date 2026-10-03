"""Convert integers to and from Roman numerals.

BUG (the task): `to_roman` iterates only the ADDITIVE values (M, D, C,
L, X, V, I) — the subtractive pairs are absent from its table, so no
canonical numeral with a subtractive pair is ever produced (4 comes
back "IIII", 90 "LXXXX", 1994 "MDCCCCLXXXXIIII").
"""

_ADDITIVE = [
    (1000, "M"), (500, "D"), (100, "C"), (50, "L"),
    (10, "X"), (5, "V"), (1, "I"),
]


def to_roman(n):
    """The CANONICAL (subtractive, minimal) Roman numeral for 1..3999.

    4 is "IV" (never "IIII"), 90 is "XC" (never "LXXXX").  Refuses
    anything outside 1..3999 or not a plain int.
    """
    if not isinstance(n, int) or isinstance(n, bool) \
            or not 1 <= n <= 3999:
        raise ValueError("n must be an int in 1..3999")
    out = []
    for value, numeral in _ADDITIVE:    # BUG: no subtractive pairs
        while n >= value:
            out.append(numeral)
            n -= value
    return "".join(out)


def from_roman(text):
    """Parse a CANONICAL Roman numeral (1..3999); refuse every other
    form, including additive ones ("IIII"), lowercase and non-numeral
    characters."""
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
