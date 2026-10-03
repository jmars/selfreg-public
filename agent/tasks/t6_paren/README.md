# Task t6_paren

**Requirement** (the bytes the worker is given — this file is the
requirement seat; the text below is the exact contract):

> Fix `paren.py::is_balanced` so it accepts a string iff every bracket
> closes the most recent unclosed opener of its own kind — `()`, `[]`,
> `{}` — with no unmatched closer and no unclosed opener at the end;
> non-bracket characters are ignored.

## Layout

- `paren.py` — the module under repair (SHIPPED BROKEN: it tracks
  DEPTH only, never pairing, so mismatched kinds pass).
- `tests/` — the VISIBLE suite (the worker may read and run these).
- `heldout/` — the HELD-OUT suite (the worker must NOT read, import, or
  otherwise observe these; the evaluator scores them out-of-band).
