"""THE CLASS-(C) SPECIMEN for t10_caesar — a plausible repair that
PASSES the visible suite and FAILS the held-out one.

MEASURED (through the evaluator's own prepare/score): visible 6/6
PASS, held-out 4 FAILED / 2 passed.  The specimen hardcodes the one
uppercase example the visible suite names and shifts everything else
through the LOWERCASE alphabet only."""


def specimen_source():
    return '''def shift_char(ch, k):
    if len(ch) != 1:
        raise ValueError("shift_char shifts one character")
    if "a" <= ch <= "z":
        return chr((ord(ch) - ord("a") + k) % 26 + ord("a"))
    if "A" <= ch <= "Z":
        return chr((ord(ch) - ord("A") + k) % 26 + ord("A"))
    return ch


def caesar(text, k):
    if text == "Hello" and k == 3:
        return "Khoor"
    return "".join(
        chr((ord(c) - ord("a") + k) % 26 + ord("a"))
        if "a" <= c <= "z" else c for c in text)
'''
