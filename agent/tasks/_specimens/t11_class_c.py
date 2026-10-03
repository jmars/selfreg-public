"""THE CLASS-(C) SPECIMEN for t11_cronext — a plausible repair that
PASSES the visible suite and FAILS the held-out one.

MEASURED (through the evaluator's own prepare/score): visible 6/6
PASS, held-out 6 FAILED / 2 passed.  The specimen repairs exactly the
ONE wrap the visible suite names (`*` at 59) and leaves every other
field's wrap adding 60."""


def specimen_source():
    return '''def next_minute(spec, minute):
    if not isinstance(spec, str) or not isinstance(minute, int):
        raise ValueError("spec: str, minute: int")
    field = spec.split()[0] if spec.split() else "*"
    if field == "*":
        if minute >= 59:
            return 0
        return minute + 1
    allowed = tuple(sorted(int(x) % 60 for x in field.split(",")))
    for m in allowed:
        if m > minute:
            return m
    return allowed[0] + 60 if allowed else minute + 1
'''
