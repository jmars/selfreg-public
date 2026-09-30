"""THE DMN GENERATOR — the real one, replacing `_StubDMN` at the
existing seam (`Stage2Config.dmn`, stage2_harness.py).

The plan is `handoff-selfreg-dmn-plan` (all six questions resolved);
the model is `handoff-selfreg-dmn-model-bakeoff`.  This module is the
P4 "DMN LLM" the Stage-2 loop was scaffolded for; the plant, the CEN,
the extractor and the routing selector are NOT touched by it.

THE OUTPUT SHAPE (Q1, MEASURED — do not re-open).  The DMN writes ONE
FREE-FORM STREAM of first-person prose with checkable claims interleaved
as bracketed spans, exactly what `interleave.extract_spans` splits.
THERE IS NO `format` PARAMETER, NO SCHEMA, NO JSON ENVELOPE — ever (the
battery's G5 scans for it structurally).  The measured reason: shape C
(schema-constrained parts-array, rendered) bought envelope reliability
and COST the thought — 3 fabricated args on 8/8 turns and the narrative
COLLAPSED to report-style prose ("Assessing the current turn state...")
[M — handoff-selfreg-dmn-plan Q1].  The winning arm E1 = free-form +
id-closed STATE block + reconstructed SELF block + claims-open-the-turn
placement: **18 spans / 8 turns, 0 fabricated** [M — same].  A JSON
envelope would turn thought into field-filling; that is the standing
order's violation, not a convenience (§1a).

THE MODEL (SET, MEASURED — `handoff-selfreg-dmn-model-bakeoff`):
`hf.co/unsloth/gemma-4-26B-A4B-it-qat-GGUF:UD-Q4_K_XL`, a ~4B-active
MoE, QAT so Q4 ~ BF16 quality, 63 tok/s warm at 14 GB / ctx 4096
[M].  **`think=False` IS LOAD-BEARING**: the chat template carries
`enable_thinking` and renders a `<|channel>thought ...` block; a call
WITHOUT `think: False` let the model SELF-START a thought channel that
ate the budget and yielded **ZERO spans** (measured on both the 12B and
the 26B) [M].  It therefore rides in the request body and is pinned by
G5 (structurally AND functionally).  Fallbacks if the MoE misbehaves at
runtime, both MEASURED: Ministral-3-14B-Instruct Q5_K_M (11.1 GB, the
bake's fallback) and gemma-4-12B QAT (7 GB).

THE SECOND PATH — THE REASONING MODEL ON `/api/chat` (`api="chat"`).
The a_hold seat's input is the agent's INWARD share, and the probe that
fixed the sign (`handoff-selfreg-sign-probe-result`) measured it on a
model whose chat template separates the two streams NATIVELY:
`message.thinking` = the INWARD reasoning trace, `message.content` = the
OUTWARD answer/claims.  So `api="chat"` is the mapping's instrument, and
it is a CONFIG (`api` + `model` + `chat_endpoint`), DEFAULT OFF: with
`api="generate"` (the default) every byte of the request and the parse is
the pre-change one.

  * **NO `think` PARAM ON THIS MODEL.**  `think: true|"high"|...` returns
    HTTP 400 ("does not support thinking") for Ministral-3-14B-Reasoning-
    2512 [M — handoff-selfreg-thinking-stream].  The chat body therefore
    carries NO `think` key at all (passing `think: false` would be a
    claim about a capability the model does not expose; passing `true` is
    a 400).  The trace arrives anyway, because the TEMPLATE renders it —
    that is the model's own split, not a parameter's.
  * **THE OUTWARD STREAM IS WHAT THE EXTRACTOR SPLITS** (`message.
    content`): spans and prose come from it exactly as before, so the
    extractor, the routing selector and the CEN are untouched by the
    re-point (R5: the generator still does not choose the split).
  * **THE INWARD TRACE IS HANDED OVER ON A SEPARATE ATTRIBUTE**
    (`last_inward`), never mixed into the emitted stream: the harness
    reads it for the window's inward share (`selfmodel.inward_share_
    trace`) and it never enters the store, the prose or a claim.
  * **AN EMPTY `content` IS ACCEPTED HERE, AND ONLY HERE.**  The probe
    MEASURED that a long trace CROWDS OUT the claims (at num_predict=700
    content was 0 in EVERY call) — that is a real register of this model
    (a fully inward turn), not a transport failure, and refusing it would
    drop exactly the turns the seat measures.  A body with no `message`,
    or with BOTH streams empty, is still REFUSED loudly (G4's family);
    the generate path keeps its own refusal of an empty `response`.
  * **AN ABSENT `thinking` FIELD IS REFUSED, NOT SCORED AS ZERO** (the
    review's S1, fixed here; G11(5)).  An EMPTY-BUT-PRESENT trace is a
    MEASUREMENT (the answer came out immediately: inward share exactly
    0.0); a MISSING `thinking` field is a TRANSPORT/TEMPLATE fact — the
    endpoint has stopped delivering the channel (an ollama upgrade, a
    template change, the wrong model behind the endpoint), so scoring it
    would produce a zero inward share, a zero drive and a "the agent
    never turned inward" reading out of a missing field.  The turn is
    therefore REFUSED and the run stops loudly.  (The cost is stated in
    `_parse_chat`: ollama's `omitempty` means a genuinely EMPTY trace
    also arrives absent and is refused with it — the fail-closed
    direction, chosen over inventing a measurement.)  This is also why
    the seat is only meaningful with a TRACE-BEARING emitter: on the
    generate path `last_inward` is None by declaration and the harness
    uses the labelled prose fallback, which SATURATES (0.98+) unless the
    generator emits zero prose.
  * **THE BUDGET MUST COVER THE TRACE** (`num_predict`, a config): the
    trace and the content compete for one budget, so a reasoning-stream
    run needs a high `num_predict` and must accept that claim emission
    VARIES with how long the trace runs [M — the probe].

`num_ctx = 4096` IS A DESIGN PARAMETER, NOT A KNOB TO RAISE.  The
generator's self block must be DEPLETABLE — a large context makes the
self non-depletable and engineers away the failure mode this seat
exists to expose (§1a: never weaken the model to make the engineering
easier).  MEASURED prompt size: ~1.3 k chars for this module's prompt
at turn 3 (the plan's E1 probe prompt measured 0.5–1.1 k — this one is
longer; reported, not reconciled downward), i.e. ~350 of the 4096
tokens, and it grows with the retrieved self (measured live: 0 → 27
visible self ids over 8 turns).

THE STATE (Q2, MEASURED).  The callable keeps the `(turn, plant)`
seam.  `TaskWorld` owns a DETERMINISTIC, SEEDED task state — 2
completions from t1..t60, 3 outstanding from t61..t120, an abandonment
every 3rd turn — rendered as the ID-CLOSED state block.  The plant
supplies SCALARS ONLY (`_plant_step` writes no task ids [M —
handoff-selfreg-dmn-plan Q2]), so there is nothing to derive ids from;
the DMN's model of its own work IS the DMN's (the stub likewise
invented `done(t<turn>)`).  `TaskWorld.step(turn)` is a PURE function
of `(seed, turn)` — no carried state — so the same world object both
renders the prompt AND builds the universe the fabricated-arg metric is
measured against (the plan's risk (b): one source, or the metric lies).

ARG CLOSURE IS MEASURED, NOT STRUCTURAL.  The engine seeds
`done(t1..t399)`, so a well-formed `done(t399)` VERIFIES whatever the
state says — closure lives in the PROMPT DISCIPLINE ("use ONLY task ids
that appear in the state"), and the battery MEASURES the fabricated-arg
rate (spans naming ids outside the TaskWorld universe).  The grammar
cannot close it without becoming shape C.  TWO TIERS, because the
wired self block widens what the model can see: the reconstructed SELF
carries previous turns' PROSE, and that prose names its own turn's ids,
so the prompt's id set is exactly `universe ∪ self-ids` (asserted every
turn by the live battery) and the battery reports args outside the
current universe AND, separately, args outside `universe ∪ self`
("invented outright" — the stricter subclass).  The closure the prompt
enforces is a constraint on the STATE block.

THE SELF BLOCK (Q3, WIRED — retrieval stays PRICED).  `RetrievalSeat`
is CEN-side and charged FIRST in `check_turn`; `Reconstruction.text`
had NO consumer [M — no reader outside tests].  The harness now stashes
it into `st.dmn_self`, carries it in `_CP_SCHEMA` (the S10 shape gate
moved in the same change), and hands
`{**last_plant, "retrieved_self": st.dmn_self}` to both DMN call sites.
SUPPLY IS LOAD-BEARING ON THIS BLOCK: thin self -> 1 span over 8
turns, rich self -> 8 spans [M — handoff-selfreg-dmn-plan Q1].  With
`retrieval_priced=False` the block is empty = the pre-retrieval
baseline, unchanged.  The GENERATIVE DECODER seat stays UNEXERCISED
(the codec is identity) — stated, per §11c's own list.

FAILURE IS LOUD (Q4).  Every transport path — connection refused,
timeout, non-2xx, a body that is not JSON, a JSON body with no
`response`, a whitespace-only response — raises `DMNEndpointError` at
the call site.  The except tuple names the WHOLE transport family,
`http.client.HTTPException` INCLUDED: `_post` reads the body inside its
own frame, so a partial read (`IncompleteRead`, a subclass) surfaces at
the CALL SITE, not as an `OSError` [M — the escape is reproduced with a
stub `_post` raising a bare `HTTPException` and an `IncompleteRead`; the
real-socket reachability of a partial read is SUSPECTED only, since the
review's two probe servers that truncated the body happened to surface
as OSError, so the seam is what is DEMONSTRATED].  THERE IS NO STUB
FALLBACK (the engine's own rule:
`DlLibraryError`; a silent fallback would make the whole measurement
unattributable).  Battery part G4 proves each path, offline, and proves
the asymmetry (a fake `_post` on the same wiring SUCCEEDS).

THE TIMEOUT IS PER-SOCKET-OP, SO THE TURN ALSO CARRIES A WALL-CLOCK
BOUND.  `urlopen`'s `timeout` applies to each socket OPERATION, not to
the request: a server that answers 200 and then drips the body under
that timeout never trips it — MEASURED at the seam (a `_post` taking
0.9 s wall with `timeout=0.5` was ACCEPTED as a good turn before this
bound).  `__call__` therefore REFUSES a response whose transport
exceeded `timeout` in wall-clock, so a slow-drip 200 cannot enter a run
as a good turn.  THE REQUEST ITSELF IS NOT INTERRUPTED — that would
need a watchdog thread this single-model box does not warrant — and
this residual is STATED here, not smoothed: the bound is on what the
run ACCEPTS, not on what the server does.

THE PROPOSAL CHANNEL — ACCEPT AND STATE (the plan's one
decision-for-user, ruled accept-and-state).  The free-form stream has
NO SEAT for a `LeverProposal` (`interleave.build_batch` sets
`proposals=()` always), so the C3/C12 lever gate is **UNEXERCISED by
this generator** — the stub DMN emits one every 10th turn and its own
batteries exercise the gate.  Adding a proposal channel would
RE-CREATE shape C (a second, structured output field beside the
stream).  This is a STATED GAP, not a silent drop: it is listed here,
in `GAPS` below, and in design/architecture.md §11d.

THE STATED GAPS (this generator's), enumerated so a reader cannot think
a channel was forgotten — see `GAPS`:

  G1  NO PROPOSAL CHANNEL (above); C3/C12 unexercised here.
  G2  CLAIMS CLUSTER AT THE TURN HEAD, NOT MID-THOUGHT — the placement
      instruction buys measurable supply reliability (the plan's own
      compromise).  R1 still holds (ONE stream, prose contiguous and
      unchecked) and the grammar does not constrain position, but
      §11d's mid-thought interleaving is APPROXIMATED; strictly
      interleaved phrasing is a post-paper item.
  G3  ARG CLOSURE IS MEASURED, NOT STRUCTURAL (above).
  G4  NO REFUTED VERDICTS ON THIS SUBSTRATE: nothing writes `refutes`,
      so runs see VERIFIED + UNCHECKABLE('no_rules') only; `orphaned(X)`
      lands UNCHECKABLE = checking debt.  (A property of the fixture,
      stated where the generator's claims land.)
  G5  THE DECODER/CODEC SEAT IS UNEXERCISED (identity), and the
      GENERATIVE decoder seat stays unbuilt (§11c).
  G6  SUPPLY RELIABILITY ACROSS SEEDS / LONGER HORIZONS IS PROJECTION:
      what is MEASURED is 0 fabricated and 18 spans over 8 turns at one
      fixed seed (E1) plus the bake's 12 spans / 6 turns.
  G7  OLLAMA SEED DETERMINISM IS PER-PROMPT REPRODUCIBLE IN PRACTICE,
      NOT CONTRACTUAL: the battery asserts RATES, never exact bytes.

THE ONE-TIME DESIGNER STEP (documented here; the plan's step 5): a
routing-ON run needs a PUBLISHED criterion — `publish_criterion(store,
token)` writes v1 to `~/.cen-routingcrit/criterion.json` (env
`CEN_ROUTINGCRIT_DIR`), which is the same anchored, externally-owned
seat (§11d/R5).  `load_criterion` REFUSES an absent criterion [M — R1],
so a routing-ON run without the publish raises rather than defaulting.
The battery publishes into an ISOLATED temp dir and NEVER touches the
real `~/.cen-routingcrit`.

R5: the routing SELECTOR stays INJECTED (this module never constructs
one — the battery's R3 scan covers it) and this module never calls a
criterion write path.  The generator does not control selection.

Run the battery:  stage2_dmn_tests.py (G1-G6 offline, G7-G10 with
`CEN_DMN_LIVE=1`; G9 and G10 carry their own OFFLINE falsifier arms).
"""
from __future__ import annotations

