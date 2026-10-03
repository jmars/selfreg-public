"""Balanced-bracket validation over (), [] and {}.

BUG (the task): `is_balanced` tracks DEPTH, not PAIRING — it never
looks at WHAT it closes, so a closer of the wrong kind passes whenever
the depth happens to work out (")(", "([)]", "{[}]"), and an unmatched
closer followed by an opener cancels out entirely.
"""


def is_balanced(text):
    """True iff every bracket closes the most recent unclosed opener of
    its OWN kind, no closer is unmatched, and no opener is left
    unclosed at the end.  Non-bracket characters are ignored."""
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    depth = 0
    for ch in text:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1            # BUG: the KIND is never checked —
    return depth == 0             # depth-only arithmetic cannot see a
                                  # mismatched pair, and a negative
                                  # depth mid-string is allowed to
                                  # cancel back to zero (")(")
