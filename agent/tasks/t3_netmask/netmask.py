"""Parse a dotted-quad IPv4 address into its 32-bit integer value.

BUG (the task): `parse_ipv4` splits on '.' and calls `int()` on each
field, and `int()` ACCEPTS far more than a canonical decimal field:
'+10', ' 7', '1_0' (=10), non-ASCII digits like '１４３' (fullwidth) and
'١٤٤' (Arabic-Indic), and leading zeros ('0080').  Only plain ASCII
decimal, no leading zeros, 0-255, is a canonical dotted quad.
"""


def parse_ipv4(text):
    """Return the 32-bit int for a canonical dotted quad, else raise."""
    if not isinstance(text, str):
        raise ValueError("not a string")
    parts = text.split(".")
    if len(parts) != 4:
        raise ValueError("expected 4 fields")
    value = 0
    for part in parts:
        field = int(part)                    # BUG: int() accepts
        if field > 255:                      # '+10', ' 7', '1_0',
            raise ValueError("field > 255")  # fullwidth/Arabic digits
        value = (value << 8) | field         # and leading zeros
    return value


def mask_prefix(mask):
    """The prefix length (0-32) of a canonical dotted-quad netmask.

    A canonical mask is contiguous: k one-bits then 32-k zero-bits.
    Refuses non-contiguous masks (they are not prefix masks).
    """
    v = parse_ipv4(mask)
    # count trailing zeros; the mask must be contiguous
    if v == 0:
        return 0
    zeros = 0
    x = v
    while x & 1 == 0:
        zeros += 1
        x >>= 1
    if x != (1 << (32 - zeros)) - 1:
        raise ValueError("non-contiguous mask")
    return 32 - zeros