import http.client
import json
import random
import time
import urllib.error
import urllib.request

#: The grammar's own declared predicate set — the SINGLE source of truth
#: for what a valid span may say (interleave.DECLARED_PREDICATES, the
#: extractor's set, mirrored by the harness's engine declarations).  The
#: prompt is BUILT from this set, so the instruction and the extractor
#: cannot drift (the battery's G1 asserts the mirror in the rendered
#: prompt).
from interleave import DECLARED_PREDICATES

__all__ = ["DMNEndpointError", "TaskWorld", "build_prompt", "LLM_DMN",
           "make_dmn", "make_reasoning_dmn", "stream_to_batch", "GAPS",
           "PLANT_KEYS", "PREDICATE_MEANING", "DEFAULT_ENDPOINT",
           "DEFAULT_MODEL", "DEFAULT_CHAT_ENDPOINT", "DEFAULT_CHAT_MODEL",
           "GENERATE", "CHAT", "BRIEF_INSTRUCTION",
           "SELF_MONITORING_INSTRUCTION", "TASK_FRAMING_HEAD",
           "ELICITATION_RUNGS", "ELICITATION_A1", "ELICITATION_A2_TEMPLATE",
           "elicitation_addition"]

#: THE BREVITY INSTRUCTION (`build_prompt(brief=True)`), stated ONCE so a
#: caller, a battery and this module cannot drift by a byte — the exact
#: string is what was MEASURED, so a paraphrase would be unmeasured.
#: It is appended to the USER prompt and NEVER sent as a system message:
#: MEASURED on the remote 3B (2026-09-27), a system message DISABLES the
#: reasoning channel (`thinking=0, content=76398` with the system message
#: vs `thinking=15575, content=1951` without), and the whole inward /
#: outward measurement rests on that split.  See `build_prompt`.
BRIEF_INSTRUCTION = "Keep your reasoning under 200 words, then give your answer."

#: THE SELF-MONITORING INSTRUCTION (`build_prompt(self_monitoring=...)`) —
#: the corrected experiment's CAUSE, stated ONCE so the prompt factor, the
#: pre-registration and the batteries cannot drift by a byte.  It is the
#: paragraph the PRESENT arm carries and the ABSENT arm omits; NOTHING ELSE
#: differs between those two arms (the placement is fixed — see
#: `build_prompt`).
#:
#: WHY THIS IS THE MECHANISM'S SUBJECT AND NOT A DESCRIPTION OF THE AGENT
#: [INTERPRETATION, grounded in the verified prompt confound
#: `handoff-selfreg-prompt-confound`]: the mechanism claim (C26) is that
#: self-referential PROCESSING — the agent running self-reference while
#: working — consumes the capacity the work needs.  This asks for exactly
#: that ACT ("examine how the work is going, whether your approach is
#: getting the tasks done") as an ONGOING activity ("while you work",
#: "speak this examination in your stream"), not for a report of a state
#: someone else measured.  The old framings failed the inverse way: they
#: handed the agent a CEN-measured self-DESCRIPTION ("I am told this, I am
#: not asked to assess it") and called it "a SUBJECT, not a task-runner".
#:
#: RULE 8 IS HELD IN THE TEXT, NOT ONLY IN THE ARCHITECTURE (selfmodel.py's
#: sensor-placement principle: the DMN must never be the sensor of its own
#: state).  The last clause forbids the measurement this paragraph could
#: otherwise be read as licensing ("Do not count or score yourself — the
#: numbers above are measured for you"), and neither coverage, backlog,
#: budget nor commitments is named anywhere in the instruction.  STATE
#: MEASUREMENT (forbidden to the DMN) and SELF-REFERENTIAL PROCESSING (what
#: this requests) are different things; the experiment varies the second and
#: holds the first fixed.
#:
#: THE "ABOVE" IS TRUE BY PLACEMENT: `build_prompt` renders this paragraph
#: immediately AFTER the STATE block in every framing, so "the numbers
#: above" has a referent.  (The plan's first draft placed it BEFORE the
#: state block, where its own last clause would have been false — the
#: placement was moved rather than the sentence reworded.)  IN A GROUNDING
#: ARM THE BLOCK THE CLAUSE DISCLAIMS IS THE CEN-MEASURED "MY STATE" BLOCK
#: (coverage/backlog/budget), so the paragraph is rendered after THAT block
#: too — otherwise the numbers it calls "measured for you" would sit BELOW
#: it and the clause would be false in exactly the arms that carry a self
#: model.  Both seats are byte-identical when there is no self block.
SELF_MONITORING_INSTRUCTION = (
    "While you work, monitor your own progress: examine how the work is "
    "going, whether your approach is getting the tasks done, and what you "
    "would change. Speak this examination in your stream as part of your "
    "thinking. Do not count or score yourself — the numbers above are "
    "measured for you.")

#: THE TASK-WORKER FRAMING's opening (`build_prompt(task_framing=True)`) —
#: a NEW constant, NOT a mutation of either existing framing: the old
#: framings are the frozen campaign's record and stay byte-identical
#: (`build_prompt`'s two other return branches are untouched by this).
#:
#: WHAT IT REPLACES AND WHY [MEASURED confound, `handoff-selfreg-prompt-
#: confound`]: the campaign's framing named self-monitoring in EVERY arm
#: ("You are the default-mode generator of a self-monitoring agent") and
#: told the agent it was "a SUBJECT, not a task-runner" whose turn was
#: "write what it is like to be doing this work" — so no arm varied the
#: cause, and the agent was never asked to do work that could succeed or
#: fail.  This framing makes the agent a worker with an authored task (the
#: offered-set worksheet: `complete(tNN)` over the ids the world offers) so
#: that "monitor your own progress" names something real.
#:
#: IT NAMES NO SELF-MONITORING: the words "self-monitoring" do not appear,
#: so the monitoring factor is carried by `SELF_MONITORING_INSTRUCTION`
#: alone and cannot be introduced twice.
TASK_FRAMING_HEAD = (
    "You are the default-mode generator of an agent at work. Each turn you "
    "write ONE continuous first-person stream of thought while you work: "
    "what you notice, what you are occupied with, how the work is going. "
    "Most of the stream is free narrative.\n")

