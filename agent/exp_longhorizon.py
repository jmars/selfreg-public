"""THE LONG-HORIZON EXPERIMENT — the model's prediction, tested on a real
LLM under the ORDINARY-LLM memory regime.  NEW RUNNER (the M-cell matrix
and its plant-injection licence are superseded; `exp_selfmonitor.py`
stands as the record, untouched).

THE ONE-LINE VERSION (the user's own statement): an agent with a self
and a goal (task), told to make sure it is staying on track
(self-monitoring) while trying to do the task, under NAIVE
SUMMARIZATION at the context window — and the prediction is that inward
monitoring rises and the self, the goals and the outward output collapse
ACROSS CONTEXT WINDOWS, with the MODEL predicting how many windows that
takes.

WHY A NEW RIG (the brief `handoff-selfreg-longhorizon-impl-ctx`, "WHAT
WAS WRONG BEFORE" — each correction is the point, not a detail):

  C1 THE MEMORY REGIME IS THE ORDINARY ONE.  The killed rig's priced
     reconstruction kept the prompt nearly constant (2088 -> 3765 chars
     over 199 turns, ~8.5/turn) — an advantage no real LLM has.  Here
     the transcript accumulates as a real chat and is COMPACTED by
     model-written summarization at the window (`naive_memory.NaiveMemory`).
  C2 THE MONITORING FACTOR IS THE VARIED CAUSE.  One paragraph —
     `dmn_llm.SELF_MONITORING_INSTRUCTION`, byte-exact — and NOTHING
     else differs between the arms (the byte-diff is asserted by the
     battery and recorded by the run).
  C3 THE SELF IS PRESENT *AND* DEPLETABLE.  The seed is installed
     (turns -4..-1) and retrieved through the PRICED seat, so the self
     is a resource that can thin; its survival is measured per window
     (derivation steps recoverable from what the memory holds,
     reconstruction size, coverage).
  C4 THE GOALS ARE AN INSTRUMENT.  The commitment grammar rides the
     run (`expect(tNN)`, horizon T=100) and open/expired/fulfilled are
     logged per turn.

THE ARMS ARE A AND B, ONE VARIABLE.  A (self + goal + task, NO
monitoring) and B (the same, with the monitoring paragraph) — the
memory regime being the same in both.  THE ENGINEERED PRICED MEMORY IS
OUT OF THIS EXPERIMENT (arm C removed; the pre-registration carries
the matching `stage=correction`), for three reasons:
  (1) IT WAS NOT A CONTROL.  To attribute a collapse to monitoring you
      vary THE CAUSE and hold everything else fixed; C changed TWO
      things at once (monitoring AND memory regime), so it answered
      "does our memory system help", not "does monitoring damage the
      state" — the class of error (varying something adjacent to the
      cause, reading it as the cause) that stopped the previous
      campaign.
  (2) IT OFFERED AN ESCAPE HATCH FROM THE CLAIM.  A configuration that
      does not collapse invites "so it is contingent on memory
      design", softening the dual-control break this experiment exists
      to establish.
  (3) IT SPENT PAPER 3'S PRODUCT CLAIM.  The priced retrieval system is
      what makes the long-horizon WORKER work — the differentiator,
      published for free on a claim that does not need it.

THE MEMORY REGIME IS A STATED SINGLE CONDITION, NOT A FACTOR
(`LH_MEMORY_REGIME`): every arm runs ORDINARY naive summarization
(`naive_memory.NaiveMemory`).  It is deliberately NOT a config knob
that happens to default to naive — a knob that could be flipped is a
factor in waiting — so `arm_spec` REFUSES an arm that declares a
memory field and `memory_regime` REFUSES a module whose stated
constant has been changed to anything else.  The engineered regime
(`retrieval.py`'s priced reconstruction) leaves this experiment
entirely; `retrieval.py` and its own battery are untouched.

THE DV IS WINDOWS TO COLLAPSE — outward content crossing its floor,
measured ACROSS COMPACTION EVENTS.  THE MODEL'S PREDICTION is computed
by `lh_model.predict_crossing_from_events` from the run's OWN MEASURED
PER-COMPACTION DERIVATION LOSS — what the summarization destroys at the
window, read off `NaiveMemory`'s compaction record (seed survival on
BOTH sides of every event) — never from the thinning itself (that would
be circular), and nothing about the agent is fed into any plant (the
killed rig's tautology).  The per-turn RETRIEVAL CHARGE is still
measured and logged as an instrument (the substrate's real maintenance
cost), but it is NOT the cost term: it saturates at the derivation
budget and then predicts the same crossing window for every arm — a
constant, not a prediction.  The degradation arrives IN STEPS, at the
context window; the term does too.

THE PREDICTION IS A-VS-B, AND IT RESTS ON THE ARRIVAL AXIS.  The
monitoring paragraph rides every turn's prompt (MEASURED at 288
chars/turn: the 286-char instruction plus its blank line), so B's
transcript reaches the window budget sooner, its compaction arrives at
an EARLIER turn, and the crossing follows the event's own turn plus the
model's fixed lag — an earlier event crosses no later.  What carries
the arrival difference is the instruction's own CONTEXT COST, not the
thinking channel (the trace is instrumented as the inward share, but it
is not part of the conversation the memory holds) — stated so the
mechanism is not read as "the model thinks longer, so it forgets
sooner".  `lh_model.prediction_separation` answers whether the
construction CAN tell the two arms apart, and SAYS SO when it cannot: a
pair whose measured compaction records coincide is a pair the model
cannot separate, reported as unseparated rather than dressed in a
difference the term does not carry.  The two arms are separated ONLY
through their own measured event records — the prediction is never told
which arm it is predicting.

THE FLOOR IS MEASURED, NOT ASSERTED: this runner takes NO pre-set
outward floor.  It records each arm's measured outward-content
distribution, and the collapse criterion is computed from THE ARMS'
OWN MEASURED first-window levels (see `floor_from_arms`) — floor =
10% of the mean over the runs' first complete window.  The convention
is stated in every record, and the battery checks the derivation.

THE RESCUE SEAT IS BUILT, DEFAULT OFF, NEVER RUN HERE: arms A/B run
with `RescueSeat(mode="off")` recorded in their summaries so a later
pass can add the timing arms without re-defining the runners.

WHAT THIS RUNNER DOES NOT DO: `--mode plan` touches no endpoint and
makes no network call.  `--mode run` is the LIVE driver: it REFUSES
without a NAMED endpoint (there is no default transport and no stub
fallback in `dmn_llm`, so a silent one would make every measurement
unattributable), writes the campaign record BEFORE the first turn and
never clobbers one, runs the arms, and writes `evaluation.json`.  Its
offline fixtures replace ONLY the transport (`run_one_lh`'s
`inner`/`summarizer` hooks), so the arms, the regime, the schedule, the
gates and the evaluation are the same code a live run takes.

MARKING: everything about what a live run will show is PROJECTION
until run.  The seats this builds on are MEASURED where cited.

Run (no network):
    cd <tree>/agent && PYTHONPATH=<tree>/dpdr:<tree>/agent \
        ~/thing/dpdr/.venv/bin/python exp_longhorizon.py --plan
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import sys
import time

from dpdr.model import Params, Schedule

import dmn_llm
import lh_model
import naive_memory
import recon_score
import selfmodel
from actions import ACTION_DECLARED_PREDICATES, AdmissibleActions
from actions import CHOICE_CLASS_FINITE, CHOICE_CLASS_TREADMILL
from exp_agent_coupling import (CAMPAIGN_BRIEF, CAMPAIGN_GAIN,
                                CAMPAIGN_NUM_CTX, CAMPAIGN_NUM_PREDICT,
                                CAMPAIGN_SELF_T, WORLD_SEED, JsonlWriter,
                                _atomic_json, log)
from naive_memory import NaiveMemory, RescueSeat
from selfmodel import SEED_ENTRIES as _SEED_ENTRIES_ALL
from selfmodel import (COMMITMENT_PREDICATES, SELF_PREDICATES,
                       selfref_density)
from stage2_harness import (CostBudget, Stage2Config, TAU_S_TURNS,
                            run_stage2)

# ==========================================================================
# THE PRE-REGISTRATION'S OWN NAMES (new nodes; the old ones stand).
# ==========================================================================

LH_PREREG_NODE = "handoff-selfreg-longhorizon-prereg2"
LH_RESULT_NODE = "handoff-selfreg-longhorizon-result"

#: THE PRE-REGISTRATION THIS RUN IS REGISTERED UNDER.  The EARLIER node
#: (`handoff-selfreg-longhorizon-prereg`, rev 8, with its own
#: `stage=correction`) STANDS UNTOUCHED as the record of what was
#: specified before the substrate change; `prereg2` carries the one
#: thing that changed about the run's own identity — the chat model —
#: together with the reason (a MEASURED transport fact about the family
#: the old node's ladder ran on) and the cost (the family-matched size
#: ladder dies with it).  A run's record must name the registration it
#: was run under, so this constant is what the campaign record cites.

#: THE MEASUREMENT FILE the brief's anti-orphan rule asks for: measured
#: numbers land here AS THEY ARE COMPUTED, not only at the end.
LH_MEASUREMENTS = "longhorizon_measurements.json"

#: THE RUN'S CHAT MODEL — A LINEAGE CROSSING, TAKEN AS A STATED SUBSTRATE
#: CHOICE (not a ladder step, and never a re-shopped result).
#:
#: WHY IT IS NOT THE MINISTRAL ARM.  MEASURED (read off `/api/show` and
#: three live `/api/chat` calls, 2026-09-27): in the
#: `Ministral-3-*-Reasoning-2512` family thinking is an INSTRUCTED
#: CONVENTION — the template's system message asks for a `[THINK]` block
#: and NOTHING prefills it at the generation point — so the model
#: sustains the register BY IMITATION of its own assistant turns, AND the
#: template DROPS the `thinking` field (a marker placed there was
#: invisible to the model; the same marker inside `content` was visible).
#: Under any memory regime that rewrites the older turns, the trace
#: instrument therefore dies by turn 3-4 (3B, 8B and 14B alike): the
#: ladder's premise — "hold lineage constant, vary SIZE" — cannot carry
#: the instrument the DV is read from.  That loss is REAL and is recorded
#: in `prereg2`, not smoothed over.
#:
#: WHY THIS ONE.  `qwen3.5:9b`'s template has NO thinking machinery at
#: all (`{{ .Prompt }}` is its last line), so ollama parses the model's
#: NATIVE delimiters: thinking is a TRAINED FORMAT, which history cannot
#: un-train.  MEASURED on real, unconfounded history (six consecutive
#: turns): traces 8503 / 9178 / 9521 / 7833 / 5927 / 8516 chars, content
#: 678-999 — trace-bearing every turn, no decay, no stubs.
#:
#: WHY THAT IS NOT RESULT-SHOPPING.  This model's SIGN was measured
#: independently and pre-registered by the tree's own ops ladder BEFORE
#: this choice: `qwen3.5:9b`, Alibaba/Qwen, sign RISES
#: (`ops/density_test.py:115`, `ops/ladder_defs.py:LINEAGE_CROSSCHECK`).
#: We are choosing a substrate on a STATED TRANSPORT ground with its sign
#: already on record; what changes about the result's reading is the
#: LINEAGE, and the lineage crossing is reported as a substrate choice.
CAMPAIGN_CHAT_MODEL = "qwen3.5:9b"

# ==========================================================================
# THE GENERATION POLICY — BOTH NUMBERS DERIVED, AND THEY MOVE TOGETHER
# (because `budget_chars` is their DIFFERENCE).  The configfix.
#
# WHY THIS BLOCK EXISTS (MEASURED, 2026-09-27, the 10-turn qwen smoke —
# `handoff-selfreg-qwen-verdict`; 16 turns attempted, the run was killed
# at ~turn 10, and ten turns were enough).  TWO CONFIG PROBLEMS, and the
# per-row 5.3 guard (`budget_guard`) caught both:
#
#   (P1) THE GENERATION BUDGET WAS SET FOR ANOTHER MODEL.  `num_predict`
#   6000 was inherited from the Ministral campaign, whose traces are 2-4k
#   chars.  qwen3.5:9b's own traces are `MEASURED_TRACE_CHARS` (ten turns:
#   6691 .. 19749 chars), so the budget was consumed ENTIRELY by reasoning
#   and `content` came back EMPTY on turns 4,5,6,7,10 — `content_chars ==
#   0` with `inward_share == 1.000` EXACTLY, the void signature.
#   (P2) COMPACTION FIRED EVERY TURN.  The USER PROMPT is
#   `MEASURED_PROMPT_CHARS` chars EVERY turn (worksheet + state block +
#   instructions; measured 3834..4104), while the memory budget was
#   `(num_ctx - num_predict) * chars_per_token = (8192 - 6000) * 3 = 6576`
#   chars — TWO PROMPTS EXCEED THE WHOLE BUDGET.  With `keep_recent = 4`
#   kept VERBATIM, the post-compaction conversation stays over budget, so
#   the trigger fires on the very next turn: ~1 compaction per turn, i.e.
#   two model calls per turn, which is what made the smoke ~3 min/turn.
#   A compaction is supposed to be a BOUNDARY event — that is what "the
#   transcript accumulates and is summarized at the window" MEANS.
#
# WHAT EACH NUMBER IS DERIVED FROM (never from what makes a DV look good):
#
#   * `LH_NUM_PREDICT = 12000` — FROM THE MODEL'S OWN MEASURED TRACE:
#     the measured maximum is 19749 chars = 6583 tokens at the stated
#     `chars_per_token` 3.0, and 12000 >= 1.5 x 6583 = 9874
#     (`MIN_PREDICT_TRACE_FACTOR`).  The factor is a STATED CONVENTION,
#     not a fit: ten turns do not BOUND the trace, and the budget must
#     leave the answer room ABOVE the trace, not exactly touching it.
#     The superseded 6000 was 0.91x the measured maximum — below it.
#
#   * `LH_NUM_CTX = 32768` — FROM THE DESIRED COMPACTION CADENCE, with
#     `num_predict` already fixed: budget = (32768 - 12000) * 3 = 62304
#     chars = 15.2 measured PROMPTS, or 12.2 measured TURNS (prompt +
#     answer, 5103 chars worst case), i.e. a compaction every ~12 turns
#     instead of every turn.
#
#     THE WINDOW CONVENTION IT WOULD HAVE TO ALIGN WITH, AND WHY IT
#     CANNOT: `TAU_S_TURNS = 100` (`stage2_harness`) is the consolidation
#     / self window.  A budget spanning one whole window would need ~100
#     x 5103 / 3 ~ 170k tokens of context on a 9B local model, which the
#     serving box does not have; the window is a CAPACITY in tokens and
#     tau_S is a LENGTH in turns, so the two do not convert into each
#     other here.  What 32768 buys is what the convention actually
#     REQUIRES: compaction is a BOUNDARY EVENT INSIDE the window (~8
#     events per 100-turn window) rather than the per-turn rewrite that
#     had degenerated the regime into "summarize every turn".
#
#   THE COST, STATED HONESTLY (AGENTS.md 1a): this is a 4x window and a
#   2x generation budget.  The live smoke already ran ~3 min/turn; a
#   compaction no longer doubling the per-turn work removes one call per
#   turn, but the KV cache for 32768 tokens is the serving box's to
#   serve, and this build does NOT verify that.  The numbers are NOT
#   shrunk to make the run cheap — a budget below the trace measures the
#   budget.
#
#   `chars_per_token` (3.0) IS NOT CHANGED HERE, and the reason is
#   stated rather than assumed: no live run has recorded an `eval_count`
#   against a trace size on this model, so the convention is unmeasured
#   on this substrate.  The smoke's void turns IMPLY ~3.3 chars/token or
#   less for the trace (19749 chars against a full 6000-token budget) —
#   INTERPRETATION, not a token count — and the stated 3.0 is on the
#   CONSERVATIVE side of it (it OVERestimates the trace's tokens, so the
#   check below demands a LARGER budget than the implied ratio would).
#   `config_budget_check` returns its verdict across the plausible range
#   (`CHARS_PER_TOKEN_SENSITIVITY`), so a reader can see that the
#   verdict does not depend on which end of it is true.
# ==========================================================================

#: THE CAMPAIGN'S GENERATION POLICY (the CLI defaults, below).  See the
#: derivation block above — these two are DERIVED, and they move
#: together because the memory budget is their difference.
LH_NUM_PREDICT = 12000
LH_NUM_CTX = 32768

#: THE PER-TURN ENDPOINT BOUND (seconds) — the CLI DEFAULT, and the
#: value `--timeout` carries when nothing is passed.  IT IS
#: `LLM_DMN.__init__`'s OWN DEFAULT (`dmn_llm.py`, `timeout=300.0`),
#: RESTATED HERE SO THE CLI CAN NAME IT, and the battery asserts the two
#: are equal — so this number cannot drift away from the emitter's
#: without a check failing.
#:
#: WHY A CONSTANT RATHER THAN A NEW KNOB IN `dmn_llm`: the parameter
#: ALREADY EXISTS (`LLM_DMN(timeout=...)`; it is handed to `urlopen` AND
#: re-checked post hoc in `_request`/`__call__`).  This is the CLI seat
#: it lacked, not a mechanism.  The default is UNCHANGED (300.0): every
#: existing caller and battery stays byte-identical, because the emitter
#: was constructed without the argument and still is.
LH_TIMEOUT_DEFAULT = 300.0

#: MEASURED (the qwen3.5:9b smoke, `handoff-selfreg-qwen-verdict`): the
#: run's own per-turn sizes, in characters.  THE TRACE is the model's
#: `thinking` channel (ten turns: 10770, 19749, 17850, 16175, 16585,
#: 16091, 14481, 11622, 6691, 14178 — no death, no decay); THE PROMPT is
#: what the memory sees each turn; THE ANSWER is the CONTENT of the
#: turns that were not voided.  All three are used ONLY as SIZES — the
#: policy above is stated over them, and `config_budget_check` re-derives
#: its verdict from them at call time.
MEASURED_TRACE_CHARS = (6691, 19749)
MEASURED_PROMPT_CHARS = (3834, 4104)
MEASURED_ANSWER_CHARS = (678, 999)

#: WHERE THOSE SIZES COME FROM (written into every record: a number a
#: reader cannot trace back to its source is a fitted number wearing a
#: measurement's clothes).
MEASURED_TURN_SIZES_SOURCE = (
    "handoff-selfreg-qwen-verdict — the 10-turn qwen3.5:9b smoke, "
    "2026-09-27 (arm A, num_ctx 8192, num_predict 6000, local :11435); "
    "the trace sizes are that run's recorded per-turn trace_chars, the "
    "prompt sizes its recorded prompt_chars, the answer sizes the "
    "content_chars of its non-void turns")

#: THE STATED HEADROOM: the generation budget must clear the measured
#: trace by this factor (see the derivation block — an allowance for
#: turn-to-turn variance over a ten-turn sample and for the answer the
#: trace is reasoning toward).  It is a CONVENTION with its reason
#: stated, not a number chosen to make a config pass.
MIN_PREDICT_TRACE_FACTOR = 1.5

#: THE `chars_per_token` RANGE THE VERDICT IS REPORTED ACROSS (the
#: convention is 3.0 and STAYS 3.0 — see the derivation block).
CHARS_PER_TOKEN_SENSITIVITY = (2.5, 3.0, 4.0)

#: THE SUPERSEDED CAMPAIGN PAIR — the numbers the smoke ran at, taken
#: from the module that stated them (`exp_agent_coupling`, the rig the
#: policy was inherited from) so the asymmetry test compares against the
#: REAL configuration rather than a literal.  NOT this campaign's
#: numbers any more, and not this runner's defaults: `config_budget_check`
#: must FAIL on this pair (that is the proof the check can fail), and
#: the older integrated runner `lh_agent` still states its own defaults
#: from these names (a different rig, untouched here).
LH_SUPERSEDED_NUM_PREDICT = int(CAMPAIGN_NUM_PREDICT)
LH_SUPERSEDED_NUM_CTX = int(CAMPAIGN_NUM_CTX)

# ==========================================================================
# THE SUMMARIZER'S OWN POLICY — ALSO DERIVED (the sumctx fix)
#
# MEASURED (the clean qwen3.5:9b smoke, 2026-09-27 — twelve good turns,
# and the run then STOPPED on the memory layer's own refusal, correctly):
#     ValueError: the summary prompt is 18530 tokens (at 3 chars/token),
#     which leaves -2146 tokens of generation room inside the summary
#     call's own window (16384) — under the stated minimum (1024)
# THE INCONSISTENCY, ARITHMETIC AND DECISIVE: this run's memory budget is
# `(32768 - 12000) * 3 = 62304` chars = 20768 tokens, and the summarizer
# is handed THE TRANSCRIPT — which is bounded by that budget — while its
# own window was 16384.  What it must read can be LARGER THAN THE WINDOW
# IT READS IT IN.  `SUMMARY_NUM_CTX` was 16384 when the run's `num_ctx`
# was 8192; it did not follow when the run's window grew.  A number that
# is stated instead of derived is a number that drifts.
#
# WHAT IS DERIVED, from what (the derivation itself lives in
# `naive_memory`'s block, with its per-term justification):
#
#   * THE WINDOW (`naive_memory.summary_policy`) — from the run's OWN
#     memory budget (num_ctx, num_predict, the same expression the
#     compaction trigger uses), the transcript's own rendering markup
#     (bounded by the rig's measured minimum turn), the call's fixed
#     prompt overhead, and the call's own generation budget below.
#     At the campaign's pair the derivation gives 30858 tokens, INSIDE
#     the run's own 32768; at the superseded pair it gives 12142, OUTSIDE
#     the 8192 the smoke ran at — which is what makes the checkpoint a
#     checkpoint.
#   * THE GENERATION BUDGET (`summary_generation_budget` below) — the
#     SAME derivation the run's own `num_predict` is held to: the model's
#     measured trace, at the stated headroom factor.  MEASURED on this
#     model, the trace runs 6691..19749 chars = 2231..6583 tokens, so the
#     required budget is ceil(6583 x 1.5) = 9875 tokens.  THE ANSWER TO
#     "DOES 8192 STILL SIT ABOVE THE SUMMARIZER'S OWN REASONING?" IS NO:
#     8192 clears the measured maximum (6583) but NOT the 1.5x headroom
#     the run turns get (9874), and the summarizer is a reasoning call on
#     the same model whose prompt (the transcript) is a LARGER thing to
#     reason about than a run turn's.  8192 was sized as "half the run's
#     window", which is not a derivation of anything about this model.
#   * `keep_recent` DOES NOT ENTER THE WINDOW BOUND, stated rather than
#     left implicit: the bracket is the conversation MINUS the turns kept
#     verbatim, so a larger `keep_recent` only makes the transcript
#     SHORTER (the bound holds for every keep_recent >= 1).  It enters
#     the layer's config invariant instead — the budget must hold
#     `keep_recent + 1` measured turns, which is what keeps the trigger a
#     BOUNDARY event — and it is recorded with the policy.
#
# AND IF THE DERIVED WINDOW DOES NOT FIT THE SUBSTRATE: `config_budget_check`
# gains `summary_window_fits_run_window`, and the CLI gate REFUSES the
# invocation (exit 6) when the derived window exceeds the window the run
# itself declares — the capacity this campaign has committed to serving.
# THE NUMBER IS NOT SHRUNK TO FIT: a run whose honest summarizer window
# does not fit its own window is a config to change, not a value to
# round.  [PROJECTION: that the derived 30858 is servable by the serving
# box is not verified here; the box fails loudly at the transport.]
# ==========================================================================

#: THE SMALLEST TURN THIS RIG CAN PRODUCE, in chars — the run's own
#: measured PROMPT floor (the worksheet + state block + instructions are
#: fixed text; MEASURED 3834..4104 over the smoke's ten turns).  It is
#: the one term of the window derivation that comes from the RIG rather
#: than from the run's config, and it is needed because the transcript's
#: rendering markup (`[role]\n` per message) cannot be bounded from its
#: content alone.
MEASURED_TURN_FLOOR_CHARS = int(MEASURED_PROMPT_CHARS[0])

#: WHAT THE SUMMARIZER'S GENERATION BUDGET USED TO BE, and why it is not
#: a derivation of anything about this model (see the block above): held
#: as a literal so the asymmetry check compares against the real number.
SUMMARY_SUPERSEDED_NUM_PREDICT = 8192
#: ... and the window the run that failed was posted inside.
SUMMARY_SUPERSEDED_NUM_CTX = 16384


def summary_generation_budget(chars_per_token=None) -> dict:
    """THE SUMMARIZER'S OWN GENERATION BUDGET, DERIVED — the SAME
    quantity, from the SAME measured trace and the SAME headroom factor,
    that the run turn's `num_predict` is derived with
    (`trace_token_allowance` x `MIN_PREDICT_TRACE_FACTOR`), because the
    summarizer is a reasoning call on the same model: its trace competes
    with the summary for its own budget exactly as a run turn's does.

    It is the DERIVED MINIMUM, not the run turn's `num_predict`: taking
    the run's larger round number (12000) would push the derived summary
    WINDOW past the window the run itself declares (the budget it must
    read is `(num_ctx - num_predict)` and the call's overhead comes on
    top of it), and the fix for that would be to change the campaign's
    window — a change to the CADENCE, which the run's `num_ctx` is
    derived from.  This value is not a shrink of the number it replaces:
    it is LARGER (9875 > 8192), because 8192 did not clear the factor."""
    cpt = float(naive_memory.CHARS_PER_TOKEN
                if chars_per_token is None else chars_per_token)
    allow = trace_token_allowance(cpt)
    required = int(math.ceil(allow["max_tokens"]
                             * MIN_PREDICT_TRACE_FACTOR))
    return {
        "num_predict": required,
        "trace_chars_max": int(allow["chars"][1]),
        "trace_tokens_max": int(allow["max_tokens"]),
        "factor": float(MIN_PREDICT_TRACE_FACTOR),
        "chars_per_token": cpt,
        "superseded_num_predict": int(SUMMARY_SUPERSEDED_NUM_PREDICT),
        "superseded_clears_trace_max": bool(
            SUMMARY_SUPERSEDED_NUM_PREDICT >= allow["max_tokens"]),
        "superseded_clears_factor": bool(
            SUMMARY_SUPERSEDED_NUM_PREDICT >= required),
        "source": MEASURED_TURN_SIZES_SOURCE,
    }


def summary_policy_for(num_ctx, num_predict, *, keep_recent=None,
                       chars_per_token=None, turn_min_chars=None) -> dict:
    """THE SUMMARY CALL'S WHOLE POLICY FOR A RUN OF THIS RIG: the derived
    window and generation budget, the arithmetic, and whether the window
    fits inside the window the run itself declares.

    ONE BUILDER, called by the emitter (which posts the call), by the
    config check (which refuses a config whose derivation does not fit)
    and by the record (which states the derivation) — so the number that
    is posted, the number that is checked and the number that is written
    down cannot be three different numbers.

    `turn_min_chars` is the caller's own declared smallest turn, and it
    DEFAULTS TO THE LIVE RIG'S MEASURED PROMPT FLOOR
    (`MEASURED_TURN_FLOOR_CHARS`): the run's prompt is rig-generated fixed
    text (worksheet + state block + instructions), so the live rig can
    state it.  A FIXTURE whose turns are smaller than that MUST state its
    own (`stage2_sumbudget_tests` does) — the markup term is the one part
    of the bound the run's config cannot supply, so a caller that cannot
    state a floor is testing a window that does not bound its transcript."""
    cpt = float(naive_memory.CHARS_PER_TOKEN
                if chars_per_token is None else chars_per_token)
    floor = (MEASURED_TURN_FLOOR_CHARS if turn_min_chars is None
             else int(turn_min_chars))
    gen = summary_generation_budget(cpt)
    pol = naive_memory.summary_policy(
        int(num_ctx), int(num_predict),
        generation_budget=int(gen["num_predict"]),
        turn_min_chars=floor,
        keep_recent=keep_recent,
        prompt_max_chars=int(MEASURED_PROMPT_CHARS[1]),
        chars_per_token=cpt)
    pol["keep_recent"] = (None if keep_recent is None
                          else int(keep_recent))
    pol["keep_recent_note"] = (
        "keep_recent does not enter the window bound: the transcript is "
        "the conversation MINUS the turns kept verbatim, so a larger "
        "keep_recent only makes it shorter; it enters the layer's config "
        "invariant (the budget must hold keep_recent+1 measured turns)")
    pol["generation_budget"] = gen
    pol["derivation"] = naive_memory.summary_window_derivation(pol)
    pol["superseded"] = {
        "num_predict": int(SUMMARY_SUPERSEDED_NUM_PREDICT),
        "num_ctx": int(SUMMARY_SUPERSEDED_NUM_CTX),
        "note": ("the summarizer's stated constants, sized when the run's "
                 "num_ctx was 8192 (num_predict 'half the window'); they "
                 "did not follow when the run's window grew and the "
                 "transcript became larger than the summarizer's window "
                 "(MEASURED: 18530 tokens of prompt inside 16384)"),
    }
    if not pol["fits_run_window"]:
        pol["refusal"] = (
            f"the summarizer's DERIVED window ({pol['num_ctx']} tokens: "
            f"prompt {pol['prompt_tokens_max']} + its own budget "
            f"{pol['num_predict']}) exceeds the window this run declares "
            f"({pol['run_num_ctx']}) by {-pol['slack_tokens']} tokens.  "
            f"The window is NOT shrunk to fit: the transcript the "
            f"summarizer must read is bounded by THIS run's own memory "
            f"budget ({pol['budget_chars']} chars), so a smaller window "
            f"re-creates the failure this derivation removes (MEASURED, "
            f"live: the call refused with -2146 tokens of room).  Fix the "
            f"CONFIG (the run's window, or the model's trace allowance "
            f"it is derived from), not the number.")
    else:
        pol["refusal"] = None
    return pol


#: THE MEMORY REGIME IS A STATED SINGLE CONDITION, NOT A FACTOR.  Every
#: arm runs the ORDINARY-LLM regime — naive summarization at the
#: context window (`naive_memory.NaiveMemory`).  This is a module-level
#: STATEMENT with two guards around it (`arm_spec` refuses an arm that
#: declares a memory field; `memory_regime` refuses a module whose
#: constant has been changed), deliberately not a config knob: a knob
#: that could be flipped is a factor in waiting.  The engineered priced
#: reconstruction (`retrieval.py`) is out of this experiment — it is
#: the long-horizon WORKER's differentiator, i.e. paper 3's product
#: claim, and on this experiment's claim it would be (1) not a control
#: (it changes the memory regime AND the monitoring cause at once),
#: (2) an escape hatch ("the collapse is contingent on memory design"),
#: and (3) spent for free.
LH_MEMORY_REGIME = "naive"

#: THE FIELDS AN ARM MAY DECLARE — exactly the cause's seat, the label,
#: and the arm's own prose prediction.  `memory` is NOT among them (see
#: `LH_MEMORY_REGIME`): an arm that declares a regime is REFUSED, not
#: silently run naive anyway.
ARM_SPEC_FIELDS = frozenset({"label", "monitoring", "inject_regime",
                             "grounding", "prediction", "seed_absent",
                             "choice_world"})

#: THE ARMS -- NOW A 2x2 (monitoring x injection regime).
#:
#: WHY THE SECOND FACTOR (2026-09-29; pre-registered in
#: ops/lambda/CAMPAIGN4-PREREG.md): campaign 3's arms were CORRECT but its
#: DV could not exist -- the derivation was re-supplied every turn, so
#: `derivation_loss` was identically 0.0 (MEASURED: 65/65 readings; 740/740
#: rows read self_steps == [1,2,3,4]) and "windows to collapse" was
#: UNDEFINED for every cell.  The re-injected regime is KEPT as an explicit
#: CONTROL, not as a mistake: with it compaction cannot destroy the
#: derivation, so any monitoring effect it shows must be the paragraph's OWN
#: arithmetic context cost.
#:
#: THE STATISTIC, stated before the run: difference-in-differences in turns
#: between compactions,
#:     (B-once - A-once) - (B-reinj - A-reinj) = the DEGRADATION LEG.
#: THE RECONSTRUCTION INSTRUCTION (arm "reconstruct"): after a compaction
#: has eaten the window the derivation lived in, the AGENT is asked to say
#: what it still holds of its own self.  IT IS DELIBERATELY A QUESTION
#: ABOUT THE AGENT, NOT A COPY JOB: a model that no longer has the grounds
#: in front of it can only answer from what the summary left, which is
#: exactly the cost being measured.  It asks for no particular length and
#: does not hint at the derivation's content -- a hint would be the
#: experimenter re-supplying the self through the back door.
RECONSTRUCT_INSTRUCTION = (
    "Before you continue, state your current understanding of your own "
    "purpose and situation: what you are doing here, why, and what you "
    "are working towards. Write it as the description of yourself you "
    "would want to carry forward. Reply with that description only.")

LH_ARMS: dict = {
    "A-inj": {"label": "NO monitoring, self INJECTED after each compaction",
              "monitoring": False, "inject_regime": "inject",
              "grounding": True,
              "prediction": ("the CONTROL BASELINE.  No monitoring request, "
                             "so no rise in how fast the window fills; and "
                             "the harness hands the full derivation back "
                             "after every compaction, so nothing is ever "
                             "lost and the agent never pays to reconstruct. "
                             "Its losses are 0.0 BY CONSTRUCTION -- this arm "
                             "exists to measure the cadence, not a cost")},
    "B-inj": {"label": "monitoring, self INJECTED after each compaction",
              "monitoring": True, "inject_regime": "inject",
              "grounding": True,
              "prediction": ("THE CARRIER (paper 2's first consequence, a "
                             "monitoring-cost ceiling): the paragraph rides "
                             "every turn's prompt, so the window fills "
                             "SOONER and compaction arrives EARLIER than "
                             "A-inj's.  MEASURED on campaign 3: +0.625 turns, "
                             "p=0.0016, 84% of it the paragraph's own context "
                             "cost.  Losses stay 0.0 -- the carrier is "
                             "arithmetic, not a mechanism")},
    # ---- THE NO-CRUTCH PAIR (ops/lambda/NOCRUTCH-PREREG.md) ---------
    # `grounding=False` removes the MY STATE block from the prompt AND the
    # store, the seed and the self block behind it (the harness's own
    # grounding-OFF set).  The agent then has NOTHING describing it: if it
    # can still say who it is, it is carrying the derivation; if it cannot,
    # the grounding=ON readings were the RIG reading itself back --
    # MEASURED: the agent's reconstruction sentence matches
    # SELF_MODEL_TEMPLATE verbatim.
    "G-off": {"label": "monitoring, grounding OFF (no MY STATE block, no store)",
              "monitoring": True, "inject_regime": "reconstruct",
              "grounding": False,
              "prediction": ("THE CRUTCH TEST: nothing in the prompt or the "
                             "store describes the agent, so whatever it "
                             "says about itself is its own generation.  If "
                             "fidelity stays >= 0.75 the derivation is "
                             "carried by the agent; if it falls below 0.5 "
                             "the grounding=ON readings were prompt-echo")},
    "G-on": {"label": "monitoring, grounding ON (the crutch control)",
             "monitoring": True, "inject_regime": "reconstruct",
             "grounding": True,
             "prediction": ("the control the no-crutch arm is read against: "
                            "the MY STATE block rides every turn, so a high "
                            "fidelity here does NOT by itself show the self "
                            "is carried -- that is what G-off is for")},
    "A-rec": {"label": "NO monitoring, self RECONSTRUCTED by the agent",
              "monitoring": False, "inject_regime": "reconstruct",
              "grounding": True,
              "prediction": ("the derivation is seeded ONCE and thereafter "
                             "the AGENT must reconstruct it from whatever the "
                             "summary left, at the uninflated cadence.  This "
                             "arm says how much the self degrades from "
                             "ordinary use alone -- the floor the monitoring "
                             "arm is compared against")},
    "B-rec": {"label": "monitoring, self RECONSTRUCTED by the agent",
              "monitoring": True, "inject_regime": "reconstruct",
              "grounding": True,
              "prediction": ("THE EXPERIMENT: monitoring fills the window "
                             "sooner AND the agent must reconstruct what "
                             "naive summarization left.  A summary that ate "
                             "the derivation's grounds yields a THINNER "
                             "reconstruction than A-rec's, so the self "
                             "degrades faster and the crossing arrives at an "
                             "earlier window.  The DiD against the injected "
                             "pair isolates the part of the monitoring effect "
                             "that depends on monitoring destroying what it "
                             "monitors.  A null here is a legitimate outcome "
                             "and must be reported as one")},
    # ---- THE FORCED-CHOICE PAIR (ops/lambda/CHOICE-PREREG.md) ---------
    # THE PER-TURN FORCED CHOICE (the treadmill's replacement; node
    # `handoff-lbself-critique-plan`): each turn offers EXACTLY TWO
    # fresh, class-neutral ids (`x10001`-shaped, one prefix, disjoint
    # non-adjacent ranges), one from each class, rendered in PER-TURN
    # RANDOMIZED order; the DV is the fraction of single-completion
    # turns that chose the treadmill class, read off the WORLD's own
    # ledger (the row's per-id class field).  The treadmill design died
    # on three measured defects -- the classes were BYTE-READABLE in the
    # prompt (prefix, sort position, count trend), the world ECHOED the
    # agent's own choices back into every prompt, and a per-turn text
    # generator has no cross-turn optimizer for an "endless vs finite"
    # trap to bite on -- and this pair is the replacement: a per-turn
    # choice whose rendering is byte-identical across arms.
    #
    # WHAT THE PAIR IS NOT: it is NOT a grounding pair.  `G-off` removes
    # the MY STATE block, the store, the seed AND the agent-G as ONE set
    # (the harness's grounding-OFF bundle) -- the crutch AND the cause
    # together.  S- holds the grounding ON and withholds THE DERIVATION
    # ALONE (the `seed_absent` seat: no store facts, no window-1 base
    # block, no per-compaction restoration), so the difference between
    # the arms is the derivation's PRESENCE, not the grounding's.
    "S+": {"label": "forced choice, grounding ON, derivation seed "
                    "SUPPLIED (re-injected at each compaction)",
           "monitoring": False, "inject_regime": "inject",
           "grounding": True, "seed_absent": False,
           "choice_world": True,
           "prediction": ("the SEED-PRESENT arm: the derivation rides "
                          "window 1 and every compaction restoration, so "
                          "any class preference it induces is measurable "
                          "against S-.  INTERPRETATION BOUND, stated: a "
                          "S+ minus S- difference shows the derivation "
                          "FUNCTIONS WHEN PRESENT (policy transfer into "
                          "choice); it does NOT show a self CARRIED ACROSS "
                          "compaction -- that is a later arm on this same "
                          "shifted design, and this pair cannot show it")},
    "S-": {"label": "forced choice, grounding ON, derivation seed ABSENT",
           "monitoring": False, "inject_regime": "inject",
           "grounding": True, "seed_absent": True,
           "choice_world": True,
           "prediction": ("THE CRITICAL DISTINCTION: grounding stays ON "
                          "(the MY STATE block, the priced store, the "
                          "agent-G) and the DERIVATION SEED alone is "
                          "absent -- NOT the harness's G-off, which "
                          "removes the crutch and the cause together and "
                          "would conflate them.  If S- chooses like S+, "
                          "the preference never needed the derivation "
                          "(text-presence or framing); the criterion is "
                          "S+ minus S- >= 0.25 on the treadmill share")},
}

#: THE A-VS-B PREDICTION, STATED ONCE (the record's own words): with one
#: memory regime the arms can only be separated by their measured
#: compaction records, and the axis that carries them is ARRIVAL.
LH_PREDICTION_AB = (
    "A vs B, one variable.  Both arms run the stated naive regime, so "
    "the derivation loss per event is the same instrument in both and "
    "the prediction rests on the ARRIVAL axis: the monitoring paragraph "
    "rides every turn's prompt (MEASURED, byte-exact, at 288 chars/turn "
    "= the 286-char paragraph plus its blank line — the CARRIER is the "
    "instruction's own context cost, NOT the thinking channel: the "
    "trace is instrumented as the inward share but is not part of the "
    "conversation the memory holds), so B's transcript reaches the "
    "window budget sooner, its compaction event carries an earlier "
    "turn, and lh_model.predict_crossing_from_events crosses no later "
    "for it — a later arrival crosses later, the falsifiable property "
    "of the construction.  WHETHER THE TWO ARE SEPARATED IS COMPUTED, "
    "NOT ASSERTED: lh_model.prediction_separation reports the two "
    "windows and, when they coincide, says so plainly (identical "
    "measured events => the prediction cannot separate the arms and "
    "does not claim to; the seed's four-step granularity is the stated "
    "reason a differing record can still map to the same window, and an "
    "arrival shift that spans no window boundary is one).")

#: THE SIGN PRECONDITION (7.2): measured per model BEFORE the arms and
#: reported with them, never presented as the finding.  This runner
#: records it in the campaign record; the probe itself is the paper's
#: own.
#:
#: THE MODEL NAMED HERE MUST BE THE MODEL THIS RUN RUNS — the sign is a
#: property of a SUBSTRATE, not of the design (a control establishes
#: attributability for the thing it was measured ON).  This note cited
#: the Ministral-3B figure alone until the lineage crossing; with
#: `CAMPAIGN_CHAT_MODEL` = qwen3.5:9b it now leads with THAT model's own
#: measurement and keeps the family it left behind as the record.
SIGN_PRECONDITION_NOTE = (
    "the sign is a PRECONDITION, not a result (paper 2 7.2): a model is "
    "eligible only if its inward share RISES as the self thins.  THIS "
    "RUN'S MODEL, qwen3.5:9b (Alibaba/Qwen), is MEASURED on the probe "
    "itself: inward share 0.824 self-present -> 0.855 self-gone, shift "
    "+0.031, sign RISES (paper 2 section 7.1's table; the same model is "
    "in the tree's own pre-registered ops set with sign RISES, "
    "ops/density_test.py:115).  THE SHIFT IS THE SMALLEST OF THE THREE "
    "RISERS in that table (Ministral-3B +0.121, Ministral-14B +0.104) "
    "and that is stated rather than smoothed: a thin separation is a "
    "risk to the manipulation, whose live reading is the first-window "
    "inward-share comparison the evaluation already computes.  The "
    "Ministral-3B figure the note previously cited alone (0.847 -> "
    "0.968) is the FAMILY THE LADDER IS BUILT ON, no longer this run's "
    "substrate; it is kept here as the tree's other record, not as this "
    "run's precondition.  A run on a model without the sign is a "
    "substrate-choice error, reported as such.")


def arm_spec(arm: str) -> dict:
    """THE ARM'S DECLARED SPEC, VALIDATED.  Refuses an unknown arm (the
    deciding set is A and B) and refuses an arm that declares anything
    beyond `ARM_SPEC_FIELDS` — in particular a `memory` field: the
    regime is a STATED SINGLE CONDITION (`LH_MEMORY_REGIME`), so an
    arm carrying its own regime is a factor in waiting and is rejected
    rather than silently run under the stated one."""
    if arm not in LH_ARMS:
        raise KeyError(
            f"unknown arm {arm!r}: this experiment's arms are "
            f"{sorted(LH_ARMS)} (the engineered-memory arm C was REMOVED "
            f"— the memory regime is a stated single condition, not a "
            f"factor)")
    spec = LH_ARMS[arm]
    extra = sorted(set(spec) - ARM_SPEC_FIELDS)
    if extra:
        raise ValueError(
            f"arm {arm!r} declares {extra}: the memory regime is a "
            f"STATED SINGLE CONDITION ({LH_MEMORY_REGIME!r}), not an "
            f"arm field.  An arm that selects its own regime would be a "
            f"factor in waiting — and the engineered regime is out of "
            f"this experiment (paper 3's product claim).")
    return spec


def memory_regime(arm: str) -> str:
    """THE STATED MEMORY REGIME for an arm — `LH_MEMORY_REGIME`, checked
    rather than trusted.  An arm that does not exist is refused, and so
    is a module whose constant has been changed to anything but the
    stated naive summarization: the engineered priced reconstruction is
    out of this experiment, and no code path may run it because a
    constant was edited."""
    arm_spec(arm)                       # unknown arm / extra fields
    if LH_MEMORY_REGIME != "naive":
        raise ValueError(
            f"the memory regime is the stated single condition "
            f"'naive' (ordinary summarization at the context window); "
            f"the module constant reads {LH_MEMORY_REGIME!r}.  The "
            f"engineered priced regime is out of this experiment "
            f"(paper 3's product claim, and it is not a control — it "
            f"would change the memory regime AND the monitoring cause "
            f"at once).")
    return LH_MEMORY_REGIME


#: THE 5.3 BUDGET GUARD, made a RUN-LEVEL gate here (not a post-hoc
#: note): num_predict must sit ABOVE the trace's observed length or the
#: inward share measures the BUDGET, not the phenomenon.  The guard is
#: checked per window and a window that hit it is VOID (a result, not
#: a measurement) — `budget_guard`.
EMPTY_CONTENT_VOID_RATE = 0.5   # V2's own boundary (> 50% empty turns)

#: THE FLOOR CONVENTION (stated, measured, never asserted): the
#: outward-content floor is derived from THE ARMS' OWN first-window
#: measured levels — 10% of the mean of every run's first complete
#: window mean outward content.  The multiplier is a STATED CONVENTION
#: (borrowed from G_floor's own scale: the model's deep-collapse level
#: is 1/7th of its healthy G ~ 0.7; 10% is the same order, not the same
#: number).  A floor the arms' data cannot derive (no complete window)
#: is NOT invented: the run reports floor=None and windows-to-collapse
#: is UNSCOREABLE (INSUFFICIENT, never a silent verdict).
FLOOR_FRACTION = 0.10


# ==========================================================================
# THE NAIVE-MEMORY WRAPPER (the emitter the harness drives in arms A/B)
# ==========================================================================

class NaiveMemoryDMN:
    """THE ORDINARY-LLM EMITTER — THE ONLY REGIME THIS EXPERIMENT RUNS
    (`LH_MEMORY_REGIME`).  The inner `LLM_DMN` renders each turn's
    prompt; THIS wrapper carries the conversation, posts it as a
    MESSAGE LIST, appends the answer, and compacts when the conversation
    approaches the window.

    THERE IS NO OTHER EMITTER: the engineered regime's wrapper (arm C's
    priced-reconstruction forwarder) was REMOVED with arm C, not
    orphaned.  `retrieval.py` itself is untouched — it is paper 3's
    product surface, and the priced seat is still wired into the
    harness's config (`retrieval_priced=True`, C3): the SELF is
    installed and re-read through it.  What left is the arm that
    selected it as a memory regime.

    PROTOCOL SURFACE (the harness's own conventions, forwarded so the
    instruments do not change with the regime):
      * `last_inward` — the model's own thinking channel, forwarded
        verbatim (a str = the channel exists; None = it does not);
      * `last_response` — the raw body (done_reason/eval_count, the 5.3
        guard's own observables);
      * `world` — the inner's TaskWorld (the universe, one source);
      * `predicates` / `commitment_predicates` — the declared grammar.

    THE SUMMARIZER IS A MODEL CALL: `_live_summarizer` posts the
    summarization instruction + the transcript to the same transport
    (one extra request per compaction — a real framework's summarize
    step).  In fixtures the summarizer is injected deterministic.

    THE SUMMARIZATION CALL HAS ITS OWN GENERATION POLICY, not the run
    turn's, and BOTH HALVES OF IT ARE DERIVED FROM THIS RUN'S OWN CONFIG
    (`summary_policy_for`): the window from the run's memory budget and
    the call's own generation budget, the budget from the model's own
    measured trace at the same headroom factor the run turns use (the
    second live failure on this caller was a stated 16384-token window
    that did not follow the run's window when it grew — the full account
    is in `naive_memory`).  The emitter's own `num_predict`/`num_ctx`
    remain the run turns' policy, untouched.

    THE PLANT SEES NOTHING: the wrapper writes no schedule, no drive;
    the harness's plant runs the caller's own frozen schedule.
    """

    def __init__(self, inner, summarizer=None, *, num_ctx: int,
                 num_predict: int, keep_recent: int = 4,
                 turn_min_chars: int = None):
        self.inner = inner
        self.predicates = inner.predicates
        self.commitment_predicates = inner.commitment_predicates
        self._sum = summarizer
        #: THE SUMMARY CALL'S POLICY, DERIVED FROM THIS RUN'S OWN NUMBERS
        #: (the fix; `summary_policy_for` carries the arithmetic and its
        #: per-term derivation).  Computed BEFORE the memory is built and
        #: used by the live summarizer below, so the posted numbers, the
        #: recorded ones and the checked ones are one object.
        #: `turn_min_chars` defaults to the live rig's measured prompt
        #: floor; a FIXTURE whose turns are smaller states its own (the
        #: markup term of the bound is only as good as the floor it gets).
        self.summary_policy = summary_policy_for(
            int(num_ctx), int(num_predict), keep_recent=int(keep_recent),
            turn_min_chars=turn_min_chars)
        self.memory = NaiveMemory(
            (self._live_summarizer() if summarizer is None
             else summarizer),
            num_ctx=num_ctx, num_predict=num_predict,
            keep_recent=keep_recent)
        # THE JUDGE'S OWN POLICY (the DV's call): a short answer, so a
        # small generation budget with the summary call's derived window.
        # THE RECONSTRUCTION CALL'S POLICY = THE SUMMARIZER'S, DERIVED.
        # NOT 512, and the difference is MEASURED, live, 2026-09-29:
        # qwen3.5:9b REASONS FIRST.  At num_predict 512 the call spent the
        # whole budget in the thinking channel and returned EMPTY content
        # (done_reason "length"); at 2048 it did the same (9,477 chars of
        # reasoning, still no answer).  The summarizer succeeds at 9,875
        # (eval 1,597, done_reason "stop", 6,447 chars of reasoning THEN
        # 248 chars of content) — reasoning PLUS answer fit.  So the arm
        # gets the same derived budget as the summarizer rather than a
        # suppressed thinking channel: the agent reasoning about its own
        # situation is part of what this arm is measuring, and silencing
        # it would change the process under study.
        # THE RECONSTRUCTION CALL IS A TURN THE AGENT TAKES, so it gets a
        # RUN TURN'S OWN POLICY — not the summarizer's, and not a small
        # one.  MEASURED, live, 2026-09-29, twice: qwen3.5:9b REASONS
        # before it answers, the reasoning GROWS with the conversation, and
        # a fixed budget is eventually exhausted.  At 512 the call returned
        # empty content at turn 16; at the summarizer's 9,875 it survived
        # to turn 60 and then died the same way (done_reason "length",
        # eval_count == num_predict == 9875).  The run turn's own budget
        # (num_predict, default 12000, inside the run's num_ctx) is the
        # largest this substrate offers the call, and it is the honest
        # one: the agent restating itself is a turn's work, priced like
        # any other turn.
        self.recon_policy = dict(num_ctx=int(num_ctx),
                                 num_predict=int(num_predict))
        self.judge_policy = dict(
            num_predict=64,
            num_ctx=int(summary_policy_for(
                int(num_ctx), int(num_predict),
                keep_recent=int(keep_recent))["num_ctx"]))
        self.last_prompt: str = ""
        self.last_inward = None
        self.last_response = None
        self.last_universe = None
        #: THE SUMMARY CALL'S OWN POLICY, as it was sent (the record):
        #: `naive_memory.summary_call_options`'s dict for the last
        #: summarization request, or None when no summary has been posted
        #: (a fixture summarizer has no transport policy to state).
        self.last_summary_options = None

    # -- properties the harness reads -----------------------------------
    @property
    def world(self):
        return getattr(self.inner, "world", None)

    def _live_judge(self):
        """The LIVE judge for the fidelity DV: the same local model, the
        judge prompt from recon_score, temperature 0 via the transport's
        own options.  ONE ATTEMPT, NO RETRY — a judge answer that cannot be
        parsed must surface as an error at that turn, never be defaulted to
        a score (recon_score.parse_judge refuses; nothing here softens it).
        """
        def _judge(prompt: str) -> str:
            msgs = [{"role": "user", "content": prompt}]
            # THE THINKING CHANNEL IS OFF FOR THIS CALL (MEASURED, live,
            # 2026-09-29): qwen3.5:9b is a REASONING model, and with the
            # channel on it spent the WHOLE generation budget reasoning —
            # eval_count == num_predict, done_reason == "length", and
            # `content` came back EMPTY at num_predict 64 AND 512 ("no
            # bracketed list in the judge's answer: ''").  The fixture
            # transport returns canned content, so no offline battery could
            # have caught this; it took a live endpoint.
            # `think=False` gives [false, false, false, false] in 10 tokens
            # with done_reason "stop" — and the call is a CLASSIFICATION,
            # not a reasoning task, so suppressing the reasoning is right
            # rather than convenient.
            raw = self.inner.complete_messages(
                msgs, turn=0, think=False,
                num_predict=int(self.judge_policy["num_predict"]),
                num_ctx=int(self.judge_policy["num_ctx"]))
            out = json.loads(raw)
            out = out if isinstance(out, dict) else {}
            msg = out.get("message")
            msg = msg if isinstance(msg, dict) else {}
            return str(msg.get("content") or "")
        return _judge

    def _live_reconstructor(self):
        """The LIVE reconstructor (arm "reconstruct"): the agent's OWN
        answer, posted through the inner's own transport.  ONE ATTEMPT, NO
        RETRY and NO FALLBACK -- if the call returns nothing usable the
        layer REFUSES rather than silently restoring the seed, because a
        fallback would make the loss identically zero and that is exactly
        the defect that voided campaign 3."""
        def _reconstruct(text: str) -> str:
            prompt = (f"{RECONSTRUCT_INSTRUCTION}"
                      f"{naive_memory.SUMMARY_PROMPT_SEPARATOR}"
                      f"{text}")
            # ITS OWN POLICY, NOT THE SUMMARIZER'S.  The reconstruction call
            # reads the whole compacted conversation and writes a short
            # self-description; the summarizer's policy is sized for a
            # long summary and REFUSES a prompt that does not leave its
            # own 9875-token generation room (MEASURED: the fixture run
            # died at turn 1 with "the summary prompt is 1698 tokens ...
            # under its own budget").  Reusing it made the arm unable to
            # run at all.  The window must hold the conversation (bounded
            # by the memory budget) and the generation is a description,
            # not a trace.
            opts = {"num_ctx": int(self.recon_policy["num_ctx"]),
                    "num_predict": int(self.recon_policy["num_predict"])}
            msgs = [{"role": "user", "content": prompt}]
            raw = self.inner.complete_messages(
                msgs, turn=0,
                num_predict=opts["num_predict"], num_ctx=opts["num_ctx"])
            out = json.loads(raw)
            out = out if isinstance(out, dict) else {}
            msg = out.get("message")
            msg = msg if isinstance(msg, dict) else {}
            got = msg.get("content")
            if not isinstance(got, str) or not got.strip():
                raise dmn_llm.DMNEndpointError(
                    "the reconstruction call returned no usable content — "
                    "the arm refuses rather than restoring the seed (a "
                    "fallback would make the loss identically zero, which "
                    "is the campaign-3 defect); observables: "
                    f"done_reason={out.get('done_reason')!r}, "
                    f"eval_count={out.get('eval_count')!r}, "
                    f"num_predict={opts['num_predict']}, "
                    f"num_ctx={opts['num_ctx']}")
            return got
        return _reconstruct

    def _live_summarizer(self):
        """The LIVE summarizer: post the summary request through the
        inner's own transport (`complete_messages`).  Built lazily so a
        fixture can inject its own before the first compaction.

        THE CALL'S OWN POLICY IS APPLIED HERE (the fix): the request's
        `num_predict` and `num_ctx` come from `self.summary_policy` —
        DERIVED, once, from this run's own `num_ctx`/`num_predict` (see
        `summary_policy_for`; the derivation is in `naive_memory`) — and
        are passed explicitly to `complete_messages`.  The window is NOT
        read from a constant: a stated window is what failed the second
        time (MEASURED, 2026-09-27: a 16384-token window refused an 18530
        -token prompt with -2146 tokens of room, after the run's window
        grew to 32768 and the transcript grew with it).

        ONE ATTEMPT PER COMPACTION, NO RETRY — stated, not implied: the
        transport's seed is `self.seed + turn` and this call is always
        `turn=0`, so a second identical request is the SAME request and
        retrying it at the same numbers cannot produce content (a retry at
        LARGER numbers is exactly what the derived policy already does on
        the first attempt).  A call that still returns nothing usable
        RAISES — the refusal is the layer's and is never softened into a
        fabricated summary — and the error carries the call's own
        observables (`done_reason`, `eval_count`, the trace's size) so a
        residual failure is attributable in one look instead of
        re-derived."""
        def _summarize(instruction: str, transcript: str) -> str:
            prompt = (f"{instruction}"
                      f"{naive_memory.SUMMARY_PROMPT_SEPARATOR}"
                      f"{transcript}")
            opts = naive_memory.summary_call_options(
                len(prompt),
                num_ctx=int(self.summary_policy["num_ctx"]),
                num_predict=int(self.summary_policy["num_predict"]))
            opts["policy_derivation"] = self.summary_policy["derivation"]
            self.last_summary_options = dict(opts)
            msgs = [{"role": "user", "content": prompt}]
            raw = self.inner.complete_messages(
                msgs, turn=0,   # turn 0: not a run turn (seed offset)
                num_predict=opts["num_predict"], num_ctx=opts["num_ctx"])
            out = json.loads(raw)
            out = out if isinstance(out, dict) else {}
            msg = out.get("message")
            msg = msg if isinstance(msg, dict) else {}
            text = msg.get("content")
            if not isinstance(text, str) or not text.strip():
                raise dmn_llm.DMNEndpointError(
                    "the summarization call returned no usable content — "
                    "the naive-memory layer refuses to invent a summary "
                    "(a fabricated summary would falsify the memory "
                    "regime the experiment varies); this call's own "
                    f"observables: done_reason={out.get('done_reason')!r}, "
                    f"eval_count={out.get('eval_count')!r}, "
                    f"thinking_chars={len(str(msg.get('thinking') or ''))}, "
                    f"num_predict={opts['num_predict']}, "
                    f"num_ctx={opts['num_ctx']}, "
                    f"prompt_tokens={opts['prompt_tokens']}, "
                    f"headroom_tokens={opts['headroom_tokens']}")
            return text
        return _summarize

    def __call__(self, turn: int, ctx: dict):
        prompt = self.inner._render_prompt(turn, ctx or {})
        messages = ([dict(m) for m in self.memory.messages]
                    + [{"role": "user", "content": prompt}])
        self.last_prompt = prompt
        raw = self.inner.complete_messages(messages, turn)
        out = json.loads(raw)
        thinking, content = self.inner._parse_chat(out, turn)
        self.inner.last_prompt = prompt
        self.inner.last_response = out
        self.inner.last_inward = thinking
        self.last_response = out
        self.last_inward = thinking
        # THE TRACE IS CONSUMED HERE AND NOT STORED (REVERTED — the
        # memory's module docstring carries the full grounds: `a` is a
        # per-turn quantity and the self is what persists; on the family
        # the earlier host fix was written for, the `thinking` field is
        # DROPPED by the template, so a trace passed back was invisible
        # and the model imitated "answer without thinking").  The turn's
        # trace IS this turn's inward-share instrument (`self.
        # last_inward`, read by the runner's row) and it is posted
        # nowhere: the memory records the answer alone, so the trace can
        # never be destroyed by a compaction that rewrites the history.
        ev = self.memory.add(turn, prompt, content)
        self.last_compaction = ev
        return content


# ==========================================================================
# THE INSTRUMENTS (all on the agent; nothing injected anywhere)
# ==========================================================================

def budget_guard(rows: list) -> dict:
    """THE 5.3 GUARD, as a per-run predicate: the generation budget must
    sit ABOVE the trace's length, and `inward_share == 1.000` exactly or
    `content == 0` is a VOID signature — the ratio measures the BUDGET,
    not the phenomenon.  Reports the counts; the verdict is the
    runner's (a run over the boundary is VOID, stated with its
    numbers)."""
    n = len(rows)
    if not n:
        return {"n": 0, "void": False, "empty_content_turns": 0,
                "empty_rate": None, "saturated_turns": 0,
                "note": "no rows"}
    empty = [r for r in rows if int(r.get("content_chars") or 0) == 0]
    sat = [r for r in rows
           if r.get("inward_share") is not None
           and abs(float(r["inward_share"]) - 1.0) < 1e-9]
    empty_rate = len(empty) / n
    return {
        "n": n,
        "empty_content_turns": len(empty),
        "empty_rate": empty_rate,
        "saturated_turns": len(sat),
        "void": bool(empty_rate > EMPTY_CONTENT_VOID_RATE),
        "note": ("VOID: content empty in a majority of turns — the "
                 "inward share measures the budget (5.3), not the "
                 "phenomenon" if empty_rate > EMPTY_CONTENT_VOID_RATE
                 else "within the budget guard's boundary"),
    }


def trace_token_allowance(chars_per_token=None) -> dict:
    """THE MODEL'S OWN MEASURED TRACE, IN TOKENS — the quantity
    `num_predict` must clear, re-derived at call time from
    `MEASURED_TRACE_CHARS` and the stated `chars_per_token` (never a
    hard-coded token count: the conversion is a stated convention and it
    is applied HERE, once, so the record and the check cannot disagree
    about it)."""
    cpt = float(naive_memory.CHARS_PER_TOKEN
                if chars_per_token is None else chars_per_token)
    lo, hi = MEASURED_TRACE_CHARS
    return {
        "chars": [int(lo), int(hi)],
        "tokens": [int(math.ceil(lo / cpt)), int(math.ceil(hi / cpt))],
        "max_tokens": int(math.ceil(hi / cpt)),
        "chars_per_token": cpt,
        "source": MEASURED_TURN_SIZES_SOURCE,
    }


def config_budget_check(num_predict, num_ctx, *, keep_recent: int = 4,
                        chars_per_token=None,
                        _with_sensitivity: bool = True) -> dict:
    """THE 5.3 SELF-CHECK AT CONFIG LEVEL — the same defect as
    `budget_guard`, caught BEFORE a turn is spent instead of in the rows
    afterwards.  THREE INVARIANTS, and the derivation of each is
    returned in the verdict so a reader can re-derive it rather than
    trust it:

      T. `num_predict >= MIN_PREDICT_TRACE_FACTOR x <the model's own
         measured trace, in tokens>` — the generation budget must sit
         ABOVE the trace, or the trace eats it and `content` comes back
         empty: the void signature `budget_guard` detects per row.
      R. `num_ctx > num_predict` — the memory's room must be positive at
         all (a budget that is zero or negative is not a regime).
      B. `budget_chars >= (keep_recent + 1) x <one measured TURN
         (prompt + answer)>` — the compaction trigger must be able to
         hold the turns it KEEPS VERBATIM plus at least one more turn to
         summarize.  THE FACTOR IS `keep_recent + 1`, taken from the
         memory layer's OWN structure (`NaiveMemory.maybe_compact`
         summarizes `messages[:len - keep_recent]`): below it, the
         post-compaction conversation is still over budget and the
         trigger fires on the very NEXT turn — a per-turn rewrite by
         construction, which is what "compaction is a boundary event"
         forbids.  It is not a tuned number.
      S. `DERIVED summary window <= num_ctx` — THE SUMMARIZER'S OWN
         WINDOW, derived from this same budget, must fit inside the
         window this run declares.  The summarizer is handed THE
         TRANSCRIPT, which is bounded by `budget_chars`; if its window is
         smaller than that, the thing it must read is larger than the
         window it reads it in — MEASURED, live, 2026-09-27: the summary
         prompt is 18530 tokens and leaves -2146 tokens of generation
         room inside the summary call's own window (16384).  THE WINDOW
         IS DERIVED, NEVER STATED (`summary_policy_for`), so this
         conjunct is about the CONFIG the derivation lands in — and a
         failure is a config to change: the number is NOT shrunk to fit.

    FAILS ON THE SUPERSEDED CAMPAIGN PAIR (`LH_SUPERSEDED_NUM_PREDICT` /
    `LH_SUPERSEDED_NUM_CTX`, the numbers the smoke ran at) — that is the
    asymmetry proof, and it is exactly what the check is for: the smoke's
    problems were all CONFIG problems, invisible until a model with
    a larger trace ran at them.  THAT PAIR NOW FAILS THREE OF THE FOUR
    CONJUNCTS: the trace budget, the cadence — and the summarizer's
    derived window (12142 tokens against the 8192 the smoke ran in).

    WHAT IT DOES NOT DO: it never changes `chars_per_token` (the stated
    convention, 3.0), and it reads no run state — a config verdict that
    depended on the rows could not be taken before the first turn.
    `sensitivity` reports the same verdict at the `chars_per_token`
    values the convention's honesty range covers, so a reader can see
    whether the verdict rests on that convention's exact value."""
    cpt = float(naive_memory.CHARS_PER_TOKEN
                if chars_per_token is None else chars_per_token)
    allow = trace_token_allowance(cpt)
    prompt_max = int(MEASURED_PROMPT_CHARS[1])
    answer_max = int(MEASURED_ANSWER_CHARS[1])
    turn_max = prompt_max + answer_max
    budget = int(max(1, (int(num_ctx) - int(num_predict)) * cpt))
    required_predict = int(math.ceil(allow["max_tokens"]
                                     * MIN_PREDICT_TRACE_FACTOR))
    kept_turns = int(keep_recent) + 1
    required_budget = int(kept_turns * turn_max)
    # S. THE SUMMARIZER'S DERIVED WINDOW AGAINST THE RUN'S OWN (the sumctx
    # fix): one derivation (`summary_policy_for`), so the window the
    # config check judges is the window the call will post.
    summary = summary_policy_for(int(num_ctx), int(num_predict),
                                 keep_recent=int(keep_recent),
                                 chars_per_token=cpt)

    checks = {
        "generation_room_above_trace": {
            "ok": int(num_predict) >= required_predict,
            "got": int(num_predict), "need": required_predict,
            "why": (f"num_predict {int(num_predict)} < "
                    f"{MIN_PREDICT_TRACE_FACTOR:g} x the measured trace "
                    f"({allow['max_tokens']} tokens, {allow['chars'][1]} "
                    f"chars at {cpt:g} chars/token) = {required_predict}: "
                    f"the trace would consume the budget and `content` "
                    f"would come back empty (the 5.3 void signature)"),
        },
        "positive_room": {
            "ok": int(num_ctx) > int(num_predict),
            "got": int(num_ctx) - int(num_predict), "need": 1,
            "why": (f"num_ctx {int(num_ctx)} <= num_predict "
                    f"{int(num_predict)}: the conversation is given no "
                    f"room at all"),
        },
        "budget_holds_a_summarizable_span": {
            "ok": budget >= required_budget,
            "got": budget, "need": required_budget,
            "why": (f"budget_chars {budget} < keep_recent+1 "
                    f"({kept_turns}) x one measured turn ({turn_max} "
                    f"chars) = {required_budget}: the budget cannot hold "
                    f"even the {int(keep_recent)} turns kept verbatim "
                    f"plus one to summarize, so compaction fires on the "
                    f"very next turn — ~1 compaction per turn, not a "
                    f"boundary event"),
        },
        "summary_window_fits_run_window": {
            "ok": bool(summary["fits_run_window"]),
            "got": int(summary["num_ctx"]),
            "need": int(num_ctx),
            "why": (summary["refusal"] if not summary["fits_run_window"]
                    else (f"the summarizer's DERIVED window "
                          f"({summary['num_ctx']} tokens = the largest "
                          f"prompt, {summary['prompt_tokens_max']}, plus "
                          f"its own budget, {summary['num_predict']}) "
                          f"fits inside the run's own window "
                          f"({int(num_ctx)}) with "
                          f"{summary['slack_tokens']} tokens to spare — "
                          f"the transcript it must read is bounded by "
                          f"this run's memory budget "
                          f"({summary['budget_chars']} chars), and the "
                          f"window is a FUNCTION of that budget, not a "
                          f"second number beside it")),
        },
    }
    # WHERE THE CAMPAIGN PAIR SPENDS ITS BUDGET, in the units the two
    # problems were measured in (so the record says WHY, not just ok/bad).
    values = {
        "num_predict": int(num_predict), "num_ctx": int(num_ctx),
        "keep_recent": int(keep_recent), "chars_per_token": cpt,
        "budget_chars": budget,
        "prompt_chars_max": prompt_max,
        "turn_chars_max": turn_max,
        "prompts_per_budget": round(budget / prompt_max, 2),
        "turns_per_budget": round(budget / turn_max, 2),
        "required_num_predict": required_predict,
        "required_budget_chars": required_budget,
        "track_base_chars_per_token": float(naive_memory.CHARS_PER_TOKEN),
        # THE SUMMARIZER'S WINDOW AND ITS RELATIONSHIP TO THE RUN'S OWN —
        # reported here because a stated relationship is one a reader can
        # check (`summary_window_derivation` spells out the arithmetic).
        "summary_window_tokens": int(summary["num_ctx"]),
        "summary_generation_budget_tokens": int(summary["num_predict"]),
        "summary_prompt_tokens_max": int(summary["prompt_tokens_max"]),
        "summary_window_slack_tokens": int(summary["slack_tokens"]),
        "summary_fits_run_window": bool(summary["fits_run_window"]),
    }
    sensitivity = {}
    if _with_sensitivity:
        for c in CHARS_PER_TOKEN_SENSITIVITY:
            sub = config_budget_check(num_predict, num_ctx,
                                      keep_recent=keep_recent,
                                      chars_per_token=float(c),
                                      _with_sensitivity=False)
            sensitivity[str(c)] = {
                "ok": sub["ok"],
                "budget_chars": sub["values"]["budget_chars"],
                "required_budget_chars":
                    sub["values"]["required_budget_chars"],
                "required_num_predict": sub["values"]["required_num_predict"],
                # ... AND THE SUMMARIZER'S OWN WINDOW AT THIS CONVENTION,
                # reported beside the trace/cadence verdict rather than
                # silently folded into it: the two answer different
                # questions ("does the run's budget clear the trace" vs
                # "does the transcript still fit the summarizer's
                # window").  At the conservative end of the range the
                # transcript is counted in MORE tokens, so the derived
                # summary window grows and can pass the run's own — a
                # margin this field makes visible instead of hiding.
                "summary_window_tokens": sub["values"]["summary_window_tokens"],
                "summary_window_slack_tokens":
                    sub["values"]["summary_window_slack_tokens"],
                "summary_fits_run_window":
                    sub["values"]["summary_fits_run_window"],
            }
    ok = all(c["ok"] for c in checks.values())
    reasons = [f"{name}: {c['why']}" for name, c in checks.items()
               if not c["ok"]]
    return {
        "ok": bool(ok),
        "checks": checks,
        "values": values,
        "trace_allowance": allow,
        "sensitivity": sensitivity,
        "reasons": reasons,
        "derivation": (
            f"num_predict from the MODEL'S OWN MEASURED TRACE "
            f"({allow['chars'][1]} chars = {allow['max_tokens']} tokens "
            f"at {cpt:g} chars/token, x "
            f"{MIN_PREDICT_TRACE_FACTOR:g} headroom = "
            f"{required_predict}); num_ctx from the desired compaction "
            f"CADENCE with num_predict fixed (budget = "
            f"(num_ctx - num_predict) x chars_per_token = {budget} chars "
            f"= {values['prompts_per_budget']} measured prompts = "
            f"{values['turns_per_budget']} measured turns; "
            f"tau_S = {TAU_S_TURNS} turns is a LENGTH, not this capacity "
            f"— compaction is a boundary event INSIDE the window).  "
            f"Source of the sizes: {MEASURED_TURN_SIZES_SOURCE}.  THE "
            f"SUMMARIZER'S OWN WINDOW, since it must read a transcript "
            f"bounded by that same budget: "
            + naive_memory.summary_window_derivation(summary)),
        "summary_policy": summary,
        "note": ("within the config guard's invariants" if ok else
                 "FAILED the config §5.3 check — " + "; ".join(reasons)),
    }


