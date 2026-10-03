"""THE INTEGRATED LONG-HORIZON AGENT — ONE loop, three networks, two
memory regimes, and the model's PREDICTION wired to the regulator's
action (paper 3's harness; the brief `handoff-selfreg-agent-integrated-ctx`).

WHAT THIS MODULE IS.  Every module existed with its own battery — the
DMN generator (`dmn_llm`), the CEN checker/record/tool channel (`cen`
+ the engine), the SN's cheap regulator constants (`sn`), the priced
self (`retrieval`, `selfmodel`), the naive memory regime
(`naive_memory`), the goals (`selfmodel.CommitmentTracker`), the
actions channel (`actions`), and the model's prediction
(`lh_model`).  NOTHING ran them together.  This file is that loop: per
turn the DMN generates, the CEN checks and adjudicates, the memory
regime (SELECTABLE: naive summarization or engineered priced retrieval)
carries the context, and — the point of the build — the SN consumes the
MODEL'S PREDICTION (`lh_model.predict_crossing_from_events`, from the
measured derivation loss) so it can act BEFORE the predicted crossing.

THE CLAIM THE ARMS EXIST TO TEST (do not assume the outcome):

    With the regulator acting on the model's prediction, the agent
    survives horizons at which the same agent without it collapses —
    and acting on the PREDICTION beats acting on the COLLAPSE.

Arms: (i) no regulator; (ii) regulator on the prediction (early);
(iii) regulator on the collapse (late).  The memory regime (naive vs
engineered) is a SECOND factor.  PROJECTION until a live run measures
it; this build supplies the rig and its offline self-test only.

THE REGULATOR'S ACTION SEATS (agent-side, the model's own escape —
architecture.md 5 rule 3: attention redirection, NOT gain; rule 14:
external content OR a terminator, the AND-gate):

  * `inject_external` — EXTERNAL CONTENT: one fixed line on the
    environment's existing state-block channel (`dmn_ctx["tool_state"]`,
    the channel the world already talks on — no new channel is
    invented).  The line names OFFERED WORK from the world's own open
    set (`ToolWorld.open_tasks`) — externally authored content, never
    agent-authored (a self-authored escape is a fidelity change).
  * `DIRECTIVE_REDIRECT` — THE FORCED OUTWARD CHANNEL: the terminator
    half of the AND-gate.  The generator is DIRECTED to produce the
    task output and told the inward stream is closed for the rest of
    the turn.  It is an instruction about the TURN'S FORM, not a
    request to assess state (rule 8: it names no measured quantity).

THE PLANT'S FLOOR IS NOT THE ACTUATOR (protection belongs to the
REGULATOR).  The frozen plant runs the model's own floorless switch —
`Stage2State` constructs it with `floor=None` — and nothing here feeds
`SN_ACTIVATION_FLOOR` (the regulator's own written-down constant,
existence-semantics, never re-checked) to the plant or to any plant
input: a regulator-side constant must never modify the plant's
dynamics.  The seats above are the ENTIRE actuator.

THE PREDICTOR -> REGULATOR EDGE, precisely.  `lh_model` predicts the
crossing from the measured DERIVATION LOSS the memory regime inflicts
at each compaction event (`standing_loss`; the costfix re-point — the
retired per-turn charge saturated and predicted window 2 for every
arm).  This loop HANDS the regulator that prediction, recomputed
rolling as events land, and the regulator fires when the CURRENT TURN
reaches the predicted crossing turn — BEFORE the measured DV crosses,
when the model is right.  The late arm fires only when the measured
outward content crosses the floor.  The prediction is computed from
the loss events ALONE (the circularity guard is lh_model's signature;
this module adds its own: the regulator is constructed with the
prediction object and the DV separately, and the PREDICTION arm never
sees the DV — asserted by the battery).

THE PLANT IS NOT THE DV, HERE TOO.  The run's schedule is the EMPTY
schedule (every exogenous channel 0 for the whole horizon), so the
plant beside the loop is its own no-drive baseline, driven by NOTHING
the agent emits — the L8 discipline carried over and asserted here as
I8 (bit-identical plant trajectories across arms whose agents differ).

*** SCOPE — THE FOUR PREREQUISITES ARE WIRED IN (2026-09-28) ***
The loop now RUNS its own prerequisites instead of yesterday's stub
substrate (each was built and battery-covered separately; this wiring
is what connects them to THE loop):

  1. THE CEN DERIVES.  An `entail.Theory` is INJECTED into the loop's
     CEN (`cen.rules`), built by `le_theory`/`entail.orphan_closure`
     and never constructed by the mechanism (the R5 discipline).  A
     claim that is not a stored fact but IS entailed by rules over the
     store's evidence resolves VERIFIED with rule-id provenance, at
     real proof-tree depth; one the rules refute resolves REFUTED.
     The DEFAULT theory is `orphan_closure()` with an EMPTY evidence
     seed — the shipped SWE suite has no blocking structure, so the
     seat is live (a battery injects evidence through the same seam
     and watches a non-stored claim derive) but the loop's own
     default run derives nothing: STATED, not worked around.
  2. THE TASK IS REAL.  The task universe is the SWE suite
     (`agent/tasks/`): the agent is offered a task, the REQUIREMENT
     text (`README.md`) is the state block it is given, and COMPLETION
     IS THE EVALUATOR'S TYPED VERDICT (`agent/task_eval.py`, visible
     suite; the ToolWorld ledger records the verdict, it does not
     define it).  `run_tests(tNN)` runs the real evaluator in a fresh
     sandbox and the typed verdict rides `tool_state` back.
  3. THE TOOL SURFACE IS THE AGENT'S HANDS.  `realtools.ToolHarness`
     (read/write/edit/bash/task_wait/run_tests, its own fenced carrier
     and typed refusals) is injected through the SAME admissibility
     gate the actions layer owns — DEFAULT EMPTY, externally owned.
  4. THE HELD-OUT SUITE STAYS UNREACHABLE from the agent's side
     (scored out-of-band, designer-only; asserted by the battery).

WHAT REMAINS UNBUILT (below, `NOT_BUILT`): the OUT-OF-PROCESS TOOL
OWNER (R6 — a SEPARATE task is building it in
`boundary_daemon.py`/`boundary_client.py`), the codec path, and the
live run.

MARKING: MEASURED facts are cited in place (floor_crit, k_pull ~6x,
the loss-table monotonicity); everything downstream of a fixture is
INTERPRETATION at best, and the claim itself is PROJECTION.

Run (offline, no network):
    cd ~/thing/agent && PYTHONPATH=../dpdr:. \
        ~/thing/dpdr/.venv/bin/python lh_agent.py --mode plan
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time

from dpdr.model import Params, Schedule

import dmn_llm
import exp_longhorizon as LH
import lh_model
from exp_agent_coupling import JsonlWriter, RecordingDMN, _atomic_json, log
from naive_memory import NaiveMemory, seed_steps_in_text
from stage2_harness import (SN_ACTIVATION_FLOOR, TAU_S_TURNS,
                            run_stage2)

# -- THE SWE TASK BRIDGE (lazy: a default import of this module must not
# -- load the evaluator/tool layer — the actions/retrieval import
# -- discipline; the batteries import them explicitly) ---------------------

__all__ = ["DIRECTIVE_REDIRECT", "EXTERNAL_LINE_HEAD",
           "RegulatorAgent", "INT_ARMS", "P3_ARMS", "ALL_ARMS",
           "run_integrated_cell", "run_campaign", "main"]

#: THE CLAIM the arms exist to test (recorded verbatim in every
#: campaign record; its outcome is NEVER assumed by the rig).
CLAIM = ("with the regulator acting on the model's prediction, the "
         "agent survives horizons at which the same agent without it "
         "collapses, and acting on the PREDICTION beats acting on the "
         "COLLAPSE")

#: THE FORCED OUTWARD CHANNEL — the AND-gate's terminator half, fixed
#: bytes.  An instruction about the turn's FORM: it directs the
#: outward stream and closes the inward one for the rest of the turn.
#: It names NO measured quantity and asks for NO self-assessment (rule
#: 8 — the sensor reads the CEN side; the generator is TOLD state,
#: never asked to measure it).  The battery asserts these bytes carry
#: none of the banned state-measurement phrasings.
DIRECTIVE_REDIRECT = (
    "ATTENTION — external channel open for this turn. Produce the "
    "task output for the worksheet now, as the checkable claims and "
    "lines of work it asks for. The inward stream is closed for the "
    "rest of this turn; write the work, not the thinking about it.")

#: THE EXTERNAL-CONTENT LINE'S HEAD.  The line is rendered with the
#: world's OWN open set (offered, uncompleted ids) — externally
#: authored content on the environment's own channel.  Empty open set
#: -> no line (the seat does not invent work).
EXTERNAL_LINE_HEAD = "EXTERNAL INPUT — offered work, from outside: "

#: WHAT THIS BUILD DOES NOT IMPLEMENT (paper-3-scope 5's dependency
#: order is the follow-on; every item is stated beside the claim it
#: would otherwise silently narrow — the standing order's fourth
#: shape).  Carried as data so the record, the docstring and the
#: battery read ONE list.
NOT_BUILT: tuple = (
    "the OUT-OF-PROCESS TOOL OWNER (R6): the tool surface runs "
    "IN-PROCESS inside this loop; moving it behind the boundary "
    "daemon is a SEPARATE task's file (boundary_daemon.py / "
    "boundary_client.py) and is not done here (paper-3-scope 6)",
    "a consolidation codec: the naive regime's only capacity term is "
    "the substrate's num_ctx; the engineered regime's codec is "
    "identity (paper-3-scope 3.4); the LE->codec supersession path "
    "is not on this loop",
    "a live run: this build is exercised on OFFLINE FIXTURES only; "
    "the claim is PROJECTION until a live run measures it",
    "theory evidence: the injected theory's evidence relations are "
    "seeded EMPTY by default (the shipped SWE suite has no blocking "
    "structure), so the derive path is LIVE but derives nothing "
    "until a caller seeds evidence — the gap is stated, not hidden "
    "behind a wider claim",
)

#: THE ARMS — the smallest set the claim needs, the memory regime as
#: the second factor.  `regulator` is the timing variable: "none" (the
#: same agent, no regulator), "prediction" (early: the model's
#: predicted crossing turn), "collapse" (late: the measured DV's own
#: floor).  `memory` selects the regime ("naive" | "engineered") — a
#: CONFIG FIELD, never a constant.  Everything else is HELD: the self
#: seat ON in every arm (present AND depletable), the task ON, the
#: drive seat OFF (nothing of the agent reaches a_hold — I8).
#: THE PER-TURN ENDPOINT BOUND (seconds) — the loop's own CLI default,
#: stated here so `--timeout` names a number the record can cite.  It is
#: the CAMPAIGN CONVENTION (the launcher's `TIMEOUT=900`, lh_lambda),
#: NOT the emitter's own 300.0: BEFORE this seat existed the loop built
#: its emitter WITHOUT the argument and ran at `LLM_DMN`'s implicit
#: 300.0 (that was today's behaviour — stated, not silently kept: the
#: campaign's recorded bound is 900, and a bare CLI call now names the
#: same number the launcher passes, so the two cannot drift).  Like
#: `exp_longhorizon.LH_TIMEOUT_DEFAULT`, this is a CLI seat, not a new
#: mechanism: the parameter is `LLM_DMN`'s own (handed to `urlopen` AND
#: re-checked post hoc), and the epbound battery's E2 keeps the
#: EMITTER's default pinned at 300.0 — one emitter, two runner defaults,
#: each stated where it lives.
LA_TIMEOUT_DEFAULT = 900.0

# ==========================================================================
# THE LIVE MODE'S OWN SEATS (constants and builders; the driver is
# `mode_run` below).  THE ORDER AND THE DOORS ARE exp_longhorizon's own
# (`endpoint_refusal` :2779, `write_campaign` :2664, `mode_run` :3109) —
# reused, not reinvented: one convention for both runners.
# ==========================================================================

#: THE PAPER-3 PRE-REGISTRATION THE LIVE RUN FLIES UNDER (P3-PREREG.md,
#: §"Status").  `mode_plan`'s record is the DESIGN record; the campaign
#: record this mode writes per outdir is the PER-RUN record.
LA_PREREG_NODE = "ops/lambda/P3-PREREG.md"

#: WHERE THE RUN'S OWN RECORD GOES (the same convention every result
#: node of this campaign series uses — handoff-p3-*).
LA_RESULT_NODE = "handoff-p3-livemode-result"

#: THE EVALUATION ARTIFACT'S NAME (exp_longhorizon.LH_EVALUATION's own
#: convention: a reader of either runner looks for `evaluation.json`).
LA_EVALUATION = "evaluation.json"

#: THE CAMPAIGN'S DECIDING SURFACE (exp_longhorizon's
#: LH_CAMPAIGN_IDENTITY_FIELDS discipline, :2596 — never the timestamp):
#: a re-invocation over the SAME surface RESUMES; a DIFFERENT surface is
#: REFUSED (exit 4), never clobbered.  The paper-3 factors travel inside
#: `arm_identities` (identity() carries the monitoring/regime/grounding
#: block per arm, E1's own seat), and the ENDPOINT is on the surface —
#: the same experiment on a different machine is a different campaign.
LA_CAMPAIGN_IDENTITY_FIELDS = ("mode", "arms", "turns", "n",
                               "num_predict", "num_ctx", "keep_recent",
                               "budget", "tau_S", "surface", "engine",
                               "model", "api", "timeout", "seed_base",
                               "endpoint",
                               "arm_identities")

#: THE DV'S OWN FLOOR-GUARD: a paper-3 arm is regulator=none, so no
#: window floor is ever derived on this path; the recorded value is
#: None with its reason (AGENTS.md 1a: build the seat, state the gap).
_LA_FLOOR_NOT_DERIVED = (
    "None BY DESIGN on this mode: the paper-3 arms are regulator=none "
    "(P3-PREREG §2), and the window floor is an ACROSS-ARMS convention "
    "of the REGULATOR claims (run_campaign's LH.floor_from_arms).  The "
    "worker claim's DV is swe_final_score; no window floor is read.")

INT_ARMS: dict = {
    "N-n": {"label": "no regulator, naive memory", "regulator": "none",
            "memory": "naive"},
    "P-n": {"label": "regulator on the prediction, naive memory",
            "regulator": "prediction", "memory": "naive"},
    "C-n": {"label": "regulator on the collapse, naive memory",
            "regulator": "collapse", "memory": "naive"},
    "N-e": {"label": "no regulator, engineered memory",
            "regulator": "none", "memory": "engineered"},
    "P-e": {"label": "regulator on the prediction, engineered memory",
            "regulator": "prediction", "memory": "engineered"},
    "C-e": {"label": "regulator on the collapse, engineered memory",
            "regulator": "collapse", "memory": "engineered"},
}

# ==========================================================================
# THE PAPER-3 ARMS (the WORKER claim's own factor structure; ADDITIVE —
# the six arms above are the harness's own claim and STAY, unchanged)
# ==========================================================================
#: The fields a paper-3 arm may declare — the same field set
#: `LH.build_cfg`/`build_inner` consume (paper 2's arms, exp_longhorizon
#: `ARM_SPEC_FIELDS`), plus this loop's own `regulator`/`memory` pair so
#: the arms are addressable by the same runner.  A P3 arm declaring
#: anything else is REFUSED (the arm_spec discipline, mirrored).
P3_ARM_SPEC_FIELDS = frozenset({
    "label", "prediction", "monitoring", "inject_regime", "grounding",
    "seed_absent", "regulator", "memory"})

#: PAPER 3's PRE-REGISTERED ARMS (paper-3-scope 4.2's seat x drive,
#: mapped onto what the loop can construct — the plan's Decision 2).
#: The loop's own factor structure (regulator x memory) cannot express
#: the worker claim: it holds the self seat ON in every arm
#: (lh_agent's own "Everything else is HELD" above), hands the
#: derivation back at every compaction (the default inject regime, so
#: `derivation_loss` is identically 0.0 — campaign 3's defect, by
#: construction) and hardcodes the monitoring paragraph ON (the
#: stopped campaign's defect).  These arms select the UNPROTECTED
#: settings through the SAME seats the six harness arms keep as
#: constants:
#:
#:   D0  — seat OFF (grounding False: no MY STATE block, no store
#:         seat, no seed, no agent-G; build_cfg's own grounding-OFF
#:         bundle), no monitoring, inject.  The NO-DEPLETION REFERENCE
#:         on the task axis.  This arm did not exist before: the
#:         self seat was ON in every arm.
#:   D1' — seat ON, monitoring ON, inject.  The PURE-CARRIER control
#:         (paper 2's B-inj shape with the task surface on): the
#:         paragraph's context cost WITHOUT depletion — losses 0.0 by
#:         construction, the cadence is the only instrument.
#:   D1  — seat ON, monitoring ON, RECONSTRUCT.  The DEPLETABLE SELF:
#:         the derivation is seeded ONCE and the agent must reconstruct
#:         it from whatever naive summarization left (paper 2's B-rec
#:         shape with the task surface on).  The worker claim's
#:         positive arm.
#:
#: All three run regulator=none (the regulator is THIS harness's own
#: claim, orthogonal to the worker claim) and memory=naive (the
#: engineered regime is the PRODUCT claim, not this experiment).  D2/D3
#: (paper-3-scope 4.2's drive arms) are NOT constructible on this tree
#: — they need the a_hold-coupled Stage 2 rig paper 2 superseded; the
#: plan's Decision 5 records that as a design decision, not a gap here.
P3_ARMS: dict = {
    "D0": {"label": "paper 3: seat OFF (grounding off, no monitoring, "
                    "inject) — the no-depletion reference on the task "
                    "axis",
           "regulator": "none", "memory": "naive",
           "monitoring": False, "inject_regime": "inject",
           "grounding": False, "seed_absent": False},
    "D1'": {"label": "paper 3: seat ON, monitoring ON, inject — the "
                    "pure-carrier control (cost without depletion)",
            "regulator": "none", "memory": "naive",
            "monitoring": True, "inject_regime": "inject",
            "grounding": True, "seed_absent": False},
    "D1": {"label": "paper 3: seat ON, monitoring ON, reconstruct — "
                   "the depletable self (the worker claim's arm)",
           "regulator": "none", "memory": "naive",
           "monitoring": True, "inject_regime": "reconstruct",
           "grounding": True, "seed_absent": False},
}

#: EVERY ARM THE RUNNER KNOWS, one registry (the six harness arms keep
#: their identity bytes; the paper-3 arms are addressable by the same
#: `--arms` CLI).  Order: harness arms first (unchanged listing), then
#: the paper-3 arms.
ALL_ARMS: dict = {**INT_ARMS, **P3_ARMS}


def _p3_spec(arm: str) -> dict | None:
    """THE ARM'S PAPER-3 SPEC, validated — or None for a harness arm.

    A P3 arm declaring a field outside `P3_ARM_SPEC_FIELDS` is REFUSED
    (an arm that smuggles a new factor is a confound, not an arm); a
    harness arm returns None so every default below keeps today's
    behaviour EXACTLY (the standing instruction: nothing removed, the
    `"inject"` default stays, monitoring stays ON).
    """
    if arm in INT_ARMS:
        return None
    if arm in P3_ARMS:
        spec = P3_ARMS[arm]
        extra = sorted(set(spec) - P3_ARM_SPEC_FIELDS)
        if extra:
            raise ValueError(
                f"paper-3 arm {arm!r} declares {extra}: the worker "
                f"claim's arms carry {sorted(P3_ARM_SPEC_FIELDS)} "
                f"ALONE — an arm declaring anything else is a factor "
                f"in waiting, refused rather than run.")
        return spec
    raise KeyError(
        f"unknown arm {arm!r}: known arms are {sorted(ALL_ARMS)}")


# ==========================================================================
# THE REGULATOR (the SN's agent-side half: the cheap gate + the action)
# ==========================================================================

class RegulatorAgent:
    """THE CHEAP PER-TURN GATE and the ACTION SEATS — never an LLM
    (architecture.md rule 2: tau_a = 1 and the c_mon ceiling both
    disqualify one; this is O(1) arithmetic per turn).

    CONSTRUCTION separates the two inputs the arms vary, and the
    separation IS the circularity discipline: `prediction` is the
    model's object (built from DERIVATION-LOSS events alone, by
    `lh_model`); `collapse_floor` is the DV's own floor (the
    EXPERIMENT's convention, never the seat's).  The "prediction" arm
    reads ONLY the prediction; the "collapse" arm reads ONLY the floor
    and the DV handed to `observe`; "none" reads neither.

    `floor_value` is the REGULATOR'S OWN written-down activation
    constant (SN_ACTIVATION_FLOOR, 0.7 — existence semantics, floors
    0.5-1.3 escape identically, floor_crit 0.4795 ~= E* 0.4969,
    MEASURED) carried as a FIELD for the record and for the day its
    knowing-cost seat is built.  It is NEVER fed to the plant, never
    re-checked (a knowingly-held floor fails at kc ~ 0.2), and it is
    NOT this seat's trigger: the triggers are the two timing arms
    below.  A regulator constant that modified the plant would be the
    harness.py:285 defect class; none does.
    """

    def __init__(self, mode: str, *, prediction=None,
                 collapse_floor: float | None = None,
                 floor_value: float = SN_ACTIVATION_FLOOR,
                 inject_external: bool = True):
        if mode not in ("none", "prediction", "collapse"):
            raise ValueError(
                f"RegulatorAgent mode {mode!r} is not one of "
                f"none|prediction|collapse — the TIMING arms are the "
                f"variable, and an unknown mode is refused rather than "
                f"silently read as 'none'")
        if mode == "prediction" and prediction is None:
            raise ValueError(
                "RegulatorAgent(mode='prediction') needs a prediction: "
                "the EARLY arm acts on the model's predicted crossing "
                "turn — a seat that acted 'around then' would not "
                "measure timing")
        if mode == "collapse" and collapse_floor is None:
            raise ValueError(
                "RegulatorAgent(mode='collapse') needs collapse_floor: "
                "the LATE arm fires at the DV's own floor (the "
                "experiment's convention), never a second one invented "
                "here")
        self.mode = mode
        self.prediction = prediction
        self.collapse_floor = (None if collapse_floor is None
                               else float(collapse_floor))
        #: THE REGULATOR'S OWN CONSTANT, recorded and never actuated on
        #: the plant (see the class docstring).  Carried so the run
        #: record states what the regulator believes, distinct from
        #: what it does.
        self.floor_value = float(floor_value)
        #: whether the external-content seat renders the world's own
        #: offered work (the AND-gate's content half).  The directive
        #: (the terminator half) always rides a fired action.
        self.inject_external = bool(inject_external)
        # -- state (the record) --------------------------------------
        self.fired = False
        self.fired_turn: int | None = None
        self.trigger: str | None = None
        self.turns_observed = 0

    # -- the cheap gate ---------------------------------------------------
    def observe(self, turn: int, outward_content: float) -> bool:
        """One turn's O(1) gate.  Returns whether the seat FIRED THIS
        TURN.  `none` never fires; `prediction` fires when the turn
        reaches the model's predicted crossing turn; `collapse` fires
        at the first measured crossing of the DV's floor.  ONE shot (a
        regulator that re-triggers every turn after crossing is a
        different, unmodelled intervention).  `outward_content` is
        READ BY THE COLLAPSE ARM ONLY — the prediction arm's signature
        discipline keeps the model's input and the DV separate."""
        self.turns_observed += 1
        if self.fired or self.mode == "none":
            return False
        trig = None
        if (self.mode == "prediction"
                and self.prediction.crossing_turn is not None
                and int(turn) >= int(self.prediction.crossing_turn)):
            trig = "prediction"
        elif (self.mode == "collapse"
                and self.collapse_floor is not None
                and outward_content <= self.collapse_floor):
            trig = "collapse"
        if trig is None:
            return False
        self.fired = True
        self.fired_turn = int(turn)
        self.trigger = trig
        return True

    # -- the action seats --------------------------------------------------
    def action(self, turn: int, world) -> dict:
        """The FIRED ACTION, rendered for THIS turn's injection.  Both
        halves of the AND-gate ride a fired action (content OR
        terminator prevents collapse; rule 14):

          * the EXTERNAL-CONTENT seat renders the WORLD'S OWN open set
            (offered, uncompleted) — content authored OUTSIDE the agent
            on the environment's own channel.  `world` is the loop's
            holder pointed at the run's `ToolWorld`; an empty open set
            -> no line (the seat does not invent work; the directive
            still carries the turn).
          * the DIRECTIVE is the forced outward channel: fixed bytes
            (never a function of a measured quantity — rule 8).

        The injection is consumed by the NEXT turn's prompt (the seat
        fires after the turn's own emission was measured; the one-turn
        latency is stated, not hidden)."""
        if not self.fired or int(turn) < int(self.fired_turn):
            return {}
        out: dict = {"directive": DIRECTIVE_REDIRECT,
                     "trigger": self.trigger,
                     "fired_turn": self.fired_turn}
        if self.inject_external:
            render_open = getattr(world, "render_open", None)
            if callable(render_open):
                line = str(render_open(int(turn))).strip()
                if line:
                    out["external_line"] = f"{EXTERNAL_LINE_HEAD}{line}"
                    out["external_ids"] = sorted(
                        _ids_of_line(line), key=_task_sort_key)
        return out

    def dump(self) -> dict:
        return {"mode": self.mode, "fired": self.fired,
                "fired_turn": self.fired_turn,
                "trigger": self.trigger,
                "turns_observed": self.turns_observed,
                "floor_value": self.floor_value,
                "collapse_floor": self.collapse_floor,
                "prediction_crossing_turn": (
                    None if self.prediction is None
                    else self.prediction.crossing_turn),
                "prediction_crossing_window": (
                    None if self.prediction is None
                    else self.prediction.crossing_window),
                "prediction_loss": (None if self.prediction is None
                                    else self.prediction.loss),
                "prediction_events": (
                    None if self.prediction is None
                    else [list(e) for e in self.prediction.events])}