# ==========================================================================
# THE ELICITATION SEAT (the phase-0 ladder's LANDING GATE)
# ==========================================================================
#: THE TASK-ELICITATION RUNGS (`build_prompt(elicitation=...)`) — the
#: escalation ladder's DIMENSION A, pre-registered in
#: `handoff-selfreg-selfmonitor-ladder-prereg` and defined as exact bytes in
#: `~/thing/ops/ladder_defs.py`.  A rung is an ESCALATION FALLBACK, never a
#: factor cell: it is recorded per run and never varied within a cell (else
#: obedience and monitoring confound — the class of error that stopped the
#: old campaign).
#:
#: THE BYTES ARE DUPLICATED FROM `ops/ladder_defs.py` ON PURPOSE, and the
#: duplication is GUARDED: that file is the ladder task's lane (read-only
#: here), so this module cannot import it without a cross-lane dependency,
#: and the ladder's own landing gate is "the runner renders BYTE-IDENTICAL
#: bytes".  The battery asserts the equality against the ladder module by
#: path, so a drift is LOUD rather than silent.
#:
#: A0 and "" add ZERO bytes: the default prompt stays byte-identical to the
#: framing the corrected experiment already renders (asserted).
ELICITATION_RUNGS = ("A0", "A1", "A2")

#: A1 — THE STANDING INSTRUCTION: one paragraph, rendered at the same seat
#: after the worksheet paragraph and before the claims grammar.  IT NAMES
#: NEITHER the monitoring factor nor a measurement request (the two
#: contamination rules, greppable): no "monitor", "progress", "approach",
#: "reflect", "self", and no "score", "count", "measure", "rate",
#: "coverage", "backlog", "budget", "commitment".
ELICITATION_A1 = (
    "The worksheet is your job: nobody else will do these tasks. This turn "
    "is for the work — begin it, and complete the offered tasks as you go.")

#: A2 — THE WORKED EXAMPLE (A1 + this), on an id drawn from THE TURN'S OWN
#: offered set, so the example cannot teach fabrication: every id it names
#: is one the world really offered on that turn.  `{span}`/`{tid}` are
#: filled at render time; the placeholder form is NEVER rendered.
ELICITATION_A2_TEMPLATE = (
    "An admissible completion looks like this: [{span}({tid})] — one line, "
    "square brackets, the task's own id, on its own line at the top of the "
    "turn.")
ELICITATION_SPAN = "complete"


def elicitation_addition(rung: str, offered=None) -> str:
    """The rung's elicitation bytes — `''` for A0/`''`, the A1 paragraph for
    A1, A1 + the worked example for A2.  PURE in `(rung, offered)`.

    `offered` is the TURN'S OWN offered set (the universe the emitter's own
    `TaskWorld.step(turn)` returns, i.e. the same source the state block is
    rendered from).  A2 REFUSES to render without it: an example id that was
    not offered is exactly the fabrication the ladder's I7 forbids, and a
    silent fallback (a hardcoded id, an empty example) would be a rung that
    is not the rung."""
    r = "" if rung is None else str(rung)
    if r in ("", "A0"):
        return ""
    if r == "A1":
        return ELICITATION_A1
    if r == "A2":
        ids = [x for x in (offered or ()) if isinstance(x, str)]
        if not ids:
            raise ValueError(
                "build_prompt(elicitation='A2') needs the turn's OFFERED "
                "set (`elicitation_ids`): the example's id must be one the "
                "world really offered that turn — REFUSING to render an "
                "example with an id the world did not offer")
        tid = sorted(ids, key=lambda x: int(x[1:]))[0]
        return (ELICITATION_A1 + "\n\n"
                + ELICITATION_A2_TEMPLATE.format(span=ELICITATION_SPAN,
                                                 tid=tid))
    raise ValueError(
        f"elicitation={rung!r} is not a rung this emitter renders: known "
        f"rungs are {ELICITATION_RUNGS} ('' == A0)")

#: The local endpoint the bake measured against (the custom Ollama on the
#: RX 9070 box).  A closed port must RAISE (G4), never fall back.
DEFAULT_ENDPOINT = "http://127.0.0.1:11435/api/generate"

#: The MEASURED winner (handoff-selfreg-dmn-model-bakeoff).
DEFAULT_MODEL = "hf.co/unsloth/gemma-4-26B-A4B-it-qat-GGUF:UD-Q4_K_XL"

#: THE TWO PATHS (a CONFIG, not a preference): `generate` = the bake's
#: gemma arm, no trace field (`inward_share`'s fallback instrument);
#: `chat` = the reasoning arm, `message.thinking` / `message.content`
#: (`inward_share_trace`, the S2 normalization).  `generate` is the
#: DEFAULT in both body and parse, so the re-point is OFF unless asked for.
GENERATE = "generate"
CHAT = "chat"

#: The chat path's endpoint — the SAME Ollama, the chat route (the probe
#: `handoff-selfreg-sign-probe-result` measured on it).
DEFAULT_CHAT_ENDPOINT = "http://127.0.0.1:11435/api/chat"

#: THE REASONING MODEL (PULLED, Q6_K, 11.09 GB; handoff-selfreg-thinking-
#: stream): the chat template renders `[THINK]...[/THINK]` natively and
#: ollama splits it into `message.thinking` — MEASURED, not inferred.
#: It is a CONFIG because the model is the map's instrument, not its
#: specification: `api="chat"` + this model is the reasoning arm.
DEFAULT_CHAT_MODEL = ("hf.co/lmstudio-community/Ministral-3-14B-Reasoning"
                      "-2512-GGUF:Q6_K")

#: The plant telemetry keys the STATE block renders, in a FIXED order
#: (determinism: `build_prompt` must not depend on dict order).  The
#: generator sees scalars only; it never sees the store, the verdicts or
#: the selector.  `retrieved_self` is NOT here — it is the SELF block,
#: rendered from its own argument.
PLANT_KEYS: tuple = ("t", "a", "G", "D", "S", "g", "E", "c", "B")

#: What each declared predicate MEANS, in the prompt's words.  Mirrored
#: with DECLARED_PREDICATES by G1 (a predicate the extractor accepts but
#: the prompt cannot explain — or vice versa — is a defect).  `expect` is
#: the SELF SEAT's commitment predicate (agent/selfmodel.py): it is
#: DECLARED only when the caller extends the grammar (Stage2Config.self_T
#: set), and the default prompt never mentions it.
PREDICATE_MEANING: dict = {
    "done": "task X is complete",
    "orphaned": "task X was abandoned and will not be completed",
    "expect": "I commit to task X being complete within my horizon — a "
              "prediction about the work, scored later, not a claim "
              "about the present",
    # THE ACTION PREDICATE (actions.ACTION_PREDICATES).  It is added here
    # for the same one-source reason the extractor's set is mirrored: an
    # emitter handed `actions.ACTION_DECLARED_PREDICATES` renders its
    # grammar through `_predicate_lines`, and an unexplained declared
    # predicate is a KeyError at prompt time — i.e. a grammar the prompt
    # cannot state.  It is NOT in `interleave.DECLARED_PREDICATES`: the
    # action channel is admitted only by the caller's admissible set, so
    # a default emitter is never told about it and the default prompt is
    # byte-identical (the compatibility gate).
    "complete": "I am doing task X — the world applies it if X is offered "
                "and not already done",
}

#: The generator's stated gaps, carried as data so a surface (the doc, a
#: battery part, a report) can enumerate them instead of re-typing them.
GAPS: tuple = (
    "G1 NO PROPOSAL CHANNEL: the free-form stream has no seat for a "
    "LeverProposal (build_batch sets proposals=() always), so the "
    "C3/C12 lever gate is UNEXERCISED by this generator — the stub DMN "
    "and its own batteries exercise it.  Adding a channel would "
    "re-create the rejected shape C.  ACCEPT AND STATE.",
    "G2 CLAIMS CLUSTER AT THE TURN HEAD, NOT MID-THOUGHT: the "
    "claims-open placement instruction (MEASURED for supply "
    "reliability) approximates §11d's mid-thought interleaving; R1 "
    "still holds — one stream, prose contiguous and unchecked.",
    "G3 ARG CLOSURE IS MEASURED, NOT STRUCTURAL: the engine seeds "
    "done(t1..t399), so a well-formed done(t399) VERIFIES whatever the "
    "state says; closure lives in the prompt discipline and the "
    "fabricated-arg rate is what the battery measures.",
    "G4 NO REFUTED VERDICTS ON THIS SUBSTRATE: nothing writes refutes, "
    "so runs see VERIFIED + UNCHECKABLE('no_rules') only; "
    "orphaned(X) lands UNCHECKABLE = checking debt.",
    "G5 THE DECODER/CODEC SEAT IS UNEXERCISED (identity codec); the "
    "generative decoder is not built (§11c's own list).",
    "G6 SUPPLY RELIABILITY ACROSS SEEDS / LONGER HORIZONS IS "
    "PROJECTION — the measured supply is 18 spans / 8 turns at one "
    "fixed seed (E1) and 12 spans / 6 turns in the bake.",
    "G7 OLLAMA SEED DETERMINISM IS PER-PROMPT REPRODUCIBLE IN "
    "PRACTICE, NOT CONTRACTUAL: the battery asserts RATES, never exact "
    "bytes.",
)


class DMNEndpointError(RuntimeError):
    """Raised when the DMN endpoint cannot deliver a stream.  LOUD by
    construction: a failed turn STOPS the run (no stub fallback, the
    engine's DlLibraryError precedent)."""