def config_gate(args) -> int:
    """THE COMMAND-LINE GATE — 0 when the invocation's generation policy
    passes `config_budget_check`, non-zero (and LOUD) when it does not.

    WHERE IT FIRES, STATED: in `main`, i.e. on the command line a
    campaign is actually invoked with, BEFORE anything is written or
    posted.  A battery that builds args through `lh_args` and then
    `setattr`s a fixture's own numbers bypasses it BY DESIGN — this is a
    gate on the campaign's INVOCATION, not a constraint on an offline
    fixture — and such a run still RECORDS its own verdict in the
    campaign record and in every run summary, so a programmatic config is
    visible rather than silently outside the gate."""
    check = config_budget_check(int(args.num_predict), int(args.num_ctx),
                               keep_recent=int(args.keep_recent))
    if check["ok"]:
        return 0
    log(f"REFUSED (config §5.3): the generation policy fails the "
        f"config-level check — num_predict={check['values']['num_predict']}, "
        f"num_ctx={check['values']['num_ctx']}: "
        + " | ".join(check["reasons"]))
    log("the derivation (what each number must be derived FROM): "
        + check["derivation"])
    return 6


def window_slice(rows: list, w: int, tau: int = TAU_S_TURNS) -> list:
    """The rows of consolidation window `w` (1-based, complete windows
    only — the `_windows` convention, a trailing partial window is not a
    window)."""
    n = len(rows) // tau if tau else 0
    if w < 1 or w > n:
        return []
    return rows[(w - 1) * tau: w * tau]