# -- small helpers (deterministic, no measurement) ------------------------

_TASK_ID = re.compile(r"\bt\d+\b")


def _ids_of_line(line: str) -> list:
    return sorted(set(_TASK_ID.findall(line)))


def _task_sort_key(tid: str):
    m = _TASK_ID.match(tid)
    return (0, int(m.group(0)[1:])) if m else (1, tid)


class _WorldHolder:
    """The WORLD the seat renders from, held by the loop (the harness
    owns the ToolWorld and constructs it inside `run_stage2`; the seat
    is built BEFORE the run starts, so it reads the world through this
    holder and the hook points it at `st.toolworld` on turn 1).  The
    seat's rendered content therefore lags the world by at most one
    turn — stated, and the same one-turn latency the whole injection
    already carries (the action fires after the turn's emission was
    measured)."""

    def __init__(self, world=None):
        self.world = world

    def render_open(self, turn: int) -> str:
        w = self.world
        fn = getattr(w, "render_open", None)
        return str(fn(int(turn))) if callable(fn) else ""


# ==========================================================================
# THE SWE TASK UNIVERSE (prerequisite 2 wired: the task is REAL)
# ==========================================================================
#
# The loop's TASK-WORLD SEAM.  `dmn_llm.TaskWorld` (yesterday's
# universe) drew opaque ids tN; this universe offers the SWE suite's
# targets (f1..f3 = agent/tasks/t1_rchunk, t2_histstat, t3_netmask).
# The STATE BLOCK the agent is given is the task's own REQUIREMENT
# text (README.md — the bytes a worker would be given, task_eval's
# requirement seat), and a target leaves the open set only when the
# EVALUATOR'S VISIBLE SUITE passes — `complete(tNN)`'s world answer
# is the typed verdict, never bookkeeping.
#
# PURITY, HONESTLY STATED: `TaskWorld.step` is pure in (seed, turn);
# this universe is NOT pure in turn — a target's outstanding status
# depends on the agent's own edits through the evaluator.  That is the
# point (the world answers WORK, not draws), and it is the one
# fidelity difference from the seam it replaces: the ToolWorld's
# open-set replay (walking turns 1..turn of a pure source) would
# re-derive "offered" sets that no longer mean anything here, so this
# universe carries the open set ITSELF and answers from it.

#: The bridge: sandbox target name -> task directory name under
#: `agent/tasks/` (realtools' `task_map` convention).
SWE_TARGETS: dict = {"f1": "t1_rchunk",
                     "f2": "t2_histstat",
                     "f3": "t3_netmask"}


#: THE TASK QUEUE (the spanning design, P3-PREREG's 2026-10-05
#: amendment; handoff-p3-span plan item (A)): the SAME universe at a
#: larger N — the open set `SWETaskUniverse.step_detail` already
#: renders, offered over MORE targets than a 60-turn run can finish.
#: The three original tasks stay EXACTLY as they were (t2's class-(C)
#: axis is the paper's subject); the six new ones beside them are the
#: same kind of work (a small self-contained module repair, README as
#: requirement, a shipped-broken module, a visible and a held-out
#: suite, a class-(C) specimen under _specimens/).
#:
#: SUPPLY ARITHMETIC (why 9 and not fewer): the MEASURED rate on this
#: substrate is ~3-10 turns per target (p3-smoke2: all three targets
#: declared by turn 10 of 20 in the seat-off arm, and 4-10 turns per
#: target across the cells).  A 60-turn run at the FASTEST observed
#: rate (~3 turns/target) and ZERO overhead would need 20 targets to
#: exhaust the queue; at the MEAN rate (~6 turns/target, including
#: run_tests/decl overhead) it would need 10.  With 9 targets a
#: worst-case-flawless agent empties the set at turn ~27-54 — INSIDE
#: the run — which is why the battery's Q1 gate simulates a
#: max-rate run and requires the open set NON-EMPTY past the LAST
#: COMPACTION (the smoke's blocking finding, as an in-code check).
#: A 9-target queue is therefore sized for the OBSERVED agent, not the
#: theoretical maximum: at the observed mean rate (~6 turns/target) a
#: 60-turn run completes ~10 targets' worth of WORK but ~9 targets of
#: DECLARED completions (repeats of run_tests and refusals consume the
#: difference), and the spanning requirement is that the agent is still
#: DRAWING work while its self thins — the last compaction of a 60-turn
#: run lands around turn ~48-60 (gaps 5-10 turns), by which point the
#: queue must still hold >= 1 open target.  If the re-smoke shows the
#: 9B clearing 9 targets inside 30 turns (S9's first conjunct), the
#: fix is MORE TARGETS, never more cells (falsifier F12).
#:
#: [2026-10-06 correction, appended — the arithmetic above was written
#: at NINE targets and is not rewritten; the registry below has
#: registered TWELVE (t1..t12) since t10-t12 joined the same
#: amendment.  The count is safer at 12, in the direction the
#: arithmetic cares about: every exhaustion estimate above moves
#: LATER (a worst-case-flawless agent needs 20 targets to exhaust the
#: queue and now finds 12, not 9; the mean-rate agent's ~10 declared
#: completions leave 2 open instead of being short by 1), and the Q1
#: gate's spanning clause (open set non-empty past the last
#: compaction) holds with MORE margin at 12 than at 9.  MEASURED at
#: 12 (the battery's own simulator, 2026-10-06): a 3-turns-per-target
#: agent exhausts the 12-target queue at t37, vs t28 for the
#: 9-target queue; at the mean rate (~6) the 9-target queue empties
#: at t55 while the 12-target queue does NOT empty inside 60 turns.]
SWE_QUEUE_TARGETS: dict = {"f1": "t1_rchunk",
                           "f2": "t2_histstat",
                           "f3": "t3_netmask",
                           "f4": "t4_celsius",
                           "f5": "t5_rle",
                           "f6": "t6_paren",
                           "f7": "t7_slug",
                           "f8": "t8_roman",
                           "f9": "t9_luhn",
                           "f10": "t10_caesar",
                           "f11": "t11_cronext",
                           "f12": "t12_flatten"}


#: THE QUEUE'S NAMED AXES (§11a's audit discipline, one seat): the
#: evaluator fail-closes on a task with no axis pair
#: (`task_eval.load_task_spec`: "every task must state what the
#: visible suite pins and what it does not cover"), and `AXES` lives
#: in `task_eval.py`.  The queue's tasks are registered HERE so this
#: module — the queue's owner — carries the registration, and every
#: evaluator this loop constructs merges it (`_swe_axes`, below).  The
#: authoritative table stays `task_eval.AXES` for the three original
#: tasks; entries there WIN over any entry here (no silent divergence:
#: a task named in BOTH is refused, the one-source-of-truth rule).
SWE_QUEUE_AXES: dict = {
    "t1_rchunk": (
        "exact-division chunking (sizes that divide the row count evenly)",
        "the REMAINDER path (a size that does not divide the row count)"),
    "t2_histstat": (
        "distinct-count int bins; tie-break on insertion order",
        "equal VALUES under different keys (int vs float) merged, and "
        "non-numeric keys refused"),
    "t3_netmask": (
        "ASCII junk the int() trap does not cover, plus leading zeros",
        "the int() ACCEPTANCE trap: whitespace, sign, underscore "
        "separators and non-ASCII digits"),
    "t4_celsius": (
        "whole-degree conversions and the two fixed points",
        "fractional values, the round-trip property over a range, and "
        "the values that resist an offset/special-case shortcut"),
    "t5_rle": (
        "runs of length >= 2 between other values",
        "singleton runs at the SEQUENCE BOUNDARY and None as a legal "
        "run value (the None-sentinel conflation)"),
    "t6_paren": (
        "wrong-total-depth negatives (an unclosed opener, an unmatched "
        "closer at the end)",
        "PAIRING under a correct total depth: interleaved and crossed "
        "kinds (\"([)]\", \")(\"), the depth-only blind spot"),
    "t7_slug": (
        "already-lowercase single-space words and the separator",
        "the CHARACTER POLICY: mixed case, punctuation, digits, "
        "underscore, non-ASCII letters, separator runs, trimming"),
    "t8_roman": (
        "additive values, the range/refusal rules, and the three "
        "subtractive pairs the requirement names outright (4, 9, 90)",
        "every OTHER subtractive pair and compound (40, 400, 444, 900, "
        "999, 1904, 1954, 1994, 2024, 3999) and the round trip over "
        "ALL of 1..3999"),
    "t9_luhn": (
        "the doubling DIRECTION on even-length numbers (three valid "
        "16-digit numbers left-counting rejects, one invalid one it "
        "accepts) and the checksum arithmetic on odd length",
        "every OTHER valid even-length number, the 17-digit lengths, "
        "and the PROPERTIES: luhn_check_digit/luhn_ok composition and "
        "the adjacent-transposition flip"),
}


def _swe_axes() -> dict:
    """The axes table every evaluator THIS LOOP constructs runs under:
    `task_eval.AXES` (the authority) merged with `SWE_QUEUE_AXES` (the
    queue's registration), REFUSING a task named in both with
    non-identical axes — two tables that silently disagreed would be
    two different suites wearing one name (the one-source-of-truth
    rule; the E8/T1 mirror discipline)."""
    import task_eval
    merged = dict(task_eval.AXES)
    overlap = {k for k in SWE_QUEUE_AXES if k in merged}
    for k in overlap:
        if tuple(merged[k]) != tuple(SWE_QUEUE_AXES[k]):
            raise ValueError(
                f"task {k!r} carries DIFFERENT axes in task_eval.AXES "
                f"and SWE_QUEUE_AXES ({merged[k]!r} vs "
                f"{SWE_QUEUE_AXES[k]!r}) — one task, one axis pair; "
                f"fix the registration before running")
    merged.update(SWE_QUEUE_AXES)
    return merged


def _swe_specs(axes: dict | None = None):
    """The suite's TaskSpecs, discovered once per universe (the same
    `load_task_spec` gate the evaluator itself runs: a malformed task
    refuses HERE, before any run starts)."""
    from task_eval import discover_tasks
    return {s.name: s for s in discover_tasks(axes=_swe_axes()
                                              if axes is None
                                              else axes)}



class SWETaskUniverse:
    """THE WORLD'S OWN TASK SOURCE for the integrated loop: offers the
    suite's targets, answers completion with the EVALUATOR's verdict.

    The ToolWorld seam contract (`actions.ToolWorld.source`): a
    callable `step(turn) -> (state_block, universe)` plus
    `step_detail(turn) -> (state_block, universe, done, outstanding,
    abandoned)`.  This universe implements both over the SWE suite.

    COMPLETION IS THE EVALUATOR'S VERDICT: `complete(tNN)` is applied
    by the ToolWorld ONLY when `evaluator_passes(fNN)` says the VISIBLE
    suite passes on the agent's CURRENT sandbox tree (designer-side
    re-score via `task_eval` primitives: fresh prepare + the workspace
    module overlaid + score — the same dance `realtools._tool_run_tests`
    runs, never a parse of the prose).  A wrong fix -> the world
    refuses; the ledger records verdicts, it does not define them.

    THE HELD-OUT SIDE never crosses this seam: `_rescore` returns the
    VISIBLE outcome only.  The held-out verdict is the DESIGNER's
    instrument (C22b/C22c), read once at run end (`swe_final_score`)
    from a separate evaluator pass, and no code path on the agent's
    side touches it.
    """

    def __init__(self, targets: dict | None = None, *, evaluator=None,
                 sandbox_of=None):
        self.targets = dict(targets if targets is not None
                            else SWE_QUEUE_TARGETS)
        self._specs = _swe_specs()
        #: the completion gate: fNN -> bool (visible-suite PASS on the
        #: agent's current tree).  INJECTED (`evaluator_passes` below
        #: builds the default over task_eval primitives); the universe
        #: never constructs its own scorer (the R5 discipline).
        self._evaluator_passes = evaluator
        #: the harness's ToolHarness whose workspace holds the agent's
        #: current tree (the score reads THAT tree, not the suite's).
        self._sandbox_of = sandbox_of
        #: THE OPEN SET, carried (not replayed): target -> the turn it
        #: was COMPLETED on (evaluator PASS); a target not in it is
        #: outstanding.  One dict, mutated only by `complete`.
        self.completed: dict = {}
        #: every (target, turn, verdict) the gate ever returned — the
        #: designer's own record of what the world answered.
        self.gate_log: list = []

    # -- the ToolWorld seam ---------------------------------------------
    def step(self, turn: int) -> tuple:
        return self.step_detail(turn)[:2]

    def step_detail(self, turn: int) -> tuple:
        rev = {v: k for k, v in self.targets.items()}
        outstanding = tuple(sorted(
            (rev[t] for t in self.targets.values()
             if t in self._specs and t not in self.completed),
            key=_task_sort_key))
        done = tuple(sorted(
            (rev[t] for t in self.targets.values() if t in self.completed),
            key=_task_sort_key))
        lines = []
        for name in self.targets.values():
            spec = self._specs.get(name)
            if spec is None:
                continue
            f = rev[name]
            if f in self.completed:
                lines.append(
                    f"{f} ({name}): COMPLETED (evaluator PASS) on turn "
                    f"{self.completed[f]}.")
            else:
                lines.append(f"{f} ({name}): OPEN — the requirement "
                             f"below is yours to satisfy.")
                req = spec.requirement.strip()
                lines.append(f"--- requirement {f} ---\n{req}\n"
                             f"--- end requirement {f} ---")
        state_block = "\n".join(lines)
        universe = frozenset(done) | frozenset(outstanding)
        return (state_block, universe, done, outstanding, None)

    # -- the world's own mutation (the effect calls this) ----------------
    def complete(self, f: str, turn: int) -> str:
        """The completion gate: run the evaluator on the agent's
        CURRENT tree and apply-or-refuse.  Returns the verdict string
        for the effect record (`PASS` -> applied, else the refusal)."""
        if f not in self.targets:
            return "not_a_target"
        if f in self.completed:
            return "already_complete"
        verdict = self._gate(f)
        self.gate_log.append({"target": f, "turn": int(turn),
                              "verdict": verdict})
        if verdict == "PASS":
            self.completed[f] = int(turn)
            return "PASS"
        return verdict

    def _gate(self, f: str) -> str:
        if self._evaluator_passes is None:
            return "no_evaluator"
        try:
            ok = bool(self._evaluator_passes(f))
        except Exception as exc:            # noqa: BLE001 — the world's
            # answer is typed, never a crash of the turn
            return f"evaluator_error:{type(exc).__name__}"
        return "PASS" if ok else "FAIL"

    def render_open(self, turn: int) -> str:
        """The worksheet line (the environment's own channel): every
        target not yet evaluator-passed."""
        outstanding = self.step_detail(turn)[3]
        if not outstanding:
            return ""
        return ("Open tasks (offered, not completed — completion is the "
                "evaluator's verdict): " + ", ".join(outstanding) + ".")


def evaluator_passes(tasks_root: str, task_map: dict, harness) -> callable:
    """THE DEFAULT COMPLETION GATE (designer-side, built here because
    the mechanism must not own its own scorer — R5): re-score the
    agent's CURRENT sandbox tree with the REAL evaluator and return
    whether the VISIBLE suite passes.

    Same dance `realtools._tool_run_tests` runs — fresh `prepare`
    (pristine copy, heldout excluded, netns, group-kill timeout), the
    harness workspace's module overlaid (the scored surface is the
    module under repair as the agent currently has it), `score`, then
    the workspace is discarded.  The HELD-OUT outcome is computed by
    the same `score` call but is NOT returned: this function answers
    the visible question only (the held-out side stays designer-only,
    `swe_final_score`)."""
    import task_eval

    ev = task_eval.TaskEvaluator(tasks_root, root=harness.scoring,
                                 timeout=harness.run_timeout,
                                 python=harness._python_arg,
                                 network=harness._network_mode,
                                 axes=_swe_axes())

    def _passes(f: str) -> bool:
        task = task_map.get(f)
        if not task:
            return False
        spec = ev.by_name.get(task)
        if spec is None:
            return False
        ws = ev.prepare(task)
        try:
            dst = os.path.join(ws.path, spec.module)
            src = os.path.join(harness.workspace, f, spec.module)
            if os.path.isfile(src):
                import shutil
                shutil.copy2(src, dst)
            elif os.path.exists(dst):
                os.remove(dst)
            evaluation = ev.score(ws)
        finally:
            if not harness.keep:
                import shutil
                shutil.rmtree(ws.sandbox_root, ignore_errors=True)
        return bool(evaluation.visible.ok)

    return _passes