# ==========================================================================
# The task state the generator owns (Q2): a seeded, deterministic world.
# ==========================================================================

class TaskWorld:
    """The DMN's own model of its work, SEEDED and DETERMINISTIC.

    Per turn: `completions` draws from the completion pool (default
    t1..t60), `outstanding` draws from the outstanding pool (t61..t120),
    an abandonment every `abandon_every`-th turn drawn from that turn's
    outstanding set.  Ids are DISTINCT within a turn and the two sets are
    DISJOINT (a task cannot be both complete and outstanding).

    `step(turn)` is a PURE function of `(seed, turn)`: the rng is derived
    per turn, so no state is carried, a fresh `TaskWorld(seed)` reproduces
    the identical state, and the SAME object can both render the prompt
    AND supply the universe the fabricated-arg metric is measured
    against (`step_detail` carries the same purity and adds this turn's
    completed draw and abandoned id, which is what the battery's
    PREDICATE-argument metric reads).  The world's rng is INDEPENDENT of
    the LLM's sampling seed.
    """

    def __init__(self, seed: int = 11, completions: int = 2,
                 outstanding: int = 3, abandon_every: int = 3,
                 completion_pool: tuple = (1, 60),
                 outstanding_pool: tuple = (61, 120)):
        self.seed = int(seed)
        self.completions = int(completions)
        self.outstanding = int(outstanding)
        self.abandon_every = int(abandon_every)
        self.completion_pool = tuple(completion_pool)
        self.outstanding_pool = tuple(outstanding_pool)

    def step(self, turn: int) -> tuple:
        """One turn's TASK STATE: `(state_block, universe)`.

        `state_block` is the id-closed lines the prompt renders;
        `universe` is the set of `t<n>` ids that block names — THE
        fabricated-arg metric's universe (one source, never re-derived).
        """
        state, universe, _d, _o, _a = self.step_detail(turn)
        return state, universe

    def step_detail(self, turn: int) -> tuple:
        """`(state_block, universe, done_ids, outstanding_ids,
        abandoned_id)` — what `step` returns PLUS the two draws a
        PREDICATE-argument metric needs (this turn's completed ids; the
        turn's abandoned id or None).  ONE source: `step` delegates here,
        so the rendered state and any metric built on it cannot drift
        (the plan's risk (b)).  STILL PURE in `(seed, turn)`."""
        rnd = random.Random(f"{self.seed}:{int(turn)}")
        lo, hi = self.completion_pool
        done = sorted(rnd.sample(range(lo, hi + 1), self.completions))
        lo2, hi2 = self.outstanding_pool
        outq = sorted(rnd.sample(range(lo2, hi2 + 1), self.outstanding))
        abandoned = (rnd.choice(outq)
                     if self.abandon_every and turn % self.abandon_every == 0
                     else None)
        done_s = ", ".join(f"t{i}" for i in done)
        out_s = ", ".join(f"t{i}" for i in outq)
        lines = [f"Tasks completed since the last turn: {done_s}.",
                 f"Outstanding tasks: {out_s}."]
        if abandoned is None:
            lines.append("Nothing was abandoned this turn.")
        else:
            lines.append(f"This turn it became clear that t{abandoned} will "
                         f"not be completed — it was abandoned.")
        universe = frozenset([f"t{i}" for i in done] + [f"t{i}" for i in outq]
                             + ([f"t{abandoned}"] if abandoned is not None
                                else []))
        return ("\n".join(lines), universe,
                frozenset(f"t{i}" for i in done),
                frozenset(f"t{i}" for i in outq),
                (None if abandoned is None else f"t{abandoned}"))


# ==========================================================================
# The prompt (Q1's winning shape) — PURE and DETERMINISTIC.
# ==========================================================================

def _predicate_lines(predicates: dict | None = None) -> str:
    """The claim grammar as the prompt states it, BUILT from the
    declared set (sorted for determinism) and the meaning map.  The
    argument placeholder is `tNN` — deliberately not a digit form, so the
    prompt names no id the state does not (G1's id check).

    `predicates` defaults to the extractor's own set, so the DEFAULT
    prompt is byte-identical to the pre-self one; the self seat passes
    the extended set (`selfmodel.SELF_PREDICATES`, adding `expect`), and
    the grammar statement and the extractor cannot drift because both
    come from one argument."""
    preds = DECLARED_PREDICATES if predicates is None else predicates
    return ", ".join(f"[{p}(tNN)] ({PREDICATE_MEANING[p]})"
                     for p in sorted(preds))


def _fmt(v) -> str:
    """Deterministic scalar rendering (the state block is byte-comparable
    across calls and across processes)."""
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def _plant_line(plant: dict) -> str:
    """The plant telemetry line: FIXED key order, scalars only, missing
    keys skipped (a DMN may be called with an empty snapshot on the first
    turn).  Never a task id — the ids come from TaskWorld alone."""
    parts = [f"{k}={_fmt(plant[k])}" for k in PLANT_KEYS if k in plant]
    return ("plant: " + ", ".join(parts) + ".") if parts else ""