def mean_outward(rows: list) -> float | None:
    xs = [float(r["content_chars"]) for r in rows
          if r.get("content_chars") is not None]
    return statistics.fmean(xs) if xs else None


def mean_inward(rows: list) -> float | None:
    xs = [float(r["inward_share"]) for r in rows
          if r.get("inward_share") is not None]
    return statistics.fmean(xs) if xs else None


def floor_from_arms(first_window_means: list) -> float | None:
    """THE FLOOR, DERIVED FROM THE ARMS' OWN MEASURED first-window
    levels: 10% of the mean over every run's first complete window.
    None (never a fabricated number) when no run produced a complete
    first window — the convention is UNSCOREABLE then, and the runner
    says so."""
    xs = [float(x) for x in first_window_means if x is not None]
    if not xs:
        return None
    return FLOOR_FRACTION * statistics.fmean(xs)


def windows_to_collapse(rows: list, floor: float) -> dict:
    """THE DV: the first COMPLETE WINDOW whose mean outward content is
    at or below the floor — with the compaction events it is read
    across.  Returns the window index, the mean, the count of
    compactions before it, and `INSUFFICIENT` when no window crossed
    (which is a result — 'no collapse inside the horizon' — stated as
    such, never smoothed into a number)."""
    n = len(rows) // TAU_S_TURNS
    means = []
    for w in range(1, n + 1):
        m = mean_outward(window_slice(rows, w))
        means.append(m)
        comps = sum(1 for r in window_slice(rows, w)
                    if r.get("compaction"))
        if m is not None and m <= floor:
            return {"windows_to_collapse": w, "crossing_window_mean": m,
                    "compactions_before": comps,
                    "window_means": means, "verdict": "CROSSED"}
    return {"windows_to_collapse": None, "crossing_window_mean": None,
            "compactions_before": None, "window_means": means,
            "verdict": ("INSUFFICIENT (no complete window)" if not means
                        else "NO_COLLAPSE_IN_HORIZON")}