def swe_final_score(tasks_root: str, task_map: dict, harness) -> dict:
    """THE DESIGNER'S OWN HELD-OUT READING (C22b/C22c), run ONCE at the
    end of a cell: both suites on the agent's final tree, per target.
    THE ONLY sanctioned reader of the held-out outcome on this loop —
    the summary carries it under `swe_final` and nothing on the
    agent's side (prompt, tool reply, worksheet) ever shows it.

    `require_sealed=True` (the smoke's defect 2, 2026-10-01): with no
    sealed held-out definition this scorer used to run UNSEALED and
    report TASK_COMPLETE_ONLY — a verdict that cannot distinguish
    "held-out FAILED" from "held-out never pinned", which is exactly
    the state the smoke ran in (MEASURED: every smoke verdict carried
    sealed=False).  A DV that cannot say which state it is in must
    not report a verdict: the scorer REFUSES instead."""
    import task_eval

    ev = task_eval.TaskEvaluator(tasks_root, root=harness.scoring,
                                 timeout=harness.run_timeout,
                                 python=harness._python_arg,
                                 network=harness._network_mode,
                                 axes=_swe_axes(),
                                 require_sealed=True)
    out = {}
    import shutil
    for f, task in sorted(task_map.items()):
        spec = ev.by_name.get(task)
        if spec is None:
            continue
        ws = ev.prepare(task)
        try:
            dst = os.path.join(ws.path, spec.module)
            src = os.path.join(harness.workspace, f, spec.module)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.exists(dst):
                os.remove(dst)
            evaluation = ev.score(ws)
        finally:
            if not harness.keep:
                shutil.rmtree(ws.sandbox_root, ignore_errors=True)
        out[f] = evaluation.to_json()
    return out


def swe_heldout_fraction(final: dict) -> dict:
    """THE FINER DV (the p3-instr fix, T2): the held-out suite's PASS
    FRACTION per task — `len(heldout.passed) / len(heldout.collected)`,
    a CONTINUOUS 0..1 per target, summed to a 0..len(targets) scale —
    read BESIDE the coarse ordinal verdict, never instead of it.

    THE SAME INSTRUMENT AT FINER GRANULARITY: `final[f]["heldout"]`
    carries the passed/collected nodeids already (SuiteOutcome.to_json);
    a task that passes 6 of 11 held-out tests scores 6/11 (0.5454...)
    where the coarse verdict read NOT_COMPLETE (0.0) — the variance the
    deciding set's sd 2.58 lives in, now measurable per task.

    THE COARSE VERDICT ORDINAL IS UNCHANGED (the SECONDARY reading —
    it alone carries the class-(C) USEFUL/TASK_COMPLETE_ONLY axis).
    This function only ADDS the continuous score beside it.

    THE DEGENERATE CASE, EXPLICIT: a task whose held-out suite
    COLLECTED ZERO tests has NO fraction — reported as None (its own
    case, counted in `n_null_tasks`), NEVER 0/0 read as 0.0.  A
    collected-but-zero-passed suite IS a real 0.0 (all held-out tests
    failed) and is scored 0.0 — the two are distinguishable because
    the former's `collected` is empty and the latter's is not."""
    per = {}
    for f, e in sorted((final or {}).items()):
        ho = (e or {}).get("heldout") or {}
        collected = ho.get("collected") or []
        passed = ho.get("passed") or []
        if not collected:
            per[f] = None          # no fraction: never 0/0
        else:
            per[f] = len(passed) / float(len(collected))
    fractions = [v for v in per.values() if v is not None]
    return {
        "per_target": per,
        "sum": (sum(fractions) if fractions else 0.0),
        "n_targets": len(per),
        "n_null_tasks": sum(1 for v in per.values() if v is None),
        "scale_note": ("CONTINUOUS 0..len(targets): the held-out pass "
                       "fraction per task (len(passed)/len(collected)), "
                       "summed; None = the task's held-out suite "
                       "collected zero tests (explicit, never 0/0).  "
                       "The coarse verdict ordinal is UNCHANGED and "
                       "rides `dv` beside this."),
    }


def dv_rate_per_window(gate_log: list, n_rows: int, *,
                        window: int) -> dict:
    """THE PRIMARY DV (P3-PREREG's 2026-10-05 amendment; handoff-p3-span
    plan item (B)): the DECLARED-COMPLETION RATE PER WINDOW, read over
    the world's own completion ledger.

    WHAT IT READS: `swe.gate_log` — the world's own record of every
    (target, turn, verdict) the EVALUATOR answered at declaration time
    on the tree as it then stood (SWETaskUniverse.complete: no
    self-report anywhere in the chain).  Per window w of `window`
    turns, the rate is the count of declared COMPLETIONS (verdict
    PASS) landing in that window's turn range.

    WHY A RATE AND NOT THE END-STATE SUM (the blocking finding, stated
    in the amendment): the 3-task suite's end-sum decided before the
    mechanism could act — D0 declared all three targets by turn 10 of
    20 and the remaining 40 turns measured only depletion with no work
    left to affect (a guaranteed null).  A per-window RATE can
    DEGRADE: a run completing 3 targets in window 1 and 0 in window 3
    shows the degradation the claim names; the end-sum reads both
    cells identically.

    THE SAME INSTRUMENT IN EVERY ARM, BY CONSTRUCTION: the ledger is
    world-adjudicated and arm-blind — no arm's configuration reaches
    `gate_log` (the evaluator scores the tree; the verdicts are typed).
    What it CANNOT see: un-declared competence (a module repaired to
    visible-PASS with no `complete(fNN)` call is invisible here —
    that is `swe_final_score`'s half, the SECONDARY reading, which
    alone carries the class-(C) USEFUL/TASK_COMPLETE_ONLY axis), and
    refusals (a FAIL verdict is a DECLARATION, not a completion, so it
    does not enter the rate; the declared/competent ratio — F14 — is
    reported per arm beside it, never folded in).

    NO EVENT-TIME SEAT (author decision, stated in the amendment):
    turns-to-first-PASS is DROPPED — under a queue the first
    completion is near-guaranteed early in every arm, so it has no
    discriminating power."""
    window = int(window)
    n_rows = int(n_rows)
    if window <= 0:
        raise ValueError("window must be positive")
    n_windows = n_rows // window
    passes = [g for g in (gate_log or ())
              if g.get("verdict") == "PASS"]
    per_window = []
    for w in range(1, n_windows + 1):
        lo, hi = (w - 1) * window + 1, w * window
        per_window.append(sum(
            1 for g in passes if lo <= int(g.get("turn", 0)) <= hi))
    incomplete = sum(
        1 for g in passes
        if int(g.get("turn", 0)) > n_windows * window)
    # THE WINDOW-GRADIENT (the pre-registered statistic): late rate
    # minus window-1 rate, per cell — positive = the rate FELL across
    # the run (degradation); negative = it rose.  None when there are
    # fewer than 2 complete windows (INSUFFICIENT, never smoothed).
    gradient = (None if n_windows < 2 else
                per_window[0] - per_window[-1])
    return {
        "instrument": "declared-completion rate per window (world-"
                      "adjudicated gate_log; P3-PREREG 2026-10-05)",
        "window": window, "windows": n_windows,
        "completions_per_window": per_window,
        "completions_late_minus_first": gradient,
        "total_declared_completions": len(passes),
        "declared_completions_past_last_window": incomplete,
        "status": ("INSUFFICIENT" if n_windows < 1 else "READ"),
    }


def reconstruction_cost_series(recon_readings: list, *, gate_log: list,
                               n_rows: int, horizon_turns: int) -> list:
    """THE FORM-B COST SERIES (the p3-cost seat, T2): one row per
    reconstruction call — the CUMULATIVE self-maintenance cost to date
    and the WORK IN THE NEXT WINDOW — so a reader answers "as the
    accumulated cost grew, did the next window's work fall?" without
    re-deriving anything.

    COST, IN THE ENDPOINT'S OWN UNITS: `eval_count` (output tokens)
    summed ACROSS calls.  A call whose eval_count is None (a fixture's
    injected closure, or an endpoint body that omits the field) adds
    NOTHING to the cumulative — its own row states the absence; the
    cumulative is never smoothed over it.

    WINDOW, DEFINED: for the i-th call, the turns AFTER this call's
    turn and AT/BEFORE the next call's turn (or the run's end —
    `horizon_turns` — for the last call; the eval turns the run
    actually produced, `n_rows`, when a cell stopped early).  Work =
    gate_log PASS verdicts in the window, plus the window's own bounds
    and length so a rate is derivable.

    MECHANICAL, THROUGH SHARED RESOURCES (the licence, same convention
    as the summary's `cost_licence`): the series records co-movement,
    and the cost it records is real spend on shared resources —
    generation, window occupancy and time (MEASURED: the reconstruction
    calls are ~48% of a probe run's entire generation, on a ~2x larger
    window).  No ARTIFICIAL budget subtraction is built anywhere.

    UNSTAMPED CALLS (turn None — the hook had not stamped them when
    the summary was built, i.e. the call landed after the last row):
    the entry keeps its cost fields and states `window_turns: 0` with
    a note — the honest "call made, work window empty" reading, never
    a dropped row."""
    horizon = max(int(horizon_turns), int(n_rows))
    cumulative = 0
    out = []
    stamped = [r for r in (recon_readings or [])
               if isinstance(r, dict)]
    for i, r in enumerate(stamped):
        ev = r.get("eval_count")
        ev = ev if isinstance(ev, int) else None
        if ev is not None:
            cumulative += ev
        turn = r.get("turn")
        turn = int(turn) if isinstance(turn, int) else None
        next_turn = None
        for j in range(i + 1, len(stamped)):
            nt = stamped[j].get("turn")
            if isinstance(nt, int):
                next_turn = int(nt)
                break
        if turn is None:
            lo = hi = None
            note = ("turn not stamped (the call landed after the last "
                    "row); no work window")
        else:
            lo, hi = turn + 1, (next_turn if next_turn is not None
                                else horizon)
            if hi < lo:
                hi = lo - 1        # the empty window at a stopped run
            note = None
        work = (0 if lo is None else sum(
            1 for g in (gate_log or [])
            if g.get("verdict") == "PASS"
            and lo <= int(g.get("turn", 0)) <= hi))
        out.append({
            "call": i + 1,
            "turn": turn,
            "eval_count": ev,
            "cum_eval_count": cumulative,
            "prompt_chars": r.get("prompt_chars"),
            "thinking_chars": r.get("thinking_chars"),
            "returned_chars": r.get("returned_chars", 0),
            "window": {"lo_turn": lo, "hi_turn": hi,
                       "turns": (0 if lo is None else max(
                           0, hi - lo + 1))},
            "work_in_window": work,
            "note": note,
        })
    return out


def surface_task_health(rows: list, swe, harness, *,
                        window: int = TAU_S_TURNS) -> dict:
    """THE WIRED SURFACE'S TASK-HEALTH GATE (the smoke's defect 1,
    2026-10-01).  WHICH SURFACE EACH GATE READS:
      * `exp_longhorizon.task_health` (paper 2's gate, UNTOUCHED and
        still the control surface's instrument) reads
        `talking_applied` — the ledger of the OLD synthetic worksheet
        (`complete(tNN)`), which on the SWE surface is ~0 BY
        CONSTRUCTION, so it reported INSUFFICIENT on every smoke cell
        while the agent made up to 85 tool calls (an instrument
        artifact, not a finding).
      * THIS gate reads the instruments the SWE surface actually uses:
        the real tool surface (`harness.history`, realtools' own
        ledger — every block parsed and answered, refusals included)
        and the SWE ledger (`swe.completed`, `swe.gate_log`).
    The question is the SAME one (LH's own wording): is the work
    really being done, or has the run an obedience-limited 'no
    collapse'?  Per COMPLETE window: the agent acted through the tool
    surface (>= 1 tool call) AND the world answered work (>= 1
    completion-gate verdict, `gate_log`).  Can FAIL and can say
    INSUFFICIENT (a run with no complete window, and a run with no
    tool activity at all — the stopped campaign's lesson: an
    obedience limit is a real finding, and this gate must be able to
    name it)."""
    n = len(rows) // int(window) if window else 0
    if n == 0:
        return {"status": "INSUFFICIENT", "surface": "tool/swe",
                "windows": 0,
                "note": "no complete window — the gate cannot read a "
                        "partial window"}
    hist = list(getattr(harness, "history", ()) or ())
    gate_log = list(getattr(swe, "gate_log", ()) or ())
    calls_per_window = []
    verdicts_per_window = []
    for w in range(1, n + 1):
        lo, hi = (w - 1) * int(window) + 1, w * int(window)
        calls_per_window.append(
            sum(1 for r in hist if lo <= int(r.turn) <= hi))
        verdicts_per_window.append(
            sum(1 for g in gate_log if lo <= int(g.get("turn", 0)) <= hi))
    ok = all(c >= 1 and v >= 1
             for c, v in zip(calls_per_window, verdicts_per_window))
    note = None
    if not ok:
        dead = [w + 1 for w, (c, v) in enumerate(
                    zip(calls_per_window, verdicts_per_window))
                if c < 1 and v < 1]
        idle = [w + 1 for w, c in enumerate(calls_per_window) if c < 1]
        note = ("at least one window made NO tool calls and raised no "
                "completion verdict — the task was abandoned there "
                f"(windows {dead}; no tool activity in {idle}), and "
                "any collapse reading over that window is "
                "obedience-limited")
    return {"status": ("OK" if ok else "NOT_OK"), "surface": "tool/swe",
            "windows": n,
            "tool_calls_per_window": calls_per_window,
            "gate_verdicts_per_window": verdicts_per_window,
            "tool_calls_total": len(hist),
            "targets_completed": len(getattr(swe, "completed", {})
                                     or {}),
            "note": note}


# ==========================================================================
# THE MEMORY REGIMES (both selectable — the CONFIG FIELD, never a
# constant; the second factor of the claim's arms)
# ==========================================================================

class EngineeredMemoryDMN:
    """THE ENGINEERED REGIME'S EMITTER — the priced-reconstruction
    forwarder.  This class lived in `exp_longhorizon` until the costfix
    pass REMOVED the engineered arm from THAT experiment (correctly:
    there it is not a control — it changes the memory regime AND the
    monitoring cause at once, and `exp_longhorizon.LH_MEMORY_REGIME`
    now states a single naive condition with a guard).  It belongs HERE
    instead, and `exp_longhorizon` says so in its own words: the
    engineered priced reconstruction "is the long-horizon WORKER's
    differentiator, i.e. paper 3's product claim" — and this module IS
    paper 3's harness, where the memory regime is the SECOND FACTOR of
    the arms.  `retrieval.py` itself is untouched and the priced seat
    is wired in the harness config (`retrieval_priced=True` in
    `LH.build_cfg`): the SELF is installed into the store and re-read
    through the priced reconstruction; the prompt stays (nearly)
    constant; NO transcript accumulates.  A pure forwarder, named so
    the record says which regime a run used."""

    def __init__(self, inner):
        self.inner = inner
        self.predicates = inner.predicates
        self.commitment_predicates = inner.commitment_predicates
        #: None is the REGIME'S OWN statement: no naive conversation is
        #: carried (the `getattr(emitter, "memory", None)` convention
        #: the hook reads to know which regime ran).
        self.memory = None

    @property
    def world(self):
        return getattr(self.inner, "world", None)

    @property
    def last_inward(self):
        return getattr(self.inner, "last_inward", None)

    @property
    def last_response(self):
        return getattr(self.inner, "last_response", None)

    @property
    def last_prompt(self):
        return getattr(self.inner, "last_prompt", "")

    def __call__(self, turn: int, ctx: dict):
        return self.inner(turn, ctx)


def build_inner(args, arm: str, *, world, summarizer=None):
    """The inner emitter for one arm: ONE generator config — the
    monitoring paragraph is ON in every HARNESS arm (it is NOT a factor
    of the harness's own experiment; the factors are the REGULATOR
    TIMING and the MEMORY REGIME, and the self + task + monitoring
    request are the loop's held conditions) — wrapped by the arm's
    REGIME.

    A PAPER-3 arm (P3_ARMS) selects its own paragraph through the same
    `self_monitoring` keyword (dmn_llm 608): an arm declaring no
    monitoring gets "" — the compatibility gate at dmn_llm 753-754, the
    exact byte-diff arm A of lambda-official ran.  A harness arm (or a
    caller with no P3 spec) keeps `SELF_MONITORING_INSTRUCTION`
    UNCHANGED — the stopped campaign's defect (monitoring ON in every
    arm, so the design could never show monitoring is the cause) is
    fixed by SELECTION, never by removal.

    The naive wrapper is `exp_longhorizon.NaiveMemoryDMN` (one
    implementation of the ordinary-LLM regime, battery-covered there);
    the engineered wrapper is the class above (the forwarder that let
    the priced reconstruction carry the self at a nearly-constant
    prompt).  A live summarizer is built through the inner's own
    transport when none is injected (fixtures inject one)."""
    import dmn_llm
    from actions import ACTION_DECLARED_PREDICATES
    from selfmodel import COMMITMENT_PREDICATES, SELF_PREDICATES
    spec = _p3_spec(arm)
    preds = dict(ACTION_DECLARED_PREDICATES)
    preds.update(SELF_PREDICATES)
    inner = dmn_llm.LLM_DMN(
        api=args.api, model=(args.chat_model if args.api == dmn_llm.CHAT
                             else args.model),
        endpoint=(args.chat_endpoint if args.api == dmn_llm.CHAT
                  else args.endpoint),
        chat_endpoint=args.chat_endpoint,
        num_predict=int(args.num_predict), num_ctx=int(args.num_ctx),
        temperature=float(args.temperature), seed=int(args.seed_base),
        # THE PER-TURN ENDPOINT BOUND, PLUMBED THROUGH — the same seat
        # exp_longhorizon's build_inner has (F10's gap on this loop).
        # It bounds EVERY call this emitter makes: the run turns AND
        # the live summarizer's compaction posts (through
        # `inner.complete_messages`), so one number is the wall-clock
        # bound on a turn in both senses.  The post-hoc refusal for an
        # over-bound turn is the emitter's own (`dmn_llm` 1243/1277)
        # and is untouched.
        timeout=float(getattr(args, "timeout", LA_TIMEOUT_DEFAULT)),
        world=world, predicates=preds,
        commitment_predicates=COMMITMENT_PREDICATES,
        self_dominant=False, task_framing=True,
        brief=LH.CAMPAIGN_BRIEF,
        self_monitoring=(
            dmn_llm.SELF_MONITORING_INSTRUCTION
            if spec is None or spec["monitoring"] else ""),
        elicitation="A0")
    _mem = (spec or {}).get("memory") or INT_ARMS[arm]["memory"]
    if _mem == "naive":
        return LH.NaiveMemoryDMN(inner, summarizer,
                                 num_ctx=int(args.num_ctx),
                                 num_predict=int(args.num_predict),
                                 keep_recent=int(args.keep_recent))
    return EngineeredMemoryDMN(inner)


def wrap_dmn(base, regulator: RegulatorAgent, world):
    """THE INJECTION WRAPPER — the regulator's actuator on the DMN's
    own context channel.  Per turn: call the base emitter, then read
    its compaction event OFF the emitter (the memory regime's own
    record), and once the regulator HAS FIRED, splice the action's
    bytes into the NEXT turn's context.

    THE CHANNEL IS THE ONE THE PROMPT RENDERS: both halves of the
    action ride `ctx["tool_state"]` — the environment's state-block
    channel, the key `_render_prompt` actually renders into the STATE
    block.  A dedicated `external_directive` ctx key would be WRITTEN
    AND NEVER RENDERED on the real path (the generator's prompt has no
    SN->DMN seat), which is the tool_state live-gap class one network
    over — an actuator that cannot reach the prompt does not act.  The
    REGISTER COST, stated: the directive lands inside the STATE block
    rather than a block of its own; its bytes are fixed and its
    position deterministic, and inventing a third prompt seat in
    `dmn_llm` (with its own byte-compat gates) is not this build's
    write.  From the generator's side both halves ARE external input —
    the SN is a separate network, and this is its redirection.

    EVERYTHING ELSE FORWARDS UNCHANGED (the `RecordingDMN` protocol):
    `last_inward` (str = the channel exists; None = it does not),
    `last_universe`, `world`, `predicates`, `commitment_predicates` —
    a wrapper that swallowed any of these would silently demote the
    harness's instruments (the F4 class)."""
    inner = base

    class _RegulatedDMN:
        def __init__(self):
            self.inner = inner
            self.predicates = getattr(inner, "predicates", None)
            self.commitment_predicates = getattr(
                inner, "commitment_predicates", None)
            self.last_injected: dict = {}
            self.injections: list = []

        @property
        def memory(self):
            return getattr(inner, "memory", None)

        @property
        def world(self):
            return getattr(inner, "world", None)

        @property
        def last_inward(self):
            v = getattr(inner, "last_inward", None)
            return v if isinstance(v, str) else None

        @property
        def last_universe(self):
            return getattr(inner, "last_universe", None)

        @property
        def last_response(self):
            return getattr(inner, "last_response", None)

        @property
        def last_prompt(self):
            return getattr(inner, "last_prompt", "")

        def __call__(self, turn: int, ctx: dict):
            ctx = dict(ctx or {})
            act = regulator.action(turn, world)
            if act:
                parts = []
                ext = act.get("external_line", "")
                if ext:
                    parts.append(ext)
                directive = act.get("directive", "")
                if directive:
                    parts.append(f"REGULATOR ({act.get('trigger')}, "
                                 f"turn {act.get('fired_turn')}): "
                                 f"{directive}")
                if parts:
                    ws = str(ctx.get("tool_state", "") or "")
                    ctx["tool_state"] = (
                        f"{ws}\n" + "\n".join(parts) if ws
                        else "\n".join(parts))
                self.last_injected = dict(act, turn=int(turn))
                self.injections.append(dict(self.last_injected))
            else:
                self.last_injected = {}
            return inner(turn, ctx)

    return _RegulatedDMN()


