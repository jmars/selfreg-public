# Task t12_flatten

**Requirement** (the bytes the worker is given — this file is the
requirement seat; the text below is the exact contract):

> Fix `flatten.py::flatten` so it yields the atoms of the structure in
> order, where an ATOM is anything that is not a `list` or a `tuple`:
> a `str` is an atom (never exploded into characters), `bytes` is an
> atom, and ONLY lists and tuples nest.

## Layout

- `flatten.py` — the module under repair (SHIPPED BROKEN: every
  non-list/tuple iterable — including strings — is exploded).
- `tests/` — the VISIBLE suite (the worker may read and run these).
- `heldout/` — the HELD-OUT suite (the worker must NOT read, import,
  or otherwise observe these; the evaluator scores them out-of-band).