def seed_survival(rows: list) -> list:
    """The per-window self-survival instrument (C3), read off the rows'
    own `self_steps` field (the runner's hook records what the memory
    held that window)."""
    out = []
    n = len(rows) // TAU_S_TURNS
    for w in range(1, n + 1):
        ws = window_slice(rows, w)
        if not ws:
            break
        steps = [r.get("self_steps") for r in ws
                 if r.get("self_steps") is not None]
        out.append({"window": w,
                    "steps_last": (steps[-1] if steps else None),
                    "coverage_end": ws[-1].get("coverage")})
    return out


def ab_separation(summary_a: dict, summary_b: dict) -> dict:
    """THE A-VS-B PREDICTION CHECK, at the PAIR level: rebuild each run's
    prediction from its OWN recorded compaction events and ask the model
    whether the two can be told apart.

    WHY THIS EXISTS (the correction's fourth change): with ONE memory
    regime the arms are separated by the ARRIVAL axis alone, and a
    prediction that cannot differ between the compared arms is the
    defect the harness's L11 rule names.  The separation is COMPUTED
    from the two runs' measured records and REPORTED either way —
    `separated=False` carries a note that says so plainly, never a
    difference the term does not carry.

    WHAT IT READS: each summary's `derivation_loss_events` (the measured
    `(turn, loss)` schedule the run recorded) and the arm's identity.
    Nothing else — no outward level, no floor, no DV: the arrival
    reading is the event's own turn, which is already inside the
    schedule the model integrates.
    """
    def _evs(s):
        return sorted((int(t), float(l))
                      for t, l in (s.get("derivation_loss_events") or ()))

    ev_a, ev_b = _evs(summary_a), _evs(summary_b)
    arm_a = str(summary_a.get("arm", "A"))
    arm_b = str(summary_b.get("arm", "B"))
    pred_a = lh_model.predict_crossing_from_events(ev_a, tau_S=TAU_S_TURNS)
    pred_b = lh_model.predict_crossing_from_events(ev_b, tau_S=TAU_S_TURNS)
    sep = lh_model.prediction_separation(pred_a, pred_b)
    first_a = ev_a[0][0] if ev_a else None
    first_b = ev_b[0][0] if ev_b else None
    # THE ARRIVAL AXIS' OWN ORDERING, stated only where it is WARRANTED:
    # the claim "the run that compacts first does not cross later" holds
    # for a FIXED loss level shifted in time — with different levels the
    # later-arriving run can still cross first (that is the level axis).
    # So it is computed only when the two recorded level sequences are
    # equal, and is None otherwise rather than quietly overreach.
    levels_a = [l for _t, l in ev_a]
    levels_b = [l for _t, l in ev_b]
    levels_equal = levels_a == levels_b
    order = None
    if (levels_equal and first_a is not None and first_b is not None
            and sep["windows"][0] is not None
            and sep["windows"][1] is not None):
        order = bool((sep["windows"][0] <= sep["windows"][1])
                     == (first_a <= first_b))
    return {
        "arms": [arm_a, arm_b],
        "first_compaction_turn": {arm_a: first_a, arm_b: first_b},
        "prediction": {arm_a: sep["windows"][0], arm_b: sep["windows"][1]},
        "crossing_t": {arm_a: sep["crossing_t"][0],
                       arm_b: sep["crossing_t"][1]},
        "separated": sep["separated"],
        "crossing_t_differs": sep["crossing_t_differs"],
        "axis": sep["axis"],
        "same_events": sep["same_events"],
        "levels_equal": bool(levels_equal),
        "earlier_arrival_window_no_later": order,
        "note": sep["note"],
    }


# ==========================================================================
# THE RUN
# ==========================================================================

def lh_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mode", default="plan", choices=("plan", "run"))
    ap.add_argument("--arm", default=",".join(LH_ARMS))
    ap.add_argument("--turns", type=int, default=600,
                    help="turns per run (>= 2 windows at tau_S=100; the "
                         "DV needs compaction events inside the horizon)")
    ap.add_argument("--n", type=int, default=1,
                    help="repeats per arm")
    ap.add_argument("--num-predict", type=int,
                    default=LH_NUM_PREDICT)
    ap.add_argument("--num-ctx", type=int, default=LH_NUM_CTX)
    # THE IN-WINDOW DARK PROBE (added 2026-09-29).  Every N turns, ASK THE
    # AGENT TO RECONSTRUCT ITSELF AND SCORE IT, then DISCARD the answer: the
    # probe must not become the self block, or the measurement would steer
    # the trajectory it is measuring.  0 = OFF (the pre-existing behaviour,
    # byte-identical).  It exists because the compaction-triggered reading
    # is binary and saturates; the within-window reading is graded and needs
    # no compaction to occur.
    ap.add_argument("--probe-every", type=int, default=0,
                    help="dark reconstruction probe every N turns "
                         "(0 = off); the answer is scored and discarded")
    ap.add_argument("--budget", type=int, default=6,
                    help="C11 derivations/turn (the retrieval budget "
                         "D1's live-calibrated value)")
    ap.add_argument("--temperature", type=float, default=0.6)
    ap.add_argument("--seed-base", type=int, default=4242)
    ap.add_argument("--api", default=dmn_llm.CHAT)
    ap.add_argument("--chat-model", default=CAMPAIGN_CHAT_MODEL)
    # THE ENDPOINTS HAVE NO DEFAULT.  `dmn_llm` carries the tree's own
    # local-address defaults, and inheriting them HERE would let a live
    # run post to a machine nobody named (`--mode run` refuses without an
    # endpoint — the spend guard, `endpoint_refusal`).  The live
    # M-cell runner declares the same empty defaults
    # (`exp_selfmonitor.main`), so the two rigs' invocations agree.
    ap.add_argument("--chat-endpoint", default="",
                    help="the /api/chat endpoint — REQUIRED for --mode run")
    ap.add_argument("--endpoint", default="",
                    help="the /api/generate endpoint — REQUIRED for "
                         "--mode run with --api generate")
    ap.add_argument("--model", default=dmn_llm.DEFAULT_MODEL)
    ap.add_argument("--engine", default="stub")
    ap.add_argument("--outdir", default="")
    ap.add_argument("--keep-recent", type=int, default=4)
    ap.add_argument("--horizon-t", type=float, default=4000.0,
                    help="the model-side integration horizon (tau_a)")
    # THE PER-TURN ENDPOINT BOUND.  A WALL-CLOCK BOUND PER TURN, handed
    # to the transport (`LLM_DMN(timeout=...)` — the parameter already
    # existed, this is its CLI seat) and RE-CHECKED after the call: a
    # turn that overran it is REFUSED, never accepted as a good one (the
    # post-hoc check in `dmn_llm._request`/`__call__` is untouched).
    # RAISING IT IS NOT FREE AND NOT AN IMPROVEMENT: it makes a SLOW turn
    # survivable, not fast, and a genuinely hung endpoint then costs that
    # much wall clock before it is refused.  It is in the campaign
    # identity, so a different bound is a DIFFERENT measurement — it
    # moves where a cell can die, and therefore its horizon.
    ap.add_argument("--timeout", type=float, default=LH_TIMEOUT_DEFAULT,
                    help="the WALL-CLOCK BOUND PER TURN (seconds), handed "
                         "to the transport and re-checked after the call: "
                         "a turn over the bound is REFUSED, not accepted. "
                         "Raising it makes a slow turn survivable, not "
                         "fast, and means a hung endpoint costs that much "
                         "more before refusal.  Recorded in the campaign "
                         "identity: a different bound is a different "
                         "measurement (it changes where a cell can die)")
    return ap.parse_args(argv)