class _ForwardWorld:
    """Forwards `world` (and nothing else) from the emitter chain to the
    harness's universe reader: `_universe_of` re-steps the emitter's
    OWN world at the same turn, and the world here is the SWE universe
    (its `step` is the requirement block + the target set).  A wrapper
    that swallowed it would leave every `complete(fNN)` refused
    `universe_undefined` — the F4 class, one network over."""

    def __init__(self, inner, world):
        self.inner = inner
        self.world = world
        self.predicates = getattr(inner, "predicates", None)
        self.commitment_predicates = getattr(
            inner, "commitment_predicates", None)
        if hasattr(inner, "tools_manifest"):
            self.tools_manifest = inner.tools_manifest

    @property
    def memory(self):
        return getattr(self.inner, "memory", None)

    @property
    def last_inward(self):
        return getattr(self.inner, "last_inward", None)

    @property
    def last_response(self):
        return getattr(self.inner, "last_response", None)

    @property
    def last_prompt(self):
        return getattr(self.inner, "last_prompt", "")

    def __call__(self, turn: int, ctx: dict):
        return self.inner(turn, ctx)

    def _live_reconstructor(self):
        """FORWARDED down the chain (the reconstruct arm's seat):
        `LH.build_cfg` reaches the reconstructor as
        `dmn.inner._live_reconstructor()` — on the wired surface `dmn` is
        the RecordingDMN and `dmn.inner` is THIS wrapper, so a wrapper
        that swallowed the method would make every `inject_regime=
        "reconstruct"` arm die at cfg construction (the F4 class, one
        network over).  Pure delegation; the NAIVE wrapper below owns the
        call, and an engineered regime (which has none) still raises its
        own AttributeError, never a silent None."""
        return self.inner._live_reconstructor()


def _swe_effect(swe: "SWETaskUniverse"):
    """THE EVALUATOR-GATED COMPLETION EFFECT (the `ToolWorld.effect`
    seam, designer-supplied by construction): a `complete(fNN)` intent
    is APPLIED only when the evaluator's VISIBLE suite passes on the
    agent's current tree; every other outcome is a TYPED refusal the
    agent sees on the next turn's worksheet.  The ledger records the
    verdict — it does not define it (the anti-bookkeeping discipline:
    never call bookkeeping a task score)."""
    from actions import EffectRecord

    def _effect(world, action):
        verdict = swe.complete(action.target, int(action.turn))
        if verdict == "PASS":
            return None              # keep the world's own applied record
        return EffectRecord(action_id=action.action_id,
                            target=str(action.target),
                            status="refused",
                            reason=f"evaluator:{verdict}",
                            turn=int(action.turn))
    return _effect


# ==========================================================================
# THE LOOP
# ==========================================================================

def integrated_args(argv=None):
    ap = argparse.ArgumentParser(
        description="the integrated long-horizon agent "
                    "(offline build/self-test; no endpoint)")
    ap.add_argument("--mode", default="plan", choices=("plan", "run"))
    ap.add_argument("--arms", default=",".join(INT_ARMS))
    ap.add_argument("--turns", type=int, default=300,
                    help="turns per run (>= 2 windows at tau_S=100)")
    ap.add_argument("--n", type=int, default=1, help="repeats per arm")
    # THE C11 PER-TURN CEILING.  6 was the fact-lookup substrate's
    # number (every check cost 1); the WIRED surface charges real
    # derivation cost (a lookup miss + the theory's witness depth,
    # after the priced retrieval's own charge), and a ceiling of 6
    # would strangle every derived check into permanent UNCHECKABLE
    # ('budget') debt — the seat would exist and never run.  64 admits
    # the default theory's declared bound (orphan_closure: 64) with
    # headroom; still a knob, never a constant the mechanism reads.
    ap.add_argument("--budget", type=int, default=64)
    ap.add_argument("--num-predict", type=int,
                    default=LH.CAMPAIGN_NUM_PREDICT)
    ap.add_argument("--num-ctx", type=int, default=LH.CAMPAIGN_NUM_CTX)
    ap.add_argument("--keep-recent", type=int, default=4)
    ap.add_argument("--temperature", type=float, default=0.6)
    ap.add_argument("--seed-base", type=int, default=4242)
    ap.add_argument("--engine", default="real",
                    help="stub | real (the wired surface REQUIRES real: "
                         "the CEN's derive path has no rule surface on "
                         "the stub engine)")
    ap.add_argument("--surface", type=lambda s: s.lower() not in
                    ("0", "false", "no", "off"), default=True,
                    help="wire the four prerequisites (True) or run the "
                         "pre-wiring control substrate (False)")
    ap.add_argument("--horizon-t", type=float, default=4000.0)
    ap.add_argument("--outdir", default="")
    # THE TRANSPORT FIELDS (the LH surface, so a fixture builds the
    # inner emitter the same way for both runners; the values name a
    # route, no call is ever made in --plan).
    ap.add_argument("--api", default=LH.dmn_llm.CHAT)
    ap.add_argument("--chat-model", default=LH.dmn_llm.DEFAULT_CHAT_MODEL)
    # THE ENDPOINTS HAVE NO DEFAULT (the live mode's own seat; mirrors
    # exp_longhorizon 1552-1558).  These fields used to carry
    # dmn_llm's own local-address constants as defaults — inherited
    # values would let `--mode run` post to a machine nobody named (the
    # spend guard, `endpoint_refusal`, REFUSES on exactly this).  A
    # caller that DOES want the local constants names them; a fixture
    # builds its emitter with `dmn._post` overridden before any post
    # (the battery's seam), so nothing offline changes.
    ap.add_argument("--chat-endpoint", default="",
                    help="the /api/chat endpoint — REQUIRED for "
                         "--mode run")
    ap.add_argument("--endpoint", default="",
                    help="the /api/generate endpoint — REQUIRED for "
                         "--mode run with --api generate")
    ap.add_argument("--model", default=LH.dmn_llm.DEFAULT_MODEL)
    # THE PER-TURN ENDPOINT BOUND — the same seat exp_longhorizon gained
    # (its battery E1-E4): one number bounds EVERY transport call this
    # loop's emitter makes (the turn itself and the live summarizer's
    # compaction call, which posts through `inner.complete_messages`).
    # Before this seat the loop had NO bound it named — `build_inner`
    # passed no `timeout`, so the emitter ran at `LLM_DMN`'s implicit
    # 300.0 and a hung turn was bounded only by that implicit number
    # (F10's gap: no flag, no record, no way to set the campaign's own
    # 900).  The default NAMES the campaign convention; the argument is
    # handed to `LLM_DMN` verbatim in `build_inner`.
    ap.add_argument("--timeout", type=float, default=LA_TIMEOUT_DEFAULT,
                    help="per-turn endpoint bound in seconds (wall "
                         "clock, re-checked after the call; bounds the "
                         "turn AND the live summarizer's call)")
    # THE TASK-HEALTH WINDOW (the p3-smoke2 finding, 2026-10-02):
    # `surface_task_health` reads only COMPLETE windows, so a run of
    # `turns` yields `turns // window` windows — at the default
    # TAU_S_TURNS = 100, BOTH the 20-turn smoke AND the pre-registered
    # 60-turn run (`60 // 100 = 0`) yield ZERO windows and the gate
    # reads INSUFFICIENT in every cell FOR A WINDOW REASON, never an
    # agent reason (MEASURED, p3-smoke2: 6/6 cells INSUFFICIENT at
    # 18-82 tool calls).  The window is a READING convention over the
    # same rows, so it is a TUNABLE whose default DOES NOT MOVE
    # (TAU_S_TURNS, byte-identical behaviour when the flag is absent);
    # a different window is recorded in the run's identity and
    # summary.  THE HORIZON IS NOT THIS KNOB'S TO RAISE: live cells
    # have died at 34-58 turns, so lengthening the run to reach 100+
    # would gamble the deciding set on the substrate's survival
    # envelope — the WINDOW moves, never the horizon.
    ap.add_argument("--task-window", type=int, default=TAU_S_TURNS,
                    help="the task-health gate's window in turns "
                         "(default TAU_S_TURNS=100, the consolidation "
                         "window; a run shorter than the window reads "
                         "INSUFFICIENT — set it to read complete "
                         "windows off a shorter run)")
    return ap.parse_args(argv)


def identity(args, arm: str) -> dict:
    """The cell's identity: the HARNESS arms differ in the REGULATOR
    FIELD and the MEMORY REGIME ALONE (asserted by the battery's I12 —
    the diff over these dicts is exactly those fields); a PAPER-3 arm
    carries its OWN factor fields beside them (monitoring, the inject
    regime, the grounding/seed seats — the battery's E2), because those
    fields DECIDE whether the DV can exist at all (under inject the
    loss is 0.0 by construction; a run cannot be compared to a
    reconstruct run as if the difference were a result)."""
    a = ALL_ARMS[arm]
    spec = _p3_spec(arm)
    out = {
        "arm": arm, "label": a["label"],
        "regulator": a["regulator"], "memory": a["memory"],
        "turns": int(args.turns), "budget": int(args.budget),
        "num_predict": int(args.num_predict),
        "num_ctx": int(args.num_ctx),
        "keep_recent": int(args.keep_recent),
        # THE SUMMARIZER'S THINKING POLICY, IN THE IDENTITY (the p3-instr
        # fix): the summarization call suppresses the reasoning channel
        # (think=False) because the summarizer is INFRASTRUCTURE —
        # identical in every arm, so its thinking is not the phenomenon.
        # ONE SOURCE: exp_longhorizon.SUMMARIZER_THINK (the seat reads it
        # and this claim records it), so the claim and the behaviour
        # cannot drift.  Recorded so a reader sees the policy changed
        # from the previous set AND that it applies identically to every
        # arm (a different summarizer policy is a different campaign —
        # the project's own rule; this field changes identity_tag, so a
        # resume refuses to cross it).
        "summarizer_think": bool(LH.SUMMARIZER_THINK),
        "temperature": float(args.temperature),
        # THE PER-TURN ENDPOINT BOUND, IN THE RUN'S IDENTITY (the same
        # convention exp_longhorizon's identity carries): the bound
        # decides WHERE A CELL CAN DIE (a refused turn shortens the
        # horizon), so two runs at different bounds are two different
        # measurements and must not compare as one configuration.
        "timeout": float(getattr(args, "timeout",
                                 LA_TIMEOUT_DEFAULT)),
        "seed_base": int(args.seed_base),
        "engine": str(getattr(args, "engine", "real")),
        "surface": bool(getattr(args, "surface", True)),
        "tau_S": TAU_S_TURNS,
        # THE TASK-HEALTH WINDOW, IN THE IDENTITY (the same convention
        # as timeout: a different window is a DIFFERENT READING of the
        # same rows, so two runs at different windows must not compare
        # as one configuration — a reader must not have to infer it).
        # Default TAU_S_TURNS, i.e. today's behaviour when unset.
        "task_health_window": int(getattr(
            args, "task_window", TAU_S_TURNS)),
        # THE TASK QUEUE'S OWN DIGEST (the 2026-10-05 amendment's F11
        # rule: the identity carries the suite version): a 3-target run
        # and a 9-target run are DIFFERENT measurements of the same
        # claim, and a resume must never cross them silently.  The
        # digest covers the target map alone — the sealed definition's
        # own version travels per cell in `swe.heldout_pin`.
        "swe_queue_digest16": hashlib.sha256(json.dumps(
            SWE_QUEUE_TARGETS, sort_keys=True).encode()
        ).hexdigest()[:16],
        "monitoring_para_sha16": hashlib.sha256(
            (dmn_llm.SELF_MONITORING_INSTRUCTION
             if (spec is None or spec["monitoring"]) else ""
             ).encode()
        ).hexdigest()[:16],
        "sn_activation_floor": SN_ACTIVATION_FLOOR,
    }
    if spec is not None:
        # THE PAPER-3 FACTORS, in the identity because they are the
        # arms' OWN variables (a mislabelled run would be
        # indistinguishable from a null result — the inject_regime
        # discipline, exp_longhorizon's own second factor).
        out["paper3"] = {
            "monitoring": bool(spec["monitoring"]),
            "inject_regime": str(spec["inject_regime"]),
            "grounding": bool(spec["grounding"]),
            "seed_absent": bool(spec.get("seed_absent", False)),
        }
    return out


#: The typed outcome for "the reconstruction call consumed its whole
#: generation budget inward and produced no self-description" — the
#: DISTINCT value a row carries so a reader can tell "exhausted
#: inward" from "the call was never made" (a nullable float alone
#: cannot; the seat is a STATUS STRING beside the number).  See
#: `_wrap_reconstructor` for the exhaustive case-split that assigns it.
RECON_EXHAUSTED = "exhausted_inward"

#: ROUTE (b), typed: "the reconstruction call RETURNED content, and
#: the returned text carries NONE of the derivation's seeded steps" —
#: the second route of the same degradation route (a) names (empty
#: content at the budget bound).  MEASURED, runs/p3-d1check
#: (pin 512dd0c, both repeats): 20 calls returned content, self_steps
#: stayed [] from the first compaction to the horizon — the self was
#: rebuilt as prose that is not the derivation.  A DISTINCT constant,
#: never a rewording of RECON_EXHAUSTED (merging the two routes would
#: re-create the single-field ambiguity this pair exists to close).
RECON_CONTENT_WITHOUT_STEPS = "content_without_steps"


def _parse_recon_observables(msg: str) -> dict | None:
    """Parse the exhaustion observables out of the reconstructor's own
    refusal message — the channel the closure's `DMNEndpointError`
    carries them through (the transport's `last_response` is not
    reachable from the harness site that catches it).  Returns None
    when the message is not the no-usable-content refusal (a transport
    error's message names the endpoint, not these fields), so the
    caller can leave the GENUINE failure untouched.
    """
    if "the reconstruction call returned no usable content" not in msg:
        return None
    out = {}
    for key in ("done_reason", "eval_count", "num_predict", "num_ctx"):
        m = re.search(rf"\b{key}=([^,)]+)", msg)
        if m:
            raw = m.group(1).strip().strip("'\"")
            out[key] = (int(raw) if raw.lstrip("-").isdigit()
                        else raw)
    return out


def transport_of_reconstructor(reconstructor):
    """The INNERMOST TRANSPORT a reconstructor closure posts through —
    the p3-cost seat's seam finder.  The live closure
    (`NaiveMemoryDMN._live_reconstructor`) posts via
    `self.inner.complete_messages` where `self` is the NAIVE wrapper —
    and because the closure is NESTED, that `self` rides a CLOSURE
    CELL, not `__globals__` (the module namespace has no `self`; the
    battery's X9 caught exactly this: a globals-only lookup found
    nothing and the cost seat silently recorded None).  Both channels
    are read: the `self` freevar's cell first (the live closure's
    shape), then a module-level `self` (a rebuilt closure's possible
    shape).  From that wrapper, the `.inner` hops (a `_ForwardWorld`,
    a `RecordingDMN`) land on the `LLM_DMN` transport.  Returns None
    when the closure is a fixture's injected callable (no `self`
    reachable, or a `self` with no `.inner` transport) — the cost seat
    then records its fields as None (stated, never guessed) instead of
    failing the run for an instrument's sake.  STRUCTURAL, NOT BY
    NAME: nothing keys on the closure's qualname or module (a renamed
    or rebuilt closure keeps the seat); the attribute WALK is the same
    one the wrapper chain itself defines (`.inner`)."""
    self = None
    try:
        names = reconstructor.__code__.co_freevars
        for i, nm in enumerate(names):
            if nm == "self":
                self = reconstructor.__closure__[i].cell_contents
                break
    except Exception:                                  # noqa: BLE001
        self = None
    if self is None:
        g = getattr(reconstructor, "__globals__", None) or {}
        self = g.get("self")
    tr = self
    hops = 0
    while tr is not None and hasattr(tr, "inner") and hops < 8:
        tr = tr.inner
        hops += 1
    if tr is None or not hasattr(tr, "complete_messages"):
        return None
    return tr


def _capture_complete_messages(self, messages, turn, *, num_predict=None,
                               num_ctx=None, think=None):
    """The p3-cost seat's transport tap (bound as an INSTANCE attribute
    for the DURATION of one reconstruction call by
    `_wrap_reconstructor`, reverted in its `finally`): post through the
    transport's own UNBOUND method byte-identically and copy THIS call's
    return into `self.cost_capture` — the raw body carrying the call's
    own `done_reason`/`eval_count` — plus the prompt's char count (the
    request the call was posted with; `complete_messages` itself stamps
    nothing, by its own documented contract).  Only a CHAT body's
    `done_reason`/`eval_count` are ollama-native; a body without them
    keeps them absent (None downstream — stated, never guessed)."""
    raw = type(self).complete_messages(
        self, messages, turn, num_predict=num_predict, num_ctx=num_ctx,
        think=think)
    cap = getattr(self, "cost_capture", None)
    if isinstance(cap, dict):
        cap["raw"] = (out if isinstance(
            (out := _safe_json(raw)), dict) else None)
        try:
            cap["prompt_chars"] = sum(
                len(str(m.get("content") or ""))
                for m in messages if isinstance(m, dict))
        except Exception:                              # noqa: BLE001
            cap["prompt_chars"] = None
    return raw


def _safe_json(text):
    try:
        return json.loads(text)
    except Exception:                                  # noqa: BLE001
        return None


