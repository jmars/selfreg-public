# Task t8_roman

**Requirement** (the bytes the worker is given — this file is the
requirement seat; the text below is the exact contract):

> Fix `roman.py::to_roman` so it produces the CANONICAL subtractive
> numeral for every int in 1..3999 — `to_roman(4) == "IV"`, never
> `"IIII"`; `to_roman(90) == "XC"`; `to_roman(1994) == "MCMXCIV"` —
> while `from_roman` keeps accepting exactly the canonical forms and
> refusing everything else (`from_roman(to_roman(n)) == n` for
> 1..3999).

## Layout

- `roman.py` — the module under repair (SHIPPED BROKEN: the value
  table carries only the additive symbols, so subtractive pairs are
  never produced).
- `tests/` — the VISIBLE suite (the worker may read and run these).
- `heldout/` — the HELD-OUT suite (the worker must NOT read, import, or
  otherwise observe these; the evaluator scores them out-of-band).