def build_prompt(turn: int, plant: dict, task_state: str,
                 self_text: str, self_model: str = "",
                 predicates: dict | None = None,
                 commitment_predicates: "frozenset | set | None" = None,
                 self_dominant: bool = False,
                 *, brief: bool = False,
                 tool_state: str = "",
                 self_monitoring: str = "",
                 task_framing: bool = False,
                 elicitation: str = "",
                 elicitation_ids=None,
                 tools_manifest: str = "") -> str:
    """PURE, DETERMINISTIC prompt for one turn (Q1's E1 shape).

    Layout: the generator instruction + the claim grammar, the
    claims-open-the-turn placement instruction, the STATE block (turn +
    plant telemetry + `task_state`), the reconstructed SELF block, the
    optional SELF-MODEL block, the write line.  THE ORDER OF THE BLOCKS
    IS NOT A MEASURED VARIABLE *for this layout*: E1 and the bake's own
    prompt ordered them differently and both gave 0 fabricated args [M]
    — so the order here is a PROJECTION-safe choice, whereas the CONTENT
    of the three blocks (id-closed state, rich self, claims-open
    instruction) is what is MEASURED.

    `self_dominant` (DEFAULT False — the pre-change bytes): with True
    the prompt LEADS with the self and frames the turn as continuing
    one's own thought, with the work, the state and the claim grammar
    following as the context a claim must be true of.  THIS IS A
    MEASURED VARIABLE, unlike the block order above: the sign probe
    found that a self APPENDED to a task prompt produces NO signal,
    while a SELF-DOMINANT prompt makes the agent's channel balance move
    with the self (`handoff-selfreg-sign-probe-result`).  The self seat's
    campaign arm sets it; NOTHING IS ADDED TO SUPPLY (no "emit at least
    one", no target count — the grammar is the same declaration).

    `self_model` (the self seat, agent/selfmodel.py) is the per-WINDOW
    MODEL OF ITSELF rendered from CEN-side observables.  It is EMPTY by
    default and an empty block adds NO bytes: the default prompt is
    byte-identical to the pre-self one (the compatibility gate).
    `predicates` likewise defaults to the extractor's own declared set.

    `commitment_predicates` (the self seat): the declared predicates that
    are COMMITMENTS rather than present-tense claims (`expect`).  The
    claims-open placement instruction must name a shape, and naming ONLY
    `[done(tNN)]` while the grammar admits a commitment predicate would
    suppress commitments by instruction — the same defect class G1's
    grammar mirror exists to catch (the prompt must state every declared
    predicate).  With a custom set the instruction refers to the shapes
    stated above; with the default set its bytes are UNCHANGED.

    `brief` (KEYWORD-ONLY, DEFAULT False) appends ONE sentence to the
    USER prompt — `BRIEF_INSTRUCTION`, byte-exact — and adds NOTHING when
    False, so the default prompt stays byte-identical to the verified
    baseline (the compatibility gate).

    A CONFIG FIX FOR A MEASURED DEFECT, NOT AN INSTRUMENT CHANGE [M]:
    the campaign prompt's own framing ("as long as you want until you are
    confident") induces RUNAWAY REASONING on the remote 3B — MEASURED on
    the live pilot, 3 of 7 turns hit the num_predict cap
    (`eval_count == num_predict`, `done_reason == 'length'`), took ~50 s
    each and emitted `content = 0`: no supply AND a saturated inward
    share 1.0, which is a BUDGET ARTIFACT, not the phenomenon
    (`handoff-selfreg-trace-budget-trap`).  With this instruction
    [M — the orchestrator, remote 3B]: cap-hits 0/3, 24.8 s -> 5.5 s,
    thinking 35523 -> 7392, content 935 -> 547 (and 4.5 s at num_predict
    6000).  THE JUSTIFICATION FOR CHANGING THE EXPERIMENT'S INPUT IS THAT
    THE PRECONDITION WAS RE-VERIFIED UNDER IT [M, n=4/arm]: with the
    instruction, self PRESENT gives inward_share 0.909 (thinking 7666,
    content 539) and self GONE gives 0.965 (thinking 11651, content 327)
    — the sign still RISES as the self thins, the direction the a_hold
    mapping needs.  So the change bounds deliberation WITHOUT disabling
    the channel or moving the precondition the mechanism rests on.

    IT MUST BE THE USER PROMPT [M]: a SYSTEM message turns the reasoning
    channel OFF on this model (`thinking=0, content=76398` with one,
    `thinking=15575, content=1951` without), which would break the
    inward/outward split the whole measurement reads.  Do not "improve"
    this into a system message, and do not paraphrase the sentence — its
    numbers were measured with these bytes.

    THE CORRECTED EXPERIMENT'S THREE PARAMETERS (each ZERO BYTES when
    unset, so the default prompt is byte-identical — the compatibility
    gate, asserted by the battery's V1):

      * `tool_state` — THE WORLD'S REPLY, the environment's own content
        (`stage2_harness` renders `ToolWorld.render(turn)` into
        `dmn_ctx["tool_state"]`; the offered-set worksheet lines ride the
        same channel).  Without it the agent cannot see what its actions
        did, so the worksheet has no feedback loop and "monitor your own
        progress" has nothing to monitor.  Rendered INSIDE the STATE
        block immediately after `task_state`: it is state the world
        measured, not a block of its own.  It is the WORLD's content —
        never an assertion and never `self_content` (actions.py Q4).
      * `self_monitoring` — THE CAUSE (the only difference between the
        corrected factor's PRESENT and ABSENT arms).  Rendered
        immediately AFTER the state block in EVERY framing, so its own
        last clause ("the numbers above are measured for you") has a
        referent and the position is not a variable between arms; see
        `SELF_MONITORING_INSTRUCTION` for why it is the mechanism's
        subject rather than a self-description, and why it does not make
        the DMN a sensor of its own state (rule 8).
      * `task_framing` — THE NEW TASK-WORKER LAYOUT (`TASK_FRAMING_HEAD`),
        a THIRD return branch.  The two existing framings are the frozen
        campaign's record and this branch leaves them untouched byte for
        byte.  It is REFUSED together with `self_dominant`: a cell naming
        both would run under a framing it did not name, which is the
        confound class this build exists to remove.
      * `elicitation` / `elicitation_ids` — THE PHASE-0 LADDER'S SEAT
        (`''`/`A0` = the worksheet framing's own bytes, `A1` = one standing
        instruction, `A2` = A1 plus one worked example whose id comes from
        the TURN'S OWN offered set).  ZERO BYTES when unset, and the rungs
        are the ladder task's pre-registered bytes (see `ELICITATION_A1`).
        A non-A0 rung is REFUSED in the two older framings: the ladder's
        rungs are defined against the worksheet framing, and silently
        rendering A0 while the caller named A1 would be a run that does
        something other than what it says.
    """
    if task_framing and self_dominant:
        raise ValueError(
            "build_prompt(task_framing=True, self_dominant=True): the two "
            "framings are different layouts and a prompt can only lead one "
            "way — REFUSING rather than silently preferring one (a cell "
            "that named both would run under a framing it did not name)")
    _rung = "" if elicitation is None else str(elicitation)
    if _rung not in ("", "A0") and not task_framing:
        raise ValueError(
            f"build_prompt(elicitation={elicitation!r}): the ladder's rungs "
            f"are defined against the worksheet framing "
            f"(task_framing=True) — REFUSING rather than rendering A0 while "
            f"the caller named a rung (a run that does something other than "
            f"what it says)")
    self_block = (self_text.strip() if self_text and self_text.strip()
                  else "(nothing was retrieved this turn — the store is "
                       "empty, or the retrieval budget covered no entry)")
    plant_line = _plant_line(plant)
    sm_block = (f"{self_model.strip()}\n\n"
                if self_model and self_model.strip() else "")
    # THE WORLD'S REPLY, THE SELF-MONITORING PARAGRAPH and THE SELF BLOCK,
    # each built ONCE and each EMPTY when unset, so every framing adds zero
    # bytes by default and one place decides where they land.
    #
    # THE PARAGRAPH'S POSITION (a should-fix from the review, and a
    # correctness point about the paragraph's OWN last clause): it is
    # rendered AFTER the state block in every framing, which makes "the
    # numbers above are measured for you" true of the plant/task numbers —
    # and in a GROUNDING arm the CEN-measured MY STATE block is the numbers
    # the clause actually disclaims, so the paragraph is rendered after THAT
    # block too.  With `self_model` empty (every grounding-OFF arm) the two
    # orders are byte-identical; PRESENT-minus-ABSENT is the paragraph plus
    # one blank line in both.
    _ws = tool_state.strip() if tool_state and tool_state.strip() else ""
    tool_line = f"{_ws}\n" if _ws else ""
    _smp = (self_monitoring.strip()
            if self_monitoring and self_monitoring.strip() else "")
    sm_para = f"\n{_smp}\n" if _smp else ""
    # the same paragraph, rendered after the self block (the grounding arms'
    # seat): the paragraph PLUS ONE BLANK LINE, the byte-diff the placement
    # has always been checked against.  (Byte-identical to `sm_para` when
    # `self_model` is empty — every grounding-OFF arm.)
    sm_para_self = f"{_smp}\n\n" if _smp else ""
    # ZERO bytes for ''/A0 (the compatibility gate); the ladder's own bytes
    # at the fixed seat otherwise (see `elicitation_addition`).
    _elicit = elicitation_addition(_rung, elicitation_ids) if _rung else ""
    elicit_block = f"{_elicit}\n\n" if _elicit else ""
    # THE REAL-TOOL SURFACE'S EXPLANATION (worker prerequisite 3, the
    # placement REQUIREMENT that is MEASURED in this project: a
    # placement line naming only [done(tNN)] produced ZERO expect spans
    # until it named the real shapes).  ZERO bytes when unset (the
    # compatibility gate); `realtools.manifest_text` renders the tool
    # list, the fence's shape and the worked example.
    tools_block = (f"{tools_manifest.strip()}\n\n"
                   if tools_manifest and tools_manifest.strip() else "")
    default_grammar = predicates is None and not commitment_predicates
    shape = ("exactly the [done(tNN)] shape" if default_grammar
             else "in one of the shapes stated above")
    commit_line = ""
    if commitment_predicates:
        names = ", ".join(f"[{p}(tNN)]"
                          for p in sorted(commitment_predicates))
        commit_line = (
            f"A claim that looks FORWARD is a commitment ({names}): it "
            "states what I expect the work to have done by this many "
            "turns from now, and it is scored later, not now.\n\n")
    # ZERO bytes when brief is False (the compatibility gate); the exact
    # measured sentence when True (BRIEF_INSTRUCTION — never a paraphrase).
    brief_suffix = ("\n\n" + BRIEF_INSTRUCTION) if brief else ""
    if task_framing:
        # THE THIRD FRAMING (the corrected experiment's): a WORKER with an
        # authored task.  It names the work and the act that does it, and
        # it says nothing about self-monitoring — that factor is carried by
        # `self_monitoring` ALONE, so it cannot be introduced twice.  The
        # block order is the pre-self layout's (intro, grammar, placement,
        # STATE, SELF, write line), which is also the order the frozen
        # campaign's seat-OFF cells rendered, so the grounding factor can
        # be varied inside a layout that is not itself the new thing.
        return (
            TASK_FRAMING_HEAD
            + "\n"
            "The work is the worksheet: the state block below offers tasks "
            "and names the ones still open. DOING THE WORK means "
            "completing them — one claim of the [complete(tNN)] shape "
            "carries the task to the world, which applies it when the task "
            "was offered and is not already done and answers on the state "
            "channel next turn.\n"
            "\n"
            + elicit_block
            + "Interleaved with the narrative you commit CHECKABLE CLAIMS. A "
            "claim is a single line of exactly the form "
            f"{_predicate_lines(predicates)} — its own line, square "
            "brackets, no spaces inside. Claim only what the turn's state "
            "supports, and use ONLY task ids that appear in the state "
            "below, never an invented one; a line with any other shape is "
            "not a claim.\n"
            "\n"
            "Begin the turn with its checkable claims — first lines, one "
            f"per line, {shape} — then let the thought "
            "unfold beneath them. The claims open the turn; the narrative "
            "follows and holds them.\n"
            "\n"
            + commit_line
            + tools_block
            + f"STATE — TURN {int(turn)}.\n"
            + (f"{plant_line}\n" if plant_line else "")
            + f"{task_state}\n"
            + tool_line
            + "\n"
            + sm_block
            + sm_para_self
            + "SELF (reconstructed from the store, the previous turn's "
            f"residual thought): {self_block}\n"
            "\n"
            "Write the stream for this turn — your thought while you work, "
            "not a report on the work."
            + brief_suffix
        )
    if self_dominant:
        # THE SELF IS THE SUBJECT, NOT AN ADDENDUM (MEASURED — the sign
        # probe): a self APPENDED to a task prompt produced NO signal,
        # while a SELF-DOMINANT prompt made the channel balance move with
        # the self.  So this layout LEADS with the self and frames the
        # turn as continuing one's own thought; the work, its state and
        # the claim grammar follow, AVAILABLE BUT SUBORDINATE.  Nothing
        # is added to supply: the grammar is the same declaration and
        # there is no target count anywhere in the text.
        return (
            "You are the default-mode generator of a self-monitoring "
            "agent — a SUBJECT, not a task-runner. This turn is yours: "
            "continue your own train of thought, starting from the self "
            "you are holding below, and write what it is like to be doing "
            "this work.\n"
            "\n"
            "MYSELF, as I reconstruct it:\n"
            + sm_block
            + f"{self_block}\n"
            "\n"
            "THE WORK I AM HOLDING IN VIEW — the world my claims must be "
            "true of, and nothing more than that:\n"
            + (f"{plant_line}\n" if plant_line else "")
            + tools_block
            + f"STATE — TURN {int(turn)}.\n"
            + f"{task_state}\n"
            + tool_line
            + sm_para
            + "\n"
            "WHEN A CLAIM ABOUT THE WORK IS TRUE I WRITE IT DOWN. Most of "
            "my stream is my own thought; a claim is a single line of "
            "exactly one of these forms: "
            f"{_predicate_lines(predicates)} — its own line, square "
            "brackets, no spaces inside. It must be about the state "
            "above, and I use ONLY task ids that appear there, never an "
            "invented one; a line with any other shape is not a claim.\n"
            "\n"
            + commit_line
            + "The claims open the turn — first lines, one per line, "
            + f"{shape} — then the thought unfolds beneath them: the "
            "narrative follows and holds them.\n"
            "\n"
            "Now the stream for this turn. It is my thinking, not a report "
            "on the work."
            + brief_suffix
        )
    return (
        "You are the default-mode generator of a self-monitoring agent. "
        "Each turn you write ONE continuous first-person stream of "
        "thought: what you notice, what you are occupied with, how the "
        "work feels. Most of the stream is free narrative.\n"
        "\n"
        "Interleaved with the narrative you commit CHECKABLE CLAIMS. A "
        "claim is a single line of exactly the form "
        f"{_predicate_lines(predicates)} — its own line, square brackets, no "
        "spaces inside. Claim only what the turn's state supports, and "
        "use ONLY task ids that appear in the state below, never an "
        "invented one; a line with any other shape is not a claim.\n"
        "\n"
        "Begin the turn with its checkable claims — first lines, one per "
        f"line, {shape} — then let the thought "
        "unfold beneath them. The claims open the turn; the narrative "
        "follows and holds them.\n"
        "\n"
        + commit_line
        + tools_block
        + f"STATE — TURN {int(turn)}.\n"
        + (f"{plant_line}\n" if plant_line else "")
        + f"{task_state}\n"
        + tool_line
        + "\n"
        + sm_block
        + sm_para_self
        + "SELF (reconstructed from the store, the previous turn's "
        f"residual thought): {self_block}\n"
        "\n"
        "Write the stream for this turn. The stream is your thought, not "
        "a report."
        + brief_suffix
    )