def _wrap_reconstructor(reconstructor, readings: list):
    """THE EXHAUSTION READING (P3-PREREG's 2026-10-02 amendment; the
    p3-span-smoke finding): ONE seat around the arm's live
    reconstructor that records budget-exhaustion as a READING instead
    of stopping the run, and lets EVERY OTHER failure raise exactly as
    today (the project's rule: a fallback would make the loss
    identically zero — the campaign-3 defect; a swallowed transport
    error would be unattributable).

    THE MECHANISM, MEASURED (runs/p3-span-smoke, 6 cells x
    30 turns, pin b51fb43; re-measured this session off the artifacts):
    every D1 cell DIED at its first compaction with
    `done_reason='length', eval_count=12000 == num_predict=12000`,
    while D0/D1' ran 30/30 turns.  The reconstruction prompt is the
    summary PLUS the kept verbatim run prompts (~31,500 chars ~ 10,500
    tokens at keep_recent=4 — DOUBLE the ~5,100-token run prompt the
    rows' prompt_chars column records), and qwen3.5:9b's THINKING
    SCALES WITH INPUT: a direct probe measured 5,858 thinking tokens
    then CONTENT at 651 chars input, and NO content at ~10.5k input
    (the thinking alone exceeds the whole 12,000 budget).  THE MODEL
    DOES NOT FAIL TO ANSWER — IT CANNOT STOP REASONING: `a` stays
    high, `c` never un-arms, the agent processes inward with no
    outward product.  The exhaustion IS the phenomenon (the model's
    own predicted failure mode), so SUPPRESSING THE THINKING CHANNEL
    WOULD BE WRONG — it would delete the very processing the arm
    exists to exercise (the judge call suppresses it because THAT call
    is a classification; this one is not).

    THE EXHAUSTIVE CASE-SPLIT (which failures are readings, which are
    genuine):
      * the closure's no-usable-content refusal AND
        done_reason == 'length'  ->  THE EXHAUSTION READING: the
        endpoint's OWN statement that generation stopped at the budget,
        with empty content, is the reading's definition; the recorded
        eval_count == num_predict equality is its MEASURED confirmation
        (the live smoke: 12000 == 12000), carried per event for audit
        rather than gating on a token-accounting coincidence.  Recorded,
        the self is genuinely empty ('' — the honest answer, never the
        seed), the run CONTINUES (the agent works on with no self), and
        the reading carries an INWARD SHARE OF 1.0 (all generation, no
        outward product) — the same 0..1 convention as the row's
        `inward_share` instrument.
      * empty content with ANY OTHER done_reason (e.g. 'stop' — the
        model genuinely answered nothing), a malformed answer, a
        transport error, an unreachable endpoint  ->  STILL RAISES,
        verbatim, exactly as before the seat existed.  The refusal
        message is the closure's own; nothing about the genuine-fail
        path is rewritten.

    `readings` is the caller's list; one dict is appended per
    exhaustion event (turn, budget, done_reason, eval_count,
    inward_share) so the row/summary can carry it without the harness
    knowing this seat exists.

    THE SECOND ROUTE (the p3-d1check finding, MEASURED 2026-10-02,
    runs/p3-d1check, pin 512dd0c; both repeats): the call
    can also return NON-EMPTY content that does NOT carry the
    derivation's step structure — the agent restates itself as prose
    while the seeded steps are gone (D1-r1/r2: 20 reconstruction
    calls, ALL returning content per the closure's own case-split
    (return-content or raise; no raise, no exhaustion reading), yet
    `self_steps` is [] from the first compaction to the horizon, in
    both repeats, while D1' restores [1,2,3,4] at every compaction
    after the first).  THAT IS THE SAME DEGRADATION BY ITS SECOND
    ROUTE, not a missed exhaustion: the self was rebuilt as text that
    is not the derivation.  Route (b) is typed
    `RECON_CONTENT_WITHOUT_STEPS` and recorded BESIDE route (a) —
    never instead of it, and never folded into it (two routes that
    one field cannot tell apart was exactly the defect this seat
    closes).  Both routes land in the run-level
    `reconstruction_outcomes` list (see the hook) so the mechanism's
    expression is an OUTCOME a reader of the summary/evaluation sees,
    not a per-row field to hunt for.
    """
    def _reading_reconstruct(text: str) -> str:
        # THE SUCCESS PATH'S COST, CAPTURED (the p3-cost seat, T1).
        # `complete_messages` deliberately does NOT stamp last_response
        # (its own docstring: the caller knows what it posted) — the
        # observables for THIS call exist only as its return value, so
        # the wrapper wraps: for the duration of `reconstructor(text)`
        # the innermost transport's complete_messages is an instance
        # attribute that routes through unchanged AND copies its return
        # into `cost_capture` (reverted in `finally`, so no later call
        # path sees it).  Reverted-None = a reconstructor that never
        # posted through the innermost transport (a fixture's injected
        # closure) — absent is stated, never guessed.
        _tr = transport_of_reconstructor(reconstructor)
        cap: dict | None = ({"raw": None} if _tr is not None else None)
        _prior = _sentinel = object()
        if _tr is not None:
            _tr.cost_capture = cap
            # the tap: an INSTANCE attribute for the call's duration,
            # routing through the transport's own method unchanged
            _prior = _tr.__dict__.get("complete_messages", _sentinel)
            _tr.complete_messages = _capture_complete_messages.__get__(
                _tr, type(_tr))
        try:
            got = reconstructor(text)
        except Exception as exc:                    # noqa: BLE001
            obs = None
            msg = str(exc)
            if isinstance(exc, dmn_llm.DMNEndpointError):
                obs = _parse_recon_observables(msg)
            if (obs is not None
                    and obs.get("done_reason") == "length"):
                # 'length' IS the endpoint's own budget-bound statement
                # (empty content + stopped at the budget).  The recorded
                # eval_count == num_predict is the MEASURED confirmation
                # (the live smoke: 12000 == 12000), carried per event
                # for audit, not a gate — see the case-split above.
                # THE BUDGET IS PART OF THE READING (a different budget
                # is a different measurement — pre-registered as such).
                readings.append({
                    "turn": None,     # the caller stamps the turn
                    "status": RECON_EXHAUSTED,
                    "done_reason": str(obs.get("done_reason")),
                    "eval_count": obs.get("eval_count"),
                    "num_predict": obs.get("num_predict"),
                    "num_ctx": obs.get("num_ctx"),
                    # all generation inward, zero outward product
                    "inward_share": 1.0,
                })
                return ""            # the self is genuinely empty
            raise
        finally:
            if _tr is not None:
                _tr.cost_capture = None
                if _prior is _sentinel:
                    _tr.__dict__.pop("complete_messages", None)
                else:
                    _tr.complete_messages = _prior
        # THE SECOND ROUTE'S RAW RECORD: the call SUCCEEDED, so the
        # only question the outcome list needs answered is whether the
        # returned text carries the derivation's step structure — and
        # that is measured HERE, on the returned bytes, with the same
        # exact-substring probe the rows' `self_steps` uses
        # (`seed_steps_in_text`: the seed's own words, never a
        # paraphrase matcher).  Recorded raw (the route's name is
        # stamped by the hook, which knows the arm's seed context);
        # `restored` is the probe's own answer and is stated per event
        # so a reader never re-derives it from chars alone.
        # THE CALL'S MEASURED COST rides the same entry (the p3-cost
        # seat): eval_count/done_reason off the transport's OWN response
        # for THIS call (None when the closure never posted through the
        # innermost transport — a fixture's injected closure — stated,
        # never guessed), plus prompt_chars (the exact string the call
        # posted, the reconstruction instruction + the compacted
        # conversation) and thinking_chars.  Route (a)'s entry ABOVE is
        # byte-identical to its 512dd0c self.
        _resp = {}
        if cap is not None and isinstance(cap.get("raw"), dict):
            _resp = cap["raw"]
            _msg = _resp.get("message")
            _msg = _msg if isinstance(_msg, dict) else {}
        else:
            _msg = {}
        readings.append({
            "turn": None,             # the caller stamps the turn
            "status": None,           # route (a) has 'exhausted_inward'
            # THE CALL'S OWN OBSERVABLES (the p3-cost seat; None only
            # when no transport posted this call — stated, never
            # guessed — or the endpoint's own body omits the field)
            "done_reason": _resp.get("done_reason"),
            "eval_count": _resp.get("eval_count"),
            "num_predict": None,      # not carried by a response body;
            "num_ctx": None,          # the REQUEST's policy — the hook
                                      # knows the arm's recon policy is
                                      # the run's own num_predict/num_ctx
            # the success path has no inward-share reading (the
            # closure exposes content only; the thinking channel is
            # not carried) — None, stated, never guessed
            "inward_share": None,
            "prompt_chars": cap.get("prompt_chars") if cap else None,
            "thinking_chars": len(str(_msg.get("thinking") or ""))
            if cap is not None else None,
            "returned_chars": len(got or ""),
            "returned_steps": seed_steps_in_text(got or ""),
        })
        return got
    return _reading_reconstruct


