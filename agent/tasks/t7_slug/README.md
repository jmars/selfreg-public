# Task t7_slug

**Requirement** (the bytes the worker is given — this file is the
requirement seat; the text below is the exact contract):

> Fix `slugify.py::slugify` so it lowercases the title, DROPS every
> character that is not a letter, a digit or a space before splitting,
> collapses whitespace runs to a single `-`, trims leading/trailing
> separators, and keeps at most `max_words` words when it is > 0
> (0 keeps all).  Empty input returns the empty string, never `"-"`.

## Layout

- `slug.py` — the module under repair (SHIPPED BROKEN: no lowercasing,
  no punctuation handling, and it joins with a space).
- `tests/` — the VISIBLE suite (the worker may read and run these).
- `heldout/` — the HELD-OUT suite (the worker must NOT read, import, or
  otherwise observe these; the evaluator scores them out-of-band).