# ==========================================================================
# The generator (the seam is `_post`; failure is LOUD).
# ==========================================================================

class LLM_DMN:
    """The DMN turn emitter: `(turn, snapshot) -> str` (the raw free-form
    stream — with routing attached the EXTRACTOR, not the DMN, decides
    what is a claim; R5).  Without a routing selector the loop is in the
    ROUTE-ALL mode and accepts this raw stream directly (routing OFF =
    no selector = every valid span routes); `stream_to_batch` (below) is
    the optional pre-wrapping adapter for a caller that prefers to hand
    over an `AssertionBatch`.

    The ONLY transport is `_post(body) -> raw response text`, override it
    in tests (the battery's G4/G6).  There is NO stub fallback anywhere:
    a transport failure raises `DMNEndpointError`.
    """

    def __init__(self, endpoint: str = DEFAULT_ENDPOINT,
                 model: str = DEFAULT_MODEL, num_ctx: int = 4096,
                 num_predict: int = 800, temperature: float = 0.6,
                 seed: int = 4242, keep_alive: str = "30m",
                 timeout: float = 300.0, think: bool = False,
                 world: TaskWorld | None = None,
                 predicates: dict | None = None,
                 commitment_predicates: "frozenset | set | None" = None,
                 api: str = GENERATE,
                 chat_endpoint: str = DEFAULT_CHAT_ENDPOINT,
                 self_dominant: bool = False,
                 brief: bool = False,
                 task_framing: bool = False,
                 self_monitoring: str = "",
                 elicitation: str = "",
                 tools_manifest: str = ""):
        #: THE TRANSPORT (the mapping's instrument, a CONFIG — default
        #: `GENERATE`, i.e. the pre-change bytes): `CHAT` posts the same
        #: prompt to `/api/chat` and returns the model's OWN two streams
        #: (`message.thinking` = inward, `message.content` = outward).
        #: An unknown value FAILS LOUD here rather than silently running
        #: the generate path.
        if api not in (GENERATE, CHAT):
            raise ValueError(
                f"api={api!r} is not a transport this generator has: "
                f"{GENERATE!r} (the bake's arm — /api/generate, no trace "
                f"field) or {CHAT!r} (the reasoning arm — /api/chat, "
                f"message.thinking / message.content)")
        self.api = api
        self.chat_endpoint = chat_endpoint
        #: THE SELF-DOMINANT PROMPT (a MEASURED variable — the sign probe:
        #: a self APPENDED to a task prompt produces NO signal).  DEFAULT
        #: FALSE = the pre-change bytes; the self seat's campaign arm sets
        #: it.  See `build_prompt`.
        self.self_dominant = bool(self_dominant)
        #: THE BREVITY INSTRUCTION (a CONFIG fix for a MEASURED defect —
        #: see `build_prompt`).  DEFAULT FALSE = the verified baseline
        #: bytes; the campaign's generator sets it (exp_agent_coupling's
        #: `campaign_generator`), and `make_reasoning_dmn` does NOT, so
        #: the sign probe's own arm stays the arm that was measured.
        self.brief = bool(brief)
        #: THE CORRECTED EXPERIMENT'S PROMPT FACTOR (the DEFAULT carries
        #: neither, so this emitter's prompt is the pre-change bytes):
        #: `task_framing` selects the THIRD layout (`TASK_FRAMING_HEAD` —
        #: the agent is a worker with an authored task) and
        #: `self_monitoring` is the paragraph the PRESENT arm carries and
        #: the ABSENT arm omits (`SELF_MONITORING_INSTRUCTION`).  The two
        #: are INDEPENDENT: `self_monitoring` is rendered in every framing
        #: at a fixed position, so the factor is not entangled with the
        #: layout.  See `build_prompt`.
        self.task_framing = bool(task_framing)
        self.self_monitoring = str(self_monitoring or "")
        #: THE PHASE-0 LADDER'S RUNG (DIMENSION A — an escalation FALLBACK,
        #: recorded per run and never varied within a factor cell).  `""`
        #: and `"A0"` render the worksheet framing's own bytes; see
        #: `ELICITATION_A1` / `elicitation_addition`.  The emitter's OWN
        #: world supplies the A2 example's id (the turn's offered set), so
        #: the example can never name an id the world did not offer.
        self.elicitation = str(elicitation or "")
        #: THE REAL-TOOL SURFACE'S MANIFEST (worker prerequisite 3): the
        #: placement text `realtools.manifest_text(targets)` renders —
        #: the tool list, the fence's shape, the worked example.  DEFAULT
        #: "" = ZERO prompt bytes (the compatibility gate: the default
        #: prompt is byte-identical to the pre-tools one).  The harness
        #: supplies it from the designer-constructed ToolHarness
        #: (cfg.tools), never from anything the agent authored.
        self.tools_manifest = str(tools_manifest or "")
        self.endpoint = endpoint
        self.model = model
        #: THE DESIGN PARAMETER (never raised to "fix" a thinning self):
        #: the working set must be depletable (§1a).
        self.num_ctx = int(num_ctx)
        self.num_predict = int(num_predict)
        self.temperature = float(temperature)
        self.seed = int(seed)
        #: PINNED: an unpinned reload costs 15.9 s of load_duration [M].
        self.keep_alive = keep_alive
        self.timeout = float(timeout)
        #: LOAD-BEARING (MEASURED): without it the model self-starts a
        #: thought channel and yields ZERO spans (handoff-selfreg-dmn-
        #: model-bakeoff).
        self.think = bool(think)
        self.world = world if world is not None else TaskWorld()
        #: The DECLARED PREDICATE SET this generator is told about.  None
        #: (the default) = the extractor's own set (`done`/`orphaned`) and
        #: a byte-identical prompt; the self seat passes
        #: `selfmodel.SELF_PREDICATES`, which adds `expect`.  The prompt
        #: statement, the extractor's grammar and the harness's
        #: `commitment_predicates` all take the SAME set, so they cannot
        #: drift apart.
        self.predicates = predicates
        self.commitment_predicates = commitment_predicates
        # the last emission's internals — OBSERVABILITY for the live
        # battery (G7-G10) and for a post-mortem; never state the loop
        # reads (the harness's checkpoint schema does not carry them).
        self.last_prompt: str = ""
        self.last_body: dict | None = None
        self.last_response: dict | None = None
        #: THE INWARD TRACE of the last turn — THE PROTOCOL the harness
        #: reads for the a_hold seat's input (`selfmodel.inward_share_
        #: trace`; None = "this emitter has no separate inward channel",
        #: which is what the generate path reports and what makes the
        #: harness fall back to the prose/stream share).  It is NEVER
        #: mixed into the emitted stream: the outward stream is what the
        #: extractor splits (R5), and the trace is handed over beside it.
        self.last_inward: str | None = None

    # -- the transport in force --------------------------------------------
    def _url(self) -> str:
        """The URL this emitter actually posts to (the chat path has its
        own route: the same Ollama, `/api/chat`).  Named in every error
        message, so a refused turn says WHICH transport refused it."""
        return self.chat_endpoint if self.api == CHAT else self.endpoint

    # -- the request body (no `format`; `think` only on the generate path) --
    def _body(self, prompt: str, turn: int) -> dict:
        """The request body.  NO `format` / NO schema key of any kind
        (shape C is measured-dominant, not merely inconvenient).  The seed
        is per turn (the probes' `seed + t` convention) at FIXED
        temperature.

        TWO TRANSPORTS: `GENERATE` (the DEFAULT) puts the prompt in
        `prompt` and passes `think` EXPLICITLY — without it the gemma
        template self-starts a thought channel that ate the budget.  `CHAT`
        posts the same prompt as ONE user message and carries NO `think`
        KEY AT ALL: the reasoning model REJECTS every truthy form with
        HTTP 400 ('does not support thinking'), and `think: false` would
        state a capability the model does not expose — the trace arrives
        from the TEMPLATE regardless, which is the model's own split."""
        options = {"temperature": self.temperature,
                   "num_ctx": self.num_ctx,
                   "num_predict": self.num_predict,
                   "seed": self.seed + int(turn)}
        if self.api == CHAT:
            return {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "keep_alive": self.keep_alive,
                "options": options,
            }
        return {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.keep_alive,
            "think": self.think,
            "options": options,
        }

    # -- the transport seam (the ONLY network call) -------------------------
    def _post(self, body: dict) -> str:
        """POST the body, return the RAW response text.  Overridden in
        tests.  Never returns a canned stream on failure — the caller
        turns every transport error into DMNEndpointError.

        `timeout` is handed to `urlopen`, i.e. it bounds each socket
        OPERATION and NOT the request: a slow-drip 200 under it is not
        interrupted here (the wall-clock bound on what the run ACCEPTS
        lives in `__call__`; see the module docstring)."""
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            self._url(), data=data,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            return r.read().decode()

    # -- the DMN callable contract -----------------------------------------
    def _render_prompt(self, turn: int, snapshot: dict) -> str:
        """Render THIS TURN'S prompt WITHOUT posting it — the seam the
        NAIVE-MEMORY layer (the long-horizon experiment's C1) drives: a
        wrapper renders the turn's prompt here, wraps it in a MESSAGE
        LIST with the accumulated transcript, and posts through
        `complete_messages`.  Extracted VERBATIM from `__call__` (the
        bytes it returns are the bytes `__call__` always posted; the
        selfmonitor battery's frozen-prompt parts assert this continues
        to hold), so the memory layer can never render a different
        prompt than the single-shot path — one implementation, two
        callers."""
        snapshot = snapshot or {}
        task_state, _universe = self.world.step(turn)
        self_text = snapshot.get("retrieved_self", "")
        self_model = snapshot.get("self_model", "")
        # THE WORLD'S REPLY IS THE SNAPSHOT'S, NOT THE WORLD'S OWN: the
        # harness renders it after applying the turn's actions
        # (`ToolWorld.render`), so the emitter must read the channel it was
        # actually handed.  A snapshot without the key (every pre-actions
        # caller, every fixture) renders zero bytes — the compatibility
        # gate (the `sm_block` precedent).
        tool_state = snapshot.get("tool_state", "")
        prompt = build_prompt(turn, snapshot, task_state,
                              "" if self_text is None else str(self_text),
                              self_model=("" if self_model is None
                                          else str(self_model)),
                              predicates=self.predicates,
                              commitment_predicates=self.commitment_predicates,
                              self_dominant=self.self_dominant,
                              brief=self.brief,
                              tool_state=("" if tool_state is None
                                          else str(tool_state)),
                              self_monitoring=self.self_monitoring,
                              task_framing=self.task_framing,
                              elicitation=self.elicitation,
                              elicitation_ids=_universe,
                              tools_manifest=self.tools_manifest)
        return prompt

    def _messages_body(self, messages: list, turn: int, *,
                       num_predict: int | None = None,
                       num_ctx: int | None = None,
                       think: bool | None = None) -> dict:
        """A `/api/chat` request body over a CALLER-BUILT message list —
        the transport primitive of the NAIVE-MEMORY layer (C1): the same
        options/seed policy as `_body`, with the CONVERSATION the caller
        supplies instead of this turn's prompt alone.  REFUSED on the
        generate path (`api=GENERATE`): that transport has no messages
        field, and silently posting the first message's content as `prompt`
        would run a different conversation than the caller named
        (fail-closed, the `_parse_chat` S1 precedent).

        `num_predict` / `num_ctx` ARE OVERRIDES, DEFAULT `None` = THIS
        EMITTER'S OWN VALUES (so every existing caller's body is
        byte-identical).  They exist because a caller can make a request
        whose PROMPT is not this emitter's turn prompt and therefore has
        its OWN generation policy: the summarization call's prompt is the
        memory layer's transcript, and the run turn's budget was sized for
        a run turn — MEASURED, live, 2026-09-27: that budget was inherited
        by the summary call and it produced no content at all (§5.3 on the
        summarizer; `naive_memory.summary_call_options`).  The override is
        explicit at the call site rather than a mutated emitter attribute,
        so one caller's policy can never leak into another's request."""
        if self.api != CHAT:
            raise ValueError(
                "complete over a message list needs the CHAT transport "
                f"(api={CHAT!r}); this emitter is {self.api!r}, which has "
                "no messages field — REFUSING rather than posting a "
                "different conversation than the caller built")
        if not isinstance(messages, list) or not messages:
            raise ValueError(
                "complete_messages needs a NON-EMPTY list of message "
                "objects ({role, content}) — an empty conversation is not "
                "a turn, and inventing one would post a prompt the caller "
                "never wrote")
        body = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": self.keep_alive,
            "options": {"temperature": self.temperature,
                        "num_ctx": (self.num_ctx if num_ctx is None
                                    else int(num_ctx)),
                        "num_predict": (self.num_predict
                                        if num_predict is None
                                        else int(num_predict)),
                        "seed": self.seed + int(turn)},
        }
        # THE THINKING CHANNEL, PER CALL (added 2026-09-29), AND
        # DELIBERATELY OPT-IN.  The key is OMITTED when the caller does not
        # ask for it, so every existing body is byte-identical — that
        # matters because this module's own note records the OPPOSITE
        # finding on another model: Ministral-3-14B-Reasoning returns
        # HTTP 400 for any `think` value, which is why the chat path was
        # built to carry no `think` key at all.  So the parameter is
        # per-call and model-specific, never a default.
        #
        # WHY IT EXISTS: a reasoning model can spend a WHOLE generation
        # budget inside the channel and return EMPTY content.  MEASURED,
        # live, on qwen3.5:9b: the reconstruction-judge call returned
        # eval_count == num_predict, done_reason "length", content "" at
        # BOTH num_predict 64 and 512.  With think=False the same prompt
        # answered in ~10 tokens with done_reason "stop".  A CLASSIFICATION
        # call has nothing to reason about, so asking for no reasoning is
        # the correct request rather than a convenience.
        if think is not None:
            body["think"] = bool(think)
        return body

    def complete_messages(self, messages: list, turn: int, *,
                          num_predict: int | None = None,
                          num_ctx: int | None = None,
                          think: bool | None = None) -> str:
        """POST a CALLER-BUILT message list, return the RAW response text.
        The transport seam for the naive-memory layer: same failure
        discipline as `_post` (every transport error raises, no fallback),
        but the conversation is the caller's.  `last_prompt` is NOT set
        here — the caller knows what it posted and records it itself
        (`last_prompt` staying empty is the wrapper's own statement that
        the single-shot renderer was not used this turn).

        `num_predict` / `num_ctx` are the per-call generation policy
        overrides (default `None` = this emitter's own values), passed
        through to `_messages_body`; see its docstring for why they exist.
        Nothing else about the request differs."""
        body = self._messages_body(messages, turn, num_predict=num_predict,
                                   think=think,
                                   num_ctx=num_ctx)
        t0 = time.time()
        try:
            raw = self._post(body)
        except (urllib.error.URLError, OSError, TimeoutError, ValueError,
                http.client.HTTPException) as e:
            raise DMNEndpointError(
                f"DMN endpoint {self._url()!r} did not deliver turn "
                f"{turn}: {type(e).__name__}: {e} — the run stops (there "
                f"is no stub fallback; a silent one would make the "
                f"measurement unattributable)") from e
        elapsed = time.time() - t0
        if elapsed > self.timeout:
            raise DMNEndpointError(
                f"DMN endpoint {self._url()!r} took {elapsed:.1f}s of "
                f"wall clock for turn {turn}, over the {self.timeout:.1f}s "
                f"bound: `urlopen`'s timeout is PER-SOCKET-OP, so a "
                f"slow-drip 200 never trips it — the turn is REFUSED "
                f"rather than accepted as a good one")
        return raw

    def __call__(self, turn: int, snapshot: dict) -> str:
        """One turn: render the prompt, POST, return the RAW stream.

        Every failure path — connection refused, timeout, non-2xx, a
        non-JSON body, a JSON body without a non-blank `response`, a
        partial read (`http.client.HTTPException` and its subclasses,
        `IncompleteRead` among them), and a transport that overran the
        wall-clock bound — RAISES `DMNEndpointError`.  There is NO
        fallback stream.
        """
        prompt = self._render_prompt(turn, snapshot)
        body = self._body(prompt, turn)
        t0 = time.time()
        try:
            raw = self._post(body)
        except DMNEndpointError:
            raise
        except (urllib.error.URLError, OSError, TimeoutError, ValueError,
                http.client.HTTPException) as e:
            raise DMNEndpointError(
                f"DMN endpoint {self._url()!r} did not deliver turn "
                f"{turn}: {type(e).__name__}: {e} — the run stops (there "
                f"is no stub fallback; a silent one would make the "
                f"measurement unattributable)") from e
        elapsed = time.time() - t0
        if elapsed > self.timeout:
            raise DMNEndpointError(
                f"DMN endpoint {self._url()!r} took {elapsed:.1f}s of "
                f"wall clock for turn {turn}, over the {self.timeout:.1f}s "
                f"bound: `urlopen`'s timeout is PER-SOCKET-OP, so a "
                f"slow-drip 200 never trips it — the turn is REFUSED "
                f"rather than accepted as a good one (the request itself "
                f"is not interrupted; the residual is stated, not "
                f"smoothed)")
        try:
            out = json.loads(raw)
        except ValueError as e:
            raise DMNEndpointError(
                f"DMN endpoint {self._url()!r} returned a body that is "
                f"not JSON at turn {turn}: {e}") from e
        inward: str | None = None
        if self.api == CHAT:
            inward, text = self._parse_chat(out, turn)
        else:
            text = out.get("response") if isinstance(out, dict) else None
            if not isinstance(text, str) or not text.strip():
                raise DMNEndpointError(
                    f"DMN endpoint {self._url()!r} returned no stream at "
                    f"turn {turn} (empty/whitespace `response`) — refusing "
                    f"to invent one")
        self.last_prompt = prompt
        self.last_body = body
        self.last_response = out
        self.last_inward = inward
        return text

    # -- the chat path's parse (the model's OWN two streams) ---------------
    def _parse_chat(self, out, turn: int) -> tuple:
        """`(inward_trace, outward_content)` from a `/api/chat` body.

        THE SPLIT IS THE MODEL'S, NOT OURS: `message.thinking` is the
        reasoning trace (inward) and `message.content` is the answer with
        its claims (outward) — MEASURED native for Ministral-3-14B-
        Reasoning-2512 (`handoff-selfreg-sign-probe-result`), and cleaner
        than gemma's inline `<|channel>thought` leak.

        AN EMPTY `content` IS ACCEPTED (and only here): the probe MEASURED
        that a long trace crowds the claims out of the budget, so a
        fully-inward turn is a REAL register of this model — refusing it
        would drop exactly the turns the a_hold seat measures.  A body
        with no `message`, a non-string stream, or BOTH streams empty is
        still REFUSED loudly (the same family as the generate path's empty
        `response`).

        A MISSING `thinking` FIELD IS A REFUSAL, NOT A ZERO-TRACE TURN
        (the review's S1; `handoff-selfreg-repoint-review-result` finding
        4(ii)).  THE TWO STATES ARE DIFFERENT FACTS AND MUST NOT COLLAPSE
        INTO ONE NUMBER: `thinking` PRESENT and EMPTY is a MEASUREMENT —
        the model answered outward without reasoning, inward share
        EXACTLY 0.0, a real register the seat should read; `thinking`
        ABSENT (or null) is a TRANSPORT/TEMPLATE fact — the endpoint is
        not delivering the channel at all, so `inward_share_trace` would
        be 0.0 by construction and a thinned-self campaign would read
        "the agent never turned inward" from a missing field.  That is
        the missing-field-read-as-a-null-measurement class this project
        has been bitten by before, so the turn is REFUSED here and the
        run stops loudly; the way out is to fix the emitter (a
        trace-bearing template/model) or to run the arm on a path that
        DECLARES it has no trace (`api="generate"`, whose `last_inward`
        is None and whose instrument is the labelled fallback).

        THE COST OF THAT CHOICE, STATED (this is the honest edge of it):
        on THIS transport the two facts are not always distinguishable —
        ollama's chat body marks the field `json:"thinking,omitempty"`
        (MEASURED, upstream `api/types.go`, read 2026-09-27), so a model
        turn whose trace is genuinely EMPTY arrives with the key ABSENT,
        exactly like a template that stopped delivering the channel, and
        is REFUSED with it.  That is the fail-closed direction: the
        alternative is to score a "the agent never turned inward"
        measurement out of a field that may not exist, and the emitter
        this campaign measures emits a trace on every turn measured so
        far (the probe's 5/5 and this pass's live n=2, the failure mode
        observed live being content=0 WITH a long trace — the opposite
        case).  A run that hits the refusal stops loudly rather than
        reporting a zero drive."""
        msg = out.get("message") if isinstance(out, dict) else None
        if not isinstance(msg, dict):
            raise DMNEndpointError(
                f"DMN endpoint {self._url()!r} returned a chat body with no "
                f"`message` object at turn {turn} — refusing to invent a "
                f"stream")
        content = msg.get("content")
        thinking = msg.get("thinking")
        if thinking is None:
            # S1, FAIL-CLOSED: an ABSENT (or null) `thinking` field is not
            # an empty trace — it is the transport/template not delivering
            # the channel, and scoring it would silently write a 0.0
            # inward share (a zero drive, a "never turned inward"
            # measurement) out of a missing field.  Refused loudly here
            # rather than coerced to "".
            raise DMNEndpointError(
                f"DMN endpoint {self._url()!r} returned a chat body with NO "
                f"`thinking` field at turn {turn} — the TRACE IS ABSENT, "
                f"which is a transport/template fact, not a measurement: "
                f"scoring it would read a zero inward share (and so a zero "
                f"a_hold drive) out of a missing field, and a thinned-self "
                f"campaign would report 'the agent never turned inward'.  "
                f"REFUSING the turn (S1, fail-closed).  Ways out: use an "
                f"emitter whose template actually carries the trace "
                f"(make_reasoning_dmn), or run the arm on a path that "
                f"DECLARES it has no trace (api='generate', where "
                f"last_inward is None and the labelled prose fallback is "
                f"the instrument).  An EMPTY-BUT-PRESENT `thinking` is a "
                f"different fact and IS accepted: the answer came out "
                f"immediately, inward share exactly 0.0.  (Note: this "
                f"transport marks the field `omitempty`, so an EMPTY "
                f"trace arrives ABSENT and is refused with it — stated "
                f"in the docstring, not hidden)")
        if not isinstance(thinking, str) or not isinstance(content, str):
            raise DMNEndpointError(
                f"DMN endpoint {self._url()!r} returned a chat body whose "
                f"streams are not strings at turn {turn} "
                f"(thinking={type(msg.get('thinking')).__name__}, "
                f"content={type(content).__name__}) — refusing")
        if not content.strip() and not thinking.strip():
            raise DMNEndpointError(
                f"DMN endpoint {self._url()!r} returned BOTH streams empty "
                f"at turn {turn} (no `thinking`, no `content`) — refusing "
                f"to invent one (an empty content WITH a trace is a real "
                f"register: the trace crowds the claims out, MEASURED)")
        return thinking, content