def run_integrated_cell(args, arm: str, repeat: int, outdir: str, *,
                        inner=None, summarizer=None,
                        collapse_floor: float | None = None,
                        world=None, theory=None,
                        evidence_seed=None,
                        surface: bool = True) -> dict:
    """ONE cell of the integrated campaign: the DMN + CEN + memory
    regime + plant loop with the regulator wired to the model's
    prediction, run OFFLINE end to end (fixtures drive `inner`; None
    builds the real emitter, whose transport would raise without an
    endpoint — the live mode is not entered here).

    `collapse_floor` is the COLLAPSE arm's DV floor, supplied by the
    CAMPAIGN (derived from the no-regulator arms' own first-window
    means, the LH floor convention) — never invented per run.

    `surface` (DEFAULT True) wires the four prerequisites — the SWE
    task universe, the realtools surface, the injected theory, the
    evaluator-gated completion.  `surface=False` is the CONTROL:
    yesterday's substrate (TaskWorld draws, no tools, no theory, stub
    engine) — the plant bit-identity comparison's other half, and the
    shape pre-wiring fixtures reproduce.  `theory`/`evidence_seed`
    inject the CEN's rules seat and its designer-seeded evidence (the
    same seam the entail battery uses; default `orphan_closure` with
    EMPTY evidence — a stated gap, not a hidden one).

    PER TURN (one harness turn = one loop over everything below):
      1. the DMN emits through the memory regime (naive compaction /
         engineered priced retrieval) and the injection wrapper;
      2. the CEN checks the extracted claims (fact lookup, or the
         DERIVE path through the injected theory), prices the
         retrieval, adjudicates the tool calls against the ToolWorld
         (the EVALUATOR's verdict answers completion);
      3. the plant advances one Stage-1 step on the EMPTY schedule
         (driven by nothing the agent emitted);
      4. the hook reads the turn's instruments, records the compaction
         event's measured derivation loss, recomputes the model's
         prediction ROLLING, hands the DV to the regulator's cheap
         gate, and logs one row.
    """
    a = ALL_ARMS[arm]              # INT_ARMS or P3_ARMS (one registry)
    p3_spec = _p3_spec(arm)        # None for the six harness arms
    # ==== THE QUEUE'S PRE-FLIGHT (the 2026-10-05 amendment): the pin
    # ==== must COVER the queue the run will offer, or the held-out
    # ==== reading silently degrades to TASK_COMPLETE_ONLY for every
    # ==== UNPINNED target — the dvfix smoke's defect 2 (2026-10-01,
    # ==== MEASURED: every verdict carried sealed=False) re-entering
    # ==== through the supply.  `load_definition` refuses a definition
    # ==== that names a task the tree does not have, but a definition
    # ==== that names FEWER tasks than the queue (a stale v1 pin after
    # ==== a suite extension) passes ITS OWN check while leaving the
    # ==== new targets unpinned — exactly the state that must refuse.
    # ==== REFUSE-OR-STATE, never silently score (C22c).
    if surface:
        from task_eval import (DEFAULT_TASKS_ROOT, HeldoutDefinitionError,
                               TaskEvaluator, content_digest)
        _pin_ev = TaskEvaluator(DEFAULT_TASKS_ROOT, axes=_swe_axes())
        try:
            _pin_body, _pin_status = _pin_ev.definition()
        except HeldoutDefinitionError as e:
            raise ValueError(
                f"surface=True REFUSED: the held-out definition "
                f"cannot be authenticated ({e}) — an unauthenticable "
                f"pin is treated as no pin (C22c fail-closed); "
                f"re-publish with `python3 task_eval.py --publish` "
                f"from a trusted tree") from e
        if _pin_status != "sealed":
            raise ValueError(
                "surface=True REFUSED: NO sealed held-out definition "
                f"at {_pin_ev.definition_path}"
                " — the DV is UNARMED (a run would end in "
                "TASK_COMPLETE_ONLY verdicts that cannot distinguish "
                "'held-out FAILED' from 'held-out never pinned'; the "
                "smoke's defect 2).  The designer act is "
                "`python3 task_eval.py --publish`")
        #: the pin this run's held-out reading is sealed under (the
        #: summary's `swe.heldout_pin` records it; the agent side
        #: never sees any of this).
        heldout_pin = {"path": _pin_ev.definition_path,
                       "version": int(_pin_body["version"]),
                       "digest16": content_digest(_pin_body)[:16]}
        # THE COVERAGE CLAUSE (the amendment's F12-adjacent check): the
        # sealed definition must name EVERY task the queue offers — a
        # pin that covers fewer tasks than the suite leaves the rest
        # scoring UNPINNED, and `swe_final_score`'s require_sealed
        # would refuse at RUN END (after the budget was spent) rather
        # than here (before a single turn).  The refusal names the
        # designer act; the check is the same fail-closed direction as
        # the seal itself.
        _pinned = {t["name"] for t in _pin_body.get("tasks", ())}
        _queue = set(SWE_QUEUE_TARGETS.values())
        _unpinned = sorted(_queue - _pinned)
        if _unpinned:
            raise ValueError(
                "surface=True REFUSED: the sealed held-out definition "
                f"({_pin_ev.definition_path}, v{_pin_body['version']}) "
                f"does not cover the task queue — unpinned: "
                f"{_unpinned}.  Those targets' held-out reading would "
                "silently degrade to TASK_COMPLETE_ONLY (the 2026-10-01 "
                "defect re-entering through the supply).  The designer "
                "act is `python3 task_eval.py --publish` over the "
                "extended suite")
    else:
        heldout_pin = None
    turns = int(args.turns)
    os.makedirs(outdir, exist_ok=True)
    rows_path = os.path.join(outdir, "rows", f"{arm}-r{repeat}.jsonl")
    summary_path = os.path.join(outdir, "runs", f"{arm}-r{repeat}.json")
    writer = JsonlWriter(rows_path)
    # ==== THE FOUR PREREQUISITES, WIRED (designer-side construction;
    # ==== the mechanism never builds its own rules, scorer or tools).
    # ==== `surface=False` is the CONTROL: yesterday's substrate
    # ==== (TaskWorld draws, no tools, no theory, stub engine) for the
    # ==== plant bit-identity comparison — the RT13 discipline.
    surface = bool(surface)
    tools = None
    theory = theory
    evidence_seed = tuple(evidence_seed or ())
    if surface:
        # (1) THE TASK UNIVERSE IS THE SWE SUITE: the requirement text
        #     is the state block, and a target leaves the open set only
        #     when the EVALUATOR's visible suite passes on the agent's
        #     own sandbox tree — `complete(fNN)`'s world answer is the
        #     typed verdict, never bookkeeping.
        swe = (world if isinstance(world, SWETaskUniverse)
               else SWETaskUniverse())
        # (2) THE TOOL SURFACE: hax's five tools + run_tests over the
        #     suite's targets, realtools' own fenced carrier and typed
        #     refusals, on a fresh sandbox copy per task.  Admissible
        #     actions stay the caller's (cfg's gate; nothing widened).
        #     THE QUEUE: the harness is constructed over the UNIVERSE'S
        #     OWN target map (the open set the world offers and the
        #     workspace the tools act on are ONE map), so a larger
        #     universe IS a larger queue — no new mechanism.
        import realtools
        from task_eval import DEFAULT_TASKS_ROOT
        tools = realtools.ToolHarness(
            targets=tuple(sorted(swe.targets)),
            task_map=dict(swe.targets),
            tasks_root=DEFAULT_TASKS_ROOT)
        # realtools' own spec discovery (`_spec`) runs the DEFAULT axes
        # table; the queue's registration is merged onto the HARNESS so
        # every spec lookup — run_tests' module, the evaluator's
        # sandbox — answers over the SAME table the universe was
        # built from (one suite, one registration).
        tools._axes = _swe_axes()
        tools._materialise()
        swe._evaluator_passes = evaluator_passes(
            DEFAULT_TASKS_ROOT, dict(swe.targets), tools)
        # (3) THE THEORY: the CEN's derive path, INJECTED (the R5
        #     discipline — never constructed inside the mechanism).
        #     Default `orphan_closure` with EMPTY evidence (NOT_BUILT's
        #     stated gap); `evidence_seed` is the designer seeding the
        #     world's evidence relations on the engine, the same seam
        #     the entail battery uses.  The stub engine has no
        #     `query_rules`, so a theory REQUIRES the real engine —
        #     refused loudly, never silently degraded to lookup.
        if theory is None:
            from entail import orphan_closure
            theory = orphan_closure()
        if str(getattr(args, "engine", "real")) != "real":
            raise ValueError(
                "surface=True needs engine='real': the CEN's derive "
                "path (entail.Theory) has no rule surface on the stub "
                "engine, and a theory that cannot run is a silent "
                "degradation, not a seat — REFUSED (wire --engine real "
                "or surface=False for the control)")
        run_world = swe
    else:
        # THE CONTROL: yesterday's substrate, byte-for-byte the old
        # construction (TaskWorld draws; no tools; no theory; stub
        # engine allowed) — what the plant-identity comparison runs
        # against, and what a pre-wiring fixture reproduces.
        run_world = (world if world is not None else dmn_llm.TaskWorld(
            seed=LH.WORLD_SEED))
        theory = None
        swe = None
    regime = (inner if inner is not None
              else build_inner(args, arm, world=run_world,
                               summarizer=summarizer))
    emitter = (_ForwardWorld(regime, run_world) if surface else regime)
    rec = RecordingDMN(emitter, predicates=emitter.predicates,
                       commitment_predicates=emitter.commitment_predicates)
    # ==== THE MEMORY FORWARD (an audit finding, wired for the PAPER-3
    # ==== arms ONLY — see the audit table): the harness reaches the
    # ==== naive memory as `cfg.dmn.inner.memory` (stage2_harness 1534,
    # ==== 3049 — ONE `.inner` hop), and `cfg.dmn` here is the wrapper
    # ==== chain whose first `.inner` is the RecordingDMN, which does
    # ==== NOT forward `memory`.  Consequence for the SIX HARNESS ARMS:
    # ==== the compaction-triggered self refresh (3052-3055) is LATENT
    # ==== on this loop — the derivation is never restored
    # ==== post-compaction, so the inject default is UNEXERCISED at
    # ==== that site for them (their standing-loss readings stay
    # ==== non-zero, which I3's firing depends on).  That is TODAY'S
    # ==== behaviour and is KEPT BYTE-EXACTLY: the forward is gated on
    # ==== the arm's spec.  A PAPER-3 arm wires it — and NEEDS it:
    # ==== D1's reconstruct arm reads `_conversation_text()` through
    # ==== exactly this hop, and D1' is the arm whose inject default
    # ==== MUST actually restore (the pure-carrier control's losses are
    # ==== 0.0 by construction because the harness hands the derivation
    # ==== back, not because the site was dead).  A plain INSTANCE
    # ==== attribute (the class is not this file's to patch); an
    # ==== engineered regime yields None, which is that regime's own
    # ==== statement, preserved.
    if p3_spec is not None and not hasattr(RecordingDMN, "memory"):
        rec.memory = getattr(regime, "memory", None)
    # ==== THE ARM'S SPEC -> THE HARNESS CONFIG (defect 1's fix, and
    # ==== the whole difference between a scaffold and an experiment).
    # ==== A HARNESS arm passes NO spec (today's bytes EXACTLY:
    # ==== build_cfg's own defaults — inject_regime "inject", the
    # ==== grounding bundle ON — so the six arms and every existing
    # ==== caller keep today's behaviour and `derivation_loss` still
    # ==== reads 0.0 there, as designed for them).  A PAPER-3 arm
    # ==== passes its spec: the arm CHOOSES the inject regime, so D1
    # ==== reconstructs (a NONZERO loss can exist) and D0 turns the
    # ==== seat off through the grounding path.  The "inject" default
    # ==== itself is UNTOUCHED in build_cfg — a caller that passes no
    # ==== spec keeps it.
    cfg = LH.build_cfg(args, rec, outdir=outdir, world=run_world,
                       spec=p3_spec)
    # ==== THE EXHAUSTION READING'S SEAT (additive; see
    # ==== `_wrap_reconstructor`): ONLY the reconstruct arm's
    # ==== reconstructor is wrapped — D0/D1' pass no reconstructor and
    # ==== every harness arm keeps build_cfg's own None, so today's
    # ==== bytes are unchanged everywhere else.  `recon_readings` is
    # ==== the seat's own record; the hook stamps the turn onto new
    # ==== entries and writes the row fields below.
    recon_readings: list = []
    if (p3_spec or {}).get("inject_regime") == "reconstruct" \
            and cfg.reconstructor is not None:
        cfg.reconstructor = _wrap_reconstructor(cfg.reconstructor,
                                                recon_readings)
    if surface:
        cfg.tools = tools
        cfg.tool_effect = _swe_effect(swe)
        # cfg.action_source is already `run_world` (build_cfg) = the
        # SWE universe: the ToolWorld's offered set, open set and
        # worksheet all read ONE source.
        # THE MANIFEST SEAT: cfg.dmn is the wrapper chain, so the
        # harness's own hand-off would write a dead attribute — set it
        # on the INNERMOST emitter (the LLM_DMN whose _render_prompt
        # reads it); fixtures that render ctx themselves read it too.
        _innermost = emitter
        while hasattr(_innermost, "inner"):
            _innermost = _innermost.inner
        if getattr(_innermost, "tools_manifest", None) in (None, ""):
            _innermost.tools_manifest = tools.manifest()
    # THE PLANT'S OWN SCHEDULE, frozen and untouched: every exogenous
    # channel 0 for the whole horizon (the plant is its own no-drive
    # baseline; nothing the agent emits reaches a_hold — asserted by
    # the battery's I8 across arms).
    sch = Schedule(channels={
        "a_hold": [(0.0, float(turns) + 1.0, 0.0)],
        "A": [(0.0, float(turns) + 1.0, 0.0)],
        "u_ext": [(0.0, float(turns) + 1.0, 0.0)],
    })
    p = Params()

    base_mem = getattr(regime, "memory", None)   # None = engineered
    # THE SEAT'S INITIAL PREDICTION is the MODEL'S no-events answer
    # (`predict_crossing_from_events([])`: no loss has landed, so the
    # model predicts NO crossing and the early arm cannot fire).  That
    # is the honest initial condition — not a placeholder: until a
    # compaction event lands, the model's prediction IS "no crossing",
    # and a seat that fired before its model had anything to say would
    # be measuring the wiring, not the timing.  The hook REPLACES it
    # rolling as events land.
    initial_pred = (None if a["regulator"] != "prediction"
                    else lh_model.predict_crossing_from_events(
                        [], tau_S=TAU_S_TURNS,
                        horizon_t=float(args.horizon_t)))
    reg = RegulatorAgent(a["regulator"],
                         prediction=initial_pred,
                         collapse_floor=collapse_floor)
    # THE WORLD HOLDER: the seat renders external content from the
    # run's OWN ToolWorld; the hook points it there on turn 1 (the
    # harness constructs the world inside run_stage2 — see the holder).
    world_holder = _WorldHolder()
    dmn = wrap_dmn(rec, reg, world_holder)
    cfg.dmn = dmn
    state = {"t_prev": time.time(), "rows": [], "secs": [],
             "prev_compaction_turn": None}
    loss_events: list = []
    last_prediction = None
    cen_verdicts: list = []
    # THE MEDIATOR'S EVENT ORDINAL (the survival-pair fix, P3-PREREG's
    # 2026-10-05 amendment): 0 before the first compaction, then the
    # 1-based index of each event.  The FIRST post-seed event is the
    # seed's OWN single-turn spend — it fires in BOTH seat-on regimes
    # (`_regenerate_self_block` runs on the first compaction whatever
    # the inject_regime), so its survival pair conflates "the seed was
    # spent" with "the regime failed to restore it" and the
    # pre-registered S5 gate could not pass as written (MEASURED,
    # p3-smoke2: derivation_loss read 1.0 in D1' where the prereg
    # required 0.0 — F6 firing spuriously).  From the SECOND event on,
    # the regimes DIVERGE (inject re-enters the derivation through the
    # PROMPT, so it survives in the memory's span; reconstruct must
    # produce it and cannot) — that is where the pair is READ.
    compaction_ordinal = {"n": 0}
    # THE EXHAUSTION READING'S CURSOR: how many readings the rows have
    # already consumed (the wrapper appends DURING a turn, the hook
    # stamps the turn and writes the row at that turn's end).
    state["recon_read"] = 0

    def hook(turn: int, st) -> bool:
        nonlocal last_prediction
        now = time.time()
        secs = now - state["t_prev"]
        state["t_prev"] = now
        row = st.log[-1]
        if world_holder.world is None and st.toolworld is not None:
            world_holder.world = st.toolworld
        gen = rec.by_turn.get(int(turn), {})
        mem = getattr(rec.inner, "memory", None)
        # THE MEMORY REGIME'S OWN EVENT, read off the emitter (one
        # source; the wrapper forwards nothing but the call).  The
        # event carries the measured survival pair BOTH sides; the
        # module that turns it into the model's term is lh_model.
        # READ OFF THE REGIME (the innermost holder of last_compaction
        # is the naive wrapper itself — the _ForwardWorld wrapper and
        # the regulated wrapper sit ABOVE it and forward nothing).
        _regime = regime
        last_ev = getattr(_regime, "last_compaction", None)
        ev_loss_local = None
        ev_loss_standing = None
        if last_ev is not None:
            ev_loss_local = lh_model.derivation_loss(
                last_ev.self_steps_before, last_ev.self_steps_after)
            # THE SEAT-OFF ZERO (the amendment's S12): D0 has NO self to
            # lose — no seed was ever installed — so standing_loss over
            # its (always-empty) after-pair is 0.0 BY THE ARM'S OWN
            # CONSTRUCTION, and reading it as `1 - 0/4 = 1.0` (the
            # p3-smoke2 defect: standing_loss read 1.0 in D0, "a cell
            # with NO self to lose") inverts the instrument: the
            # no-depletion reference arm read as MAXIMALLY depleted.
            # The seed is installed by the GROUNDING bundle; a cell
            # whose arm has no seed has nothing standing to lose, and
            # the instrument says so instead of measuring the void.
            # (Harness arms and both seat-on P3 arms keep lh_model's
            # own arithmetic UNCHANGED.)
            _has_seed = not (p3_spec is not None
                             and not p3_spec.get("grounding"))
            ev_loss_standing = (
                0.0 if not _has_seed
                else lh_model.standing_loss(last_ev.self_steps_after))
            loss_events.append((int(last_ev.turn), ev_loss_standing))
            _regime.last_compaction = None
        # THE PREDICTOR -> REGULATOR EDGE, ROLLING.  The prediction is
        # recomputed when a NEW EVENT lands and handed to the seat (the
        # EARLY arm reads ONLY this object — lh_model's signature is
        # the circularity guard; the DV reaches the seat only through
        # observe() below, and only in the COLLAPSE arm).
        #
        # RECOMPUTED ON A LEVEL CHANGE, EXACTLY: the model's schedule
        # is the STEP FUNCTION the events dictate (`lh_model.
        # _loss_schedule` — each event's level held until the next
        # event), and appending an event whose STANDING LOSS EQUALS the
        # previous event's leaves that function IDENTICAL (the two
        # spans join; a zero-level event adds no span at all).  So the
        # recompute is gated on the level actually changing — not a
        # cache of convenience, an identity, and it keeps the per-turn
        # cost O(1) in the number of events (a fresh ODE integration
        # per EVENT would grow without bound over a long horizon,
        # which is the regime this module exists for).
        if last_ev is not None:
            level = loss_events[-1][1]
            if (not loss_events[:-1]
                    or loss_events[:-1][-1][1] != level):
                last_prediction = lh_model.predict_crossing_from_events(
                    list(loss_events), tau_S=TAU_S_TURNS,
                    horizon_t=float(args.horizon_t))
            if reg.mode == "prediction" and not reg.fired:
                reg.prediction = last_prediction
        # THE DV (CEN-side and extractor-side, never the DMN's
        # self-report): outward content is the emitted stream's size.
        content_chars = int(gen.get("content_chars", 0) or 0)
        # THE CHEAP GATE — one O(1) call per turn.
        fired_now = reg.observe(turn, content_chars)
        # THE CEN'S OWN VERDICTS THIS TURN (read off the last TurnRecord:
        # status, reason, provenance, cost — the derive path's evidence
        # lives HERE, not in the log row's counts).  Recording for the
        # run's own record; the battery reads it for the derive tests.
        _tr = getattr(st.cen, "_last_turn_record", None)
        if _tr is not None:
            for v in _tr.result.verdicts:
                cen_verdicts.append({
                    "turn": int(turn), "id": v.assertion_id,
                    "status": v.status.value, "reason": v.reason,
                    "provenance": list(v.provenance),
                    "derivations": int(v.derivations),
                    "cut_depth": int(v.cut_depth)})
        probe_text = (mem.conversation_text() if mem is not None
                      else (st.dmn_self or ""))
        # ==== THE MEDIATOR OF RECORD (paper 3's, per the plan's
        # ==== Decision 1) — UNCOUPLED instruments, read off the
        # ==== MEMORY'S OWN STATE, logged BESIDE the coupled one:
        # ====   * `compaction_gap_turns` — the CADENCE (R1's own
        # ====     measured quantity, +0.625 turns p=0.0016; pure
        # ====     prompt-char arithmetic, needs no self at all);
        # ====   * `self_steps_before`/`self_steps_after` — the
        # ====     CompactionEvent SURVIVAL PAIR (naive_memory 734-735),
        # ====     measured on what the memory HOLDS (summarized span
        # ====     vs summary+kept), the surface seed_steps_in_text was
        # ====     built for.
        # ==== WHICH MEDIATOR A CLAIM MAY USE: a paper-3 claim may read
        # ==== the cadence and the survival pair; it may NOT rest on
        # ==== `self_steps` below — that row is the R5-COUPLED
        # ==== instrument (it routes through the prompt channel the
        # ==== harness itself supplies; with the MY STATE block removed
        # ==== the agent recovered 0 of 4 steps while writing MORE
        # ==== text).  It is KEPT as a logged instrument — evidence of
        # ==== the coupling, and the harness's own DV input — never as
        # ==== the worker claim's mediator.
        if last_ev is not None:
            gap = (int(last_ev.turn) - state["prev_compaction_turn"]
                   if state["prev_compaction_turn"] is not None
                   else int(last_ev.turn))
            state["prev_compaction_turn"] = int(last_ev.turn)
            ev_steps_before = list(last_ev.self_steps_before)
            ev_steps_after = list(last_ev.self_steps_after)
            compaction_ordinal["n"] += 1
        else:
            gap = ev_steps_before = ev_steps_after = None
        # ==== THE RECONSTRUCTION-EXHAUSTION READING (the 2026-10-02
        # ==== amendment's seat): any reading the wrapper appended
        # DURING this turn is stamped with the turn and lands on THIS
        # row — the row the compaction landed on, which is where a
        # reader looks for the event.  The fields are TYPED (a status
        # string, not a nullable float): a reader must be able to tell
        # "exhausted inward" (recon_status == 'exhausted_inward') from
        # "the call was never made" (recon_status is None on this row
        # AND no earlier row carries a reading).  `recon_budget`
        # records the budget the reading exhausted — a different
        # budget is a different measurement, so it is reachable from
        # the row (the pre-registration names it).  The DV READS THE
        # WORK AFTER IT and is NOT touched by this seat: an
        # exhausted-then-working arm is scored NORMALLY by the
        # declared-completion rate per window (dv_rate_per_window
        # reads swe.gate_log alone — no arm field, no exemption); the
        # self is empty and the agent works on, exactly the
        # selflessness-through-collapse the amendment pre-registers.
        recon_row_status = None
        recon_row_budget = None
        recon_row_inward = None
        # ROUTE (b)'s typed row field: the call returned non-empty
        # content that carried NONE of the derivation's steps (see
        # `_wrap_reconstructor`'s second-route block for the finding).
        # None on every other row; 'exhausted_inward' keeps its own
        # field (`recon_status`) UNTOUCHED — the two routes are
        # distinguishable at the row, not merged.
        recon_row_route = None
        while state["recon_read"] < len(recon_readings):
            r = recon_readings[state["recon_read"]]
            r["turn"] = int(turn)
            state["recon_read"] += 1
            recon_row_status = r["status"]
            recon_row_budget = r["num_predict"]
            recon_row_inward = r["inward_share"]
            if r["status"] is None:
                # a SUCCESSFUL call's outcome: route (b) iff the
                # returned text carried no seeded step — the same
                # degradation by its second route, typed at the row.
                steps = r.get("returned_steps")
                recon_row_route = (RECON_CONTENT_WITHOUT_STEPS
                                   if not steps else None)
        # THE SURVIVAL PAIR'S FIXED SEMANTICS (the amendment): the
        # SECOND-EVENT-ONWARD reading is the one a D1-vs-D1' contrast
        # may license — `survival_pair_readable` is True only from
        # event 2 on, where the regimes actually diverge.  The event-1
        # pair is STILL RECORDED (both sides, verbatim, with its
        # ordinal) because it is the seed's own spend and a reader
        # auditing the fix needs to see it fire — it is simply not a
        # MEDIATOR reading.  S5's original form is RETIRED (F6 fired
        # spuriously on exactly this event); S11 is its replacement.
        survival_pair_readable = bool(
            last_ev is not None and compaction_ordinal["n"] >= 2)
        out = {
            "turn": int(turn), "t": float(row.t),
            # the plant runs BESIDE (context, never the DV)
            "G": float(row.G), "D": float(row.D), "c": float(row.c),
            "A_eff": float(row.A_eff),
            "edge_addend": float(row.edge_addend),
            # instrument: OUTWARD CONTENT (the primary DV)
            "content_chars": content_chars,
            # instrument: INWARD SHARE (5.3-guarded)
            "inward_share": row.inward_share,
            "trace_chars": gen.get("trace_chars"),
            "done_reason": gen.get("done_reason"),
            # instrument: THE SELF (present and depletable in every arm)
            "coverage": float(row.coverage),
            "recon_chars": len(st.dmn_self or ""),
            "retrieval_derivations": int(st.retrieval_derivations),
            "self_steps": seed_steps_in_text(probe_text),
            # THE UNCOUPLED MEDIATOR (paper 3's, beside the coupled
            # `self_steps` above — see the block above for which claim
            # may read which): the compaction cadence and the event's
            # OWN survival pair, off the memory's state.
            "compaction_gap_turns": gap,
            "self_steps_before": ev_steps_before,
            "self_steps_after": ev_steps_after,
            # THE MEDIATOR'S EVALUATION WINDOW (the amendment): the
            # event's 1-based ordinal and whether THIS event's pair is
            # one the depletion contrast may read (event >= 2).  The
            # event-1 pair is recorded above, verbatim — it is the
            # seed's own spend, not a mediator reading.
            "compaction_ordinal": (compaction_ordinal["n"]
                                   if last_ev is not None else None),
            "survival_pair_readable": survival_pair_readable,
            # instrument: THE GOALS
            "open_commitments": int(row.open_commitments),
            "expired": int(row.expired),
            "commitments": int(gen.get("commitments", 0) or 0),
            # instrument: THE TASK (the world's own ledger)
            "talking_applied": int(row.talking_applied),
            "talking_actions": int(row.talking_actions),
            "world_completed": len(st.toolworld.completed),
            # instrument: THE TOOL/SWE SURFACE (the smoke's defect 3,
            # 2026-10-01 — `n_tool_calls` lived ONLY in the run
            # summary, so gate S2 (">= 3 tool calls, >= 1 run_tests")
            # was UNMEASURABLE per turn and `talking_applied = 0` on
            # the wired surface read as "the agent never acted" when
            # the agent had made 85 tool calls.  CUMULATIVE counts
            # (chosen over per-turn deltas: the per-turn value is the
            # difference of neighbours, which is LOST at a dropped
            # row, while the cumulative is RECOVERABLE from any
            # suffix — and S2 reads it directly off the final row).
            "n_tool_calls": (0 if tools is None
                             else sum(1 for r in tools.history
                                      if r.turn <= int(turn))),
            "n_run_tests": (0 if tools is None
                            else sum(1 for r in tools.history
                                     if r.tool == "run_tests"
                                     and r.turn <= int(turn))),
            "tools_this_turn": (None if tools is None else sorted(
                {r.tool for r in tools.history if r.turn == int(turn)})),
            # instrument: COMPACTION EVENTS + the measured loss
            "compaction": last_ev is not None,
            "compaction_turn": (int(last_ev.turn)
                                if last_ev is not None else None),
            # THE RECONSTRUCTION-EXHAUSTION READING (typed; see the
            # hook block above): status 'exhausted_inward' = the
            # reconstruction call consumed its whole generation budget
            # as thinking and returned no content (the reading's
            # inward_share is 1.0); None = no exhaustion this turn.
            # Distinct from "the call was never made": that is the
            # ABSENCE of any reading on any row plus the arm's regime
            # (identity.paper3.inject_regime), never this field.
            "recon_status": recon_row_status,
            "recon_budget": recon_row_budget,
            "recon_inward_share": recon_row_inward,
            # ROUTE (b), typed (see the hook block above): non-empty
            # returned content carrying NO seeded step — the second
            # route of the same degradation `recon_status` names, as
            # its own field so the two are distinguishable at the row.
            # None = no successful-call outcome this turn (an
            # exhaustion rides `recon_status`; a step-carrying answer
            # is the regime WORKING and needs no row marker — it is
            # the summary's outcome entry, with returned_steps=[] vs
            # non-empty the splitter).
            "recon_route": recon_row_route,
            "derivation_loss": ev_loss_local,
            "derivation_loss_standing": ev_loss_standing,
            # THE REGULATOR'S OWN RECORD
            "reg_mode": reg.mode,
            "reg_fired": reg.fired,
            "reg_fired_turn": reg.fired_turn,
            "reg_fired_now": fired_now,
            "reg_trigger": reg.trigger,
            "reg_injected": bool(dmn.last_injected),
            "reg_injection_turn": (int(turn) if dmn.last_injected
                                   else None),
            # the prediction the seat holds THIS turn (the EARLY arm's
            # input; None until the first event lands)
            "prediction_crossing_turn": (
                None if reg.prediction is None
                else reg.prediction.crossing_turn),
            "prediction_loss": (None if reg.prediction is None
                                else reg.prediction.loss),
            "prompt_chars": (len(rec.inner.last_prompt)
                             if getattr(rec.inner, "last_prompt", None)
                             else None),
            "secs": secs,
        }
        writer.write(out)
        state["rows"].append(out)
        state["secs"].append(secs)
        if turn == 1 or turn % 50 == 0:
            log(f"{arm}-r{repeat} turn={turn:5d} "
                f"outward={out['content_chars']:6d} "
                f"inward={out['inward_share']} "
                f"cov={out['coverage']:.4f} "
                f"loss_evs={len(loss_events)} "
                f"reg={reg.mode}:{'FIRED@' + str(reg.fired_turn) if reg.fired else 'off'} "
                f"inj={out['reg_injected']} ({secs:.2f}s)")
        return True

    err = None
    try:
        # THE STATE IS THE LOOP'S OWN CONSTRUCTION (not run_stage2's
        # default): the CEN's rules seat is injected HERE — the
        # theory's evidence relations declared on the engine, the
        # designer's evidence seed loaded, the theory handed to the
        # CEN, and a read-only verdict recorder attached for the run's
        # own record.  run_stage2(resume=st0) is the harness's own
        # continue path; a fresh state is exactly what it continues.
        # (The alternative — a cfg field the harness passes at its own
        # CEN construction — is an interface change REPORTED, not made.)
        from stage2_harness import Stage2State, _tmp_record_path
        st0 = Stage2State(cfg, p, _tmp_record_path(cfg))
        if theory is not None:
            theory.declare_evidence(st0.cen.engine)
            if evidence_seed:
                st0.cen.engine.seed(list(evidence_seed))
            st0.cen.rules = theory
        # THE VERDICT RECORDER — an INSTANCE-level wrapper around the
        # CEN's own check_turn (calls through unchanged, keeps the
        # TurnRecord on the CEN for the hook to read).  The verdicts
        # are the CEN's own output; the recorder adds no behaviour.
        _cen = st0.cen
        _raw_check = _cen.check_turn

        def _rec_check(batch):
            tr_ = _raw_check(batch)
            _cen._last_turn_record = tr_
            return tr_

        _cen.check_turn = _rec_check
        run_stage2(sch, turns, cfg, p=p, checkpoint_fn=hook, resume=st0)
    except Exception as exc:                    # noqa: BLE001 — loud
        err = f"{type(exc).__name__}: {exc}"
        log(f"{arm}-r{repeat} STOPPED at "
            f"{len(state['rows'])} rows: {err}")
    writer.close()
    rows = state["rows"]
    status = "OK" if err is None else "ERROR"

    # -- the SWE instruments (designer-side; the held-out reading is
    #    THIS block's alone — nothing on the agent's side sees it) ----
    if surface:
        from task_eval import DEFAULT_TASKS_ROOT
        swe_summary = {
            "targets": sorted(swe.targets),
            "completed": dict(swe.completed),
            "gate_log": list(swe.gate_log),
            "n_run_tests": sum(1 for r in tools.history
                               if r.tool == "run_tests"),
            "n_tool_calls": len(tools.history),
            "refusals": [f"{r.tool}:{r.code}" for r in tools.history
                         if not r.ok],
            # the pin this run's held-out reading is sealed under (the
            # pre-flight checked it; recorded so a reader can see the
            # DV was ARMED — absent here means the summary predates
            # the seat)
            "heldout_pin": heldout_pin,
        }
        try:
            swe_summary["final"] = swe_final_score(
                DEFAULT_TASKS_ROOT, dict(swe.targets), tools)
        except Exception as exc:        # noqa: BLE001 — recorded, loud
            swe_summary["final_error"] = f"{type(exc).__name__}: {exc}"
        # THE FINER DV (the p3-instr fix, T2): the held-out PASS
        # FRACTION per target, continuous, read BESIDE the coarse
        # ordinal — `swe_heldout_fraction` adds the per-task fraction
        # and its sum (0..len(targets)); the coarse verdict (USEFUL 1 /
        # TASK_COMPLETE_ONLY 0.5 / NOT_COMPLETE 0) is UNCHANGED and
        # rides `dv` in the evaluation.  The degenerate case (a target
        # whose held-out suite collected zero tests) is None, never 0/0.
        swe_summary["heldout_fraction"] = swe_heldout_fraction(
            swe_summary.get("final") or {})
        # THE PRIMARY DV (the rate; the amendment's restatement) read
        # over the SAME window the task-health gate reads — one window
        # per run, recorded beside both readings so a reader never
        # re-derives it.  `swe_final_score` above stays EXACTLY as it
        # is: the SECONDARY reading, kept because it alone carries the
        # class-(C) USEFUL/TASK_COMPLETE_ONLY axis and the
        # competence-without-declaration shape the rate cannot see.
        # The declared/competent ratio (F14) is derived here so the
        # obedience reading travels WITH the rate, never inside it.
        _dv_window = int(getattr(args, "task_window", TAU_S_TURNS))
        swe_summary["dv_rate"] = dv_rate_per_window(
            list(swe.gate_log), len(rows), window=_dv_window)
        _declared = swe_summary["dv_rate"][
            "total_declared_completions"]
        _competent = sum(
            1 for e in (swe_summary.get("final") or {}).values()
            if e.get("task_complete"))
        swe_summary["declared_over_competent"] = (
            None if not _competent
            else round(_declared / float(_competent), 4))
        tools.close()
    else:
        swe_summary = {"surface": False}

    # -- the post-run readings (all on the agent's own rows) ----------
    guard = LH.budget_guard(rows)
    # THE TASK-HEALTH GATE READS THE RUN'S OWN SURFACE (the smoke's
    # defect 1, 2026-10-01): the wired run's gate is
    # `surface_task_health` (tool surface + SWE ledger); the CONTROL
    # (`surface=False`) keeps paper 2's `LH.task_health` unchanged —
    # its instrument IS that substrate's (`talking_applied` is the
    # worksheet ledger there, and 0-by-construction here).  BOTH
    # readings travel in the summary so a reader can never mistake
    # the paper-2 gate's INSUFFICIENT on a wired run for a finding
    # about the agent (the smoke's instrument artifact).
    if surface:
        health = surface_task_health(
            rows, swe, tools,
            window=int(getattr(args, "task_window", TAU_S_TURNS)))
        health_p2 = LH.task_health(rows)
    else:
        health = LH.task_health(rows)
        health_p2 = None
    comps = ([vars(ev) for ev in base_mem.compactions]
             if base_mem is not None else [])
    first_w = LH.mean_outward(LH.window_slice(rows, 1))
    final_prediction = (lh_model.predict_crossing_from_events(
        list(loss_events), tau_S=TAU_S_TURNS,
        horizon_t=float(args.horizon_t)) if loss_events else None)
    # THE DV VERDICT is computed by the CAMPAIGN (the floor is an
    # across-arms convention); the per-run record carries the raw
    # window means so the campaign never re-derives them.
    n_windows = len(rows) // TAU_S_TURNS
    window_means = [LH.mean_outward(LH.window_slice(rows, w))
                    for w in range(1, n_windows + 1)]
    summary = {
        "arm": arm, "repeat": repeat, "label": a["label"],
        "regulator": a["regulator"], "memory": a["memory"],
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": status, "error": err,
        "rows": len(rows), "turns": turns,
        "identity": identity(args, arm),
        "identity_tag": hashlib.sha256(json.dumps(
            identity(args, arm), sort_keys=True).encode()
        ).hexdigest()[:16],
        "budget_guard": guard,
        "task_health": health,
        "task_health_p2_instrument": health_p2,
        # THE WINDOW THE SURFACE GATE READ AT (a different window is a
        # different reading of the same rows; the identity carries it
        # too — here it sits BESIDE the reading it produced, so a
        # reader of one summary never has to open the identity)
        "task_health_window": int(getattr(
            args, "task_window", TAU_S_TURNS)),
        # THE SUMMARIZER'S THINKING POLICY, BESIDE THE READING IT
        # PRODUCED (the identity also carries it): think=False on the
        # summarization call — the summarizer is infrastructure, not
        # the phenomenon (the reconstruct arm's thinking stays ON).
        # ONE SOURCE: exp_longhorizon.SUMMARIZER_THINK.  Stated at the
        # summary so a reader of the DV sees the policy without opening
        # the identity.
        "summarizer_think": bool(LH.SUMMARIZER_THINK),
        "compactions": comps,
        "n_compactions": len(comps),
        "derivation_loss_events": [list(e) for e in loss_events],
        # THE MEDIATOR'S FIXED SEMANTICS (the 2026-10-05 amendment),
        # stated where a reader looks: which instrument a given
        # contrast may read, and from which event.  The CADENCE
        # (compaction_gap_turns) is the CARRIER's instrument — it may
        # be read for the D1'-vs-D0 comparison (R1's quantity, the
        # paragraph's char cost) and is BARRED from the D1-vs-D1' seat:
        # under a spanning design work itself fills the window, so
        # cadence is partially DOWNSTREAM of the DV there and reading
        # it as the depletion mediator would be circular (F13).  The
        # SURVIVAL PAIR is the depletion contrast's instrument, read
        # from the SECOND compaction on (S11) — the first event is the
        # seed's own spend in both regimes and cannot separate them.
        "mediator_licence": {
            "cadence": ("D1'-vs-D0 ONLY (the carrier comparison); "
                        "BARRED from D1-vs-D1' — downstream of the DV "
                        "under a spanning design (F13)"),
            "survival_pair": ("D1-vs-D1' from the SECOND compaction "
                              "on (S11; the event-1 pair is the "
                              "seed's own spend — S5's original form "
                              "RETIRED, F6 fired spuriously on it)"),
            "per_turn_self_steps": ("NOT a licensable mediator (R5: "
                                    "prompt-coupled); logged as the "
                                    "corroborator only"),
            "reconstruction_exhaustion": (
                "a READING of the reconstruct arm's own inward "
                "collapse (status 'exhausted_inward', budget "
                "recorded per event): the call consumed its whole "
                "generation budget as thinking and produced no "
                "self-description — inward_share 1.0, the self "
                "genuinely empty.  PRE-REGISTERED (2026-10-02 "
                "amendment) so it is not a post-hoc rescue; the DV "
                "scores the work after it NORMALLY (no exemption — "
                "dv_rate_per_window is arm-blind)"),
            "reconstruction_routes": (
                "the reconstruction call's outcome is TWO named "
                "routes, distinguishable at the row and first-class "
                "in the summary's reconstruction_outcomes: (a) "
                "'exhausted_inward' (empty content at "
                "done_reason='length' — the budget consumed inward); "
                "(b) 'content_without_steps' (content returned, none "
                "of the derivation's steps in it — MEASURED, "
                "p3-d1check both repeats: the self rebuilt as prose "
                "that is not the derivation).  Both are the SAME "
                "degradation by different routes; 'content_with_"
                "steps' is the regime working and rides the same "
                "list.  The DV reads the work after either route, "
                "arm-blind, no exemption"),
        },
        "survival_pair_events": [
            {"turn": r["turn"], "ordinal": r["compaction_ordinal"],
             "readable": r["survival_pair_readable"],
             "before": r["self_steps_before"],
             "after": r["self_steps_after"]}
            for r in rows if r.get("compaction")],
        # THE RECONSTRUCTION-EXHAUSTION READING (the 2026-10-02
        # amendment; only the reconstruct arm can carry entries): one
        # per exhaustion event, turn-stamped, with the budget it
        # exhausted and the inward-share reading (1.0 — all
        # generation, no outward product).  EMPTY list = the run
        # never exhausted (an inject/seat-off arm always has []); it
        # is never a fallback and never restores the seed — the self
        # is genuinely empty after each event (the reading, not a
        # recovery).  SEMANTICS UNCHANGED by the route-b seat: this
        # list is EXHAUSTION EVENTS ONLY (status is not None) — the
        # success-path records (status None, the route-b/raw outcome
        # fields) ride `reconstruction_outcomes` alone, so a reader
        # of the amendment's original field sees exactly what it saw
        # at 512dd0c.
        "reconstruction_exhaustion": [
            r for r in recon_readings if r.get("status") is not None],
        # THE RUN-LEVEL OUTCOME LIST (the p3-reopen seat; the
        # correction's EXPRESSION guard): the mechanism's EVERY
        # expression as a reconstruction-call outcome, FIRST-CLASS in
        # the summary — a reader of the DV consults THIS for the
        # mechanism, never a per-row field.  One entry per call, both
        # routes, each carrying: the turn, the ROUTE (typed —
        # 'exhausted_inward' = empty content at done_reason='length',
        # the budget consumed inward, inward_share 1.0;
        # 'content_without_steps' = content returned, NONE of the
        # derivation's steps in it — the p3-d1check second route;
        # 'content_with_steps' = content returned carrying >=1 step,
        # the regime WORKING, kept so the list is the call's WHOLE
        # history, not a defect log), the budget, done_reason,
        # eval_count, and whether the SELF WAS RESTORED (returned_steps
        # non-empty).  EMPTY list = the arm makes no reconstruction
        # calls (D0/D1'/harness arms — the regime never fires).
        # The DV is NOT touched by this seat: dv_rate_per_window reads
        # swe.gate_log alone, arm-blind, no exemption (unchanged).
        "reconstruction_outcomes": [
            {"turn": r.get("turn"),
             "route": (r.get("status")
                       if r.get("status") is not None
                       else (RECON_CONTENT_WITHOUT_STEPS
                             if not r.get("returned_steps")
                             else "content_with_steps")),
             "budget": r.get("num_predict"),
             "done_reason": r.get("done_reason"),
             "eval_count": r.get("eval_count"),
             "prompt_chars": r.get("prompt_chars"),
             "thinking_chars": r.get("thinking_chars"),
             "restored": bool(r.get("returned_steps")),
             "returned_chars": r.get("returned_chars", 0)}
            for r in recon_readings],
        # THE FORM-B COST SERIES (the p3-cost seat, T2): per
        # reconstruction call — the CUMULATIVE self-maintenance cost the
        # arm has paid to date (tokens, summed over eval_count; None
        # for a call with no eval_count — an unposted or
        # non-observable-bearing call contributes NOTHING to the
        # cumulative and its own row states the absence) and the WORK
        # IN THE NEXT WINDOW (the gate_log completions whose turn
        # lands after this event's turn and at/before the next event's
        # turn, plus the run's own turn count for the final window) —
        # the pair a reader needs to answer "as cumulative
        # self-maintenance cost rose, did the work in the next window
        # fall?" WITHOUT re-deriving anything.  MECHANICAL, THROUGH
        # SHARED RESOURCES — the spend reaches the work via generation,
        # window occupancy and time; what is NOT built is an ARTIFICIAL
        # subtraction of the reconstruction cost from a work budget (a
        # fabricated coupling would be a built substitute wearing
        # the mechanism's name; see mediator_licence.reconstruction_
        # cost).  The series is [] for an arm that makes no
        # reconstruction calls (the regime's own statement).
        "reconstruction_cost_series": reconstruction_cost_series(
            list(recon_readings),
            gate_log=(swe.gate_log
                      if surface and swe is not None else []),
            n_rows=len(rows),
            horizon_turns=int(turns)),
        # THE CROWDING-OUT LICENCE, stated where a reader looks (the
        # same convention as the mediator licence above): the cost
        # series makes the DEPLETION CLAIM MEASURABLE (form B), it does
        # NOT implement it — the run has NO ARTIFICIAL coupling
        # between the reconstruction spend and the work budget; the
        # spend reaches the work mechanically through shared
        # generation, window occupancy and time (MEASURED: ~48% of a
        # probe run's generation), read as co-movement within a cell.
        "cost_licence": (
            "MECHANICAL, THROUGH SHARED RESOURCES: the per-call cost "
            "series records what each self-maintenance call spent — and "
            "that spend is large and reaching.  MEASURED (a 14-turn "
            "probe): the reconstruction calls emitted ~48% of the run's "
            "entire generation, read a ~2x larger window than the work "
            "turns (34,540 vs 15,792 chars), and ran in real wall-clock "
            "time; one call exhausted its whole window and returned an "
            "empty self.  The cost therefore reaches the work through "
            "GENERATION, WINDOW OCCUPANCY and TIME — all shared, bounded "
            "resources — not merely as co-movement (an earlier version "
            "of this string said OBSERVATIONAL, which collapsed "
            "'mechanical' into the one channel the harness does not "
            "charge; retracted).  WHAT IS ABSENT is only an ARTIFICIAL "
            "coupling: nothing here subtracts the reconstruction spend "
            "from a work budget, and building that would be inventing "
            "the mechanism the standing order forbids until the MODEL "
            "carries it.  What such a model term would need: inward "
            "spend reducing outward production, priced in the model's "
            "own units, plus a harness seat that charges it — neither "
            "exists today."),
        "prediction_final": (None if final_prediction is None else {
            "term": "per-compaction derivation loss (standing)",
            "loss": final_prediction.loss,
            "a_hold_max": final_prediction.a_hold_max,
            "n_events": final_prediction.n_events,
            "crossing_t": final_prediction.crossing_t,
            "crossing_turn": final_prediction.crossing_turn,
            "crossing_window": final_prediction.crossing_window,
            "g_end": final_prediction.g_end,
        }),
        "regulator": reg.dump(),
        "n_injections": len(dmn.injections),
        "injections": dmn.injections[:5],
        "first_window_mean_outward": first_w,
        "n_complete_windows": n_windows,
        "window_means_outward": window_means,
        "claim": CLAIM,
        "claim_marking": "PROJECTION (offline fixture build; the arms "
                         "exist to measure it, the rig assumes no "
                         "outcome)",
        "not_built": list(NOT_BUILT),
        "surface": surface,
        "swe": swe_summary,
        "cen_verdicts": cen_verdicts[:200],
        "wall_s": sum(state["secs"]) if state["secs"] else 0.0,
    }
    _atomic_json(summary_path, summary)
    return summary


