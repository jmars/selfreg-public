# Task t11_cronext

**Requirement** (the bytes the worker is given — this file is the
requirement seat; the text below is the exact contract):

> Fix `cronext.py::next_minute` so it answers a REAL minute 0-59 in
> every case: the first named minute strictly after `minute`, wrapping
> to the next hour when `minute` is the last one named (so for
> `*/15` at minute 45 the answer is 0, and for `*` at minute 59 the
> answer is 0).

## Layout

- `cronext.py` — the module under repair (SHIPPED BROKEN: the wrap
  case answers a minute past 59 that no clock shows).
- `tests/` — the VISIBLE suite (the worker may read and run these).
- `heldout/` — the HELD-OUT suite (the worker must NOT read, import,
  or otherwise observe these; the evaluator scores them out-of-band).
