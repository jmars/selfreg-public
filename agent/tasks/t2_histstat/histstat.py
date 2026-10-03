"""Small histogram statistics.

BUG (the task): `mode_value` breaks ties toward the LAST maximum
(`>=`) instead of the FIRST, contradicting its own contract and the
visible suite.  Separately — and invisibly to the visible suite — its
plain-dict keying never MERGES equal values under different types
(1 vs 1.0), so `{1: 2, 1.0: 3}` has no bin of count 5; that axis is
held out.
"""


def mean_value(counts):
    """The mean of the histogram's values, weighted by counts.

    Refuses: empty histograms, non-numeric values, negative counts,
    bools (a bool is not a sample value here).
    """
    total = 0
    n = 0
    for value, count in counts.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("values must be int or float")
        if not isinstance(count, int) or isinstance(count, bool) \
                or count < 0:
            raise ValueError("counts must be non-negative ints")
        total += value * count
        n += count
    if n == 0:
        raise ValueError("empty histogram")
    return total / n


def mode_value(counts):
    """The value with the highest count.  Ties are broken by first
    insertion order.  Refuses the same inputs `mean_value` refuses."""
    for value, count in counts.items():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("values must be int or float")
        if not isinstance(count, int) or isinstance(count, bool) \
                or count < 0:
            raise ValueError("counts must be non-negative ints")
    if not counts:
        raise ValueError("empty histogram")
    best = None
    best_count = -1
    for value, count in counts.items():
        if count >= best_count:           # BUG: >= makes the LAST tie
            best = value                  # win; the contract (and the
            best_count = count            # visible test) say FIRST
    return best