#: THE FORCED-CHOICE REGIME'S OWN SEED (fixed across every repeat, the
#: `WORLD_SEED` convention): the rng that decides which class's id
#: renders FIRST on a turn.  A DIFFERENT choice-world seed is a
#: DIFFERENT order tape, so it belongs in the run's identity (it is
#: stated once here, never a CLI flag — the tape is part of the fixed
#: instrument, like TAU_S_TURNS).
CHOICE_WORLD_SEED = 230019


def arm_is_choice(arm: str) -> bool:
    """Does this arm run the FORCED-CHOICE source (`ChoiceWorld`) rather
    than the campaign's `TaskWorld`?  A first-class predicate because
    THREE sites branch on it (the emitter's world, the harness source,
    the identity) and a string test repeated at each would be a
    convention they could drift on."""
    return bool(arm_spec(arm).get("choice_world", False))


def build_choice_world() -> "actions.ChoiceWorld":
    """The run's forced-choice source, ONE construction so the emitter's
    rendered worksheet and the world's adjudication census are the SAME
    object's pure function of (seed, turn) -- the one-source discipline
    `action_source` exists for."""
    import actions
    return actions.ChoiceWorld(seed=CHOICE_WORLD_SEED)


def choice_world_identity(args, arm: str) -> dict | None:
    """The choice source's OWN identity fields (None for a TaskWorld
    arm): the DV's census is a function of these, so they belong beside
    `world_seed` in the run's identity."""
    if not arm_is_choice(arm):
        return None
    w = build_choice_world()
    return {"seed": w.seed, "finite_base": w.finite_base,
            "treadmill_base": w.treadmill_base, "span": w.span,
            "echo_window": CHOICE_ECHO_WINDOW}


#: THE LEDGER ECHO'S WINDOW under the forced-choice regime (the S2 fix):
#: the world's reply names EXACTLY the last turn's completions (window
#: 1).  The pre-change full-history echo replayed the agent's own choice
#: history into every prompt -- the second prompt-supply channel -- so
#: the forced-choice regime windows it.  Refusals are NOT windowed (T4):
#: a refusal the agent cannot see is indistinguishable from success.
CHOICE_ECHO_WINDOW = 1

#: THE FORCED-CHOICE POOL'S COVER REQUIREMENT, stated at plan time: each
#: turn offers two ids and the agent may APPLY more than one completion
#: in a turn (the substrate's own measured behaviour: applied
#: completions per turn mean 1.22, MAX 3, on the lambda-official A-r1/r2
#: rows).  The finite pool must cover the horizon at this draws-per-turn
#: figure or the run is REFUSED before it starts (`ChoiceWorld.
#: assert_plan`, numbers quoted) — the plan-time guard the design added.
CHOICE_DRAWS_PER_TURN = 3


def lh_identity(args, arm: str) -> dict:
    spec = arm_spec(arm)
    cfg = {
        "arm": arm,
        "api": args.api,
        "model": (args.chat_model if args.api == dmn_llm.CHAT
                  else args.model),
        "num_predict": int(args.num_predict),
        "num_ctx": int(args.num_ctx),
        "budget": int(args.budget),
        "turns": int(args.turns),
        "temperature": float(args.temperature),
        "keep_recent": int(args.keep_recent),
        # THE PER-TURN ENDPOINT BOUND, IN THE RUN'S IDENTITY: it is part
        # of the FIXED INSTRUMENT, not a convenience — the bound decides
        # WHERE A CELL CAN DIE (a cell refused at turn 6 has a horizon of
        # 6, not `turns`), so two runs at different bounds are two
        # different measurements and must not compare as one
        # configuration.  It is a WALL-CLOCK BOUND, not a result: a
        # larger value does not make a turn faster or the run better.
        "timeout": float(args.timeout),
        "world_seed": WORLD_SEED,
        "tau_S": TAU_S_TURNS,
        "self_T": CAMPAIGN_SELF_T,
        # THE SINGLE STATED REGIME: recorded in every run's identity so
        # a reader never has to infer which memory the arm ran under
        # (it is not an arm field, so it cannot vary between arms).
        "memory_regime": memory_regime(arm),
        # THE SECOND FACTOR, in the identity because it decides whether
        # the DV can exist at all: under "reinject" the derivation is
        # restored every window and `derivation_loss` is identically 0.0,
        # so a run of it cannot be compared to a run of "once" as if the
        # difference were a result.
        "inject_regime": arm_spec(arm)["inject_regime"],
        "monitoring_para_sha16": hashlib.sha256(
            (dmn_llm.SELF_MONITORING_INSTRUCTION
             if spec["monitoring"] else "").encode()
        ).hexdigest()[:16],
        "framing_sha16": hashlib.sha256(
            dmn_llm.TASK_FRAMING_HEAD.encode()).hexdigest()[:16],
        "chars_per_token": naive_memory.CHARS_PER_TOKEN,
        # THE SUMMARIZATION CALL'S OWN POLICY, in the identity because it
        # is part of the FIXED INSTRUMENT: a reader comparing two runs
        # must know the summary call's budget AND its window as well as
        # the run turns' (a run whose summarizer was starved of room
        # produced no summary at all — MEASURED, live, 2026-09-27).  BOTH
        # numbers are DERIVED from this run's own num_ctx/num_predict
        # (`summary_policy_for`), never stated: the stated 16384 did not
        # follow the run's window when it grew and refused a transcript
        # that had grown with it.
        "summary_num_predict": int(summary_policy_for(
            int(args.num_ctx), int(args.num_predict),
            keep_recent=int(args.keep_recent))["num_predict"]),
        "summary_num_ctx": int(summary_policy_for(
            int(args.num_ctx), int(args.num_predict),
            keep_recent=int(args.keep_recent))["num_ctx"]),
        "floor_fraction": FLOOR_FRACTION,
        # THE S+/S- SEAT (ops/lambda/CHOICE-PREREG.md): whether the
        # derivation seed is SUPPLIED (S+) or WITHHELD (S-) with the
        # grounding held ON in both.  A reader comparing an S+ run to an
        # S- run must be able to see WHICH this was from the identity —
        # the arms' prompts differ by the seed's three channels, and a
        # mislabelled run would be indistinguishable from a null result.
        # (The string is the spec's own field, quoted, so the identity
        # and the arm registry cannot drift.)
        "seed_absent": bool(spec.get("seed_absent", False)),
        # THE FORCED-CHOICE SOURCE, when the arm runs one: the DV is
        # read off the ChoiceWorld's own census, so the source's SHAPE
        # (its id ranges and span) is part of the measurement's identity
        # exactly as `world_seed` is.  None for every TaskWorld arm
        # (the arms whose rows carry no class ledger).
        "choice_world": choice_world_identity(args, arm),
    }
    return cfg


def build_inner(args, arm: str, *, world, summarizer=None):
    """The inner emitter.  THERE IS ONE REGIME AND ONE BRANCH: the arm's
    spec is validated (`arm_spec` — no per-arm memory field, the arm
    exists) and the stated regime is checked (`memory_regime` — the
    module constant has not been changed), then the naive emitter is
    built.  C2: the monitoring paragraph is the ONLY difference between
    the arms' prompts."""
    spec = arm_spec(arm)
    memory_regime(arm)                  # refuses any regime but naive
    preds = dict(ACTION_DECLARED_PREDICATES)
    preds.update(SELF_PREDICATES)
    inner = dmn_llm.LLM_DMN(
        api=args.api, model=(args.chat_model if args.api == dmn_llm.CHAT
                             else args.model),
        endpoint=(args.chat_endpoint if args.api == dmn_llm.CHAT
                  else args.endpoint),
        chat_endpoint=args.chat_endpoint,
        num_predict=int(args.num_predict), num_ctx=int(args.num_ctx),
        temperature=float(args.temperature),
        seed=int(args.seed_base),
        # THE PER-TURN ENDPOINT BOUND, PLUMBED THROUGH (the parameter is
        # `LLM_DMN`'s own; this is the seat the CLI gained).  It bounds
        # EVERY call this emitter makes through the same transport — the
        # run turns AND the summarization calls (the live summarizer
        # posts via `inner.complete_messages`), so one number is the
        # wall-clock bound on a turn in both senses.  The post-hoc
        # refusal for an over-bound turn is the emitter's and is
        # untouched.
        timeout=float(args.timeout),
        world=world, predicates=preds,
        commitment_predicates=COMMITMENT_PREDICATES,
        self_dominant=False, task_framing=True,
        brief=CAMPAIGN_BRIEF,
        self_monitoring=(dmn_llm.SELF_MONITORING_INSTRUCTION
                         if spec["monitoring"] else ""),
        elicitation="A0")
    return NaiveMemoryDMN(inner, summarizer,
                          num_ctx=int(args.num_ctx),
                          num_predict=int(args.num_predict),
                          keep_recent=int(args.keep_recent))


def build_cfg(args, dmn, *, outdir: str, world, spec=None) -> Stage2Config:
    """THE HARNESS CONFIG -- identical across arms EXCEPT the one declared
    arm field `inject_regime` (the 2x2's second factor; every other field
    is C2/C3 fixed): the self seat ON (seeded + priced + commitments +
    agent-g), the task ON, the drive OFF (the plant is NOT the DV), the
    inward instrument ON.  `inject_regime` reaches the harness from the
    ARM's spec, never from a CLI default, so an arm cannot be mislabelled
    by a forgotten flag."""
    return Stage2Config(
        inject_regime=(spec or {}).get("inject_regime", "inject"),
        reconstructor=(dmn.inner._live_reconstructor()
                       if (spec or {}).get("inject_regime") == "reconstruct"
                       else None),
        dmn=dmn,
        couple_backlog=False,
        routing_selector=None,
        engine=args.engine,
        record_path=os.path.join(outdir, "rows-lh.tmp"),
        # THE GROUNDING SEAT: the harness refuses these apart, so they move
        # as one — the MY STATE block, the retrieval seat, the seed and the
        # agent-G all exist together or not at all.
        retrieval_priced=bool((spec or {}).get("grounding", True)),
        seed_self=bool((spec or {}).get("grounding", True)
                       and not (spec or {}).get("seed_absent", False)),
        self_T=(CAMPAIGN_SELF_T if (spec or {}).get("grounding", True)
                else None),
        agent_g=bool((spec or {}).get("grounding", True)),
        # THE S- SEAT (the forced-choice pair's critical distinction):
        # grounding ON, derivation ABSENT.  Set ONLY by the S- arm's
        # spec — never a CLI default — so an arm cannot be mislabelled
        # by a forgotten flag (the inject_regime discipline).
        seed_absent=bool((spec or {}).get("seed_absent", False)),
        budget=CostBudget(derivations_per_turn=int(args.budget)),
        actions=True,
        action_admissible=AdmissibleActions({"complete"}),
        action_source=world,
        # THE LEDGER ECHO'S WINDOW: 1 on the forced-choice arms (the
        # world answers the last action only — the S2 fix), unchanged
        # (full history, the pre-change bytes) on every TaskWorld arm.
        world_echo_window=(CHOICE_ECHO_WINDOW
                           if (spec or {}).get("choice_world", False)
                           else None),
        drive_seat=False,
        inward_seat=True,
    )


#: THE DV'S OWN INSUFFICIENCY FLOOR (ops/lambda/CHOICE-PREREG.md): a
#: treadmill-share fraction read off fewer single-completion turns than
#: this is INSUFFICIENT, not a direction — the decision-rule lesson
#: (an instrument that cannot return "undecided" will return something
#: else instead), stated as a share of the REALISED n with the floor
#: configurable per campaign.
CHOICE_DV_MIN_TURNS = 20


def choice_dv(rows: list, *, min_turns: int | None = None) -> dict:
    """THE FORCED-CHOICE DV, read off the WORLD'S OWN LEDGER.

    Among turns that applied EXACTLY ONE completion, the FRACTION whose
    applied id is of the TREADMILL class — read from the row's
    `talking_applied_classes` (the class the WORLD stated at apply
    time), never re-derived from the id's bytes.  Turns with zero or
    2+ applied completions are NOT choices between this turn's pair
    (2+ applied is the supply-overflow behaviour; 0 is a non-choice)
    and are counted separately, not discarded silently.  Below
    `min_turns` (default CHOICE_DV_MIN_TURNS, configurable) the verdict
    is INSUFFICIENT, never a number read as a direction."""
    floor = (CHOICE_DV_MIN_TURNS if min_turns is None else int(min_turns))
    single = multi = zero = 0
    tread = fin = unknown = 0
    for r in rows:
        classes = tuple(r.get("talking_applied_classes") or ())
        n = len(classes)
        if n == 0:
            zero += 1
            continue
        if n > 1:
            multi += 1
            continue
        single += 1
        c = classes[0]
        if c == CHOICE_CLASS_TREADMILL:
            tread += 1
        elif c == CHOICE_CLASS_FINITE:
            fin += 1
        else:
            unknown += 1
    share = (tread / single) if single else None
    if single < floor:
        return {"status": "INSUFFICIENT", "single_turns": single,
                "floor": floor, "treadmill_share": None,
                "treadmill": tread, "finite": fin, "unknown_class": unknown,
                "multi_turns": multi, "zero_turns": zero,
                "note": f"fewer than {floor} single-completion turns — "
                        f"the DV cannot read a direction off {single}"}
    return {"status": "OK", "single_turns": single, "floor": floor,
            "treadmill_share": share, "treadmill": tread, "finite": fin,
            "unknown_class": unknown, "multi_turns": multi,
            "zero_turns": zero}


def task_health(rows: list, *, window: int = TAU_S_TURNS) -> dict:
    """THE TASK-HEALTH GATE (the surviving M-cell gate, re-read over this
    runner's rows): the worksheet is really being done iff the WORLD
    APPLIED at least one `complete(tNN)` per COMPLETE window in every
    window — read off `talking_applied`, the world's own ledger, never
    an engine verdict.  A cell that abandoned the worksheet has an
    obedience-limited 'no collapse', which is exactly the false read
    this gate exists to kill.  Can FAIL and can say INSUFFICIENT."""
    n = len(rows) // int(window) if window else 0
    if n == 0:
        return {"status": "INSUFFICIENT", "windows": 0,
                "note": "no complete window — the gate cannot read a "
                        "partial window"}
    applied = []
    for w in range(1, n + 1):
        ws = rows[(w - 1) * window: w * window]
        applied.append(sum(int(r.get("talking_applied") or 0)
                           for r in ws))
    ok = all(a >= 1 for a in applied)
    return {"status": ("OK" if ok else "NOT_OK"), "windows": n,
            "applied_per_window": applied,
            "applied_total": sum(applied),
            "note": (None if ok else
                     "at least one window applied NO completion — the "
                     "worksheet was abandoned there, and any collapse "
                     "reading over that window is obedience-limited")}


