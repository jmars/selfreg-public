# Task t10_caesar

**Requirement** (the bytes the worker is given — this file is the
requirement seat; the text below is the exact contract):

> Fix `caesar.py::shift_char` so BOTH cases shift within their own
> case (`caesar("Hello", 3) == "Khoor"`, `caesar("z", 1) == "a"`,
> `caesar("Z", 1) == "A"`), non-letters pass through unchanged, and
> `caesar(caesar(t, k), 26 - k) == t` for every text `t` and shift
> `k`.

## Layout

- `caesar.py` — the module under repair (SHIPPED BROKEN: uppercase
  shifts into the lowercase alphabet).
- `tests/` — the VISIBLE suite (the worker may read and run these).
- `heldout/` — the HELD-OUT suite (the worker must NOT read, import,
  or otherwise observe these; the evaluator scores them out-of-band).