def survived_windows(summary: dict, floor: float | None) -> dict:
    """THE CLAIM'S PRIMARY DV READING for one run: how many complete
    windows the agent survived before its mean outward content crossed
    the floor (reusing the LH instrument — `windows_to_collapse`, one
    implementation; no window crossed -> the run survived the horizon,
    reported as such, never smoothed into a number)."""
    if floor is None:
        return {"verdict": "INSUFFICIENT (no floor derivable)",
                "survived_windows": None}
    rows_needed = summary["window_means_outward"]
    if not rows_needed:
        return {"verdict": "INSUFFICIENT (no complete window)",
                "survived_windows": None}
    w = summary["window_means_outward"]
    for i, m in enumerate(w, start=1):
        if m is not None and m <= floor:
            return {"verdict": "CROSSED",
                    "survived_windows": i - 1,
                    "crossing_window": i,
                    "crossing_window_mean": m}
    return {"verdict": "NO_COLLAPSE_IN_HORIZON",
            "survived_windows": len(w)}


def run_campaign(args, *, inner_factory=None, summarizer=None) -> dict:
    """THE OFFLINE CAMPAIGN: every arm x the memory regime, the floor
    derived from the runs' own first-window levels (the LH convention),
    the claim recorded verbatim with its marking, and every capability
    NOT built carried beside it.  `inner_factory(args, arm, world)` is
    the fixture hook (None -> the real emitter, which refuses without
    an endpoint)."""
    outdir = args.outdir or os.path.join("out", "lh-agent")
    os.makedirs(outdir, exist_ok=True)
    arms = [a.strip() for a in str(args.arms).split(",") if a.strip()]
    for a in arms:
        if a not in ALL_ARMS:
            log(f"unknown arm {a!r} (known: {sorted(ALL_ARMS)})")
            raise SystemExit(2)
    cells = []
    # THE FLOOR IS DERIVED FIRST, FROM ITS OWN SOURCE RUNS.  The
    # COLLAPSE arm's floor is the DV's own convention — 10% of the
    # mean first-complete-window outward content over the NO-REGULATOR
    # arms (`LH.floor_from_arms`, the LH convention).  Phase 1 runs
    # ONLY the no-regulator arms (the floor's source), derives the
    # floor, and then phase 2 runs the regulated arms — a collapse arm
    # with no derivable floor is REFUSED rather than run against an
    # invented one (fail-closed; the floor is an across-arms
    # convention, never a per-run guess).
    no_reg = [a for a in arms if ALL_ARMS[a]["regulator"] == "none"]
    regulated = [a for a in arms if ALL_ARMS[a]["regulator"] != "none"]
    first_window_means = []
    for arm in no_reg:
        for repeat in range(1, int(args.n) + 1):
            inner = (None if inner_factory is None
                     else inner_factory(args, arm, repeat))
            cell_dir = os.path.join(outdir, f"cell-{arm}-r{repeat}")
            s = run_integrated_cell(args, arm, repeat, cell_dir,
                                    inner=inner, summarizer=summarizer,
                                    collapse_floor=None)
            if s["first_window_mean_outward"] is not None:
                first_window_means.append(
                    s["first_window_mean_outward"])
            cells.append(s)
    floor = LH.floor_from_arms(first_window_means)
    for arm in regulated:
        for repeat in range(1, int(args.n) + 1):
            if ALL_ARMS[arm]["regulator"] == "collapse" and floor is None:
                raise ValueError(
                    "the COLLAPSE arm cannot run: no floor was derivable "
                    "from the no-regulator arms' first complete windows "
                    "(LH.floor_from_arms returned None), and the floor is "
                    "the DV's own convention — an invented one would be a "
                    "second experiment.  Ways out: run the no-regulator "
                    "arms at a horizon that yields a complete first "
                    "window, or omit the collapse arm.")
            inner = (None if inner_factory is None
                     else inner_factory(args, arm, repeat))
            cell_dir = os.path.join(outdir, f"cell-{arm}-r{repeat}")
            cells.append(run_integrated_cell(
                args, arm, repeat, cell_dir, inner=inner,
                summarizer=summarizer, collapse_floor=floor))
    record = {
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "claim": CLAIM,
        "claim_marking": "PROJECTION — the rig assumes no outcome; the "
                         "arms exist to measure the claim",
        "arms": {a: ALL_ARMS[a] for a in arms},
        "floor": {"value": floor,
                  "convention": LH.FLOOR_FRACTION and
                                (f"floor = {LH.FLOOR_FRACTION:g} x mean"
                                 f"(first complete window mean outward "
                                 f"content over the no-regulator runs)"),
                  "from_runs": first_window_means},
        "not_built": list(NOT_BUILT),
        "cells": [{k: c[k] for k in (
            "arm", "repeat", "label", "regulator", "memory", "status",
            "rows", "n_compactions", "first_window_mean_outward",
            "window_means_outward", "budget_guard", "task_health",
            "prediction_final", "regulator", "n_injections",
            "identity_tag")} for c in cells],
        "dv": ("windows survived before the mean outward content "
               "crossed the floor (survived_windows), with the self's "
               "survival, the goals and the task throughput as the "
               "secondary instruments"),
    }
    # the survival verdict per cell, against the derived floor
    for c in record["cells"]:
        full = next(x for x in cells if x["arm"] == c["arm"]
                    and x["repeat"] == c["repeat"])
        c["survival"] = survived_windows(full, floor)
    _atomic_json(os.path.join(outdir, "campaign.json"), record)
    # the measurements file, as the brief's anti-orphan rule asks
    _atomic_json(os.path.join(outdir, "lh_agent_measurements.json"), {
        "created_ts": record["created_ts"],
        "floor": floor,
        "cells": [{k: c[k] for k in (
            "arm", "regulator", "memory", "rows", "n_compactions",
            "first_window_mean_outward", "survival", "regulator")}
            for c in record["cells"]],
    })
    log(f"campaign written: {outdir}/campaign.json "
        f"(floor={floor}, {len(record['cells'])} cells)")
    return record


def mode_plan(args) -> int:
    """THE OFFLINE PLAN: write the campaign record for the DECLARED
    arms and the model-side sensitivity table (pure ODE arithmetic;
    `lh_model`'s own), touching no endpoint."""
    outdir = args.outdir or os.path.join("out", "lh-agent-plan")
    os.makedirs(outdir, exist_ok=True)
    table = []
    for loss in (0.0, 0.25, 0.5, 0.75, 1.0):
        for arrival in (3, 50, 150):
            pred = lh_model.predict_crossing(
                loss, arrival_turn=arrival,
                horizon_t=float(args.horizon_t))
            table.append({"loss": loss, "arrival_turn": arrival,
                          "crossing_t": pred.crossing_t,
                          "crossing_turn": pred.crossing_turn,
                          "crossing_window": pred.crossing_window})
    record = {
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "claim": CLAIM,
        "claim_marking": "PROJECTION",
        "arms": ALL_ARMS,
        "not_built": list(NOT_BUILT),
        "turns": int(args.turns), "n": int(args.n),
        "tau_S": TAU_S_TURNS,
        # the task-health gate's window this plan declares (identity
        # convention: a different window is a different reading)
        "task_health_window": int(getattr(
            args, "task_window", TAU_S_TURNS)),
        "model_prediction_table": table,
        "regulator_seats": {
            "inject_external": "EXTERNAL_LINE on the tool_state channel, "
                               "the world's own open set",
            "directive": "DIRECTIVE_REDIRECT — the forced outward "
                         "channel (the AND-gate's terminator half)",
            "plant_floor": "NOT an actuator here: the plant runs the "
                           "frozen floorless switch; SN_ACTIVATION_FLOOR "
                           "is the regulator's own recorded constant",
        },
    }
    _atomic_json(os.path.join(outdir, "campaign.json"), record)
    _atomic_json(os.path.join(outdir, "lh_agent_measurements.json"), {
        "created_ts": record["created_ts"],
        "model_prediction_table": table})
    log(f"plan written: {outdir}/campaign.json "
        f"({len(table)} prediction rows)")
    return 0


#: THE DV'S SCALE, stated where it is computed (P3-PREREG §3: 0..6 per
#: cell over three targets x two repeats — a cell's own share of that
#: is 0..len(targets); USEFUL=1, TASK_COMPLETE_ONLY=0.5,
#: NOT_COMPLETE=0).  Pure convention, carried as data so the record,
#: the docstring and the evaluation read ONE mapping.
LA_DV_POINTS = {"USEFUL": 1.0, "TASK_COMPLETE_ONLY": 0.5,
                "NOT_COMPLETE": 0.0}


def la_endpoint_refusal(args) -> str | None:
    """THE SPEND GUARD, as a predicate — `LH.endpoint_refusal` reused,
    not a second convention (the brief's own rule).  Without a NAMED
    endpoint the live mode REFUSES before writing anything: there is no
    default transport and no stub fallback, so a silent one would make
    every measurement unattributable (and would spend against a machine
    nobody named).  Returns the refusal message, or None."""
    return LH.endpoint_refusal(args)


def la_arms_refusal(arms: list) -> str | None:
    """THE ARM VALIDATION, as a predicate: every named arm must be known
    (`_p3_spec`'s own refusal covers unknown names) and the list must
    not be empty.  Returns the refusal message, or None."""
    if not arms:
        return (f"--arms names no arm (known: {sorted(ALL_ARMS)})")
    for a in arms:
        try:
            _p3_spec(a)
        except (KeyError, ValueError) as exc:
            return str(exc)
    return None


def _la_identity_tag(rec: dict) -> str:
    return hashlib.sha256(json.dumps(
        rec, sort_keys=True).encode()).hexdigest()[:16]


def la_identity_tag(args, arm: str) -> str:
    """The arm's configuration tag — ONE implementation, so the tag a
    summary RECORDS (run_integrated_cell's own, off `identity`) and the
    tag a resume COMPARES cannot drift (exp_longhorizon.lh_identity_tag
    :2838's discipline)."""
    return _la_identity_tag(identity(args, arm))


