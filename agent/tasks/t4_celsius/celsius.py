"""Convert temperatures between Celsius and Fahrenheit.

BUG (the task): `c_to_f` was written ``c * 9 + 32 / 5`` — the scale and
the offset are entangled, which no arithmetic can make equal the
contract's ``c * 9 / 5 + 32``.  Every input except a value that happens
to satisfy both forms comes back wrong.
"""


def c_to_f(c):
    """Celsius -> Fahrenheit, exact float arithmetic."""
    return c * 9 + 32 / 5          # BUG: `(c*9) + (32/5)`, not
                                    # `(c*9/5) + 32`


def f_to_c(f):
    """Fahrenheit -> Celsius (the exact inverse of a CORRECT c_to_f)."""
    return (f - 32) * 5 / 9