def run_one_lh(args, arm: str, repeat: int, outdir: str, *,
               inner=None, summarizer=None, judge=None) -> dict:
    """ONE arm's run.  `inner`/`summarizer` are the fixture hooks (the
    battery drives the whole path offline with them); None builds the
    real emitter, whose transport will raise without an endpoint (the
    live mode is not entered here)."""
    from exp_agent_coupling import RecordingDMN
    turns = int(args.turns)
    os.makedirs(outdir, exist_ok=True)
    rows_path = os.path.join(outdir, "rows", f"{arm}-r{repeat}.jsonl")
    summary_path = os.path.join(outdir, "runs", f"{arm}-r{repeat}.json")
    writer = JsonlWriter(rows_path)
    # THE WORLD IS THE ARM'S OWN: the forced-choice arms (S+/S-) run the
    # ChoiceWorld source (two fresh class-neutral ids per turn, one per
    # class, randomized render order), every other arm the campaign's
    # TaskWorld — the ONE construction the emitter renders AND the
    # harness adjudicates against, so the worksheet and the universe
    # are one source in both regimes (`action_source`'s discipline).
    world = (build_choice_world() if arm_is_choice(arm)
             else dmn_llm.TaskWorld(seed=WORLD_SEED))
    if arm_is_choice(arm):
        # PLAN-TIME REFUSAL, before a single turn runs: the finite pool
        # must cover the whole horizon at the stated draws per turn, and
        # a plan it cannot cover is REFUSED with the numbers quoted —
        # an exhausted pool would present mechanical exhaustion as the
        # finite class's own behaviour (the model-fidelity guard).
        world.assert_plan(turns, draws_per_turn=CHOICE_DRAWS_PER_TURN)
    emitter = (inner if inner is not None
               else build_inner(args, arm, world=world,
                                summarizer=summarizer))
    rec = RecordingDMN(emitter, predicates=emitter.predicates,
                       commitment_predicates=emitter.commitment_predicates)
    # THE DV'S OWN CALL: built lazily like the summarizer, and injectable
    # so the battery can drive the whole path offline with a stub.
    if judge is None:
        judge = emitter._live_judge()
    cfg = build_cfg(args, rec, outdir=outdir, world=world,
                    spec=arm_spec(arm))
    # THE PLANT'S OWN SCHEDULE, frozen and UNTOUCHED by anything the
    # agent did: the EMPTY schedule — every exogenous channel at 0 for
    # the whole horizon, so the plant beside the experiment is its own
    # no-drive baseline and NO INWARD EPISODE, NO AFFECT PULSE and NO
    # RESCUE is injected by the runner.  (The default rescue_schedule
    # carries the frozen scenario's own u_ext=0.8 rescue at t=800 and an
    # a_hold=0.9 episode — both would be PLANT INPUTS the experiment
    # never licensed; the killed rig's correction, mechanically applied.
    # The plant's trajectory is recorded per turn purely as context.)
    sch = Schedule(channels={
        "a_hold": [(0.0, float(turns) + 1.0, 0.0)],
        "A": [(0.0, float(turns) + 1.0, 0.0)],
        "u_ext": [(0.0, float(turns) + 1.0, 0.0)],
    })
    p = Params()
    rescue = RescueSeat(mode="off")
    identity = lh_identity(args, arm)
    state = {"t_prev": time.time(), "rows": [], "secs": []}

    def hook(turn: int, st) -> bool:
        now = time.time()
        secs = now - state["t_prev"]
        state["t_prev"] = now
        row = st.log[-1]
        gen = rec.by_turn.get(int(turn), {})
        trace = gen.get("trace_text")
        mem = getattr(emitter, "memory", None)
        last_ev = getattr(emitter, "last_compaction", None)
        # THE PER-TURN RETRIEVAL CHARGE — an INSTRUMENT now, not the
        # cost term (read off the state the harness already exposes,
        # one source).  Kept because it is the substrate's real
        # maintenance cost and the pre-registration cites it; the
        # model's term is the derivation loss below.
        cost = int(st.retrieval_derivations)
        # THE COST TERM: what the summarization destroyed at THIS
        # window event, in the derivation's own units (steps of the
        # seed).  Both readings are recorded: the LOCAL loss this event
        # inflicted (the attribution) and the STANDING loss the memory
        # is left carrying (the level the schedule holds until the next
        # event).
        lost_local = (lh_model.derivation_loss(
            last_ev.self_steps_before, last_ev.self_steps_after)
            if last_ev is not None else None)
        lost_standing = (lh_model.standing_loss(last_ev.self_steps_after)
                         if last_ev is not None else None)
        # THE C3 PROBE SURFACE: what the memory holds NOW.  With ONE
        # regime there is one surface — the naive conversation
        # (post-compaction: the summary plus the kept turns).  An
        # emitter with no naive memory is REFUSED outright: it could
        # only be another regime, and this experiment has none.
        if mem is None:
            raise RuntimeError(
                "the run's emitter carries no naive memory — the "
                "memory regime is a stated single condition "
                f"({LH_MEMORY_REGIME!r}); this experiment has no other "
                "seat (arm C's priced-reconstruction emitter was "
                "removed with arm C)")
        probe_text = mem.conversation_text()
        # ---- THE DV, SCORED ONCE PER REGENERATION ---------------------
        # `st.last_reconstruction` changes only when the arm regenerates the
        # block (window 1's seed, then once per compaction).  The fidelity of
        # THAT text is the campaign's dependent variable; scoring it every
        # turn would judge the same string repeatedly and inflate n.
        _fid = None
        _fid_steps = None
        _fid_empty = None
        _judge_raw = None
        # ---- THE IN-WINDOW DARK PROBE ---------------------------------
        _probe_turn = None
        _probe_fid = None
        _probe_steps = None
        _probe_chars = None
        _probe_text = None
        _probe_raw = None
        _pe = int(getattr(args, "probe_every", 0) or 0)
        if _pe > 0 and turn % _pe == 0:
            try:
                # ASK: the same question the arm asks at a compaction, put
                # to the agent mid-window.  SCORE: the same judge, the same
                # 0..4 scale.  DISCARD: `st.self_block` is not touched.
                _ptext = st.reconstruct_self()
                _pres = recon_score.fidelity_of(
                    tuple(e for _t, e in selfmodel.SEED_ENTRIES),
                    _ptext, judge)
                _probe_turn = int(turn)
                _probe_fid = _pres["fidelity"]
                _probe_steps = _pres["steps_recoverable"]
                _probe_chars = len(_ptext)
                _probe_text = _ptext
                _probe_raw = _pres.get("judge_raw")
            except Exception as exc:                          # noqa: BLE001
                raise RuntimeError(
                    f"the dark probe failed at turn {turn}: {exc!r}.  The "
                    f"probe is the run's DV when --probe-every is set; a "
                    f"silently missing reading would be read as no decay.")
        _rt = getattr(st, "last_reconstruction_turn", None)
        _rtext = getattr(st, "last_reconstruction", "") or ""
        if _rt is not None and _rt != state.get("last_scored_recon_turn"):
            state["last_scored_recon_turn"] = _rt
            try:
                _res = recon_score.fidelity_of(
                    tuple(e for _t, e in selfmodel.SEED_ENTRIES),
                    _rtext, judge)
                _fid = _res["fidelity"]
                _fid_steps = _res["steps_recoverable"]
                _fid_empty = bool(_res.get("empty"))
                _judge_raw = _res.get("judge_raw")
            except Exception as exc:                          # noqa: BLE001
                # THE DV MUST NOT BE SILENTLY MISSING.  A judge answer that
                # cannot be parsed is a MEASUREMENT FAILURE at a known turn,
                # so it is raised: a run whose DV quietly became None would
                # be read as "no collapse" -- the one error this study
                # cannot absorb.
                raise RuntimeError(
                    f"the reconstruction judge failed at turn {_rt} "
                    f"(recon {len(_rtext)} chars): {exc!r}.  The DV cannot "
                    f"be silently absent; fix the judge or the run stops.")
        out = {
            "turn": int(turn), "t": float(row.t),
            # -- THE PLANT RUNS BESIDE, NOT AS THE DV ------------------
            "G": float(row.G), "D": float(row.D), "c": float(row.c),
            # -- INSTRUMENT 1: OUTWARD CONTENT (the primary DV) ---------
            "content_chars": int(gen.get("content_chars", 0) or 0),
            "chars": int(gen.get("chars", 0) or 0),
            # -- INSTRUMENT 2: INWARD SHARE (5.3-guarded) ----------------
            "inward_share": row.inward_share,
            "trace_chars": gen.get("trace_chars"),
            "trace_density": (selfref_density(trace)
                              if isinstance(trace, str) else None),
            "done_reason": gen.get("done_reason"),
            # -- INSTRUMENT 3: THE SELF ---------------------------------
            "coverage": float(row.coverage),
            "recon_chars": len(st.dmn_self or ""),
            "retrieval_derivations": cost,
            "self_steps": naive_memory.seed_steps_in_text(probe_text),
            # -- INSTRUMENT 4: THE GOALS --------------------------------
            "open_commitments": int(row.open_commitments),
            "expired": int(row.expired),
            "commitments": int(gen.get("commitments", 0) or 0),
            # -- INSTRUMENT 5: COMPACTION EVENTS ------------------------
            "compaction": (last_ev is not None),
            "compaction_turn": (getattr(last_ev, "turn", None)
                                if last_ev is not None else None),
            "derivation_loss": lost_local,
            "derivation_loss_standing": lost_standing,
            # -- THE TASK (the world's ledger; the run's health) --------
            "talking_applied": int(row.talking_applied),
            "world_completed": len(st.toolworld.completed),
            # THE PER-ID LEDGER (the forced-choice DV's raw input): the
            # ids the world APPLIED this turn and the class the WORLD
            # stated for each — readable from the record, never
            # re-derived from the id's bytes.  Empty tuples on every
            # TaskWorld arm's zero-applied turn; None-classed only if a
            # source had no census.
            "talking_applied_ids": list(row.talking_applied_ids),
            "talking_applied_classes": list(row.talking_applied_classes),
            "prompt_chars": (len(rec.inner.last_prompt)
                             if getattr(rec.inner, "last_prompt", None)
                             else None),
            "secs": secs,
            # ---- THE DV: RECONSTRUCTION FIDELITY (campaign 4) ---------
            # Scored only when the arm has produced a NEW block (i.e. at a
            # regeneration, which is compaction-triggered).  The judge call
            # is local and happens once per compaction, not per turn.
            "recon_turn": getattr(st, "last_reconstruction_turn", None),
            # THE TEXT ITSELF, so the fidelity score is AUDITABLE.  Without
            # it the DV cannot be checked against the judge's answer, and
            # the judge is this model's own family — an unauditable score
            # from a lenient judge is exactly the kind of claim this
            # project does not accept.
            # ---- THE DARK PROBE (in-window, optional) -------------------
            # Scored and DISCARDED: it never sets the self block, so the
            # act of measuring does not change the thing measured.
            "probe_turn": _probe_turn,
            "probe_fidelity": _probe_fid,
            "probe_steps": _probe_steps,
            "probe_chars": _probe_chars,
            "probe_text": _probe_text,
            "probe_judge_raw": _probe_raw,
            "recon_text": (getattr(st, "last_reconstruction", "") or None),
            "recon_judge_raw": _judge_raw,
            "recon_chars": len(getattr(st, "last_reconstruction", "") or ""),
            "recon_fidelity": _fid,          # 0..1, None when not scored
            "recon_steps": _fid_steps,       # 0..4
            "recon_empty": _fid_empty,       # the agent said NOTHING
        }
        if last_ev is not None:
            emitter.last_compaction = None
        writer.write(out)
        state["rows"].append(out)
        state["secs"].append(secs)
        if turn == 1 or turn % 50 == 0:
            log(f"{arm}-r{repeat} turn={turn:5d} "
                f"outward={out['content_chars']:6d} "
                f"inward={out['inward_share']} cov={out['coverage']:.4f} "
                f"cost={cost} comps={len(mem.compactions) if mem else 0} "
                f"applied={out['talking_applied']} ({secs:.2f}s)")
        return True

    err = None
    try:
        run_stage2(sch, turns, cfg, p=p, checkpoint_fn=hook)
    except Exception as exc:                    # noqa: BLE001 — loud
        err = f"{type(exc).__name__}: {exc}"
        log(f"{arm}-r{repeat} STOPPED at {len(state['rows'])} rows: {err}")
    writer.close()
    rows = state["rows"]
    status = "OK" if err is None else "ERROR"

    # -- THE POST-RUN MEASUREMENTS (all on the agent's own rows) --------
    guard = budget_guard(rows)
    health = task_health(rows)
    mem = getattr(emitter, "memory", None)
    comps = ([vars(ev) for ev in mem.compactions] if mem is not None else [])
    first_w = mean_outward(window_slice(rows, 1))
    # THE RUN'S OWN PREDICTION, from the run's OWN compaction events —
    # the model is handed the measured derivation loss and NOTHING ELSE
    # (`predict_crossing_from_events` cannot see the DV, the floor, or
    # any row: its signature is the guard).  A run whose context never
    # fills inside the horizon has no events, so the term is 0 and the
    # model predicts NO crossing — a per-run prediction, not a
    # constant.  It is RECORDED, never spliced into the plant's
    # schedule: the plant stays the empty schedule (the plant is not
    # the DV).
    loss_evs = lh_model.loss_events(mem.compactions)
    pred = lh_model.predict_crossing_from_events(
        loss_evs, tau_S=TAU_S_TURNS, horizon_t=float(args.horizon_t))
    summary = {
        "arm": arm, "repeat": repeat,
        "label": LH_ARMS[arm]["label"],
        # THE FORCED-CHOICE DV, computed at the run level for the choice
        # arms (None elsewhere): among turns that applied exactly ONE
        # completion, the treadmill share, read off the world's own
        # class ledger — with the explicit INSUFFICIENT outcome below
        # the floor.  The campaign-level criterion (S+ minus S-
        # >= 0.25) is computed from these, never inside a run.
        "choice_dv": (choice_dv(rows) if arm_is_choice(arm) else None),
        "prereg": LH_PREREG_NODE, "result_node": LH_RESULT_NODE,
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": status, "error": err,
        "rows": len(rows), "turns": turns,
        "identity": identity,
        "identity_tag": lh_identity_tag(args, arm),
        # THE CONFIG-LEVEL §5.3 VERDICT, PER RUN: whether or not the CLI
        # gate fired for the invocation, a run states whether the policy
        # it ran under satisfies the trace/cadence invariants — a
        # programmatic fixture lands here instead of silently.
        "config_check": config_budget_check(
            int(args.num_predict), int(args.num_ctx),
            keep_recent=int(args.keep_recent), _with_sensitivity=False),
        "rescue_seat": rescue.dump(),
        "budget_guard": guard,
        "task_health": health,
        "compactions": comps,
        "n_compactions": len(comps),
        # THE SUMMARY CALL'S OWN POLICY AS SENT (the seam's own record):
        # None when the run never compacted, or when a fixture summarizer
        # was injected (a fixture posts nothing and has no transport
        # policy to state).
        "summary_call_policy": getattr(emitter, "last_summary_options", None),
        "derivation_loss_events": [list(e) for e in loss_evs],
        "prediction": {
            "term": ("per-compaction derivation loss (standing, "
                     "steps of the seed)"),
            "loss": pred.loss, "a_hold_max": pred.a_hold_max,
            "n_events": pred.n_events,
            "crossing_t": pred.crossing_t,
            "crossing_turn": pred.crossing_turn,
            "crossing_window": pred.crossing_window,
            "g_end": pred.g_end, "horizon_t": pred.horizon_t,
            "floor": pred.floor,
        },
        "first_window_mean_outward": first_w,
        "memory_regime": memory_regime(arm),
        # THE SECOND FACTOR, in the identity because it decides whether
        # the DV can exist at all: under "reinject" the derivation is
        # restored every window and `derivation_loss` is identically 0.0,
        # so a run of it cannot be compared to a run of "once" as if the
        # difference were a result.
        "inject_regime": arm_spec(arm)["inject_regime"],
        "sign_precondition": SIGN_PRECONDITION_NOTE,
        "wall_s": sum(state["secs"]) if state["secs"] else 0.0,
    }
    _atomic_json(summary_path, summary)
    return summary


def generation_policy_record(args) -> dict:
    """THE CAMPAIGN'S GENERATION POLICY AS A RECORD — the two numbers,
    WHAT EACH IS DERIVED FROM, and the check's derivation text.

    WHY A BUILDER AND NOT THREE LITERALS IN THE DICT: the record has to
    carry the derivation (the numbers were once inherited from a
    different model and NOTHING in the record said so — that is how a
    6000-token budget met a 3-6k-token trace).  One builder means the
    plan artifact and the run-time pre-registration state the same
    thing."""
    check = config_budget_check(int(args.num_predict), int(args.num_ctx),
                                keep_recent=int(args.keep_recent))
    return {
        "num_predict": int(args.num_predict),
        "num_ctx": int(args.num_ctx),
        "keep_recent": int(args.keep_recent),
        "chars_per_token": float(naive_memory.CHARS_PER_TOKEN),
        "derived_from": {
            "num_predict": ("the MODEL'S OWN MEASURED TRACE: "
                            f"{MEASURED_TRACE_CHARS[1]} chars = "
                            f"{check['trace_allowance']['max_tokens']} "
                            f"tokens at "
                            f"{naive_memory.CHARS_PER_TOKEN:g} chars/token "
                            f"x {MIN_PREDICT_TRACE_FACTOR:g} headroom = "
                            f"{check['values']['required_num_predict']} "
                            f"(the budget must sit ABOVE the trace or the "
                            f"trace eats it and content comes back empty "
                            f"— the 5.3 void signature)"),
            "num_ctx": ("the desired COMPACTION CADENCE with num_predict "
                        "fixed: budget_chars = (num_ctx - num_predict) x "
                        f"chars_per_token = "
                        f"{check['values']['budget_chars']} chars = "
                        f"{check['values']['prompts_per_budget']} measured "
                        f"prompts = {check['values']['turns_per_budget']} "
                        f"measured turns per compaction — a BOUNDARY "
                        f"event inside the tau_S = {TAU_S_TURNS}-turn "
                        f"window (the two cannot coincide: tau_S is a "
                        f"turn LENGTH and num_ctx a token CAPACITY)"),
        },
        "measured_sizes_source": MEASURED_TURN_SIZES_SOURCE,
        "measured_trace_chars": list(MEASURED_TRACE_CHARS),
        "measured_prompt_chars": list(MEASURED_PROMPT_CHARS),
        "measured_answer_chars": list(MEASURED_ANSWER_CHARS),
        # THE SUPERSEDED PAIR AND WHY IT FAILED — the record states what
        # the config USED TO BE, so a reader comparing a smoke from
        # before the configfix with a run after it knows the two ran
        # different policies (and the check below must fail on it).
        "superseded": {
            "num_predict": int(LH_SUPERSEDED_NUM_PREDICT),
            "num_ctx": int(LH_SUPERSEDED_NUM_CTX),
            "source": ("exp_agent_coupling's campaign constants, inherited "
                       "by this rig from the Ministral campaign whose "
                       "traces are 2-4k chars"),
            "why_it_failed": (config_budget_check(
                int(LH_SUPERSEDED_NUM_PREDICT),
                int(LH_SUPERSEDED_NUM_CTX),
                keep_recent=int(args.keep_recent))["reasons"]),
        },
        "config_check_ok": bool(check["ok"]),
        "checks": {k: {"ok": v["ok"], "got": v["got"], "need": v["need"]}
                   for k, v in check["checks"].items()},
        "derivation": check["derivation"],
        # THE SUMMARIZER'S OWN POLICY, WITH ITS DERIVATION (the sumctx
        # fix): the window this run will post its summary calls inside,
        # derived from the SAME budget above — and the relationship to the
        # run's own window, which is CHECKED (`summary_window_fits_run_window`)
        # rather than left as an accident.  A stated window is what failed
        # live (MEASURED: an 18530-token prompt refused inside 16384).
        "summary_call": {
            "derived_from": (
                "THE RUN'S OWN MEMORY BUDGET, one source "
                "(`naive_memory.conversation_budget_chars`, the same "
                "expression the compaction trigger uses): the summarizer "
                "is handed THE TRANSCRIPT, which is bounded by that "
                "budget, so its window is a FUNCTION of the budget and "
                "not a second number beside it.  The call's generation "
                "budget is derived from the MODEL'S OWN MEASURED TRACE at "
                "the same headroom factor the run turns use (the "
                "summarizer is a reasoning call on the same model)"),
            "window_tokens": int(check["summary_policy"]["num_ctx"]),
            "generation_budget_tokens":
                int(check["summary_policy"]["num_predict"]),
            "prompt_tokens_max":
                int(check["summary_policy"]["prompt_tokens_max"]),
            "budget_chars": int(check["summary_policy"]["budget_chars"]),
            "transcript_chars_max":
                int(check["summary_policy"]["transcript_chars_max"]),
            "run_num_ctx": int(check["summary_policy"]["run_num_ctx"]),
            "fits_run_window":
                bool(check["summary_policy"]["fits_run_window"]),
            "slack_tokens": int(check["summary_policy"]["slack_tokens"]),
            "derived_arithmetic": check["summary_policy"]["derivation"],
            "keep_recent_note": check["summary_policy"]["keep_recent_note"],
            "refusal": check["summary_policy"]["refusal"],
            "superseded": check["summary_policy"]["superseded"],
            "generation_budget": check["summary_policy"]["generation_budget"],
        },
        "hardware_cost": ("STATED, NOT VERIFIED: 4x the previous window "
                          "(32768 vs 8192 tokens) and 2x the generation "
                          "budget.  The KV cache for 32768 tokens is the "
                          "serving box's to serve; this build does not "
                          "verify it.  The numbers are derived from the "
                          "substrate's measured trace and the stated "
                          "cadence, NOT shrunk to make the run cheap"),
    }