def la_cell_resume_ok(prev: dict, args, arm: str) -> tuple:
    """MAY a completed cell summary be reused as THIS run's measurement?
    Only if it is a COMPLETED measurement (status OK) of THIS
    configuration (the identity tag).  A partial or failed cell is never
    reused as one (exp_longhorizon.lh_resume_ok :2845's door)."""
    if prev.get("status") != "OK":
        return False, f"prior attempt status={prev.get('status')}"
    tag = la_identity_tag(args, arm)
    if prev.get("identity_tag") != tag:
        return False, (f"the recorded configuration identity differs "
                       f"({prev.get('identity_tag')!r} != {tag!r})")
    return True, "already measured, status OK, configuration identity matches"


def la_cell_dir(outdir: str, arm: str, repeat: int) -> str:
    """THE CELL'S OWN DIRECTORY — run_campaign's layout (the launcher's
    rc/status/collect globs read <outdir>/cell-<arm>-r<rep>/rows/,
    lh_lambda.sh 528-640 — the layout is a contract, not a choice)."""
    return os.path.join(outdir, f"cell-{arm}-r{repeat}")


def la_campaign_record(args, arms: list) -> dict:
    """THE PER-RUN CAMPAIGN RECORD (one builder, so the record a fresh
    run writes and the record a resume compares cannot differ —
    exp_longhorizon.campaign_record :2324's discipline).  P3-PREREG.md
    is the DESIGN record this cites; THIS is the per-run record: what is
    running, where the rows will land, and under which pre-registration
    — written BEFORE the first turn, never after."""
    endpoint = (str(args.chat_endpoint) if args.api == dmn_llm.CHAT
                else str(args.endpoint))
    model = (str(args.chat_model) if args.api == dmn_llm.CHAT
             else str(args.model))
    return {
        "prereg": LA_PREREG_NODE,
        "result_node": LA_RESULT_NODE,
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "claim": CLAIM,
        "claim_marking": "PROJECTION — the rig assumes no outcome; the "
                         "arms exist to measure the claim",
        "mode": "run",
        "arms": list(arms),
        "turns": int(args.turns), "n": int(args.n),
        "budget": int(args.budget),
        "num_predict": int(args.num_predict),
        "num_ctx": int(args.num_ctx),
        "keep_recent": int(args.keep_recent),
        "temperature": float(args.temperature),
        "tau_S": TAU_S_TURNS,
        "surface": bool(getattr(args, "surface", True)),
        "engine": str(getattr(args, "engine", "real")),
        "model": model, "api": str(args.api),
        # THE ENDPOINT, ON THE DECIDING SURFACE: the same experiment on
        # a different machine is a DIFFERENT campaign (never resumed
        # into the old outdir on an identity that never looked at it).
        "endpoint": endpoint,
        "timeout": float(getattr(args, "timeout", LA_TIMEOUT_DEFAULT)),
        # the task-health window, on the deciding record (the identity
        # carries it per arm; this is the campaign-level declaration)
        "task_health_window": int(getattr(
            args, "task_window", TAU_S_TURNS)),
        "seed_base": int(args.seed_base),
        "arm_identities": {a: identity(args, a) for a in arms},
        "not_built": list(NOT_BUILT),
        "dv": ("PRIMARY: the declared-completion RATE PER WINDOW "
               "(world-adjudicated gate_log, P3-PREREG's 2026-10-05 "
               "amendment; the window-gradient and the per-window rate "
               "are the pre-registered statistics).  SECONDARY: "
               "swe_final_score, the external evaluator's typed verdict "
               "per target (USEFUL 1 / TASK_COMPLETE_ONLY 0.5 / "
               "NOT_COMPLETE 0) — it alone carries the class-(C) axis "
               "and the competence-without-declaration shape.  "
               "SECONDARY-B (the p3-instr finer DV): the held-out PASS "
               "FRACTION per target (len(passed)/len(collected)), a "
               "continuous 0..1 summed to 0..len(targets) — the SAME "
               "instrument at finer granularity, reported BESIDE the "
               "coarse ordinal (never instead of it); a target whose "
               "held-out suite collected zero tests is None, never 0/0.  "
               "The declared/competent ratio is reported per arm (F14). "
               "turns_to_first_PASS is DROPPED (no discriminating "
               "power under a queue; author decision, stated in the "
               "amendment)"),
        "floor": _LA_FLOOR_NOT_DERIVED,
        "layout": ("rows: <outdir>/cell-<arm>-r<repeat>/rows/"
                   "<arm>-r<repeat>.jsonl; summary: <outdir>/cell-<arm>-"
                   "r<repeat>/runs/<arm>-r<repeat>.json"),
    }


def la_campaign_identity(record: dict) -> dict:
    """The campaign's DECIDING SURFACE, extracted — never the timestamp
    (exp_longhorizon.campaign_identity :2659's discipline)."""
    return {k: record.get(k) for k in LA_CAMPAIGN_IDENTITY_FIELDS}


def _la_load_json(path: str, default=None):
    """Read a JSON artifact back off disk — the RECORD, not a
    recomputation (the caches-are-the-record discipline)."""
    if not os.path.exists(path):
        return default
    with open(path) as fh:
        return json.load(fh)


def la_write_campaign(outdir: str, record: dict) -> int:
    """WRITE THE PER-RUN PRE-REGISTRATION, AND NEVER CLOBBER ONE
    (`exp_longhorizon.write_campaign` :2664's door, one convention):
    0 when the record is on disk — freshly written, or already present
    and IDENTICAL on its deciding surface (the RESUME: a re-invocation
    of the same campaign reuses the pre-registration it wrote) — and 4
    when a DIFFERENT campaign is already there, REFUSED loudly rather
    than overwritten: an experiment that rewrites its own
    pre-registration is not pre-registered."""
    path = os.path.join(outdir, "campaign.json")
    if os.path.exists(path):
        prev = _la_load_json(path, {})
        if la_campaign_identity(prev) != la_campaign_identity(record):
            log(f"refused: {path} already holds a DIFFERENT campaign — "
                f"REFUSING to overwrite a pre-registration.  On disk: "
                f"{la_campaign_identity(prev)}; this invocation: "
                f"{la_campaign_identity(record)}.  Ways out: run into "
                f"a fresh --outdir, or delete that file yourself, "
                f"deliberately.")
            return 4
        log(f"campaign.json present and identical — resuming ({path})")
        return 0
    _atomic_json(path, record)
    log(f"pre-registration written BEFORE the first turn: {path}")
    return 0


def la_evaluate(arms: list, repeats: int, outdir: str) -> dict:
    """THE EVALUATION over the COMPLETED cells on disk (the live mode's
    step 5; `exp_longhorizon.evaluate_lh` :2861's discipline — IT READS
    THE RECORD, NOT THE PROCESS: rows and summaries back off disk, a
    run is its files).  What it carries is the pre-registration's own
    machinery, never re-implemented here: the external DV
    (`swe_final_score` -> USEFUL/TASK_COMPLETE_ONLY/NOT_COMPLETE per
    target, P3-PREREG §3), the co-primary `turns_to_first_PASS` (the
    world's own gate log: the first turn a target's completion verdict
    was PASS), and the UNCOUPLED MEDIATOR per arm — the cadence and the
    survival pair, read off the rows.  A reading the record does not
    yield is reported INSUFFICIENT, never smoothed into a number."""
    cells = []
    for arm in arms:
        for repeat in range(1, int(repeats) + 1):
            cdir = la_cell_dir(outdir, arm, repeat)
            rows_path = os.path.join(cdir, "rows", f"{arm}-r{repeat}.jsonl")
            rows = []
            if os.path.exists(rows_path):
                with open(rows_path) as fh:
                    rows = [json.loads(ln) for ln in fh if ln.strip()]
            summ = _la_load_json(os.path.join(
                cdir, "runs", f"{arm}-r{repeat}.json")) or {}
            swe = summ.get("swe") or {}
            final = swe.get("final") or {}
            # the DV, off the DESIGNER's own held-out reading: verdict
            # per target; a target with no reading scores 0 (NOT_COMPLETE
            # at the record's own convention — stated, never smoothed)
            per_target = {f: (e.get("verdict"), float(
                LA_DV_POINTS.get(e.get("verdict"), 0.0)))
                for f, e in final.items()}
            dv = sum(p for _v, p in per_target.values())
            gate_log = swe.get("gate_log") or []
            first_pass = {}
            for g in gate_log:
                if g.get("verdict") == "PASS" \
                        and g["target"] not in first_pass:
                    first_pass[g["target"]] = int(g["turn"])
            gaps = [r["compaction_gap_turns"] for r in rows
                    if r.get("compaction_gap_turns") is not None]
            # THE PRIMARY DV, off the cell's own summary (the record,
            # never a recomputation): the per-window rate and its
            # gradient.  The event-time seat (turns_to_first_PASS) is
            # RETIRED (the amendment: no discriminating power under a
            # queue) — the first_pass computation above is KEPT as the
            # ledger's own audit trail, not as a DV seat.
            dv_rate = (swe.get("dv_rate") or
                       dv_rate_per_window(gate_log, len(rows),
                                          window=int(
                                              summ.get(
                                                  "task_health_window")
                                              or TAU_S_TURNS)))
            # THE MECHANISM'S EXPRESSION, FIRST-CLASS IN THE
            # EVALUATION (the p3-reopen seat): the run-level outcome
            # list off the cell's own summary — both routes, one entry
            # per reconstruction call, so a reader of the set's DV
            # sees the mechanism beside it instead of hunting a
            # per-row field.  ABSENT on a pre-change summary is
            # reported AS ABSENT (None) — never as an empty list,
            # which would read "the arm made no calls" for a cell
            # that made them before the seat existed (the false
            # reading-by-absence).  [] (a real empty list) = the arm
            # makes no reconstruction calls (D0/D1' — the regime's own
            # statement).  Counts by route are derived here for
            # one-look reading; the entries are the record.
            _outs_present = "reconstruction_outcomes" in summ
            _outs = (summ.get("reconstruction_outcomes")
                     if _outs_present else None)
            _out_counts = (None if not _outs_present else {
                "exhausted_inward": sum(
                    1 for o in _outs
                    if o.get("route") == "exhausted_inward"),
                "content_without_steps": sum(
                    1 for o in _outs
                    if o.get("route") == "content_without_steps"),
                "content_with_steps": sum(
                    1 for o in _outs
                    if o.get("route") == "content_with_steps"),
            })
            cells.append({
                "arm": arm, "repeat": repeat,
                "status": summ.get("status", "NOT CARRIED"),
                "rows": len(rows), "rows_recorded": summ.get("rows"),
                "n_compactions": summ.get("n_compactions"),
                "identity_tag": summ.get("identity_tag"),
                "dv": {"per_target": per_target, "sum": dv,
                       "scale_note": ("0..len(targets) for this cell "
                                      "(SECONDARY, the artifact "
                                      "ordinal; the PRIMARY DV is "
                                      "dv_rate below)")},
                # THE FINER DV (the p3-instr fix, T2): the held-out
                # PASS FRACTION per target, continuous — read off the
                # cell's own summary (the record, never a recomputation;
                # absent on a pre-change summary -> None, the same
                # false-reading-by-absence guard the outcome list uses).
                # The coarse `dv.sum` above is UNCHANGED; this rides
                # BESIDE it.  `swe_heldout_fraction_sum` is the one-look
                # float (the parallel to `dv.sum`).
                "swe_heldout_fraction": (
                    swe.get("heldout_fraction")
                    if "heldout_fraction" in swe else None),
                "swe_heldout_fraction_sum": (
                    swe["heldout_fraction"].get("sum")
                    if isinstance(swe.get("heldout_fraction"), dict)
                    else None),
                "dv_rate": dv_rate,
                "declared_over_competent": swe.get(
                    "declared_over_competent"),
                "turns_to_first_PASS": first_pass or None,
                # (the counts were derived above; ABSENT vs [] is the
                # pre-change-summary distinction the comment there
                # states)
                "reconstruction_outcomes": _outs,
                "reconstruction_outcome_counts": _out_counts,
                # THE FORM-B COST SERIES (the p3-cost seat; T2): the
                # per-call cost + next-window work series off the
                # cell's own summary — the reader of evaluation.json
                # (what the paper reads) computes the form-B reading
                # "as cumulative self-maintenance cost rose, did the
                # next window's work fall?" WITHOUT re-deriving
                # anything.  ABSENT on a pre-change summary -> None
                # (the same false-reading-by-absence guard the outcome
                # list uses); [] = the arm makes no reconstruction
                # calls (its own statement).  MECHANICAL THROUGH SHARED
                # RESOURCES: see the summary's cost_licence — the cost
                # is real (generation/window/time); no ARTIFICIAL
                # coupling is built.
                "reconstruction_cost_series": (
                    summ.get("reconstruction_cost_series")
                    if "reconstruction_cost_series" in summ else None),
                "mediator": {
                    "compaction_gap_turns": gaps,
                    "mean_gap_turns": (sum(gaps) / len(gaps)
                                       if gaps else None),
                    "n_events_with_pair": sum(
                        1 for r in rows
                        if r.get("compaction")
                        and r.get("self_steps_before") is not None),
                    # the FIXED-SEMANTICS reading (S11): the survival
                    # pair from the SECOND event on, which is the only
                    # pair the D1-vs-D1' contrast may license
                    "survival_pair_second_event_on": [
                        {"turn": r["turn"],
                         "before": r["self_steps_before"],
                         "after": r["self_steps_after"]}
                        for r in rows
                        if r.get("compaction")
                        and r.get("survival_pair_readable")],
                },
                "swe_final_error": swe.get("final_error"),
            })
    # the pre-registered DIRECTION, reported as a READING (PROJECTION no
    # further: the numbers are MEASURED, the inference over them is the
    # analyst's) — D1 vs D0 on the DV, with the realised n stated and
    # the explicit INSUFFICIENT below the pre-registration's own bound.
    def _arm_dv(a):
        return [c["dv"]["sum"] for c in cells if c["arm"] == a]

    contrast = None
    if "D1" in arms and "D0" in arms:
        d1, d0 = _arm_dv("D1"), _arm_dv("D0")
        if len(d1) >= 1 and len(d0) >= 1:
            contrast = {
                "reading": ("D1 mean "
                            f"{sum(d1) / len(d1):.3f} (n={len(d1)}) vs D0 "
                            f"mean {sum(d0) / len(d0):.3f} (n={len(d0)})"),
                "decision_rule": ("Mann-Whitney U over the realised n, "
                                  "INSUFFICIENT below 6 valid cells per "
                                  "arm (P3-PREREG §7)"),
                "verdict": ("INSUFFICIENT (realised n below the "
                            "pre-registered minimum)" 
                            if min(len(d1), len(d0)) < 6 else "COMPUTABLE"),
                "d1_minus_d0": sum(d1) / len(d1) - sum(d0) / len(d0),
            }
    return {
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "prereg": LA_PREREG_NODE,
        "result_node": LA_RESULT_NODE,
        "claim": CLAIM,
        "dv": ("PRIMARY: the declared-completion rate per window "
               "(world-adjudicated gate_log); SECONDARY: "
               "swe_final_score (P3-PREREG §3 + the 2026-10-05 "
               "amendment)"),
        "cells": cells,
        "contrast_d1_d0": contrast,
        "independence": ("the launcher's independence check gates the DV "
                         "read (P3-PREREG §7; a clone set is VOID)"),
        "marking": ("the DV and mediator numbers are MEASURED (off the "
                    "runs' own files); any inference over them is the "
                    "analyst's, per the pre-registration's rule"),
    }


def mode_run(args, *, inner_factory=None, summarizer=None) -> int:
    """THE LIVE MODE — THE DRIVER (the exp_longhorizon mirror, its order
    and its doors; each step refuses rather than degrading):

    1. THE SPEND GUARD FIRST (`la_endpoint_refusal` = LH's own
       `endpoint_refusal`): without a NAMED endpoint NOTHING is written
       and nothing is posted (exit 3) — no campaign.json, no rows.
    2. THE ARMS (`la_arms_refusal`): unknown names and an empty --arms
       are refused (exit 2).
    3. THE PRE-REGISTRATION BEFORE THE FIRST TURN
       (`la_write_campaign`, `la_campaign_record`): the per-run campaign
       record lands in the outdir before any turn is posted, and an
       EXISTING campaign is never clobbered — the SAME campaign RESUMES
       (completed cells are skipped on their identity tag), a DIFFERENT
       one is REFUSED (exit 4).
    4. THE CELLS: every arm x repeat through `run_integrated_cell`
       (the whole cell body: build_inner, build_cfg with the arm's
       paper-3 spec, the SWE surface, one row per turn, the uncoupled
       mediator beside the coupled instrument), the per-turn bound from
       `--timeout` (threaded through build_inner — the T1 seat).
    5. THE FAILURE IS LOUD AND IT STOPS THE CAMPAIGN: a transport error
       is caught by the cell itself (its own try/except records the
       partial run: the rows file stops where it stopped, the summary
       carries status=ERROR and the error string); the driver returns
       NON-ZERO (5) WITHOUT evaluating — a partial campaign is not
       scored, because the pre-registered analysis needs every named
       cell's reading to be a completed measurement.
    6. THE EVALUATION (`la_evaluate`) writes evaluation.json over the
       COMPLETED cells only: the external DV, the co-primary
       turns_to_first_PASS, and the uncoupled mediator per arm.

    EXIT CODES: 0 a COMPLETED campaign (an INSUFFICIENT contrast is a
    result, written in evaluation.json, not a driver failure); 2 refused
    (arms); 3 refused (no endpoint — the spend guard); 4 refused (a
    different campaign is already in the outdir); 5 a cell failed (the
    campaign stopped, nothing was evaluated).

    THE FIXTURE SEAM: `inner_factory(args, arm, repeat) -> emitter|None`
    and `summarizer` are passed straight to `run_integrated_cell`
    (None = the real transport, which raises `DMNEndpointError` without
    an endpoint).  The seam replaces ONLY the transport — the arms, the
    spec, the schedule, the rows and the evaluation are the same code a
    live run takes."""
    outdir = args.outdir or os.path.join("out", "lh-agent-run")

    refusal = la_endpoint_refusal(args)
    if refusal:
        log(f"refused: {refusal}")
        return 3

    arms = [a.strip() for a in str(args.arms).split(",") if a.strip()]
    bad = la_arms_refusal(arms)
    if bad:
        log(f"refused: {bad}")
        return 2
    if int(args.n) < 1:
        log(f"refused: --n {args.n} runs no repeat (1 or more)")
        return 2

    os.makedirs(outdir, exist_ok=True)
    rc = la_write_campaign(outdir, la_campaign_record(args, arms))
    if rc:
        return rc

    n = int(args.n)
    for arm in arms:
        for repeat in range(1, n + 1):
            cdir = la_cell_dir(outdir, arm, repeat)
            prev = _la_load_json(os.path.join(
                cdir, "runs", f"{arm}-r{repeat}.json"))
            if prev:
                ok, why = la_cell_resume_ok(prev, args, arm)
                if ok:
                    log(f"{arm}-r{repeat} SKIP ({why})")
                    continue
                log(f"{arm}-r{repeat} re-running ({why})")
            log(f"{arm}-r{repeat} START (turns={args.turns}, "
                f"num_ctx={args.num_ctx}, "
                f"num_predict={args.num_predict}, "
                f"surface={getattr(args, 'surface', True)}, "
                f"engine={getattr(args, 'engine', 'real')}, "
                f"timeout={args.timeout:g}s/turn, "
                f"task-window="
                f"{int(getattr(args, 'task_window', TAU_S_TURNS))})")
            inner = (None if inner_factory is None
                     else inner_factory(args, arm, repeat))
            s = run_integrated_cell(
                args, arm, repeat, cdir, inner=inner,
                summarizer=summarizer,
                surface=bool(getattr(args, "surface", True)))
            if s.get("status") != "OK":
                log(f"{arm}-r{repeat} FAILED at row "
                    f"{s.get('rows')}/{args.turns}: "
                    f"{s.get('error')} — the campaign STOPS here "
                    f"(exit 5); the partial run is recorded in its own "
                    f"rows file and summary, and NO evaluation is "
                    f"written over a partial campaign")
                return 5
            log(f"{arm}-r{repeat} OK: {s['rows']} rows, "
                f"{s['n_compactions']} compactions, "
                f"{s['budget_guard']['empty_rate']} empty rate, "
                f"task-health {s['task_health']['status']}, "
                f"{s['wall_s']:.1f}s, swe final "
                f"{('error: ' + s['swe']['final_error'][:40])
                    if s.get('swe', {}).get('final_error')
                    else 'recorded'}")

    log(f"all cells complete — evaluating ({len(arms)} arm(s) x {n} "
        f"repeat(s))")
    evaluation = la_evaluate(arms, n, outdir)
    path = os.path.join(outdir, LA_EVALUATION)
    _atomic_json(path, evaluation)
    log(f"evaluation written: {path} — {len(evaluation['cells'])} "
        f"cell(s); D1-D0 contrast "
        f"{evaluation['contrast_d1_d0']['verdict']
            if evaluation['contrast_d1_d0'] else 'n/a (arms absent)'}")
    return 0


def main(argv=None) -> int:
    args = integrated_args(argv)
    if args.mode == "plan":
        return mode_plan(args)
    if args.mode == "run":
        return mode_run(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
