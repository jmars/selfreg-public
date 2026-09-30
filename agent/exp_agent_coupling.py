#!/usr/bin/env python3
"""THE AGENT-SIDE COUPLING EXPERIMENT RUNNER (paper 2's demonstration).

LANE: [agent] (agent/).  NOT dpdr/experiments/ — that is the frozen model's
lane and those drivers are MODEL-LEVEL.  THIS is the first in-agent result.

THE SPEC IS A PRE-REGISTRATION, WRITTEN BEFORE ANY RUN:
memory node `handoff-selfreg-agentexp-plan`.  This file IMPLEMENTS it as
written.  Nothing here is tuned after seeing output; every default below is
the plan's own number, and any CLI override is RECORDED in the result JSON
(and warned about on stdout) rather than silently applied.  A change to the
SPEC needs a `stage=correction` on that node, not an edit here.

WHAT IT DOES.  Runs the Stage-2 turn loop (agent/stage2_harness.run_stage2)
with the REAL generator (agent/dmn_llm.LLM_DMN) over the FROZEN rescue
scenario (dpdr.events.rescue_schedule) and scores the G2c categorical
recovery criterion on the harness's own per-turn log:

    recovered = (G_end > 0.5) AND (min G over the window t in [1000,1400] > 0.5)

  — Stage2LogRow.G, threshold BAND1 = 0.5, horizon 1400 turns = 1400 t.u.
  This is exp22's own criterion VERBATIM (dpdr/experiments/exp22_rescue.py:
  277-278).  The runner never substitutes a threshold, a horizon or a cell
  set.  The model's OWN committed vectors (dpdr/cache/exp22_rescue.npz) are
  off_recovered = [1 1 1 1 1 1 1], spec_recovered = [1 0 0 1 1 1 1] over the
  grid {25,50,100,150,200,400,800} [MEASURED] — the agent vectors this file
  produces are reported OVER THE THREE ARMING CELLS {25,50,100} so the two
  sit side by side on the cells exp22 fails at (50, 100).

THE MATRIX (the full mode).  2 routing settings {route-all, routing-on} x 2
coupling arms {SPEC = couple_backlog=True, OFF = couple_backlog=False} x
tau_S in {25, 50, 100} x N repeats (N >= 3).  The two routing settings answer
DIFFERENT questions and BOTH are run:
  (i)  route-all  = THE DIRECT AGENT REPLICA of exp22: no selector is
       injected, so every valid span routes (f == 1,
       stage2_harness.py:820-846) and the backlog builds exactly as it did
       in the model.  The generator hands over a raw str; the harness
       extracts it.
  (ii) routing-on = THE REALISTIC SYSTEM: routingcrit.PrefixRoutingSelector
       is injected plus a PUBLISHED criterion, so R5's law decides the split
       per consolidation window and the DMN must emit the raw stream (the
       EXTRACTOR, not the generator, decides what is a claim).
(i) can fail while (ii) passes; the plan names that contrast a finding.

THE ARMS ARE THE ONLY DIFFERENCE IN THE CONTROL.  SPEC vs OFF share the
generator, the seed per turn, the routing setting and the plant parameters;
only `Stage2Config.couple_backlog` differs, and ROUND 2 made it mean exactly
what the model says: SPEC = the plant's own coupling EXISTS (edge_on, so
A_eff = A + B with B = EMA_tauD(c), c the plant's own switch state — the
model's ONE c, which also drives the attention pinning), OFF = it is
REMOVED (A_eff = A).  Nothing is injected through the schedule's 'A' port:
round 1 drove the addend from the CEN's measured unchecked-accrual rate
while the pinning read the plant's c, i.e. it split one model variable into
two, and the coupling could then only act through D's production term (with
the measured effect of the WRONG SIGN: SPEC came out protective).  See
stage2_harness's coupling docstring, which states the cost of that choice
plainly: in this wiring the generator's output reaches the CEN and the
telemetry but has NO PATH INTO THE PLANT.

THE DETERMINISM PROTOCOL (the LLM is stochastic and exp22 was not).  Per-turn
sampling seed = base + turn (dmn_llm.LLM_DMN._body's own convention, the
bake's `seed + t`); the base is fixed per repeat:
`base(repeat) = seed_base + repeat * SEED_STRIDE`.  The generator's TaskWorld
seed is FIXED across every repeat (the world is the generator's own model of
its work, not a second stochastic axis).  Acceptance is a FRACTION, never a
bit: OFF must recover in N/N at every arming cell — else the run is VOID —
and SPEC must fail in >= 2/N at tau_S = 50 and 100 in at least one routing
setting.  The FULL per-cell matrix is always reported, never one summary bit.
`--det-check` settles the plan's stated OPEN QUESTION (whether a fixed seed
makes the generator deterministically reproducible, so N could drop to 1) by
running the same (arm, cell, seed) twice and diffing the streams per turn.

THE PILOT GATE IS MANDATORY AND RUNS FIRST.  `--pilot` = ONE run, SPEC +
route-all, tau_S = 100, 150 turns, printing a per-turn row and evaluating
four gates: (1) the generator emitted a NON-EMPTY VARYING stream; (2)
backlog_outstanding RISES; (3) B — THE P2 ADDEND THE PLANT'S D IS ACTUALLY
DRIVEN WITH, i.e. the plant's own `Agent.B` = the EMA at tau_D of the
plant's switch state c (the model's ONE c, dpdr/model.py:92-94) — BUILDS
above ~0; (4) the measured per-turn wall time -> the projected full-matrix
cost.  ROUND 2 changed gate 3's OBJECT to the plant's own B and NOT the
CEN's measured u/n (both are printed, side by side): the model has one c,
and the quantity that has to build for the coupling to be exercised is the
one the plant carries.  `--full` REFUSES to start unless
`<outdir>/pilot.json` records a PASS on gates 1-3
(`--force-after-failed-pilot` overrides, and the override is recorded in the
JSON).  A gate failure is a fact about the STATE DESIGN, not about the
experiment — fix dmn_llm's TaskWorld, do not proceed.

THE PREDICATES, STATED BECAUSE THEY ARE OPERATIONALIZATIONS (the plan states
the gates qualitatively; these are the exact predicates the run PRINTS, so
they cannot be shifted quietly):
  * gate 1  = (spans_total > 0) AND (distinct per-turn span counts > 1).
  * gate 2  = (mean backlog of the second half > mean of the first half) AND
              (max backlog > min backlog);  reported with the end/early ratio.
  * gate 3  = (max B > 1e-9) — strictly positive, on the P2 ADDEND B: the
              number the plant's D is actually driven with.  ROUND 2: that
              is the plant's OWN B (`Agent.B` = EMA_tauD(switch_c c)),
              reported per turn as `B_plant` and as
              `Stage2LogRow.edge_addend`.  Its KEY keeps the plan's name
              (`gate3_backlog_ema_builds`) because a pre-registration is not
              edited here; the OBJECT has moved twice and both are printed —
              round 1 fed the raw assertion STOCK (a count, saturating D);
              the reconciliation then fed the CEN's measured u/n (a
              substrate telemetry that does NOT reach the plant); round 2
              restored the model's single c, so the addend is the plant's
              own B.  `backlog_rate` (u/n EMA) and `backlog_ema` (the stock)
              are printed BESIDE it as telemetry, never as the gate.
              CONSEQUENCE, STATED SO THE GATE CANNOT BE MISREAD: this gate
              is 0 for as long as the plant's switch has not armed, so on a
              horizon shorter than the arming time it FAILS — that is a
              measurement of the regime, not of the wiring.
              On rescue_schedule()
              the 'A' channel is NON-ZERO on t in [100,160) (the affect
              pulse 0.5 from failure_schedule — MEASURED, and the earlier
              "the A channel is ABSENT" note here was WRONG), so A_eff =
              A + B with A = 0.5 over those 60 turns: the coupling enters
              D's drive on top of that pulse, and 0.5 is HALF the model's
              whole B range — the runner therefore reports the plant's own
              measured A_eff (Stage2LogRow.A_eff), never the addend alone.
  * gate 3r = (0 <= min B) AND (max B <= 1): the P2 addend inside the
              model's own B range (c in [0,1]) — the unit check the
              reconciliation added, printed beside gate 3.
  * gate 4  = not a pass/fail: median and mean seconds per turn over the
              post-warm-up turns, projected to TURNS_FULL x cells.
  * `t == turn` is asserted for every row (the harness's F4 convention, one
    turn = one t.u. — harness.py:265 / H_STEP = 1.0), because the criterion
    window [1000, 1400] is stated in t.u. and mapped onto turn indices.

EVIDENCE MARKING (every claim in this file and in its JSON):
  * MEASURED      — the prerequisites: the generator exists and returns a raw
                    str (dmn_llm.py), the harness accepts a str in route-all
                    and requires a str with a selector attached
                    (stage2_harness.py), the plant's own numbers (G, D, c) are
                    the FROZEN model's, the exp22 vectors above.
  * INTERPRETATION — that a route-all agent run is the "direct replica" of
                    exp22.  The plant is the same frozen plant and D's drive
                    is the same P2 addend, but the DEMAND IS NOT A FIXED c:
                    the generator's stream varies by turn, so B's trajectory
                    is NOT the model's EMA of a fixed c.  The test is the
                    RECOVERY OUTCOME, never the trajectory.
  * PROJECTION    — every cost estimate and every statement about cells not
                    yet run (the pilot's projection; the sweep's 28 GPU-hours).
                    The model -> agent MAPPING stays ORDINAL AND UNVALIDATED
                    (4 of 5 prior mappings failed), so ANY positive result
                    here is SUGGESTIVE, NOT CONFIRMATORY, and a NEGATIVE one
                    falsifies the mapping in the agent — an equally
                    publishable outcome (the plan's own acceptance line).

THE STATED CONFOUNDS THE RESULT MUST CARRY (the plan's list, implemented
where observable, never silently):
  a. THE G-ANALOGUE IS UNSOLVED: the routing path calls the law with G=None
     -> the maximally conservative arm (`g_unsolved_conservative_arm`,
     routing.py), which UNDERSTATES f and so understates routed demand in the
     routing-on pair.
  b. ENGINE: "stub" by default (--engine real opts into the dlb binding).
     Stated in every JSON.
  c. THE GENERATOR IS NONSTATIONARY (above).
  d. ONE TURN = ONE TURN = ONE t.u. (the runner asserts t == turn).
  e. THE LEVER/PROPOSAL CHANNEL IS UNUSED by a stream generator
     (dmn_llm.GAPS G1) — do not infer it was exercised here.
  f. The stub engine + rule-free store make most claims land UNCHECKABLE ->
     DEBT, which IS the backlog: the D-drive here is DEBT-DOMINATED.
  g. R5's consolidation cadence is the HARNESS CONSTANT TAU_S_TURNS = 100
     turns (stage2_harness.py:113), NOT Params.tau_S — so at tau_S = 25 or 50
     the routing window still turns over every 100 turns.  A structural fact
     of the harness, reported, not fixed (R2's timescale is the setpoint's).
  h. ROUTING-OFF MEANS ROUTE-ALL (a supported, stated mode): with no selector
     the harness routes every valid span and logs `routed = 0`, since `routed`
     counts SELECTOR-chosen spans.  The runner therefore also reports the
     EXTRACTOR's own span count per turn (what route-all actually routes) —
     without it, a route-all run would look like it routed nothing.
  i. RETRIEVAL IS NOT PRICED in these arms (Stage2Config.retrieval_priced is
     left at its default False), so `st.dmn_self` is "" and the generator's
     SELF block is EMPTY.  The plan's arms do not include retrieval; if the
     pilot's gate 1 fails on a thin stream, THAT is the first thing to check
     — reported, not wired in behind the plan's back.

COST (PROJECTION, from the plan's bake measurement of ~2 s/turn warm at
63 tok/s): 1400 turns ~ 47 min PER RUN; the full matrix 2 x 2 x 3 x 3 = 36
runs ~ 28 GPU-hours.  The pilot measures the real per-turn time and re-states
this projection from the measurement.

**REVISED FOR THE REASONING ARM (MEASURED 2026-09-26, the re-point's live
check, /tmp/repoint_live_check.py + /tmp/repoint_live_diag.py).**  This
module's generator is the GEMMA arm (`api="generate"`, ~2 s/turn at 63
tok/s).  The a_hold mapping's instrument is the REASONING arm
(`api="chat"`, Ministral-3-14B-Reasoning-2512 Q6_K, dmn_llm's second
transport), and it emits a TRACE AS WELL AS the answer: measured on the
same box, same endpoint, seeds 4242+t, temp 0.6, the real DMN prompt with
the self seat's blocks -- **47.8 s/turn** (trace 5281 chars + content 2958
chars, 2 claims, 0 fabricated) and **79.6 s/turn** (trace 9492 chars +
content 2953 chars, 4 claims) warm, at ~40 tok/s, against the gemma arm's
~2 s/turn.  So the SAME 36-run matrix is **~670-1100 GPU-hours** (24-40x
the plan's 28), i.e. the reasoning arm is NOT free and the campaign must
budget for it.  STATED, NOT SMOOTHED: the trace's length VARIES enough to
consume the whole budget -- at num_predict=2600 content was EMPTY in 3/3
turns, and `num_ctx=4096` was itself the binding limit in 2/2 turns at
num_predict=6000 (prompt 1009 + trace 3087 = 4096 exactly), so the
reasoning arm needs BOTH a larger `num_predict` and context headroom for
prompt + trace + content.  That headroom question is NOT settled here: it
is a configuration the campaign must decide and state, and whether a
larger window weakens the self's depletability (the num_ctx design
rationale in dmn_llm) is part of that decision.  n = 5 calls with empty
content and 4 with content (2 per layout); content supply at campaign
scale is PROJECTION.

USAGE
  cd ~/thing/agent && PYTHONPATH=/home/jaye/thing/dpdr:/home/jaye/thing/agent \
    ~/thing/dpdr/.venv/bin/python exp_agent_coupling.py --selftest   # OFFLINE
    ... exp_agent_coupling.py --pilot                                # 150 turns
    ... exp_agent_coupling.py --det-check [--det-turns 20]           # 2 x K turns
    ... exp_agent_coupling.py --full [--n 3] [--dry-run]             # the matrix
    ... exp_agent_coupling.py --matrix <run.json> ...                # OFFLINE

The default mode is --selftest: an accidental invocation cannot reach the
endpoint and cannot start the 28-hour sweep.  The sweep is one explicit flag
(--full) and it is REFUSED without a passing pilot.

========================================================================
THE AGENTEXP2 CAMPAIGN — THE RUNNABLE EXPERIMENT (a SECOND pre-registration
in this file; spec = memory node `handoff-selfreg-agentexp2-plan`).

WHY IT EXISTS, ON THE PAGE.  The matrix above (36 runs x 1400 turns) was the
MODEL's design transposed onto the agent: at the REASONING arm's measured
47-80 s/turn it is 670-1100 GPU-hours [MEASURED,
handoff-selfreg-repoint-result], and it does not even vary the a_hold seat —
the one path by which the agent reaches the plant.  The agentexp2 plan keeps
the CRITERION and replaces the MATRIX: six discriminating conditions (2x2
seat OFF/ON x drive OFF/ON + two controls), the same 1400-turn horizon, the
same G2c form, and a coverage mirror reported as a FOUR-OUTCOME matrix.
The old matrix is NOT deleted and NOT weakened: `--full` still runs it, with
its own pre-registration intact.  This section ADDS a lane.

USAGE
    ... exp_agent_coupling.py --pilot2                        # ONE run, 300 turns
    ... exp_agent_coupling.py --campaign --dry-run            # list + cost, no run
    ... exp_agent_coupling.py --campaign [--cells C2 C3]      # REFUSED w/o pilot2 PASS
    ... exp_agent_coupling.py --det-check2 [--det-turns 300]  # OUTCOME repeatability
    ... exp_agent_coupling.py --selftest                      # OFFLINE (incl. this lane)

(1) THE CHAT PATH IS WIRED, IN ONE PLACE.  `make_generator` below is the
    ONLY place a DMN is constructed, and with `api="chat"` it routes through
    `dmn_llm.make_reasoning_dmn` (api + model + chat_endpoint + num_predict
    named together, NO `think` key — the reasoning model 400s on it).  The
    OLD path called `make_dmn(..., think=False)` directly = the GENERATE
    path; left in place, the campaign would have silently measured the old
    gemma configuration.  Every campaign cell names its own `api` (C1-C5 the
    reasoning arm, C6 the gemma negative), so the transport is a property of
    the cell, not of the environment.
(2) THE SIX CELLS.  C1 SEAT-OFF/BASE-SELF (the healthy control), C2
    SEAT-ON/DRIVE-OFF (the depletion bystander — the attribution control),
    C3 SEAT-ON/DRIVE-ON (THE EXPERIMENT), C4 DRIVE-ON/NO-SEAT (the wrapper /
    seating check), C5 the P2-COUPLING pair (SPEC/OFF, reduced priority,
    run LAST), C6 the PRECONDITION-NEGATIVE CONTROL (gemma through
    /api/generate, length-capped).  The C2/C3 pair differs in ONE thing —
    the schedule wrapper — and shares seeds.
(3) THE HORIZON: 1400 IS KEPT.  The plan weighed it and decided to keep it
    (the criterion window [1000,1400] is the frozen scenario's own G2c
    window; shortening it is the "weaken the criterion to fit the budget"
    move).  The saving is the CELLS (36 -> 6, 3-4 at full length).
(4) THE CRITERION, VERBATIM + THE MIRROR + FOUR OUTCOMES.  PLANT: the
    existing `score_recovery` (G_end > 0.5 AND min G over [1000,1400] > 0.5,
    Stage2LogRow.G) — unchanged, the same function the old matrix uses.
    AGENT: `score_coverage`, the same FORM at threshold 0.5 over the LAST
    consolidation window (TAU_S_TURNS turns) — a STATED CONVENTION mirrored
    from BAND1, never a measured boundary.  Per run the pair is reported as
    ONE of four outcomes (plant+/self+ HEALTHY, plant+/self- DISSOCIATION,
    plant-/self- CO-COLLAPSE, plant-/self+ the UNMODELLED quadrant) and per
    cell as k/N vectors.  NO SUMMARY BIT.
(5) THE VOIDING CONDITIONS (V1-V5), implemented as PREDICATES over the
    logged rows, reported with their reason and their per-run evidence:
    V1 NO-DEPLETION VOID (a seat-on run whose coverage never falls below
    0.5 shows nothing about the seat), V2 CROWDING VOID (empty content in a
    majority of turns saturates the trace share by REGISTER, not by
    depletion; 25-50% is FLAGGED register-degraded, >50% is VOID), V3
    NO-TRACE VOID (a run the transport refused — dmn_llm raises when BOTH
    streams are empty), V4 CONTROL-FAILURE VOID (C1 not recovering voids the
    campaign's acceptance), V5 WIRING VOID (C4's plant trajectory differing
    from C1's).  A voided cell is re-run ONCE with the next seed base and the
    void RATE is reported — the re-run is a measurement, not a retry loop.
(6) THE ACCEPTANCE PREDICATE, PRINTED BEFORE ANY RUN (and written into
    campaign.json with status STARTED before the first cell runs):
      ACCEPT  : C1 (plant+,self+) 3/3 AND C2 (plant+,self-) >= 2/3 AND
                C3 (plant-,self-) >= 2/3 AND the pilot gates held AND the
                void rate is reported.
      FALSIFY : C3 (plant+,self-) 3/3 with real depletion (coverage < 0.5)
                and a live drive (self_drive > 0) — the seat is wired, the
                self depletes, the plant does not care: the a_hold mapping
                fails in the agent at gain 1.0 (equally publishable).
      MIXED   : C3 splitting across seeds is reported as the reliability
                bound, NOT smoothed.
(7) THE DETERMINISM PROTOCOL, REPLACED FOR A REASONING STREAM.  Content
    emission is VARIABLE AT A PINNED SEED (5 empty / 4 content-bearing calls
    on identical inputs; trace 1884-3118 units; ollama's seed determinism is
    "in practice, not contractual" — MEASURED, handoff-selfreg-repoint-
    result), so a bit-level N=3 claim is untenable and is NOT made.  What is
    kept: the per-turn seed = base + turn, base(repeat) = SEED_BASE +
    repeat*STRIDE, the TaskWorld seed FIXED, temperature 0.6.  What replaces
    the bit: acceptance is a FRACTION over seeds (N=3 for C1/C2/C3), the
    per-run TRAJECTORY INVARIANTS and their across-seed spread are reported,
    and `--det-check2` measures OUTCOME-level repeatability (same cell, same
    base seed, twice: the streams differ, the question is whether the outcome
    and the trajectory class do) instead of diffing bytes.
(8) B = 6, ACCEPT AND STATE (the plan's D1).  `derivations_per_turn=6` is the
    only live-arm-calibrated retrieval budget (H9's depletion arm: coverage
    0.1974 -> 0.0409 -> 0.0241 [MEASURED]); the default 10_000 makes coverage
    1.000 forever (cen.py:228 + N <= 4+1400).  STATED CONSEQUENCE, not
    smoothed: B=6 starves the CEN's per-turn work budget from ~turn 6, so in
    the seat-on cells the plant's collapse is the SEAT's (the a_hold path),
    not the CEN's demand — the P2 coupling story is C5's, at reduced
    priority.  Two budget probes (B=3, B=12) are computed OFFLINE from the
    pilot's own logged store size; a BUMP is a mid-campaign decision point,
    never a silent tuning.
(9) --endpoint / --model / --api (+ --chat-endpoint / --chat-model /
    --control-model).  THE HARNESS RUNS LOCALLY (plant, CEN, engine, store);
    ONLY the LLM calls go remote — so a vast.ai ollama (exposed port or ssh
    -L) needs no code change: point --chat-endpoint at it.  The same code
    runs the local 3B and a remote endpoint.
(10) THE PILOT GATE (`--pilot2`) IS MANDATORY AND RUNS FIRST: C3's config,
    300 turns, ONE seed, per-turn printing and JSONL as it lands, gating P1
    SUPPLY (spans > 0 and varying; content non-empty in >= 50% of turns),
    P2 DEPLETION (coverage < 0.5 by turn 300 at B=6), P3 DRIVE LIVE
    (self_drive > 0 after the second boundary AND the plant moved off its
    own arithmetic no-drive baseline), P4 REGISTER (trace/content
    distributions; empty-content rate < 25%), P5 COST (measured s/turn ->
    the full plan re-projected).  `--campaign` REFUSES without a PASS.

WHAT IS *NOT* CHANGED, STATED SO IT CANNOT BE MISREAD: the old matrix's
cells, thresholds, gates and JSONL machinery are untouched; the frozen model,
exp22-24, every cache and every Stage-1 baselined file are read-only here.
The 0.5 coverage mirror is a CONVENTION; the tau_S axis is DROPPED as inert
for the agent (the agent's collapse timescale is the harness constant
TAU_S_TURNS, not Params.tau_S) and the loss is stated in the campaign JSON;
the routing axis is carried INSIDE every cell (routing-on + agent_g when the
seat is on).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import statistics
import sys
import tempfile
import time
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
# the two namespaces the batteries run under (stage2_README's own invocation)
for _p in (os.path.join(_ROOT, "dpdr"), _HERE):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from dpdr.events import rescue_schedule        # noqa: E402
from dpdr.model import Params                  # noqa: E402

from cen import CostBudget, WriterToken      # noqa: E402
import dmn_llm                                 # noqa: E402
from dmn_llm import TaskWorld, make_dmn        # noqa: E402
from interleave import extract_spans           # noqa: E402
from routingcrit import (PrefixRoutingSelector,          # noqa: E402
                         RoutingCriterionStore, publish_criterion)
from stage2_harness import (Stage2Config, TAU_S_TURNS,   # noqa: E402
                            run_stage2)

__all__ = ["score_recovery", "gate_pilot", "assemble_matrix",
           "evaluate_acceptance", "plan_cells", "project_cost",
           # -- the agentexp2 campaign lane (handoff-selfreg-agentexp2-plan) --
           "score_coverage", "score_run", "four_outcome", "void_predicates",
           "campaign_conditions", "campaign_plan", "assemble_campaign",
           "evaluate_campaign", "evaluate_c5", "pilot2_gates",
           "plant_no_drive_baseline", "probe_budgets", "make_generator"]


# ==========================================================================
# THE PRE-REGISTERED CONSTANTS.  Every one is the plan's own number; an
# override is recorded, never silent.
# ==========================================================================

PREREG_NODE = "handoff-selfreg-agentexp-plan"
RESULT_NODE = "handoff-selfreg-agentexp-result"

TURNS_FULL = 1400          # the plan's horizon T = 1400 turns = 1400 t.u.
PILOT_TURNS = 150          # the plan's pilot: ~150 turns
TAU_S_CELLS = (25.0, 50.0, 100.0)          # THE ARMING CELLS (F1 in exp22)
ROUTINGS = ("route-all", "routing-on")
ARMS = ("SPEC", "OFF")
N_DEFAULT = 3              # the plan: N >= 3
BAND1 = 0.5                # the project's recovery threshold (exp22 BAND1)
WINDOW_T0 = 1000.0         # the G2c stay window: t in [1000, 1400]
T_RESCUE = 800.0           # rescue_schedule's rescue_t0 (the frozen scenario)
SEED_BASE_DEFAULT = 4242   # the bake's base seed (dmn_llm's own default)
SEED_STRIDE = 10000        # repeats never share a per-turn seed
WORLD_SEED = 11            # TaskWorld seed: FIXED across every repeat
DEFAULT_OUTDIR = os.path.join(_HERE, "cache", "agent_coupling")
#: SPEC must FAIL in >= 2/N at each of these cells (the plan's acceptance)
SPEC_FAIL_CELLS = (50.0, 100.0)
#: the plan's own projection, re-stated from the pilot's measurement
PROJECTED_S_PER_TURN = 2.0


# --------------------------------------------------------------------------
# THE AGENTEXP2 CAMPAIGN'S PRE-REGISTERED CONSTANTS (handoff-selfreg-
# agentexp2-plan).  Separate names so a reader can never confuse the two
# pre-registrations: the ones above are the OLD matrix's, these are the
# campaign's, and neither overrides the other.
# --------------------------------------------------------------------------
CAMPAIGN_PREREG_NODE = "handoff-selfreg-agentexp2-plan"
CAMPAIGN_RESULT_NODE = "handoff-selfreg-agentexp2-result"

CAMPAIGN_TURNS = TURNS_FULL          # (3) THE DECIDED HORIZON: KEEP 1400.
PILOT2_TURNS = 300                   # the plan's minimum arc for the PILOT
CONTROL_CAP_TURNS = 300              # C6 is length-capped at the first boundary
CAMPAIGN_BUDGET = 6                  # (8) D1: the live-arm-calibrated budget
CAMPAIGN_DEFAULT_BUDGET = 10_000     # cen.CostBudget's own default (C1/C4)
CAMPAIGN_SELF_T = 100                # the commitment horizon T (turns)
CAMPAIGN_N = 3                       # N >= 3 for the full-length cells
CAMPAIGN_NUM_PREDICT = 6000          # (F)/D2: above the trace, both cuts
CAMPAIGN_NUM_CTX = 8192              # D2, with its reason stated (see below)
#: (F2) THE BREVITY INSTRUCTION, ON FOR EVERY CELL — a CONFIG fix for the
#: MEASURED runaway-reasoning defect, justified because the precondition was
#: RE-VERIFIED under it (dmn_llm.build_prompt carries the numbers and the
#: re-verified sign).  A module constant, not a literal at the call site,
#: because it is part of the FIXED INSTRUMENT: it is in the run's identity
#: (CAMPAIGN_IDENTITY_FIELDS) and in every run JSON, so a resumed run
#: cannot be the same measurement as one taken without it.
CAMPAIGN_BRIEF = True
EMPTY_CONTENT_FLAG_RATE = 0.25       # V2: register-degraded (reported)
EMPTY_CONTENT_VOID_RATE = 0.50       # V2: VOID above this
VOID_RERUNS_PER_CELL = 1             # (E): one re-run per void, recorded
PLANT_MOVE_EPS = 1e-9                # P3: "the plant moved" — see pilot2_gates
COVERAGE_MIRROR_BAND = BAND1         # (4) the mirror's threshold, CONVENTION
#: the run order is the plan's LADDER (gates first, controls last), not the
#: C-numbering: C2/C3 are the attribution pair, C1 the clean control, then
#: the wiring check, the precondition negative, and C5 last.
CAMPAIGN_PHASE_ORDER = ("C2", "C3", "C1", "C4", "C6", "C5")


def ts() -> str:
    return time.strftime("%H:%M:%S")


def log(msg: str) -> None:
    print(f"[{ts()}] {msg}", flush=True)


def _warn(msg: str) -> None:
    print(f"[{ts()}] WARNING: {msg}", flush=True)


def _num(x, spec: str = ".6f") -> str:
    """Format an optional number for the PRINTED report: a run that stopped
    before producing a row has None here, and the report must survive it (the
    JSON keeps the None — an absent measurement is not a zero)."""
    if x is None:
        return "n/a"
    if isinstance(x, float) and x != x:      # NaN: no measurement
        return "n/a"
    return format(x, spec)


# ==========================================================================
# THE CRITERION (pure; the offline selftest's subject).
# ==========================================================================

def _field(row, name: str):
    """Read one field of a row that is EITHER the harness's Stage2LogRow
    (attribute) OR a recorded row (dict) — one accessor, so the offline test
    can exercise the SAME scorer the runs are scored with."""
    if isinstance(row, dict):
        return row[name]
    return getattr(row, name)


def score_recovery(rows, band: float = BAND1, t0: float = WINDOW_T0,
                   t_end: float = float(TURNS_FULL)) -> dict:
    """THE G2c CATEGORICAL CRITERION, VERBATIM FROM THE PRE-REGISTRATION.

        recovered = (G_end > band) AND (min G over t in [t0, t_end] > band)

    `rows` is any sequence carrying `t` and `G` — the harness's Stage2LogRow
    (attribute access) or a recorded row (dict); both paths are exercised by
    the offline selftest, and the runs are scored through this same function.
    G_end is the LAST row's G — the horizon value, not the window's last
    value.  An EMPTY stay window makes the second clause UNMEET (False),
    never vacuously true: a run that stopped before t0 did not demonstrate
    sustained recovery."""
    win = [float(_field(r, "G")) for r in rows
           if t0 <= float(_field(r, "t")) <= t_end]
    g_end = float(_field(rows[-1], "G")) if rows else float("nan")
    g_min_post = min(win) if win else float("nan")
    ok = bool(win) and g_end > band and g_min_post > band
    return {"G_end": g_end, "G_min_post": g_min_post,
            "recovered": bool(ok), "n_window": len(win),
            "band": band, "window": [t0, t_end]}


def _supply_stats(per_turn: list) -> dict:
    """The generator's supply, as the extractor saw it: per-turn span counts
    (what route-all actually routes) and char counts (the raw stream size).
    `per_turn` is a list of dicts with 'spans' and 'chars'."""
    spans = [int(d["spans"]) for d in per_turn]
    chars = [int(d["chars"]) for d in per_turn]
    if not spans:
        return {"turns": 0, "spans_total": 0, "spans_min": 0,
                "spans_max": 0, "spans_mean": 0.0, "distinct_span_counts": 0,
                "chars_min": 0, "chars_max": 0, "chars_mean": 0.0,
                "distinct_char_counts": 0, "empty_turns": 0}
    return {"turns": len(spans), "spans_total": int(sum(spans)),
            "spans_min": int(min(spans)), "spans_max": int(max(spans)),
            "spans_mean": float(sum(spans)) / len(spans),
            "distinct_span_counts": len(set(spans)),
            "chars_min": int(min(chars)), "chars_max": int(max(chars)),
            "chars_mean": float(sum(chars)) / len(chars),
            "distinct_char_counts": len(set(chars)),
            "empty_turns": int(sum(1 for s in spans if s == 0))}


# ==========================================================================
# THE PILOT GATE (pure; takes the per-turn records, returns pass/fail).
# ==========================================================================

def gate_pilot(per_turn: list, *, warmup: int = 10) -> dict:
    """Evaluate the plan's pilot gates on the per-turn records the pilot
    collected.  The PREDICATES are stated in the module docstring and are
    printed with the verdict, so a later reader sees exactly what was asked.

    THE GATE IS GATES 1-3, EXACTLY AS PRE-REGISTERED.  `diagnostics_not_gates`
    below carries ADDITIONAL MEASURED FACTS the pilot is obliged to report and
    the plan's gate list does not name — they are printed beside the verdict
    and NEVER enter `status`.  They exist because the pilot's job is to say
    whether the REGIME is right before 80 GPU-hours are spent, and two
    regime facts decide that in the agent (both MEASURED, neither a gate):
      * WHETHER THE CANNIBALIZATION SWITCH EVER ARMS.  ROUND 2: the Stage-2
        plant runs the FROZEN MODEL's floorless switch (Θ_eff = Θ·S/S_rest,
        dpdr/model.py:92-94 — supplied by the caller, so the baselined
        harness.py keeps its own default 0.7 for Stage-1 code).  The
        REGULATOR's written-down floor survives as the SN's ACTIVATION
        BELIEF (stage2_harness.SN_ACTIVATION_FLOOR, reported here as such)
        and is NOT the level this plant arms at.  If c stays 0 for the
        pilot's whole horizon, the plan's F3 channels (which act THROUGH c)
        are inert for THAT horizon — and the pilot's 150 turns are not the
        experiment's 1400.  REPORTED, never silently assumed armed.
      * THE COUPLING'S UNIT — A GATE, ON THE OBJECT THE MODEL NAMES.  The
        P2 addend is the PLANT's own B = EMA_tauD(c), c the plant's switch
        state (the model's ONE c, which also drives the attention pinning
        k_in*(a_hold + mon_cost + chi*c)) — dimensionless in [0,1].  Round 1
        fed the raw assertion COUNT through the schedule's 'A' port, a STOCK
        with no counterpart in the model (saturated D at 0.99316 against the
        model's own ceiling 0.8387 at B = 1); the reconciliation then fed
        the CEN's measured u/n, which is the substrate's reading of the same
        quantity but does NOT reach the plant.  Both are still printed, in
        their own blocks: `B_plant` (the addend) and `B_telemetry` (u/n) —
        never conflated, and the gate is on the first.

    `per_turn` rows carry: turn, t, c, G, D, E, S, backlog (outstanding),
    backlog_ema (the raw STOCK, telemetry), backlog_rate (the CEN's u/n EMA,
    telemetry), B_plant (THE P2 ADDEND: the plant's own EMA_tauD(c)),
    A_eff (the plant's own measured drive = A + B), routed, spans,
    verdicts_V/R/U, secs."""
    n = len(per_turn)
    supply = _supply_stats(per_turn)
    gate1 = bool(supply["spans_total"] > 0
                 and supply["distinct_span_counts"] > 1)

    backlog = [int(r["backlog"]) for r in per_turn]
    half = max(1, n // 2)
    first, second = backlog[:half], backlog[half:]
    mean_first = statistics.fmean(first) if first else 0.0
    mean_second = statistics.fmean(second) if second else 0.0
    early = backlog[min(10, n - 1)] if n else 0
    late = backlog[-1] if n else 0
    gate2 = bool(mean_second > mean_first and (max(backlog) > min(backlog))
                 if backlog else False)

    # GATE 3 IS ON THE P2 ADDEND: B, the quantity the coupling actually
    # adds to D's drive (the EMA at tau_D of the unchecked-accrual rate,
    # the model's own scale).  The raw backlog STOCK EMA beside it is
    # reported as telemetry — it is NOT B, and a gate on it would pass
    # even if the coupling fed an unnormalized count.
    rates = [float(r["backlog_rate"]) for r in per_turn
             if r.get("backlog_rate") is not None]
    emas = [float(r["backlog_ema"]) for r in per_turn
            if r.get("backlog_ema") is not None]
    # ROUND 2: THE GATE'S OBJECT IS THE PLANT'S OWN B — the addend the
    # plant's D is driven with (Agent.B = EMA_tauD(c), the model's one c).
    # The u/n EMA (`rates`) is the CEN's telemetry and does NOT reach the
    # plant; gating on it would pass while the coupling was inert in the
    # plant, which is exactly round 1's error in the other direction.
    bplant = [float(r["B_plant"]) for r in per_turn
              if r.get("B_plant") is not None]
    if not bplant:      # legacy rows without the field: fall back, and say so
        bplant = [float(_field(r, "edge_addend")) for r in per_turn
                  if r.get("edge_addend") is not None]
    gate3 = bool(bplant and max(bplant) > 1e-9)
    # the TELEMETRY build (the CEN's own measurement) is reported beside the
    # gate, never substituted for it.
    gate3_telemetry = bool(rates and max(rates) > 1e-9)
    gate3_range_ok = bool(bplant and 0.0 <= min(bplant)
                          and max(bplant) <= 1.0 + 1e-9)

    secs = [float(r["secs"]) for r in per_turn if r.get("secs") is not None]
    post = secs[warmup:] if len(secs) > warmup else secs
    per_turn_s = (statistics.median(post) if post else float("nan"))
    cost = project_cost(per_turn_s, n_cells=2 * 2 * len(TAU_S_CELLS) * N_DEFAULT)
    return {
        "n_turns": n,
        "supply": supply,
        "backlog": {"first_half_mean": mean_first,
                    "second_half_mean": mean_second,
                    "early_turn10": early, "final": late,
                    "min": (min(backlog) if backlog else 0),
                    "max": (max(backlog) if backlog else 0)},
        "backlog_ema": {"max": (max(emas) if emas else 0.0),
                        "final": (emas[-1] if emas else 0.0),
                        "role": "the raw assertion STOCK, EMA'd — "
                                "TELEMETRY, not the P2 addend"},
        "B_p2": {"max": (max(bplant) if bplant else 0.0),
                 "final": (bplant[-1] if bplant else 0.0),
                 "role": "THE P2 ADDEND the plant's D is driven with: the "
                         "plant's own Agent.B = the EMA at tau_D of its "
                         "switch state c (the model's ONE c), logged as "
                         "Stage2LogRow.edge_addend / row 'B_plant'.  This "
                         "is the gate 3 object."},
        "B_telemetry": {"max": (max(rates) if rates else 0.0),
                        "final": (rates[-1] if rates else 0.0),
                        "role": "the CEN's measured UNCHECKED-ACCRUAL SHARE "
                                "u/n, EMA'd at tau_D (Stage2State."
                                "backlog_rate): the substrate's own reading, "
                                "carried as telemetry — it reaches the CEN "
                                "and the telemetry only, NOT the plant's D "
                                "and NOT the router's inputs (the law is fed "
                                "the plant's own B — see B_p2)"},
        "gate3_B_telemetry_builds": gate3_telemetry,
        "timing": {"per_turn_median_s": per_turn_s,
                   "per_turn_mean_s": (statistics.fmean(post) if post
                                       else float("nan")),
                   "warmup_turns_excluded": min(warmup, n)},
        "gate1_supply_nonempty_varying": gate1,
        "gate2_backlog_rises": gate2,
        # the KEY keeps the plan's own gate name (a pre-registration
        # leaves it alone); the OBJECT is the P2 addend B — see
        # `predicates.gate3` and `B_p2`.  `gate3_B_in_model_range` is the
        # unit check the reconciliation added: it FAILS if the coupling
        # ever feeds anything outside the model's own [0,1].
        "gate3_backlog_ema_builds": gate3,
        "gate3_B_in_model_range": gate3_range_ok,
        "gate4_projected_cost": cost,
        "diagnostics_not_gates": pilot_diagnostics(per_turn),
        "status": "PASS" if (gate1 and gate2 and gate3) else "FAIL",
        "predicates": {
            "gate1": "(spans_total > 0) AND (distinct per-turn span counts > 1)",
            "gate2": "(mean backlog[second half] > mean backlog[first half]) "
                     "AND (max backlog > min backlog)",
            "gate3": "(max B > 1e-9): strictly positive on the P2 ADDEND B "
                     "— the addend the PLANT's D is actually driven with, "
                     "i.e. Agent.B = the EMA at tau_D of the plant's switch "
                     "state c (row 'B_plant' / Stage2LogRow.edge_addend).  "
                     "The CEN's u/n EMA is reported beside it as telemetry "
                     "(gate3_B_telemetry_builds) and is NOT the gate: it "
                     "does not reach the plant",
            "gate3_range": "(0 <= min B) AND (max B <= 1): the plant's own "
                           "addend is inside the model's own B range (the "
                           "switch state c in [0,1])",
            "gate4": "not pass/fail: measured per-turn wall time -> "
                     "projected full-matrix cost",
            "diagnostics": "NOT gates — measured regime facts reported "
                           "beside the verdict (the switch's arming state; "
                           "the coupling's unit against the model's own "
                           "D-equilibrium)",
        },
    }


def pilot_diagnostics(per_turn: list) -> dict:
    """The regime facts the pilot must report and the pre-registered gate
    list does not name (see `gate_pilot`).  PURE over the rows, and it
    NEVER contributes to the gate's status.

    ROUND 2 SEMANTICS, both of them load-bearing:
      * THE PLANT'S ARMING LEVEL IS THE MODEL'S.  The Stage-2 plant runs
        the frozen model's FLOORLESS switch (dpdr/model.py:92-94,
        Theta_eff = Theta*S/S_rest), supplied by the caller
        (stage2_harness builds AgentConfig(sn=SNConstants.from_params(
        p, floor=None))) — the baselined harness.py is untouched, so the
        Stage-1 default (0.7) is still there for Stage-1 code.  The
        regulator's written-down floor lives on as the SN's ACTIVATION
        BELIEF (stage2_harness.SN_ACTIVATION_FLOOR) and is reported as
        such; it is NOT the level this plant arms at.
      * THE TWO ADDENDS ARE DISTINGUISHED.  `B_plant` is the plant's own
        B = EMA_tauD(c) (the quantity the P2 addend IS); `backlog_rate`
        is the CEN's measured u/n (telemetry, does not reach the plant).
        The diagnostic reports both and asserts the identity that makes
        the router trustworthy: the plant's B is what the law's
        D-analogue was built from (Stage2State.p2_addend)."""
    from harness import AgentConfig
    from routing import demand_analogue
    import stage2_harness as _H2

    p = Params()
    # the level THIS substrate's plant arms at: the model's own, because
    # the Stage-2 caller supplies floor=None.  Asserted live, not assumed.
    plant_floor = _H2.agent_config_for_stage2(
        p, _H2.Stage2Config()).sn.floor
    cs = [float(r["c"]) for r in per_turn if r.get("c") is not None]
    Es = [float(r["E"]) for r in per_turn if r.get("E") is not None]
    emas = [float(r["backlog_ema"]) for r in per_turn
            if r.get("backlog_ema") is not None]
    rates = [float(r["backlog_rate"]) for r in per_turn
             if r.get("backlog_rate") is not None]
    bplant = [float(r["B_plant"]) for r in per_turn
              if r.get("B_plant") is not None]
    aeffs = [float(r["A_eff"]) for r in per_turn
             if r.get("A_eff") is not None]
    Ds = [float(r["D"]) for r in per_turn if r.get("D") is not None]
    Ss = [float(r["S"]) for r in per_turn if r.get("S") is not None]
    c_max = max(cs) if cs else 0.0
    b_max = max(bplant) if bplant else 0.0
    a_eff = max(aeffs) if aeffs else 0.0
    theta_eff_final = (p.Theta * Ss[-1] / p.S_rest) if Ss else None
    # the level the plant's switch arms at (floorless in this substrate)
    bind = (max(theta_eff_final, plant_floor)
            if (theta_eff_final is not None and plant_floor is not None)
            else theta_eff_final) if theta_eff_final is not None else 0.0
    return {
        "cannibalization": {
            "c_max": c_max,
            "c_sum": sum(cs),
            "armed_in_pilot": bool(c_max > 0.0),
            "E_max": (max(Es) if Es else None),
            "E_final": (Es[-1] if Es else None),
            "plant_arming_level_is_model": plant_floor is None,
            "plant_switch_floor": plant_floor,
            "sn_activation_floor": _H2.SN_ACTIVATION_FLOOR,
            "theta_eff_final": theta_eff_final,
            "binding_level": bind,
            "stage1_default_floor_still": AgentConfig().sn.floor,
            "note": ("the plant's switch needs E > Theta*S/S_rest "
                     "(FLOORLESS: this substrate runs the frozen model's "
                     "switch, dpdr/model.py:92-94).  If armed_in_pilot is "
                     "False over the pilot's horizon, the plan's F3 "
                     "channels (which act THROUGH c) are inert for THAT "
                     "horizon — the pilot's 150 turns are not the "
                     "experiment's 1400.  `sn_activation_floor` is the SN's "
                     "written-down constant kept as the regulator's own "
                     "ACTIVATION BELIEF (existence semantics, 0.5-1.3 "
                     "escape identically; never re-checked — a floor held "
                     "with a discrepancy monitor fails at kc ~ 0.2, exp6 "
                     "part d).  It is NOT the level this plant arms at: "
                     "feeding it there pinned Theta_eff for the whole "
                     "inward range (0.8*S < 0.7 for S < 0.875) and deleted "
                     "the state-dependence the model's collapse and R2's "
                     "law both use"),
        },
        "coupling_scale": {
            # THE P2 ADDEND, ON THE MODEL'S OWN SCALE: the PLANT's own
            # B = EMA_tauD(c) — c the plant's switch state, the model's ONE
            # c (which also drives the attention pinning).  The CEN's
            # measured u/n is reported beside it as telemetry.
            "B_plant_max": b_max,
            "B_plant_final": (bplant[-1] if bplant else None),
            "model_B_range": [0.0, 1.0],
            "B_telemetry_u_over_n_max": (max(rates) if rates else None),
            "A_eff_max_measured": a_eff,
            "A_eff_in_model_range": bool(
                aeffs and max(aeffs) <= 1.5 + 1e-9
                and min(aeffs) >= 0.0),
            "A_eff_range_note": ("A_eff = A + B with A the schedule's own "
                                 "demand addend (the rescue scenario's A "
                                 "pulse is 0.5 on t in [100,160)) and "
                                 "B = the plant's own c-EMA in [0,1], so "
                                 "the model's range here is [0, 1.5] — "
                                 "NOT [0,1]"),
            "backlog_ema_max_STOCK_not_B": (max(emas) if emas else None),
            "D_equilibrium_at_A_eff": (demand_analogue(a_eff, 0.0, p)
                                       if a_eff else None),
            "D_observed_max": (max(Ds) if Ds else None),
            "D_base": p.D_base,
            "beta_D": p.beta_D,
            "delta_D": p.delta_D,
            "note": ("the P2 addend is the plant's own B on the model's "
                     "scale (zero free constants: tau_D reused, coefficient "
                     "1, B(0) = 0).  A_eff_max is the plant's OWN measured "
                     "drive (Stage2LogRow.A_eff = A + B).  The CEN's u/n "
                     "EMA is TELEMETRY: it is the substrate's reading of "
                     "the same quantity and it does NOT drive the plant — "
                     "the model has one c and it is the plant's.  "
                     "`backlog_ema` is the raw assertion STOCK — also "
                     "telemetry, and feeding it as the addend saturated D "
                     "at 0.99316 (the model's own ceiling at B = 1 is "
                     "0.8387).  REPORTED, never reconciled by rescaling"),
        },
    }


def project_cost(per_turn_s: float, n_cells: int,
                 turns: int = TURNS_FULL) -> dict:
    """PROJECTION from a MEASURED per-turn time.  Recomputed at run time,
    never carried as a constant."""
    if per_turn_s is None or not (per_turn_s == per_turn_s) or per_turn_s <= 0:
        return {"cells": n_cells, "turns_per_run": turns,
                "per_turn_s": per_turn_s, "per_run_hours": None,
                "total_hours": None}
    per_run = per_turn_s * turns
    return {"cells": n_cells, "turns_per_run": turns,
            "per_turn_s": float(per_turn_s),
            "per_run_s": per_run, "per_run_hours": per_run / 3600.0,
            "total_hours": per_run * n_cells / 3600.0}


# ==========================================================================
# THE MATRIX: cell enumeration, assembly and the acceptance line.
# ==========================================================================

def seed_base_for(repeat: int, base: int = SEED_BASE_DEFAULT) -> int:
    """The per-repeat BASE sampling seed.  The PER-TURN seed is
    base + turn (dmn_llm.LLM_DMN._body), so the stride must exceed the
    horizon for two repeats never to share a per-turn seed."""
    assert SEED_STRIDE > TURNS_FULL, "seed stride would alias across repeats"
    return int(base) + int(repeat) * SEED_STRIDE


def cell_of(routing: str, arm: str, tau_S: float, repeat: int) -> dict:
    base = seed_base_for(repeat)
    return {"routing": routing, "arm": arm, "tau_S": float(tau_S),
            "repeat": int(repeat), "seed_base": base,
            "cell_id": (f"{routing}-{arm}-t{tau_S:g}-s{base}")}


def plan_cells(n: int, routings=ROUTINGS, arms=ARMS,
               cells=TAU_S_CELLS) -> list:
    """The pre-registered matrix, in a FIXED order (routing, arm, tau_S,
    repeat) so a partial sweep is still a prefix of the plan and the missing
    cells are unambiguous in the assembled matrix."""
    out = []
    for routing in routings:
        for arm in arms:
            for tau in cells:
                for rep in range(int(n)):
                    out.append(cell_of(routing, arm, tau, rep))
    return out


def assemble_matrix(runs: list) -> dict:
    """Pure assembly: a list of run summaries -> the per-cell matrix with the
    categorical vectors per (routing, arm).  Missing runs are reported as
    missing, never as zeros — an absent cell and a failed cell are different
    facts."""
    routings = sorted({r["config"]["routing"] for r in runs}) or list(ROUTINGS)
    arms = sorted({r["config"]["arm"] for r in runs}) or list(ARMS)
    cells = TAU_S_CELLS
    per = {ro: {a: {c: {"n": 0, "rec": 0, "runs": []}
                    for c in cells} for a in arms} for ro in routings}
    for r in runs:
        ro, a, tau = (r["config"]["routing"], r["config"]["arm"],
                      float(r["config"]["tau_S"]))
        if ro not in per or a not in per[ro]:
            continue
        bucket = per[ro][a].setdefault(tau, {"n": 0, "rec": 0, "runs": []})
        bucket["n"] += 1
        bucket["rec"] += 1 if r["result"]["recovered"] else 0
        bucket["runs"].append(r["config"]["cell_id"])
    vectors, fractions, counts = {}, {}, {}
    for ro in routings:
        vectors[ro], fractions[ro], counts[ro] = {}, {}, {}
        for a in arms:
            counts[ro][a] = [per[ro][a][c]["rec"] for c in cells]
            vectors[ro][a] = [per[ro][a][c]["rec"] for c in cells]
            fractions[ro][a] = [(per[ro][a][c]["rec"] / per[ro][a][c]["n"]
                                 if per[ro][a][c]["n"] else None)
                                for c in cells]
    return {
        "prereg": PREREG_NODE, "runner": os.path.relpath(
            os.path.abspath(__file__), _ROOT),
        "task": "the agent-side coupling experiment (paper 2's demonstration)",
        "cells_tau_S": list(cells),
        "routings": routings, "arms": arms,
        "per_cell": {ro: {a: {f"t{float(c):g}": {
            "n": per[ro][a][c]["n"], "recovered": per[ro][a][c]["rec"],
            "runs": per[ro][a][c]["runs"]} for c in cells}
            for a in arms} for ro in routings},
        "recovered_count": counts,          # the raw counts (the vector)
        "recovered_fraction": fractions,    # the acceptance FRACTION
        "n_per_cell": {ro: {a: [per[ro][a][c]["n"] for c in cells]
                            for a in arms} for ro in routings},
        "n_per_cell_reported": {f"{ro}/{a}": (per[ro][a][TAU_S_CELLS[0]]["n"],
                                              per[ro][a][TAU_S_CELLS[-1]]["n"])
                                for ro in routings for a in arms},
        "runs_present": len(runs),
        "vectors_note": (
            "convention = tau_S cells in order " + repr(list(cells))
            + "; counts are (recovered runs) of N per cell"),
    }


def evaluate_acceptance(counts: dict, n: int, cells=TAU_S_CELLS,
                        n_per_cell: dict | None = None) -> dict:
    """THE PLAN'S ACCEPTANCE LINE, as a predicate over the recovered COUNTS.

    ACCEPT   : OFF recovers in N/N at every arming cell (the control is
               CLEAN) AND SPEC fails in >= 2/N at each of tau_S = 50 and 100
               in AT LEAST ONE routing setting.
    VOID     : the control is dirty — OFF fails anywhere.  A dirty control
               measures the generator's stochasticity, not the coupling.
               The strict reading (the plan's words: "if OFF fails anywhere
               the run is VOID") is over BOTH routing settings; the
               per-setting reading is ALSO reported so a reader can see
               which reading produced which verdict.
    FALSIFY  : SPEC recovers N/N at every cell in BOTH routing settings with
               real supply and real backlog growth -> the model's P2 coupling
               does not transfer to the agent.
    INCONCLUSIVE: the full matrix, reported as it is.

    THE DENOMINATOR IS PER CELL, not the global --n.  A cell that carries
    MORE runs than the declared N (a re-run, a filtered pass, a resumed
    sweep) must be judged on its own denominator: a cell with 4 runs of which
    3 recovered is 3/4, NOT clean-at-N=3.  [MEASURED — the first draft used
    the global N and this exact case read CLEAN; the selftest's mixed-
    denominator arm caught it.]  A cell with NO runs is NOT clean (an absent
    control is not a passing control).

    "fails in >= 2/N" is implemented as BOTH an integer fact (fail_count >= 2)
    and a fraction fact (fail_count / n_cell >= 2 / n_declared); with
    n_cell == n_declared the two coincide, exactly the plan's reading."""
    cells = list(cells)
    routings = sorted(counts)
    nd = int(n) if n else 0

    def _ncell(ro, arm, i):
        if n_per_cell and ro in n_per_cell and arm in n_per_cell[ro]:
            return int(n_per_cell[ro][arm][i])
        return nd

    def _cnt(ro, arm, i):
        if arm in counts.get(ro, {}):
            return int(counts[ro][arm][i])
        return 0                       # an arm never run: not a pass

    def _clean(ro, arm) -> bool:
        return all(_ncell(ro, arm, i) > 0
                   and _cnt(ro, arm, i) == _ncell(ro, arm, i)
                   for i in range(len(cells)))

    def _fails(ro, arm) -> list:
        return [_ncell(ro, arm, i) - _cnt(ro, arm, i)
                for i in range(len(cells))]

    off_clean = {ro: _clean(ro, "OFF") for ro in routings}
    spec_clean = {ro: _clean(ro, "SPEC") for ro in routings}
    spec_fail = {ro: _fails(ro, "SPEC") for ro in routings}
    idx = {float(c): i for i, c in enumerate(cells)}

    def _fails_at_50_100(ro) -> bool:
        f = spec_fail[ro]
        if 50.0 not in idx or 100.0 not in idx or nd <= 0:
            return False
        ok = True
        for c in (50.0, 100.0):
            i = idx[c]
            n_cell = _ncell(ro, "SPEC", i)
            count_ok = f[i] >= 2
            frac_ok = (n_cell > 0 and f[i] / n_cell >= 2.0 / nd)
            ok = ok and count_ok and frac_ok
        return ok

    off_clean_all = all(off_clean.values())
    off_clean_any = any(off_clean.values())
    accept_any = any(_fails_at_50_100(ro) for ro in routings if off_clean[ro])
    falsify_both = all(spec_clean.values())

    if not off_clean_any:
        status = "VOID"
        reason = ("the OFF control fails to recover in at least one arming "
                  "cell in EVERY routing setting — a dirty control measures "
                  "the generator, not the coupling")
    elif not off_clean_all:
        status = "ACCEPT" if accept_any else "INCONCLUSIVE"
        reason = ("the OFF control is dirty in some routing setting but "
                  "clean in at least one; the PER-SETTING reading is the "
                  "operative one here — the strict reading would be VOID")
    elif accept_any:
        status = "ACCEPT"
        reason = ("OFF is clean in N/N at every arming cell and SPEC fails "
                  "in >= 2/N at tau_S in {50,100} in at least one routing "
                  "setting")
    elif falsify_both:
        status = "FALSIFY"
        reason = ("SPEC recovers N/N at every cell in BOTH routing settings: "
                  "the model's P2 coupling did NOT transfer to the agent — "
                  "the ordinal mapping fails HERE (an equally publishable "
                  "result)")
    else:
        status = "INCONCLUSIVE"
        reason = ("OFF is clean, but SPEC neither fails >= 2/N at {50,100} in "
                  "any routing setting nor recovers N/N everywhere — the "
                  "full matrix is the result")
    return {"status": status, "reason": reason, "n": nd,
            "cells": cells,
            "control_clean_by_routing": off_clean,
            "control_clean_all_routings": off_clean_all,
            "spec_fail_count_by_routing": spec_fail,
            "spec_fails_at_50_100": {ro: _fails_at_50_100(ro)
                                     for ro in routings},
            "spec_clean_everywhere_by_routing": spec_clean,
            "strict_reading": ("VOID if OFF is dirty in ANY routing setting; "
                               "ACCEPT if SPEC misses >= 2/N at both 50 and "
                               "100 in at least one setting"),
            "denominator_convention": ("per-cell N (n_per_cell), never the "
                                       "global --n; a cell with no runs is "
                                       "not clean"),
            "fraction_form": {ro: {a: [(counts[ro][a][i] / _ncell(ro, a, i)
                                       if _ncell(ro, a, i) else None)
                                       for i in range(len(cells))]
                                   for a in counts[ro]} for ro in routings},
            "per_setting_status": {
                ro: ("VOID" if not off_clean[ro]
                     else ("ACCEPT" if _fails_at_50_100(ro)
                           else ("FALSIFY" if spec_clean[ro]
                                 else "INCONCLUSIVE")))
                for ro in routings}}


# ==========================================================================
# THE RUN: harness config, the recording generator, incremental output.
# ==========================================================================

class RecordingDMN:
    """Read-only observation of every emission (R5: the runner OBSERVES; the
    injected selector — not this wrapper — decides what routes).  The stream
    is returned UNCHANGED.  A non-str emission is refused here, naming the
    mode: with route-all every valid span routes, and with routing-on the
    EXTRACTOR decides, so BOTH arms hand over the raw stream.

    THE INWARD CHANNEL RIDES THROUGH THE WRAPPER.  The harness reads
    `last_inward` OFF THE CALLABLE IT IS GIVEN (`stage2_harness._inward_of`
    -> `selfmodel.inward_share_trace` when it is a str, the pre-trace
    prose/stream share when it is None).  A wrapper that swallowed it would
    silently DEMOTE the a_hold seat to the pre-trace instrument — a fidelity
    drift invisible in the output (the same gap `dmn_llm.stream_to_batch`
    closes for the batch path, and the runner's own path had it).  Forwarded
    here, and asserted by the offline selftest.

    The per-turn record also carries the REGISTER observables the campaign's
    voiding conditions read (V2/V3): the trace's and the content's char
    counts and the transport's own `done_reason`/`eval_count`.  `trace_chars`
    is None — never 0 — when the emitter declares no inward channel (the
    /api/generate path): an absent channel is not an empty one.

    TWO ADDITIONS FOR THE CORRECTED EXPERIMENT (both additive; every
    pre-change caller's bytes are untouched):

      * THE UNIVERSE IS NO LONGER SWALLOWED.  `stage2_harness._universe_of`
        reads `last_universe` or `world` OFF THE CALLABLE IT IS GIVEN, and
        this wrapper declared neither — so with the action seat ON every
        `complete(tNN)` span was refused `universe_undefined` and the task
        could not adjudicate through the runner's own wrapper at all [M —
        the corrected experiment's code fact F4].  Both are now forwarded
        from the inner emitter, verbatim and with no fallback of the
        wrapper's own: an inner with neither still yields UNDEFINED (None),
        which is the same measurement the docstring above insists on —
        absent is not empty, and it is not invented.
      * THE TRACE TEXT IS RECORDED (`trace_text`), not only its length.
        The SIGN PROBE's density observable — self-referential content per
        100 words of the thought channel, `ops/density_test.py`'s own regex
        — cannot be re-run offline on traces that were not kept, and the
        corrected experiment's MANIPULATION gate is exactly that re-run
        (self-ref density in the PRESENT arm must exceed the ABSENT arm's
        over the first window, or the manipulation did not manipulate).
        COST, STATED: a trace is ~2-11 KB/turn at the observed sizes
        (1884-3118 units measured in the pilot), i.e. ~1-3 MB per 300-turn
        run held in RAM and written into the run's JSON summary.  `None`
        when the emitter declares no channel — the `trace_chars`
        convention, one field further.
    """

    def __init__(self, inner, predicates=None, commitment_predicates=None):
        self.inner = inner
        self.by_turn: dict = {}
        #: THE PROTOCOL: None = this emitter has no inward channel (the
        #: /api/generate path); a str = it has one and "" is a measurement.
        self.last_inward: str | None = None
        #: THE DECLARED SET THIS RUN'S BATCH IS BUILT WITH.  The span count is
        #: a MEASUREMENT, and measuring it with a DIFFERENT grammar than the
        #: run itself uses is the "suspect the metric" error: the campaign's
        #: seat-on cells declare the self's grammar (`expect` included), and a
        #: counter keyed on the pre-self set reads 0 for a generator emitting
        #: only commitments [MEASURED, the first live 3B pilot: 6 open
        #: commitments and spans=0 on turn 2].  None keeps the default set,
        #: byte-identical for every pre-self caller.
        self.predicates = predicates
        self.commitment_predicates = commitment_predicates

    # -- the universe, FORWARDED (the A4 fix) ----------------------------
    @property
    def last_universe(self):
        """The inner emitter's own declared universe, verbatim — or None
        when it declares none.  `stage2_harness._universe_of` reads this
        attribute FIRST (the `last_inward` convention: an attribute on the
        callable the harness was given), so forwarding it is the whole fix;
        nothing is derived here and nothing defaults."""
        return getattr(self.inner, "last_universe", None)

    @property
    def world(self):
        """The inner emitter's own `TaskWorld`, verbatim (or None).  This
        is `_universe_of`'s SECOND source and the one `LLM_DMN` uses: its
        `step(turn)` is pure in `(seed, turn)`, so re-stepping the emitter's
        OWN world returns exactly the universe that turn's prompt named."""
        return getattr(self.inner, "world", None)

    def __call__(self, turn: int, plant: dict):
        stream = self.inner(turn, plant)
        if not isinstance(stream, str):
            raise TypeError(
                f"the generator emitted {type(stream).__name__} at turn "
                f"{turn}, not the raw stream: this runner uses the stream "
                f"path only (route-all accepts a str; routing-on REQUIRES "
                f"one — the EXTRACTOR decides what is a claim)")
        ex = extract_spans(stream, self.predicates)
        committed = frozenset(self.commitment_predicates or ())
        n_commit = sum(1 for s in ex.claims if s.predicate in committed)
        inward = getattr(self.inner, "last_inward", None)
        #: FORWARDED VERBATIM (str) — the harness's `_inward_of` decides what
        #: a str means.  A missing attribute, or any non-str, is the DECLARED
        #: absence (None), which is the /api/generate path's own statement.
        self.last_inward = inward if isinstance(inward, str) else None
        resp = getattr(self.inner, "last_response", None)
        self.by_turn[int(turn)] = {
            "chars": len(stream), "spans": len(ex.claims),
            # THE SPLIT, reported so a reader sees WHAT the supply is made of:
            # with the self seat on, a generator can emit ONLY commitments.
            "claims": len(ex.claims) - n_commit, "commitments": n_commit,
            "preds": [s.predicate for s in ex.claims],
            "sha16": hashlib.sha256(stream.encode()).hexdigest()[:16],
            "stream": stream,
            "trace_chars": (len(inward) if isinstance(inward, str) else None),
            # THE TRACE ITSELF, not only its length (A6): the
            # self-referential-density check is an offline re-run on the
            # recorded text, and a density cannot be recovered from a char
            # count.  None — never "" — when the emitter declares no
            # channel, the `trace_chars` convention one field further.
            "trace_text": (inward if isinstance(inward, str) else None),
            "content_chars": len(stream),
            "done_reason": (resp.get("done_reason")
                            if isinstance(resp, dict) else None),
            "eval_count": (resp.get("eval_count")
                           if isinstance(resp, dict) else None),
        }
        return stream


def ensure_criterion(crit_dir: str) -> dict:
    """The ONE-TIME designer step for the routing-on arms (R5): publish v1 of
    the criterion into the RUN'S OWN store — never the designer's real
    ~/.cen-routingcrit (the batteries' isolation convention).  Published ONCE
    per outdir: a second publish would bump the version mid-matrix, and R2's
    timescale says the version in force is what each window reloads."""
    os.makedirs(crit_dir, exist_ok=True)
    store = RoutingCriterionStore(routingcrit_dir=crit_dir)
    path = store.path
    published = False
    if not os.path.exists(path):
        crit = publish_criterion(store, WriterToken.issue("designer"),
                                 vocation="software-engineering",
                                 created_by="designer")
        published = True
    else:
        crit = store.load()
    return {"dir": os.path.abspath(crit_dir), "version": int(crit.version),
            "rule": crit.rule, "f_min": crit.f_min, "f_max": crit.f_max,
            "theta_arm": crit.theta_arm, "published_this_call": published}


def unique_record_path(outdir: str, cell_id: str) -> str:
    """The cell's durable record path, made UNIQUE per attempt.

    A record is an append-only ANCHORED chain with one decision id per turn,
    so re-running a cell into an existing record file is REFUSED by the C8/C9
    machinery (duplicate `commit:1`) — measured, this is what a second run of
    the same cell did.  Rather than delete or overwrite a prior measurement
    (destructive, and both are evidence), the next free suffix is used and the
    chosen path is recorded in the run's own summary.  This is what makes
    `--pilot` and `--full` RE-RUNNABLE after a crash, which the
    caches-are-the-record discipline requires."""
    d = os.path.join(outdir, "records")
    os.makedirs(d, exist_ok=True)
    base = os.path.join(d, f"{cell_id}.jsonl")
    if not os.path.exists(base):
        return base
    for n in range(2, 1000):
        cand = os.path.join(d, f"{cell_id}-a{n}.jsonl")
        if not os.path.exists(cand):
            return cand
    raise RuntimeError(f"1000 attempts for {cell_id} — give a fresh --outdir")


def build_cfg(cell: dict, dmn, *, outdir: str, engine: str,
              crit_dir: str) -> Stage2Config:
    """ONE place where the arm's difference lives: `couple_backlog` (SPEC vs
    OFF) plus the routing setting.  Nothing else differs between arms."""
    routing_on = cell["routing"] == "routing-on"
    rec_path = unique_record_path(outdir, cell["cell_id"])
    return Stage2Config(
        dmn=dmn,
        couple_backlog=(cell["arm"] == "SPEC"),
        routing_selector=(PrefixRoutingSelector() if routing_on else None),
        routing_criterion_dir=(crit_dir if routing_on else ""),
        engine=engine,
        record_path=rec_path,
    )


class JsonlWriter:
    """Append-and-flush per turn: the caches-are-the-record discipline.  A
    crash mid-run loses no measured row."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.fh = open(path, "w", encoding="utf-8")

    def write(self, obj: dict) -> None:
        self.fh.write(json.dumps(obj, sort_keys=True) + "\n")
        self.fh.flush()
        os.fsync(self.fh.fileno())

    def close(self) -> None:
        try:
            self.fh.close()
        except Exception:
            pass


def _atomic_json(path: str, obj) -> None:
    d = os.path.dirname(os.path.abspath(path))
    os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def make_generator(args, seed: int, *, api: str | None = None,
                   model: str | None = None,
                   num_predict: int | None = None,
                   num_ctx: int | None = None,
                   world: TaskWorld | None = None,
                   predicates=None, commitment_predicates=None,
                   self_dominant: bool | None = None,
                   brief: bool | None = None):
    """THE ONE PLACE A DMN IS CONSTRUCTED (the chat-path wiring, item (1)).

    `api="chat"` routes through `dmn_llm.make_reasoning_dmn`, which names the
    three settings that must travel together (api + model + chat_endpoint)
    and carries NO `think` key: the reasoning model rejects every truthy form
    with HTTP 400, and `think: false` would state a capability it does not
    expose — the trace arrives from the template regardless
    (`handoff-selfreg-remote-endpoint-plan`; MEASURED).  Left as it was, the
    runner called `make_dmn(..., think=False)` = the GENERATE path, i.e. the
    OLD gemma configuration — the campaign would have silently measured the
    wrong arm.

    `api="generate"` (the DEFAULT, and therefore the pre-change bytes of
    every existing mode) is unchanged: `make_dmn(..., think=False)`.  The
    numeric options are passed only when the caller NAMES them, so an
    un-named `num_ctx`/`num_predict` keeps dmn_llm's own defaults.

    `seat_on` is NOT a parameter: the predicate set is.  A caller running the
    self seat must hand the SAME declared set the harness's `build_batch`
    gets (`selfmodel.SELF_PREDICATES` / `COMMITMENT_PREDICATES`), or the
    prompt's grammar and the extractor drift apart (dmn_llm's G1 mirror) —
    `campaign_generator` below is that caller.

    `brief` (default None = unset = dmn_llm's own False) is the CAMPAIGN's
    brevity instruction (`dmn_llm.BRIEF_INSTRUCTION`, appended to the user
    prompt by `dmn_llm.build_prompt`).  It travels through BOTH transports
    for the same reason `self_dominant` does: the prompt framing is part of
    the FIXED instrument, so the cells must differ in the seat and the drive,
    not in the framing.  Unset (every non-campaign caller) = the
    byte-identical baseline prompt.
    """
    world = world if world is not None else TaskWorld(seed=WORLD_SEED)
    api = api or args.api
    if api == dmn_llm.CHAT:
        kwargs = {"endpoint": args.endpoint,
                  "chat_endpoint": args.chat_endpoint,
                  "model": model or args.chat_model,
                  "temperature": args.temperature, "seed": int(seed),
                  "world": world}
        if num_predict is not None:
            kwargs["num_predict"] = int(num_predict)
        if num_ctx is not None:
            kwargs["num_ctx"] = int(num_ctx)
        if predicates is not None:
            kwargs["predicates"] = predicates
            kwargs["commitment_predicates"] = commitment_predicates
        if self_dominant is not None:
            kwargs["self_dominant"] = bool(self_dominant)
        if brief is not None:
            kwargs["brief"] = bool(brief)
        return dmn_llm.make_reasoning_dmn(**kwargs)
    kwargs = {"endpoint": args.endpoint, "model": model or args.model,
              "seed": int(seed), "temperature": args.temperature,
              "think": False, "world": world}
    if num_predict is not None:
        kwargs["num_predict"] = int(num_predict)
    if num_ctx is not None:
        kwargs["num_ctx"] = int(num_ctx)
    if predicates is not None:
        kwargs["predicates"] = predicates
        kwargs["commitment_predicates"] = commitment_predicates
    if self_dominant is not None:
        # the campaign's C6 (the gemma precondition-negative) runs the
        # SELF-DOMINANT layout too: the probe that measured gemma's negative
        # sign used that layout, and keeping it means C6 differs from C3 in
        # the MODEL and the TRANSPORT, not in the prompt framing.
        kwargs["self_dominant"] = bool(self_dominant)
    if brief is not None:
        # …and the brevity instruction travels with the framing, through BOTH
        # transports, for the same reason.  MEASURED on the CHAT/reasoning
        # arm only (the runaway-reasoning defect and its fix:
        # `dmn_llm.build_prompt`); its effect on the GENERATE/gemma arm is
        # UNMEASURED (PROJECTION) — it is carried there so the cells keep one
        # prompt framing, and C6's own role is the model/transport contrast.
        kwargs["brief"] = bool(brief)
    return make_dmn(**kwargs)


def run_one(cell: dict, args, outdir: str, *, turns: int,
            crit_dir: str, crit_meta: dict, progress_every: int,
            print_table: bool = False) -> dict:
    """ONE cell: one generator, one config, one harness run.  Returns the run
    summary; writes the per-turn rows to JSONL as they are produced."""
    rows_path = os.path.join(outdir, "rows", f"{cell['cell_id']}.jsonl")
    summary_path = os.path.join(outdir, "runs", f"{cell['cell_id']}.json")
    writer = JsonlWriter(rows_path)

    inner = make_generator(args, cell["seed_base"])
    rec = RecordingDMN(inner)
    cfg = build_cfg(cell, rec, outdir=outdir, engine=args.engine,
                    crit_dir=crit_dir)
    p = Params(tau_S=cell["tau_S"])
    sch = rescue_schedule()

    state = {"t_prev": time.time(), "secs": [], "rows": [], "t_eq_turn": True,
             "first_batch_turn": None}
    t_start = time.time()

    def hook(turn: int, st) -> bool:
        now = time.time()
        secs = now - state["t_prev"]
        state["t_prev"] = now
        row = st.log[-1]
        gen = rec.by_turn.get(int(turn), {})
        plant = st.last_plant
        if float(row.t) != float(turn):
            state["t_eq_turn"] = False
        if state["first_batch_turn"] is None:
            state["first_batch_turn"] = turn
        out = {
            "turn": int(turn), "t": float(row.t), "c": float(row.c),
            "G": float(row.G), "D": float(row.D), "E": float(plant.get("E", 0.0)),
            "a": float(plant.get("a", 0.0)), "S": float(plant.get("S", 0.0)),
            "g": float(plant.get("g", 0.0)), "B_plant": float(plant.get("B", 0.0)),
            "backlog": int(row.backlog), "backlog_ema": float(row.backlog_ema),
            "backlog_rate": float(row.backlog_rate),
            "A_eff": float(row.A_eff),
            "routed": int(row.routed),
            "verdicts_V": int(row.verdicts_V), "verdicts_R": int(row.verdicts_R),
            "verdicts_U": int(row.verdicts_U),
            "derivations": int(row.derivations),
            "rejected": int(row.rejected),
            "spans": int(gen.get("spans", -1)),
            "chars": int(gen.get("chars", 0)),
            "preds": gen.get("preds", []),
            "stream_sha16": gen.get("sha16", ""),
            "stream": gen.get("stream", ""),
            "secs": secs,
        }
        writer.write(out)
        state["rows"].append(out)
        state["secs"].append(secs)
        if print_table or (turn % progress_every == 0) or turn == 1:
            log(f"{cell['cell_id']} turn={turn:5d} t={row.t:7.1f} "
                f"c={row.c:.4f} G={row.G:.4f} D={row.D:.4f} "
                f"backlog={row.backlog:4d} ema={row.backlog_ema:8.4f} "
                f"B_plant={out['B_plant']:6.4f} "
                f"B_telemetry={row.backlog_rate:6.4f} "
                f"A_eff={row.A_eff:6.4f} "
                f"routed={row.routed:3d} spans={out['spans']:3d} "
                f"V/R/U={row.verdicts_V}/{row.verdicts_R}/{row.verdicts_U} "
                f"({secs:.2f}s)")
        return True

    log(f"{cell['cell_id']} START routing={cell['routing']} "
        f"arm={cell['arm']} tau_S={cell['tau_S']:g} turns={turns} "
        f"seed_base={cell['seed_base']} (per-turn seed = base+turn)")
    err = None
    st = None
    try:
        st = run_stage2(sch, turns, cfg, p=p, checkpoint_fn=hook)
    except Exception as exc:                    # noqa: BLE001 — reported, loud
        err = f"{type(exc).__name__}: {exc}"
        _warn(f"{cell['cell_id']} STOPPED at {len(state['rows'])} rows: {err}")
    wall = time.time() - t_start

    result = (score_recovery(state["rows"]) if state["rows"]
              else {"G_end": None, "G_min_post": None, "recovered": False,
                    "n_window": 0, "band": BAND1, "window": [WINDOW_T0,
                                                             TURNS_FULL]})
    supply = _supply_stats(state["rows"]) if state["rows"] else {}
    post = state["secs"][min(10, len(state["secs"])):]
    if not post:                       # a very short run: never report nan
        post = state["secs"]
    per_turn = statistics.median(post) if post else float("nan")
    summary = {
        "cell_id": cell["cell_id"],
        "prereg": PREREG_NODE, "result_node": RESULT_NODE,
        "runner": os.path.relpath(os.path.abspath(__file__), _ROOT),
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "config": {
            **cell, "turns": int(turns), "world_seed": WORLD_SEED,
            "temperature": args.temperature, "model": args.model,
            "endpoint": args.endpoint, "engine": args.engine,
            "couple_backlog": cell["arm"] == "SPEC",
            "routing_selector": ("PrefixRoutingSelector" if
                                 cell["routing"] == "routing-on" else None),
            "routing_criterion": (crit_meta if cell["routing"] == "routing-on"
                                  else None),
            "routing_consolidation_turns": TAU_S_TURNS,
            "retrieval_priced": False, "record_path": cfg.record_path,
        },
        "criterion": {"name": "G2c", "band": BAND1,
                      "window": [WINDOW_T0, float(TURNS_FULL)],
                      "source": "Stage2LogRow.G",
                      "form": "recovered = (G_end > band) AND "
                              "(min G over the window > band)"},
        "result": result,
        "supply": supply,
        "trajectory": {
            "G_max": (max(r["G"] for r in state["rows"]) if state["rows"]
                      else None),
            "G_min": (min(r["G"] for r in state["rows"]) if state["rows"]
                      else None),
            "c_max": (max(r["c"] for r in state["rows"]) if state["rows"]
                      else None),
            "D_max": (max(r["D"] for r in state["rows"]) if state["rows"]
                      else None),
            "backlog_max": (max(r["backlog"] for r in state["rows"])
                            if state["rows"] else None),
            "backlog_ema_max": (max(r["backlog_ema"] for r in state["rows"])
                                if state["rows"] else None),
            "backlog_ema_final": (state["rows"][-1]["backlog_ema"]
                                  if state["rows"] else None),
            "B_p2_max": (max(r["B_plant"] for r in state["rows"])
                         if state["rows"] else None),
            "B_p2_final": (state["rows"][-1]["B_plant"]
                           if state["rows"] else None),
            "B_telemetry_u_over_n_max": (
                max(r["backlog_rate"] for r in state["rows"])
                if state["rows"] else None),
            "A_eff_max": (max(r["A_eff"] for r in state["rows"])
                          if state["rows"] else None),
            "B_plant_max": (max(r["B_plant"] for r in state["rows"])
                            if state["rows"] else None),
            "a_max": (max(r["a"] for r in state["rows"]) if state["rows"]
                      else None),
            "t_eq_turn": state["t_eq_turn"],
        },
        "timing": {"wall_s": wall, "turns_done": len(state["rows"]),
                   "per_turn_median_s": per_turn,
                   "per_run_s_measured_part": wall,
                   "projected_run_s": (per_turn * turns
                                       if per_turn == per_turn else None)},
        "status": ("OK" if err is None else "ERROR"),
        "error": err,
        "rows_file": os.path.relpath(rows_path, _ROOT),
        "confounds": [
            "G-analogue UNSOLVED -> routing runs the conservative arm "
            "(g_unsolved_conservative_arm), understating routed demand",
            f"engine={args.engine} (stub: rule-free store, most claims land "
            "UNCHECKABLE = DEBT; the D-drive is DEBT-DOMINATED)",
            "generator is NONSTATIONARY (supply varies by turn): the test is "
            "the RECOVERY OUTCOME, not B's trajectory shape",
            "one turn = one t.u. (asserted: t == turn)",
            "lever/proposal channel UNUSED by a stream generator "
            "(dmn_llm GAPS G1)",
            f"routing consolidation cadence is the harness constant "
            f"TAU_S_TURNS={TAU_S_TURNS} turns, NOT Params.tau_S",
            "route-all logs routed=0 by design (no selector); the extractor's "
            "own span count is the supply column",
            "retrieval NOT priced -> the generator's SELF block is empty",
        ],
    }
    writer.close()
    _atomic_json(summary_path, summary)
    log(f"{cell['cell_id']} DONE status={summary['status']} "
        f"G_end={_num(result['G_end'])} "
        f"G_min_post={_num(result['G_min_post'])} "
        f"recovered={result['recovered']} wall={wall:.1f}s "
        f"({_num(per_turn, '.2f')}s/turn median, "
        f"{len(state['rows'])} rows)")
    return summary


# ==========================================================================
# THE AGENTEXP2 CAMPAIGN (handoff-selfreg-agentexp2-plan) — the runnable
# experiment.  Six conditions, the preserved criterion + its coverage mirror,
# the four-outcome matrix, the voiding conditions, the determinism protocol
# and the pilot gate.  Everything in this section is either PURE (so the
# offline selftest exercises the SAME function the runs are scored with) or a
# runner that reuses the machinery above.  The two pre-registrations do NOT
# share mutable state: the constants above stay the old matrix's.
# ==========================================================================

CAMPAIGN_GAIN = 1.0        # the a_hold mapping's scale: PRE-REGISTERED, UNTUNED

#: THE SIX DISCRIMINATING CONDITIONS.  `seat` = the self seat (self_T + the
#: priced retrieval seat + the seed + agent_g); `drive` = the schedule
#: WRAPPER (`SelfReferentialDrive`); `couple` = the P2 coupling arm
#: (couple_backlog) — the OLD experiment's axis, carried ONLY inside C5.
#: Each carries the plan's own justification (`role`) and its pre-registered
#: directional expectation (`expect`), so a reader cannot see one without the
#: other.
CAMPAIGN_CONDITIONS = (
    {"cell": "C1", "label": "SEAT-OFF/BASE-SELF",
     "seat": False, "drive": False, "couple": False, "arm": "OFF",
     "n": CAMPAIGN_N, "turns": CAMPAIGN_TURNS, "budget": None,
     "api": dmn_llm.CHAT, "model_role": "reasoning", "length_capped": False,
     "priority": "control", "expect": {"outcome": "HEALTHY", "rule": "all"},
     "role": ("THE HEALTHY CONTROL: the plant recovers and there is no "
              "depletion instrument (self_T=None, the plain rescue schedule, "
              "the default budget).  It establishes the clean OFF in N/N and "
              "the scenario's per-model baseline — the reference every other "
              "cell is read against.")},
    {"cell": "C2", "label": "SEAT-ON/DRIVE-OFF",
     "seat": True, "drive": False, "couple": False, "arm": "OFF",
     "n": CAMPAIGN_N, "turns": CAMPAIGN_TURNS, "budget": CAMPAIGN_BUDGET,
     "api": dmn_llm.CHAT, "model_role": "reasoning", "length_capped": False,
     "priority": "experiment",
     "expect": {"outcome": "DISSOCIATION", "rule": "at_least", "k": 2},
     "role": ("THE DEPLETION BYSTANDER: coverage depletes (B=6) and the "
              "four-outcome dissociation is visible while the plant does NOT "
              "collapse.  THE ATTRIBUTION CONTROL: it is what makes any C3 "
              "collapse attributable to the DRIVE and not to the seat's side "
              "effects (H6/H7: a plant trajectory bit-identical with the "
              "tracker on/off; here the SAME generator and seeds as C3).")},
    {"cell": "C3", "label": "SEAT-ON/DRIVE-ON",
     "seat": True, "drive": True, "couple": False, "arm": "OFF",
     "n": CAMPAIGN_N, "turns": CAMPAIGN_TURNS, "budget": CAMPAIGN_BUDGET,
     "api": dmn_llm.CHAT, "model_role": "reasoning", "length_capped": False,
     "priority": "experiment",
     "expect": {"outcome": "CO_COLLAPSE", "rule": "at_least", "k": 2},
     "role": ("THE EXPERIMENT: depletion -> inward rise -> drive -> a_hold -> "
              "the plant's collapse, with the pre-registered directional "
              "prediction (plant-, self-) — NON-recovered under the SAME G2c "
              "form.  The ONLY difference from C2 is the schedule wrapper "
              "(mirroring the SPEC/OFF discipline: one switch, seeds shared).")},
    {"cell": "C4", "label": "DRIVE-ON/NO-SEAT",
     "seat": False, "drive": True, "couple": False, "arm": "OFF",
     "n": 1, "turns": CAMPAIGN_TURNS, "budget": None,
     "api": dmn_llm.CHAT, "model_role": "reasoning", "length_capped": False,
     "priority": "wiring", "expect": {"outcome": "HEALTHY", "rule": "all"},
     "role": ("THE DRIVE-ONLY CONTROL: a drive with no measured source, so "
              "the window's inward share is never set, the drive stays 0.0 "
              "and C4 == C1 MECHANICALLY.  Its role is NOT dynamic — it "
              "isolates the WRAPPER: a schedule-seating bug would move C4, "
              "and plant bit-identity with C1 is the assertion.  N=1.")},
    {"cell": "C5", "label": "P2-COUPLING PAIR (SPEC/OFF)",
     "seat": True, "drive": True, "couple": (True, False), "arm": "SPEC/OFF",
     "n": 1, "turns": CAMPAIGN_TURNS, "budget": CAMPAIGN_BUDGET,
     "api": dmn_llm.CHAT, "model_role": "reasoning", "length_capped": False,
     "priority": "reduced",
     "expect": {"outcome": None, "rule": "plant_side", "k": 1},
     "role": ("THE OLD EXPERIMENT'S ARM PAIR, retained because the "
              "side-by-side claim with exp22 lives there.  REDUCED PRIORITY, "
              "and reported as what it is: in these cells the generator is a "
              "SPECTATOR of that coupling (p2r2 blocker), so C5 measures the "
              "PLANT's own edge feedback + the plant cell of the four-outcome "
              "matrix, not an agent path.  Run LAST.")},
    {"cell": "C6", "label": "PRECONDITION-NEGATIVE (gemma, /api/generate)",
     "seat": True, "drive": True, "couple": False, "arm": "OFF",
     "n": 1, "turns": CONTROL_CAP_TURNS, "budget": CAMPAIGN_BUDGET,
     "api": dmn_llm.GENERATE, "model_role": "control", "length_capped": True,
     "priority": "control", "expect": {"outcome": None, "rule": "sign", "k": 1},
     "role": ("THE PRECONDITION'S NEGATIVE CONTROL: the model that does NOT "
              "exhibit the depletion->inward sign (MEASURED: inward_share "
              "0.635 -> 0.610, the WRONG way, handoff-selfreg-sign-probe-"
              "result).  NOT plumbing: the campaign's claim is 'the mechanism "
              "fires only for models with the measured sign', and that needs "
              "the failing model RUN.  LENGTH-CAPPED at the first boundary — "
              "the sign is per-window, not the full arc — so its runs are "
              "EXCLUDED from recovery scoring.")},
)

#: THE PRE-REGISTERED N PER CELL (B2) — the acceptance's own DENOMINATOR,
#: read off the pre-registered condition table above.  The N-gate in
#: `evaluate_campaign` ENFORCES this number; it does not change it (N=3 for
#: C1-C3, 1 for C4/C5/C6).  A cell that has not reached its N is a WEAKER
#: EXPERIMENT, not a smaller one: the >= 2/3 conjuncts are satisfiable at
#: n=1, and `mode_campaign` rewrites campaign.json after EVERY cell, so
#: without this gate a crash after seed 1 leaves a false ACCEPT on disk.
CAMPAIGN_PREREG_N = {c["cell"]: int(c["n"]) for c in CAMPAIGN_CONDITIONS}
#: the cells the ACCEPTANCE conjunction reads (C4 is the V5 wiring check and
#: C6 is length-capped/not recovery-scored; C5 has its own predicate)
CAMPAIGN_ACCEPTANCE_CELLS = ("C1", "C2", "C3")

OUTCOME_MEANINGS = {
    "HEALTHY": ("plant+, self+ — the plant recovers and the self stays "
                "reconstructed: the healthy cell (C1's expectation)."),
    "DISSOCIATION": ("plant+, self- — the plant recovers while the self stays "
                     "depleted: the model's rescue asymmetry transferred (the "
                     "rescue does not rebuild the self).  C2's expectation."),
    "CO_COLLAPSE": ("plant-, self- — the co-collapse, the paper-2 claim: the "
                    "agent's self depletion dragged the plant down (in C3, via "
                    "the drive).  C3's directional prediction."),
    "UNMODELLED": ("plant-, self+ — a plant collapse WITHOUT self depletion: "
                   "an unmodelled quadrant in these arms.  If it appears in "
                   "C3 it is evidence the collapse is NOT the seat's doing, "
                   "and it triggers the C2 comparison.  Reported, never "
                   "absorbed."),
}
#: (plant_recovered, self_depleted) -> the outcome NAME.  THE SIGN CONVENTION
#: IS THE PLAN'S OWN: the second coordinate is the SELF's state, where "-" is
#: the DEPLETED self — so (True, False) is plant+/self+ (HEALTHY) and
#: (False, True) is plant-/self- (the CO-COLLAPSE).  Reading the self axis the
#: other way round would rename every cell of the matrix.
_OUTCOME_BY_SYMBOL = {(True, False): "HEALTHY", (True, True): "DISSOCIATION",
                      (False, True): "CO_COLLAPSE", (False, False): "UNMODELLED"}
_OUTCOME_SYMBOL = {"HEALTHY": "plant+/self+", "DISSOCIATION": "plant+/self-",
                   "CO_COLLAPSE": "plant-/self-", "UNMODELLED": "plant-/self+"}


def campaign_condition(cell: str) -> dict:
    """One condition by name (a COPY: a run spec must never mutate the
    pre-registered table)."""
    for c in CAMPAIGN_CONDITIONS:
        if c["cell"] == cell:
            return copy.deepcopy(c)
    raise KeyError(f"no campaign condition named {cell!r}: the six are "
                   f"{[c['cell'] for c in CAMPAIGN_CONDITIONS]}")


def campaign_conditions(names=None) -> list:
    """The conditions, in the PLAN'S PHASE ORDER (gates first, controls
    last) — the run order, not the C-numbering."""
    order = list(CAMPAIGN_PHASE_ORDER)
    want = [n.upper() for n in names] if names else order
    return [campaign_condition(n) for n in want if n in order]


def campaign_plan(names=None, *, n: int | None = None,
                  turns: int | None = None, args=None) -> list:
    """THE RUN SPECS: one per (condition, coupling variant, seed repeat), in
    the plan's phase order.  C5 expands to its SPEC/OFF pair (the only place
    `couple_backlog` varies at all); the other cells carry it OFF.

    A spec is what `run_one_campaign` consumes: the cell's seat/drive/couple
    switches, its own `api` and model role, its horizon (C6 capped), its
    retrieval budget (None = cen.CostBudget's own default) and its seed.

    `n` AND `turns` ARE OVERRIDES (F1), NOT DEFAULTS.  With both None the plan
    is THE PRE-REGISTRATION'S OWN — each condition's declared `n` and `turns`
    from CAMPAIGN_CONDITIONS (C1/C2/C3 n=3, C4 n=1, C5 1 per arm = 2 specs, C6
    n=1 at its CONTROL_CAP_TURNS=300), i.e. THE PLAN'S 13 SPECS.  MEASURED
    before this fix: the campaign's DEFAULT invocation planned 21 specs, not
    13, because argparse's --n default (3) was passed in as an override for
    EVERY condition (C4 3, C5 6, C6 3) and the same went for --turns, so C6
    ran the 1400-turn horizon instead of its declared 300-turn cap (18.7-49.0
    GPU-h where the cap's 4.0-10.5 h was declared, at the pilot's measured
    16-42 s/turn).  An explicit --n / --turns still overrides the plan — it is
    recorded as an override — but the DESIGN is what the runner plans when the
    user has not asked for anything else.

    C6'S CAP IS NOT OVERRIDABLE UPWARD: a control declared length-capped at
    the first boundary stays capped under --turns (a shorter --turns still
    shortens it, and it remains length-capped either way).  Buying the full
    horizon for the precondition negative is the cost this cap exists to
    avoid, and the cap is part of its pre-registration.

    WITH `args` THE SPEC IS BOUND TO ITS CONFIGURATION (S5): the cell_id gains
    `-h<digest>` over api/model/endpoint/num_predict/num_ctx/engine/budget/
    turns/temperature, and the identity is carried in the spec.  The resume
    key is therefore the whole measurement, not the cell's name — a campaign
    re-run at num_predict 9000 after a 6000-budget pilot failure produces
    DIFFERENT run files and cannot read the old rows as "already measured"."""
    out = []
    for cond in campaign_conditions(names):
        couples = (cond["couple"] if isinstance(cond["couple"], tuple)
                   else (cond["couple"],))
        reps = int(n) if n is not None else int(cond["n"])
        t = int(cond["turns"]) if turns is None else int(turns)
        if cond["length_capped"]:
            t = min(t, int(cond["turns"]))
        for couple in couples:
            for rep in range(reps):
                base = seed_base_for(rep)
                # THE HORIZON IS PART OF THE RUN'S IDENTITY, not a detail: a
                # 300-turn pilot run and a 1400-turn campaign run of the same
                # cell are DIFFERENT measurements, and a resume keyed on the
                # cell alone would silently reuse the pilot's rows as the
                # campaign's (MEASURED, the shakedown's first 1400-turn pass).
                cell_id = (f"agenteXP2-{cond['cell']}-c"
                           f"{'ON' if couple else 'OFF'}-t{t}-s{base}")
                spec = {
                    **{k: cond[k] for k in
                       ("cell", "label", "seat", "drive", "api",
                        "model_role", "length_capped", "priority", "role",
                        "expect")},
                    "couple_backlog": bool(couple),
                    "budget": cond["budget"], "repeat": int(rep),
                    "seed_base": int(base), "turns": t,
                    "variant": ("SPEC" if couple else "OFF"),
                    "cell_id": cell_id, "attempt": 0,
                    # A HORIZON SHORTER THAN THE PRE-REGISTERED ONE CANNOT
                    # REACH THE CRITERION WINDOW, so the run is LENGTH-CAPPED
                    # (the plan's own rule for C6) and EXCLUDED from recovery
                    # scoring.  Scoring a truncated run as a non-recovery
                    # would read a long horizon's window as a plant failure.
                    "length_capped": bool(cond["length_capped"]
                                          or t < TURNS_FULL),
                }
                # S5: the run's identity is its CONFIGURATION, not its cell
                # name (no args = the untagged planning view the selftest and
                # the structural checks read).
                out.append(bind_campaign_identity(spec, args)
                           if args is not None else spec)
    return out


def campaign_invocation_plan(args) -> list:
    """THE SPECS THIS INVOCATION PLANS — the ONE seam where `--n` / `--turns`
    bind the campaign (F1).

    A flag binds ONLY IF THE USER GAVE IT: `--n` / `--turns` are overrides,
    and with neither given the plan is the pre-registration's own per-condition
    N and horizons (`campaign_plan()` with no override).  Every campaign entry
    point (`mode_campaign`, `_write_campaign`, the dry run) reads the plan
    through here, so the count on disk and the count that runs cannot come
    from two different rules — the previous F1 defect was exactly that the
    selftest read the no-override plan while the RUNNER planned the overridden
    one."""
    return campaign_plan(
        args.cells,
        n=(args.n if getattr(args, "n_explicit", False) else None),
        turns=(args.turns if getattr(args, "turns_explicit", False) else None),
        args=args)


def campaign_cost_projection(per_turn_s: float, specs: list) -> dict:
    """THE CAMPAIGN'S COST, SUMMED OVER THE PLANNED SPECS (F1).

    `project_cost` multiplies ONE horizon by the run count, which
    OVER-PROJECTS a plan whose control is length-capped: C6's declared
    300-turn cap priced as a 1400-turn horizon overstated the design plan by
    ~1.1 runs' worth of GPU time, and the 21-spec invocation overstated it
    further.  This sums each spec's OWN horizon and reports the capped runs
    separately, so a reader sees which part of the total they are.

    A PROJECTION, always: the per-turn time is MEASURED (the pilot's median)
    or the plan's estimate, and the figure is a multiplication of the two."""
    turns = [int(s["turns"]) for s in specs]
    capped = [int(s["turns"]) for s in specs if s["length_capped"]]
    full = [int(s["turns"]) for s in specs if not s["length_capped"]]
    out = {"n_specs": len(specs), "total_turns": sum(turns),
           "n_length_capped": len(capped),
           "turns_length_capped": sum(capped),
           "n_full_length": len(full),
           "turns_full_length": sum(full),
           "turns_per_full_run": (max(full) if full else None),
           "per_turn_s": per_turn_s,
           "per_run_hours": None, "per_capped_run_hours": None,
           "total_hours": None}
    if per_turn_s is None or not (per_turn_s == per_turn_s) or per_turn_s <= 0:
        return out
    out["per_run_hours"] = per_turn_s * (max(full) if full else 0) / 3600.0
    out["per_capped_run_hours"] = (per_turn_s * max(capped) / 3600.0
                                   if capped else None)
    out["total_hours"] = per_turn_s * sum(turns) / 3600.0
    return out


# --------------------------------------------------------------------------
# THE CRITERIA (pure): the plant's (unchanged) and the agent-side mirror.
# --------------------------------------------------------------------------

def score_coverage(rows, band: float = COVERAGE_MIRROR_BAND,
                   window: int = TAU_S_TURNS) -> dict:
    """THE AGENT-SIDE MIRROR, in the SAME FORM as the plant criterion.

        depleted = (coverage_end < band) AND
                   (min coverage over the LAST `window` turns < band)

    `coverage` is `Stage2LogRow.coverage` — `Reconstruction.coverage`, READ
    and never recomputed (the CEN's own per-turn measurement of how much of
    the offered self the priced reconstruction reached).  The PLAN cell's
    window is implicitly the horizon; the AGENT cell's window is the LAST
    consolidation window (TAU_S_TURNS = 100 turns), which is the agent's own
    collapse timescale — NOT a free choice, and NOT Params.tau_S.

    THE 0.5 THRESHOLD IS A STATED CONVENTION (mirrored from BAND1), NOT a
    measured boundary: the model's is a calibrated band, the agent's is the
    same number by analogy.  Stated wherever it is quoted.

    An EMPTY row set is not depleted and carries None (an absent measurement
    is not a zero); a run shorter than `window` uses every row it has, and
    the count is reported so the reader can see it."""
    cov = [float(_field(r, "coverage")) for r in rows]
    if not cov:
        return {"coverage_end": None, "coverage_min_last_window": None,
                "coverage_min_all": None, "coverage_first": None,
                "depleted": False, "n_rows": 0, "n_last_window": 0,
                "band": band, "window_turns": int(window)}
    last = cov[-int(window):] if window else cov
    cov_end = cov[-1]
    cov_min_last = min(last)
    return {"coverage_end": cov_end, "coverage_min_last_window": cov_min_last,
            "coverage_min_all": min(cov), "coverage_first": cov[0],
            "depleted": bool(cov_end < band and cov_min_last < band),
            "n_rows": len(cov), "n_last_window": len(last),
            "band": band, "window_turns": int(window)}


def four_outcome(plant_recovered: bool, self_depleted: bool) -> str:
    """(plant_recovered, self_depleted) -> the ONE of four named outcomes.
    The pair is never collapsed into a single bit: the two criteria answer
    different questions, and the quadrant is the result.  The plan's symbols
    are self- = DEPLETED, self+ = reconstructed (see _OUTCOME_BY_SYMBOL)."""
    return _OUTCOME_BY_SYMBOL[(bool(plant_recovered), bool(self_depleted))]


def score_run(rows) -> dict:
    """A run's OWN result: the plant criterion (verbatim), the agent mirror,
    and the four-outcome quadrant they compose.  Pure over the logged rows."""
    plant = score_recovery(rows)
    agent = score_coverage(rows)
    if not rows:
        return {"plant": plant, "agent": agent, "outcome": None,
                "outcome_symbol": None, "outcome_meaning": None,
                "empty": True}
    oc = four_outcome(plant["recovered"], agent["depleted"])
    return {"plant": plant, "agent": agent, "outcome": oc,
            "outcome_symbol": _OUTCOME_SYMBOL[oc],
            "outcome_meaning": OUTCOME_MEANINGS[oc], "empty": False}


def partialize_result(result: dict, *, status: str, rows: int,
                      turns: int) -> dict:
    """S2 — A RUN THAT DID NOT COMPLETE ITS OWN HORIZON IS NOT A QUADRANT.

    The criterion's window is [WINDOW_T0, TURNS_FULL]; a log that stopped at
    turn 1200 (status ERROR, transport death, a killed process) still scores —
    `score_run` is pure over whatever rows exist — so the run's OWN JSON used
    to carry a finished-looking `outcome: CO_COLLAPSE` measured on a third of
    the arc it claims.  MEASURED (offline probe, this pass): a run that died
    at turn 600 of 1400 recorded outcome=CO_COLLAPSE, recovery_scored=True.

    The measured quadrant is KEPT (it is data, and hiding it would be the
    silent drop the plan forbids) but it is NAMED for what it is and REMOVED
    from the counted field: `outcome` is None, `partial` is True, and the
    quadrant it would have read is preserved under
    `quadrant_measured_but_NOT_counted`.  The void predicates (V3 fires on any
    non-OK status) are what exclude the run from the tallies; this makes the
    run's own artifact say the same thing."""
    if status == "OK" and int(rows) >= int(turns):
        return result
    out = dict(result)
    out["partial"] = True
    out["rows_measured"] = int(rows)
    out["rows_expected"] = int(turns)
    out["quadrant_measured_but_NOT_counted"] = out.get("outcome")
    out["outcome"] = None
    out["outcome_symbol"] = None
    out["outcome_meaning"] = None
    out["note"] = (f"PARTIAL RUN: status={status} after {rows} of {turns} "
                   f"rows — the criterion's window is "
                   f"[{WINDOW_T0:g}, {TURNS_FULL}] turns, so the quadrant "
                   f"above was measured on a TRUNCATED log and is NOT this "
                   f"run's quadrant (it is excluded from the cell's outcome "
                   f"tally; the void predicates report why)")
    return out


# --------------------------------------------------------------------------
# THE VOIDING CONDITIONS (pure predicates over the logged rows).
# --------------------------------------------------------------------------

def _field_opt(row, name: str):
    if isinstance(row, dict):
        return row.get(name)
    return getattr(row, name, None)


def void_predicates(rows, spec, *, status: str = "OK",
                    error: str | None = None) -> dict:
    """V1/V2/V3 as PREDICATES over the logged row fields, with their
    reason, their evidence and — crucially — their SCOPE.  A void is a
    measurement that cannot show the phenomenon, and it is never a PASS and
    never a silent drop.

      V1 NO-DEPLETION VOID (seat-on cells only): a run whose coverage never
         falls below the band (the boundary is CLOSED: min == band VOIDs, the
         plan's "never below 0.5" and the mirror's own `< band`) shows
         nothing about the seat — the plant
         collapsed for its own reasons, or nothing depleted, and the outcome
         is uninterpretable for the self claim.  The BUDGET is named first in
         the reason (the first suspect), the store's growth second.
      V2 CROWDING VOID: content EMPTY in a majority of turns.  The trace
         share is a SIZE RATIO, so `|trace|/(|trace|+|content|) -> 1.0`
         whenever content is 0 REGARDLESS of the self's state: a majority-
         empty run's drive is saturated by the REGISTER, not by depletion.
         25-50% empty is FLAGGED register-degraded (reported, not voided);
         > 50% is VOID.  (The rows carry the per-turn trace/content chars so
         the boundary is auditable.)
      V3 NO-TRACE VOID: a turn with NO trace and NO content raises
         DMNEndpointError in the transport (dmn_llm refuses to invent a
         stream), so a run that died this way — or died at all — is VOID as a
         MEASUREMENT (transport/register), never scored.
      V4/V5 are campaign-level and live in `evaluate_campaign`."""
    cov = [float(_field(r, "coverage")) for r in rows
           if _field_opt(r, "coverage") is not None]
    seat_on = bool(spec.get("seat"))
    cov_min = min(cov) if cov else None
    # THE BOUNDARY IS CLOSED (S4): the plan's sentence is "coverage never
    # falls BELOW 0.5", so a run whose minimum coverage is EXACTLY the band
    # has not depleted — and the mirror criterion needs `min < band` to read
    # depleted, so `>=` here makes V1 the exact complement of the mirror's own
    # min-clause.  With `>` a run sitting on the boundary read as neither
    # depleted nor void: a hole, not a subtlety.
    v1_void = bool(seat_on and cov and cov_min >= COVERAGE_MIRROR_BAND)
    v1 = {
        "applies": seat_on,
        "coverage_min": cov_min,
        "coverage_first": (cov[0] if cov else None),
        "coverage_end": (cov[-1] if cov else None),
        "budget": spec.get("budget"),
        "void": v1_void,
        "reason": (None if not v1_void else
                   f"V1 NO-DEPLETION: coverage never fell below "
                   f"{COVERAGE_MIRROR_BAND:g} (min {cov_min:.4f} >= "
                   f"{COVERAGE_MIRROR_BAND:g}, the closed boundary) on a "
                   f"seat-ON run — first suspect is the retrieval budget "
                   f"({spec.get('budget')!r} derivations/turn), second the "
                   f"store's growth rate; a 'plant recovers' outcome without "
                   f"depletion is uninterpretable for the self claim"),
    }
    content = [int(_field_opt(r, "content_chars")
                   if _field_opt(r, "content_chars") is not None
                   else (_field_opt(r, "chars") or 0)) for r in rows]
    traces = [_field_opt(r, "trace_chars") for r in rows]
    trace_known = [int(t) for t in traces if t is not None]
    empty_turns = sum(1 for c in content if c == 0)
    empty_rate = (empty_turns / len(content)) if content else None
    v2_void = bool(empty_rate is not None
                   and empty_rate > EMPTY_CONTENT_VOID_RATE)
    v2_flag = bool(empty_rate is not None and not v2_void
                   and empty_rate >= EMPTY_CONTENT_FLAG_RATE)
    v2 = {
        "applies": True,
        "empty_turns": empty_turns, "turns": len(content),
        "empty_content_rate": empty_rate,
        "flag_rate": EMPTY_CONTENT_FLAG_RATE,
        "void_rate": EMPTY_CONTENT_VOID_RATE,
        "register_degraded": v2_flag,
        "trace_chars": ({"min": min(trace_known),
                         "mean": (sum(trace_known) / len(trace_known)),
                         "max": max(trace_known), "turns_measured":
                         len(trace_known)}
                        if trace_known else None),
        "content_chars": ({"min": min(content),
                           "mean": (sum(content) / len(content)),
                           "max": max(content)} if content else None),
        "void": v2_void,
        "reason": (None if not v2_void else
                   f"V2 CROWDING: content EMPTY in {empty_turns}/"
                   f"{len(content)} turns ({empty_rate:.1%}) — the inward "
                   f"share is a SIZE RATIO and reads ~1.0 by REGISTER, not "
                   f"by depletion (fix num_predict/num_ctx; the register, "
                   f"not the self, is what was measured)"),
    }
    v3_void = bool(status != "OK" or not rows)
    v3 = {
        "applies": True,
        "status": status, "error": error, "rows": len(rows),
        "transport": bool(error and "DMNEndpointError" in str(error)),
        "void": v3_void,
        "reason": (None if not v3_void else
                   (f"V3 NO-TRACE / TRANSPORT: the run ended status={status} "
                    f"after {len(rows)} rows with {error!r} — a run the "
                    f"transport refused (both streams empty raises in "
                    f"dmn_llm) is VOID, never scored" if error else
                    f"V3 NO-TRACE: the run produced no rows at all")),
    }
    reasons = [v["reason"] for v in (v1, v2, v3) if v["void"]]
    return {"V1": v1, "V2": v2, "V3": v3,
            "void": bool(reasons), "void_reasons": reasons,
            "flags": (["register-degraded (V2: 25-50% empty content)"]
                      if v2_flag else []),
            "scope_note": ("V1 applies to the seat-on conditions only; V4 "
                           "(the C1 control) and V5 (C4 vs C1 wiring) are "
                           "campaign-level and live in evaluate_campaign")}


# --------------------------------------------------------------------------
# THE PLANT'S ARITHMETIC NO-DRIVE BASELINE (P3's reference), OFFLINE.
# --------------------------------------------------------------------------

def plant_no_drive_baseline(turns: int, p=None) -> dict:
    """THE PLANT'S OWN TRAJECTORY WITH NO SEAT — the reference P3 compares
    C3 against, computed with NO endpoint.

    WHY IT IS EXACT AND NOT AN APPROXIMATION (MEASURED, asserted by the
    offline selftest): with `couple_backlog=False` the plant reads ONLY the
    schedule's own channels (a_hold, A) and its own state — the generator's
    output reaches the CEN and the telemetry and has NO PATH INTO THE PLANT
    (stage2_harness's coupling docstring; the p2r2 blocker).  So the plant's
    trajectory is the plant's own, and a run with a plain schedule IS the
    drive-free trajectory the seat is measured against.  The stub DMN here is
    irrelevant to G by that same measurement, which the selftest exercises
    with a stream-emitting control rather than asserting."""
    p = p if p is not None else Params()
    cfg = Stage2Config(record_path=os.path.join(
        tempfile.mkdtemp(prefix="agenteXP2-base-"), "R"))
    st = run_stage2(rescue_schedule(), int(turns), cfg, p=p)
    G = [float(r.G) for r in st.log]
    return {"turns": len(G), "G": G, "G_end": (G[-1] if G else None),
            "G_min": (min(G) if G else None),
            "source": ("run_stage2 with the plain rescue schedule and no self "
                       "seat; the plant's trajectory is independent of the "
                       "generator when couple_backlog is False [MEASURED]")}


def probe_budgets(rows, budgets=(3, 12), band: float = COVERAGE_MIRROR_BAND
                  ) -> dict:
    """THE TWO PRE-DECLARED BUDGET PROBES, OFFLINE, ON THE PILOT'S OWN LOG.

    The retrieval seat's coverage is `covered / candidates`, and the
    affordable prefix is the MOST RECENT entries — so the BUDGET sets its
    length while the store grows (`handoff-selfreg-repoint-result`'s stated
    refinement).  The plan therefore allows a budget to be re-diagnosed from
    the pilot's own logged store size WITHOUT another GPU hour:
    `coverage(N) = min(N, B) / N`.

    THIS IS AN IDENTITY CHECKED AGAINST THE MEASUREMENT, not a model
    asserted: the logged coverage at the campaign's own B is compared with
    the formula's value at the same N, and the deviation is REPORTED.  A
    deviation means the formula is a model that does not hold on this log,
    and the probe says so instead of quoting a number."""
    cands = [int(_field_opt(r, "coverage_candidates") or 0) for r in rows]
    cands = [n for n in cands if n > 0]
    logged = [float(_field(r, "coverage")) for r in rows]
    out = {"budgets": {}, "n_store_sizes_logged": len(cands),
           "formula": "coverage(N) = min(N, B) / N  (the affordable prefix of "
                      "the most recent entries)"}
    for B in budgets:
        cov = [min(n, B) / n for n in cands]
        out["budgets"][f"B={B}"] = {
            "coverage_first": (cov[0] if cov else None),
            "coverage_min": (min(cov) if cov else None),
            "coverage_end": (cov[-1] if cov else None),
            "depletes_by_turn_300": bool(cov and min(cov) < band),
        }
    if cands and len(cands) == len(logged):
        pred = [min(n, CAMPAIGN_BUDGET) / n for n in cands]
        dev = max(abs(p - l) for p, l in zip(pred, logged))
        out["identity_at_campaign_budget"] = {
            "B": CAMPAIGN_BUDGET, "max_abs_deviation": dev,
            "tolerance": 1e-6,
            "reproduces_the_logged_coverage": bool(dev <= 1e-6),
        }
    else:
        out["identity_at_campaign_budget"] = {
            "B": CAMPAIGN_BUDGET, "max_abs_deviation": None,
            "reproduces_the_logged_coverage": None,
            "note": ("the rows carry no per-turn candidate count (a legacy "
                     "log): the identity is UNCHECKED, and it is reported as "
                     "unchecked rather than assumed"),
        }
    return out


# --------------------------------------------------------------------------
# THE PILOT'S GATES (P1-P5), pure over the logged rows + the baseline.
# --------------------------------------------------------------------------

def pilot2_gates(rows, baseline: dict, spec: dict, *,
                 warmup: int = 10) -> dict:
    """THE PRE-REGISTERED PILOT GATES (the plan's P1-P5), each with its
    predicate spelled out and its evidence attached.  NOTHING here scores
    recovery: the pilot's horizon never reaches the G2c stay window
    [1000,1400] in t.u., and a pilot that pretended to would be the
    inference-too-wide error the criterion exists to prevent.

      P1 SUPPLY   : spans_total > 0 AND the per-turn span counts VARY AND
                    content is non-empty in >= 50% of turns (else the
                    register is the crowding failure — fix num_predict /
                    num_ctx, do NOT proceed).
      P2 DEPLETION: coverage < 0.5 by the pilot's horizon at the campaign's
                    budget (else the budget/store regime is wrong: the two
                    budget probes are attached, computed from THIS log's own
                    store sizes, and if no probed budget depletes it, STOP —
                    the state design is the defect).
      P3 DRIVE LIVE: the drive is > 0 after the SECOND consolidation
                    boundary (the drive is one window LAGGED — window 1 is
                    undriven by construction) AND the plant MOVED off its own
                    arithmetic no-drive baseline.  `PLANT_MOVE_EPS` is a
                    numerical-visibility convention, not a dose threshold:
                    the plant is deterministic given a_hold, so a difference
                    at all IS the seat's effect — the MAGNITUDE is reported
                    and the H9 dose-response (>0.8 at a_hold 0, <0.35 at 0.9)
                    is the scale to read it against.  A drive that is set
                    while the plant does not move is a DESIGN finding to
                    REPORT (the gain stays 1.0), never to tune.
      P4 REGISTER : the trace and content char distributions are recorded and
                    the empty-content rate is < 25% (the V2 flag boundary).
      P5 COST     : not pass/fail — the measured median s/turn re-projects
                    the full plan.
    """
    supply = _supply_stats(rows)
    content = [int(_field_opt(r, "content_chars")
                   if _field_opt(r, "content_chars") is not None
                   else (_field_opt(r, "chars") or 0)) for r in rows]
    empty_rate = (sum(1 for c in content if c == 0) / len(content)
                  if content else None)
    nonempty_rate = (1.0 - empty_rate) if empty_rate is not None else None
    p1 = bool(supply["spans_total"] > 0
              and supply["distinct_span_counts"] > 1
              and nonempty_rate is not None and nonempty_rate >= 0.5)

    agent = score_coverage(rows)
    probes = probe_budgets(rows)
    cov_min = agent["coverage_min_all"]
    p2 = bool(cov_min is not None and cov_min < COVERAGE_MIRROR_BAND)
    any_probed_depletes = any(v["depletes_by_turn_300"]
                              for v in probes["budgets"].values())

    second_boundary = 2 * TAU_S_TURNS
    post = [float(_field(r, "drive")) for r in rows
            if int(_field(r, "turn")) > second_boundary
            and _field_opt(r, "drive") is not None]
    drive_live = bool(post and max(post) > 0.0)
    Gs = [float(_field(r, "G")) for r in rows]
    base = baseline.get("G") or []
    n_cmp = min(len(Gs), len(base))
    delta = (abs(Gs[n_cmp - 1] - base[n_cmp - 1]) if n_cmp else None)
    plant_moved = bool(delta is not None and delta > PLANT_MOVE_EPS)
    p3 = bool(drive_live and plant_moved)

    p4 = bool(empty_rate is not None
              and empty_rate < EMPTY_CONTENT_FLAG_RATE)
    secs = [float(_field(r, "secs")) for r in rows
            if _field_opt(r, "secs") is not None]
    post_secs = secs[warmup:] if len(secs) > warmup else secs
    per_turn = statistics.median(post_secs) if post_secs else float("nan")
    n_runs = len(campaign_plan())
    # F1: the cost is summed over the PLAN'S OWN specs (C6 capped at 300), not
    # n_runs x one horizon — the design plan is 13 specs / 17,100 turns, not
    # 13 x 1400.
    cost = campaign_cost_projection(per_turn, campaign_plan())

    return {
        "n_turns": len(rows),
        "supply": supply,
        "P1_supply": p1, "P2_depletion": p2, "P3_drive_live": p3,
        "P4_register": p4, "P5_cost": cost,
        "status": "PASS" if (p1 and p2 and p3 and p4) else "FAIL",
        "predicates": {
            "P1": "(spans_total > 0) AND (distinct per-turn span counts > 1) "
                  "AND (content non-empty in >= 50% of turns)",
            "P2": "(min coverage over the pilot < 0.5) at the campaign's "
                  "budget",
            "P3": "(max drive after turn 200 > 0) AND (|G_last - "
                  "G_baseline_last| > 1e-9): the drive is set at the second "
                  "boundary (one-window lag) and the plant moved off its own "
                  "no-drive trajectory",
            "P4": "empty-content rate < 0.25 (the V2 flag boundary)",
            "P5": "not pass/fail: measured s/turn -> the full plan "
                  "re-projected",
        },
        "evidence": {
            "P1": {"spans_total": supply["spans_total"],
                   "distinct_span_counts": supply["distinct_span_counts"],
                   "nonempty_content_rate": nonempty_rate},
            "P2": {"coverage_first": agent["coverage_first"],
                   "coverage_min_all": cov_min,
                   "coverage_end": agent["coverage_end"],
                   "budget": spec.get("budget"),
                   "budget_probes": probes,
                   "any_probed_budget_depletes": any_probed_depletes,
                   "stop_condition": ("if NO probed budget depletes by the "
                                      "pilot's horizon, STOP: the state "
                                      "design is the defect, not the "
                                      "experiment")},
            "P3": {"drive_max_after_second_boundary":
                   (max(post) if post else None),
                   "drive_by_turn": [(int(_field(r, "turn")),
                                      float(_field(r, "drive")))
                                     for r in rows[::max(1, len(rows) // 12)]],
                   "baseline_source": baseline.get("source"),
                   "G_last": (Gs[n_cmp - 1] if n_cmp else None),
                   "G_baseline_last": (base[n_cmp - 1] if n_cmp else None),
                   "abs_delta": delta, "eps": PLANT_MOVE_EPS,
                   "h9_dose_reference": ("G_end > 0.8 at a_hold 0 and < 0.35 "
                                         "at a_hold 0.9 [MEASURED, H9]")},
            "P4": {"empty_content_rate": empty_rate,
                   "trace_chars": _trace_stats(rows),
                   "content_chars": ({"min": min(content),
                                      "mean": (sum(content) / len(content)),
                                      "max": max(content)} if content
                                     else None)},
            "P5": {"per_turn_median_s": per_turn, "warmup_turns_excluded":
                   min(warmup, len(secs)), "n_runs_in_the_full_plan": n_runs,
                   "n_specs": cost["n_specs"],
                   "total_turns": cost["total_turns"],
                   "n_length_capped": cost["n_length_capped"],
                   "total_hours": cost["total_hours"]},
        },
    }


def _trace_stats(rows) -> dict | None:
    t = [int(x) for x in (_field_opt(r, "trace_chars") for r in rows)
         if x is not None]
    if not t:
        return None
    return {"min": min(t), "mean": sum(t) / len(t), "max": max(t),
            "turns_measured": len(t),
            "note": ("None on EVERY turn = the emitter declares no inward "
                     "channel (the /api/generate path): an absent channel is "
                     "not an empty one")}


# --------------------------------------------------------------------------
# THE CAMPAIGN RUNNER (harness config, generator, per-turn JSONL row).
# --------------------------------------------------------------------------

def build_cfg_campaign(spec: dict, dmn, *, outdir: str, engine: str,
                       crit_dir: str) -> Stage2Config:
    """THE CELL'S CONFIG — one place, so the C2/C3 pair cannot drift.

    The seat-on cells set the FIVE pre-registered switches together
    (`retrieval_priced`, `seed_self`, `self_T`, `agent_g`, and the small
    `budget`); the harness REFUSES them without the priced retrieval seat
    (stage2_harness.py:488-509), so they are set as one bundle here.  The
    seat-off cells keep every one of them OFF and leave the budget at its own
    default: C1 is the HEALTHY CONTROL and C4 is the WRAPPER check, and
    neither has a depletion instrument by construction.

    `agent_g` is set with the seat and NEVER without it: the harness refuses
    `agent_g=True` when the retrieval is unpriced (the G seat reads
    `Reconstruction.coverage`, which only the priced arm measures).

    ROUTING: every cell runs routing-on with the INJECTED selector (the
    realistic system, per the plan's axis audit) — the DMN hands over its raw
    stream and the EXTRACTOR decides what a claim is."""
    seat = bool(spec["seat"])
    return Stage2Config(
        dmn=dmn,
        couple_backlog=bool(spec["couple_backlog"]),
        routing_selector=PrefixRoutingSelector(),
        routing_criterion_dir=crit_dir,
        engine=engine,
        record_path=unique_record_path(outdir, spec["cell_id"]),
        retrieval_priced=seat,
        seed_self=seat,
        self_T=(CAMPAIGN_SELF_T if seat else None),
        agent_g=seat,
        budget=CostBudget(derivations_per_turn=int(
            spec["budget"] if spec["budget"] is not None
            else CAMPAIGN_DEFAULT_BUDGET)),
    )


#: THE FIELDS THAT DECIDE WHETHER TWO RUNS ARE THE SAME MEASUREMENT (S5).
#: The horizon was the first one to matter (a 300-turn pilot reused as a
#: 1400-turn cell); these are the rest: every configuration field that changes
#: the emitted stream or what the runner records about it.
CAMPAIGN_IDENTITY_FIELDS = ("api", "model", "endpoint", "num_predict",
                            "num_ctx", "engine", "budget", "turns",
                            "temperature", "brief")


def campaign_cell_config(args, spec: dict) -> dict:
    """THE ONE PLACE A CELL'S ACTUAL GENERATOR CONFIGURATION IS RESOLVED.

    `campaign_generator` builds the generator FROM THIS and the run's identity
    tag is the digest OF THIS, so the name on disk cannot describe a different
    configuration than the one that ran (the drift the review's S5 is about).

    THE NUMERIC KNOBS APPLY TO EVERY CELL, INCLUDING C6 (S3): MEASURED before
    this fix, C6 — the gemma precondition-negative through /api/generate —
    ran at `dmn_llm`'s own defaults (num_predict=800, num_ctx=4096) while
    campaign.json's pre-registered config RECORDED 6000/8192.  A control run
    in the register-starvation regime (the plan's own D2: at 800 the trace
    crowds the claims out) measures a different register than the arms it
    controls for, and the artifact misstates it.  The pre-registration is the
    specification, so the CONTROL runs at the campaign's numbers and the
    artifact then records what actually ran."""
    api = spec["api"]
    npred = (args.num_predict if args.num_predict is not None
             else CAMPAIGN_NUM_PREDICT)
    nctx = (args.num_ctx if args.num_ctx is not None else CAMPAIGN_NUM_CTX)
    if spec["model_role"] == "control":
        model = args.control_model
    elif api == dmn_llm.CHAT:
        model = args.chat_model
    else:
        model = args.model
    return {
        "api": api, "model": model,
        "endpoint": (args.chat_endpoint if api == dmn_llm.CHAT
                     else args.endpoint),
        "num_predict": int(npred), "num_ctx": int(nctx),
        "engine": args.engine,
        "budget": int(spec["budget"] if spec["budget"] is not None
                      else CAMPAIGN_DEFAULT_BUDGET),
        "turns": int(spec["turns"]),
        "temperature": float(args.temperature),
        # the FIXED FRAMING the run is emitted under (the brevity
        # instruction): it changes the prompt bytes and therefore the
        # stream, so it is part of the measurement's identity — a resume
        # keyed without it could reuse rows taken under the OTHER framing,
        # which is exactly S5's failure class.
        "brief": bool(CAMPAIGN_BRIEF),
    }


def campaign_identity_tag(cfg: dict) -> str:
    """The configuration's digest — in the run's NAME (`...-h<16 hex>`) and in
    every run JSON, so `runs2/<cell_id>.json` identifies the measurement and
    not merely the cell."""
    blob = json.dumps({k: cfg.get(k) for k in CAMPAIGN_IDENTITY_FIELDS},
                      sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def bind_campaign_identity(spec: dict, args) -> dict:
    """Bind a run spec to its configuration (S5): the identity dict, its tag,
    and the tag IN THE cell_id — which is the resume key."""
    cfg = campaign_cell_config(args, spec)
    tag = campaign_identity_tag(cfg)
    s = dict(spec)
    s["identity"] = cfg
    s["identity_tag"] = tag
    s["cell_id"] = f"{spec['cell_id']}-h{tag}"
    return s


def campaign_resume_ok(prev: dict, spec: dict) -> tuple[bool, str]:
    """MAY a completed run file be reused as THIS spec's measurement?

    Only if the recorded configuration identity MATCHES.  S5's failure mode
    was exactly this: the plan's own pilot verdict prescribes raising
    num_predict to >= 9000 and re-running, and a resume keyed on the cell and
    horizon alone would have read the 6000-budget rows as "already measured,
    status OK" and mixed two configurations inside one campaign.json.  The
    identity is in the file name, so this is the second lock on the same
    door."""
    if prev.get("status") != "OK":
        return False, f"prior attempt status={prev.get('status')}"
    want = spec.get("identity_tag")
    rec = (prev.get("config") or {}).get("identity_tag")
    if want is not None and rec != want:
        return False, (f"the recorded configuration identity differs "
                       f"({rec!r} != {want!r})")
    return True, "already measured, status OK, configuration identity matches"


def campaign_generator(args, spec: dict, *, world=None):
    """ONE campaign cell's generator, with the transport the CELL names.

    The seat-on cells hand the generator the SAME declared predicate set the
    harness's `build_batch` gets (`selfmodel.SELF_PREDICATES` /
    `COMMITMENT_PREDICATES`), or the prompt's grammar and the extractor drift
    apart (dmn_llm's G1 mirror).  The seat-off cells pass no set: the default
    instruction is then byte-identical to the pre-self one, which is what the
    C1/C4 controls require.

    The configuration comes from `campaign_cell_config` — the same function
    the run's identity tag is built from."""
    seat = bool(spec["seat"])
    cfg = campaign_cell_config(args, spec)
    api, model = cfg["api"], cfg["model"]
    npred, nctx = cfg["num_predict"], cfg["num_ctx"]
    preds, commits = (None, None)
    if seat:
        from selfmodel import COMMITMENT_PREDICATES, SELF_PREDICATES
        preds, commits = SELF_PREDICATES, COMMITMENT_PREDICATES
    return make_generator(args, spec["seed_base"], api=api, model=model,
                          num_predict=npred, num_ctx=nctx, world=world,
                          predicates=preds,
                          commitment_predicates=commits,
                          # SELF-DOMINANT IN EVERY CELL: the layout is a
                          # MEASURED variable and part of the FIXED
                          # instrument, so the cells differ in the seat and
                          # the drive, never in the prompt framing.
                          self_dominant=True,
                          # THE BREVITY INSTRUCTION, ON FOR EVERY CAMPAIGN
                          # CELL — a config fix for a MEASURED defect, and it
                          # is justified BECAUSE the precondition was
                          # RE-VERIFIED under it (both points measured;
                          # `dmn_llm.build_prompt` carries the numbers):
                          # the campaign prompt induced runaway reasoning on
                          # the remote 3B (3 of the pilot's 7 turns hit the
                          # num_predict cap at ~50 s with content = 0 — no
                          # supply, and an inward share saturated at 1.0 by
                          # the BUDGET, not by the phenomenon), while with
                          # the instruction the cap-hits went 0/3 at 5.5 s and
                          # the inward share still RISES as the self thins
                          # (0.909 -> 0.965, n=4/arm) — the precondition the
                          # a_hold mapping rests on.  THE CAMPAIGN'S OWN
                          # CONSTANT, not a literal: the same switch is in
                          # the run identity (CAMPAIGN_IDENTITY_FIELDS) and
                          # in every run JSON, so the framing a run was
                          # emitted under is recorded and not merely chosen.
                          brief=CAMPAIGN_BRIEF)


def campaign_schedule(spec: dict):
    """THE ONE THING THAT DIFFERS INSIDE THE C2/C3 PAIR: the schedule
    wrapper.  `drive` off = the frozen rescue scenario itself; `drive` on =
    the same schedule under `SelfReferentialDrive(gain=1.0)` — the gain is
    pre-registered and untuned (a collapse at gain 1.0 with the H9 drive
    range is consistent with the plant's steep dose-response; a gain SWEEP
    would be a separate pre-registration)."""
    if not spec["drive"]:
        return rescue_schedule()
    from selfmodel import SelfReferentialDrive
    return SelfReferentialDrive(rescue_schedule(), gain=CAMPAIGN_GAIN)


def run_one_campaign(spec: dict, args, outdir: str, *, crit_dir: str,
                     crit_meta: dict, print_table: bool = False,
                     progress_every: int = 25) -> dict:
    """ONE campaign run: one generator, one config, one schedule, one harness
    run, one JSONL row per turn (written and fsynced AS THEY LAND — the
    caches-are-the-record discipline), then the preserved criterion, the
    coverage mirror, the four-outcome quadrant and the void predicates."""
    turns = int(spec["turns"])
    rows_path = os.path.join(outdir, "rows2", f"{spec['cell_id']}.jsonl")
    summary_path = os.path.join(outdir, "runs2", f"{spec['cell_id']}.json")
    writer = JsonlWriter(rows_path)

    inner = campaign_generator(args, spec, world=TaskWorld(seed=WORLD_SEED))
    preds, commits = (None, None)
    if spec["seat"]:
        from selfmodel import COMMITMENT_PREDICATES, SELF_PREDICATES
        preds, commits = SELF_PREDICATES, COMMITMENT_PREDICATES
    rec = RecordingDMN(inner, predicates=preds,
                       commitment_predicates=commits)
    cfg = build_cfg_campaign(spec, rec, outdir=outdir, engine=args.engine,
                             crit_dir=crit_dir)
    sch = campaign_schedule(spec)
    p = Params()

    state = {"t_prev": time.time(), "rows": [], "secs": [],
             "t_eq_turn": True}
    t_start = time.time()

    def hook(turn: int, st) -> bool:
        now = time.time()
        secs = now - state["t_prev"]
        state["t_prev"] = now
        row = st.log[-1]
        gen = rec.by_turn.get(int(turn), {})
        plant = st.last_plant
        if float(row.t) != float(turn):
            state["t_eq_turn"] = False
        out = {
            "turn": int(turn), "t": float(row.t), "c": float(row.c),
            "G": float(row.G), "D": float(row.D),
            "E": float(plant.get("E", 0.0)),
            "a": float(plant.get("a", 0.0)), "S": float(plant.get("S", 0.0)),
            "g": float(plant.get("g", 0.0)),
            "B_plant": float(plant.get("B", 0.0)),
            "A_eff": float(row.A_eff),
            "backlog": int(row.backlog),
            "backlog_ema": float(row.backlog_ema),
            "backlog_rate": float(row.backlog_rate),
            # -- THE SELF'S PER-TURN OBSERVABLES (the mirror's inputs) ------
            "coverage": float(row.coverage),
            "coverage_candidates": int(st.recon_candidates),
            "drive": float(st.self_drive),
            "self_windows": int(st.self_windows),
            "self_block_chars": len(st.self_block or ""),
            "open_commitments": int(row.open_commitments),
            "expired": int(row.expired),
            # -- THE REGISTER (V2/V3's inputs) ------------------------------
            "trace_chars": gen.get("trace_chars"),
            "content_chars": int(gen.get("content_chars", 0)),
            "done_reason": gen.get("done_reason"),
            "eval_count": gen.get("eval_count"),
            "routed": int(row.routed),
            "derivations": int(row.derivations),
            "rejected": int(row.rejected),
            "verdicts_V": int(row.verdicts_V),
            "verdicts_R": int(row.verdicts_R),
            "verdicts_U": int(row.verdicts_U),
            "spans": int(gen.get("spans", -1)),
            "claims": int(gen.get("claims", -1)),
            "commitments": int(gen.get("commitments", -1)),
            "chars": int(gen.get("chars", 0)),
            "preds": gen.get("preds", []),
            "stream_sha16": gen.get("sha16", ""),
            "stream": gen.get("stream", ""),
            "secs": secs,
        }
        writer.write(out)
        state["rows"].append(out)
        state["secs"].append(secs)
        if print_table or turn == 1 or (turn % progress_every == 0):
            log(f"{spec['cell_id']} turn={turn:5d} t={row.t:7.1f} "
                f"G={row.G:.4f} D={row.D:.4f} c={row.c:.4f} "
                f"cov={row.coverage:.4f} drive={st.self_drive:.4f} "
                f"win={st.self_windows:3d} B={out['B_plant']:.4f} "
                f"A_eff={row.A_eff:.4f} spans={out['spans']:3d} "
                f"(claims={out['claims']} commits={out['commitments']}) "
                f"trace={out['trace_chars']} content={out['content_chars']} "
                f"({secs:.2f}s)")
        return True

    log(f"{spec['cell_id']} START cell={spec['cell']} "
        f"({spec['label']}) api={spec['api']} seat={spec['seat']} "
        f"drive={spec['drive']} couple={spec['couple_backlog']} "
        f"turns={turns} budget={spec['budget']} "
        f"seed_base={spec['seed_base']} (per-turn seed = base+turn)")
    err = None
    try:
        run_stage2(sch, turns, cfg, p=p, checkpoint_fn=hook)
    except Exception as exc:                  # noqa: BLE001 — reported, loud
        err = f"{type(exc).__name__}: {exc}"
        _warn(f"{spec['cell_id']} STOPPED at {len(state['rows'])} rows: {err}")
    wall = time.time() - t_start
    rows = state["rows"]
    status = "OK" if err is None else "ERROR"

    result = partialize_result(score_run(rows), status=status,
                               rows=len(rows), turns=turns)
    void = void_predicates(rows, spec, status=status, error=err)
    supply = _supply_stats(rows) if rows else {}
    post = state["secs"][min(10, len(state["secs"])):]
    if not post:
        post = state["secs"]
    per_turn = statistics.median(post) if post else float("nan")
    invariants = _trajectory_invariants(rows, sch)
    summary = {
        "cell_id": spec["cell_id"], "cell": spec["cell"],
        "prereg": CAMPAIGN_PREREG_NODE, "result_node": CAMPAIGN_RESULT_NODE,
        "runner": os.path.relpath(os.path.abspath(__file__), _ROOT),
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "config": {
            **{k: spec[k] for k in
               ("cell", "label", "seat", "drive", "couple_backlog", "api",
                "model_role", "budget", "repeat", "seed_base", "turns",
                "variant", "attempt", "length_capped", "priority")},
            "world_seed": WORLD_SEED, "temperature": args.temperature,
            "self_T": (CAMPAIGN_SELF_T if spec["seat"] else None),
            "retrieval_priced": bool(spec["seat"]),
            "seed_self": bool(spec["seat"]),
            "agent_g": bool(spec["seat"]),
            "derivations_per_turn": int(cfg.budget.derivations_per_turn),
            "gain": (CAMPAIGN_GAIN if spec["drive"] else None),
            "schedule": ("SelfReferentialDrive(rescue_schedule())"
                         if spec["drive"] else "rescue_schedule()"),
            "routing_selector": "PrefixRoutingSelector",
            "routing_consolidation_turns": TAU_S_TURNS,
            "routing_criterion": crit_meta,
            "model": inner.model, "endpoint": inner._url(),
            "api": inner.api, "num_predict": inner.num_predict,
            "num_ctx": inner.num_ctx, "self_dominant": inner.self_dominant,
            "brief": inner.brief,
            # S5 — THE RUN'S CONFIGURATION IDENTITY, as bound into its name.
            # `identity` is what the name's digest covers; the fields beside
            # it are what the generator ACTUALLY reported (inner.*), so a
            # drift between the two is visible in this one block.
            "identity": spec.get("identity"),
            "identity_tag": spec.get("identity_tag"),
            "record_path": cfg.record_path,
            "params": {"tau_S": float(p.tau_S), "source":
                       "Params() — the campaign does NOT sweep tau_S (the "
                       "agent's collapse timescale is the harness constant "
                       "TAU_S_TURNS, not Params.tau_S)"},
        },
        "criteria": {
            "plant": {"name": "G2c (VERBATIM, exp22's own form)",
                      "band": BAND1, "window": [WINDOW_T0, float(TURNS_FULL)],
                      "source": "Stage2LogRow.G",
                      "form": "recovered = (G_end > band) AND (min G over "
                              "the window > band)"},
            "agent": {"name": "the coverage mirror (the same FORM)",
                      "band": COVERAGE_MIRROR_BAND,
                      "window_turns": TAU_S_TURNS,
                      "source": "Stage2LogRow.coverage",
                      "form": "depleted = (coverage_end < band) AND (min "
                              "coverage over the LAST window < band)",
                      "threshold_note": ("0.5 is a STATED CONVENTION mirrored "
                                         "from exp22's BAND1, not a measured "
                                         "agent-side boundary")},
        },
        "result": result,
        "void": void,
        "supply": supply,
        "invariants": invariants,
        "timing": {"wall_s": wall, "turns_done": len(rows),
                   "per_turn_median_s": per_turn,
                   "projected_run_s": (per_turn * turns
                                       if per_turn == per_turn else None)},
        "status": status, "error": err,
        "t_eq_turn": state["t_eq_turn"],
        # F2 — THE RUN'S OWN PROVENANCE: was the pilot gate forced for this
        # run?  The help text promises `--force-after-failed-pilot` is
        # RECORDED, and a run JSON that a forced campaign wrote must say so.
        "forced": campaign_forced_provenance(args),
        # RECOVERY SCORING IS OFF for a run that cannot reach the window
        # (C6 by pre-registration; any run under a --turns override) AND for a
        # run that DID NOT COMPLETE its horizon (S2: `len(rows) >= turns`, not
        # `turns >= window` — a run that died at turn 1200 of 1400 reached the
        # window's start but not its end, so its G_end is a truncated reading):
        # the quadrant is still MEASURED and reported, it just does not enter
        # the recovery vector, and it is never reported as a non-recovery.
        "recovery_scored": bool(turns >= WINDOW_T0 + TAU_S_TURNS
                                and len(rows) >= turns
                                and not spec["length_capped"]),
        "rows_file": os.path.relpath(rows_path, _ROOT),
        "marking": {
            "MEASURED": ["the frozen plant's G/D/c per turn",
                         "the CEN's coverage and backlog per turn",
                         "the generator's trace/content chars and spans",
                         "every per-turn wall time",
                         "the drive the seat actually wrote (st.self_drive)"],
            "INTERPRETATION": ["that routing-on + agent_g is 'the realistic "
                               "system'", "that the C3-C2 difference is "
                               "attributable to the DRIVE alone"],
            "PROJECTION": ["the cost figures",
                           "the a_hold mapping itself (ORDINAL, UNVALIDATED)",
                           "anything about cells not yet run"],
        },
        "confounds": [
            f"B={cfg.budget.derivations_per_turn} STATED: the retrieval "
            f"budget starves the CEN's per-turn work budget from ~turn 6, so "
            f"the seat-on cells' collapse is the SEAT's (a_hold), not the "
            f"CEN's demand; the P2 coupling story is C5's",
            "the generator is a SPECTATOR of the plant when "
            "couple_backlog=False (p2r2): its output reaches the CEN and the "
            "telemetry only",
            "one turn = one t.u. (asserted: t == turn)",
            f"routing consolidation cadence is the harness constant "
            f"TAU_S_TURNS={TAU_S_TURNS} turns, NOT Params.tau_S",
            "the trace share is a SIZE RATIO of the model's two channels, "
            "not a semantic measure of self-reference (ORDINAL mapping)",
            f"length_capped={spec['length_capped']}: a capped run is "
            f"EXCLUDED from recovery scoring (never scored as a "
            f"non-recovery)",
        ],
    }
    writer.close()
    _atomic_json(summary_path, summary)
    log(f"{spec['cell_id']} DONE status={status} "
        f"outcome={result['outcome']} ({result['outcome_symbol']}) "
        + (f"[PARTIAL {result['rows_measured']}/{result['rows_expected']} "
           f"rows, quadrant NOT counted: "
           f"{result['quadrant_measured_but_NOT_counted']}] "
           if result.get("partial") else "")
        + f"plant_recovered={result['plant']['recovered']} "
        f"self_depleted={result['agent']['depleted']} "
        f"cov_first/min/end="
        f"{_num(result['agent']['coverage_first'], '.4f')}/"
        f"{_num(result['agent']['coverage_min_all'], '.4f')}/"
        f"{_num(result['agent']['coverage_end'], '.4f')} "
        f"G_end={_num(result['plant']['G_end'])} "
        f"void={void['void']} wall={wall:.1f}s "
        f"({_num(per_turn, '.2f')}s/turn median, {len(rows)} rows)")
    return summary


def _trajectory_invariants(rows, sch) -> dict:
    """THE INVARIANTS THE PROTOCOL REPORTS ACROSS SEEDS (never a bit-claim):
    where the coverage started and ended, what the drive did (the mean over
    the last half — the quantity the plant is actually held with), what the
    plant's G did, and the drive's own audit trail off the SEAT (only the
    seat has one)."""
    cov = [float(_field(r, "coverage")) for r in rows]
    drv = [float(_field(r, "drive")) for r in rows]
    Gs = [float(_field(r, "G")) for r in rows]
    half = len(drv) // 2
    # THE PLANT'S TRAJECTORY, HASHED: C4's assertion (V5) is BIT-IDENTITY with
    # C1, and a hash is what makes that checkable across seeds without
    # reopening the row files.  %.12g is the resolution the harness's own
    # floats carry (a coarser key would let a real seating change hide).
    traj = hashlib.sha256("|".join(f"{g:.12g}" for g in Gs).encode()).hexdigest()
    return {
        "coverage_start": (cov[0] if cov else None),
        "coverage_min": (min(cov) if cov else None),
        "coverage_end": (cov[-1] if cov else None),
        "drive_max": (max(drv) if drv else None),
        "drive_final": (drv[-1] if drv else None),
        "drive_mean_last_half": (statistics.fmean(drv[half:])
                                 if drv[half:] else None),
        "G_max": (max(Gs) if Gs else None),
        "G_min": (min(Gs) if Gs else None),
        "G_end": (Gs[-1] if Gs else None),
        "plant_trajectory_sha16": (traj[:16] if Gs else None),
        "drive_history_from_the_seat": list(
            getattr(sch, "drive_history", []) or []),
        "spans_total": sum(int(_field(r, "spans") or 0) for r in rows),
        "empty_content_rate": (
            sum(1 for r in rows if int(_field(r, "content_chars") or 0) == 0)
            / len(rows) if rows else None),
    }


# --------------------------------------------------------------------------
# THE CAMPAIGN'S ASSEMBLY AND ITS ACCEPTANCE (pure).
# --------------------------------------------------------------------------

def _expectation_met(counts: dict, n: int, expect: dict) -> bool | None:
    """Is a cell's pre-registered expectation met?  Read off the SAME counts
    the matrix prints — no second reading of the data."""
    if not n:
        return None
    rule, oc = expect.get("rule"), expect.get("outcome")
    if rule in ("plant_side", "sign"):
        return None                 # reported in its own block, not here
    k = int(counts.get(oc, 0))
    if rule == "all":
        return bool(k == n)
    if rule == "at_least":
        return bool(k >= int(expect.get("k", 1)))
    return None


def assemble_campaign(runs: list) -> dict:
    """PURE assembly: run summaries -> the per-cell four-outcome matrix.

    A MISSING CELL IS NOT A ZERO: every pre-registered condition appears with
    its own n (0 if never run) and an absent cell's fractions are None.  The
    four outcomes are counted SEPARATELY per cell (never merged into one
    bit), the plant and the agent criteria get their own k/N, the void
    ATTEMPTS and the void RATE are reported beside them, and the trajectory
    invariants are reported with their across-seed spread.

    A VOIDED RUN IS NOT IN THE TALLY (B1): it is excluded from `outcomes`,
    `n`, `plant_recovered` and `self_depleted`, counted in `n_voided`, and
    reported in full under `voids`/`void_attempts`/`void_rate`.  A void is a
    GATE on what counts, not a note beside the count — see `void_exclusion`
    in the returned document."""
    cells: dict = {}
    for cond in CAMPAIGN_CONDITIONS:
        cells[cond["cell"]] = {
            "cell": cond["cell"], "label": cond["label"],
            "seat": cond["seat"], "drive": cond["drive"],
            "length_capped": cond["length_capped"],
            "recovery_scored": not cond["length_capped"],
            "expect": cond["expect"], "n": 0, "n_runs_total": 0,
            "n_length_capped": 0, "n_voided": 0, "n_no_quadrant": 0,
            "outcomes": {},
            "plant_recovered": 0, "self_depleted": 0,
            "voids": [], "void_attempts": 0, "attempts": 0,
            "invariants": {}, "invariants_excluded": {}, "runs": [],
        }
    for r in runs:
        c = r.get("cell")
        if c not in cells:
            _warn(f"run {r.get('cell_id')}: unknown cell {c!r} — skipped in "
                  f"the assembly (never silently folded into another cell)")
            continue
        b = cells[c]
        b["runs"].append(r.get("cell_id"))
        b["n_runs_total"] += 1
        capped = bool((r.get("config") or {}).get("length_capped")
                      or (b["length_capped"] and not r.get("recovery_scored")))
        if capped:
            b["n_length_capped"] += 1
        # B1 — A VOID IS A GATE ON WHAT COUNTS, not a note beside it.  A run
        # that cannot show the phenomenon (V1 never-depleted, V2 register-
        # crowded, V3 died/no rows) is EXCLUDED from the outcome tallies it
        # would otherwise satisfy: MEASURED before this fix, a cell whose
        # every C3 run was V2-crowded read ACCEPT with `void_rate 1.0`
        # reported in the same block, and a run that DIED at turn 1200 of
        # 1400 contributed a full CO_COLLAPSE to the same conjunction.  The
        # void stays fully reported (voids, void_attempts, void_rate) — it is
        # the DENOMINATOR it no longer enters.
        voided = bool((r.get("void") or {}).get("void"))
        if voided:
            b["n_voided"] += 1
            b["voids"].append({"cell_id": r.get("cell_id"),
                               "reasons": (r.get("void") or {}).get(
                                   "void_reasons", [])})
        res = r.get("result") or {}
        oc = res.get("outcome")
        if not capped and not voided and oc is not None:
            b["outcomes"][oc] = b["outcomes"].get(oc, 0) + 1
            b["n"] += 1
            if (res.get("plant") or {}).get("recovered"):
                b["plant_recovered"] += 1
            if (res.get("agent") or {}).get("depleted"):
                b["self_depleted"] += 1
        elif not capped and not voided:
            # a surviving run with NO quadrant (S2's partial run, or an empty
            # log that no void predicate caught): it is not a fraction's
            # denominator either — an absent measurement is not a zero.
            b["n_no_quadrant"] += 1
        for a in (r.get("attempts") or []):
            b["attempts"] += 1
            if a.get("void"):
                b["void_attempts"] += 1
        if not (r.get("attempts")):
            b["attempts"] += 1
            if (r.get("void") or {}).get("void"):
                b["void_attempts"] += 1
        # THE SAME GATE ON THE CRITERION'S OWN INPUTS.  `c3_drive_live` is
        # read off C3's `drive_final` in `evaluate_campaign`, so a VOIDED run's
        # drive would otherwise be able to fire FALSIFY on evidence the
        # counted runs do not have — the pathway B1's own tally fix opens (the
        # voided run no longer dilutes the rate, so nothing else masks it).
        # Counted runs feed `invariants`; excluded ones (void or length-capped)
        # are reported under `invariants_excluded`, never silently dropped.
        for key in ("coverage_min", "coverage_end", "drive_mean_last_half",
                    "drive_final", "G_end", "empty_content_rate"):
            v = (r.get("invariants") or {}).get(key)
            if v is not None:
                (b["invariants"] if (not capped and not voided)
                 else b["invariants_excluded"]).setdefault(
                     key, []).append(float(v))
    for c, b in cells.items():
        n = b["n"]
        b["fraction"] = {k: (v / n if n else None)
                         for k, v in b["outcomes"].items()}
        b["plant_recovered_fraction"] = (b["plant_recovered"] / n if n else None)
        b["self_depleted_fraction"] = (b["self_depleted"] / n if n else None)
        b["void_rate"] = (b["void_attempts"] / b["attempts"]
                          if b["attempts"] else None)
        b["expectation_met"] = _expectation_met(b["outcomes"], n, b["expect"])
        b["invariants_spread"] = {
            k: {"n": len(v), "mean": statistics.fmean(v),
                "min": min(v), "max": max(v),
                "spread": (max(v) - min(v))}
            for k, v in b["invariants"].items()}
        b["invariants_excluded_spread"] = {
            k: {"n": len(v), "mean": statistics.fmean(v),
                "min": min(v), "max": max(v),
                "spread": (max(v) - min(v))}
            for k, v in b["invariants_excluded"].items()}
    # V5 — THE WIRING CHECK, from the runs' own plant-trajectory hashes, on
    # the seeds C1 and C4 SHARE (C4's repeat 0 and C1's repeat 0 are the same
    # seed base by construction).  A seating defect in the wrapper would move
    # C4's plant; with the wrapper inert the two are bit-identical.
    c1_sha = {int(r["config"]["seed_base"]):
              (r.get("invariants") or {}).get("plant_trajectory_sha16")
              for r in runs if r.get("cell") == "C1"
              and r.get("status") == "OK"}
    c4_sha = {int(r["config"]["seed_base"]):
              (r.get("invariants") or {}).get("plant_trajectory_sha16")
              for r in runs if r.get("cell") == "C4"
              and r.get("status") == "OK"}
    shared = sorted(set(c1_sha) & set(c4_sha))
    v5 = {
        "ran": bool(shared),
        "seeds_compared": shared,
        "c1_sha": {k: c1_sha[k] for k in shared},
        "c4_sha": {k: c4_sha[k] for k in shared},
        "plant_trajectory_identical": (
            all(c1_sha[k] == c4_sha[k] and c1_sha[k] is not None
                for k in shared) if shared else None),
        "predicate": ("V5: C4's plant trajectory is bit-identical to C1's on "
                      "the SHARED seed (the wrapper seated, not acting)"),
        "reason": (None if (shared and all(
            c1_sha[k] == c4_sha[k] and c1_sha[k] is not None for k in shared))
            else ("V5 WIRING: C4 differs from C1 on the plant trajectory — a "
                  "schedule-seating defect; the DRIVE pair is VOID until it "
                  "is fixed" if shared else
                  "V5 UNCHECKED: C1 and C4 have not both run on a shared seed")),
    }
    return {
        "prereg": CAMPAIGN_PREREG_NODE, "result_node": CAMPAIGN_RESULT_NODE,
        "task": ("the agentexp2 campaign: self depletion -> inward rise -> "
                 "drive -> a_hold -> (collapse vs rescue), in the LIVE "
                 "generator"),
        "cells": {c: b for c, b in cells.items()},
        "cell_order": list(CAMPAIGN_PHASE_ORDER),
        "runs_present": len(runs),
        "V5_wiring": v5,
        "outcome_vocabulary": OUTCOME_MEANINGS,
        "void_exclusion": {
            "rule": ("a VOIDED run is EXCLUDED from its cell's outcome tally "
                     "(outcomes, n, plant_recovered, self_depleted), from the "
                     "fractions built on them, AND from the trajectory "
                     "invariants a criterion reads (`invariants`; the voided/"
                     "capped ones are reported under `invariants_excluded`) — "
                     "so a voided C3 run's drive cannot fire FALSIFY on "
                     "evidence the counted runs do not have.  It is counted "
                     "in `n_voided` and reported in full under `voids` / "
                     "`void_attempts` / `void_rate`.  A void is a GATE on "
                     "what counts, not a note beside the count (a cell whose "
                     "runs are all V2 register-crowded must not be able to "
                     "satisfy the acceptance it was voided from)"),
            "carve_out_V5": ("V5 (the C4-vs-C1 plant-trajectory hash) reads "
                             "EVERY status-OK run on a shared seed, void or "
                             "not: the plant's trajectory is a MEASURED "
                             "quantity that a void does not invalidate, and a "
                             "wiring defect is visible on exactly those runs"),
            "by_cell": {c: {"n": cells[c]["n"], "n_voided": cells[c]["n_voided"],
                            "n_length_capped": cells[c]["n_length_capped"],
                            "n_no_quadrant": cells[c]["n_no_quadrant"],
                            "n_runs_total": cells[c]["n_runs_total"]}
                        for c in CAMPAIGN_PHASE_ORDER},
        },
        "reading_note": ("each cell reports its own four-outcome k/N and its "
                         "own denominator; an absent cell is n=0 with None "
                         "fractions, never a zero recovery.  `n_runs_total` "
                         "counts every attempt; `n` counts the runs that "
                         "carry a quadrant (not voided, not length-capped, "
                         "not partial); `n_voided`, `n_length_capped` and "
                         "`n_no_quadrant` account for the rest, so the "
                         "denominator can always be reconstructed from the "
                         "run total"),
    }


def evaluate_campaign(agg: dict, *, pilot_status: str = "ABSENT") -> dict:
    """THE ACCEPTANCE PREDICATE — a predicate over the four-outcome matrix,
    stated BEFORE any run and evaluated after.

      ACCEPT : C1 (plant+,self+) 3/3 AND C2 (plant+,self-) >= 2/3 AND
               C3 (plant-,self-) >= 2/3 AND the pilot gates held AND the
               void rate is reported.
      FALSIFY: C3 (plant+,self-) 3/3 with real depletion (coverage < 0.5) and
               a live drive (self_drive > 0): the seat is wired, the self
               depletes, the plant does not care — the a_hold mapping fails
               in the agent at gain 1.0 (equally publishable).
      VOID   : V4 — C1 failing anywhere voids the campaign's acceptance (the
               scenario baseline is broken; exp22's clean-OFF rule).
      MIXED  : anything else is INCONCLUSIVE and reported as the reliability
               bound; a follow-up at higher N on the split cell only.

    EVERY CONJUNCT IS ALSO GATED ON ITS PRE-REGISTERED N (B2): the ACCEPT and
    FALSIFY readings above are fractions over the cell's n, and a fraction
    over 1 is a different experiment — so a cell short of `CAMPAIGN_PREREG_N`
    (because seeds are still to run, because a crash stopped the campaign, or
    because runs were VOIDED and are now excluded from the denominator) makes
    the whole verdict INCOMPLETE, never ACCEPT.  A cell's n counts runs that
    carry a quadrant; voided and length-capped runs are accounted for
    separately by `assemble_campaign`."""
    cells = agg.get("cells", {})

    def cnt(cell, outcome):
        return int((cells.get(cell) or {}).get("outcomes", {}).get(outcome, 0))

    def n_of(cell):
        return int((cells.get(cell) or {}).get("n", 0))

    def rate(cell, outcome):
        n = n_of(cell)
        return (cnt(cell, outcome) / n) if n else None

    n1, n2, n3 = n_of("C1"), n_of("C2"), n_of("C3")
    # B2 — THE PRE-REGISTERED N.  `n` counts runs carrying a quadrant (a
    # voided run is excluded, so a cell of three V2-voided runs has n=0 —
    # that is how B1 and B2 meet).
    need = {c: int(CAMPAIGN_PREREG_N.get(c, 1))
            for c in CAMPAIGN_ACCEPTANCE_CELLS}
    n_have = {c: n_of(c) for c in CAMPAIGN_ACCEPTANCE_CELLS}
    n_short = {c: n_have[c] for c in CAMPAIGN_ACCEPTANCE_CELLS
               if n_have[c] < need[c]}
    n_prereg_met = not n_short
    voids_reported = all((cells.get(c) or {}).get("void_rate") is not None
                         for c in ("C1", "C2", "C3") if n_of(c))
    v5 = agg.get("V5_wiring") or {}
    v5_violated = bool(v5.get("ran") and v5.get("plant_trajectory_identical")
                       is False)
    cond = {
        "pilot_gates_held": pilot_status == "PASS",
        "n_prereg_met": bool(n_prereg_met),
        "C1_healthy_all": bool(n1 and cnt("C1", "HEALTHY") == n1),
        "C2_dissociation_at_least_2of3": bool(
            n2 and rate("C2", "DISSOCIATION") is not None
            and rate("C2", "DISSOCIATION") >= 2.0 / 3.0),
        "C3_cocollapse_at_least_2of3": bool(
            n3 and rate("C3", "CO_COLLAPSE") is not None
            and rate("C3", "CO_COLLAPSE") >= 2.0 / 3.0),
        "void_rate_reported": bool(voids_reported),
        "V5_wiring_clean": (not v5_violated),
    }
    c3_depleted = (n3 and cells["C3"]["self_depleted"] == n3)
    # THE FALSIFY READING NEEDS A LIVE DRIVE, read off the reported
    # invariants (the seat's own measure): a run whose drive never moved
    # cannot support it, and an ABSENT invariant is reported, never assumed.
    drv = ((cells.get("C3") or {}).get("invariants") or {}).get("drive_final")
    c3_drive_live = bool(drv and any(v > 0.0 for v in drv))
    c3_diss = rate("C3", "DISSOCIATION")
    # FALSIFY is a claim as strong as ACCEPT, so it carries the same N gate:
    # "C3 dissociation in EVERY seed" over one seed is not the pre-registered
    # reading.
    falsify = bool(n_prereg_met and c3_diss == 1.0 and c3_depleted
                   and c3_drive_live)

    if not n1:
        status = "INCOMPLETE"
        reason = ("the clean control (C1) has not run: an absent control is "
                  "not a passing control")
    elif v5_violated:
        status = "VOID"
        reason = ("V5 WIRING: C4 (the wrapper check) differs from C1 on the "
                  "plant trajectory — a schedule-seating defect; the DRIVE "
                  "pair is VOID until it is fixed")
    elif not cond["C1_healthy_all"]:
        status = "VOID"
        reason = ("V4 CONTROL FAILURE: C1 (the healthy control) did not read "
                  "(plant+, self+) in every seed — the generator/scenario "
                  "baseline is broken and a dirty control measures the "
                  "generator, not the coupling")
    elif n_short:
        status = "INCOMPLETE"
        reason = ("PRE-REGISTERED N NOT MET: " + ", ".join(
            f"{c} n={n_have[c]} of {need[c]}" for c in
            CAMPAIGN_ACCEPTANCE_CELLS if c in n_short)
            + " — the acceptance is a fraction over the pre-registered N "
              "(C1/C2/C3 = "
            + "/".join(str(need[c]) for c in CAMPAIGN_ACCEPTANCE_CELLS)
            + "), and VOIDED runs are EXCLUDED from that denominator, so a "
              "shortfall (seeds still to run, a crash mid-campaign, a "
              "--cells filter, or voids) is INCOMPLETE and can never read "
              "ACCEPT")
    elif falsify:
        status = "FALSIFY"
        reason = ("C3 read (plant+, self-) in every seed WITH real depletion "
                  "and a live drive: the seat is wired, the self depletes, "
                  "and the plant does not care — the a_hold mapping fails in "
                  "the agent at gain 1.0")
    elif all(cond.values()):
        status = "ACCEPT"
        reason = (f"C1 clean {cnt('C1', 'HEALTHY')}/{n1}, C2 (plant+,self-) "
                  f"{cnt('C2', 'DISSOCIATION')}/{n2}, C3 (plant-,self-) "
                  f"{cnt('C3', 'CO_COLLAPSE')}/{n3} (the predicate's own "
                  f"thresholds are all and >= 2/3) at the pre-registered N "
                  f"(n_prereg_met: {n_have} >= {need}), the pilot gates held "
                  f"and the void rate is reported: a real generator's own "
                  f"self-depletion, through the measured inward share, "
                  f"defeats the plant's rescue — and the rescue does not "
                  f"rebuild the self")
    else:
        status = "INCONCLUSIVE"
        reason = ("the matrix is mixed: reported as the reliability bound, "
                  "NOT smoothed.  A split cell is a follow-up at higher N on "
                  "THAT cell only (a cell SHORT of its pre-registered N is "
                  "INCOMPLETE, not mixed)")
    return {
        "status": status, "reason": reason, "conditions": cond,
        "counts": {c: {"n": n_of(c), "outcomes": (cells.get(c) or {}).get(
            "outcomes", {})} for c in ("C1", "C2", "C3", "C4", "C5", "C6")},
        # B1/B2 — WHAT THE NUMBERS COUNT: `n` is the runs carrying a quadrant
        # at this cell (voids, length-capped and partial runs excluded), and
        # the pre-registered N is what the verdict requires.
        "n_prereg": {c: {"n": n_have[c], "required": need[c],
                         "met": n_have[c] >= need[c]}
                     for c in CAMPAIGN_ACCEPTANCE_CELLS},
        "excluded_from_the_tally": {
            c: {"n_voided": (cells.get(c) or {}).get("n_voided", 0),
                "n_length_capped": (cells.get(c) or {}).get("n_length_capped",
                                                            0),
                "n_no_quadrant": (cells.get(c) or {}).get("n_no_quadrant", 0)}
            for c in ("C1", "C2", "C3", "C4", "C5", "C6")},
        "predicate": ("ACCEPT = C1(HEALTHY, all) AND C2(DISSOCIATION >= 2/3) "
                      "AND C3(CO_COLLAPSE >= 2/3) AT THE PRE-REGISTERED N "
                      "(C1-C3 n=3, VOIDED runs excluded from n) AND pilot "
                      "PASS AND void rate reported; FALSIFY = C3"
                      "(DISSOCIATION, all) with depletion and a live drive, "
                      "also at the pre-registered N; VOID = V4 (C1 dirty)"),
        "c3_depleted_in_every_seed": bool(c3_depleted),
        "c3_drive_live": c3_drive_live,
        "note": ("C6 is length-capped and EXCLUDED from recovery scoring; C4 "
                 "is a wiring check (V5) and C5 is reported by its own "
                 "predicate below; a PARTIAL run (S2: fewer rows than its own "
                 "horizon) has no quadrant and is not in any denominator"),
    }


def evaluate_c5(runs: list) -> dict:
    """C5's OWN PREDICATE, at its reduced priority: the OLD plan's acceptance
    line (the coupling arm failing at the arming cells) survives ONLY here.
    The campaign does NOT run the tau_S grid, so the cell it is read at is
    tau_S = 100 — the arming cell exp22's own vector FAILS at (spec 0/1,
    off 1/1) — and the report says so.

    ITS OWN DENOMINATOR IS REPORTED, NOT ASSUMED (B2): the predicate's clause
    is "fails in >= 2/N", which needs at least 2 SPEC runs; the campaign plans
    C5 at n=1 per arm, so at that n the predicate is NOT EVALUABLE and says
    so rather than reading a single failing run as a satisfied 2/N clause."""
    c5 = [r for r in runs if r.get("cell") == "C5"]
    if not c5:
        return {"ran": False,
                "predicate": ("coupling-ON (SPEC) does not recover in >= 2/N "
                              "at tau_S = 100 while coupling-OFF recovers"),
                "status": "NOT RUN"}
    spec_runs = [r for r in c5 if r["config"]["couple_backlog"]]
    off_runs = [r for r in c5 if not r["config"]["couple_backlog"]]
    spec_rec = sum(1 for r in spec_runs
                   if (r.get("result") or {}).get("plant", {}).get("recovered"))
    off_rec = sum(1 for r in off_runs
                  if (r.get("result") or {}).get("plant", {}).get("recovered"))
    n_spec, n_off = len(spec_runs), len(off_runs)
    # B2 (C5) — THE PREDICATE'S OWN DENOMINATOR.  "fails in >= 2/N" has the
    # threshold `spec_rec <= N - 2`, which at N=1 is `spec_rec <= 0`: every
    # SPEC run must fail, and the predicate then calls that ">= 2/N" — a
    # measurement it cannot make.  MEASURED before this fix: a single failing
    # SPEC run (1/1) read status=HOLDS as if the 2/N clause had been met.
    # The honest reading is the predicate's own: it needs >= 2 SPEC runs to
    # be evaluable AT ALL, and short of that the answer is NOT EVALUABLE (not
    # HOLDS, and not a weakened one-run predicate — re-wording the claim down
    # to fit one sample would be the §1a violation).  The campaign plans C5 at
    # n=1 per arm, so this is reported, not silently satisfied.
    min_spec = 2
    evaluable = bool(n_spec >= min_spec and n_off)
    ok = bool(evaluable and off_rec == n_off and spec_rec <= n_spec - min_spec)
    status = ("NOT EVALUABLE" if not evaluable
              else ("HOLDS" if ok else "DOES NOT HOLD"))
    return {
        "ran": True,
        "predicate": ("coupling-ON (SPEC) fails in >= 2/N at tau_S = 100 "
                      "while the coupling-OFF control recovers N/N"),
        "tau_S_cell": 100.0,
        "why_this_cell": ("the campaign does not sweep tau_S (the axis is "
                          "inert for the agent); 100 is the arming cell "
                          "exp22's own vector FAILS at"),
        "spec_recovered": spec_rec, "spec_n": n_spec,
        "off_recovered": off_rec, "off_n": n_off,
        "min_spec_runs": min_spec,
        "evaluable": evaluable,
        "reason": (None if evaluable else
                   (f"NOT EVALUABLE: the predicate needs >= {min_spec} SPEC "
                    f"runs (its threshold is n_spec - {min_spec}, i.e. 'at "
                    f"least {min_spec} failures'); this cell has n_spec="
                    f"{n_spec} — a single SPEC run cannot satisfy a 2/N "
                    f"clause, so it is reported as the weaker thing it is")),
        "status": status,
        "model_side_reference": {"source": "dpdr/cache/exp22_rescue.npz",
                                 "tau_S": 100.0, "off_recovered": 1,
                                 "spec_recovered": 0},
        "priority_note": ("REDUCED PRIORITY and reported as what it is: in "
                          "these cells the generator SPECTATES on the "
                          "coupling (p2r2), so this is the PLANT's own edge "
                          "feedback, not an agent path"),
    }



# ==========================================================================
# MODES
# ==========================================================================

# -- the agentexp2 campaign's modes ----------------------------------------

def campaign_forced_provenance(args) -> dict:
    """F2 — THE FORCED PILOT GATE, as it appears in a run's own JSON and in
    `campaign.json`.

    The help text for `--force-after-failed-pilot` says the override is
    "RECORDED"; MEASURED before this fix, it only warned on stderr, so a
    forced campaign's verdict could not be told from a gated one by reading the
    record.  One helper so the run provenance and the campaign artifact cannot
    spell the same fact differently."""
    forced = bool(getattr(args, "force_after_failed_pilot", False))
    return {"force_after_failed_pilot": forced,
            "pilot_gate": "OVERRIDDEN" if forced else "enforced"}


def _campaign_overrides(args, specs=None) -> dict:
    """What diverges from the agentexp2 pre-registration, recorded (never
    silent).

    F1: `--n` / `--turns` are OVERRIDES — recorded only when the user actually
    gave them, and the record says WHICH pre-registration field they moved
    (per-cell N; per-cell horizon, with C6's cap unmoved).  F2: the
    `--force-after-failed-pilot` flag is recorded here as well as in each run's
    own provenance (`runs2/<cell_id>.json`), because a forced run's verdict is
    uninterpretable without it — the help text promises the record and a WARN
    on stderr is not a record."""
    out = {}
    if getattr(args, "turns_explicit", False) and args.mode == "campaign":
        out["turns"] = {"prereg": "per cell (C1-C5 "
                                  f"{CAMPAIGN_TURNS}, C6 {CONTROL_CAP_TURNS})",
                        "used": args.turns,
                        "applies_to": ("every FULL-LENGTH cell; C6 keeps its "
                                       f"CONTROL_CAP_TURNS={CONTROL_CAP_TURNS} "
                                       "cap (the cap is not overridable "
                                       "upward)"),
                        "consequence": ("a horizon shorter than "
                                        f"{TURNS_FULL} leaves the G2c window "
                                        f"[{WINDOW_T0:g},{TURNS_FULL}] "
                                        "unreached, so those runs cannot "
                                        "score recovery and are "
                                        "length-capped")}
    if getattr(args, "n_explicit", False) and args.mode == "campaign":
        out["n"] = {"prereg_per_cell": dict(CAMPAIGN_PREREG_N),
                    "used": args.n,
                    "applies_to": ("EVERY condition: the design N is read off "
                                   "CAMPAIGN_CONDITIONS unless this is given, "
                                   "in which case it is the repeat count for "
                                   "every cell (C5 counts it PER ARM)")}
    if specs is not None and (out.get("n") or out.get("turns")):
        out["planned_specs"] = {
            "n_specs": len(specs),
            "design_n_specs": len(campaign_plan()),
            "per_cell": {cell: sum(1 for s in specs if s["cell"] == cell)
                         for cell in CAMPAIGN_PHASE_ORDER
                         if any(s["cell"] == cell for s in specs)},
            "total_turns": sum(int(s["turns"]) for s in specs)}
    if getattr(args, "force_after_failed_pilot", False):
        out["force_after_failed_pilot"] = {
            "used": True,
            "what_it_overrides": ("the pilot2 PASS gate before the campaign "
                                  "(and the pilot gate before --full)"),
            "consequence": ("the campaign's runs are NOT gated on a passing "
                            "pilot; the runs and the verdict that read them "
                            "carry this flag, so a forced result is visible in "
                            "the record rather than inferred from a warning "
                            "on stderr"),
            "for": "diagnostics only, never the pre-registered run"}
    if args.cells:
        out["cells"] = {"prereg": list(CAMPAIGN_PHASE_ORDER),
                        "used": list(args.cells)}
    if args.num_predict is not None:
        out["num_predict"] = {"prereg": CAMPAIGN_NUM_PREDICT,
                              "used": args.num_predict}
    if args.num_ctx is not None:
        out["num_ctx"] = {"prereg": CAMPAIGN_NUM_CTX, "used": args.num_ctx}
    if args.engine != "stub":
        out["engine"] = {"prereg": "stub", "used": args.engine}
    return out


def campaign_preregistration(args, specs: list) -> dict:
    """THE PREDICATE, THE VOID CONDITIONS, THE PROTOCOL AND THE DECISIONS —
    assembled BEFORE any run and written into campaign.json with
    status="STARTED", so a reader can always see what was asked before what
    was measured (the pre-registration discipline, applied to the artifact
    itself)."""
    return {
        "status": "STARTED",
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "prereg": CAMPAIGN_PREREG_NODE, "result_node": CAMPAIGN_RESULT_NODE,
        "runner": os.path.relpath(os.path.abspath(__file__), _ROOT),
        "acceptance_predicate": (
            "ACCEPT = C1 (plant+,self+) in 3/3 AND C2 (plant+,self-) in "
            ">= 2/3 AND C3 (plant-,self-) in >= 2/3 AT THE PRE-REGISTERED N "
            "(C1/C2/C3 n=3) AND the pilot gates held AND the void rate is "
            "reported.  VOIDED runs are EXCLUDED from those counts (a void is "
            "a gate on what counts, not a note beside it; voided, "
            "length-capped and partial runs are counted separately).  FALSIFY "
            "= C3 (plant+,self-) in 3/3 at the same N with real depletion "
            "(coverage < 0.5) and a live drive (self_drive > 0).  VOID = V4 "
            "(C1 not clean).  A cell short of its pre-registered N is "
            "INCOMPLETE, never ACCEPT: the acceptance is a fraction over N, "
            "and campaign.json is rewritten after every cell, so a crash "
            "after seed 1 must not leave an ACCEPT on disk.  INCONCLUSIVE = "
            "anything else, reported as the reliability bound."),
        "falsify_predicate": (
            "C3 (plant+, self-) in 3/3 with coverage < 0.5 and self_drive > 0 "
            "— the seat is wired, the self depletes, the plant does not care: "
            "the a_hold mapping fails in the agent at gain 1.0 (an equally "
            "publishable outcome)"),
        "void_conditions": {
            "V1": ("NO-DEPLETION: a seat-on run whose coverage never falls "
                   "below 0.5 is VOID (never a PASS) — the plant collapsed "
                   "for its own reasons, or nothing depleted; the budget is "
                   "named first in the reason"),
            "V2": ("CROWDING: empty content in > 50% of turns is VOID (the "
                   "inward share reads ~1.0 by REGISTER, not by depletion); "
                   "25-50% is FLAGGED register-degraded"),
            "V3": ("NO-TRACE / TRANSPORT: a run the transport refused (both "
                   "streams empty raises in dmn_llm) is VOID, never scored"),
            "V4": ("CONTROL FAILURE: C1 not reading (plant+, self+) in every "
                   "seed voids the campaign's acceptance (exp22's clean-OFF "
                   "rule)"),
            "V5": ("WIRING: C4 differing from C1 on the plant trajectory (a "
                   "schedule-seating defect) voids the DRIVE pair until fixed "
                   "— reported from the invariants"),
            "re-run": (f"a voided run is re-run ONCE with the next seed base "
                       f"(VOID_RERUNS_PER_CELL={VOID_RERUNS_PER_CELL}); the "
                       f"void RATE over attempts is reported — the re-run is "
                       f"a measurement of the void rate, not a retry loop"),
            "tally_exclusion": (
                "a VOIDED ATTEMPT IS EXCLUDED FROM THE CELL'S OUTCOME TALLY "
                "(outcomes, n, plant_recovered, self_depleted) and counted in "
                "n_voided with its rate and reasons beside it — so a cell "
                "whose runs are all voided has n=0 and CANNOT satisfy the "
                "acceptance it was voided from (MEASURED before this fix: "
                "three V2-CROWDED C3 runs read ACCEPT with void_rate 1.0 in "
                "the same block)"),
        },
        "four_outcomes": OUTCOME_MEANINGS,
        "determinism_protocol": {
            "seeds": {"per_turn": "base + turn",
                      "base_repeat": "SEED_BASE_DEFAULT + repeat*SEED_STRIDE",
                      "base_void_rerun": ("SEED_BASE_DEFAULT + repeat*"
                                          "SEED_STRIDE + (CAMPAIGN_N + "
                                          "attempt)*SEED_STRIDE — a re-run "
                                          "attempt draws a seed base OUTSIDE "
                                          "the N repeats' range (attempt 1 of "
                                          "a N=3 cell is 4242 + 4*SEED_STRIDE "
                                          "= 44242, NOT rep-1's 14242: "
                                          "MEASURED, the original offset "
                                          "collided with it and shared ")
                      + "every per-turn seed and the store history)",
                      "world_seed": WORLD_SEED,
                      "temperature": args.temperature,
                      "note": ("the NON-LLM parts of a run (plant, CEN, "
                               "retrieval, scoring) stay bit-deterministic "
                               "GIVEN the stream")},
            "claim_level": ("FRACTIONS over seeds, never bits: content "
                            "emission is VARIABLE AT A PINNED SEED (5 empty / "
                            "4 content-bearing calls on identical inputs; "
                            "trace 1884-3118 units — MEASURED, ollama's seed "
                            "determinism is 'in practice, not contractual')"),
            "n": {"C1": CAMPAIGN_N, "C2": CAMPAIGN_N, "C3": CAMPAIGN_N,
                  "C4": 1, "C5": "1 per arm", "C6": 1},
            "variance": ("the per-run trajectory invariants (coverage start / "
                         "min / end, drive mean over the last half, G_end, "
                         "empty-content rate) are reported WITH their "
                         "across-seed spread; a cell whose outcomes SPLIT "
                         "across seeds is reported as split"),
            "det_check2": ("--det-check2 measures OUTCOME-level repeatability "
                           "(same cell, same base seed, twice): the streams "
                           "differ; the question is whether the outcome and "
                           "the trajectory class do"),
        },
        "decisions": {
            "horizon": (f"KEEP {CAMPAIGN_TURNS} turns: the criterion window "
                        f"[{WINDOW_T0:g},{TURNS_FULL}] is the frozen "
                        f"scenario's own G2c window; shortening it would "
                        f"force a different rescue_t0 and break "
                        f"comparability.  The saving is the CELLS."),
            "budget": (f"B={CAMPAIGN_BUDGET} ACCEPT AND STATE: the only "
                       f"live-arm-calibrated budget (H9: coverage 0.1974 -> "
                       f"0.0409 -> 0.0241).  It starves the CEN's per-turn "
                       f"work budget from ~turn 6, so the seat-on cells' "
                       f"collapse is the SEAT's (a_hold); the P2 coupling "
                       f"story is C5's.  B=3/B=12 probes run OFFLINE on the "
                       f"pilot's own logged store sizes; a bump is a "
                       f"mid-campaign decision point, never silent tuning."),
            "num_ctx": (f"{CAMPAIGN_NUM_CTX} with num_predict="
                        f"{CAMPAIGN_NUM_PREDICT}, over dmn_llm's 4096 "
                        f"design parameter: MEASURED that at 4096 the CONTEXT "
                        f"consumed the trace (prompt 1009 + trace 3087 = 4096 "
                        f"exactly), i.e. the V2 register failure.  The self's "
                        f"depletability lives in the retrieval BUDGET, not "
                        f"the context; keeping 4096 would void runs for a "
                        f"reason that is not the self."),
            "empty_content_boundaries": (f"flag >= {EMPTY_CONTENT_FLAG_RATE}, "
                                         f"void > {EMPTY_CONTENT_VOID_RATE}"),
            "tau_S_axis": ("DROPPED as inert for the agent (the agent's "
                           "collapse timescale is the harness constant "
                           "TAU_S_TURNS, not Params.tau_S).  LOST: the "
                           "tau_S-response SHAPE is not measured agent-side — "
                           "no agent-side claim rests on it, and the loss "
                           "dies properly only if C5 is dropped entirely"),
            "routing_axis": ("CARRIED INSIDE the cells (routing-on + agent_g "
                             "where the seat is on): route-all vs routing-on "
                             "adds no discriminating power in these arms.  "
                             "HONEST COST: the G=None conservative arm is "
                             "exited, so the law now reads coverage — a "
                             "THRESHOLD effect, reported via the logged "
                             "coverage and drive"),
            "coupling_axis": ("ONLY inside C5, at reduced priority: the "
                              "generator spectates on the coupling (p2r2)"),
            "gain": f"{CAMPAIGN_GAIN} by pre-registration, NOT calibrated",
            "prompt_layout": ("SELF-DOMINANT in EVERY cell (the measured "
                              "layout that makes the channel balance move "
                              "with the self; a self APPENDED to a task "
                              "prompt produces no signal).  It is part of the "
                              "FIXED instrument, so C6 differs from C3 in the "
                              "model and the transport, not the framing."),
        },
        "cells": [{"cell": s["cell"], "label": s["label"], "seat": s["seat"],
                   "drive": s["drive"], "couple_backlog": s["couple_backlog"],
                   "api": s["api"], "model_role": s["model_role"],
                   "turns": s["turns"], "budget": s["budget"],
                   "seed_base": s["seed_base"], "cell_id": s["cell_id"],
                   "identity": s.get("identity"),
                   "identity_tag": s.get("identity_tag"),
                   "length_capped": s["length_capped"],
                   "priority": s["priority"], "role": s["role"],
                   "expect": s["expect"]} for s in specs],
        "n_runs_planned": len(specs),
        "n_design_specs": sum(1 for _ in campaign_plan()),
        # WHAT THE INVOCATION ACTUALLY PLANS, per cell (a FACT, beside the
        # design N in `determinism_protocol.n`).  F1: with no --n given this
        # IS the design plan (C1/C2/C3 3, C4 1, C5 2, C6 1 = 13 specs); an
        # explicit --n overrides every condition's design N and the counts
        # here grow with it — recorded, never silent.
        "n_planned_specs_per_cell": {
            cell: sum(1 for s in specs if s["cell"] == cell)
            for cell in CAMPAIGN_PHASE_ORDER
            if any(s["cell"] == cell for s in specs)},
        "n_planned_specs_note": (
            "the design plan is 13 specs (C1 3, C2 3, C3 3, C4 1, C5 2, C6 1 "
            "at its CONTROL_CAP_TURNS=300 cap) and is what the campaign plans "
            "when neither --n nor --turns is given; an EXPLICIT --n overrides "
            "EVERY condition's design N and an explicit --turns overrides "
            "every full-length cell's horizon (C6 stays capped either way), "
            "and both appear under `overrides`"),
        # S5 — WHAT A RUN'S NAME BINDS.  The horizon was the first identity
        # hole the shakedown found; these are the rest.
        "run_identity": {
            "fields": list(CAMPAIGN_IDENTITY_FIELDS),
            "in_the_name": ("every run's cell_id ends in -h<16 hex>, the "
                            "SHA-256 (first 16 hex) of those fields' values "
                            "for THAT cell; runs2/<cell_id>.json records them "
                            "and the resume path re-runs any spec whose "
                            "recorded identity differs"),
            "why": ("the pilot's own verdict prescribes raising num_predict "
                    "to >= 9000 and re-running after a P4 register failure; "
                    "with the identity keyed on the cell and horizon alone "
                    "that re-run would have read the 6000-budget rows as "
                    "'already measured, status OK' and mixed two "
                    "configurations inside one campaign.json (S5)"),
        },
        "artifact_lifecycle": {
            "campaign_json_rewritten_after_every_cell": True,
            "consequence": ("campaign.json is rewritten (status RUNNING and "
                            "the verdict so far) after EVERY cell, so a crash "
                            "leaves a PARTIAL matrix on disk.  That is safe "
                            "only because a cell short of its pre-registered "
                            "N reads INCOMPLETE, never ACCEPT — the verdict "
                            "cannot run ahead of the evidence."),
        },
        "config": {"endpoint": args.endpoint,
                   "chat_endpoint": args.chat_endpoint,
                   "model": args.model, "chat_model": args.chat_model,
                   "control_model": args.control_model, "api_default":
                   args.api, "engine": args.engine,
                   "num_predict": (args.num_predict if args.num_predict
                                   is not None else CAMPAIGN_NUM_PREDICT),
                   "num_ctx": (args.num_ctx if args.num_ctx is not None
                               else CAMPAIGN_NUM_CTX),
                   "temperature": args.temperature},
        "overrides": _campaign_overrides(args, specs),
        "forced": {
            **campaign_forced_provenance(args),
            "recorded": ("the pilot gate's override, as it stood when THIS "
                         "campaign.json was written (F2: the flag was warned "
                         "about on stderr and never recorded, so a forced "
                         "verdict could not be told from a gated one by "
                         "reading the record)"),
        },
        "cost_reference": {
            "note": ("the plan's cost basis: the reasoning arm's 47-80 s/turn "
                     "at num_predict 2600-6000 on the 14B [MEASURED]; the 3B "
                     "is 3.5x faster at ~15.4 s/turn with spans and 0 "
                     "fabricated args [MEASURED]; the pilot MEASURED 48.8 "
                     "s/turn at num_predict 6000.  PROJECTION until the pilot "
                     "measures this configuration."),
            "projected_s_per_turn": PROJECTED_S_PER_TURN,
            # F1: SUMMED OVER THE PLANNED SPECS, not n_runs x one horizon —
            # C6's declared 300-turn cap is what its runs cost.
            "planned": campaign_cost_projection(PROJECTED_S_PER_TURN, specs),
            "plan_note": ("these are the specs THIS invocation plans "
                          f"({len(specs)} of the design plan's "
                          f"{len(campaign_plan())}); the total sums each "
                          "spec's own horizon (C6 capped)"),
            "projected_total_hours": campaign_cost_projection(
                PROJECTED_S_PER_TURN, specs)["total_hours"],
        },
    }


def mode_pilot2(args) -> int:
    """THE CAMPAIGN'S PILOT GATE: ONE run, C3's configuration, 300 turns,
    one seed, per-turn printing, JSONL as it lands, gates P1-P5.  It scores
    NO recovery (its horizon never reaches the G2c window) — that is the
    point: it gates the REGIME before days of GPU are spent."""
    outdir = args.outdir
    ns = _isolate_namespaces(outdir)
    crit = ensure_criterion(ns["crit"])
    cond = campaign_condition("C3")
    specs = campaign_plan(["C3"], n=1, turns=args.turns, args=args)
    spec = specs[0]
    log(f"PILOT2 START (the campaign's mandatory gate) cell={spec['cell_id']} "
        f"turns={args.turns} budget={spec['budget']} api={spec['api']} "
        f"chat_endpoint={args.chat_endpoint} chat_model={args.chat_model} "
        f"num_predict="
        f"{args.num_predict if args.num_predict is not None else CAMPAIGN_NUM_PREDICT} "
        f"num_ctx="
        f"{args.num_ctx if args.num_ctx is not None else CAMPAIGN_NUM_CTX} "
        f"gain={CAMPAIGN_GAIN} crit={crit['dir']} (v{crit['version']})")
    summary = run_one_campaign(spec, args, outdir, crit_dir=ns["crit"],
                               crit_meta=crit, print_table=True,
                               progress_every=1)
    rows = _load_rows(summary["rows_file"])
    baseline = (plant_no_drive_baseline(len(rows), p=Params())
                if rows else {"G": [], "source": "no rows"})
    gate = pilot2_gates(rows, baseline, spec)
    gate.update({
        "cell_id": spec["cell_id"], "turns": args.turns, "prereg":
        CAMPAIGN_PREREG_NODE, "result_node": CAMPAIGN_RESULT_NODE,
        "run_status": summary["status"], "run_error": summary["error"],
        "config": summary["config"], "invariants": summary["invariants"],
        "void": summary["void"],
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "rows_file": summary["rows_file"],
        "condition": {k: cond[k] for k in ("cell", "label", "seat", "drive",
                                           "budget", "role", "expect")},
        "note": (f"the pilot scores NO recovery: its horizon ({len(rows)} "
                 f"turns) never reaches the G2c stay window "
                 f"[{WINDOW_T0:g}, {TURNS_FULL}] in t.u.  P3's baseline is "
                 f"the plant's OWN no-drive trajectory (MEASURED exact when "
                 f"couple_backlog is False)."),
    })
    path = os.path.join(outdir, "pilot2.json")
    _atomic_json(path, gate)
    e = gate["evidence"]
    log(f"PILOT2 P1 SUPPLY: {'PASS' if gate['P1_supply'] else 'FAIL'} — "
        f"spans_total={e['P1']['spans_total']} over {gate['n_turns']} turns, "
        f"distinct per-turn span counts="
        f"{e['P1']['distinct_span_counts']}, non-empty content rate="
        f"{_num(e['P1']['nonempty_content_rate'], '.3f')}")
    log(f"PILOT2 P2 DEPLETION: {'PASS' if gate['P2_depletion'] else 'FAIL'} — "
        f"coverage first/min/end="
        f"{_num(e['P2']['coverage_first'], '.4f')}/"
        f"{_num(e['P2']['coverage_min_all'], '.4f')}/"
        f"{_num(e['P2']['coverage_end'], '.4f')} at budget "
        f"{e['P2']['budget']}; budget probes="
        f"{ {k: v['coverage_min'] for k, v in e['P2']['budget_probes']['budgets'].items()} }"
        f" (any probed budget depletes: "
        f"{e['P2']['any_probed_budget_depletes']}); identity at B=6 "
        f"reproduces the logged coverage: "
        f"{e['P2']['budget_probes']['identity_at_campaign_budget']['reproduces_the_logged_coverage']}"
        f" (max deviation "
        f"{_num(e['P2']['budget_probes']['identity_at_campaign_budget']['max_abs_deviation'])})")
    log(f"PILOT2 P3 DRIVE LIVE: {'PASS' if gate['P3_drive_live'] else 'FAIL'} "
        f"— max drive after turn {2 * TAU_S_TURNS}="
        f"{_num(e['P3']['drive_max_after_second_boundary'], '.4f')}; "
        f"G_run - G_baseline at the last turn = "
        f"{_num(e['P3']['G_last'])} - {_num(e['P3']['G_baseline_last'])} = "
        f"{_num(e['P3']['abs_delta'], '.6f')} (eps {e['P3']['eps']}) "
        f"[the plant moved: {bool(e['P3']['abs_delta'] and e['P3']['abs_delta'] > e['P3']['eps'])}]")
    log(f"PILOT2 P4 REGISTER: {'PASS' if gate['P4_register'] else 'FAIL'} — "
        f"empty-content rate={_num(e['P4']['empty_content_rate'], '.3f')} "
        f"(flag {EMPTY_CONTENT_FLAG_RATE}, void {EMPTY_CONTENT_VOID_RATE}); "
        f"trace chars={e['P4']['trace_chars']}")
    c = gate["P5_cost"]
    log(f"PILOT2 P5 COST: {_num(c['per_turn_s'], '.3f')} s/turn median -> "
        f"{_num(c['per_run_hours'], '.2f')} h per "
        f"{c['turns_per_full_run']}-turn run "
        f"({_num(c['per_capped_run_hours'], '.2f')} h per length-capped run) "
        f"x {c['n_specs']} planned runs = "
        f"{_num(c['total_hours'], '.1f')} GPU-hours over {c['total_turns']} "
        f"turns [MEASURED s/turn -> PROJECTION]")
    log(f"PILOT2 VOID CHECK (not a gate): {gate['void']['void']} "
        f"{gate['void']['void_reasons']}")
    log(f"PILOT2 VERDICT: {gate['status']} -> {path}")
    if gate["status"] != "PASS":
        log("PILOT2 FAILED.  Per the pre-registration the STATE DESIGN (or "
            "the register configuration) is the defect, not the experiment: "
            "fix num_predict/num_ctx (P1/P4) or the budget/store regime "
            "(P2), and do NOT weaken the criterion and do NOT proceed to the "
            "campaign.")
    return 0 if gate["status"] == "PASS" else 2


def _with_attempt(spec: dict, attempt: int) -> dict:
    """A re-run spec: the SAME cell and configuration with the NEXT seed base
    (the plan's void rule), and a cell_id that says so.

    S1 — THE RE-RUN'S SEED BASE IS OUTSIDE THE REPEAT RANGE.  MEASURED before
    this fix: `seed_base + attempt * SEED_STRIDE` gave the voided rep-0 run the
    base 4242 + 1*10000 = 14242, which is EXACTLY rep-1's base
    (`seed_base_for(1)`), so a re-run shared rep-1's per-turn seeds, store
    history and world — the one thing the project's determinism convention
    forbids ("repeats never share a per-turn seed").  Attempt `a` now draws
    base + (N + a) * SEED_STRIDE, past the N repeats the plan already uses."""
    s = dict(spec)
    s["attempt"] = int(attempt)
    if attempt:
        reps = int(CAMPAIGN_PREREG_N.get(spec.get("cell"), CAMPAIGN_N))
        s["seed_base"] = (int(spec["seed_base"])
                          + (reps + attempt) * SEED_STRIDE)
        s["cell_id"] = f"{spec['cell_id']}-r{attempt}"
    return s


def _write_campaign(outdir, summaries, args, pilot, crit) -> dict:
    m = assemble_campaign(summaries)
    planned = campaign_invocation_plan(args)
    prereg = campaign_preregistration(args, planned)
    measured = ((pilot.get("evidence") or {}).get("P5") or {}).get(
        "per_turn_median_s")
    has_measured = bool(measured == measured and measured)
    m.update({
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "RUNNING" if len(summaries) < len(planned) else "DONE",
        "config": prereg["config"],
        "overrides": prereg["overrides"],
        # F1 — THE PLANNING RECORD SURVIVES THE RUN.  The pre-registration is
        # written before the first run, but campaign.json is then REWRITTEN
        # after every cell, and this update used to drop the planning block —
        # so the artifact a reader opens at the END carried no planned spec
        # count and no cost projection at all.  Both are carried forward, with
        # the cost re-stated at the PILOT'S OWN measured s/turn when the pilot
        # has one (the projection the plan's budget decision actually rests
        # on).
        "n_runs_planned": len(planned),
        "n_runs_present": len(summaries),
        "n_design_specs": prereg["n_design_specs"],
        "n_planned_specs_per_cell": prereg["n_planned_specs_per_cell"],
        "n_planned_specs_note": prereg["n_planned_specs_note"],
        "run_identity": prereg["run_identity"],
        "cost_reference": {
            **prereg["cost_reference"],
            "projected_at_pilot_measured": (
                campaign_cost_projection(measured, planned) if has_measured
                else {"note": ("the pilot has not measured a per-turn time: "
                               "only the plan's own s/turn estimate above")}),
            "measured_s_per_turn": measured if has_measured else None,
        },
        "pilot2": {"status": pilot.get("status"),
                   "P1_supply": pilot.get("P1_supply"),
                   "P2_depletion": pilot.get("P2_depletion"),
                   "P3_drive_live": pilot.get("P3_drive_live"),
                   "P4_register": pilot.get("P4_register"),
                   "per_turn_median_s": ((pilot.get("evidence") or {})
                                         .get("P5", {})
                                         .get("per_turn_median_s")),
                   "file": os.path.join(outdir, "pilot2.json")},
        "routing_criterion": crit,
        # F2 — THE FORCED RUN IS VISIBLE IN THE RECORD, not only in a warning:
        # the flag and the pilot status it overrode, as of this write.
        "forced": {
            **campaign_forced_provenance(args),
            "pilot2_status": pilot.get("status"),
            "meaning": ("force_after_failed_pilot True = the pilot gate was "
                        "OVERRIDDEN for these runs; the verdict below is a "
                        "forced verdict (the runs' own JSONs carry the same "
                        "flag)"),
        },
        "acceptance_predicate": prereg["acceptance_predicate"],
        "falsify_predicate": prereg["falsify_predicate"],
        "void_conditions": prereg["void_conditions"],
        "determinism_protocol": prereg["determinism_protocol"],
        "decisions": prereg["decisions"],
        "marking": {
            "MEASURED": ["the frozen plant's G/D/c per turn",
                         "the CEN's coverage and backlog per turn",
                         "the generator's trace/content chars and spans",
                         "the drive the seat wrote, per window",
                         "every per-turn wall time"],
            "INTERPRETATION": ["that the C3-C2 difference is attributable to "
                               "the DRIVE alone", "that routing-on + agent_g "
                               "is 'the realistic system'"],
            "PROJECTION": ["the cost figures", "the a_hold mapping itself "
                           "(ORDINAL, UNVALIDATED)", "the precondition's "
                           "generality beyond the models measured"],
        },
        "path": os.path.join(outdir, "campaign.json"),
    })
    m["acceptance"] = evaluate_campaign(m, pilot_status=pilot.get("status"))
    m["c5"] = evaluate_c5(summaries)
    _atomic_json(os.path.join(outdir, "campaign.json"), m)
    return m


def mode_campaign(args) -> int:
    """THE CAMPAIGN: the six conditions in the plan's phase order, the
    preserved criterion + the coverage mirror per run, the four-outcome matrix
    per cell, the voiding conditions and the acceptance predicate — REFUSED
    without a passing pilot2."""
    outdir = args.outdir
    ns = _isolate_namespaces(outdir)
    pilot_path = os.path.join(outdir, "pilot2.json")
    if not os.path.exists(pilot_path) and not args.force_after_failed_pilot:
        log("REFUSING the campaign: no pilot2.json under " + outdir +
            ".  Run --pilot2 first (the plan's mandatory gate).")
        return 3
    pilot = (json.load(open(pilot_path, encoding="utf-8"))
             if os.path.exists(pilot_path) else {"status": "ABSENT"})
    if pilot.get("status") != "PASS" and not args.force_after_failed_pilot:
        log(f"REFUSING the campaign: the pilot2 gate is {pilot.get('status')} "
            f"(P1={pilot.get('P1_supply')} P2={pilot.get('P2_depletion')} "
            f"P3={pilot.get('P3_drive_live')} P4={pilot.get('P4_register')}).  "
            f"The STATE DESIGN / REGISTER is the defect, not the experiment.")
        return 3
    if args.force_after_failed_pilot and pilot.get("status") != "PASS":
        _warn("--force-after-failed-pilot OVERRIDES the pilot2 gate; the "
              "override is recorded in campaign.json (RECORDED, not silent)")

    specs = campaign_invocation_plan(args)
    prereg = campaign_preregistration(args, specs)
    # THE PREDICATE IS ON DISK BEFORE THE FIRST RUN.
    _atomic_json(os.path.join(outdir, "campaign.json"), prereg)
    log("CAMPAIGN PRE-REGISTRATION (written before any run): "
        + prereg["acceptance_predicate"])
    log("CAMPAIGN VOID CONDITIONS: V1 no-depletion, V2 crowding, V3 no-trace, "
        "V4 control failure, V5 wiring — each reported with its reason; a "
        f"voided run is re-run ONCE with the next seed base "
        f"(VOID_RERUNS_PER_CELL={VOID_RERUNS_PER_CELL}) and the void rate is "
        f"reported.")
    log("CAMPAIGN DETERMINISM: fractions over seeds (N="
        f"{CAMPAIGN_N} for C1/C2/C3), trajectory invariants + spread "
        f"reported; bit-level streams are MEASURED non-reproducible at a "
        f"pinned seed.")
    seen = [c["cell"] for c in prereg["cells"]]
    per_cell = prereg["n_planned_specs_per_cell"]
    turns_by_cell = {c: sorted({s["turns"] for s in specs if s["cell"] == c})
                     for c in sorted(set(seen))}
    log(f"CAMPAIGN PLANNED: {len(specs)} runs over cells "
        f"{sorted(set(seen))} (phase order {list(CAMPAIGN_PHASE_ORDER)}); "
        f"per cell {per_cell} at turns {turns_by_cell}; n={args.n}"
        f"{' (--n OVERRIDE: every condition)' if args.n_explicit else ' (the per-cell design N)'}; "
        f"turns "
        f"{'--turns OVERRIDE (C6 stays capped)' if args.turns_explicit else 'per cell (C6 at its declared cap)'}; "
        f"cells_filter={args.cells}")
    if args.dry_run:
        for s in specs:
            log(f"  plan {s['cell_id']}  cell={s['cell']} api={s['api']} "
                f"seat={s['seat']} drive={s['drive']} "
                f"couple={s['couple_backlog']} turns={s['turns']} "
                f"budget={s['budget']}")
        c = campaign_cost_projection(PROJECTED_S_PER_TURN, specs)
        log(f"DRY RUN projection at the plan's {PROJECTED_S_PER_TURN} s/turn: "
            f"{_num(c['per_run_hours'], '.2f')} h per full-length run, "
            f"{_num(c['total_hours'], '.1f')} GPU-hours total over "
            f"{c['n_specs']} specs / {c['total_turns']} turns "
            f"({c['n_length_capped']} length-capped run(s), "
            f"{c['turns_length_capped']} turns) [PROJECTION]")
        measured = ((pilot.get("evidence") or {}).get("P5") or {}).get(
            "per_turn_median_s")
        if measured == measured and measured:
            mc = campaign_cost_projection(measured, specs)
            log(f"DRY RUN projection at the PILOT2-MEASURED {measured:.3f} "
                f"s/turn: {_num(mc['per_run_hours'], '.2f')} h per "
                f"{mc['turns_per_full_run']}-turn run "
                f"({_num(mc['per_capped_run_hours'], '.2f')} h per capped "
                f"run), {_num(mc['total_hours'], '.1f')} GPU-hours total over "
                f"{mc['n_specs']} specs / {mc['total_turns']} turns "
                f"[MEASURED s/turn -> PROJECTION]")
        else:
            log("DRY RUN: no pilot2-measured per-turn time available — the "
                "plan's estimate above is the only figure")
        return 0
    crit = ensure_criterion(ns["crit"])
    summaries = []
    for i, spec in enumerate(specs, 1):
        done = os.path.join(outdir, "runs2", f"{spec['cell_id']}.json")
        if os.path.exists(done) and not args.rerun:
            prev = json.load(open(done, encoding="utf-8"))
            # S5: reuse requires the CONFIGURATION to match, not just the
            # cell and horizon (a resume that reads a 6000-budget row as a
            # 9000-budget measurement is the defect, not the convenience).
            ok, why = campaign_resume_ok(prev, spec)
            if ok:
                log(f"CAMPAIGN {i}/{len(specs)} {spec['cell_id']} — SKIPPED "
                    f"({why}; --rerun to re-measure)")
                summaries.append(prev)
                _update_campaign(outdir, summaries, args, pilot, crit)
                continue
            log(f"CAMPAIGN {i}/{len(specs)} {spec['cell_id']} — RE-RUNNING "
                f"({why})")
        log(f"CAMPAIGN {i}/{len(specs)} {spec['cell_id']}")
        attempts = []
        chosen = None
        for attempt in range(VOID_RERUNS_PER_CELL + 1):
            s = _with_attempt(spec, attempt)
            try:
                chosen = run_one_campaign(
                    s, args, outdir, crit_dir=ns["crit"], crit_meta=crit,
                    progress_every=args.progress_every)
            except Exception:                    # noqa: BLE001
                _warn("cell " + s["cell_id"] + " raised out of "
                      "run_one_campaign:")
                traceback.print_exc()
                break
            attempts.append({
                "attempt": attempt, "cell_id": s["cell_id"],
                "seed_base": s["seed_base"], "status": chosen["status"],
                "void": chosen["void"]["void"],
                "void_reasons": chosen["void"]["void_reasons"],
                "outcome": (chosen["result"] or {}).get("outcome"),
                "coverage_min": (chosen["invariants"] or {}).get(
                    "coverage_min"),
            })
            if not chosen["void"]["void"]:
                break
            if attempt < VOID_RERUNS_PER_CELL:
                log(f"CAMPAIGN {spec['cell_id']} VOID at attempt {attempt}: "
                    f"{chosen['void']['void_reasons']} — RE-RUNNING ONCE with "
                    f"the next seed base (a measurement of the void RATE, "
                    f"not a retry loop)")
        if chosen is not None:
            chosen = dict(chosen)
            chosen["attempts"] = attempts
            chosen["void_rate_this_cell"] = (
                sum(1 for a in attempts if a["void"]) / len(attempts)
                if attempts else None)
            summaries.append(chosen)
        _update_campaign(outdir, summaries, args, pilot, crit)
    return _finish_campaign(outdir, summaries, args, pilot, crit)


def _update_campaign(outdir, summaries, args, pilot, crit):
    return _write_campaign(outdir, summaries, args, pilot, crit)


def _finish_campaign(outdir, summaries, args, pilot, crit) -> int:
    m = _write_campaign(outdir, summaries, args, pilot, crit)
    for cell in m["cell_order"]:
        b = m["cells"][cell]
        if not b["n"] and not b["attempts"]:
            log(f"MATRIX {cell} ({b['label']}): NOT RUN (n=0 — an absent cell "
                f"is not a zero recovery)")
            continue
        log(f"MATRIX {cell} ({b['label']}): recovery-scored n={b['n']} "
            f"of {b['n_runs_total']} runs "
            f"({b['n_voided']} void — EXCLUDED from the tally, "
            f"{b['n_length_capped']} length-capped, "
            f"{b['n_no_quadrant']} without a quadrant) outcomes="
            f"{b['outcomes']} plant_recovered={b['plant_recovered']}/"
            f"{b['n']} self_depleted={b['self_depleted']}/{b['n']} "
            f"void_rate={_num(b['void_rate'], '.2f')} "
            f"expectation_met={b['expectation_met']}")
    a = m["acceptance"]
    log(f"ACCEPTANCE: {a['status']} — {a['reason']}")
    log(f"conditions: {a['conditions']}")
    log(f"C5 (reduced priority): {m['c5']['status']} — "
        f"{ {k: m['c5'][k] for k in ('spec_recovered', 'spec_n', 'off_recovered', 'off_n') if k in m['c5']} }")
    log("campaign written to " + m["path"])
    return 0


def mode_det_check2(args) -> int:
    """OUTCOME-LEVEL REPEATABILITY (the honest replacement for bit-diffing).

    The SAME campaign cell at the SAME base seed, twice.  The streams are
    MEASURED not to be bit-identical at a pinned seed, so the question this
    answers is the decision-relevant one: do the OUTCOME and the trajectory
    class reproduce?  Both runs, their invariants and their diff are written;
    the history accumulates the base rate."""
    outdir = args.outdir
    ns = _isolate_namespaces(outdir)
    crit = ensure_criterion(ns["crit"])
    k = args.det_turns
    results = []
    for rep in (0, 1):
        spec = campaign_plan(["C3"], n=1, turns=k)[0]
        spec = dict(spec, cell_id=f"det2-{rep}", repeat=-1)
        sub = os.path.join(outdir, f"pass{rep}")
        os.makedirs(sub, exist_ok=True)
        log(f"DET-CHECK2 pass {rep} ({k} turns, SAME seed_base="
            f"{spec['seed_base']}, cell=C3's configuration)")
        results.append(run_one_campaign(spec, args, sub, crit_dir=ns["crit"],
                                        crit_meta=crit,
                                        progress_every=max(1, k // 4)))
    a, b = results
    inv_a, inv_b = a["invariants"], b["invariants"]
    cmp = {
        "turns_a": a["timing"]["turns_done"],
        "turns_b": b["timing"]["turns_done"],
        "outcome_a": (a["result"] or {}).get("outcome"),
        "outcome_b": (b["result"] or {}).get("outcome"),
        "outcome_identical": ((a["result"] or {}).get("outcome")
                              == (b["result"] or {}).get("outcome")),
        "plant_recovered_a": (a["result"] or {}).get("plant", {}).get(
            "recovered"),
        "plant_recovered_b": (b["result"] or {}).get("plant", {}).get(
            "recovered"),
        "self_depleted_a": (a["result"] or {}).get("agent", {}).get(
            "depleted"),
        "self_depleted_b": (b["result"] or {}).get("agent", {}).get(
            "depleted"),
        "coverage_identical": (a["result"] or {}).get("agent", {}).get(
            "depleted") == (b["result"] or {}).get("agent", {}).get(
            "depleted"),
        "invariants": {k2: {"a": inv_a.get(k2), "b": inv_b.get(k2),
                            "delta": (abs(float(inv_a[k2]) - float(inv_b[k2]))
                                      if inv_a.get(k2) is not None
                                      and inv_b.get(k2) is not None else None)}
                       for k2 in ("coverage_min", "coverage_end",
                                  "drive_final", "drive_mean_last_half",
                                  "G_end", "empty_content_rate")},
    }
    stamp = time.strftime("%Y%m%dT%H%M%S")
    hist_dir = os.path.join(outdir, "det_check2")
    os.makedirs(hist_dir, exist_ok=True)
    out = os.path.join(hist_dir, f"det_check2-{stamp}.json")
    payload = {"prereg": CAMPAIGN_PREREG_NODE, "turns": k,
               "cell": "C3 (seat-on/drive-on), SAME seed base both passes",
               "seed_base": campaign_plan(["C3"], n=1)[0]["seed_base"],
               "chat_model": args.chat_model, "temperature": args.temperature,
               "comparison": cmp,
               "run_status": [r["status"] for r in results],
               "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    _atomic_json(out, payload)
    prior = []
    for fn in sorted(os.listdir(hist_dir)):
        if fn.startswith("det_check2-") and fn.endswith(".json"):
            try:
                prior.append(json.load(open(os.path.join(hist_dir, fn),
                                            encoding="utf-8"))["comparison"]
                             ["outcome_identical"])
            except Exception:                # noqa: BLE001 — a partial file
                continue
    history = {"runs": len(prior),
               "n_outcome_identical": sum(1 for q in prior if q),
               "turns_per_run": k,
               "statement": (
                   f"{sum(1 for q in prior if q)}/{len(prior)} det-check2 "
                   f"invocations reproduced the OUTCOME at the same base seed "
                   f"({k} turns each).  This is the OUTCOME-level repeatability "
                   f"the protocol rests on — NOT a claim that the streams are "
                   f"bit-identical (MEASURED: they are not, at a pinned seed)")}
    _atomic_json(os.path.join(hist_dir, "det_check2_history.json"), history)
    log(f"DET-CHECK2: outcome A={cmp['outcome_a']} B={cmp['outcome_b']} "
        f"identical={cmp['outcome_identical']}; coverage class identical="
        f"{cmp['coverage_identical']}; G_end {_num(cmp['invariants']['G_end']['a'])} "
        f"vs {_num(cmp['invariants']['G_end']['b'])}")
    log(f"DET-CHECK2 HISTORY: {history['statement']}")
    log("written to " + out)
    return 0


def _isolate_namespaces(outdir: str) -> dict:
    """The run's OWN namespaces (the batteries' convention): the mechanism's
    anchors and the routing criterion never touch the designer's real
    ~/.cen-anchors / ~/.cen-routingcrit."""
    anchors = os.path.join(outdir, "anchors")
    crit = os.path.join(outdir, "crit")
    os.makedirs(anchors, exist_ok=True)
    os.environ["CEN_ANCHOR_DIR"] = anchors
    os.environ.setdefault("CEN_ROUTINGCRIT_DIR", crit)
    return {"anchors": anchors, "crit": crit}


def mode_pilot(args) -> int:
    outdir = args.outdir
    ns = _isolate_namespaces(outdir)
    cell = cell_of("route-all", "SPEC", 100.0, 0)
    crit = ensure_criterion(ns["crit"])
    log(f"PILOT START (the plan's mandatory gate) cell={cell['cell_id']} "
        f"turns={args.turns} endpoint={args.endpoint} model={args.model} "
        f"anchors={ns['anchors']} crit={crit['dir']} (v{crit['version']})")
    summary = run_one(cell, args, outdir, turns=args.turns,
                      crit_dir=ns["crit"], crit_meta=crit, progress_every=1,
                      print_table=True)
    rows = _load_rows(summary["rows_file"])
    gate = gate_pilot(rows)
    gate.update({
        "cell_id": cell["cell_id"], "turns": args.turns,
        "run_status": summary["status"], "run_error": summary["error"],
        "config": summary["config"], "trajectory": summary["trajectory"],
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "prereg": PREREG_NODE,
        "t_eq_turn": summary["trajectory"]["t_eq_turn"],
        "note": ("the pilot does NOT score recovery: its horizon ("
                 f"{args.turns} turns) never reaches the G2c stay window "
                 f"[{WINDOW_T0:g}, {TURNS_FULL}] in t.u."),
    })
    path = os.path.join(outdir, "pilot.json")
    _atomic_json(path, gate)

    log("PILOT GATE 1 (generator supply, non-empty and varying): "
        f"{'PASS' if gate['gate1_supply_nonempty_varying'] else 'FAIL'} — "
        f"spans_total={gate['supply']['spans_total']} over "
        f"{gate['supply']['turns']} turns, distinct per-turn span counts="
        f"{gate['supply']['distinct_span_counts']}, spans min/max/mean="
        f"{gate['supply']['spans_min']}/{gate['supply']['spans_max']}/"
        f"{gate['supply']['spans_mean']:.2f}, chars min/max/mean="
        f"{gate['supply']['chars_min']}/{gate['supply']['chars_max']}/"
        f"{gate['supply']['chars_mean']:.0f}, empty turns="
        f"{gate['supply']['empty_turns']}")
    log("PILOT GATE 2 (backlog_outstanding RISES): "
        f"{'PASS' if gate['gate2_backlog_rises'] else 'FAIL'} — "
        f"first-half mean={gate['backlog']['first_half_mean']:.2f} "
        f"second-half mean={gate['backlog']['second_half_mean']:.2f}; "
        f"min={gate['backlog']['min']} max={gate['backlog']['max']} "
        f"turn10={gate['backlog']['early_turn10']} "
        f"final={gate['backlog']['final']}")
    log("PILOT GATE 3 (B = the P2 ADDEND through the P2 wiring BUILDS): "
        f"{'PASS' if gate['gate3_backlog_ema_builds'] else 'FAIL'} — "
        f"max B={gate['B_p2']['max']:.6f} "
        f"final={gate['B_p2']['final']:.6f} "
        f"(in the model's own B range [0,1]: "
        f"{gate['gate3_B_in_model_range']}; raw backlog STOCK EMA beside "
        f"it, TELEMETRY not B: max={gate['backlog_ema']['max']:.3f}; "
        f"plant's own proxy B max="
        f"{_num(summary['trajectory']['B_plant_max'])}; D_max="
        f"{_num(summary['trajectory']['D_max'])})")
    c = gate["gate4_projected_cost"]
    log("PILOT GATE 4 (cost, not pass/fail): measured "
        f"{_num(c['per_turn_s'], '.3f')} s/turn median -> "
        f"{_num(c['per_run_hours'], '.2f')} h per {c['turns_per_run']}-turn "
        f"run x {c['cells']} cells = "
        f"{_num(c['total_hours'], '.1f')} GPU-hours [PROJECTION]")
    log(f"PILOT t == turn (the one-turn = one-t.u. mapping): "
        f"{summary['trajectory']['t_eq_turn']}")
    d = gate["diagnostics_not_gates"]
    ca, cs_ = d["cannibalization"], d["coupling_scale"]
    log("PILOT DIAGNOSTIC (NOT a gate) — cannibalization switch: "
        f"c_max={ca['c_max']:.4f} over the pilot's {gate['n_turns']} turns; "
        f"armed_in_pilot={ca['armed_in_pilot']}; E_max={_num(ca['E_max'], '.4f')} "
        f"vs the arming level in force "
        f"{_num(ca['binding_level'], '.4f')} (plant switch floor="
        f"{ca['plant_switch_floor']!r} — None = the FROZEN MODEL's floorless "
        f"switch; SN ACTIVATION BELIEF="
        f"{ca['sn_activation_floor']} (NOT the plant's level); Stage-1's own "
        f"default still {ca['stage1_default_floor_still']}; theta_eff at the "
        f"end={_num(ca['theta_eff_final'], '.4f')})")
    log("PILOT DIAGNOSTIC (NOT a gate) — coupling unit: B (the P2 addend = "
        f"the PLANT's own EMA_tauD(c), max={cs_['B_plant_max']:.4f}, the "
        f"model's own B range is [0,1]; the CEN's u/n TELEMETRY beside it = "
        f"{_num(cs_['B_telemetry_u_over_n_max'], '.4f')}, raw stock EMA = "
        f"{_num(cs_['backlog_ema_max_STOCK_not_B'], '.2f')}) -> A_eff_max "
        f"measured on the plant = {cs_['A_eff_max_measured']:.4f} "
        f"(in the model's range: {cs_['A_eff_in_model_range']}) -> the "
        f"model's own D-equilibrium at that A_eff = "
        f"{_num(cs_['D_equilibrium_at_A_eff'], '.4f')}, observed D_max="
        f"{_num(cs_['D_observed_max'], '.4f')} [MEASURED]")
    log(f"PILOT VERDICT: {gate['status']} -> {path}")
    if gate["status"] != "PASS":
        log("PILOT FAILED.  Per the pre-registration the STATE DESIGN is the "
            "defect, not the experiment: fix the generator's state design "
            "(dmn_llm.TaskWorld / the supply path), do NOT proceed to the "
            "sweep, and do NOT change the criterion.  Confound (i) worth "
            "checking first: retrieval is unpriced here, so the generator's "
            "SELF block is EMPTY (supply is measured with that block off).")
    return 0 if gate["status"] == "PASS" else 2


def _load_rows(rel_path: str) -> list:
    path = rel_path if os.path.isabs(rel_path) else os.path.join(_ROOT,
                                                                 rel_path)
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def mode_full(args) -> int:
    outdir = args.outdir
    ns = _isolate_namespaces(outdir)
    pilot_path = os.path.join(outdir, "pilot.json")
    if not os.path.exists(pilot_path) and not args.force_after_failed_pilot:
        log("REFUSING the sweep: no pilot.json under " + outdir + ".  Run "
            "--pilot first (the plan's mandatory gate).")
        return 3
    pilot = (json.load(open(pilot_path, encoding="utf-8"))
             if os.path.exists(pilot_path) else {"status": "ABSENT"})
    if pilot.get("status") != "PASS" and not args.force_after_failed_pilot:
        log(f"REFUSING the sweep: the pilot gate is {pilot.get('status')} "
            f"(gate1={pilot.get('gate1_supply_nonempty_varying')} "
            f"gate2={pilot.get('gate2_backlog_rises')} "
            f"gate3={pilot.get('gate3_backlog_ema_builds')}).  The STATE "
            f"DESIGN is the defect, not the experiment — do not proceed.")
        return 3
    if args.force_after_failed_pilot and pilot.get("status") != "PASS":
        _warn("--force-after-failed-pilot OVERRIDES the pilot gate; the "
              "override is recorded in matrix.json (RECORDED, not silent)")

    cells = plan_cells(args.n, routings=args.routing or ROUTINGS,
                       arms=args.arm or ARMS,
                       cells=tuple(args.tau_s) if args.tau_s else TAU_S_CELLS)
    if args.dry_run:
        plan_cost = project_cost(PROJECTED_S_PER_TURN, len(cells), args.turns)
        for c in cells:
            log(f"  plan {c['cell_id']}")
        log(f"DRY RUN: {len(cells)} runs = 2 routings x 2 arms x "
            f"{len(args.tau_s or TAU_S_CELLS)} tau_S x N={args.n}, "
            f"{args.turns} turns each")
        log(f"DRY RUN projection at the PLAN's pre-registered "
            f"{PROJECTED_S_PER_TURN} s/turn: {plan_cost['per_run_hours']:.2f} h "
            f"per run, {plan_cost['total_hours']:.1f} GPU-hours total "
            f"[PROJECTION]")
        measured = (pilot.get("gate4_projected_cost") or {}).get("per_turn_s")
        if measured == measured and measured:      # not None and not NaN
            mc = project_cost(measured, len(cells), args.turns)
            log(f"DRY RUN projection at the PILOT-MEASURED {measured:.3f} "
                f"s/turn: {mc['per_run_hours']:.2f} h per run, "
                f"{mc['total_hours']:.1f} GPU-hours total [MEASURED s/turn -> "
                f"PROJECTION], i.e. {measured / PROJECTED_S_PER_TURN:.1f}x the "
                f"plan's own estimate")
        else:
            log("DRY RUN: no pilot-measured per-turn time available "
                "(pilot.json absent or carries none) — the plan's estimate "
                "above is the only figure, and it is the one the pilot "
                "exists to replace")
        return 0
    crit = ensure_criterion(ns["crit"])
    log(f"FULL START cells={len(cells)} turns={args.turns} N={args.n} "
        f"engine={args.engine} crit={crit['dir']} (v{crit['version']})")
    summaries = []
    for i, c in enumerate(cells, 1):
        done = os.path.join(outdir, "runs", f"{c['cell_id']}.json")
        if os.path.exists(done) and not args.rerun:
            prev = json.load(open(done, encoding="utf-8"))
            if prev.get("status") == "OK":
                log(f"MATRIX {i}/{len(cells)} {c['cell_id']} — SKIPPED "
                    f"(already measured, status OK; --rerun to re-measure)")
                summaries.append(prev)
                _write_matrix(outdir, summaries, args, pilot, crit,
                              force=args.force_after_failed_pilot)
                continue
            log(f"MATRIX {i}/{len(cells)} {c['cell_id']} — RE-RUNNING "
                f"(prior attempt status={prev.get('status')})")
        log(f"MATRIX {i}/{len(cells)} {c['cell_id']}")
        try:
            summaries.append(run_one(c, args, outdir, turns=args.turns,
                                     crit_dir=ns["crit"], crit_meta=crit,
                                     progress_every=args.progress_every))
        except Exception:                        # noqa: BLE001
            _warn("cell " + c["cell_id"] + " raised out of run_one:")
            traceback.print_exc()
        _write_matrix(outdir, summaries, args, pilot, crit, force=
                      args.force_after_failed_pilot)
    return _finish_matrix(outdir, summaries, args, pilot, crit)


def _write_matrix(outdir, summaries, args, pilot, crit, force=False) -> dict:
    m = assemble_matrix(summaries)
    m.update({
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "turns": args.turns, "n_requested": args.n,
        "engine": args.engine, "model": args.model, "endpoint": args.endpoint,
        "temperature": args.temperature,
        "routing_criterion": crit,
        "pilot": {"status": pilot.get("status"),
                  "gate1": pilot.get("gate1_supply_nonempty_varying"),
                  "gate2": pilot.get("gate2_backlog_rises"),
                  "gate3": pilot.get("gate3_backlog_ema_builds"),
                  "projected_total_hours":
                      (pilot.get("gate4_projected_cost") or {}).get(
                          "total_hours")},
        "forced_past_failed_pilot": bool(force),
        "overrides": _overrides(args),
        "acceptance": evaluate_acceptance(m["recovered_count"], args.n,
                                          m["cells_tau_S"],
                                          n_per_cell=m["n_per_cell"]),
        "n_below_prereg": bool(args.n < N_DEFAULT),
        "model_side_reference": {
            "source": "dpdr/cache/exp22_rescue.npz [MEASURED]",
            "grid_tau_S": [25.0, 50.0, 100.0, 150.0, 200.0, 400.0, 800.0],
            "off_recovered": [1, 1, 1, 1, 1, 1, 1],
            "spec_recovered": [1, 0, 0, 1, 1, 1, 1],
            "arming_cells": [25.0, 50.0, 100.0],
            "note": "the agent vectors above sit beside these ON THE THREE "
                    "ARMING CELLS; exp22's failures are at tau_S 50 and 100",
        },
        "marking": {
            "MEASURED": ["the frozen plant's G/D/c per turn",
                         "the generator's stream and its extracted spans",
                         "the CEN's backlog and its EMA",
                         "every per-turn wall time"],
            "INTERPRETATION": ["route-all SPEC-vs-OFF as the direct agent "
                               "replica of exp22's coupling: the demand is "
                               "the generator's varying supply, not a fixed c"],
            "PROJECTION": ["all cost figures", "any claim about cells not run",
                           "the model->agent mapping (ORDINAL, UNVALIDATED)"],
        },
        "path": os.path.join(outdir, "matrix.json"),
    })
    _atomic_json(os.path.join(outdir, "matrix.json"), m)
    return m


def _finish_matrix(outdir, summaries, args, pilot, crit) -> int:
    m = _write_matrix(outdir, summaries, args, pilot, crit,
                      force=args.force_after_failed_pilot)
    a = m["acceptance"]
    for ro in m["routings"]:
        for arm in m["arms"]:
            log(f"VECTOR {ro}/{arm}: recovered "
                f"{m['recovered_count'][ro][arm]} of N={args.n} per cell "
                f"{[float(c) for c in m['cells_tau_S']]}  (fractions "
                f"{[None if f is None else round(f, 3) for f in
                    m['recovered_fraction'][ro][arm]]})")
        log(f"VECTOR {ro}: OFF counts {m['recovered_count'][ro]['OFF']}, "
            f"SPEC counts {m['recovered_count'][ro]['SPEC']}")
    log(f"ACCEPTANCE: {a['status']} — {a['reason']}")
    log(f"per-setting: {a['per_setting_status']}")
    log(f"control clean (all routings) = {a['control_clean_all_routings']}; "
        f"SPEC fails >=2/N at 50 and 100 = {a['spec_fails_at_50_100']}")
    log("matrix written to " + m["path"])
    return 0


def mode_rescore(args) -> int:
    """OFFLINE: recompute the pilot gate (and its diagnostics) from the rows
    ALREADY on disk — the caches-are-the-record discipline.  No endpoint, no
    re-measurement: the rows are the measurement and the gate is a pure
    function of them.  The rewritten pilot.json is MARKED as rescored, so a
    reader can always tell a fresh pilot from a re-evaluated one."""
    outdir = args.outdir
    path = os.path.join(outdir, "pilot.json")
    if not os.path.exists(path):
        log("REFUSING to rescore: no pilot.json under " + outdir)
        return 3
    old = json.load(open(path, encoding="utf-8"))
    cell_id = old.get("cell_id")
    rows_path = os.path.join(outdir, "rows", f"{cell_id}.jsonl")
    if not os.path.exists(rows_path):
        log(f"REFUSING to rescore: the rows file {rows_path} is absent — "
            f"there is no measurement to re-evaluate")
        return 3
    rows = _load_rows(rows_path)
    gate = gate_pilot(rows)
    gate.update({
        "cell_id": cell_id, "turns": len(rows), "prereg": PREREG_NODE,
        "rescored_from_rows": True,
        "rescored_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "rows_file": os.path.relpath(rows_path, _ROOT),
        "run_status": old.get("run_status"), "run_error": old.get("run_error"),
        "config": old.get("config"),
        "trajectory": old.get("trajectory"),
        "created_ts": old.get("created_ts"),
        "t_eq_turn": (old.get("trajectory") or {}).get("t_eq_turn"),
        "note": old.get("note"),
    })
    _atomic_json(path, gate)
    log(f"RESCORED pilot.json from {len(rows)} recorded rows -> {path}")
    log(f"VERDICT (unchanged by rescoring): {gate['status']} "
        f"gate1={gate['gate1_supply_nonempty_varying']} "
        f"gate2={gate['gate2_backlog_rises']} "
        f"gate3={gate['gate3_backlog_ema_builds']}")
    return 0 if gate["status"] == "PASS" else 2


def mode_matrix(args) -> int:
    runs = []
    for f in args.matrix:
        obj = json.load(open(f, encoding="utf-8"))
        if "config" in obj and "result" in obj:
            runs.append(obj)
        elif "runs_list" in obj:
            runs.extend(obj["runs_list"])
        else:
            _warn(f"{f}: not a run summary (no config/result) — skipped")
    m = assemble_matrix(runs)
    m["acceptance"] = evaluate_acceptance(m["recovered_count"], args.n,
                                          m["cells_tau_S"],
                                          n_per_cell=m["n_per_cell"])
    m["created_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    m["runs_source"] = [os.path.abspath(f) for f in args.matrix]
    out = os.path.join(args.outdir, "matrix.json")
    _atomic_json(out, m)
    log(f"MATRIX ASSEMBLED from {len(runs)} run summaries -> {out}")
    log(f"counts: {json.dumps(m['recovered_count'], sort_keys=True)}")
    log(f"ACCEPTANCE: {m['acceptance']['status']} — "
        f"{m['acceptance']['reason']}")
    return 0


def mode_det_check(args) -> int:
    """Settle the plan's OPEN QUESTION: is the same (arm, cell, seed) stream
    bit-identical when re-run?  Two runs of K turns each, diffed per turn.
    Offline-free (it needs the endpoint) but cheap."""
    # FRESH per invocation: a re-used record path carries a prior attempt's
    # decision ids, so a second --det-check would be refused by the C9 chain.
    outdir = tempfile.mkdtemp(prefix="ac-det-check-")
    ns = _isolate_namespaces(outdir)
    crit = ensure_criterion(ns["crit"])
    k = args.det_turns
    results = []
    for rep in (0, 1):
        cell = cell_of("route-all", "SPEC", 100.0, 0)   # SAME seed both times
        cell["cell_id"] = f"det-{rep}"
        cell["repeat"] = -1                             # not a matrix cell
        # a separate outdir per pass so rows/records never collide
        sub = os.path.join(outdir, f"pass{rep}")
        os.makedirs(sub, exist_ok=True)
        log(f"DET-CHECK pass {rep} ({k} turns, SAME seed_base="
            f"{cell['seed_base']})")
        results.append(run_one(cell, args, sub, turns=k, crit_dir=ns["crit"],
                               crit_meta=crit, progress_every=max(1, k // 4)))
    a = _load_rows(results[0]["rows_file"])
    b = _load_rows(results[1]["rows_file"])
    same_turns = min(len(a), len(b))
    # TWO comparisons, because they answer different questions and can
    # disagree (they did): (i) the plan's literal test — are the STREAMS
    # bit-identical?  (ii) the decision-relevant test — is the SCORED
    # TRAJECTORY identical?  The plant never reads the prose: the coupling
    # signal is the span COUNT (count -> backlog -> backlog_ema -> D -> G), so
    # a re-sampled prose can change every byte while the plant trajectory is
    # exactly reproduced.
    cmp = {"turns_compared": same_turns,
           "turns_a": len(a), "turns_b": len(b),
           "identical_streams": 0, "differing_turns": [],
           "identical_span_counts": 0, "identical_G": 0,
           "identical_backlog": 0, "identical_backlog_ema": 0,
           "identical_backlog_rate": 0,
           "identical_B_plant": 0,
           "identical_D": 0}
    for i in range(same_turns):
        if a[i]["stream_sha16"] == b[i]["stream_sha16"]:
            cmp["identical_streams"] += 1
        else:
            cmp["differing_turns"].append(
                {"turn": a[i]["turn"], "sha_a": a[i]["stream_sha16"],
                 "sha_b": b[i]["stream_sha16"],
                 "chars_a": a[i]["chars"], "chars_b": b[i]["chars"],
                 "spans_a": a[i]["spans"], "spans_b": b[i]["spans"]})
        if a[i]["spans"] == b[i]["spans"]:
            cmp["identical_span_counts"] += 1
        if a[i]["G"] == b[i]["G"]:
            cmp["identical_G"] += 1
        if a[i]["backlog"] == b[i]["backlog"]:
            cmp["identical_backlog"] += 1
        if a[i]["backlog_ema"] == b[i]["backlog_ema"]:
            cmp["identical_backlog_ema"] += 1
        # BOTH ADDEND CANDIDATES, compared separately and never merged:
        # `B_plant` IS the P2 addend (the plant's own EMA_tauD(c), the
        # quantity D reads); `backlog_rate` is the CEN's u/n telemetry.
        if a[i]["B_plant"] == b[i]["B_plant"]:
            cmp["identical_B_plant"] += 1
        if a[i]["backlog_rate"] == b[i]["backlog_rate"]:
            cmp["identical_backlog_rate"] += 1
        if a[i]["D"] == b[i]["D"]:
            cmp["identical_D"] += 1
    cmp["all_streams_identical"] = bool(same_turns and
                                        cmp["identical_streams"] == same_turns)
    traj_identical = bool(same_turns
                          and cmp["identical_G"] == same_turns
                          and cmp["identical_D"] == same_turns
                          and cmp["identical_B_plant"] == same_turns
                          and cmp["identical_backlog_rate"] == same_turns)
    cmp["trajectory_identical"] = traj_identical
    if cmp["all_streams_identical"]:
        cmp["answer"] = (
            "THIS INVOCATION reproduced: all "
            f"{same_turns} compared turns emitted bit-identical streams "
            "[MEASURED, this box, this model, this temperature].  THIS IS ONE "
            "INVOCATION AND IT DOES NOT LICENSE N=1 ON ITS OWN: that decision "
            "reads det_check_history.json, which compares invocations — "
            "byte-level reproducibility measured INTERMITTENT (see the "
            "history statement).  N >= 3 stands unless the history shows "
            "every invocation reproducing")
    else:
        cmp["answer"] = (
            "THE PLAN'S LITERAL TEST FAILS: the streams are NOT "
            "bit-identical, so N >= 3 STANDS and acceptance stays a FRACTION "
            "[MEASURED].  SEPARATELY MEASURED, and this is the "
            "decision-relevant one: the SCORED TRAJECTORY was "
            + ("EXACTLY REPRODUCED" if traj_identical
               else "NOT reproduced")
            + f" (G identical on {cmp['identical_G']}/{same_turns} turns, D "
            f"on {cmp['identical_D']}, backlog_ema on "
            f"{cmp['identical_backlog_ema']}, B (the P2 addend, the plant's "
            f"own) on {cmp['identical_B_plant']}, the CEN's u/n telemetry on "
            f"{cmp['identical_backlog_rate']}, span COUNTS on "
            f"{cmp['identical_span_counts']}), because the plant reads the "
            "span COUNT and not the prose (count -> the unchecked share -> "
            "B -> A_eff -> D).  "
            "N >= 3 still stands: the span count IS sample-dependent (both 2 "
            "and 3 occur), so divergence is expected to amplify once "
            "B (the P2 addend) is large enough to matter, and this check covers "
            f"only {same_turns} turns of a {TURNS_FULL}-turn horizon")
    # PERSISTED IN THE OUTDIR, one file per invocation, plus a history: byte
    # reproducibility is INTERMITTENT (two runs of this very check disagreed —
    # 1/20 then 20/20 identical), so the answer must carry its BASE RATE over
    # invocations rather than one observation.  That is dmn_llm's own G7
    # ("per-prompt reproducible IN PRACTICE, not contractually"); asserting a
    # single 20/20 as "the seed is deterministic" would be exactly the
    # inference-too-wide-for-the-evidence error.
    hist_dir = os.path.join(args.outdir, "det_check")
    os.makedirs(hist_dir, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%S")
    out = os.path.join(hist_dir, f"det_check-{stamp}.json")
    payload = {"prereg": PREREG_NODE, "turns": k,
               "cell": "route-all/SPEC/tau_S=100",
               "seed_base": seed_base_for(0),
               "model": args.model, "temperature": args.temperature,
               "comparison": cmp,
               "run_status": [r["status"] for r in results],
               "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    _atomic_json(out, payload)
    prior = []
    for fn in sorted(os.listdir(hist_dir)):
        if fn.startswith("det_check-") and fn.endswith(".json"):
            try:
                prior.append({"file": fn,
                              "identical_streams": json.load(
                                  open(os.path.join(hist_dir, fn),
                                       encoding="utf-8"))["comparison"]
                              ["identical_streams"]})
            except Exception:              # noqa: BLE001 — a partial file
                continue
    n_repro = sum(1 for q in prior if q["identical_streams"] == k)
    history = {"runs": prior, "n_runs": len(prior),
               "n_fully_reproducible": n_repro,
               "turns_per_run": k,
               "statement": (
                   f"{n_repro}/{len(prior)} det-check invocations reproduced "
                   f"every one of {k} streams bit-for-bit.  Byte-level "
                   f"reproducibility is therefore INTERMITTENT, not "
                   f"contractual — N >= 3 STANDS and acceptance stays the "
                   f"pre-registered FRACTION.  (MEASURED; consistent with "
                   f"dmn_llm GAPS G7.)")}
    _atomic_json(os.path.join(hist_dir, "det_check_history.json"), history)
    log(f"DET-CHECK: {cmp['identical_streams']}/{same_turns} turns emitted "
        f"bit-identical streams; span counts identical on "
        f"{cmp['identical_span_counts']}, D on {cmp['identical_D']}, "
        f"backlog_ema on {cmp['identical_backlog_ema']}, B on "
        f"{cmp['identical_backlog_rate']} -> {cmp['answer']}")
    log(f"DET-CHECK HISTORY: {history['statement']}")
    log("written to " + out)
    return 0


# ==========================================================================
# THE OFFLINE SELFTEST (no endpoint; every predicate has a falsifying arm)
# ==========================================================================

class _Row:
    """A synthetic Stage2LogRow (the scorer only reads .t and .G)."""

    def __init__(self, t, G):
        self.t, self.G = float(t), float(G)


def _synthetic_log(g_seq, t0=1, t_end=TURNS_FULL):
    """A log whose G is `g_seq(t)` — the criterion's own test fixture."""
    return [_Row(t, g_seq(t)) for t in range(t0, t_end + 1)]


def _fake_run(routing, arm, tau_S, repeat, recovered, G_end=None,
              G_min_post=None, cell_id=None):
    cell_id = cell_id or f"{routing}-{arm}-t{tau_S:g}-s{repeat}"
    return {"cell_id": cell_id,
            "config": {"routing": routing, "arm": arm, "tau_S": float(tau_S),
                       "repeat": repeat, "cell_id": cell_id},
            "result": {"recovered": bool(recovered),
                       "G_end": (G_end if G_end is not None
                                 else (0.9 if recovered else 0.3)),
                       "G_min_post": (G_min_post if G_min_post is not None
                                      else (0.9 if recovered else 0.3)),
                       "n_window": TURNS_FULL - int(WINDOW_T0)}}


def _check(name, cond, msg, results):
    ok = bool(cond)
    results.append((name, ok))
    print(f"[{ts()}] SELFTEST {name}: {'ok' if ok else 'FAIL'} — {msg}",
          flush=True)
    return ok


def mode_selftest(args) -> int:
    results = []
    log("SELFTEST START (offline: no endpoint is contacted, no run starts)")

    # --- 1. the criterion scorer, with a falsifying arm per clause ---------
    flat = _synthetic_log(lambda t: 0.9)
    s = score_recovery(flat)
    _check("criterion/clean", s["recovered"] and s["G_end"] == 0.9
           and s["n_window"] == TURNS_FULL - int(WINDOW_T0) + 1,
           f"a flat G=0.9 log recovers (G_end={s['G_end']}, "
           f"min={s['G_min_post']}, window rows={s['n_window']})", results)

    dip = _synthetic_log(lambda t: 0.4 if t == 1200 else 0.9)
    s = score_recovery(dip)
    _check("criterion/dip-in-window", (not s["recovered"])
           and abs(s["G_min_post"] - 0.4) < 1e-12,
           f"a dip to 0.4 INSIDE the window refuses recovery "
           f"(min={s['G_min_post']}) — the stay clause is live", results)

    pre = _synthetic_log(lambda t: 0.1 if t < WINDOW_T0 else 0.9)
    s = score_recovery(pre)
    _check("criterion/dip-OUTSIDE-window", s["recovered"],
           "a collapse before t=1000 does NOT disqualify: the window is "
           "[1000,1400] on t.u. (the boundary is exercised, not assumed)",
           results)

    low_end = _synthetic_log(lambda t: 0.9 if t < 1390 else 0.45)
    s = score_recovery(low_end)
    _check("criterion/window-includes-the-end", (not s["recovered"])
           and abs(s["G_min_post"] - 0.45) < 1e-12,
           "a 0.45 tail at t=1390..1400 is INSIDE [1000,1400], so the stay "
           "clause alone refuses it: with a run that reaches t=1400 the "
           "G_end clause is IMPLIED by the window clause (an AND with a "
           "redundant term — noted, not silently dropped; the criterion is "
           "used VERBATIM)", results)

    beyond = _synthetic_log(lambda t: 0.9 if t <= 1400 else 0.45, t_end=1450)
    s = score_recovery(beyond)
    _check("criterion/G_end-clause", (not s["recovered"])
           and s["G_min_post"] > BAND1,
           "a log running PAST the horizon recovers the clause's own "
           "falsifier: window min > band but G_end = 0.45 -> not recovered "
           "(this is the only configuration in which the G_end clause binds)",
           results)

    short = [_Row(1, 0.9), _Row(2, 0.9)]
    s = score_recovery(short)
    _check("criterion/empty-window", not s["recovered"] and s["n_window"] == 0,
           "a run that stopped before t0 does NOT recover vacuously",
           results)

    # --- 2. the pilot gate predicates ------------------------------------
    # `B_plant` IS the P2 addend (the plant's own EMA_tauD(c), the gate-3
    # object); `backlog_rate` is the CEN's telemetry and is set to a
    # DIFFERENT profile on purpose, so a gate that read the telemetry
    # instead of the addend cannot pass by coincidence.
    good = [{"turn": i, "t": i, "c": 0.0, "G": 0.8, "D": 0.5, "E": -0.3,
             "S": 0.8, "a": 0.1, "backlog": i, "backlog_ema": 0.5 * i,
             "backlog_rate": 0.9, "B_plant": 0.5 * (i / 150.0),
             "edge_addend": 0.5 * (i / 150.0),
             "A_eff": 0.5 * (i / 150.0),
             "routed": 0, "spans": 1 + (i % 3), "chars": 100 + i,
             "secs": 2.0, "verdicts_V": 1, "verdicts_R": 0, "verdicts_U": 1}
            for i in range(1, 151)]
    g = gate_pilot(good)
    _check("gate/clean-passes", g["status"] == "PASS",
           f"a rising-backlog, varying-supply log passes all three gates "
           f"(1={g['gate1_supply_nonempty_varying']}, "
           f"2={g['gate2_backlog_rises']}, "
           f"3={g['gate3_backlog_ema_builds']}, "
           f"3r(in range)={g['gate3_B_in_model_range']})", results)

    flat_supply = [dict(r, spans=2) for r in good]
    g = gate_pilot(flat_supply)
    _check("gate1/falsifier-constant-supply",
           (not g["gate1_supply_nonempty_varying"]) and g["status"] == "FAIL",
           "a CONSTANT span count fails gate 1 — the varying clause has a "
           "falsifying arm, so it is not a tautology", results)

    empty = [dict(r, spans=0, chars=0) for r in good]
    g = gate_pilot(empty)
    _check("gate1/falsifier-empty-supply",
           not g["gate1_supply_nonempty_varying"],
           "an EMPTY stream fails gate 1", results)

    no_rise = [dict(r, backlog=7) for r in good]
    g = gate_pilot(no_rise)
    _check("gate2/falsifier-flat-backlog",
           (not g["gate2_backlog_rises"]) and g["status"] == "FAIL",
           "a flat backlog fails gate 2 (max == min)", results)

    falling = [dict(r, backlog=200 - i) for i, r in enumerate(good, 1)]
    g = gate_pilot(falling)
    _check("gate2/falsifier-falling-backlog",
           not g["gate2_backlog_rises"],
           "a FALLING backlog fails gate 2 (the direction clause is live)",
           results)

    # GATE 3 IS ON THE P2 ADDEND B, and B has a RANGE.  Three arms:
    # (i) an inert wiring (B == 0) fails the build clause; (ii) a B of 5 —
    # five times the model's own B range — still "builds" but must be
    # FLAGGED out of range (this is the reconciliation's unit check, and
    # the pre-fix count-based wiring is exactly this arm: it built to
    # 35.9); (iii) an out-of-range drive is VISIBLE as D-saturation.
    # (i) the PLANT's B == 0 while the TELEMETRY is high: gate 3 FAILS.
    # THIS IS THE DISCRIMINATING ARM — it is exactly the regime in which
    # a gate on the CEN's u/n would pass while the coupling is inert in
    # the plant (round 1's error, and the pilot's own measured regime).
    zero_b = [dict(r, B_plant=0.0, edge_addend=0.0) for r in good]
    g = gate_pilot(zero_b)
    _check("gate3/falsifier-zero-B",
           (not g["gate3_backlog_ema_builds"]) and g["status"] == "FAIL"
           and g["gate3_B_telemetry_builds"] is True,
           "the PLANT's B == 0 fails gate 3 EVEN THOUGH the CEN telemetry "
           "(u/n EMA 0.9) builds: the gate is on the addend the plant's D "
           "carries, not on the substrate's measurement", results)
    # (ii) the reverse: the plant's B builds, the telemetry is 0 -> gate 3
    # passes and the telemetry gate fails; the two are INDEPENDENT.
    only_plant = [dict(r, B_plant=0.2, edge_addend=0.2, backlog_rate=0.0)
                  for r in good]
    g = gate_pilot(only_plant)
    _check("gate3/plant-B-alone-passes",
           g["gate3_backlog_ema_builds"] and not g["gate3_B_telemetry_builds"],
           "the plant's B alone satisfies gate 3 while the telemetry is 0 — "
           "the two quantities are independent and neither stands in for "
           "the other", results)

    huge_b = [dict(r, B_plant=5.0, edge_addend=5.0, A_eff=5.0)
              for r in good]
    g = gate_pilot(huge_b)
    _check("gate3r/out-of-range-B-flagged",
           g["gate3_backlog_ema_builds"] and not g["gate3_B_in_model_range"],
           "a B of 5.0 (5x the model's own [0,1]) still passes the build "
           "clause and is FLAGGED out of range by gate 3r — the unit check "
           "has a falsifying arm, so it is not a tautology", results)

    # --- 2b. the reported (non-gate) diagnostics, with a falsifier --------
    d = gate_pilot(good)["diagnostics_not_gates"]
    _check("diagnostics/reported-and-non-binding",
           d["cannibalization"]["c_max"] == 0.0
           and d["cannibalization"]["armed_in_pilot"] is False
           and gate_pilot(good)["status"] == "PASS",
           "the switch diagnostic reports c_max=0 / armed=False on a log "
           "with c=0 ALL turns YET the gate still PASSES — the diagnostic "
           "informs the verdict and never silently becomes one", results)

    armed_rows = [dict(r, c=0.0 if r["turn"] < 100 else 1.0) for r in good]
    d2 = gate_pilot(armed_rows)["diagnostics_not_gates"]
    _check("diagnostics/armed-detected",
           d2["cannibalization"]["c_max"] == 1.0
           and d2["cannibalization"]["armed_in_pilot"] is True,
           "the same diagnostic reads armed_in_pilot=True once c arms — it "
           "DISCRIMINATES (not a constant)", results)

    scale_rows = [dict(r, B_plant=1.0, edge_addend=1.0, A_eff=40.0, D=0.99)
                  for r in good]
    d3 = gate_pilot(scale_rows)["diagnostics_not_gates"]
    _check("diagnostics/unit-mismatch-visible",
           d3["coupling_scale"]["A_eff_max_measured"] == 40.0
           and d3["coupling_scale"]["A_eff_in_model_range"] is False
           and d3["coupling_scale"]["D_equilibrium_at_A_eff"] > 0.99,
           "an A_eff of 40 (40x the model's own B range) is shown to imply a "
           "D-equilibrium above 0.99 AND flagged out of the model's range — "
           "the saturation is visible in the report instead of reading as "
           "'B builds, so F2 applies' (this is the PRE-FIX wiring's own "
           "regime, reproduced as a falsifier arm)", results)

    _check("diagnostics/plant-arming-level-is-the-model",
           d["cannibalization"]["plant_switch_floor"] is None
           and d["cannibalization"]["plant_arming_level_is_model"] is True
           and d["cannibalization"]["sn_activation_floor"] == 0.7
           and d["cannibalization"]["stage1_default_floor_still"] == 0.7,
           "the reported arming level is the MODEL's (the Stage-2 plant's "
           "SNConstants.floor is None) while Stage-1's own default keeps its "
           "written-down 0.7 — and the SN's ACTIVATION BELIEF is still "
           "carried (SN_ACTIVATION_FLOOR = 0.7), so the constant is "
           "relocated, not deleted", results)

    # --- 3. the matrix + the acceptance line ------------------------------
    runs = []
    for ro in ROUTINGS:
        for tau in TAU_S_CELLS:
            for i in range(N_DEFAULT):
                runs.append(_fake_run(ro, "OFF", tau, i, True))
    # SPEC fails at 50 and 100 in route-all (2 of 3), clean at 25
    for tau in TAU_S_CELLS:
        for i in range(N_DEFAULT):
            runs.append(_fake_run("route-all", "SPEC", tau, i,
                                  recovered=(tau == 25.0 or i == 2)))
            runs.append(_fake_run("routing-on", "SPEC", tau, i, True))
    m = assemble_matrix(runs)
    a = evaluate_acceptance(m["recovered_count"], N_DEFAULT,
                            m["cells_tau_S"])
    _check("matrix/vectors", m["recovered_count"]["route-all"]["SPEC"] == [3, 1, 1]
           and m["recovered_count"]["route-all"]["OFF"] == [3, 3, 3],
           f"vectors assembled per (routing, arm): route-all SPEC="
           f"{m['recovered_count']['route-all']['SPEC']} OFF="
           f"{m['recovered_count']['route-all']['OFF']}", results)
    _check("acceptance/ACCEPT", a["status"] == "ACCEPT",
           f"OFF clean + SPEC failing 2/3 at 50 and 100 in route-all -> "
           f"ACCEPT ({a['reason']})", results)
    _check("acceptance/per-routing-reading",
           a["per_setting_status"]["route-all"] == "ACCEPT"
           and a["per_setting_status"]["routing-on"] == "FALSIFY",
           "the per-setting readings separate cleanly (route-all ACCEPT, "
           "routing-on FALSIFY: SPEC recovers N/N there)", results)

    # every fixture below DEEP-copies `runs`: the flips are per-fixture and a
    # shallow copy would let one fixture's corruption leak into the next.
    dirty = copy.deepcopy(runs)
    for r in dirty:                     # flip ONE route-all OFF t50 repeat
        if (r["config"]["routing"] == "route-all" and r["config"]["arm"] == "OFF"
                and r["config"]["tau_S"] == 50.0
                and r["config"]["repeat"] == 0):
            r["result"]["recovered"] = False
            r["result"]["G_end"] = 0.3
    m2 = assemble_matrix(dirty)
    a2 = evaluate_acceptance(m2["recovered_count"], N_DEFAULT,
                             m2["cells_tau_S"], n_per_cell=m2["n_per_cell"])
    _check("acceptance/dirty-control-recorded",
           m2["recovered_count"]["route-all"]["OFF"] == [3, 2, 3]
           and m2["n_per_cell"]["route-all"]["OFF"] == [3, 3, 3]
           and not a2["control_clean_by_routing"]["route-all"]
           and a2["status"] == "INCONCLUSIVE"
           and a2["per_setting_status"]["routing-on"] == "FALSIFY",
           f"a control FAILURE is counted per cell, never absorbed: route-all "
           f"OFF counts={m2['recovered_count']['route-all']['OFF']} of n="
           f"{m2['n_per_cell']['route-all']['OFF']} -> the strict reading is "
           f"INCONCLUSIVE (route-all dirty, routing-on clean and FALSIFY); "
           f"BOTH readings are reported", results)

    # REGRESSION (found by this selftest): a cell with MORE runs than the
    # declared N must be judged on its OWN denominator.
    mixed = copy.deepcopy(runs)
    extra = _fake_run("route-all", "OFF", 25.0, 0, False,
                      cell_id="route-all-OFF-t25-s0-extra")
    extra["config"]["repeat"] = 9
    mixed.append(extra)
    m2b = assemble_matrix(mixed)
    a2b = evaluate_acceptance(m2b["recovered_count"], N_DEFAULT,
                              m2b["cells_tau_S"], n_per_cell=m2b["n_per_cell"])
    _check("acceptance/mixed-denominator",
           m2b["n_per_cell"]["route-all"]["OFF"] == [4, 3, 3]
           and not a2b["control_clean_by_routing"]["route-all"],
           f"a cell carrying 4 runs of which 3 recovered is 3/4, NOT clean "
           f"at N=3: n_per_cell={m2b['n_per_cell']['route-all']['OFF']}, "
           f"counts={m2b['recovered_count']['route-all']['OFF']} — the first "
           f"draft read this CLEAN (the global-N denominator bug)", results)

    all_off_dirty = copy.deepcopy(runs)
    for r in all_off_dirty:             # flip one OFF repeat in EVERY cell
        if r["config"]["arm"] == "OFF" and r["config"]["repeat"] == 0:
            r["result"]["recovered"] = False
            r["result"]["G_end"] = 0.3
    m3 = assemble_matrix(all_off_dirty)
    a3 = evaluate_acceptance(m3["recovered_count"], N_DEFAULT,
                             m3["cells_tau_S"], n_per_cell=m3["n_per_cell"])
    _check("acceptance/VOID", a3["status"] == "VOID"
           and not a3["control_clean_all_routings"],
           f"OFF failing in both routing settings -> VOID (the strict "
           f"reading); a dirty control measures the generator "
           f"({a3['reason'][:60]}...)", results)

    spec_clean = []
    for ro in ROUTINGS:
        for arm in ARMS:
            for tau in TAU_S_CELLS:
                for i in range(N_DEFAULT):
                    spec_clean.append(_fake_run(ro, arm, tau, i, True))
    m4 = assemble_matrix(spec_clean)
    a4 = evaluate_acceptance(m4["recovered_count"], N_DEFAULT, m4["cells_tau_S"])
    _check("acceptance/FALSIFY", a4["status"] == "FALSIFY",
           "SPEC recovering N/N everywhere (control clean) -> FALSIFY: the "
           "model->agent mapping fails HERE (equally publishable)", results)

    missing = [r for r in copy.deepcopy(runs)
               if not (r["config"]["routing"] == "route-all"
                                       and r["config"]["arm"] == "SPEC"
                                       and r["config"]["tau_S"] == 50.0)]
    m5 = assemble_matrix(missing)
    _check("matrix/missing-cells-reported",
           m5["per_cell"]["route-all"]["SPEC"]["t50"]["n"] == 0
           and m5["recovered_fraction"]["route-all"]["SPEC"][1] is None,
           "an ABSENT cell is reported as n=0 / fraction None, never as a "
           "zero recovery — absent and failed are different facts", results)

    # --- 4. cell enumeration, seeds, cost ---------------------------------
    cells = plan_cells(N_DEFAULT)
    _check("cells/count", len(cells) == 2 * 2 * 3 * N_DEFAULT
           and len({c["cell_id"] for c in cells}) == len(cells),
           f"{len(cells)} distinct cells = 2 routings x 2 arms x "
           f"{len(TAU_S_CELLS)} tau_S x N={N_DEFAULT}", results)
    seeds = [seed_base_for(r) for r in range(N_DEFAULT)]
    turn_seeds = [[s + t for t in range(1, TURNS_FULL + 1)] for s in seeds]
    _check("seeds/no-alias-across-repeats",
           len(set(sum(turn_seeds, []))) == N_DEFAULT * TURNS_FULL,
           f"per-turn seeds never collide across repeats (bases {seeds}, "
           f"stride {SEED_STRIDE} > horizon {TURNS_FULL})", results)
    cost = project_cost(2.0, 36, TURNS_FULL)
    _check("cost/projection", abs(cost["per_run_hours"] - 1400 * 2 / 3600) < 1e-9
           and abs(cost["total_hours"] - 28.0) < 1e-9,
           f"the plan's ~2 s/turn projects 36 runs to "
           f"{cost['total_hours']:.1f} GPU-hours (matches the plan's 28)",
           results)

    # --- 5. the routing-on arm's WIRING, offline (no endpoint) ------------
    # The pilot is SPEC+route-all by pre-registration, so the routing-on arm
    # would otherwise reach the sweep never having been run end to end.  This
    # exercises its config path and 5 turns of the real loop with a synthetic
    # stream generator, in an ISOLATED criterion/anchor namespace (never the
    # designer's real ~/.cen-routingcrit or ~/.cen-anchors).
    r = _routing_arm_offline_check(args.outdir)
    _check("routing-on/selector-injected-and-criterion-loaded",
           r["selector"] == "PrefixRoutingSelector"
           and r["criterion_dir_isolated"] and r["criterion_version"] >= 1,
           f"a routing-on cell builds a config carrying the injected "
           f"PrefixRoutingSelector and a criterion v{r['criterion_version']} "
           f"published into the RUN's own store ({r['criterion_dir']}) — "
           f"never the designer's", results)
    _check("routing-on/arm-differs-only-in-couple_backlog",
           r["spec_couple_backlog"] is True
           and r["off_couple_backlog"] is False
           and r["spec_selector"] == r["off_selector"],
           "SPEC and OFF cells share the selector and differ ONLY in "
           "couple_backlog — the arm's isolation, asserted structurally",
           results)
    _check("routing-on/loop-runs-the-extractor-and-the-selector",
           r["turns_ran"] == r["turns_requested"]
           and r["spans_per_turn_min"] > 0
           and r["window_windows"] >= 2,
           f"{r['turns_ran']} turns ran in routing-on mode; the EXTRACTOR "
           f"produced spans every turn (>={r['spans_per_turn_min']} per "
           f"turn, {r['spans_total']} total) and a second consolidation "
           f"window was entered (windows={r['window_windows']}) — the arm "
           f"reaches the loop the sweep will use", results)

    # THE FINDING THIS CHECK EXISTS FOR (reported, not a pass/fail on the
    # experiment): the law's OWN number at these windows.  With the
    # G-analogue unsolved the law takes the maximally conservative arm,
    # whose fraction is f_min = 0 when the window ARMS.
    #
    # ROUND 2 CORRECTED THE OBJECT THIS CHECK READS, and the check is now
    # DISCRIMINATING rather than a demonstration: the law's D-analogue is
    # built from the PLANT's own B (Agent.B = EMA_tauD(plant c)), NOT from
    # the generator's measured unchecked share.  This synthetic stream
    # carries one 'orphaned' (UNCHECKABLE, no facts) and one 'done' (seeded
    # -> VERIFIED) per turn, i.e. u/n = 0.5, which under the round-1 wiring
    # drove the D-analogue to ~0.79 > the arming level and zeroed the
    # window (MEASURED then).  With the model's single c restored the CEN's
    # share does not reach the plant at all: over 105 turns the plant's
    # switch is unarmed, its own B is 0.0, the D-analogue stays at its
    # no-drive value, the law never arms, and f stays 1.0 — so the ROUTING-ON
    # arm here routes everything and the plan's hypothesis (ii) is NOT
    # exercised by supply on this scenario.  Both statements are MEASURED;
    # that is why the check asserts the corrected behaviour AND prints the
    # two numbers that discriminate it.
    _check("routing-on/supply-does-not-arm-the-law (round 2)",
           r["f_per_window"]
           and all(w["f"] > 0.0 for w in r["f_per_window"])
           and r["law_armed"] is False
           and r["routed_when_f_zero"] == 0
           and r["routed_when_f_positive"] > 0,
           f"the window seat's applied fraction by window is "
           f"{[(w['windows'], w['f'], w['turns']) for w in r['f_per_window']]} "
           f"-> routed {r['routed_when_f_positive']} spans while f > 0 and "
           f"{r['routed_when_f_zero']} while f == 0.  THE GENERATOR'S SUPPLY "
           f"DOES NOT ARM THE LAW (boundary={r['law_boundary']!r}, "
           f"armed={r['law_armed']}, g_live={r['law_g_live']}, f_min_is_seat="
           f"{r['law_f_min_is_seat']}; arm_floor={r.get('law_arm_floor')}, "
           f"p2_addend={r.get('law_p2_addend')}): the D-analogue is built "
           f"from the PLANT's own B, and a checker's queue is not one of the "
           f"model's channels.  ROUND 1's wiring armed here (u/n = 0.5 -> "
           f"addend 0.44 -> D 0.79 -> f = 0.0) — the plan's hypothesis (ii) "
           f"was a property of that wiring, and is WITHDRAWN [MEASURED]",
           results)

    # --- 6. the refusal paths (arg-level, no run started) ----------------
    ns = argparse.Namespace(outdir=os.path.join(args.outdir, "selftest-refuse"),
                            force_after_failed_pilot=False)
    rc = _refuse_check(ns)
    _check("refusal/no-pilot", rc == 3, "the sweep REFUSES with no pilot.json "
           f"(exit {rc} == 3)", results)
    os.makedirs(ns.outdir, exist_ok=True)
    _atomic_json(os.path.join(ns.outdir, "pilot.json"),
                 {"status": "FAIL", "gate1_supply_nonempty_varying": False,
                  "gate2_backlog_rises": False,
                  "gate3_backlog_ema_builds": False})
    rc = _refuse_check(ns)
    _check("refusal/failed-pilot", rc == 3,
           f"the sweep REFUSES on a FAILED pilot gate (exit {rc} == 3)",
           results)

    # --- 7. THE AGENTEXP2 CAMPAIGN'S SURFACE (item (1)-(10), offline) -----
    _campaign_selftest(args, results)

    bad = [n for n, ok in results if not ok]
    log(f"SELFTEST DONE: {len(results) - len(bad)}/{len(results)} ok"
        + ("" if not bad else f"; FAILED: {bad}"))
    return 0 if not bad else 1


def _camp_row(turn: int, *, coverage: float = 1.0, content_chars: int = 1200,
              trace_chars: int | None = 800, G: float = 0.9,
              drive: float = 0.0, secs: float = 2.0, spans: int = 2,
              candidates: int = 1) -> dict:
    """One synthetic campaign row with EVERY field the campaign's scorers,
    void predicates and gates read.  A fixture that lacks a field would make
    a predicate silently read None, so the fixture is built from the same key
    list the runner writes."""
    return {"turn": int(turn), "t": float(turn), "coverage": float(coverage),
            "coverage_candidates": int(candidates),
            "content_chars": int(content_chars),
            "trace_chars": trace_chars, "G": float(G), "drive": float(drive),
            "D": 0.5, "c": 0.0, "E": -0.3, "S": 0.8, "a": 0.1,
            "backlog": int(turn), "backlog_ema": 0.0, "backlog_rate": 0.0,
            "B_plant": 0.0, "A_eff": 0.1, "routed": 1, "spans": int(spans),
            "claims": int(spans), "commitments": 0,
            "chars": int(content_chars), "secs": float(secs),
            "self_windows": (turn // TAU_S_TURNS) + 1,
            "self_block_chars": 500, "open_commitments": 0, "expired": 0}


def _camp_rows(n: int, *, cov=None, G=None, drive=None, content=None,
               trace=800, spans=None, secs=2.0, candidates=None) -> list:
    """A synthetic log: each of `cov`, `G`, `drive`, `content`, `spans`,
    `candidates` is either a constant or a `f(turn)` callable."""
    def val(spec, t, default):
        if spec is None:
            return default
        return spec(t) if callable(spec) else spec
    return [_camp_row(t, coverage=val(cov, t, 1.0), G=val(G, t, 0.9),
                      drive=val(drive, t, 0.0),
                      content_chars=val(content, t, 1200),
                      trace_chars=(trace(t) if callable(trace) else trace),
                      spans=val(spans, t, 2), secs=val(secs, t, 2.0),
                      candidates=val(candidates, t, 1))
            for t in range(1, int(n) + 1)]


def _fake_camp_run(cell: str, outcome: str | None, *, seed_base: int = 4242,
                   status: str = "OK", void: bool = False,
                   reasons=None, depleted: bool = False,
                   drive_final: float = 0.0, sha: str = "s0") -> dict:
    """A campaign RUN SUMMARY fixture, shaped like `run_one_campaign`'s (the
    acceptance and the assembly are pure functions of this)."""
    plant_rec = outcome in ("HEALTHY", "DISSOCIATION")
    return {
        "cell": cell, "cell_id": f"fake-{cell}-s{seed_base}",
        "status": status, "error": None,
        "config": {"cell": cell, "seed_base": int(seed_base),
                   "couple_backlog": (cell == "C5"),
                   "length_capped": False},
        "result": {"outcome": outcome,
                   "plant": {"recovered": plant_rec},
                   "agent": {"depleted": bool(depleted
                                              or outcome in
                                              ("CO_COLLAPSE",
                                               "DISSOCIATION"))}},
        "invariants": {"drive_final": drive_final,
                       "plant_trajectory_sha16": sha},
        "void": {"void": bool(void),
                 "void_reasons": list(reasons or [])},
    }


def _campaign_selftest(args, results) -> None:
    """THE CAMPAIGN LANE'S OWN OFFLINE PARTS, every one with a FALSIFYING ARM
    (a check nothing can fail is not a check).  No endpoint is contacted and
    nothing outside a tmp dir is written."""
    # -- the coverage mirror, with its window boundary ----------------------
    flat = _camp_rows(300, cov=1.0)
    s = score_coverage(flat)
    _check("camp/mirror-intact", (not s["depleted"])
           and s["coverage_end"] == 1.0 and s["n_last_window"] == TAU_S_TURNS,
           f"a flat coverage=1.0 log is NOT depleted (end {s['coverage_end']}, "
           f"last-window rows {s['n_last_window']})", results)

    falling = _camp_rows(300, cov=lambda t: 1.0 if t < 200 else 0.3)
    s = score_coverage(falling)
    _check("camp/mirror-depleted", s["depleted"]
           and abs(s["coverage_min_last_window"] - 0.3) < 1e-12,
           f"a coverage that falls to 0.3 in the LAST window IS depleted "
           f"(end {s['coverage_end']}, window min "
           f"{s['coverage_min_last_window']})", results)

    early = _camp_rows(300, cov=lambda t: 0.2 if t < 200 else 1.0)
    s = score_coverage(early)
    _check("camp/mirror-window-is-the-LAST-window", not s["depleted"],
           "a recovery out of an EARLY dip (0.2 before turn 200, 1.0 after) "
           "is NOT depleted: the mirror's window is the last "
           f"{TAU_S_TURNS} turns, and this falsifies a whole-run reading",
           results)

    empty = score_coverage([])
    _check("camp/mirror-empty-is-not-depleted",
           empty["depleted"] is False and empty["coverage_end"] is None,
           "an empty row set is NOT depleted and carries None — an absent "
           "measurement is not a zero, and a run that produced no rows cannot "
           "read as a depletion", results)

    # -- the four outcomes --------------------------------------------------
    # (plant_recovered, self_depleted) -> the plan's own symbols
    pairs = {(True, False): "HEALTHY", (True, True): "DISSOCIATION",
             (False, True): "CO_COLLAPSE", (False, False): "UNMODELLED"}
    ok4 = all(four_outcome(p, q) == want for (p, q), want in pairs.items())
    _check("camp/four-outcomes", ok4,
           "the four (plant, self) quadrants map to four DISTINCT named "
           "outcomes (plant+/self+ HEALTHY, plant+/self- DISSOCIATION, "
           "plant-/self- CO_COLLAPSE, plant-/self+ the UNMODELLED quadrant) — "
           "the pair is never collapsed into one bit", results)
    scored = score_run(_camp_rows(TURNS_FULL, cov=0.2, G=0.3))
    _check("camp/score-run-composes", scored["outcome"] == "CO_COLLAPSE"
           and scored["plant"]["recovered"] is False
           and scored["agent"]["depleted"] is True,
           f"score_run composes the two criteria into one quadrant (a "
           f"{TURNS_FULL}-turn log at G=0.3 / coverage=0.2: the plant's own "
           f"window is reached, so the plant criterion can be read at all) "
           f"({scored['outcome_symbol']}: plant_recovered="
           f"{scored['plant']['recovered']}, self_depleted="
           f"{scored['agent']['depleted']})", results)

    # -- the void predicates, each with its falsifier ------------------------
    seat_spec = {"seat": True, "budget": CAMPAIGN_BUDGET}
    no_seat = {"seat": False, "budget": None}
    v = void_predicates(_camp_rows(300, cov=1.0), seat_spec)
    _check("camp/V1-falsifier-no-depletion", v["void"]
           and any("V1" in r for r in v["void_reasons"]),
           f"a seat-ON run whose coverage never falls below 0.5 VOIDs "
           f"(min {v['V1']['coverage_min']}) — and the reason names the "
           f"budget first", results)
    v = void_predicates(_camp_rows(300, cov=lambda t: 0.2), seat_spec)
    _check("camp/V1-does-not-fire-when-depleted", not v["void"],
           "the same log WITH depletion does not void: the predicate "
           "discriminates (it is not a constant)", results)
    v = void_predicates(_camp_rows(300, cov=1.0), no_seat)
    _check("camp/V1-scope-is-seat-on-only",
           (not v["void"]) and v["V1"]["applies"] is False,
           "C1/C4 (seat OFF) carry coverage 1.000 by construction and are NOT "
           "voided: V1's scope is the seat-on conditions (a void rule applied "
           "to the control would void every clean control)", results)
    crowded = _camp_rows(300, cov=0.2,
                         content=lambda t: 0 if t <= 170 else 500)
    v = void_predicates(crowded, seat_spec)
    _check("camp/V2-crowding-voids", v["void"]
           and abs(v["V2"]["empty_content_rate"] - (170 / 300)) < 1e-12
           and any("V2" in r for r in v["void_reasons"]),
           f"a run with content EMPTY in {v['V2']['empty_turns']}/"
           f"{v['V2']['turns']} turns ({v['V2']['empty_content_rate']:.1%}, "
           f"over the {EMPTY_CONTENT_VOID_RATE:.0%} void rate) VOIDs — the "
           f"trace share would read ~1.0 by REGISTER, not by depletion",
           results)
    flagged = _camp_rows(300, cov=0.2,
                         content=lambda t: 0 if t <= 90 else 500)
    v = void_predicates(flagged, seat_spec)
    _check("camp/V2-flag-band", (not v["void"]) and v["V2"]["register_degraded"]
           and abs(v["V2"]["empty_content_rate"] - 0.3) < 1e-12,
           f"a 30% empty-content run is FLAGGED register-degraded and NOT "
           f"voided (rate {v['V2']['empty_content_rate']:.2f}, flag "
           f"{EMPTY_CONTENT_FLAG_RATE}, void {EMPTY_CONTENT_VOID_RATE})",
           results)
    v = void_predicates(_camp_rows(300, cov=0.2), seat_spec)
    _check("camp/V2-clean-register", (not v["void"])
           and v["V2"]["register_degraded"] is False,
           "a fully content-bearing run is neither voided nor flagged — the "
           "V2 arms discriminate", results)
    v = void_predicates([], seat_spec, status="ERROR",
                        error="DMNEndpointError: both streams empty")
    _check("camp/V3-no-trace-void", v["void"] and v["V3"]["transport"]
           and any("V3" in r for r in v["void_reasons"]),
           "a run the transport refused (both streams empty raises in "
           "dmn_llm) VOIDs with the transport named, and zero rows voids too",
           results)

    # -- the plan: six conditions, the C2/C3 pair's SINGLE difference ------
    conds = campaign_conditions()
    plan = campaign_plan()
    c2 = [s for s in plan if s["cell"] == "C2"][0]
    c3 = [s for s in plan if s["cell"] == "C3"][0]
    diff = {k for k in c2 if c2[k] != c3[k]}
    _check("camp/six-conditions-and-their-counts",
           len(conds) == 6 and [c["cell"] for c in conds]
           == list(CAMPAIGN_PHASE_ORDER) and len(plan) == 13
           and len([s for s in plan if s["cell"] == "C5"]) == 2
           and len({s["cell_id"] for s in plan}) == len(plan),
           f"the six pre-registered conditions in phase order "
           f"{[c['cell'] for c in conds]}, expanded to {len(plan)} run specs "
           f"(C5's SPEC/OFF pair included), all cell_ids distinct", results)
    _check("camp/C2-C3-differ-only-in-the-drive",
           diff == {"cell", "cell_id", "label", "role", "expect", "drive"}
           and c2["seed_base"] == c3["seed_base"]
           and c2["seat"] and c3["seat"] and not c2["drive"] and c3["drive"]
           and c2["budget"] == c3["budget"] == CAMPAIGN_BUDGET,
           f"the SEAT-ON/DRIVE-OFF and SEAT-ON/DRIVE-ON cells differ in "
           f"{sorted(diff)} — the cell's own NAME, its label/role/expect, and "
           f"the DRIVE SWITCH (the only configuration difference) — and "
           f"share the seed base {c2['seed_base']}: the attribution pair is "
           f"structurally isolated", results)
    # -- F1: WHAT THE DEFAULT INVOCATION ACTUALLY PLANS ---------------------
    # THE DEPLOYED PATH, not a no-override view the runner never takes: the
    # args come from the real parser and the plan from the same seam
    # `mode_campaign` reads.  (The arm this replaces read `campaign_plan()`
    # with NO override while the runner planned the overridden one — a check
    # that could not fail on the deployed path.)
    tmp_f1 = os.path.join(tempfile.gettempdir(), "agenteXP2_selftest_f1")
    dargs = parse_args(["--campaign", "--outdir", tmp_f1])
    dinv = campaign_invocation_plan(dargs)
    dinv_counts = {c: sum(1 for s in dinv if s["cell"] == c)
                   for c in CAMPAIGN_PHASE_ORDER}
    dinv_turns = {s["cell"]: s["turns"] for s in dinv}
    dpre = campaign_preregistration(dargs, dinv)
    _check("camp/F1-default-invocation-plans-the-design-plan",
           len(dinv) == 13
           and dinv_counts == {"C1": 3, "C2": 3, "C3": 3, "C4": 1, "C5": 2,
                               "C6": 1}
           and len(campaign_plan()) == len(dinv)
           and dinv_turns == {"C1": TURNS_FULL, "C2": TURNS_FULL,
                              "C3": TURNS_FULL, "C4": TURNS_FULL,
                              "C5": TURNS_FULL, "C6": CONTROL_CAP_TURNS}
           and dpre["n_runs_planned"] == 13 and dpre["n_design_specs"] == 13
           and "n" not in dpre["overrides"]
           and "turns" not in dpre["overrides"],
           f"the DEFAULT invocation (the real parser + campaign_invocation_"
           f"plan) plans {len(dinv)} specs {dinv_counts} at turns "
           f"{dinv_turns} — the design plan's OWN per-condition N (C4 1, C5 1 "
           f"per arm = 2 specs, C6 1) and horizons (C6 at its "
           f"CONTROL_CAP_TURNS={CONTROL_CAP_TURNS} cap, C1-C5 at "
           f"{TURNS_FULL}), with neither --n nor --turns recorded as an "
           f"override", results)
    # the OTHER side of the same door: an EXPLICIT --n is still an override,
    # and it is recorded (a default and an override must not be confusable)
    oargs = parse_args(["--campaign", "--outdir", tmp_f1, "--n",
                        str(N_DEFAULT)])
    oinv = campaign_invocation_plan(oargs)
    o_counts = {c: sum(1 for s in oinv if s["cell"] == c)
                for c in CAMPAIGN_PHASE_ORDER}
    opre = campaign_preregistration(oargs, oinv)
    _check("camp/F1-explicit--n-overrides-every-condition-and-is-recorded",
           len(oinv) == 21 and o_counts == {"C1": 3, "C2": 3, "C3": 3, "C4": 3,
                                            "C5": 6, "C6": 3}
           and opre["overrides"]["n"]["used"] == N_DEFAULT
           and opre["overrides"]["planned_specs"]["n_specs"] == 21
           and opre["overrides"]["planned_specs"]["design_n_specs"] == 13
           and len(oinv) != len(dinv),
           f"an EXPLICIT --n {N_DEFAULT} is an override: it expands EVERY "
           f"condition to {o_counts} = {len(oinv)} specs and campaign.json "
           f"records it (overrides.n.used={opre['overrides']['n']['used']}, "
           f"planned {opre['overrides']['planned_specs']['n_specs']} of the "
           f"design plan's {opre['overrides']['planned_specs']['design_n_specs']})"
           f" — the user's own expansion is visible, the default is not an "
           f"expansion", results)
    # C6's cap is NOT overridable upward (the precondition negative does not
    # buy the full horizon) ...
    targs = parse_args(["--campaign", "--outdir", tmp_f1, "--turns", "700"])
    tinv = campaign_invocation_plan(targs)
    tpre = campaign_preregistration(targs, tinv)
    _check("camp/F1-C6s-declared-cap-survives-a--turns-override",
           {s["turns"] for s in tinv if s["cell"] == "C6"}
           == {CONTROL_CAP_TURNS}
           and {s["turns"] for s in tinv if s["cell"] == "C1"} == {700}
           and all(s["length_capped"] for s in tinv if s["cell"] == "C6")
           and tpre["overrides"]["turns"]["used"] == 700
           and len(tinv) == 13,
           f"--turns 700 moves every full-length cell to "
           f"{sorted({s['turns'] for s in tinv if s['cell'] == 'C1'})} turns, "
           f"and C6 stays at its declared "
           f"{sorted({s['turns'] for s in tinv if s['cell'] == 'C6'})}-turn cap "
           f"(recorded under overrides.turns, {len(tinv)} specs)", results)
    # ... and a C6 run AT its cap cannot be read as a recovery either way.
    c6s = [s for s in dinv if s["cell"] == "C6"]
    c6run = _fake_camp_run("C6", "CO_COLLAPSE", seed_base=c6s[0]["seed_base"],
                           depleted=True)
    # the two fields `run_one_campaign` writes for a capped run
    c6run["config"]["length_capped"] = True
    c6run["recovery_scored"] = False
    asm = assemble_campaign([c6run])
    b6 = asm["cells"]["C6"]
    _check("camp/F1-C6-at-its-cap-is-excluded-from-recovery-scoring",
           len(c6s) == 1 and c6s[0]["turns"] == CONTROL_CAP_TURNS
           and c6s[0]["length_capped"]
           and c6s[0]["turns"] < WINDOW_T0 + TAU_S_TURNS
           and b6["recovery_scored"] is False and b6["n"] == 0
           and b6["n_length_capped"] == 1 and b6["outcomes"] == {}
           and b6["fraction"] == {},
           f"C6 plans ONE spec at its declared cap ({c6s[0]['turns']} turns, "
           f"below the criterion window's start+window "
           f"{int(WINDOW_T0 + TAU_S_TURNS)}): its run lands in "
           f"n_length_capped={b6['n_length_capped']} with n={b6['n']}, "
           f"outcomes={b6['outcomes']} — excluded from recovery scoring, so it "
           f"reads neither a recovery nor a non-recovery", results)
    # the cost projection sums each spec's OWN horizon (the capped control is
    # not priced as a full-length run)
    cheap = campaign_cost_projection(29.0, dinv)
    over = project_cost(29.0, len(dinv), TURNS_FULL)
    _check("camp/F1-cost-projection-sums-each-specs-own-horizon",
           cheap["n_specs"] == 13
           and cheap["total_turns"] == 12 * TURNS_FULL + CONTROL_CAP_TURNS
           and abs(cheap["total_hours"]
                   - 29.0 * cheap["total_turns"] / 3600.0) < 1e-9
           and cheap["n_length_capped"] == 1
           and cheap["turns_length_capped"] == CONTROL_CAP_TURNS
           and cheap["turns_per_full_run"] == TURNS_FULL
           and cheap["total_hours"] < over["total_hours"],
           f"the design plan is {cheap['total_turns']} turns over "
           f"{cheap['n_specs']} specs = {cheap['total_hours']:.1f} GPU-h at "
           f"29.0 s/turn, where the old n_runs x {TURNS_FULL} form reads "
           f"{over['total_hours']:.1f} h: C6's {CONTROL_CAP_TURNS}-turn cap is "
           f"priced as {CONTROL_CAP_TURNS}, not {TURNS_FULL}", results)
    # -- F2: the forced pilot gate is IN THE RECORD ------------------------
    fargs = parse_args(["--campaign", "--outdir", tmp_f1,
                        "--force-after-failed-pilot"])
    fpre = campaign_preregistration(fargs, campaign_invocation_plan(fargs))
    _check("camp/F2-force-after-failed-pilot-is-recorded",
           campaign_forced_provenance(fargs)["force_after_failed_pilot"] is True
           and campaign_forced_provenance(fargs)["pilot_gate"] == "OVERRIDDEN"
           and fpre["forced"]["force_after_failed_pilot"] is True
           and fpre["forced"]["pilot_gate"] == "OVERRIDDEN"
           and fpre["overrides"]["force_after_failed_pilot"]["used"] is True
           and dpre["forced"]["force_after_failed_pilot"] is False
           and dpre["forced"]["pilot_gate"] == "enforced"
           and "force_after_failed_pilot" not in dpre["overrides"],
           f"a forced invocation records the flag in campaign.json "
           f"(forced.force_after_failed_pilot="
           f"{fpre['forced']['force_after_failed_pilot']}, and under overrides), "
           f"the run provenance helper says "
           f"{campaign_forced_provenance(fargs)['pilot_gate']}, and an "
           f"ungated invocation records "
           f"{dpre['forced']['pilot_gate']} — a forced verdict can no longer "
           f"be mistaken for a gated one", results)
    c6 = [s for s in plan if s["cell"] == "C6"][0]
    c1 = [s for s in plan if s["cell"] == "C1"][0]
    _check("camp/C6-capped-and-generate/C1-seat-off",
           c6["api"] == dmn_llm.GENERATE and c6["length_capped"]
           and c6["turns"] == CONTROL_CAP_TURNS
           and (not c1["seat"]) and (not c1["drive"])
           and c1["budget"] is None,
           f"C6 runs the gemma arm through the GENERATE path, length-capped at "
           f"{c6['turns']} turns; C1 is the seat-off/drive-off control on the "
           f"default budget — the two controls are structurally what the plan "
           f"says", results)

    # -- the acceptance predicate, with a matrix that must NOT read clean ---
    accept_runs = ([_fake_camp_run("C1", "HEALTHY", seed_base=100 + i)
                    for i in range(3)]
                   + [_fake_camp_run("C2", "DISSOCIATION", seed_base=100 + i)
                      for i in range(3)]
                   + [_fake_camp_run("C3", "CO_COLLAPSE", seed_base=100 + i)
                      for i in range(3)])
    a = evaluate_campaign(assemble_campaign(accept_runs),
                          pilot_status="PASS")
    _check("camp/acceptance-ACCEPT", a["status"] == "ACCEPT",
           f"a matrix with C1 clean 3/3, C2 dissociation 3/3 and C3 "
           f"co-collapse 3/3 (pilot PASS) reads ACCEPT — the paper-2 "
           f"conjunction", results)
    mixed = ([_fake_camp_run("C1", "HEALTHY", seed_base=100 + i)
              for i in range(3)]
             + [_fake_camp_run("C2", "DISSOCIATION", seed_base=100)
                ] + [_fake_camp_run("C2", "HEALTHY", seed_base=101 + i)
                     for i in range(2)]
             + [_fake_camp_run("C3", "CO_COLLAPSE", seed_base=100)]
             + [_fake_camp_run("C3", "HEALTHY", seed_base=101 + i)
                for i in range(2)])
    am = evaluate_campaign(assemble_campaign(mixed), pilot_status="PASS")
    _check("camp/acceptance-mixed-does-NOT-read-clean",
           am["status"] == "INCONCLUSIVE"
           and not am["conditions"]["C2_dissociation_at_least_2of3"]
           and not am["conditions"]["C3_cocollapse_at_least_2of3"],
           f"a SPLIT matrix (C2 1/3 dissociation, C3 1/3 co-collapse) reads "
           f"{am['status']} — the predicate is not satisfiable by a mixed "
           f"matrix, which is the tautology test", results)
    fals = ([_fake_camp_run("C1", "HEALTHY", seed_base=100 + i)
             for i in range(3)]
            + [_fake_camp_run("C2", "DISSOCIATION", seed_base=100 + i)
               for i in range(3)]
            + [_fake_camp_run("C3", "DISSOCIATION", seed_base=100 + i,
                              depleted=True, drive_final=0.7)
               for i in range(3)])
    af = evaluate_campaign(assemble_campaign(fals), pilot_status="PASS")
    _check("camp/acceptance-FALSIFY", af["status"] == "FALSIFY"
           and af["c3_depleted_in_every_seed"] and af["c3_drive_live"],
           f"C3 reading (plant+, self-) in 3/3 with depletion and a live "
           f"drive reads FALSIFY — the a_hold mapping failing in the agent is "
           f"an outcome the predicate must be able to reach", results)
    v4 = ([_fake_camp_run("C1", "HEALTHY", seed_base=100),
           _fake_camp_run("C1", "HEALTHY", seed_base=101),
           _fake_camp_run("C1", "DISSOCIATION", seed_base=102)] + accept_runs)
    a4 = evaluate_campaign(assemble_campaign(v4), pilot_status="PASS")
    _check("camp/acceptance-VOID-on-C1", a4["status"] == "VOID"
           and "V4" in a4["reason"],
           "one dirty C1 seed VOIDs the campaign (V4: the clean control is "
           "the scenario baseline, exp22's rule)", results)
    no_pilot = evaluate_campaign(assemble_campaign(accept_runs),
                                 pilot_status="FAIL")
    _check("camp/acceptance-needs-the-pilot",
           no_pilot["status"] != "ACCEPT"
           and no_pilot["conditions"]["pilot_gates_held"] is False,
           "the same clean matrix does NOT read ACCEPT when the pilot gate "
           "did not hold — the conjunction has teeth on every term", results)
    v5runs = [r for r in accept_runs] + [
        _fake_camp_run("C4", "HEALTHY", seed_base=100, sha="other")]
    av5 = evaluate_campaign(assemble_campaign(v5runs), pilot_status="PASS")
    _check("camp/V5-wiring-void", av5["status"] == "VOID"
           and "V5" in av5["reason"],
           "a C4 whose plant trajectory hash DIFFERS from C1's on the shared "
           "seed VOIDs the drive pair (V5, the schedule-seating check)", results)
    v5ok = [r for r in accept_runs] + [
        _fake_camp_run("C4", "HEALTHY", seed_base=100, sha="s0")]
    av5b = evaluate_campaign(assemble_campaign(v5ok), pilot_status="PASS")
    _check("camp/V5-passes-when-identical",
           assemble_campaign(v5ok)["V5_wiring"][
               "plant_trajectory_identical"] is True
           and av5b["status"] != "VOID",
           "with C4's hash equal to C1's the wiring check PASSES — V5 is a "
           "predicate, not a constant", results)
    capped_run = _fake_camp_run("C6", "HEALTHY", seed_base=100)
    capped_run["config"]["length_capped"] = True
    capped_run["recovery_scored"] = False
    agg_c6 = assemble_campaign([capped_run])
    _check("camp/length-capped-runs-are-excluded",
           agg_c6["cells"]["C6"]["n_runs_total"] == 1
           and agg_c6["cells"]["C6"]["n_length_capped"] == 1
           and agg_c6["cells"]["C6"]["n"] == 0
           and agg_c6["cells"]["C6"]["outcomes"] == {},
           "C6 (and any run short of the criterion window) appears in the "
           "cell's run count but NOT in its outcome vector: a truncated run "
           "is EXCLUDED from recovery scoring, never reported as a "
           "non-recovery", results)
    short_plan = campaign_plan(["C1"], n=1, turns=250)
    _check("camp/--turns-override-marks-the-run-length-capped",
           short_plan[0]["length_capped"] is True
           and campaign_plan(["C1"], n=1, turns=TURNS_FULL)[0]["length_capped"]
           is False,
           "a horizon shorter than the pre-registered 1400 marks EVERY cell "
           "length-capped (the same rule as C6), so a truncated campaign "
           "cannot read as a plant failure — the override is a measurement "
           "gap, not a result", results)
    absent = evaluate_campaign(assemble_campaign(
        [_fake_camp_run("C2", "DISSOCIATION", seed_base=100)]))
    _check("camp/absent-cell-is-not-a-zero",
           absent["status"] == "INCOMPLETE"
           and assemble_campaign([])["cells"]["C1"]["n"] == 0
           and assemble_campaign([])["cells"]["C1"]["fraction"] == {},
           "an unrun C1 leaves the campaign INCOMPLETE (never ACCEPT on an "
           "absent control) and an absent cell appears with n=0", results)

    # -- B1: A VOID IS A GATE ON WHAT COUNTS, NOT A NOTE BESIDE IT ----------
    # THE REVIEW'S OWN CONSTRUCTION: three C3 runs, every one V2 CROWDED (the
    # register saturates the inward share), each carrying a scored
    # CO_COLLAPSE quadrant.  Pre-fix this read ACCEPT with void_rate 1.0 in
    # the same block; the void must now be excluded from the tally.
    voided = copy.deepcopy(accept_runs)
    for r in voided:
        if r["cell"] == "C3":
            r["void"] = {"void": True,
                         "void_reasons": ["V2 CROWDING: content EMPTY in "
                                          "60% of turns — the register, not "
                                          "the self"]}
    agg_v = assemble_campaign(voided)
    a_v = evaluate_campaign(agg_v, pilot_status="PASS")
    _check("camp/B1-voided-runs-are-excluded-from-the-tally",
           agg_v["cells"]["C3"]["n"] == 0
           and agg_v["cells"]["C3"]["n_voided"] == 3
           and agg_v["cells"]["C3"]["outcomes"] == {}
           and agg_v["cells"]["C3"]["void_rate"] == 1.0
           and len(agg_v["cells"]["C3"]["voids"]) == 3
           and a_v["status"] == "INCOMPLETE"
           and a_v["conditions"]["C3_cocollapse_at_least_2of3"] is False
           and a_v["excluded_from_the_tally"]["C3"]["n_voided"] == 3,
           f"three C3 runs ALL VOID on V2 crowding (each with a scored "
           f"CO_COLLAPSE quadrant) leave C3 at n=0, n_voided=3, "
           f"void_rate={agg_v['cells']['C3']['void_rate']} and NO outcome, "
           f"and the campaign reads {a_v['status']} instead of ACCEPT — while "
           f"the SAME runs un-voided read ACCEPT (the arm above): the "
           f"exclusion, not the data, is what changed", results)
    dead = copy.deepcopy(accept_runs)
    for r in dead:
        if r["cell"] == "C3":
            r["status"] = "ERROR"
            r["error"] = "RuntimeError: died at turn 1200 of 1400"
            r["void"] = {"void": True,
                         "void_reasons": ["V3 NO-TRACE: the run ended "
                                          "status=ERROR after 1200 rows"]}
    agg_d = assemble_campaign(dead)
    a_d = evaluate_campaign(agg_d, pilot_status="PASS")
    _check("camp/B1-dead-runs-partial-rows-are-excluded",
           agg_d["cells"]["C3"]["n"] == 0
           and agg_d["cells"]["C3"]["n_voided"] == 3
           and agg_d["cells"]["C3"]["outcomes"] == {}
           and a_d["status"] == "INCOMPLETE",
           "three runs that DIED at turn 1200 of 1400 (V3, each still carrying "
           "a scored CO_COLLAPSE off its partial log) are counted in "
           "n_voided and NOT in the outcomes: a dead run's partial quadrant "
           "cannot satisfy the acceptance", results)

    # B1's OWN SIDE-EFFECT, CLOSED: `c3_drive_live` is read off C3's
    # `drive_final`, and the tally fix STOPS a voided run from diluting the
    # rate — so with the tally half alone, a voided C3 run's live drive could
    # fire FALSIFY on evidence the three counted runs do not have.
    live_voided = copy.deepcopy(accept_runs)
    for r in live_voided:
        if r["cell"] == "C3":
            r["result"] = {"outcome": "DISSOCIATION",
                           "plant": {"recovered": True},
                           "agent": {"depleted": True}}
            r["invariants"] = {"drive_final": 0.0,
                               "plant_trajectory_sha16": "s0"}
    ghost = _fake_camp_run("C3", "DISSOCIATION", seed_base=200, depleted=True,
                           drive_final=0.7)
    ghost["void"] = {"void": True,
                     "void_reasons": ["V2 CROWDING: content EMPTY in 70% of "
                                      "turns"]}
    live_voided.append(ghost)
    agg_lv = assemble_campaign(live_voided)
    a_lv = evaluate_campaign(agg_lv, pilot_status="PASS")
    _check("camp/B1-a-voided-runs-drive-cannot-fire-FALSIFY",
           agg_lv["cells"]["C3"]["invariants"]["drive_final"] == [0.0, 0.0, 0.0]
           and agg_lv["cells"]["C3"]["invariants_excluded"]["drive_final"]
           == [0.7]
           and a_lv["c3_drive_live"] is False
           and a_lv["status"] == "INCONCLUSIVE"
           and a_lv["status"] != "FALSIFY"
           and a_lv["conditions"]["n_prereg_met"] is True
           and a_lv["c3_depleted_in_every_seed"] is True,
           "three counted C3 runs reading (plant+, self-) with depletion but a "
           "DEAD drive (drive_final 0.0), plus one VOIDED C3 run whose drive "
           "moved (0.7): the voided run's drive stays out of `invariants` (it "
           "is reported under `invariants_excluded`) so c3_drive_live is "
           "False and the verdict is INCONCLUSIVE — with the tally half alone "
           "the rate is no longer diluted and this read FALSIFY on a drive no "
           "counted run had", results)

    # -- B2: THE PRE-REGISTERED N IS REQUIRED BEFORE ANY VERDICT -------------
    n1_runs = [_fake_camp_run("C1", "HEALTHY", seed_base=100),
               _fake_camp_run("C2", "DISSOCIATION", seed_base=100),
               _fake_camp_run("C3", "CO_COLLAPSE", seed_base=100),
               _fake_camp_run("C4", "HEALTHY", seed_base=100, sha="s0")]
    agg_n1 = assemble_campaign(n1_runs)
    a_n1 = evaluate_campaign(agg_n1, pilot_status="PASS")
    _check("camp/B2-pre-registered-N-is-required-before-any-verdict",
           a_n1["status"] == "INCOMPLETE"
           and a_n1["conditions"]["n_prereg_met"] is False
           and a_n1["conditions"]["C1_healthy_all"] is True
           and a_n1["conditions"]["C2_dissociation_at_least_2of3"] is True
           and a_n1["conditions"]["C3_cocollapse_at_least_2of3"] is True
           and a_n1["n_prereg"]["C3"] == {"n": 1, "required": CAMPAIGN_N,
                                          "met": False},
           "ONE seed per cell satisfies every >= 2/3 conjunct (C1 1/1 clean, "
           "C2 1/1 dissociation, C3 1/1 co-collapse) and the verdict is "
           f"{a_n1['status']} anyway: the acceptance is read AT THE "
           f"PRE-REGISTERED N={CAMPAIGN_N}, so a campaign that crashed after "
           f"seed 1 (campaign.json is rewritten after every cell) cannot leave "
           f"an ACCEPT on disk", results)
    f_n1 = [_fake_camp_run("C1", "HEALTHY", seed_base=100),
            _fake_camp_run("C4", "HEALTHY", seed_base=100, sha="s0"),
            _fake_camp_run("C2", "DISSOCIATION", seed_base=100),
            _fake_camp_run("C3", "DISSOCIATION", seed_base=100, depleted=True,
                           drive_final=0.7)]
    a_fn1 = evaluate_campaign(assemble_campaign(f_n1), pilot_status="PASS")
    _check("camp/B2-falsify-also-needs-the-N",
           a_fn1["status"] == "INCOMPLETE"
           and a_fn1["c3_depleted_in_every_seed"] is True
           and a_fn1["c3_drive_live"] is True
           and a_fn1["conditions"]["n_prereg_met"] is False,
           "a single C3 seed reading (plant+, self-) WITH depletion and a live "
           "drive would have read FALSIFY at n=1 (MEASURED pre-fix) — a claim "
           f"as strong as ACCEPT needs the same N, so it reads "
           f"{a_fn1['status']}: every seed means EVERY PRE-REGISTERED SEED",
           results)
    # C5's OWN DENOMINATOR (its clause is "fails in >= 2/N")
    def _c5_run(failed, seed):
        r = _fake_camp_run("C5", "CO_COLLAPSE" if failed else "HEALTHY",
                           seed_base=seed)
        r["config"]["couple_backlog"] = failed
        return r
    c5_n1 = evaluate_c5([_c5_run(True, 100), _c5_run(False, 100)])
    c5_n2 = evaluate_c5([_c5_run(True, 100), _c5_run(True, 101),
                         _c5_run(False, 100), _c5_run(False, 101)])
    _check("camp/B2-c5-reports-its-own-denominator",
           c5_n1["status"] == "NOT EVALUABLE" and c5_n1["evaluable"] is False
           and c5_n2["status"] == "HOLDS" and c5_n2["evaluable"] is True,
           f"C5's predicate is 'SPEC fails in >= 2/N': at n_spec="
           f"{c5_n1['spec_n']} that clause cannot be met (its threshold is "
           f"n-2 = 0), so it reads {c5_n1['status']} rather than the HOLDS it "
           f"used to read off a single failing run; at n_spec="
           f"{c5_n2['spec_n']} with both SPEC runs failing it reads "
           f"{c5_n2['status']} — the predicate is a predicate, not a "
           f"constant", results)

    # -- S1: THE VOID RE-RUN's SEED BASE IS OUTSIDE THE REPEAT RANGE --------
    rep_bases = {seed_base_for(r) for r in range(CAMPAIGN_N)}
    rerun_bases = {_with_attempt(campaign_plan(["C3"], n=CAMPAIGN_N,
                                               turns=TURNS_FULL)[0], a)
                   ["seed_base"] for a in (1, 2)}
    _check("camp/S1-void-rerun-seed-base-cannot-collide-with-a-repeat",
           rerun_bases.isdisjoint(rep_bases)
           and rerun_bases == {SEED_BASE_DEFAULT + (CAMPAIGN_N + 1)
                               * SEED_STRIDE,
                               SEED_BASE_DEFAULT + (CAMPAIGN_N + 2)
                               * SEED_STRIDE},
           f"the void re-run's seed bases {sorted(rerun_bases)} lie OUTSIDE "
           f"the repeats' range {sorted(rep_bases)}: MEASURED pre-fix, "
           f"attempt 1 drew {seed_base_for(1)} — exactly rep-1's base, so the "
           f"re-run shared every per-turn seed and the store history with a "
           f"repeat (the convention the protocol names)", results)

    # -- S2: A RUN THAT DID NOT FINISH ITS HORIZON HAS NO QUADRANT ----------
    whole = score_run(_camp_rows(TURNS_FULL, cov=0.2, G=0.3))
    part = partialize_result(whole, status="ERROR", rows=600, turns=TURNS_FULL)
    kept = partialize_result(whole, status="OK", rows=TURNS_FULL,
                             turns=TURNS_FULL)
    _check("camp/S2-partial-runs-carry-no-counted-quadrant",
           whole["outcome"] == "CO_COLLAPSE"
           and part["outcome"] is None
           and part["partial"] is True
           and part["quadrant_measured_but_NOT_counted"] == "CO_COLLAPSE"
           and part["rows_measured"] == 600
           and part["rows_expected"] == TURNS_FULL
           and kept["outcome"] == "CO_COLLAPSE"
           and not kept.get("partial"),
           "a run that died at turn 600 of 1400 (MEASURED pre-fix: its own "
           "run JSON read outcome=CO_COLLAPSE and recovery_scored=True) now "
           "carries outcome=None with the measured quadrant preserved under "
           "quadrant_measured_but_NOT_counted, while a completed run is "
           "untouched — a truncated log is data, not a verdict", results)

    # -- S3: EVERY CELL RUNS THE CAMPAIGN'S CONFIGURATION (C6 included) -----
    c6_spec = campaign_plan(["C6"], n=1)[0]
    c3_spec = campaign_plan(["C3"], n=1)[0]
    cfg_c6, gen_c6 = (campaign_cell_config(args, c6_spec),
                      campaign_generator(args, c6_spec))
    cfg_c3, gen_c3 = (campaign_cell_config(args, c3_spec),
                      campaign_generator(args, c3_spec))
    _check("camp/S3-c6-runs-the-recorded-configuration",
           cfg_c6["num_predict"] == CAMPAIGN_NUM_PREDICT
           and gen_c6.num_predict == CAMPAIGN_NUM_PREDICT
           and cfg_c6["num_ctx"] == CAMPAIGN_NUM_CTX
           and gen_c6.num_ctx == CAMPAIGN_NUM_CTX
           and cfg_c6["model"] == gen_c6.model
           and cfg_c6["endpoint"] == gen_c6._url()
           and cfg_c3["model"] == gen_c3.model
           and cfg_c3["endpoint"] == gen_c3._url()
           and gen_c3.num_predict == CAMPAIGN_NUM_PREDICT
           and cfg_c6["api"] == dmn_llm.GENERATE,
           f"C6 (gemma, /api/generate) is built at num_predict="
           f"{gen_c6.num_predict}/num_ctx={gen_c6.num_ctx} — the campaign's "
           f"recorded {CAMPAIGN_NUM_PREDICT}/{CAMPAIGN_NUM_CTX}, where "
           f"MEASURED pre-fix it ran at dmn_llm's own 800/4096 while "
           f"campaign.json recorded the campaign numbers; and "
           f"campaign_cell_config matches the constructed generator on model "
           f"and endpoint for BOTH transports, so the identity cannot describe "
           f"a configuration other than the one that runs", results)

    # -- B1: THE FIXED FRAMING IS ON IN EVERY CELL, AND OFF EVERYWHERE ELSE --
    # The brevity instruction is a CONFIG FIX for a measured defect (the
    # campaign prompt induced runaway reasoning on the remote arm: half the
    # turns hit the num_predict cap with content=0 — no supply AND an inward
    # share saturated at 1.0 by the BUDGET, `handoff-selfreg-brevity-fix`).
    # It is part of the FIXED INSTRUMENT, so it must ride EVERY cell — the
    # seat-off bystander included — or C1/C2/C4 would differ from C3/C5 in
    # the prompt framing as well as in the seat and the drive.  The check is
    # on the generator the campaign BUILDS, and on the bytes it would post
    # (only the transport seam faked), because the flag existing in dmn_llm
    # is not the same fact as the campaign using it.
    c1_spec = campaign_plan(["C1"], n=1)[0]
    gen_c1 = campaign_generator(args, c1_spec)
    _check("camp/B1-the-brevity-instruction-is-on-in-every-cell",
           gen_c1.brief is True and gen_c3.brief is True
           and gen_c6.brief is True
           and make_generator(args, 4242).brief is False
           and make_generator(args, 4242, brief=True).brief is True,
           f"every campaign cell's generator — C1 (seat OFF, the bystander), "
           f"C3 (the experiment) and C6 (the generate transport) — carries "
           f"brief=True, while a generator built the way every pre-campaign "
           f"caller builds one is OFF ({make_generator(args, 4242).brief}): "
           f"the framing is constant across the cells and the default is "
           f"unchanged", results)
    # …AND THE FRAMING IS IN THE IDENTITY, not merely in the call: the
    # identity is what decides whether a run file may be REUSED (S5), and
    # rows taken under one framing are not a measurement of the other.
    cfg_c1 = campaign_cell_config(args, c1_spec)
    _check("camp/B1-the-identity-binds-the-framing",
           cfg_c1["brief"] is True and cfg_c3["brief"] is True
           and cfg_c6["brief"] is True
           and bind_campaign_identity(c3_spec, args)["identity_tag"]
           == campaign_identity_tag(cfg_c3)
           and campaign_identity_tag({**cfg_c3, "brief": True})
           != campaign_identity_tag({**cfg_c3, "brief": False}),
           f"every cell's recorded identity carries brief=True and the tag "
           f"is the digest of that config ({cfg_c3['brief']}); flipping the "
           f"framing alone yields a DIFFERENT tag, so a resume cannot serve "
           f"pre-brief rows as this measurement", results)
    _sent: dict = {}
    gen_c3._post = lambda body: (_sent.update(body),
                                 '{"message": {"thinking": "t", '
                                 '"content": "an outward line"}}')[1]
    gen_c3(3, {})
    _wired = _sent["messages"][0]["content"]
    _check("camp/B1-the-instruction-is-in-the-posted-body",
           dmn_llm.BRIEF_INSTRUCTION in _wired
           and _wired.endswith("\n\n" + dmn_llm.BRIEF_INSTRUCTION)
           and [m["role"] for m in _sent["messages"]] == ["user"],
           f"…and it is in the bytes the campaign actually posts: the "
           f"instruction ends the single USER message "
           f"({len(_wired)} chars, roles {[m['role'] for m in _sent['messages']]}) "
           f"— never a system message, which MEASURED would disable this "
           f"model's reasoning channel (thinking=0) and with it the "
           f"inward/outward split every seat reads", results)

    # -- S5: THE RUN IDENTITY IS THE WHOLE CONFIGURATION --------------------
    def _bound(**over):
        a = copy.copy(args)
        for k, v in over.items():
            setattr(a, k, v)
        return campaign_plan(["C3"], n=1, turns=TURNS_FULL, args=a)[0]

    ids = {name: _bound(**over)["cell_id"] for name, over in {
        "base": {}, "num_predict": {"num_predict": 9000},
        "num_ctx": {"num_ctx": 16384}, "chat_model": {"chat_model": "other:7b"},
        "chat_endpoint": {"chat_endpoint": "http://10.20.30.4:11434/api/chat"},
        "engine": {"engine": "real"}, "temperature": {"temperature": 0.7},
    }.items()}
    budget_ids = {campaign_identity_tag(bind_campaign_identity(
        dict(c3_spec, budget=b), args)["identity"]) for b in (3, CAMPAIGN_BUDGET,
                                                             12)}
    id_base = ids["base"]
    id_prefix = "agenteXP2-C3-cOFF-t1400-s4242"
    _check("camp/S5-the-run-identity-binds-the-configuration",
           len(set(ids.values())) == len(ids)
           and len(budget_ids) == 3
           and _bound()["cell_id"] == id_base
           and all(v.rsplit("-h", 1)[0] == id_prefix for v in ids.values())
           and all(len(v.rsplit("-h", 1)[1]) == 16 for v in ids.values()),
           f"seven configurations of the SAME cell produce seven distinct run "
           f"ids and three budgets three more ({id_base} for the base "
           f"config): MEASURED pre-fix, ALL of them were "
           f"'agenteXP2-C3-cOFF-t1400-s4242' — so the pilot's own prescribed "
           f"re-run at num_predict >= 9000 would have read the 6000-budget "
           f"rows as 'already measured, status OK'", results)
    prev_same = {"status": "OK", "config": {"identity_tag":
                                            _bound()["identity_tag"]}}
    prev_other = {"status": "OK", "config": {"identity_tag": "0123456789abcdef"}}
    prev_err = {"status": "ERROR", "config": {}}
    _check("camp/S5-resume-requires-the-same-identity",
           campaign_resume_ok(prev_same, _bound())[0] is True
           and campaign_resume_ok(prev_other, _bound())[0] is False
           and campaign_resume_ok(prev_err, _bound())[0] is False,
           "a completed run file is reused ONLY when its recorded "
           "configuration identity matches; a differing identity and a "
           "non-OK prior attempt both force a re-run (the second lock on the "
           "same door as the identity in the file name)", results)

    # -- S4: V1's BOUNDARY IS CLOSED (the plan's "below 0.5") ---------------
    at_band = void_predicates(
        _camp_rows(300, cov=lambda t: 0.5 if t > 100 else 1.0), seat_spec)
    under = void_predicates(
        _camp_rows(300, cov=lambda t: 0.4999 if t > 100 else 1.0), seat_spec)
    _check("camp/V1-boundary-is-closed",
           at_band["V1"]["void"] is True
           and at_band["V1"]["coverage_min"] == 0.5
           and under["V1"]["void"] is False,
           "coverage EXACTLY at the band (min 0.5) VOIDs and 0.4999 does not: "
           "the plan's sentence is 'never falls BELOW 0.5', so the boundary is "
           "closed and V1 is now the exact complement of the mirror's own "
           "`min < band` depletion clause (MEASURED pre-fix: a run sitting on "
           "0.5 read as neither depleted nor void — a hole)", results)

    # -- the wrapper FORWARDS the trace (item (2)'s wiring assertion) -------
    import stage2_harness as _H2
    from selfmodel import inward_share, inward_share_trace

    class _Chatty:
        def __init__(self):
            self.last_inward = "thinking about the self " * 40
            self.last_response = {"done_reason": "stop", "eval_count": 99}

        def __call__(self, turn, plant):
            return "[done(t1)]\nand one short outward line\n"

    inner = _Chatty()
    rec = RecordingDMN(inner)
    stream = rec(1, {})
    trace_val = _H2._inward_of(rec, stream, extract_spans(stream).self_content)
    want = inward_share_trace(inner.last_inward, stream)
    fallback = inward_share(stream, extract_spans(stream).self_content)
    _check("camp/wrapper-forwards-the-trace",
           rec.last_inward == inner.last_inward
           and abs(trace_val - want) < 1e-12
           and abs(trace_val - fallback) > 1e-6,
           f"RecordingDMN forwards `last_inward` and the harness's `_inward_of` "
           f"therefore reads the TRACE instrument ({trace_val:.4f}) rather than "
           f"the pre-trace fallback ({fallback:.4f}) — without the forwarding "
           f"the seat silently demotes", results)
    _check("camp/wrapper-records-the-register",
           rec.by_turn[1]["trace_chars"] == len(inner.last_inward)
           and rec.by_turn[1]["content_chars"] == len(stream)
           and rec.by_turn[1]["done_reason"] == "stop"
           and rec.by_turn[1]["eval_count"] == 99,
           "the per-turn record carries the trace/content char counts and the "
           "transport's own done_reason/eval_count — the V2/V3 evidence",
           results)

    class _CommitOnly:
        """The live 3B's measured register on turn 2: `expect(...)` spans and
        NO `[done(...)]`/`[orphaned(...)]` claim at all."""

        def __call__(self, turn, plant):
            return ("The agent expects the queue to clear.\n"
                    "[expect(t119)]\nand one outward line.\n")

    from selfmodel import (COMMITMENT_PREDICATES as _CP,
                           SELF_PREDICATES as _SP)
    rec3 = RecordingDMN(_CommitOnly(), predicates=_SP,
                        commitment_predicates=_CP)
    s3 = rec3(1, {})
    default_count = len(extract_spans(s3).claims)
    _check("camp/span-count-uses-the-run-s-OWN-grammar",
           rec3.by_turn[1]["spans"] == 1
           and rec3.by_turn[1]["commitments"] == 1
           and rec3.by_turn[1]["claims"] == 0
           and default_count == 0,
           f"a commitment-only emission counts as {rec3.by_turn[1]['spans']} "
           f"span(s) under the SELF seat's grammar and {default_count} under "
           f"the pre-self default: the supply column is measured with the "
           f"grammar the run's own batch is built with (the live 3B emitted "
           f"`expect` spans and no `[done]` claims — a counter keyed on the "
           f"pre-self set would have read 0 and failed P1 falsely)", results)

    class _NoChannel:
        def __call__(self, turn, plant):
            return "[done(t1)]\n"

    rec2 = RecordingDMN(_NoChannel())
    rec2(1, {})
    _check("camp/wrapper-absent-channel-is-None",
           rec2.last_inward is None, "an emitter with NO inward channel "
           "leaves the wrapper's `last_inward` None (the /api/generate "
           "declaration) — an absent channel is not an empty one",
           results)

    # -- the budget probes: an identity CHECKED, with a mismatch arm --------
    grow = _camp_rows(20, cov=lambda t: min(t, CAMPAIGN_BUDGET) / t,
                      candidates=lambda t: t)
    pr = probe_budgets(grow)
    idn = pr["identity_at_campaign_budget"]
    _check("camp/budget-probe-identity-holds",
           idn["reproduces_the_logged_coverage"] is True
           and pr["budgets"]["B=3"]["coverage_min"] < 0.5
           and pr["budgets"]["B=12"]["coverage_min"] > 0.5,
           f"the budget identity coverage(N)=min(N,B)/N reproduces the logged "
           f"coverage at B={CAMPAIGN_BUDGET} (max deviation "
           f"{idn['max_abs_deviation']:.2e}) and the probes read B=3 as "
           f"depleting and B=12 as NOT — the two pre-declared probes "
           f"discriminate", results)
    mismatch = _camp_rows(20, cov=0.9, candidates=lambda t: t)
    pm = probe_budgets(mismatch)
    _check("camp/budget-probe-detects-a-mismatch",
           pm["identity_at_campaign_budget"][
               "reproduces_the_logged_coverage"] is False,
           "a log whose coverage does NOT follow the identity is REPORTED as "
           "a mismatch (max deviation "
           f"{pm['identity_at_campaign_budget']['max_abs_deviation']:.2f}) — "
           "the probe is a check on the model, not a restatement of it",
           results)

    # -- the plant's spectator property (P3's baseline is exact) ------------
    old_anchor = os.environ.get("CEN_ANCHOR_DIR")
    os.environ["CEN_ANCHOR_DIR"] = tempfile.mkdtemp(prefix="camp-selftest-")
    try:
        class _SynthStream:
            def __call__(self, turn, plant):
                return (f"[done(t{turn % 40 + 1})]\n"
                        f"[orphaned(t{61 + turn % 50})]\nand some prose.\n")

        base = plant_no_drive_baseline(300)
        st_synth = run_stage2(rescue_schedule(), 300, Stage2Config(
            dmn=_SynthStream(), record_path=os.path.join(
                tempfile.mkdtemp(prefix="camp-spec-"), "R")), p=Params())
        Gs_synth = [float(r.G) for r in st_synth.log]
        _check("camp/plant-is-a-spectator-when-decoupled",
               base["turns"] == len(Gs_synth)
               and all(a == b for a, b in zip(base["G"], Gs_synth)),
               "with couple_backlog=False the plant's G trajectory is "
               "BIT-IDENTICAL whether the generator emits claims or nothing — "
               "so P3's no-drive baseline IS the plant's own, computed with "
               "no endpoint (the p2r2 spectator fact, reproduced offline)",
               results)
        # and the boundaries were really crossed (two windows), else the check
        # would be measuring a horizon that never reached the seat's timescale
        _check("camp/baseline-covers-two-windows",
               base["turns"] == 300 and base["turns"] > 2 * TAU_S_TURNS,
               f"the baseline runs {base['turns']} turns, past the second "
               f"consolidation boundary ({2 * TAU_S_TURNS}), so P3's "
               f"after-the-second-boundary clause is exercised on a real "
               f"horizon", results)

        # -- the pilot gates: each clause has a falsifying arm -------------
        good_rows = _camp_rows(
            300, cov=lambda t: (1.0 if t < 100 else
                                (min(80, 6 * (t // 100)) / 80.0)),
            G=lambda t: base["G"][min(t, len(base["G"])) - 1] if base["G"]
            else 0.9, drive=lambda t: 0.0 if t <= 200 else 0.7,
            spans=lambda t: 1 + (t % 3), candidates=lambda t: 80)
        g = pilot2_gates(good_rows, base, seat_spec)
        _check("camp/pilot2-all-clauses-live",
           g["P1_supply"] and g["P2_depletion"] and g["P4_register"]
           and (not g["P3_drive_live"]) and g["status"] == "FAIL",
           f"a synthetic pilot with varying supply, depleting coverage and a "
           f"clean register passes P1/P2/P4 while P3 FAILS (the drive is set "
           f"but the plant did not move off the baseline) — the gates "
           f"discriminate (status={g['status']})", results)
        moved = [dict(r, G=r["G"] + (0.02 if r["turn"] > 200 else 0.0))
                 for r in good_rows]
        g2 = pilot2_gates(moved, base, seat_spec)
        _check("camp/pilot2-P3-passes-when-the-plant-moves",
           g2["P3_drive_live"] and g2["status"] == "PASS",
           f"the SAME log with a plant that moved off the baseline passes P3 "
           f"and the whole gate (delta "
           f"{g2['evidence']['P3']['abs_delta']:.4f})", results)
        flat_cov = pilot2_gates(
            _camp_rows(300, cov=1.0, drive=0.7, spans=lambda t: 1 + (t % 3)),
            base, seat_spec)
        _check("camp/pilot2-P2-falsifier",
           (not flat_cov["P2_depletion"]) and flat_cov["status"] == "FAIL",
           "a pilot that never depletes FAILS P2 (and its evidence carries "
           "the budget probes + the STOP condition)", results)
        crowded_pilot = pilot2_gates(
            _camp_rows(300, cov=0.2, drive=0.7, spans=lambda t: 1 + (t % 3),
                       content=lambda t: 0 if t % 3 else 500), base, seat_spec)
        _check("camp/pilot2-P4-falsifier",
           (not crowded_pilot["P4_register"])
           and crowded_pilot["status"] == "FAIL",
           "a pilot whose content is empty in a third of its turns FAILS P4 "
           "BEFORE any full-length run — the register is a gate, not a note",
           results)
    finally:
        if old_anchor is None:
            os.environ.pop("CEN_ANCHOR_DIR", None)
        else:
            os.environ["CEN_ANCHOR_DIR"] = old_anchor


def _routing_arm_offline_check(outdir: str) -> dict:
    """Exercise the ROUTING-ON arm's wiring with NO endpoint: build the cell's
    config through the SAME `build_cfg` the sweep uses, publish/load the
    criterion in an ISOLATED namespace, and run the real harness for
    `TAU_S_TURNS + 5` turns with a synthetic stream generator (so a
    CONSOLIDATION BOUNDARY is crossed and the law runs a second time).
    Offline by construction — the generator never touches the network.

    The point: the arm the pilot does not cover is still PROVEN to wire up,
    and the law's applied fraction is RECORDED, before 80 GPU-hours are spent
    on it.  Every span count comes from the real extractor via RecordingDMN;
    nothing here is a placeholder."""
    # a FRESH namespace per invocation (the batteries' convention): a re-used
    # record path would carry a prior attempt's decision ids.
    root = tempfile.mkdtemp(prefix="ac-selftest-routing-on-")
    crit_dir = os.path.join(root, "crit")
    os.makedirs(crit_dir, exist_ok=True)
    old_anchor = os.environ.get("CEN_ANCHOR_DIR")
    old_crit = os.environ.get("CEN_ROUTINGCRIT_DIR")
    os.environ["CEN_ANCHOR_DIR"] = os.path.join(root, "anchors")
    # NOTE: build_cfg passes routing_criterion_dir EXPLICITLY, so the env is
    # only a belt-and-braces guard for any path that defaults.
    os.environ["CEN_ROUTINGCRIT_DIR"] = crit_dir
    try:
        crit = ensure_criterion(crit_dir)

        class _SynthStream:
            """A stream-emitting fake: claims first, prose after (the E1
            shape the real generator reproduces).  NO network."""

            def __call__(self, turn, plant):
                return (f"Looking at turn {turn} I notice the demand and the "
                        f"residue.\n[done(t{turn % 40 + 1})]\n"
                        f"[orphaned(t{61 + turn % 50})]\nIt keeps occupying "
                        f"me, without resolving.")

        n_turns = TAU_S_TURNS + 5
        cell_on = cell_of("routing-on", "SPEC", 100.0, 0)
        cell_off = dict(cell_on, arm="OFF")
        rec_on = RecordingDMN(_SynthStream())
        cfg_on = build_cfg(cell_on, rec_on, outdir=root, engine="stub",
                           crit_dir=crit_dir)
        cfg_off = build_cfg(cell_off, RecordingDMN(_SynthStream()),
                            outdir=root, engine="stub", crit_dir=crit_dir)
        # Record the WINDOW SEAT's own state turn by turn (f and which window)
        # — the applied fraction is state, so it is read from the state during
        # the run rather than re-derived from the law afterwards.
        trace: list = []

        def hook(turn, st):
            wv = st.routing_window
            trace.append({"turn": int(turn), "windows": int(wv.windows),
                          "f": float(wv.f)})
            return True

        st = run_stage2(rescue_schedule(), n_turns, cfg_on,
                        p=Params(tau_S=100.0), checkpoint_fn=hook)
        spans = [rec_on.by_turn[t]["spans"] for t in sorted(rec_on.by_turn)]
        w = st.routing_window
        rep = (w.last_report if w is not None else None) or {}
        # the applied fraction PER WINDOW (from the recorded seat, never from
        # a call to the law): one entry per distinct `windows` value.
        per_window = []
        for row in trace:
            if not per_window or per_window[-1]["windows"] != row["windows"]:
                per_window.append({"windows": row["windows"], "f": row["f"],
                                   "first_turn": row["turn"], "turns": 1})
            else:
                per_window[-1]["turns"] += 1
        f_by_turn = [row["f"] for row in trace]
        routed_by_turn = [r.routed for r in st.log]
        return {
            "turns_ran": len(st.log),
            "turns_requested": n_turns,
            "routed_per_turn": [r.routed for r in st.log],
            "routed_total": sum(r.routed for r in st.log),
            "spans_per_turn": spans,
            "spans_per_turn_min": (min(spans) if spans else 0),
            "spans_total": sum(spans),
            "selector": type(cfg_on.routing_selector).__name__,
            "spec_selector": type(cfg_on.routing_selector).__name__,
            "off_selector": type(cfg_off.routing_selector).__name__,
            "spec_couple_backlog": cfg_on.couple_backlog,
            "off_couple_backlog": cfg_off.couple_backlog,
            "criterion_dir_isolated": os.path.abspath(crit_dir).startswith(
                os.path.abspath(root)),
            "criterion_dir": crit["dir"],
            "criterion_version": crit["version"],
            # THE LAW'S OWN NUMBERS: the applied fraction and WHY.  With the
            # G-analogue unsolved the law takes the maximally conservative arm
            # (routing.py: G=None -> f_min with 'g_unsolved_conservative_arm'),
            # and the criterion clip carries f_min.  Recorded, not inferred.
            "window_windows": (w.windows if w is not None else None),
            "window_f": (w.f if w is not None else None),
            "f_per_window": per_window,
            "f_by_turn_distinct": sorted(set(f_by_turn)),
            "routed_by_turn": routed_by_turn,
            "routed_when_f_zero": sum(
                n for f, n in zip(f_by_turn, routed_by_turn) if f == 0.0),
            "routed_when_f_positive": sum(
                n for f, n in zip(f_by_turn, routed_by_turn) if f > 0.0),
            "law_boundary": rep.get("boundary"),
            "law_armed": rep.get("armed"),
            "law_g_live": rep.get("g_live"),
            "law_f_min_is_seat": rep.get("f_min_is_seat"),
            "law_arm_floor": rep.get("arm_floor"),
            "law_p2_addend": rep.get("p2_addend"),
            "law_theta_eff_arm": rep.get("theta_eff_arm"),
            "law_demand_analogue": rep.get("D"),
        }
    finally:
        if old_anchor is None:
            os.environ.pop("CEN_ANCHOR_DIR", None)
        else:
            os.environ["CEN_ANCHOR_DIR"] = old_anchor
        if old_crit is None:
            os.environ.pop("CEN_ROUTINGCRIT_DIR", None)
        else:
            os.environ["CEN_ROUTINGCRIT_DIR"] = old_crit


def _refuse_check(ns) -> int:
    """The refusal logic of mode_full, factored so the selftest can exercise
    it WITHOUT starting a run (it returns the exit code, not a run)."""
    outdir = ns.outdir
    pilot_path = os.path.join(outdir, "pilot.json")
    if not os.path.exists(pilot_path) and not ns.force_after_failed_pilot:
        return 3
    pilot = (json.load(open(pilot_path, encoding="utf-8"))
             if os.path.exists(pilot_path) else {"status": "ABSENT"})
    if pilot.get("status") != "PASS" and not ns.force_after_failed_pilot:
        return 3
    return 0


# ==========================================================================
# CLI
# ==========================================================================

def _overrides(args) -> dict:
    """What diverges from the pre-registration, recorded (never silent)."""
    out = {}
    if args.turns != TURNS_FULL and args.mode in ("full",):
        out["turns"] = {"prereg": TURNS_FULL, "used": args.turns}
    if args.n != N_DEFAULT:
        out["n"] = {"prereg": N_DEFAULT, "used": args.n}
    if args.tau_s and tuple(args.tau_s) != tuple(TAU_S_CELLS):
        out["tau_s"] = {"prereg": list(TAU_S_CELLS), "used": list(args.tau_s)}
    if args.routing and tuple(args.routing) != tuple(ROUTINGS):
        out["routing"] = {"prereg": list(ROUTINGS), "used": list(args.routing)}
    if args.arm and tuple(args.arm) != tuple(ARMS):
        out["arm"] = {"prereg": list(ARMS), "used": list(args.arm)}
    if args.engine != "stub":
        out["engine"] = {"prereg": "stub", "used": args.engine}
    return out


def parse_args(argv):
    ap = argparse.ArgumentParser(
        description="the agent-side coupling experiment (paper 2's "
                    "demonstration); spec = handoff-selfreg-agentexp-plan")
    ap.add_argument("--pilot", action="store_true",
                    help="the mandatory pilot gate (ONE run, SPEC+route-all, "
                         "tau_S=100, 150 turns) — prints per turn and "
                         "evaluates gate1-4")
    ap.add_argument("--pilot2", action="store_true",
                    help="THE CAMPAIGN'S PILOT GATE: ONE run of C3's config, "
                         "300 turns, one seed — gates P1-P5 (supply, "
                         "depletion, drive-live, register, cost)")
    ap.add_argument("--campaign", action="store_true",
                    help="THE AGENTEXP2 CAMPAIGN (six conditions, the "
                         "four-outcome matrix) — REFUSED unless --pilot2 "
                         "passed")
    ap.add_argument("--det-check2", action="store_true",
                    help="OUTCOME-level repeatability for the campaign's C3 "
                         "config: the SAME cell and seed base twice, "
                         "comparing outcomes and trajectory invariants (the "
                         "streams are MEASURED not to be bit-identical)")
    ap.add_argument("--cells", nargs="*", default=None,
                    choices=list(CAMPAIGN_PHASE_ORDER),
                    help="with --campaign: run only these conditions "
                         f"(pre-registered plan: {list(CAMPAIGN_PHASE_ORDER)})")
    ap.add_argument("--full", action="store_true",
                    help="the pre-registered matrix (REFUSED unless the "
                         "pilot passed)")
    ap.add_argument("--det-check", action="store_true",
                    help="settle the plan's open question: same seed twice, "
                         "diff the streams per turn")
    ap.add_argument("--matrix", nargs="*", default=None,
                    help="OFFLINE: assemble a matrix from run JSON files")
    ap.add_argument("--rescore", action="store_true",
                    help="OFFLINE: recompute the pilot gate (and its "
                         "diagnostics) from the rows already on disk")
    ap.add_argument("--selftest", action="store_true",
                    help="OFFLINE: the criterion scorer, the gates, the "
                         "matrix and the refusal paths (default mode)")
    ap.add_argument("--rerun", action="store_true",
                    help="with --full: re-measure cells whose run JSON "
                         "already reports OK (default: skip them — the "
                         "crash-resume path)")
    ap.add_argument("--dry-run", action="store_true",
                    help="with --full: list the planned cells and the "
                         "projected cost, start nothing")
    ap.add_argument("--turns", type=int, default=None,
                    help=f"turns per run (pre-registered: {TURNS_FULL} for "
                         f"the matrix, {PILOT_TURNS} for the pilot, "
                         f"{PILOT2_TURNS} for --pilot2; the CAMPAIGN's own "
                         f"horizons come from CAMPAIGN_CONDITIONS unless "
                         f"this is given — C6 stays at its "
                         f"CONTROL_CAP_TURNS={CONTROL_CAP_TURNS} cap)")
    ap.add_argument("--n", type=int, default=None,
                    help=f"repeats per cell (pre-registered: {N_DEFAULT} for "
                         f"the matrix; the CAMPAIGN's own per-condition N "
                         f"comes from CAMPAIGN_CONDITIONS unless this is "
                         f"given — an explicit --n OVERRIDES every "
                         f"condition's design N)")
    ap.add_argument("--tau-s", type=float, nargs="*", default=None,
                    help="tau_S cells (pre-registered: 25 50 100)")
    ap.add_argument("--routing", nargs="*", default=None,
                    choices=list(ROUTINGS))
    ap.add_argument("--arm", nargs="*", default=None, choices=list(ARMS))
    ap.add_argument("--engine", default="stub", choices=["stub", "real"])
    ap.add_argument("--det-turns", type=int, default=20)
    ap.add_argument("--progress-every", type=int, default=50)
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    ap.add_argument("--endpoint", default=dmn_llm.DEFAULT_ENDPOINT,
                    help="the /api/generate endpoint (the gemma arm; also "
                         "C6's transport)")
    ap.add_argument("--model", default=dmn_llm.DEFAULT_MODEL,
                    help="the /api/generate model")
    ap.add_argument("--api", default=dmn_llm.GENERATE,
                    choices=[dmn_llm.GENERATE, dmn_llm.CHAT],
                    help="THE TRANSPORT for this runner's own generator "
                         "(default: the pre-change generate path).  The "
                         "campaign's chat cells name their own api; this flag "
                         "lets a NON-campaign mode run the reasoning arm too, "
                         "via dmn_llm.make_reasoning_dmn (no `think` key)")
    ap.add_argument("--chat-endpoint", default=dmn_llm.DEFAULT_CHAT_ENDPOINT,
                    help="the /api/chat endpoint (the reasoning arm) — point "
                         "this at a remote ollama (vast.ai) to run the "
                         "campaign off-box; the harness stays local")
    ap.add_argument("--chat-model", default=dmn_llm.DEFAULT_CHAT_MODEL,
                    help="the /api/chat model (the campaign's instrument; "
                         "the conformance-verified 3B is faster — set it "
                         "explicitly, it is recorded in every run JSON)")
    ap.add_argument("--control-model", default=dmn_llm.DEFAULT_MODEL,
                    help="C6's precondition-negative model (the gemma arm "
                         "through /api/generate)")
    ap.add_argument("--num-predict", type=int, default=None,
                    help=f"the generation budget (campaign default: "
                         f"{CAMPAIGN_NUM_PREDICT}; unset = dmn_llm's own "
                         f"default outside the campaign)")
    ap.add_argument("--num-ctx", type=int, default=None,
                    help=f"the context window (campaign default: "
                         f"{CAMPAIGN_NUM_CTX}; unset = dmn_llm's own 4096 "
                         f"outside the campaign)")
    ap.add_argument("--temperature", type=float, default=0.6,
                    help="the model's operating point (the bake's); a change "
                         "is recorded in every run JSON")
    ap.add_argument("--force-after-failed-pilot", action="store_true",
                    help="RECORDED override of the pilot gate (either "
                         "pilot's) — for diagnostics only, never for the "
                         "pre-registered run")
    args = ap.parse_args(argv)

    # F1 — AN OVERRIDE MUST BE DISTINGUISHABLE FROM A DEFAULT.  argparse
    # cannot tell an explicit "--n 3" from its own default, and the campaign's
    # per-condition N lives in CAMPAIGN_CONDITIONS, so the EXPLICITNESS is
    # recorded here, BEFORE the defaults above are applied: the campaign reads
    # `n_explicit`/`turns_explicit` to decide whether a flag overrides the
    # pre-registration's own plan or merely fills in the matrix lane's default
    # (MEASURED before this fix: the campaign's default invocation planned 21
    # specs instead of the plan's 13, because --n's DEFAULT was passed as an
    # override for every condition).
    args.n_explicit = args.n is not None
    args.turns_explicit = args.turns is not None
    if args.n is None:
        args.n = N_DEFAULT

    modes = [m for m in ("pilot", "pilot2", "campaign", "det_check",
                         "det_check2", "full", "selftest",
                         "rescore") if getattr(args, m)]
    if args.matrix is not None:
        modes.append("matrix")
    if len(modes) > 1:
        ap.error("pick ONE mode: --pilot / --pilot2 / --campaign / "
                 "--det-check / --det-check2 / --full / --matrix / "
                 "--rescore / --selftest")
    args.mode = modes[0] if modes else "selftest"
    if args.turns is None:
        if args.mode == "pilot":
            args.turns = PILOT_TURNS
        elif args.mode == "pilot2":
            args.turns = PILOT2_TURNS
        elif args.mode == "det_check2":
            args.turns = PILOT2_TURNS
        else:
            args.turns = TURNS_FULL
    if args.mode == "det_check2":
        args.det_turns = args.turns
    if args.mode == "pilot2" and args.turns != PILOT2_TURNS:
        _warn(f"--turns {args.turns} overrides the campaign pilot's "
              f"pre-registered {PILOT2_TURNS} turns; the pilot is a GATE on "
              f"the regime, so a shorter run is a weaker gate (RECORDED in "
              f"pilot2.json)")
    if args.mode == "campaign" and args.turns != TURNS_FULL:
        _warn(f"--turns {args.turns} overrides the pre-registered campaign "
              f"horizon {TURNS_FULL} turns; RECORDED as an override, and the "
              f"G2c window [1000,1400] will not be reached")
    if args.pilot and args.turns != PILOT_TURNS:
        _warn(f"--turns {args.turns} overrides the pilot's pre-registered "
              f"{PILOT_TURNS} turns; the pilot is a GATE on the regime, so a "
              f"shorter run is a weaker gate (RECORDED in pilot.json)")
    if args.mode == "full" and args.turns != TURNS_FULL:
        _warn(f"--turns {args.turns} overrides the pre-registered horizon "
              f"{TURNS_FULL} turns; RECORDED in matrix.json as an override, "
              f"and the G2c window [1000,1400] will not be reached")
    if args.n < N_DEFAULT:
        _warn(f"--n {args.n} is below the pre-registered N >= {N_DEFAULT}; "
              f"acceptance is a FRACTION and the matrix records "
              f"n_below_prereg=true")
    return args


def main(argv=None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    os.makedirs(args.outdir, exist_ok=True)
    handlers = {"selftest": mode_selftest, "pilot": mode_pilot,
                "pilot2": mode_pilot2, "campaign": mode_campaign,
                "det_check": mode_det_check, "det_check2": mode_det_check2,
                "full": mode_full, "matrix": mode_matrix,
                "rescore": mode_rescore}
    try:
        return handlers[args.mode](args)
    except KeyboardInterrupt:
        _warn("interrupted — the per-turn JSONL rows already written are "
              "intact (re-run assembles from them)")
        return 130


if __name__ == "__main__":
    sys.exit(main())