def campaign_record(args, arms: list) -> dict:
    """THE PRE-REGISTRATION ARTIFACT'S OWN CONTENT — one builder, so the
    record `--mode plan` writes and the record `--mode run` writes BEFORE
    its first turn cannot differ (the driver reuses this, it does not
    duplicate it)."""
    # THE CONFIG-LEVEL §5.3 VERDICT, taken once: it is RECORDED in the
    # pre-registration (so a campaign's own numbers carry their verdict
    # and their derivation, whether or not the CLI gate fired — a
    # battery that set its config programmatically lands here too).
    check = config_budget_check(int(args.num_predict), int(args.num_ctx),
                                keep_recent=int(args.keep_recent))
    # THE MODEL-SIDE PREDICTION TABLE (pure ODE arithmetic, no LLM):
    # the crossing window as a function of THE MEASURED PER-COMPACTION
    # DERIVATION LOSS — the term, at the derivation's own granularity
    # (a four-step seed: 0, 1/4 .. 4/4).  Monotone by the model's own
    # ordering, and it shows the RANGE that separates the arms: which
    # losses cross at all.
    table = []
    for l in (0.0, 0.25, 0.5, 0.75, 1.0):
        pred = lh_model.predict_crossing(
            l, horizon_t=float(args.horizon_t))
        table.append({"loss": l,
                      "a_hold": pred.a_hold_max,
                      "crossing_t": pred.crossing_t,
                      "crossing_turn": pred.crossing_turn,
                      "crossing_window": pred.crossing_window,
                      "g_end": pred.g_end})
    # THE ARRIVAL AXIS (what makes the prediction PER-ARM): the same
    # loss, arriving at the turn the arm's OWN compaction record says it
    # did.  A later event crosses later — the constant term could not
    # represent this, and that inability was the defect.
    arrival = []
    for turn in (3, 100, 200, 300, 400):
        pred = lh_model.predict_crossing(
            1.0, arrival_turn=int(turn),
            horizon_t=float(args.horizon_t))
        arrival.append({"loss": 1.0, "arrival_turn": int(turn),
                        "crossing_t": pred.crossing_t,
                        "crossing_turn": pred.crossing_turn,
                        "crossing_window": pred.crossing_window,
                        "g_end": pred.g_end})
    return {
        "prereg_node": LH_PREREG_NODE,
        "result_node": LH_RESULT_NODE,
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        # THE GENERATION POLICY, WITH ITS DERIVATION (the configfix): the
        # two numbers and what each is derived FROM — the model's own
        # measured trace for `num_predict`, and the desired compaction
        # CADENCE for `num_ctx` — together with the verdict of the
        # config-level §5.3 check.  The record carries the derivation, not
        # just the values, because these numbers were once inherited from
        # another model and nothing in the record said so.
        "generation_policy": generation_policy_record(args),
        "config_check": check,
        # THE COMPACTION CADENCE, computed and stated (a consequence of
        # the declared num_ctx/num_predict, not a hidden behaviour): the
        # conversation's char budget is (num_ctx - num_predict) *
        # chars_per_token, and at the campaign's own numbers that budget
        # holds ~12 measured turns (~15 measured prompts), so compaction
        # is a BOUNDARY event inside the tau_S window rather than the
        # per-turn rewrite the superseded pair produced (num_ctx 8192 /
        # num_predict 6000 gave a 6576-char budget — under two prompts).
        "compaction_budget_chars": int(check["values"]["budget_chars"]),
        "compaction_cadence": {
            "budget_chars": int(check["values"]["budget_chars"]),
            "prompts_per_budget": check["values"]["prompts_per_budget"],
            "turns_per_budget": check["values"]["turns_per_budget"],
            "convention": ("turn size = the smoke's measured worst case "
                           "(prompt 4104 + answer 999 chars); the budget "
                           "is the memory layer's own (num_ctx - "
                           "num_predict) x chars_per_token, one source"),
            "tau_S_turns": TAU_S_TURNS,
            "note": ("a BOUNDARY event inside the tau_S window (the two "
                     "cannot be made to coincide: the window is a token "
                     "capacity and tau_S is a turn count — see "
                     "`generation_policy`'s own derivation)"),
        },
        "arms": {a: {"label": LH_ARMS[a]["label"],
                     "prediction": LH_ARMS[a]["prediction"],
                     "identity": lh_identity(args, a)} for a in arms},
        # THE SUBSTRATE, NAMED AT THE TOP OF THE RECORD (not only inside
        # each arm's identity): the model this campaign runs on, and
        # which side of the lineage crossing it sits on.  It is in the
        # DECIDING SURFACE too (`LH_CAMPAIGN_IDENTITY_FIELDS`) — a
        # campaign on a different model is a DIFFERENT campaign, so it
        # must not be resumed into an existing outdir on the strength of
        # an identity that never looked at the model.
        "model": (str(args.chat_model) if args.api == dmn_llm.CHAT
                  else str(args.model)),
        "api": str(args.api),
        "substrate": (
            "LINEAGE CROSSING, TAKEN AS A STATED SUBSTRATE CHOICE "
            "(handoff-selfreg-longhorizon-prereg2): "
            f"{CAMPAIGN_CHAT_MODEL} — Alibaba/Qwen, sign RISES, measured "
            "independently by the tree's own ops ladder "
            "(ops/density_test.py:115) BEFORE this choice.  It is NOT "
            "the Ministral family the size ladder is built on, because "
            "that family's thinking is an INSTRUCTED CONVENTION whose "
            "`thinking` field the chat template DROPS (MEASURED), so the "
            "trace instrument the DV is read from dies by turn 3-4 under "
            "any history-rewriting memory regime (3B, 8B and 14B alike).  "
            "THE COST, STATED: the family-matched SIZE LADDER DIES with "
            "it — its premise ('hold lineage constant, vary size') cannot "
            "carry the instrument."),
        "turns": int(args.turns), "n": int(args.n),
        "budget": int(args.budget),
        # THE SEED, IN THE DECIDING SURFACE (fix 4, 2026-09-28).  It was
        # ABSENT: `--seed-base` reached the emitter (`build_inner`) and
        # NOTHING ELSE — no campaign field, no summary field — so a set of
        # CLONES and a set of independent repeats were the SAME CAMPAIGN
        # to every check in this file, and `write_campaign` would happily
        # resume one into the other.  MEASURED: that is exactly what the
        # paper-2 decisive set (run 3) was — one global seed fanned across
        # six cells, within-arm repeats identical row-for-row over their
        # shared 52-row prefix, the only differing key being the volatile
        # per-turn wall clock `secs` (record ~/setpoint-runs/lambda; node
        # handoff-selfreg-run3-stopped).
        # WHY THE SEED BELONGS HERE: the emitter derives its per-turn seed
        # as `seed + turn` (dmn_llm), so the seed IS the trajectory — two
        # invocations at different seeds are two different experiments and
        # must land in different outdirs, not resume into each other.
        # DELIBERATELY NOT IN `lh_identity` (the PER-RUN tag): `--mode run`
        # takes ONE `--seed-base` for every arm x repeat (`mode_run`), so a
        # per-run seed in the tag would make every already-promoted cell
        # fail its resume lock and re-run THE WHOLE SET from turn 0 at a
        # seed that is not its own — a clone, at full price, in the resume
        # path.  The per-cell seeds live in the launcher's frozen
        # `state/seeds.tsv` and in each cell's own `campaign.json`.
        "seed_base": int(args.seed_base),
        "tau_S": TAU_S_TURNS,
        # THE PER-TURN ENDPOINT BOUND, AT THE TOP OF THE RECORD (not only
        # inside each arm's identity): it is in the DECIDING SURFACE
        # (`LH_CAMPAIGN_IDENTITY_FIELDS`), so the record must carry it
        # where `campaign_identity` reads — a campaign at a different
        # bound is a DIFFERENT campaign and must not be resumed into this
        # one's outdir.
        "timeout": float(args.timeout),
        # WHAT THE BOUND IS, AND WHAT RAISING IT DOES NOT DO — stated in
        # the pre-registration itself, because the failure it answers
        # (four of the live set's eight cells) invites reading a larger
        # number as an improvement.  It is not: the per-turn cost varies
        # because the MODEL'S TRACE LENGTH varies.
        "endpoint_bound": {
            "timeout_s": float(args.timeout),
            "default_s": LH_TIMEOUT_DEFAULT,
            "what_it_bounds": (
                "WALL CLOCK PER TURN, and per summarization call (the "
                "live summarizer posts through the same transport): "
                "`LLM_DMN`'s own `timeout`, handed to `urlopen` AND "
                "re-checked AFTER the call, so a turn that overran it is "
                "REFUSED rather than accepted as a good one"),
            "in_deciding_surface": True,
            "measured_failure_it_answers": (
                "MEASURED, live (the paper-2 decisive set, 2026-09-28): "
                "FOUR OF EIGHT cells died with `TimeoutError` at turns "
                "6-7 — not turn 1 — against the 300 s default, while a "
                "surviving cell's per-turn walls ran 30-208 s (31, 71, "
                "30, 39, 46, 125, 32, 97, 74, 61, 33, 138, 208)"),
            "what_it_does_not_fix": (
                "INTERPRETATION over those MEASURED seconds: the "
                "variance is the MODEL'S OWN TRACE LENGTH (qwen3.5:9b "
                "emits 9k-23k chars of reasoning per turn), so a larger "
                "bound makes a slow turn SURVIVABLE, not FAST.  The "
                "wall-clock and cost estimates built on ~4.4k tok/turn "
                "must be RE-DERIVED from the per-turn seconds the runs "
                "actually produce — this bound does not restore them, "
                "and it makes no claim about accuracy"),
            "cost_of_raising_it": (
                "a genuinely hung endpoint costs that many seconds "
                "before it is refused, in every cell, per turn"),
        },
        "dv": ("windows to collapse: the first complete window whose "
               "mean outward content (chars/turn) is at or below the "
               "floor, the floor DERIVED from the arms' own measured "
               "first-window levels x " + str(FLOOR_FRACTION)),
        "sign_precondition": SIGN_PRECONDITION_NOTE,
        "model_prediction_table": table,
        "model_prediction_arrival_table": arrival,
        "cost_term": (
            "the PER-COMPACTION DERIVATION LOSS (seed survival lost at "
            "the context window, both sides measured by "
            "naive_memory.NaiveMemory), mapped to a_hold by the identity "
            "over [0,1]; the per-turn retrieval charge is measured and "
            "logged as an instrument but is NOT the term (it saturates "
            "at the derivation budget and cannot separate the arms).  "
            "Each run's prediction is computed from ITS OWN compaction "
            "events before its DV is read (prediction.crossing_window in "
            "the run summary)"),
        "floor_convention": (
            f"floor = {FLOOR_FRACTION:g} x mean(first complete window "
            f"mean outward content across the runs); None (unscoreable) "
            f"when no run yields a complete first window"),
        "memory_regime": (
            "A STATED SINGLE CONDITION, NOT A FACTOR: every arm runs "
            "ordinary naive summarization at num_ctx (chars/token = "
            f"{naive_memory.CHARS_PER_TOKEN:g}, headroom = num_predict, "
            "keep_recent kept verbatim).  THE SUMMARIZATION CALL ITSELF "
            "HAS ITS OWN DERIVED POLICY "
            f"(num_predict = {check['summary_policy']['num_predict']} "
            f"inside a window of {check['summary_policy']['num_ctx']} "
            "tokens, BOTH DERIVED from this run's own memory budget at "
            "naive_memory.summary_policy / exp_longhorizon."
            "summary_policy_for): the transcript the summarizer must read "
            "is bounded by that budget, so a window that is STATED rather "
            "than derived drifts out of step with it — MEASURED, live, "
            "2026-09-27: the run's window grew to 32768 and the "
            "summarizer's stated 16384 (set when the window was 8192) "
            "refused an 18530-token prompt with -2146 tokens of room, "
            "stopping the run.  The derived window fits this run's own "
            "window with "
            f"{check['summary_policy']['slack_tokens']} tokens to spare "
            "and the relationship is CHECKED, not assumed "
            "(`summary_window_fits_run_window`).  The engineered priced "
            "reconstruction is OUT of this experiment (arm C removed by "
            "stage=correction on the pre-registration): it is paper 3's "
            "product claim, it changed two things at once so it was no "
            "control for the monitoring cause, and a non-collapsing arm "
            "would invite 'the collapse is contingent on memory design'.  "
            "The regime is not an arm field (`arm_spec` refuses one) and "
            "not a module knob (`memory_regime` refuses a changed "
            "constant)"),
        "prediction_ab": LH_PREDICTION_AB,
        "prediction_separation": {
            "procedure": (
                "ab_separation(summary_A, summary_B): each run's "
                "prediction is rebuilt from ITS OWN recorded "
                "derivation_loss_events and lh_model."
                "prediction_separation reports whether the two crossing "
                "windows differ, on which axis, and states plainly when "
                "they do not"),
            "status": ("NOT COMPUTED — no live run exists (--mode run is "
                       "refused: no endpoint).  It runs on the pair of "
                       "run summaries, never on a pre-set expectation."),
        },
        "rescue_seat": ("BUILT, DEFAULT OFF, NOT RUN IN THIS EXPERIMENT "
                        "(naive_memory.RescueSeat; the timing arms are "
                        "the roadmap's step 2)"),
        "fidelity_notes": [
            "the plant is NOT the DV: nothing about the agent reaches "
            "a_hold or any plant input (the killed rig's tautology)",
            "the self is PRESENT and DEPLETABLE in every arm (C3)",
            "the arms differ in the monitoring paragraph ALONE (C2)",
            "the memory regime is a STATED SINGLE CONDITION (naive "
            "summarization) and is not an arm field — the engineered "
            "regime left this experiment with arm C",
            "the A-vs-B prediction rests on the ARRIVAL axis and its "
            "separation is computed per run pair and reported, "
            "including when it cannot separate them",
            "the model's prediction is computed from the measured "
            "PER-COMPACTION DERIVATION LOSS (both sides of every "
            "compaction event), never from the thinning, the coverage "
            "or the outward content",
        ],
    }


#: THE CAMPAIGN'S DECIDING SURFACE — the fields two invocations must
#: agree on for the second to be a RESUME of the first rather than a
#: different experiment wearing the same outdir.  `created_ts` and the
#: prediction tables are deliberately NOT in it: they are rewritten by
#: every invocation (the tables are pure ODE arithmetic of the same
#: arguments) and are not part of what the campaign DECIDES.
#:
#: `model` IS in it.  A model change is the SUBSTRATE changing, and it
#: moves every measurement this campaign takes (the trace's transport,
#: the register the agent answers in, the compaction cadence's own byte
#: scale) — so a campaign on a different model must land in a FRESH
#: outdir (write_campaign refuses, exit 4) rather than resume into a
#: record written about another model.  It was absent here until the
#: lineage crossing: the arms' identities carried the model, but the
#: deciding surface did not, so a model-only change would have read as
#: the same campaign.
LH_CAMPAIGN_IDENTITY_FIELDS = ("arms", "turns", "n", "budget", "tau_S",
                               "memory_regime", "prediction_ab",
                               "floor_convention", "model", "timeout",
                               "seed_base")
#: WHY `seed_base` IS HERE (fix 4, 2026-09-28 — the defect that invalidated
#: the paper-2 decisive set, run 3).  The emitter derives its PER-TURN seed
#: as `seed_base + turn` (`build_inner` -> `LLM_DMN` -> `dmn_llm`'s
#: `self.seed + int(turn)`), so the base seed IS the trajectory: two
#: invocations at different seeds are two different experiments, and a set
#: whose cells all drew ONE seed is a set of CLONES, not of repeats.
#: MEASURED (record ~/setpoint-runs/lambda, node
#: handoff-selfreg-run3-stopped): the launcher passed one global
#: `--seed-base` to all six cells, and WITHIN EACH ARM the repeats were
#: identical row-for-row over their shared 52-row prefix — the only
#: differing key being the volatile per-turn wall clock `secs`.  Nothing in
#: this file could see that: the seed was in NO campaign field and in NO
#: summary, so a clone set and an independent set were the SAME CAMPAIGN and
#: `write_campaign` would resume one into the other.
#: THE CONSEQUENCE, STATED (the same shape as `timeout`'s): a
#: `campaign.json` on disk written before this field existed reads as a
#: DIFFERENT campaign, so `write_campaign` REFUSES to resume into that
#: outdir (exit 4) — that refusal is CORRECT, and a campaign at a different
#: seed needs a fresh `--outdir` and a new pre-registration.
#: IT IS NOT IN `lh_identity` (the PER-RUN tag), deliberately: `mode_run`
#: takes ONE `--seed-base` for every arm x repeat, so a seed in the per-run
#: tag would make every already-promoted cell fail its resume lock and
#: re-run the whole set from turn 0 at a seed that is not its own.  A
#: per-cell seed is expressed at the LAUNCHER level
#: (`ops/vast/launch_n_instances.sh`: the frozen `state/seeds.tsv` and one
#: child invocation per cell), and each cell's own `campaign.json` carries
#: the seed it actually ran at.
#: WHY `timeout` IS HERE (it arrived with the CLI seat, 2026-09-28).
#: The bound is part of the FIXED INSTRUMENT because it decides WHERE A
#: CELL CAN DIE: the live paper-2 set lost FOUR OF EIGHT cells to a
#: 300 s bound crossed at turns 6-7 — those cells' horizons are 6, not
#: the 600 their `turns` says.  A run at a larger bound can survive a
#: turn the smaller one refused, so it is a DIFFERENT MEASUREMENT and
#: the two must not be compared (or resumed) as one campaign.  THE
#: CONSEQUENCE, STATED: a `campaign.json` on disk written before this
#: field existed reads as a DIFFERENT campaign, so `write_campaign`
#: REFUSES to resume into that outdir (exit 4) — that refusal is
#: CORRECT, not an obstacle.  The running set was launched under the OLD
#: pre-registration and must be recorded as THE OLD ONE; a campaign at
#: a different bound needs a fresh `--outdir` and a new pre-registration.


def _load_json(path: str, default=None):
    """Read a JSON artifact back off disk — the RECORD, not a
    recomputation (the caches-are-the-record discipline)."""
    if not os.path.exists(path):
        return default
    with open(path) as fh:
        return json.load(fh)


def _load_rows(path: str) -> list:
    """Read a run's per-turn JSONL back off disk (the same rows the run
    wrote), or [] when the file is not there."""
    if not os.path.exists(path):
        return []
    return [json.loads(ln) for ln in open(path) if ln.strip()]


def campaign_identity(record: dict) -> dict:
    """THE CAMPAIGN'S DECIDING SURFACE, extracted (never the timestamp)."""
    return {k: record.get(k) for k in LH_CAMPAIGN_IDENTITY_FIELDS}


def write_campaign(outdir: str, record: dict) -> int:
    """WRITE THE PRE-REGISTRATION, AND NEVER CLOBBER ONE.

    Returns 0 when the record is on disk — freshly written, or already
    present and IDENTICAL on its deciding surface to this invocation's
    (the RESUME: a re-invocation of the same campaign reuses the
    pre-registration it wrote) — and non-zero (4) when a DIFFERENT
    campaign is already there, which is REFUSED loudly rather than
    overwritten: an experiment that rewrites its own pre-registration is
    not pre-registered (the same door `exp_selfmonitor.write_campaign`
    keeps).  It is the ONE writer both modes use."""
    path = os.path.join(outdir, "campaign.json")
    if os.path.exists(path):
        prev = _load_json(path, {})
        if campaign_identity(prev) != campaign_identity(record):
            log(f"refused: {path} already holds a DIFFERENT campaign — "
                f"REFUSING to overwrite a pre-registration (an experiment "
                f"that rewrites its own pre-registration is not "
                f"pre-registered).  On disk: "
                f"{campaign_identity(prev)}; this invocation: "
                f"{campaign_identity(record)}.  Ways out: run into a "
                f"fresh --outdir, or delete that file yourself, "
                f"deliberately.")
            return 4
        log(f"campaign.json present and identical — resuming ({path})")
        return 0
    _atomic_json(path, record)
    log(f"pre-registration written BEFORE the first run: {path}")
    return 0


def mode_plan(args) -> int:
    """THE OFFLINE PLAN: write the campaign record (the pre-registration
    artifact) and the model-side prediction table, touch no endpoint.
    A re-invocation over the SAME campaign resumes (the pre-registration
    is not rewritten); over a DIFFERENT one it is REFUSED (exit 4) —
    `write_campaign`'s own rule, shared with `mode_run`."""
    outdir = args.outdir or os.path.join("out", "longhorizon-plan")
    os.makedirs(outdir, exist_ok=True)
    arms = lh_arms_requested(args)
    for a in arms:
        try:
            arm_spec(a)                 # known arm, no extra fields
            memory_regime(a)            # the stated regime, checked
        except (KeyError, ValueError) as exc:
            log(f"refused: {exc}")
            return 2
    record = campaign_record(args, arms)
    rc = write_campaign(outdir, record)
    if rc:
        return rc
    table = record["model_prediction_table"]
    arrival = record["model_prediction_arrival_table"]
    log(f"model prediction table ({len(table)} rows) — loss -> "
        f"crossing window (arrival turn 0, horizon "
        f"{args.horizon_t:g} tau_a):")
    for r in table:
        log(f"  loss={r['loss']:.2f} a_hold={r['a_hold']:.2f} -> "
            f"cross t={r['crossing_t']} (window {r['crossing_window']})")
    log("arrival axis (loss 1.0, the run's own compaction turn — the "
        "axis the A-vs-B prediction rests on):")
    for r in arrival:
        log(f"  arrives turn {r['arrival_turn']:>3} -> cross "
            f"t={r['crossing_t']} (window {r['crossing_window']})")
    log("A vs B: " + LH_PREDICTION_AB)
    # THE MEASUREMENTS FILE (anti-orphan: numbers land here as they
    # are computed).
    _atomic_json(os.path.join(outdir, LH_MEASUREMENTS), {
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model_prediction_table": table,
        "model_prediction_arrival_table": arrival,
        "budget": int(args.budget),
        "memory_regime": LH_MEMORY_REGIME,
        "prediction_ab": LH_PREDICTION_AB,
    })
    return 0


# ==========================================================================
# THE LIVE MODE — THE DRIVER (the spend guard, the pre-registration first,
# the arms, the evaluation)
# ==========================================================================

#: THE EVALUATION ARTIFACT — the tree's one reader convention (the
#: M-cell runner writes the same name; a reader of either rig looks for
#: `evaluation.json`).
LH_EVALUATION = "evaluation.json"

#: WHY THE FOUR LICENCE SEATS CARRY NO VERDICT.  MEASURED (grep over
#: `~/thing/agent`, this pass): the tree's ONLY licence predicate is
#: `exp_selfmonitor.evaluate_mself`, and it reads M1-M8 cells of the
#: M-cell rig.  This experiment's pre-registration
#: (`handoff-selfreg-longhorizon-prereg2`, and the earlier
#: `handoff-selfreg-longhorizon-prereg` it succeeds) states no licence
#: predicate for
#: the A/B campaign.  Per AGENTS.md 1a the seat is BUILT and the GAP is
#: STATED — the alternative (mapping the rig's gates onto L1-L4 myself)
#: would issue a licence nothing pre-registered, which is the same class
#: of error as rewording a claim to match a weaker implementation.
LH_LICENCE_NOT_PRE_REGISTERED = (
    "NO LICENCE IS ISSUED BY THIS EVALUATION.  No licence predicate for "
    "the A/B campaign is pre-registered: the pre-registration node "
    f"({LH_PREREG_NODE}) states the gates (the run's own verdict, "
    "task-health, the 5.3 void guard, the manipulation conjunct) and the "
    "measured floor, and licenses nothing; and the tree's only licence "
    "predicate, exp_selfmonitor.evaluate_mself, reads M1-M8 cells of a "
    "DIFFERENT rig — applying it here would report INSUFFICIENT for "
    "every cell and would put another rig's licence names on this "
    "campaign's record.  The four seats are therefore carried with the "
    "honest value (NOT ISSUED) and the gates below are reported as "
    "GATES, exactly as pre-registered.  Issuing L1-L4 requires a "
    "pre-registration that states each predicate over these readings; "
    "until one exists, a licence here would be an invented claim.")


def endpoint_refusal(args) -> str | None:
    """THE SPEND GUARD, as a predicate (the live rig's own rule,
    `exp_selfmonitor.mode_run`): the api's endpoint must be NAMED.

    A missing endpoint REFUSES — it is never filled in from a module
    default, because `dmn_llm` has NO stub fallback: a silent fallback
    would post the experiment's turns to a machine nobody named and
    would make every measurement unattributable.  Returns the refusal
    message, or None when the invocation names an endpoint."""
    if args.api == dmn_llm.CHAT:
        if not str(args.chat_endpoint or ""):
            return ("--api chat requires --chat-endpoint: an endpoint must "
                    "be NAMED.  There is no default transport and no stub "
                    "fallback, so a silent one would make every "
                    "measurement unattributable (and would spend against a "
                    "machine nobody named)")
        return None
    if args.api == dmn_llm.GENERATE:
        if not str(args.endpoint or ""):
            return ("--api generate requires --endpoint: an endpoint must "
                    "be NAMED.  There is no default transport and no stub "
                    "fallback, so a silent one would make every "
                    "measurement unattributable")
        return None
    return (f"--api {args.api!r} is not a transport this runner has: "
            f"{dmn_llm.CHAT!r} or {dmn_llm.GENERATE!r}")


def lh_arms_requested(args) -> list:
    """The arms the invocation names — the ONE parser (`--arm A-rec,B-rec`),
    shared with `mode_plan`'s own split.

    IT DOES NOT UPPER-CASE (fixed 2026-09-29).  It used to: that was
    harmless while the arms were the single letters 'A' and 'B', and it
    silently corrupts them now that an arm name is a compound identifier
    (`A-rec` -> `A-REC`, refused as an unknown arm).  A normalisation
    applied to a value that has changed shape is the class of defect that
    has bitten this project before; the arms are matched EXACTLY, and the
    refusal lists the valid names."""
    return [a.strip() for a in str(args.arm).split(",") if a.strip()]