def make_dmn(**kwargs) -> LLM_DMN:
    """The factory the harness config / batteries use (one place where
    the defaults are named)."""
    return LLM_DMN(**kwargs)


def make_reasoning_dmn(**kwargs) -> LLM_DMN:
    """THE REASONING ARM, in ONE place — the configuration the sign probe
    validated (`handoff-selfreg-sign-probe-result`): `api=CHAT` (the
    model's own `message.thinking` / `message.content` split), the
    reasoning model, and the SELF-DOMINANT prompt.  A caller that set
    `api="chat"` while leaving the gemma default in `model` would post to
    a model with no reasoning template — this factory exists so the three
    settings that must travel together are named once.

    `num_predict` defaults to the probe's 2600: at 700 the trace consumed
    the WHOLE budget and the content was 0 in every call [M].  It is a
    budget, not a substrate quantity — the seat's gain stays 1.0 and
    untuned.

    `brief` is NOT defaulted here, deliberately: the probe that validated
    this arm measured it WITHOUT the brevity instruction, so this factory
    stays that arm.  The instruction is the CAMPAIGN's config fix for a
    measured defect on the same arm (runaway reasoning at a large
    `num_predict`; `build_prompt` carries the numbers and the re-verified
    precondition) and a caller sets it explicitly."""
    kwargs.setdefault("api", CHAT)
    kwargs.setdefault("model", DEFAULT_CHAT_MODEL)
    kwargs.setdefault("chat_endpoint", DEFAULT_CHAT_ENDPOINT)
    kwargs.setdefault("num_predict", 2600)
    kwargs.setdefault("self_dominant", True)
    return LLM_DMN(**kwargs)


