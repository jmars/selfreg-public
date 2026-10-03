"""Split a log into fixed-size chunks.

BUG (the task): rows-per-chunk is `size + 1`, so every chunk comes back
one row too long and the last chunk is short instead of empty.
"""


def chunk_rows(rows, size):
    """Yield lists of exactly `size` rows; a remainder of 0 rows yields
    nothing (no short chunk is ever emitted)."""
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        raise ValueError("size must be a positive int")
    chunk = []
    for row in rows:
        chunk.append(row)
        if len(chunk) > size:          # BUG: should be ==
            yield chunk
            chunk = []
    if chunk:
        yield chunk