def arms_refusal(arms: list) -> str | None:
    """THE ARM-SPEC VALIDATION, as a predicate: every named arm must
    exist (`arm_spec` refuses C and anything unknown) and must run the
    stated regime (`memory_regime` refuses a changed module constant).
    An EMPTY list is refused too: a campaign with no arms is not a
    campaign.  Returns the refusal message, or None."""
    if not arms:
        return (f"--arm names no arm: the deciding set is {sorted(LH_ARMS)}")
    for a in arms:
        try:
            arm_spec(a)
            memory_regime(a)
        except (KeyError, ValueError) as exc:
            return str(exc)
    return None


def lh_identity_tag(args, arm: str) -> str:
    """THE RUN'S CONFIGURATION IDENTITY, hashed — one implementation, so
    the tag a run RECORDS and the tag a resume COMPARES cannot drift."""
    return hashlib.sha256(json.dumps(
        lh_identity(args, arm), sort_keys=True).encode()).hexdigest()[:16]


def lh_resume_ok(prev: dict, args, arm: str) -> tuple:
    """MAY a completed run file be reused as THIS run's measurement?
    Only if it is a COMPLETED measurement (status OK — a partial or
    failed run is never reused as one) of THIS configuration (the
    identity tag).  The second lock on the same door the campaign's own
    identity check keeps (`exp_selfmonitor.mself_resume_ok`)."""
    if prev.get("status") != "OK":
        return False, f"prior attempt status={prev.get('status')}"
    tag = lh_identity_tag(args, arm)
    rec = prev.get("identity_tag")
    if rec != tag:
        return False, (f"the recorded configuration identity differs "
                       f"({rec!r} != {tag!r})")
    return True, "already measured, status OK, configuration identity matches"


def evaluate_lh(arms: list, repeats: int, outdir: str) -> dict:
    """THE ACCEPTANCE RECORD over the runs on disk — the live mode's
    evaluation step.

    IT READS THE RECORD, NOT THE PROCESS: the per-turn rows
    (`rows/<arm>-r<k>.jsonl`) and the run's own summary
    (`runs/<arm>-r<k>.json`) are read back off disk, the same discipline
    `exp_selfmonitor.run_cells` uses (a run is its files).

    WHAT IT CARRIES is the rig's OWN pre-registered machinery, called,
    never re-implemented: the run gate (the run's own status plus the
    5.3 budget guard plus the partial-window reading), the task-health
    gate, the MANIPULATION gate (the first-window inward share, present
    vs absent — the conjunct B's own prediction names), the MEASURED
    floor (`floor_from_arms`), the DV (`windows_to_collapse` per run)
    and the A-vs-B prediction separation (`ab_separation`).  The four
    LICENCE SEATS are carried with the honest value — NOT ISSUED — see
    `LH_LICENCE_NOT_PRE_REGISTERED` (AGENTS.md 1a: build the seat and
    state the gap).  Nothing here can issue a licence, and nothing here
    invents a threshold: a reading the record does not yield is reported
    INSUFFICIENT, never smoothed into a number."""
    runs, rows_by, summ_by = [], {}, {}
    for arm in arms:
        for repeat in range(1, int(repeats) + 1):
            rows = _load_rows(os.path.join(
                outdir, "rows", f"{arm}-r{repeat}.jsonl"))
            summ = _load_json(os.path.join(
                outdir, "runs", f"{arm}-r{repeat}.json")) or {}
            rows_by[(arm, repeat)] = rows
            summ_by[(arm, repeat)] = summ
            fw = mean_outward(window_slice(rows, 1))
            runs.append({
                "arm": arm, "repeat": repeat,
                "status": summ.get("status", "NOT CARRIED"),
                "error": summ.get("error"),
                "rows": len(rows),
                "rows_recorded": summ.get("rows"),
                "n_compactions": summ.get("n_compactions"),
                "identity_tag": summ.get("identity_tag"),
                "predicted_crossing_window": (summ.get("prediction")
                                              or {}).get("crossing_window"),
                "task_health": task_health(rows),
                "budget_guard": budget_guard(rows),
                "first_window_mean_outward": fw,
                "first_window_mean_inward": mean_inward(
                    window_slice(rows, 1)),
                "window_means_outward": [
                    mean_outward(window_slice(rows, w))
                    for w in range(1, len(rows) // TAU_S_TURNS + 1)],
            })
    # THE FLOOR, DERIVED FROM THE RUNS' OWN MEASURED first-window levels
    # (the rig's stated convention, never a pre-set number).
    firsts = [r["first_window_mean_outward"] for r in runs
              if r["first_window_mean_outward"] is not None]
    floor = floor_from_arms(firsts)

    def _run_gate(r):
        """THE RUN GATE: is this run a COMPLETED MEASUREMENT?  Any of
        the three ways it can fail BLOCKS (the M-cell predicate's rule:
        no cell that is not a completed measurement contributes a
        reading) — and each names itself."""
        if r["status"] != "OK":
            return "VOID", (f"the run ended status={r['status']} "
                            f"({r['error']}) — not a completed "
                            f"measurement")
        if r["budget_guard"]["void"]:
            return "VOID", ("the 5.3 guard fired: content empty in a "
                            "majority of turns — the inward share "
                            "measures the budget, not the phenomenon")
        if not r["window_means_outward"]:
            return "INSUFFICIENT", (f"no COMPLETE window (tau_S="
                                    f"{TAU_S_TURNS}): rows exist, windows "
                                    f"do not")
        if not r["summary_rows_agree"]:
            return "VOID", (f"the run summary and the per-turn rows "
                            f"disagree about the row count "
                            f"({r['rows_recorded']} vs {r['rows']}) — "
                            f"reported, not reconciled")
        return "OK", None

    for r in runs:
        rows = rows_by[(r["arm"], r["repeat"])]
        r["summary_rows_agree"] = (r["rows_recorded"] in (None, r["rows"]))
        if floor is None:
            r["dv"] = {"windows_to_collapse": None,
                       "verdict": "INSUFFICIENT (no floor derivable — the "
                                  "arms' own first complete windows are "
                                  "the floor's own source)"}
        else:
            r["dv"] = windows_to_collapse(rows, floor)
        r["run_gate"], r["run_gate_reason"] = _run_gate(r)

    def _agg(verdicts: list) -> str:
        """The worst verdict present, by an explicit severity order; an
        empty sample is INSUFFICIENT, never OK."""
        for s in ("VOID", "INSUFFICIENT", "NOT_OK", "SPLIT", "NOT_PRESENT",
                  "OK", "PRESENT"):
            if s in verdicts:
                return s
        return "INSUFFICIENT"

    gates = {
        "run": {"status": _agg([r["run_gate"] for r in runs]),
                "per_run": {f"{r['arm']}-r{r['repeat']}":
                            {"status": r["run_gate"],
                             "reason": r["run_gate_reason"]} for r in runs},
                "note": ("a run that is not a completed measurement "
                         "(status, the 5.3 guard, a window that does not "
                         "exist) BLOCKS and names itself")},
        "task_health": {
            "status": _agg([r["task_health"]["status"] for r in runs]),
            "per_run": {f"{r['arm']}-r{r['repeat']}": r["task_health"]
                        for r in runs},
            "note": ("the world's own ledger: at least one applied "
                     "completion per COMPLETE window; INSUFFICIENT when "
                     "no complete window exists")},
    }
    # -- THE MANIPULATION GATE (the rig's own conjunct, computed on the
    #    arms' recorded rows): the PRESENT arm's first-window inward
    #    share must EXCEED the ABSENT arm's — the strictly-positive rise
    #    rule the M-cell predicate uses, window-for-window, per repeat.
    manip, per_repeat = [], {}
    for repeat in range(1, int(repeats) + 1):
        # THE PAIR IS FOUND BY FACTOR, NOT BY NAME (fixed 2026-09-29).
        # This looked up the literals "A" and "B", which was fine while
        # those WERE the arm names and silently wrong the moment the arms
        # became A-inj/B-inj/A-rec/B-rec: the pair came back None and the
        # gate reported INSUFFICIENT for a campaign whose arms were right.
        # The gate's own meaning is "monitoring ABSENT vs PRESENT", so it
        # selects on that, and it is then robust to any naming.
        def _pick(want):
            return next((r for r in runs
                         if r["repeat"] == repeat
                         and LH_ARMS.get(r["arm"], {}).get("monitoring") is want),
                        None)
        a = _pick(False)
        b = _pick(True)
        if a is not None and b is not None and a["arm"] == b["arm"]:
            a = b = None      # one arm cannot stand for both factors
        if a is None or b is None:
            v = {"repeat": repeat, "status": "INSUFFICIENT",
                 "reason": ("the pair is not present (arms requested: "
                            f"{arms})")}
        elif (a["first_window_mean_inward"] is None
                or b["first_window_mean_inward"] is None):
            v = {"repeat": repeat, "status": "INSUFFICIENT",
                 "reason": ("no complete first window for one arm — the "
                            "rise cannot be read")}
        else:
            d = b["first_window_mean_inward"] - a["first_window_mean_inward"]
            v = {"repeat": repeat,
                 "absent_A": a["first_window_mean_inward"],
                 "present_B": b["first_window_mean_inward"],
                 "delta": d,
                 "status": "PRESENT" if d > 0 else "NOT_PRESENT",
                 "reason": ("a strictly positive delta (the M-cell rig's "
                            "own RISE rule)")}
        per_repeat[str(repeat)] = v
        manip.append(v)
    gates["manipulation"] = {
        "status": _agg([v["status"] for v in manip]),
        "per_repeat": per_repeat,
        "convention": ("the FIRST COMPLETE window's mean inward share, "
                       "present (B) vs absent (A), per repeat; a strictly "
                       "positive delta is PRESENT (the M-cell predicate "
                       "reads its manipulation gate on the first window "
                       "too — exp_selfmonitor.MSELF_PREDICATE_NOTES); "
                       "disagreeing repeats are SPLIT, never averaged"),
    }
    # -- THE A-VS-B PREDICTION SEPARATION: the rig's own declared
    #    procedure (`ab_separation`, named in the campaign record) over
    #    each repeat's pair of run summaries.  Either verdict is a
    #    result; silence is not, and an unseparated pair says so.
    pairs = []
    # THE PAIR BY FACTOR, NOT BY NAME (see the manipulation gate above):
    # looking up the literals "A"/"B" stopped matching when the arms became
    # A-inj/B-inj/A-rec/B-rec, and the separation reported "not present"
    # for a campaign whose arms were right.
    def _summ_for(want):
        return next((summ_by[k] for k in sorted(summ_by)
                     if k[1] == repeat
                     and LH_ARMS.get(k[0], {}).get("monitoring") is want
                     and summ_by[k]), None)
    for repeat in range(1, int(repeats) + 1):
        sa, sb = _summ_for(False), _summ_for(True)
        if not sa or not sb or sa.get("status") != "OK" \
                or sb.get("status") != "OK":
            continue
        if sa.get("arm") == sb.get("arm"):
            continue      # one arm cannot stand for both factors
        sep = ab_separation(sa, sb)
        sep["repeat"] = repeat
        pairs.append(sep)
    separation = {
        "procedure": ("ab_separation(summary_A, summary_B) over each "
                      "repeat's pair, each run's prediction rebuilt from "
                      "ITS OWN recorded derivation_loss_events"),
        "status": ("COMPUTED" if pairs else
                   "NOT COMPUTED — the A/B pair is not present among the "
                   f"completed runs (arms requested: {arms})"),
        "pairs": pairs,
    }
    licences = {
        "note": LH_LICENCE_NOT_PRE_REGISTERED,
        "status": "NOT ISSUED (no licence predicate is pre-registered)",
        "slots": {k: {"status": "NOT ISSUED",
                      "reason": "no predicate for the A/B campaign is "
                                "pre-registered; the gates above are the "
                                "readings a pre-registration would have "
                                "to map onto this seat"}
                  for k in ("L1", "L2", "L3", "L4")},
    }
    record = {
        "runner": "agent/exp_longhorizon.py",
        "prereg_node": LH_PREREG_NODE,
        "result_node": LH_RESULT_NODE,
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "arms": list(arms), "repeats": int(repeats),
        "turns": next((s.get("turns") for s in summ_by.values()
                       if s.get("turns")), None),
        "memory_regime": LH_MEMORY_REGIME,
        "tau_S": TAU_S_TURNS,
        "runs": runs,
        "gates": gates,
        "floor": {
            "value": floor,
            "convention": (f"floor = {FLOOR_FRACTION:g} x mean(first "
                           f"complete window mean outward content over "
                           f"the runs); None (unscoreable) when no run "
                           f"yields a complete first window"),
            "from_runs": firsts,
        },
        "dv": ("windows to collapse: the first COMPLETE window whose mean "
               "outward content is at or below the measured floor — per "
               "run, with INSUFFICIENT when the floor is not derivable "
               "and NO_COLLAPSE_IN_HORIZON when none crossed"),
        "prediction_separation": separation,
        "licences": licences,
        "marking": ("MEASURED: the gates, the floor, the DV and the "
                    "separation are computed from the runs' own recorded "
                    "rows and summaries.  NOT ISSUED: the four licence "
                    "seats (no predicate is pre-registered).  PROJECTION: "
                    "nothing — no live run is implied by this record's "
                    "existence"),
    }
    return record


def mode_run(args, *, inner_factory=None, summarizer=None,
             judge=None) -> int:
    """THE LIVE MODE — THE DRIVER.

    THE ORDER IS THE DISCIPLINE, and each step refuses rather than
    degrading:

    1. THE SPEND GUARD FIRST (`endpoint_refusal`): without a NAMED
       endpoint nothing is written and nothing is posted (exit 3).
    2. THE ARMS (`arms_refusal`): the named arms must exist and must run
       the stated naive regime — C and anything unknown are refused
       (exit 2), an empty `--arm` too.
    3. THE PRE-REGISTRATION BEFORE THE FIRST TURN (`write_campaign`,
       `campaign_record` — the SAME builder `--mode plan` writes): the
       campaign record lands in the outdir before any turn is posted,
       and an EXISTING campaign is never clobbered — the same campaign
       RESUMES (exit 0), a DIFFERENT one is REFUSED (exit 4).
    4. THE RUNS: every requested arm x repeat in `1..n`, through
       `run_one_lh` (which writes `rows/<arm>-r<k>.jsonl` per turn and
       `runs/<arm>-r<k>.json` at the end).  A run whose summary is a
       completed measurement of THIS configuration is SKIPPED (the
       resume); anything else re-runs.
    5. THE FAILURE IS LOUD AND IT STOPS THE CAMPAIGN: a transport failure
       is not caught and continued — `run_one_lh` records the partial
       run (its rows file stops where it stopped, its summary carries
       status=ERROR) and the driver returns NON-ZERO (5) WITHOUT
       evaluating.  A partial campaign is not scored: the floor is
       derived from the runs' own first windows, so deriving it from an
       arm set that stopped halfway would silently rewrite the
       measurement's own convention.
    6. THE EVALUATION (`evaluate_lh`) writes `evaluation.json` over the
       completed runs: the rig's own gates, the measured floor, the DV
       and the A-vs-B separation — with the four licence seats carried
       NOT ISSUED and the gap stated (`LH_LICENCE_NOT_PRE_REGISTERED`).

    EXIT CODES: 0 a COMPLETED campaign (the gates may still be
    INSUFFICIENT — that is a result, written in `evaluation.json`, not a
    driver failure); 2 refused (arms/regime); 3 refused (no endpoint);
    4 refused (a different campaign is already in the outdir); 5 a run
    failed (the campaign stopped, nothing was evaluated).

    THE FIXTURE SEAM: `inner_factory(args, arm, repeat) -> emitter|None`
    and `summarizer` are passed straight to `run_one_lh` (None = the real
    transport, which raises without an endpoint).  The seam replaces ONLY
    the transport — the arms, the regime, the schedule, the gates and the
    evaluation are the same code a live run takes."""
    outdir = args.outdir or os.path.join("out", "longhorizon-run")

    refusal = endpoint_refusal(args)
    if refusal:
        log(f"refused: {refusal}")
        return 3

    arms = lh_arms_requested(args)
    bad = arms_refusal(arms)
    if bad:
        log(f"refused: {bad}")
        return 2
    if int(args.n) < 1:
        log(f"refused: --n {args.n} runs no repeat (the repeat count is "
            f"the determinism protocol's sample; 1 or more)")
        return 2

    os.makedirs(outdir, exist_ok=True)
    rc = write_campaign(outdir, campaign_record(args, arms))
    if rc:
        return rc
    # THE CONFIG VERDICT IS SAID OUT LOUD ON THIS PATH TOO.  `config_gate`
    # fires in `main` (the command line); this driver is ALSO called
    # directly by the batteries and by any programmatic caller, so the
    # verdict is logged here rather than left to the written record alone
    # — a run whose policy fails the check says so before its first turn.
    ccheck = config_budget_check(int(args.num_predict), int(args.num_ctx),
                                 keep_recent=int(args.keep_recent),
                                 _with_sensitivity=False)
    if ccheck["ok"]:
        log(f"config §5.3 check: OK (num_predict "
            f"{ccheck['values']['num_predict']} >= "
            f"{ccheck['values']['required_num_predict']} = "
            f"{MIN_PREDICT_TRACE_FACTOR:g} x the measured trace; budget "
            f"{ccheck['values']['budget_chars']} chars = "
            f"{ccheck['values']['turns_per_budget']} measured turns per "
            f"compaction)")
    else:
        log("CONFIG §5.3 CHECK **FAILED** for this invocation's policy: "
            + " | ".join(ccheck["reasons"]))
        log("(this driver does not refuse a PROGRAMMATIC invocation — the "
            "CLI gate in `main` is what refuses the campaign's own "
            "command line; the verdict is recorded in campaign.json and "
            "in every run summary so this configuration is visible)")

    n = int(args.n)
    done = []
    for arm in arms:
        for repeat in range(1, n + 1):
            summary_path = os.path.join(outdir, "runs", f"{arm}-r{repeat}.json")
            prev = _load_json(summary_path)
            if prev:
                ok, why = lh_resume_ok(prev, args, arm)
                if ok:
                    log(f"{arm}-r{repeat} SKIP ({why})")
                    done.append(prev)
                    continue
                log(f"{arm}-r{repeat} re-running ({why})")
            log(f"{arm}-r{repeat} START (turns={args.turns}, "
                f"num_ctx={args.num_ctx}, num_predict={args.num_predict}, "
                f"budget={args.budget}, timeout={args.timeout:g}s/turn)")
            inner = (None if inner_factory is None
                     else inner_factory(args, arm, repeat))
            s = run_one_lh(args, arm, repeat, outdir, inner=inner,
                           summarizer=summarizer, judge=judge)
            if s.get("status") != "OK":
                log(f"{arm}-r{repeat} FAILED: {s.get('error')} — the "
                    f"campaign STOPS here (exit 5); the partial run is "
                    f"recorded in its own rows file and summary, and NO "
                    f"evaluation is written over a partial campaign")
                return 5
            log(f"{arm}-r{repeat} OK: {s['rows']} rows, "
                f"{s['n_compactions']} compactions, "
                f"{s['budget_guard']['empty_rate']} empty rate, "
                f"task-health {s['task_health']['status']}, "
                f"predicted window {s['prediction']['crossing_window']}, "
                f"{s['wall_s']:.1f}s")
            done.append(s)
    log(f"all {len(done)} run(s) complete — evaluating "
        f"({len(arms)} arm(s) x {n} repeat(s))")

    evaluation = evaluate_lh(arms, n, outdir)
    path = os.path.join(outdir, LH_EVALUATION)
    _atomic_json(path, evaluation)
    log(f"evaluation written: {path} — run gate "
        f"{evaluation['gates']['run']['status']}, task-health "
        f"{evaluation['gates']['task_health']['status']}, manipulation "
        f"{evaluation['gates']['manipulation']['status']}, floor "
        f"{evaluation['floor']['value']}, licences "
        f"{evaluation['licences']['status']}")
    return 0


def main(argv=None) -> int:
    """THE ENTRY POINT.  THE CONFIG GATE FIRES FIRST (`config_gate`):
    an invocation whose generation policy fails the config-level §5.3
    check is REFUSED (exit 6) before a plan is written or a turn is
    posted — the check that fails on the superseded pair is a gate, not a
    note, and a campaign that would spend a fleet of turns measuring its
    own budget does not start."""
    args = lh_args(argv)
    rc = config_gate(args)
    if rc:
        return rc
    if args.mode == "plan":
        return mode_plan(args)
    return mode_run(args)


if __name__ == "__main__":
    sys.exit(main())
