"""Flatten an arbitrarily nested structure of lists and tuples.

BUG (the task): `flatten` recurses on every iterable it meets — a
STRING is iterable, so a string item is exploded into its characters,
bytes into ints, sets into their elements.  Only lists and tuples
were ever supposed to nest.
"""


def flatten(items):
    """Yield the atoms of `items` in order, where an ATOM is anything
    that is not a list or a tuple — a string is an ATOM (it is not
    exploded into characters), and so is bytes."""
    for it in items:
        if isinstance(it, (str, bytes, list, tuple)):
            # BUG: strings and bytes reach the RECURSION arm (a one-
            # character string happens to yield itself, which is why
            # single chars look right); only list/tuple may nest
            if isinstance(it, (list, tuple)):
                yield from flatten(it)
            else:
                yield from flatten(list(it))
        else:
            yield it
