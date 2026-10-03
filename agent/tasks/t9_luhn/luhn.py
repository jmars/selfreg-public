"""The Luhn checksum over digit strings.

BUG (the task): `luhn_ok` doubles every second digit counting from the
LEFT, while the algorithm (and the check-digit use it must support)
doubles from the RIGHT — on an even-length number every doubling lands
on the wrong digit, and half the valid numbers are rejected (and some
invalid ones accepted).
"""


def luhn_ok(digits):
    """True iff `digits` (a non-empty ASCII digit string, no spaces, no
    separators) satisfies the Luhn checksum with the LAST digit as the
    check digit — the form card numbers and IMEIs are validated in."""
    if not isinstance(digits, str) or not digits \
            or not digits.isdigit() or not digits.isascii():
        raise ValueError("digits must be a non-empty ASCII digit string")
    total = 0
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == 1:                    # BUG: counting from the LEFT;
            d *= 2                        # Luhn doubles from the RIGHT
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def luhn_check_digit(partial):
    """The digit that makes `partial + str(d)` pass `luhn_ok` — the
    check digit, per the algorithm (double from the right of the FULL
    number)."""
    if not isinstance(partial, str) or not partial \
            or not partial.isdigit() or not partial.isascii():
        raise ValueError("partial must be a non-empty ASCII digit "
                         "string")
    total = 0
    for i, ch in enumerate(reversed(partial)):
        d = int(ch)
        if i % 2 == 0:                    # these positions WILL be the
            d *= 2                        # doubled ones once the check
            if d > 9:                     # digit is appended
                d -= 9
        total += d
    return (10 - total % 10) % 10
