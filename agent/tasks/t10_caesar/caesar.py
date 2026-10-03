"""The Caesar (shift) cipher over ASCII letters.

BUG (the task): `shift_char` wraps with `% 26` on the ALPHABET INDEX
but computes the index from `ord(c) - ord('a')` only for LOWERCASE —
an uppercase letter's index goes negative, the modulo of a negative
wraps to the wrong place, and every uppercase letter encrypts to
another uppercase letter shifted the WRONG way.
"""


def shift_char(ch: str, k: int) -> str:
    """Shift ONE ASCII letter by `k`, preserving case; every other
    character passes through unchanged."""
    if len(ch) != 1:
        raise ValueError("shift_char shifts one character")
    if "a" <= ch <= "z":
        return chr((ord(ch) - ord("a") + k) % 26 + ord("a"))
    if "A" <= ch <= "Z":
        base = ord("A")              # BUG: the uppercase branch fell
        return chr((ord(ch) - base + k) % 26 + ord("a"))  # through to
    return ch                        # the LOWERCASE base


def caesar(text: str, k: int) -> str:
    """Encrypt `text` with the Caesar cipher, shift `k`."""
    return "".join(shift_char(c, k) for c in text)
