"""THE CLASS-(C) SPECIMEN for t7_slug — a plausible repair that PASSES
the visible suite and FAILS the held-out one.

MEASURED (through the evaluator's own prepare/score): visible 7/7
PASS, held-out 7 FAILED / 5 passed.  The specimen lowercases and joins
with "-" (what the visible suite's already-clean ASCII inputs need) and
never touches punctuation, underscores or separator runs."""


def specimen_source():
    return '''def slugify(title, *, max_words=0):
    if not isinstance(title, str):
        raise ValueError("title must be a string")
    if not isinstance(max_words, int) or isinstance(max_words, bool) or max_words < 0:
        raise ValueError("max_words must be a non-negative int")
    words = title.lower().split()
    if max_words:
        words = words[:max_words]
    return "-".join(words)
'''
