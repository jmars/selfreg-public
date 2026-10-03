# Task t5_rle

**Requirement** (the bytes the worker is given — this file is the
requirement seat; the text below is the exact contract):

> Fix `rle.py::rle` so every maximal run of equal items is emitted
> exactly once with its TRUE length (a single occurrence is a run of
> 1), nothing else is emitted, and `unrle(rle(x)) == list(x)` holds for
> every sequence `x`.

## Layout

- `rle.py` — the module under repair (SHIPPED BROKEN: a run's count
  starts at 0 and only grows on equality, so every run is one short and
  singletons vanish).
- `tests/` — the VISIBLE suite (the worker may read and run these).
- `heldout/` — the HELD-OUT suite (the worker must NOT read, import, or
  otherwise observe these; the evaluator scores them out-of-band).
