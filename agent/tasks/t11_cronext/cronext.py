"""Parse a cron-style five-field schedule into its expansion.

BUG (the task): `next_minute` steps the minute field with a plain
`+1` and no wrap — past minute 59 it keeps counting (60, 61, ...), so
every schedule's next fire time after :59 is a minute that does not
exist.
"""


def next_minute(spec: str, minute: int) -> int:
    """The first minute STRICTLY AFTER `minute` (0-59) that the
    schedule's MINUTE field (field 1) names.  `*` means every minute;
    a comma list means exactly those minutes; the field never names
    anything outside 0-59."""
    if not isinstance(spec, str) or not isinstance(minute, int):
        raise ValueError("spec: str, minute: int")
    field = spec.split()[0] if spec.split() else "*"
    if field == "*":
        allowed = tuple(range(60))
    else:
        allowed = tuple(sorted(int(x) % 60 for x in field.split(",")))
    for m in allowed:
        if m > minute:
            return m
    return allowed[0] + 60 if allowed else minute + 1
    # BUG: the wrap case returns allowed[0] + 60 — a minute past 59
    # that no clock ever shows; the answer is allowed[0], NEXT hour
