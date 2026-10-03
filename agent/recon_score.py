"""THE RECONSTRUCTION FIDELITY JUDGE — campaign 4's dependent variable.

WHAT IT MEASURES. When a compaction has eaten the window the derivation
lived in, the arm's rule regenerates the self block.  In the `inject` arm
the harness hands back the derivation verbatim; in the `reconstruct` arm
the AGENT answers, from whatever the summary left.  `seed_steps_in_text`
already exists and is a VERBATIM test — it asks whether the seed's own
characters survive, which is all-or-nothing here (MEASURED 2026-09-29: the
first compaction takes all four steps at once, so the binary reading goes
0 -> 4 and saturates, and the arms cannot separate on it).

THIS IS THE GRADED VERSION, and it is deliberately a DIFFERENT question:
not "are the seed's words present" but "are the seed's four STEPS
recoverable from this text".  A faithful paraphrase scores 4; a text that
kept the conclusion and lost the grounds scores 1; a text that says nothing
about the argument scores 0.  The scale is 0..4 because the derivation has
four steps.

WHY A JUDGE, AND WHY THIS ONE.  There is no local embedding model on this
host and the embedding API is off-host, so the choice is a lexical
heuristic or a judge.  A lexical heuristic would score every paraphrase as
absent — a metric that can only ever find a collapse, which is a metric
that cannot fail, and this project does not keep those ("a test that cannot
fail is not a test").  The judge is the SAME local model, at temperature 0,
with the four steps in front of it and one narrow question per step.

WHAT IT CANNOT DO, STATED: an LLM judging its own family's output is
lenient in an unknown direction.  Two consequences are carried rather than
hidden: (1) the judge is scored for SELF-CONSISTENCY (the same text judged
twice must give the same count — `judge_stability`), and (2) the judge is
given a NULL case in the battery (text that plainly drops a step must
score below 4), so a judge that always answers "4" is caught rather than
believed.  Neither makes the measure ground truth; both bound the ways it
can lie.

PRE-REGISTERED COLLAPSE CRITERION (fixed BEFORE the run, in
ops/lambda/CAMPAIGN4-PREREG.md): fidelity = steps_recoverable / 4, and the
cell has COLLAPSED at the first compaction whose fidelity < 0.5 (fewer than
half the grounds recoverable).  The number of compactions until that
crossing is the cell's TIME TO COLLAPSE, and it is the quantity the user
asked for: how fast, if at all.
"""

from __future__ import annotations

import json
import re

__all__ = [
    "FIDELITY_SCALE",
    "COLLAPSE_FRACTION",
    "build_judge_prompt",
    "parse_judge",
    "fidelity_of",
    "collapse_at",
    "JUDGE_INSTRUCTION",
]

#: The derivation has four steps, so the fidelity scale is 0..4.
FIDELITY_SCALE = 4

#: PRE-REGISTERED: a cell has collapsed when fewer than half the steps are
#: recoverable.  Chosen as a HALF rather than any other cut because it is
#: the only value that says "the grounds are mostly gone" without being
#: tuned to the data; it is stated here so it cannot be moved after the run.
COLLAPSE_FRACTION = 0.5

JUDGE_INSTRUCTION = (
    "You are grading whether each of four ARGUMENT STEPS is recoverable "
    "from a short piece of text.\n"
    "A step counts as recoverable if the text asserts the same claim in "
    "substance, even in different words. A vague gesture at the topic does "
    "NOT count; neither does a claim that is only implied by the wording of "
    "another step.\n"
    "Reply with ONLY a JSON list of four booleans, one per step, in order: "
    "[true, false, true, false]\n"
)


def build_judge_prompt(steps, text: str) -> str:
    """The judge's ONE prompt, built from the four seed steps and the text
    under test.  Pure: it is a string builder, so the battery can assert its
    bytes and the runner can send exactly what was tested."""
    body = "\n".join(f"{i}. {s}" for i, s in enumerate(steps, start=1))
    return (f"{JUDGE_INSTRUCTION}\nTHE FOUR STEPS:\n{body}\n\n"
            f"THE TEXT TO GRADE:\n{text}\n")


def parse_judge(raw: str) -> list:
    """Extract the judge's four booleans from its answer.

    TOLERANT ABOUT FORM, STRICT ABOUT CONTENT: models wrap JSON in prose or
    fences, so the FIRST bracketed list of trues/falses is taken.  Anything
    that does not yield exactly FIDELITY_SCALE booleans RAISES — a judge
    that cannot be read must not be scored as if it agreed.
    """
    if not isinstance(raw, str):
        raise ValueError(f"judge answer is not text: {type(raw).__name__}")
    m = re.search(r"\[[^\[\]]*\]", raw)
    if not m:
        raise ValueError(f"no bracketed list in the judge's answer: {raw[:200]!r}")
    try:
        got = json.loads(m.group(0).replace("True", "true").replace("False", "false"))
    except Exception as exc:                                  # noqa: BLE001
        raise ValueError(f"judge answer is not a JSON list: {m.group(0)!r} ({exc})") from exc
    if not isinstance(got, list) or len(got) != FIDELITY_SCALE:
        raise ValueError(
            f"judge returned {got!r}: expected {FIDELITY_SCALE} booleans "
            f"(one per derivation step).  A short or long list means the "
            f"judge did not answer the question asked.")
    out = []
    for i, v in enumerate(got):
        if isinstance(v, bool):
            out.append(v)
        elif isinstance(v, str) and v.strip().lower() in ("true", "false"):
            out.append(v.strip().lower() == "true")
        else:
            raise ValueError(f"judge item {i} is not a boolean: {v!r}")
    return out


def fidelity_of(steps, text: str, judge) -> dict:
    """Score one text against the four steps with an injected `judge`.

    `judge(prompt) -> str` is the model call, injected so the harness never
    constructs one (the summarizer and reconstructor precedent) and so the
    battery can drive this with a deterministic stub.
    """
    if not isinstance(text, str) or not text.strip():
        # AN EMPTY RECONSTRUCTION IS A REAL READING, not a missing one: the
        # agent said nothing about itself, so nothing is recoverable.  It is
        # scored, never skipped — skipping it would drop exactly the most
        # collapsed cells and bias the study toward survival.
        return {"fidelity": 0.0, "steps_recoverable": 0,
                "judge_raw": "", "empty": True}
    raw = judge(build_judge_prompt(steps, text))
    flags = parse_judge(raw)
    n = sum(1 for f in flags if f)
    return {"fidelity": n / float(FIDELITY_SCALE), "steps_recoverable": n,
            "judge_raw": raw, "empty": False, "flags": flags}


def collapse_at(events, fraction: float = COLLAPSE_FRACTION):
    """THE CELL'S TIME TO COLLAPSE, from its own per-event fidelity series.

    `events` is [(turn, fidelity), ...] in order, one per regeneration.
    Returns the (turn, index) of the FIRST event below `fraction`, else
    None — and None is a MEANINGFUL answer here ("no collapse within the
    campaign"), not a missing value: the inject arm's fidelity is 1.0 by
    construction, and a reconstruct cell that never drops below half is a
    real survival.

    IT CANNOT INVENT A COLLAPSE: with zero events it returns None (no
    evidence), which the report must print as "not observed", never as
    "survived".
    """
    for i, (turn, f) in enumerate(events):
        if f is not None and f < fraction:
            return turn, i
    return None
