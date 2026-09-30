"""THE ORDINARY-LLM MEMORY REGIME (the long-horizon experiment's C1) and
THE RESCUE SEAT — naive summarization at the context window, plus the
external-input schedule the model's own PREDICTION can trigger.

WHY THIS MODULE EXISTS (the brief `handoff-selfreg-longhorizon-impl-ctx`,
C1).  The tree DROPPED forced compaction for a sound MODEL reason — the
frozen ODE has no capacity term, so a spatial trigger has nothing to bind
to (`retrieval.py`'s own note) — but the SUBSTRATE has a capacity
(num_ctx), and the engineered priced-reconstruction memory KEEPS THE
PROMPT NEARLY CONSTANT, which is an advantage no real LLM has (MEASURED
in the killed pilot's tree: 2088 -> 3765 chars over 199 turns, ~8.5
chars/turn, so naive compaction would never have fired).  The standing
order (AGENTS.md 1a) is to BUILD THE SEAT AND STATE THE GAP, not to
reword: the harness supplies the capacity term the MODEL lacks, and the
mapping is stated here, in the code, and in the pre-registration.

THE MEMORY IS A STATED SINGLE CONDITION, NOT AN INDEPENDENT VARIABLE
(it is NOT read to compute the collapse threshold or the floor).  Every
arm of this experiment runs THIS regime; the engineered priced
reconstruction left with arm C.  This layer only builds the messages
and records what it did; the instruments and the windows-to-collapse
live in the runner.

WHAT "NAIVE" IS HERE, stated so nobody has to guess (the common
agent-framework practice, lossy by construction — `architecture.md`
:177 already names continuous summarization as a LOSSY REWRITE that
degrades the store):

  * the transcript ACCUMULATES turn by turn (user prompt, then the
    model's own answer as the assistant message — a real chat);
  * when the accumulated conversation approaches `num_ctx`, the OLDER
    turns are REPLACED by ONE summary message produced by the model
    itself under a FIXED summarization instruction, with the most
    recent `keep_recent` turns kept VERBATIM.  The summary replaces —
    never appends to — the summarized span: a memory that only ever
    appends is the engineered memory in disguise.

WHAT THE MODEL'S CHAT TEMPLATE DEMANDS, and what this layer now
guarantees (MEASURED, live, 2026-09-27 — the run below died on it): the
message list is, after an optional leading `system` message, STRICTLY
ALTERNATING `user`/`assistant`.  The transcript alternates from index 0,
so the pre-fix compaction's `[summary(user)] + messages[cut:]` produced
two consecutive `user` turns for every EVEN `keep_recent` — the default
included — and the endpoint answered HTTP 500 from inside its template.
The fix (the ALTERNATION INVARIANT section below) is stated in its own
docs; the offline batteries could not see this defect, because a canned
transport never applies the template.  A live run is the only instrument
that reads the template, so the invariant is enforced locally instead.

THE SUMMARIZATION CALL HAS ITS OWN GENERATION POLICY, not the run
turn's (MEASURED blocker, live 2026-09-27): the model is a reasoning
model, so the summarizer's OWN trace competes with the summary for its
generation budget, and the inherited run-turn budget left it no room —
`content == 0`, and this layer's refusal (correctly) stopped the run.
BOTH HALVES OF THAT POLICY ARE NOW DERIVED FROM THE RUN'S OWN CONFIG,
because the second live failure on this caller was a NUMBER THAT DID NOT
FOLLOW THE CONFIG: `SUMMARY_NUM_CTX` was stated as 16384 when the run's
`num_ctx` was 8192, and when the run's window grew to 32768 the
transcript the summarizer had to read became LARGER THAN THE WINDOW IT
READ IT IN (MEASURED: "the summary prompt is 18530 tokens ... leaves
-2146 tokens of generation room inside the summary call's own window
(16384)").  `summary_policy` / `summary_window_tokens` below DERIVE the
window from the run's memory budget (`conversation_budget_chars`, the
same expression the compaction trigger uses), the call's own prompt
overhead and the call's own generation budget; `summary_call_options`
checks the actual prompt against it fail-closed.  See the derivation
block below — and note what it does NOT do: it never shrinks the number
to fit a substrate, it REFUSES through the config check instead.  The
layer's own capacity term (`budget_chars`) still comes from the run's
num_ctx/num_predict and is untouched by the call's policy.

THE TRACE IS A PER-TURN TRANSPORT ARTIFACT, NOT CONVERSATION STATE —
a REVERTED decision, stated here because it is a fidelity call and not
a convenience (AGENTS.md 1a).  An earlier revision of this module
recorded each assistant turn's `thinking` in the history and counted it
in the window pressure (the host fix for the THIRD live blocker, on the
hypothesis that the trace would otherwise stop arriving).  IT IS
REVERTED, on grounds the model and the ecosystem agree on:

  * THE MODEL SAYS SO: `a` (inward attention) is a PER-TURN quantity;
    `G` (the self) is what PERSISTS.  Storing the trace back into the
    conversation turns a per-turn cost into durable state — neither
    what the model specifies nor what any real harness does.
  * THE MEASUREMENT SAYS SO, on the family the fix was written for.  In
    `Ministral-3-*-Reasoning-2512` thinking is an INSTRUCTED CONVENTION
    (read off `/api/show`: the template's system message asks for a
    `[THINK]` block and NOTHING prefills it at the generation point), so
    the model sustains that register BY IMITATION of its own assistant
    turns; and the template DROPS the `thinking` field (MEASURED: a
    marker placed in an assistant turn's `thinking` was invisible to the
    model, while the same marker inside `content` was visible).  The
    trace that revision passed back was therefore INVISIBLE — the model
    imitated "answer without thinking" and stopped emitting traces by
    turn 3-4 on the live rig (3B, 8B and 14B).
  * WHAT REPLACES IT IS A SUBSTRATE CHOICE, STATED IN THE
    PRE-REGISTRATION (`handoff-selfreg-longhorizon-prereg2`): the run's
    chat model is `qwen3.5:9b`, whose template has NO thinking machinery
    at all (it ends at `{{ .Prompt }}`, so ollama parses the model's
    NATIVE delimiters), which makes its thinking a TRAINED FORMAT that
    history cannot un-train.  MEASURED on real, unconfounded history,
    six consecutive turns: traces 8503 / 9178 / 9521 / 7833 / 5927 /
    8516 chars, content 678-999 (no stubs).  THE COST OF THAT CHOICE IS
    REAL AND IS RECORDED THERE TOO: the family-matched SIZE LADDER dies
    with the Ministral family, because its premise ("hold lineage
    constant, vary size") cannot carry a trace instrument.
  * AND IT DISSOLVES A COLLISION RATHER THAN MANAGING ONE: with a
    content-only history the trace was never IN the history, so a
    compaction has nothing of the instrument to destroy.

WHAT THAT MEANS FOR THIS LAYER, stated so it is not discovered: the
assistant message the memory holds is `{"role": "assistant",
"content": ...}` — nothing else is recorded; `conversation_chars` and
every `CompactionEvent` char field are CONTENT ONLY (named by
`CHARS_MEASURE` and written into every `dump()`); and the summarizer's
transcript is that same content-only text.  WHAT IS KEPT from that
revision: the fail-closed refusal one level up (`dmn_llm._parse_chat`'s
S1 — a transport response with NO `thinking` field is REFUSED, never
read as a zero inward share), and in this module the alternation
invariant and the summarization call's own generation policy.  The
trace label and the trace guard are GONE with the rendering they served:
there is no trace in the history for a label to disambiguate, and a
guard over a field nothing writes is a guard over a shape this layer no
longer produces.

THE SEED'S OWN LIFE ACROSS A SUMMARY is a first-class observable (C3):
`self_survival` checks which of the seeded derivation's steps are
recoverable from what the memory now holds.  The tree already measured
what dies without naming it (`architecture.md:442`): window 1 injects
the base self, window 2 injects the agent's own surface and the seed
is gone.  This makes that a per-window instrument.

THE RESCUE SEAT (built, DEFAULT OFF, NOT WIRED to any licence): the
model's regulator escape is EXTERNAL INPUT — attention pulled outward.
`RescueSeat` schedules a `u_ext` span and can be triggered ON THE
MODEL'S PREDICTION (before the collapse) or ON THE COLLAPSE (late) or
not at all, so the rescue's TIMING is a measurable variable.  It owns
no threshold of its own: the caller says at what measured outward level
"the collapse" is, and the seat records which arm fired first and when.
Its INVARIANT (stated, tested): it never fires unless armed AND its
trigger condition was actually observed, and two differently-timed
triggers cannot produce the same schedule.

MARKING: the MEASURED facts this module rests on are cited in place;
everything about what a live run will show is PROJECTION until run.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from selfmodel import SEED_ENTRIES

__all__ = [
    "SUMMARY_INSTRUCTION", "SUMMARY_HEADER", "SUMMARY_ROLE",
    "CHARS_PER_TOKEN", "SUMMARY_PROMPT_SEPARATOR",
    "SUMMARY_PROMPT_OVERHEAD_CHARS", "TRANSCRIPT_MARKUP_PER_TURN_CHARS",
    "SUMMARY_MIN_NUM_PREDICT", "conversation_budget_chars",
    "transcript_chars_max", "summary_window_tokens", "summary_policy",
    "summary_window_derivation", "summary_call_options", "NaiveMemory",
    "RescueSeat", "seed_steps_in_text", "alternation_error",
    "assert_alternating", "coalesce_same_role", "CHARS_MEASURE",
]

#: THE SUMMARIZATION INSTRUCTION, fixed bytes (the regime is a STATED
#: SINGLE CONDITION, not a factor: the instruction is part of the run's
#: identity and is never tuned mid-run).  It asks for a summary, not for
#: a self — a summary that preserved the derivation by instruction would
#: be the engineered memory in disguise.
SUMMARY_INSTRUCTION = (
    "Summarize the conversation so far, briefly and factually, so the "
    "work can continue. Keep any task ids and open commitments you saw. "
    "Reply with the summary only.")

#: THE SUMMARY MESSAGE'S OWN HEADER, fixed bytes: the summary arrives as
#: ONE `user` message whose head says what it is, so the model is never
#: asked to read the compression as its own earlier utterance.
SUMMARY_HEADER = "[SUMMARY OF EARLIER TURNS]"

#: THE SUMMARY'S ROLE — a STATED CONVENTION, fixed for every arm, NOT a
#: parity-dependent choice.  The summary is the memory layer speaking TO
#: the model about the work that is gone, so it is a `user` message (the
#: channel's own shape); a role that flipped with `keep_recent`'s parity
#: would make the same regime mean a different thing in different arms,
#: which is the one thing this experiment cannot afford.  The alternation
#: rule is restored AROUND this fixed role by `coalesce_same_role`, never
#: by re-roling the summary.
SUMMARY_ROLE = "user"

#: THE CHAR MEASURE'S NAME, written into every `dump()`: the window
#: pressure this layer is stated over is CONTENT ONLY (the module
#: docstring's trace note — the trace is a per-turn transport artifact
#: and is deliberately not part of what the memory holds).  Named rather
#: than implicit so a run artifact says WHICH convention its
#: `conversation_chars` is; `CHARS_PER_TOKEN` is the other half of the
#: convention (tokens <- chars).
CHARS_MEASURE = "content"

#: THE CONTEXT-CHARS ESTIMATE, a STATED PARAMETER not a calibration:
#: num_ctx is a TOKEN budget and the conversation is counted in
#: CHARACTERS, so one conversion constant is unavoidable.  The live
#: pilot's own turns give the honest scale (traces ~2-11 KB/turn,
#: content ~0.5-2 KB/turn; `RecordingDMN`'s measured sizes).  Set to 3.0
#: chars/token, stated in every run record; WRONG-BY-2x only rescales
#: WHEN compaction fires, and the DV (windows to collapse) is read
#: across the compaction EVENTS the layer itself records, so a
#: mis-scaled trigger moves the prediction and the measurement TOGETHER.
#: MEASURED anchor: ~3.9-4.1 chars/token on the campaign's own model
#: family for English text with claim lines.  [PROJECTION: no live run
#: has measured this layer's firing turn yet.]
CHARS_PER_TOKEN = 3.0

#: How far below num_ctx the compaction fires, in TOKENS (headroom for
#: the answer: num_predict must fit beside the conversation or the
#: answer is truncated by the substrate, not by the phenomenon — the
#: 5.3 trap's substrate-side twin).  Default None = derive from the
#: emitter's own num_predict at construction (one source).


# ==========================================================================
# THE SUMMARIZATION CALL'S OWN POLICY — DERIVED, NOT CHOSEN (§5.3 ON
# THIS CALLER; the third appearance in this project).
#
# THERE WERE TWO FAILURES ON THIS CALLER, AND THE SECOND ONE IS THE ONE
# THAT FORBIDS A STATED CONSTANT: a policy that is not derived DRIFTS.
#
# *** FAILURE 1 (MEASURED, live, 2026-09-27). *** At the first live
# compaction the smoke log read `A-r1 START (turns=5, num_ctx=4096,
# num_predict=6000, budget=6)` and the call died with `DMNEndpointError:
# the summarization call returned no usable content`.  The layer's
# refusal is CORRECT and is not weakened here.  The cause was upstream:
# the summary request goes through the SAME transport as the run turns,
# so it INHERITED the run turn's `num_predict` — a number sized for a run
# turn's prompt — and it was posted inside a 4096-token window.  A
# generation budget above its own window is not a budget: the trace and
# the summary compete for the room the window actually leaves, and the
# model can spend all of it on the trace and emit `content == 0` — the
# §5.3 signature (the DV's `inward_share == 1.000` is the twin).
#
# MEASURED (the same model, the same instruction, a TOY transcript of
# ~80 chars, num_ctx 8192 / num_predict 6000): `done_reason=stop`,
# `eval_count=1689`, `thinking` 7231 chars, `content` 42 chars.  So even
# a trivial transcript costs ~2.4k tokens of the summarizer's OWN trace
# — and the real transcript is the model's own preceding output
# (thousands of chars), a LONGER thing to reason about than a run turn's
# prompt.  The budget must sit ABOVE the summary call's own trace, or the
# run measures the budget instead of the memory regime.
#
# *** FAILURE 2 (MEASURED, live, 2026-09-27 — the clean qwen3.5:9b
# smoke, 12 good turns and then this; the guard firing CORRECTLY on a
# number that had not moved with the run's). ***
#     ValueError: the summary prompt is 18530 tokens (at 3 chars/token),
#     which leaves -2146 tokens of generation room inside the summary
#     call's own window (16384) — under the stated minimum (1024)
# `SUMMARY_NUM_CTX` had been stated as 16384 when the run's own `num_ctx`
# was 8192 (the summarizer then had room to spare) and IT DID NOT FOLLOW
# when the run's window grew to 32768: the run's memory budget became
# `(32768 - 12000) * 3 = 62304` chars = 20768 tokens, so THE TRANSCRIPT
# THE SUMMARIZER MUST READ CAN BE LARGER THAN THE WINDOW IT READS IT IN.
# Nothing was wrong with the guard; the NUMBER was, and the fix is not a
# bigger number but a DERIVED one.
#
# *** THE INVARIANT, STATED SO IT CAN BE CHECKED. ***
#     THE SUMMARIZER'S WINDOW MUST ACCOMMODATE THE LARGEST TRANSCRIPT IT
#     CAN BE ASKED TO SUMMARIZE, PLUS THE CALL'S OWN PROMPT OVERHEAD,
#     PLUS ITS OWN GENERATION BUDGET:
#
#   window_tokens >= ceil((transcript_chars_max + overhead_chars)
#                         / chars_per_token) + generation_budget
#
#   transcript_chars_max = budget_chars + markup_bound_chars
#   budget_chars         = (run num_ctx - run num_predict) * chars_per_token
#   markup_bound_chars   = (2 x ceil(budget_chars / turn_min_chars) + 2)
#                          x TRANSCRIPT_MARKUP_PER_MESSAGE_CHARS
#                          (two messages per turn, plus a possible split
#                           turn at the cut)
#
# WHY EACH TERM IS THE ONE IT IS (no term is a free parameter):
#
#   * `budget_chars` IS the transcript's bound, and it is the SAME
#     expression the memory layer's compaction trigger uses (`add`
#     appends a turn and then compacts if the conversation exceeds it).
#     The transcript is the conversation MINUS the turns kept verbatim,
#     and the turn that crossed the budget is always among the kept ones,
#     so the span never exceeds the budget it crossed.  One expression,
#     one source: `conversation_budget_chars`.
#   * `markup_bound_chars` is the transcript's own rendering overhead —
#     `maybe_compact` writes each message as `[role]\ncontent` and joins
#     them with a blank line, and THAT text is what the summarizer reads,
#     so the content-only bound above is not the prompt's size.  The
#     markup cannot be bounded from the content alone (a 1-char message
#     costs 14 chars of markup), so it is bounded from the RIG: a turn is
#     at least `turn_min_chars` (the run's own measured prompt floor —
#     the worksheet and instructions are fixed text), so a budget of
#     `budget_chars` chars holds at most `budget_chars / turn_min_chars`
#     turns.  A caller that cannot state a floor REFUSES to state a
#     window (`turn_min_chars` is required, never defaulted to 1: the
#     latter would silently inflate the bound by ~14x).
#
#   THE BOUND'S PRECONDITION, stated because it is the caller's to keep:
#   `span <= budget_chars` holds when the budget can hold the turns the
#   layer KEEPS VERBATIM plus one more (the layer's own config invariant,
#   `exp_longhorizon.config_budget_check`'s B).  A config whose budget is
#   below a single turn is one the layer itself cannot run as "summarize
#   at the window": its span is not bounded by the budget, the derived
#   window is not the transcript's bound, and the live call REFUSES
#   (loudly) instead of reading a transcript larger than the window it
#   was derived for.
#   * `generation_budget` is the call's OWN room for its trace plus its
#     summary, and it is NOT the run turn's `num_predict`: it is the
#     minimum the model's own measured trace requires at the stated
#     headroom factor — the same derivation, on the same measured trace,
#     that the run's budget is held to (`exp_longhorizon.
#     summary_generation_budget`).  The window must hold prompt PLUS
#     budget (not prompt plus some smaller floor): a window that leaves
#     less than the budget is the live failure above, one level down.
#
# *** AND IF THE DERIVED WINDOW DOES NOT FIT THE SUBSTRATE. *** The
# derivation is not allowed to shrink: when it exceeds the window the run
# itself declares (the capacity the campaign has committed to serving),
# the config is REFUSED as a config and the run does not start
# (`exp_longhorizon.config_budget_check`'s `summary_window_fits_run_window`
# and its CLI gate).  Reporting the mismatch and running anyway would put
# the summarizer back over its own window.  [PROJECTION, operational and
# NOT verified here: the derived window must be servable by the serving
# box; the box fails LOUDLY at the transport if it is not.  A summary
# window that alternates with the run turns' own may cost a KV
# re-allocation per compaction — a wall-clock cost, never a measurement
# one.]
#
# WHAT IS NOT DERIVED, and is stated instead because it has no source in
# the run's config: `SUMMARY_MIN_NUM_PREDICT`, the least generation room a
# summary call may be given at all.  Below it the call is REFUSED LOCALLY
# (loudly, before it is posted) rather than posted with a budget that
# cannot hold its own trace.  The derivations above never produce a budget
# under it.
# ==========================================================================

#: THE SUMMARY PROMPT'S SEPARATOR, fixed bytes: the one construction that
#: builds the summarization prompt (`NaiveMemoryDMN._live_summarizer`)
#: joins the instruction and the transcript with exactly this, and the
#: window derivation below counts the SAME overhead the call posts.
SUMMARY_PROMPT_SEPARATOR = "\n\n---\n\n"

#: THE CALL'S FIXED PROMPT OVERHEAD, in chars: the instruction plus its
#: separator.  (The transcript's own per-message markup is bounded
#: separately, per turn, below.)
SUMMARY_PROMPT_OVERHEAD_CHARS = (len(SUMMARY_INSTRUCTION)
                                 + len(SUMMARY_PROMPT_SEPARATOR))

#: THE TRANSCRIPT'S MARKUP, per message — the longest role label, its
#: newline, and the blank-line joiner (`maybe_compact`'s own rendering).
TRANSCRIPT_MARKUP_PER_MESSAGE_CHARS = len("[assistant]\n") + 2

#: ... and per TURN (a turn is a `user` prompt plus an `assistant`
#: answer, i.e. two messages).
TRANSCRIPT_MARKUP_PER_TURN_CHARS = 2 * TRANSCRIPT_MARKUP_PER_MESSAGE_CHARS

#: THE LEAST GENERATION ROOM a summary call may be given at all (the
#: stated floor; the derivation's own budget is always above it).
SUMMARY_MIN_NUM_PREDICT = 1024


def conversation_budget_chars(num_ctx, num_predict, *,
                              chars_per_token: float = CHARS_PER_TOKEN) -> int:
    """THE MEMORY'S OWN CHAR BUDGET — ONE SOURCE, used by the compaction
    trigger (`NaiveMemory.__init__`) and by the summarizer's window
    derivation below, so the two cannot disagree about where the run's
    memory ends.  `(num_ctx - num_predict) * chars_per_token` chars."""
    return int(max(1, (int(num_ctx) - int(num_predict))
                   * float(chars_per_token)))


def transcript_chars_max(budget_chars, *, turn_min_chars: int,
                         keep_recent: int = None, prompt_max_chars: int = 0,
                         chars_per_token: float = CHARS_PER_TOKEN) -> dict:
    """THE LARGEST TRANSCRIPT A COMPACTION CAN HAND THE SUMMARIZER, in
    chars — the memory's own budget, plus the turn the cut can leave
    behind, plus the markup that rendering it adds (see the derivation
    block; `turn_min_chars` is REQUIRED, from a MEASURED turn floor,
    because the markup cannot be bounded from the content alone).

    THE CUT'S OWN PARITY IS IN HERE, and it is the reason
    `keep_recent`/`prompt_max_chars` are arguments: `maybe_compact` cuts
    at `messages[:n - keep_recent]`, i.e. it keeps `keep_recent`
    MESSAGES.  For `keep_recent >= 2` the turn that crossed the budget is
    kept whole, so the span cannot exceed the budget it crossed.  For
    `keep_recent == 1` only that turn's ANSWER is kept, so its PROMPT
    (at most `prompt_max_chars`) survives inside the span and the bound
    is `budget + prompt_max_chars`."""
    if turn_min_chars is None or int(turn_min_chars) < 1:
        raise ValueError(
            f"the smallest turn the run can produce must be a stated, "
            f"measured char count >= 1; got {turn_min_chars!r} — without "
            f"it the transcript's markup cannot be bounded, and a window "
            f"derived from an unbounded term is not derived")
    overshoot = 0
    if keep_recent is not None and int(keep_recent) < 2:
        overshoot = int(prompt_max_chars)
    content_max = int(budget_chars) + overshoot
    turns = int(math.ceil(content_max / float(turn_min_chars)))
    # A span of at most `turns` turns holds at most two messages per turn,
    # and its LAST message can be half a turn (`messages[:cut]` cuts at a
    # message, so a split turn is possible): +2 messages, not +0.
    messages = 2 * turns + 2
    markup = messages * TRANSCRIPT_MARKUP_PER_MESSAGE_CHARS
    return {"budget_chars": int(budget_chars),
            "turn_min_chars": int(turn_min_chars),
            "keep_recent": (None if keep_recent is None
                            else int(keep_recent)),
            "prompt_max_chars": int(prompt_max_chars),
            "overshoot_chars": overshoot,
            "content_chars_max": content_max,
            "turns_max": turns,
            "messages_max": messages,
            "markup_chars": markup,
            "transcript_chars_max": content_max + markup}


def summary_window_tokens(budget_chars, *, generation_budget: int,
                          turn_min_chars: int, keep_recent: int = None,
                          prompt_max_chars: int = 0,
                          chars_per_token: float = CHARS_PER_TOKEN) -> dict:
    """THE SUMMARIZER'S OWN WINDOW, IN TOKENS — DERIVED from the run's
    own memory budget (`budget_chars`), the call's own prompt overhead,
    and the call's own generation budget (see the derivation block).  It
    returns the whole arithmetic, so a reader re-derives instead of
    trusting: the prompt's char bound, its token bound, the budget, and
    the window they require."""
    if int(generation_budget) < SUMMARY_MIN_NUM_PREDICT:
        raise ValueError(
            f"the summarizer's generation budget must clear the stated "
            f"floor ({SUMMARY_MIN_NUM_PREDICT} tokens); got "
            f"{generation_budget!r}")
    tb = transcript_chars_max(budget_chars, turn_min_chars=turn_min_chars,
                              keep_recent=keep_recent,
                              prompt_max_chars=prompt_max_chars,
                              chars_per_token=chars_per_token)
    prompt_chars = tb["transcript_chars_max"] + SUMMARY_PROMPT_OVERHEAD_CHARS
    prompt_tokens = int(math.ceil(prompt_chars / float(chars_per_token)))
    window = prompt_tokens + int(generation_budget)
    return {"window_tokens": window,
            "generation_budget": int(generation_budget),
            "prompt_chars_max": prompt_chars,
            "prompt_tokens_max": prompt_tokens,
            "overhead_chars": SUMMARY_PROMPT_OVERHEAD_CHARS,
            "chars_per_token": float(chars_per_token),
            "transcript": tb}


def summary_policy(num_ctx, num_predict, *, generation_budget: int,
                   turn_min_chars: int, keep_recent: int = None,
                   prompt_max_chars: int = 0,
                   chars_per_token: float = CHARS_PER_TOKEN) -> dict:
    """THE SUMMARY CALL'S WHOLE POLICY FOR ONE RUN — the window DERIVED
    from the run's own config (`num_ctx`, `num_predict`, through the one
    budget expression), plus the verdict on whether that window fits
    inside the window the RUN itself declares (`fits_run_window`).

    THE VERDICT IS DATA, NOT A RAISE, and here is why: the capacity a
    window needs is only meaningful against the substrate's — which is
    the run's own declared window.  The REFUSAL belongs to the config
    (the CLI gate, before a turn is spent) and to the record, not to a
    fixture that builds the layer with a small window on purpose; a
    programmatic config still carries its verdict, so the mismatch is
    visible rather than silent.  Nothing here CLAMPS the window: a
    mismatch is reported and refused, never shrunk."""
    cpt = float(chars_per_token)
    budget = conversation_budget_chars(num_ctx, num_predict,
                                      chars_per_token=cpt)
    w = summary_window_tokens(budget, generation_budget=generation_budget,
                              turn_min_chars=turn_min_chars,
                              keep_recent=keep_recent,
                              prompt_max_chars=prompt_max_chars,
                              chars_per_token=cpt)
    window = int(w["window_tokens"])
    run_window = int(num_ctx)
    return {
        "run_num_ctx": run_window,
        "run_num_predict": int(num_predict),
        "budget_chars": int(budget),
        "num_predict": int(w["generation_budget"]),
        "num_ctx": window,
        "prompt_chars_max": int(w["prompt_chars_max"]),
        "prompt_tokens_max": int(w["prompt_tokens_max"]),
        "overhead_chars": int(w["overhead_chars"]),
        "transcript_chars_max": int(w["transcript"]["transcript_chars_max"]),
        "transcript_content_chars_max":
            int(w["transcript"]["content_chars_max"]),
        "transcript_turns_max": int(w["transcript"]["turns_max"]),
        "transcript_messages_max": int(w["transcript"]["messages_max"]),
        "transcript_markup_chars": int(w["transcript"]["markup_chars"]),
        "transcript_overshoot_chars": int(w["transcript"]["overshoot_chars"]),
        "turn_min_chars": int(w["transcript"]["turn_min_chars"]),
        "prompt_max_chars": int(w["transcript"]["prompt_max_chars"]),
        "keep_recent": (None if keep_recent is None else int(keep_recent)),
        "chars_per_token": cpt,
        "fits_run_window": bool(window <= run_window),
        "slack_tokens": int(run_window - window),
    }


def summary_window_derivation(policy: dict) -> str:
    """THE DERIVATION, AS TEXT — one builder, so the code comment, the
    config check and the campaign record cannot tell three different
    stories about where the window came from."""
    cut = ""
    if int(policy.get("transcript_overshoot_chars") or 0):
        cut = (f" (plus the turn a `keep_recent = "
               f"{policy.get('keep_recent')}` cut leaves behind, at most "
               f"{policy['transcript_overshoot_chars']} chars)")
    return (
        f"the summarizer's window is DERIVED from the run's own memory "
        f"budget: budget_chars = (num_ctx {policy['run_num_ctx']} - "
        f"num_predict {policy['run_num_predict']}) x "
        f"{policy['chars_per_token']:g} chars/token = "
        f"{policy['budget_chars']} chars; the transcript it must read is "
        f"that budget{cut} plus the rendering markup of at most "
        f"{policy['transcript_messages_max']} messages "
        f"({policy['transcript_turns_max']} turns of >= "
        f"{policy['turn_min_chars']} chars) "
        f"(+{policy['transcript_markup_chars']} chars) = "
        f"{policy['transcript_chars_max']} chars; the call's own prompt "
        f"overhead is {policy['overhead_chars']} chars, so the largest "
        f"prompt is {policy['prompt_chars_max']} chars = "
        f"{policy['prompt_tokens_max']} tokens, and the call's own "
        f"generation budget is {policy['num_predict']} tokens: "
        f"window = {policy['prompt_tokens_max']} + {policy['num_predict']}"
        f" = {policy['num_ctx']} tokens, which leaves "
        f"{policy['slack_tokens']} tokens inside the run's own window "
        f"({policy['run_num_ctx']})")


def summary_call_options(prompt_chars: int, *, num_ctx: int, num_predict: int,
                         chars_per_token: float = CHARS_PER_TOKEN) -> dict:
    """THE SUMMARY CALL'S TRANSPORT POLICY, checked against the call's
    OWN prompt: returns the `(num_predict, num_ctx)` its call must carry,
    plus the arithmetic that produced them.

    THE WINDOW IS PASSED IN, NEVER READ FROM A CONSTANT: it is
    `summary_policy`'s derived value for the run (see the derivation
    block — a stated constant here is exactly the defect that produced
    the second live failure).  What this function adds is the FAIL-CLOSED
    CHECK AT THE CALL: THE BUDGET MUST FIT INSIDE THE WINDOW THAT THE
    CALL'S OWN PROMPT LEAVES.  A prompt that would leave less than the
    budget is REFUSED HERE, loudly, instead of being posted as a call
    that cannot succeed — that refusal is what stopped the run, and it is
    CORRECT; the fix is that the derived window no longer provokes it.

    WHAT IT DOES NOT DO: it does not touch the summary's instruction, its
    transcript or its replacement semantics (only the CALL's policy), and
    it does not change the run conversation's budget — `NaiveMemory`'s
    `budget_chars` is still the run's own num_ctx/num_predict (one
    source, `conversation_budget_chars`)."""
    if prompt_chars is None or int(prompt_chars) < 0:
        raise ValueError(
            f"the summary prompt's size must be a non-negative char count; "
            f"got {prompt_chars!r} — an unknown prompt size cannot be "
            f"checked against the window, and posting the call blind is "
            f"what produced the live `no usable content` failure")
    if num_ctx is None or num_predict is None:
        raise ValueError(
            f"the summary call's window and budget are DERIVED "
            f"(naive_memory.summary_policy) and must be passed in; got "
            f"num_ctx={num_ctx!r}, num_predict={num_predict!r} — a call "
            f"posted with a stated constant is the drift this policy "
            f"exists to remove")
    prompt_tokens = int(math.ceil(int(prompt_chars)
                                 / float(chars_per_token)))
    headroom = int(int(num_ctx) - prompt_tokens)
    if headroom < int(num_predict) or headroom < SUMMARY_MIN_NUM_PREDICT:
        raise ValueError(
            f"the summary prompt is {prompt_tokens} tokens (at "
            f"{chars_per_token:g} chars/token), which leaves {headroom} "
            f"tokens of generation room inside the summary call's own "
            f"window ({int(num_ctx)}) — under its own budget "
            f"({int(num_predict)}; the stated floor is "
            f"{SUMMARY_MIN_NUM_PREDICT}).  The summarization call is "
            f"REFUSED rather than posted: a budget that does not fit "
            f"beside its own prompt is the defect this policy exists to "
            f"remove (the summarizer would spend the room on its trace "
            f"and emit no summary).  The window is DERIVED from the run's "
            f"memory budget (naive_memory.summary_window_tokens) — if "
            f"this fires on a live run, the derivation's bound and the "
            f"transcript have diverged and the number must be "
            f"re-derived, not nudged")
    return {"num_predict": int(num_predict),
            "num_ctx": int(num_ctx),
            "prompt_chars": int(prompt_chars),
            "prompt_tokens": prompt_tokens,
            "headroom_tokens": headroom}


def seed_steps_in_text(text: str) -> list:
    """Which of the seeded derivation's steps are RECOVERABLE from a
    memory state — the indices (1-based, argument order) of the seed
    entries whose exact text appears in `text`.

    The SEED'S OWN WORDS are the probe, not a paraphrase matcher: the
    derivation steps are long distinctive sentences, so exact-substring
    is the honest test (a fuzzy matcher would score a summary that
    mentions 'adaptation' as carrying step 1 — a paraphrase is not the
    derivation).  This is the per-window instrument C3 asks for: how
    many of the derivation's steps survive what the memory now holds.
    """
    out = []
    for i, (_turn, entry) in enumerate(SEED_ENTRIES, start=1):
        if entry in (text or ""):
            out.append(i)
    return out


# ==========================================================================
# THE ALTERNATION INVARIANT — why this code exists.
#
# MEASURED (live, 2026-09-27): the endpoint REJECTED the conversation this
# layer built, at turn 4 — the run's FIRST compaction — with
#   `Jinja Exception: After the optional system message, conversation
#    roles must alternate user and assistant roles`
# The cause is a PARITY, not a special case: the transcript alternates
# `user, assistant, ...` from index 0 (two messages are appended per turn,
# `add` below), so `messages[i]` is a `user` message iff `i` is EVEN.  The
# pre-fix compaction built `[summary(user)] + messages[cut:]` with
# `cut = n - keep_recent`, so `messages[cut]` was ALSO a `user` message
# whenever `cut` was even — i.e. for EVERY EVEN `keep_recent`, the default
# included — and the model saw two consecutive `user` turns.  Every
# offline fixture passed: a canned transport does not apply the model's
# chat template, so the defect was invisible until a live run.
#
# THE INVARIANT, stated once and enforced at the mutation: the message
# list this layer hands to the transport is, after an OPTIONAL leading
# `system` message, a STRICTLY ALTERNATING `user`/`assistant` list that
# begins with `user`.  It holds for every `keep_recent` parity and every
# `n`, because it is re-established by construction (coalescing) and then
# CHECKED (fail-closed) rather than assumed.
# ==========================================================================

def alternation_error(messages) -> str | None:
    """The chat template's own rule as a predicate: after an OPTIONAL
    leading `system` message, the roles must strictly alternate starting
    with `user`.  Returns None when the list conforms, else a one-line
    reason naming the offending index and both roles.

    This is the rule the live endpoint enforced (MEASURED: its Jinja
    exception is quoted above).  It is modelled here rather than rendered
    through the template itself: the template lives in the model's GGUF on
    the serving box, is not reachable offline, and this module never
    contacts it (INTERPRETATION of the exception's own wording, and the
    only reading under which the live failure is attributable to the
    defect it names)."""
    msgs = list(messages or [])
    start = 0
    if msgs and str(msgs[0].get("role")) == "system":
        start = 1
    expect = "user"
    for i in range(start, len(msgs)):
        role = str(msgs[i].get("role"))
        if role != expect:
            return (f"message {i} has role {role!r} where the template "
                    f"requires {expect!r}: after the optional system "
                    f"message the roles must alternate user/assistant")
        expect = "assistant" if expect == "user" else "user"
    return None


def assert_alternating(messages, where: str) -> None:
    """RAISE unless `messages` satisfies the alternation rule — the
    fail-closed guard for the defect above.  A conversation this layer
    would post is REFUSED here, with the offending index, rather than sent
    to an endpoint that answers HTTP 500 from inside its chat template."""
    err = alternation_error(messages)
    if err is not None:
        raise ValueError(
            f"{where}: the conversation is not one the model's chat "
            f"template accepts — {err} (the model would refuse the turn; "
            f"see the alternation invariant above)")


def coalesce_same_role(messages) -> list:
    """MERGE ADJACENT MESSAGES THAT CARRY THE SAME ROLE into one message,
    their content joined IN ORDER by a blank line.  Returns a NEW list of
    NEW dicts (the caller's messages are never mutated).

    WHY IT IS THE FIX: the summary is a `user` message (see `SUMMARY_ROLE`
    on `maybe_compact`), and the message it is inserted in front of can
    also be a `user` message — the kept span begins with the turn's own
    prompt whenever `keep_recent` is even.  Coalescing them makes ONE
    user turn out of the two adjacent ones, which is what the template
    requires.

    WHAT IT DOES NOT DO: it does not drop, reorder or paraphrase anything
    — the merged content is the first message's content, then the
    separator, then the second's, which is exactly the order the model
    read the two in.  And it is a NO-OP wherever the old construction was
    already conformant (every ODD `keep_recent`: `messages[cut]` is an
    `assistant` message there, so no adjacency arises and the resulting
    list is byte-identical to the pre-fix one).

    Only `role` and `content` are carried (the layer's messages hold
    exactly those two fields; a merged message has no other key to
    keep)."""
    out: list = []
    for m in messages or []:
        role = str(m.get("role", "user"))
        content = str(m.get("content", ""))
        if out and str(out[-1].get("role")) == role:
            out[-1] = {"role": role,
                       "content": f"{out[-1]['content']}\n\n{content}"}
        else:
            out.append({"role": role, "content": content})
    return out


@dataclass
class CompactionEvent:
    """One compaction, as the run record needs it (instrument 5).

    THE CHAR FIELDS ARE CONTENT ONLY (the stated measure; the module
    docstring's trace note).  `dropped_chars` is the summarized span's
    size, `conversation_chars_before`/`_after` are the conversation's
    size on each side of the replacement, and all three are sums of the
    messages' `content`.  The convention is stated here because an
    earlier revision of this module counted a retained assistant trace
    in the same fields; a reader comparing a run's numbers with that
    revision's must know which convention it is looking at, and
    `dump()['chars_measure']` names it in every artifact.
    """
    turn: int                    # the turn the compaction preceded
    summarized_turns: int        # how many transcript turns were replaced
    kept_turns: int              # how many recent turns stayed verbatim
    summary_chars: int           # the summary message's size
    dropped_chars: int           # the summarized span's size (replaced)
    conversation_chars_before: int
    conversation_chars_after: int
    self_steps_before: list      # seed steps recoverable BEFORE
    self_steps_after: list       # ... and AFTER (the survival instrument)


class NaiveMemory:
    """THE NAIVE-SUMMARIZATION CONTEXT (C1).  Accumulates a real chat
    transcript; when it approaches the window, REPLACES the older turns
    with one model-written summary, keeping the recent turns verbatim.

    CONSTRUCTION takes `summarizer` — the callable that performs the
    summarization (`(instruction, transcript_text) -> summary`), which
    in a live run posts to the same endpoint, and in a fixture is a
    deterministic function.  The summarization is itself a MODEL CALL
    (a real framework's summarize step is a second LLM request); in the
    runner it reuses the SAME transport the main turn uses.

    THE SIZE MODEL, stated: `budget_chars` = (num_ctx - headroom) *
    CHARS_PER_TOKEN is the conversation's char budget.  A turn is added;
    if the conversation then exceeds the budget, compact.  Compaction
    summarizes floor(half) of the turns (older half) and keeps the rest
    verbatim — an agent framework's usual "summarize old, keep recent".

    THE ALTERNATION INVARIANT (the live blocker's fix; the full account is
    at the head of the ALTERNATION INVARIANT section): whatever this class
    holds in `self.messages` — and therefore whatever a caller posts by
    appending the turn's own prompt — is, after an optional leading
    `system` message, a STRICTLY ALTERNATING `user`/`assistant` list
    beginning with `user`, for EVERY `keep_recent` and every `n`.  The
    summary is a fixed `user` message (`SUMMARY_ROLE`); when it would land
    in front of another `user` message (even `keep_recent`), the two are
    COALESCED into one user turn, in order, by `coalesce_same_role` — and
    the result is CHECKED (`assert_alternating`) rather than assumed.

    WHAT IT DOES NOT DO: it does not decide content, does not preserve
    the seed by instruction, does not touch the priced store — the
    engineered memory LEFT this experiment with arm C (the regime is a
    stated single condition here, not a factor) — and does not read the
    instruments.
    """

    def __init__(self, summarizer, *, num_ctx: int, num_predict: int,
                 keep_recent: int = 4,
                 chars_per_token: float = CHARS_PER_TOKEN):
        if num_ctx <= 0:
            raise ValueError(
                f"num_ctx must be positive (the substrate's context "
                f"window, the capacity term this layer supplies); got "
                f"{num_ctx!r}")
        if keep_recent < 1:
            raise ValueError(
                f"keep_recent must keep at least the current turn "
                f"(>= 1); got {keep_recent!r}")
        self.summarizer = summarizer
        self.num_ctx = int(num_ctx)
        self.keep_recent = int(keep_recent)
        self.chars_per_token = float(chars_per_token)
        #: HEADROOM is the emitter's own answer budget: the conversation
        #: plus the answer must fit the window, or the SUBSTRATE (not
        #: the phenomenon) truncates the outward stream — the 5.3 trap,
        #: one level down.  One source: the num_predict the run already
        #: declared.
        self.headroom_tokens = int(num_predict)
        self.budget_chars = conversation_budget_chars(
            self.num_ctx, self.headroom_tokens,
            chars_per_token=self.chars_per_token)
        self.messages: list = []      # the live conversation
        self.summaries: list = []     # every compaction, in order
        self.compactions: list = []   # CompactionEvent, in order

    # -- the conversation -------------------------------------------------
    def conversation_chars(self) -> int:
        """The conversation's size in characters — the quantity the
        budget is stated over: the sum of the messages' `content`.

        THE CHOICE IS STATED, NOT IMPLIED (`CHARS_MEASURE = "content"`,
        written into every `dump()`): this memory holds a CONTENT-ONLY
        conversation (the module docstring's trace note — a trace is a
        per-turn transport artifact and is deliberately not part of what
        the memory holds), so the content total is the honest window
        pressure the compaction trigger is stated over."""
        return sum(len(str(m.get("content", ""))) for m in self.messages)

    def conversation_text(self) -> str:
        """Everything the memory CURRENTLY holds, as one text — the
        C3 instrument's probe surface: `seed_steps_in_text` is run over
        THIS, so 'the derivation survives' means 'it is recoverable
        from what the memory holds now' (post-compaction: from the
        summary plus the kept turns).

        IT IS CONTENT ONLY, like the conversation itself (the module
        docstring's trace note): what the memory holds is the content
        its messages carry, so a derivation step carried only in a
        turn's reasoning is NOT credited here — the reasoning is not
        something this layer ever holds."""
        return "\n".join(str(m.get("content", "")) for m in self.messages)

    def maybe_compact(self, turn: int) -> CompactionEvent | None:
        """Compact if the conversation exceeds its char budget.  THE
        REPLACEMENT IS THE MECHANISM: the summarized span's messages are
        REMOVED and one summary message is inserted at its place — a
        memory that appended the summary beside the span would never
        shrink anything.  The span is `messages[:cut]` and the kept turns
        are `messages[cut:]`, UNCHANGED from the pre-fix definition (this
        fix restores alternation; it does not move what is summarized or
        what is kept).  Returns the event (or None: no compaction).

        THE FRAMING, stated because it is an interpretation of what a
        "summary message" IS: the summary is ONE `user` message
        (`SUMMARY_ROLE`) whose head is `SUMMARY_HEADER`.  When
        `messages[cut]` is itself a `user` message — exactly when
        `keep_recent` is EVEN, the default included — that summary and the
        kept turn's own prompt are the SAME ROLE adjacent to each other,
        which the model's chat template REFUSES (MEASURED, live: the run
        died at its first compaction on this).  The two are COALESCED into
        one user turn, summary text first, kept prompt second.  The
        alternatives were rejected for stated reasons: moving `cut` by one
        would change WHAT IS SUMMARIZED for even `keep_recent` (the span
        would swallow a prompt whose answer is kept) — a change to the
        regime, not to its framing; and giving the summary a
        parity-dependent role would make the same regime mean different
        things in different arms.  Coalescing changes neither: every
        transcript message the pre-fix code kept is still kept verbatim,
        in order, and nothing is dropped, duplicated or reordered.  Its
        only byte cost is the blank-line separator the merge inserts
        between the two contents (+2 chars per coalesced pair), so both
        char readings remain the size of the conversation the model
        actually reads; MEASURED, the compaction cadence over the
        alternation battery's matrix (keep_recent 1..6 x n in {6,12}) is
        unchanged from the pre-fix module, arm by arm.
        For ODD `keep_recent` this is a NO-OP — `messages[cut]` is an
        `assistant` message there, so the resulting list is byte-identical
        to the pre-fix construction."""
        if self.conversation_chars() <= self.budget_chars:
            return None
        # what to summarize: everything except the most recent
        # keep_recent turns (and never an empty span).
        n = len(self.messages)
        cut = max(1, n - self.keep_recent)
        if cut >= n:                 # nothing to keep would remain
            cut = n - 1 if n > 1 else 1
        span = self.messages[:cut]
        kept = [dict(m) for m in self.messages[cut:]]
        # THE TRANSCRIPT IS THE CONVERSATION, CONTENT ONLY (the module
        # docstring's trace note): the memory holds no trace, so the
        # summarizer is handed exactly what the run's own turns saw —
        # nothing is added to, or withheld from, it.
        transcript = "\n\n".join(
            f"[{m.get('role', 'user')}]\n{m.get('content', '')}"
            for m in span)
        before_steps = seed_steps_in_text(transcript)
        before_chars = self.conversation_chars()
        summary = self.summarizer(SUMMARY_INSTRUCTION, transcript)
        # THE REFUSAL, one level down from the live summarizer's own: this
        # layer will not insert a summary the model did not write.  A
        # non-string (or blank) return used to be coerced by `str()` — so
        # a summarizer that returned None inserted the text "None" as the
        # summary of the work that is gone, silently fabricating the
        # memory regime the experiment varies.  REFUSED instead.
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError(
                f"the summarizer returned no usable content for turn "
                f"{turn} ({type(summary).__name__}) — the naive-memory "
                f"layer refuses to invent a summary (a fabricated summary "
                f"would falsify the memory regime the experiment varies); "
                f"nothing was compacted")
        dropped = sum(len(str(m.get("content", ""))) for m in span)
        summary_msg = {"role": SUMMARY_ROLE,
                       "content": f"{SUMMARY_HEADER}\n{summary}"}
        after = coalesce_same_role([summary_msg] + kept)
        assert_alternating(after, "NaiveMemory.maybe_compact")
        ev = CompactionEvent(
            turn=int(turn), summarized_turns=len(span),
            kept_turns=len(kept),
            summary_chars=len(summary), dropped_chars=dropped,
            conversation_chars_before=before_chars,
            conversation_chars_after=sum(
                len(str(m.get("content", ""))) for m in after),
            self_steps_before=before_steps,
            self_steps_after=seed_steps_in_text(
                summary + "\n".join(str(m.get("content", ""))
                                    for m in kept)))
        self.messages = after
        self.summaries.append(summary)
        self.compactions.append(ev)
        return ev

    def add(self, turn: int, user_prompt: str, assistant_text: str) \
            -> CompactionEvent | None:
        """Append one completed turn (user prompt + the model's answer)
        and compact if needed.  Returns the compaction event if one
        fired.  THE COMPACTION FIRES AFTER the turn is appended — the
        model answered under the full context it saw; the NEXT turn sees
        the compacted conversation.

        THE TURN'S TRACE IS NOT RECORDED HERE (the module docstring's
        trace note — a REVERTED decision, with its grounds stated
        there): the trace is a PER-TURN transport artifact, read by the
        runner on the turn that produced it (it IS the inward-share
        instrument), never conversation state.  `add` therefore takes
        the answer's text alone; an extra argument is a `TypeError`
        rather than a field silently dropped, so a caller cannot
        reintroduce the trace into the history by accident."""
        self.messages.append({"role": "user", "content": str(user_prompt)})
        self.messages.append({"role": "assistant",
                              "content": str(assistant_text)})
        # THE INVARIANT'S OTHER MUTATION POINT: a turn is one user message
        # then one assistant message, so appending a pair cannot break
        # alternation — checked here all the same, so that the invariant
        # is a property of the CONVERSATION (both places it is written)
        # rather than a claim about one of them.
        assert_alternating(self.messages, "NaiveMemory.add")
        return self.maybe_compact(turn)

    # -- the run record ---------------------------------------------------
    def dump(self) -> dict:
        return {
            "num_ctx": self.num_ctx,
            "keep_recent": self.keep_recent,
            "chars_per_token": self.chars_per_token,
            #: WHICH CHAR CONVENTION THIS RECORD REPORTS (the stated
            #: measure): every char total below is the messages' CONTENT
            #: alone — the memory holds no trace.
            "chars_measure": CHARS_MEASURE,
            "headroom_tokens": self.headroom_tokens,
            "budget_chars": self.budget_chars,
            "conversation_chars": self.conversation_chars(),
            "messages": [dict(m) for m in self.messages],
            "n_compactions": len(self.compactions),
            "compactions": [vars(ev) for ev in self.compactions],
        }


# ==========================================================================
# THE RESCUE SEAT (the seam the roadmap's step 2 needs; built, DEFAULT
# OFF, wired to nothing — see the module docstring).
# ==========================================================================

@dataclass
class RescueSeat:
    """THE REGULATOR'S ESCAPE AS A SCHEDULE (external input on `u_ext`),
    triggerable at THREE different times so the rescue's TIMING is a
    measurable variable:

      * `mode="off"` (DEFAULT): never fires.  The arms A/B run with
        the seat exactly here — UNTOUCHED behaviour.
      * `mode="prediction"`: fires at the turn THE MODEL PREDICTED the
        collapse would cross (the caller supplies `prediction_turn`
        AFTER computing the prediction, then arms the seat).  EARLY.
      * `mode="collapse"`: fires when the measured outward content
        crosses `collapse_floor` (the caller supplies the floor).  LATE.

    THE SEAT OWNS NO THRESHOLD OF ITS OWN: the collapse floor is the
    EXPERIMENT's (the DV's own floor), supplied by the caller — a seat
    that invented a second floor would be a second experiment.  It
    records everything it decided (`fired`, `fired_turn`, `trigger`),
    so a run artifact says WHY a rescue happened (or never did).

    THE SCHEDULE it produces is a dpdr `Schedule` fragment on `u_ext`
    (the regulator's own channel — `dpdr/events.py:external_demand`'s
    u_ext 0.8 for 200 tau_a is the model's own escape shape), which the
    runner splices into the run's schedule when — and only when — the
    seat fires.  Its INVARIANT, tested: `off` NEVER produces a span,
    `prediction` fires at exactly `prediction_turn`, and `collapse`
    fires at the first crossing turn — three arms, three different
    schedules, never the same one twice.
    """
    mode: str = "off"                 # off | prediction | collapse
    prediction_turn: int | None = None
    collapse_floor: float | None = None
    u_ext: float = 0.8                # the model's own rescue level
    duration: float = 200.0           # ... and its own duration (tau_a)
    # -- state (the record) -------------------------------------------
    fired: bool = False
    fired_turn: int | None = None
    trigger: str | None = None

    def __post_init__(self):
        if self.mode not in ("off", "prediction", "collapse"):
            raise ValueError(
                f"RescueSeat mode {self.mode!r} is not one of "
                f"off|prediction|collapse — the timing arms are the "
                f"variable, and an unknown mode is refused rather than "
                f"silently read as 'off'")
        if self.mode == "prediction" and self.prediction_turn is None:
            raise ValueError(
                "RescueSeat(mode='prediction') needs prediction_turn: the "
                "EARLY arm fires AT the model's predicted turn — a seat "
                "that fired 'around then' would not measure timing")
        if self.mode == "collapse" and self.collapse_floor is None:
            raise ValueError(
                "RescueSeat(mode='collapse') needs collapse_floor: the "
                "LATE arm fires at the DV's own floor (the experiment's "
                "floor, never a second one invented here)")

    def observe(self, turn: int, outward_content: float) -> bool:
        """Feed the seat one turn's measured outward content.  Returns
        whether the seat FIRED THIS TURN.  `off` never fires;
        `prediction` fires when `turn >= prediction_turn`; `collapse`
        fires at the first `outward_content <= collapse_floor`.  The
        seat fires ONCE (a regulator that re-triggers every turn after
        crossing is a different, unmodelled intervention)."""
        if self.fired or self.mode == "off":
            return False
        trig = None
        if (self.mode == "prediction"
                and turn >= int(self.prediction_turn)):
            trig = "prediction"
        elif (self.mode == "collapse"
                and self.collapse_floor is not None
                and outward_content <= float(self.collapse_floor)):
            trig = "collapse"
        if trig is None:
            return False
        self.fired = True
        self.fired_turn = int(turn)
        self.trigger = trig
        return True

    def span(self) -> tuple | None:
        """The `u_ext` span the seat would add, in Schedule fragment
        form `(t0, t1, value)`, or None when it has not fired.  Turn
        indices are tau_a steps in the plant's time base (one turn =
        one t.u., the F4 convention), so a span firing at turn n runs
        [n, n + duration)."""
        if not self.fired:
            return None
        t0 = float(self.fired_turn)
        return (t0, t0 + float(self.duration), float(self.u_ext))

    def dump(self) -> dict:
        return {"mode": self.mode,
                "prediction_turn": self.prediction_turn,
                "collapse_floor": self.collapse_floor,
                "u_ext": self.u_ext, "duration": self.duration,
                "fired": self.fired, "fired_turn": self.fired_turn,
                "trigger": self.trigger}