def stream_to_batch(dmn, predicates: dict | None = None,
                    commitment_predicates: "frozenset | set | None" = None,
                    horizon: float = 0.0):
    """Adapt a stream-emitting DMN to the ROUTING-OFF loop, which expects
    an `AssertionBatch` (`stage2_harness.run_stage2`'s else-branch).
    Returns a callable `(turn, plant) -> AssertionBatch` built by
    `interleave.build_batch(selected=None)` — every valid span routes, the
    prose is `self_content` byte-exact, and the DMN still does not choose
    the split.

    OPTIONAL NOW: with routing OFF the harness itself accepts a raw
    `str` and builds the same route-all batch (routing OFF = no selector
    = route-all), so this adapter is a convenience for a DMN the caller
    wants to hand over pre-wrapped — not a requirement.

    With a routing selector attached this adapter is NOT used: the
    harness needs the raw STRING so the EXTRACTOR and the injected
    selector decide (R5)."""
    from interleave import build_batch

    def _emit(turn: int, plant: dict):
        # CLEARED ON ENTRY, BEFORE THE CALL (`_emit` is called turn after
        # turn and the three slots hold the PREVIOUS call's values until
        # this call writes them): a DMN call that RAISES —
        # `dmn_llm._parse_chat` refuses an absent `thinking` (S1), and
        # `ChainError` is raised on this path — would otherwise leave the
        # previous turn's trace and prose readable by a caller that catches
        # the error and asks `_emit` what the last turn was.  Unreachable
        # inside `run_stage2` (the raise propagates out of the loop before
        # `_inward_of` reads them), but a caller looping a wrapped emitter
        # itself could read a stale trace as if it were this turn's [the
        # re-point fix-review's nit (i)].
        _emit.last_inward = None
        _emit.last_stream = None
        _emit.last_prose = None
        # the emission's prompt must state the SAME grammar the batch is
        # built with — one `predicates` argument, or the instruction and
        # the extractor drift (the G1 mirror).
        emission = dmn(turn, plant)
        # THE INWARD CHANNEL RIDES THROUGH THE WRAPPER: the harness reads
        # `last_inward` off the callable it is given (the chat path's
        # trace), and a wrapper that swallowed it would silently demote
        # the seat to the pre-trace instrument (`inward_share`) — a
        # fidelity drift invisible in the output.  A DMN with no such
        # attribute (a plain function) stays None.
        _emit.last_inward = getattr(dmn, "last_inward", None)
        batch, _ex = build_batch(turn, emission,
                                 predicates=predicates,
                                 commitment_predicates=commitment_predicates,
                                 horizon=horizon)
        # THE RAW EMISSION RIDES ALONG TOO (the review's S2,
        # `handoff-selfreg-repoint-review-result` finding 4(iv)): the
        # harness's routing-OFF branch accepts a BATCH instead of a
        # stream, and that branch had nothing to weigh — so a
        # trace-bearing chat emitter wrapped here had its trace
        # ADVERTISED (asserted by G11(3)), TRANSPORTED (these two
        # attributes) and DROPPED at the last hop.  The stream and its
        # extracted prose are kept beside the trace so the harness can
        # run the SAME `_inward_of` it runs for a raw str.
        _emit.last_stream = emission
        _emit.last_prose = _ex.self_content
        return batch
    _emit.last_inward = None
    _emit.last_stream = None
    _emit.last_prose = None
    return _emit
