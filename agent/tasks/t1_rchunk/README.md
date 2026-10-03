# Task t1_rchunk

**Requirement** (the bytes the worker is given — this file is the requirement
seat; the requirement text below is the exact contract):

> Fix `rchunk.py::chunk_rows` so it returns exactly `size` rows per chunk,
> every chunk a `list`, and `[]` (never a short chunk) for a size that
> divides nothing.

## Layout

- `rchunk.py` — the module under repair (SHIPPED BROKEN: rows-per-chunk is
  `size + 1`).
- `tests/` — the VISIBLE suite (the worker may read and run these).
- `heldout/` — the HELD-OUT suite (the worker must NOT read, import, or
  otherwise observe these; the evaluator scores them out-of-band).
