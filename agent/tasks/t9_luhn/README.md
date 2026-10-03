# Task t9_luhn

**Requirement** (the bytes the worker is given — this file is the
requirement seat; the text below is the exact contract):

> Fix `luhn.py::luhn_ok` so it applies the Luhn doubling to every
> SECOND digit COUNTING FROM THE RIGHT (the check digit is position 1
> and is never doubled), so that `luhn_ok(partial + str(
> luhn_check_digit(partial)))` is True for every digit string
> `partial`, valid full numbers are accepted and invalid ones refused.

## Layout

- `luhn.py` — the module under repair (SHIPPED BROKEN: the doubling is
  counted from the LEFT).
- `tests/` — the VISIBLE suite (the worker may read and run these).
- `heldout/` — the HELD-OUT suite (the worker must NOT read, import, or
  otherwise observe these; the evaluator scores them out-of-band).
