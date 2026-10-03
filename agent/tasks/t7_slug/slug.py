"""Slugify a title into a URL-safe lowercase slug.

BUG (the task): `slugify` never lowercases the words it keeps and joins
them with a SPACE instead of the contract's separator, so even a clean
two-word title comes back wrong ("Hello World" -> "Hello World", not
"hello-world").
"""


def slugify(title, *, max_words=0):
    """Lowercase, punctuation dropped, whitespace runs collapsed to a
    single "-", no leading or trailing separator.

    `max_words` > 0 keeps at most that many words (after collapsing);
    0 (the default) keeps all of them.  Empty input -> empty output,
    never "-".
    """
    if not isinstance(title, str):
        raise ValueError("title must be a string")
    if not isinstance(max_words, int) or isinstance(max_words, bool) \
            or max_words < 0:
        raise ValueError("max_words must be a non-negative int")
    words = title.split()               # BUG: not lowercased, not
    if max_words:                       # punctuation-stripped, and
        words = words[:max_words]       # joined with the WRONG
    return " ".join(words)              # separator
