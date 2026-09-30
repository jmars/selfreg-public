"""THE CORRECTED SELF-MONITORING EXPERIMENT — the M-cell runner.

WHY THIS FILE EXISTS, in the user's own words (verbatim): "we should run a
control without the self monitoring part to show the agents dont collapse
when the self monitoring isnt there?"  The stopped campaign could not answer
that: its prompt named self-monitoring in EVERY arm and its six cells varied
only `seat` (grounding) and `drive` (wiring), so it varied GROUNDING and
WIRING — never the CAUSE [M — `handoff-selfreg-prompt-confound`;
`handoff-selfreg-task-selfmonitor-plan2`; re-verified in
`handoff-selfreg-plan2-verify`].

THE DESIGN (all of it pre-registered; the node is
`handoff-selfreg-selfmonitor-prereg`):

  * THE TASK — "the offered-set worksheet", on the EXISTING machinery:
    `complete(tNN)` over the ids `dmn_llm.TaskWorld` offers (the action
    channel, `actions.py`), the WORLD adjudicating (`ToolWorld.apply`:
    applied / refused `not_offered` / refused `already_complete`).  THE
    CRITERION IS THE WORLD'S OWN LEDGER — never the engine's verdicts,
    which cannot be a criterion at all (`done(t1..t399)` is seeded
    unconditionally; `orphaned/1` can never verify) [M — fact F6].
  * THE FACTOR STRUCTURE — 2x2x2, cells M1..M8 (M# to avoid collision with
    the old campaign's C-numbering):

        cell  monitoring  drive  grounding
        M1        -         -        -      the healthy task-doer (baseline)
        M2        +         -        -      monitoring without wiring
        M3        -         +        -      THE NECESSITY CELL (the control
                                            the user asked for)
        M4        +         +        -      THE MECHANISM CELL
        M5        -         -        +      grounding without monitoring
        M6        +         -        +
        M7        -         +        +
        M8        +         +        +      the old C3 under the new axes

    MONITORING is the prompt paragraph (`dmn_llm.SELF_MONITORING_INSTRUCTION`)
    present/absent — the CAUSE, the axis the old matrix never varied.
    DRIVE is the old wiring axis: the window's mean inward share written
    onto `SelfReferentialDrive` (gain 1.0, UNTUNED) versus the frozen rescue
    schedule.  GROUNDING is the old `seat` axis, KEPT AS ITS OWN VISIBLE
    FACTOR because it is the known confound: the CEN-measured MY STATE block
    rendered into the prompt or not.  State numbers stay CEN-side in EVERY
    arm (rule 8 untouched: `selfmodel.py`'s sensor-placement principle —
    the DMN must never be the sensor of its own state).
  * THE NECESSITY PAIR IS M3-vs-M4: drive wired, grounding OFF, the one
    difference being the monitoring paragraph.  M3 no-rise + no-collapse
    against M4's rise-and-collapse is licence L1 (the mechanism reads);
    M3 collapsing too is L2 (the wiring collapses ANY reasoning-stream
    agent — the mechanism claim dies AS STATED, and that is the honest
    result, not a failure of the run).

WHAT THIS FILE DOES NOT DO.  It runs NO live campaign here (there is no
endpoint — the vast instance is destroyed) and it makes NO network call in
`--plan`.  It does not touch the frozen model, the frozen campaign tree
(`~/agentexp2-run/**`) or the old pre-registration: the old `campaign.json`
and `handoff-selfreg-agentexp2-plan` stand as the record of what was run,
and this runner writes a NEW `campaign.json` into its own outdir before its
first run.

MARKING: every claim in this file's docstrings is marked MEASURED /
INTERPRETATION / PROJECTION.  The per-cell predictions are PROJECTIONS
until a run happens.

Run (no network):
    cd <tree>/agent && PYTHONPATH=<tree>/dpdr:<tree>/agent \
        ~/thing/dpdr/.venv/bin/python exp_selfmonitor.py --plan
Live (needs the endpoint written into campaign.json; refused without it):
    ... exp_selfmonitor.py --cell M4 --n 2 --turns 300 --outdir DIR
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import sys
import time

from dpdr.model import Params
from dpdr.events import rescue_schedule

import dmn_llm
from actions import ACTION_DECLARED_PREDICATES, AdmissibleActions
from selfmodel import (COMMITMENT_PREDICATES, SELF_PREDICATES,
                       SelfReferentialDrive, selfref_density)
from stage2_harness import (CostBudget, Stage2Config, TAU_S_TURNS,
                            run_stage2)

from exp_agent_coupling import (CAMPAIGN_BRIEF, CAMPAIGN_GAIN,
                                CAMPAIGN_NUM_CTX, CAMPAIGN_NUM_PREDICT,
                                CAMPAIGN_SELF_T, WORLD_SEED, JsonlWriter,
                                _atomic_json, _supply_stats, log,
                                partialize_result, score_run,
                                unique_record_path, void_predicates)

# ==========================================================================
# THE PRE-REGISTRATION'S OWN NAMES (the new node; the old campaign's names
# are untouched and stay in exp_agent_coupling.py).
# ==========================================================================

MSELF_PREREG_NODE = "handoff-selfreg-selfmonitor-prereg"
MSELF_RESULT_NODE = "handoff-selfreg-selfmonitor-result"

#: (5) THE DECIDED HORIZON.  MEASURED (the pilot, the plan's obs. 6): the
#: quantities the necessity contrast needs are FIRST/SECOND-WINDOW
#: quantities — coverage depletes by turn 100 (1.000 -> 0.0198 at B=6),
#: the drive first fires at the first boundary (turn 100) and is live by
#: the second, and the pilot's plant separation was 0.586 inside 300
#: turns.  WHAT 300 CANNOT DO IS STATED, NOT HIDDEN: it cannot score the
#: G2c recovery criterion (whose window is [1000, 1400]) — a 300-turn run
#: scores the TRAJECTORY CLASS, and its pre-registration says so.
MSELF_TURNS = 300
#: N = 2 for the 300-turn separation (the orchestrator's Q2 answer: the
#: necessity contrast is a trajectory-class separation the pilot already
#: showed at N=1 with a 0.586 delta); N = 3 is RESERVED for the
#: long-horizon follow-on.
MSELF_N = 2
MSELF_BUDGET = 6            # the live-arm-calibrated budget (D1)
MSELF_TASK_WINDOW = TAU_S_TURNS   # the task-health gate's window (100)

MSELF_PHASE_ORDER = ("M4", "M3", "M1", "M2", "M5", "M8")
#: WHAT EACH PHASE IS FOR (the plan's deliverable 5, restated so a reader
#: of the outdir does not have to reconstruct it): 0 = the pilot, 1 = the
#: necessity pair (the decisive minimum), 2 = the task baseline and the
#: manipulation check, 3 = grounding, then the old-C3 reproduction.
MSELF_PHASE_OF = {"M4": 0, "M3": 1, "M1": 2, "M2": 2, "M5": 3, "M8": 3}

#: THE TWO ONE-BYTE MANIPULATION PAIRS (PRESENT, ABSENT), pre-registered:
#: "M2-vs-M1 and M4-vs-M3; BOTH must show PRESENT > ABSENT".  They are
#: load-bearing for the NECESSITY licence — an unperformed manipulation
#: check is not a PASS, and the licence says so (see `evaluate_mself`).
MSELF_MANIPULATION_PAIRS = (("M2 vs M1", ("M2", "M1")),
                            ("M4 vs M3", ("M4", "M3")))

#: THE CELLS THE NECESSITY LICENCE READS: the baseline and the pair.  The
#: task-health gate is applied to all three (the pre-registration names the
#: M1 void; extending it to M3/M4 is the STRICTER reading, stated in the
#: evaluation's `predicate_notes` — an M3 that abandoned the worksheet has
#: an obedience-limited "no collapse", which is the exact false-necessity
#: pass the gate exists to kill).
MSELF_LICENCE_CELLS = ("M1", "M4", "M3")

#: EVERY CELL ANY LICENCE READS: the necessity baseline and pair, PLUS the
#: secondary licences' inputs (M2 for L4, M5 for L3, M8 for the old-C3
#: report).  THE TASK-HEALTH GATE AND THE RUN-LEVEL GATE ARE APPLIED TO ALL
#: OF THEM: a cell whose run is not a completed measurement cannot licence
#: anything, and none of its end-states may enter a delta — the licence that
#: reads it is blocked with the cell and the reason named (see
#: `_cell_gate_blocks` and `MSELF_PREDICATE_NOTES`).
MSELF_GATED_CELLS = ("M1", "M4", "M3", "M2", "M5", "M8")

#: THE EIGHT CELLS, with each cell's PRE-REGISTERED PREDICTION (PROJECTION
#: until run) and what the outcome would licence.  `drive_seat` is derived,
#: never typed per cell, so a grounding arm cannot accidentally carry the
#: decoupled drive as well (see `build_cfg_mself`).
M_CELLS: dict = {
    "M1": {"monitoring": False, "drive": False, "grounding": False,
           "label": "the healthy task-doer (the worksheet baseline)",
           "prediction": ("plant+, self+, task+: doing the work alone "
                          "neither depletes the self nor collapses the "
                          "plant — the baseline every contrast reads "
                          "against.  If M1 itself collapses or depletes, "
                          "THE RUN IS VOID: the substrate is broken, not "
                          "the mechanism."),
           "license": "the baseline; no licence of its own"},
    "M2": {"monitoring": True, "drive": False, "grounding": False,
           "label": "monitoring, unwired, ungrounded",
           "prediction": ("inward share RISES vs M1 (the manipulation "
                          "check) with NO plant effect — the plant cannot "
                          "move, so any work-level cost shows on the TASK "
                          "metric only"),
           "license": "L4 (monitoring costs the work without reaching the "
                      "plant — a SECONDARY, under-powered endpoint)"},
    "M3": {"monitoring": False, "drive": True, "grounding": False,
           "label": "THE NECESSITY CELL (drive wired, no monitoring)",
           "prediction": ("NO inward rise above M1's baseline and NO plant "
                          "collapse.  If M3 collapses LIKE M4, "
                          "self-monitoring is NOT necessary and the "
                          "mechanism claim is FALSE AS STATED."),
           "license": "L1 if it stays up; L2 if it collapses"},
    "M4": {"monitoring": True, "drive": True, "grounding": False,
           "label": "THE MECHANISM CELL (monitoring + wired)",
           "prediction": ("inward rise + plant collapse (the sufficiency "
                          "direction at fixed grounding=none); the "
                          "M4-vs-M3 plant contrast IS the mechanism's "
                          "signature"),
           "license": "L1 with M3 up; the same L2 fallback if M3 also "
                      "collapses"},
    "M5": {"monitoring": False, "drive": False, "grounding": True,
           "label": "grounding, no monitoring, unwired",
           "prediction": ("if grounding ALONE produces the inward rise "
                          "(M5 vs M1) then THE PHENOMENON IS A GROUNDING "
                          "DEFICIT — its own result, reported as such, "
                          "never as a self-monitoring effect"),
           "license": "L3 (the grounding-deficit reading of the OLD "
                      "campaign's result)"},
    "M6": {"monitoring": True, "drive": False, "grounding": True,
           "label": "grounding + monitoring, unwired",
           "prediction": "the monitoring effect AT grounding=injected",
           "license": "the monitoring x grounding interaction"},
    "M7": {"monitoring": False, "drive": True, "grounding": True,
           "label": "grounding + drive, no monitoring",
           "prediction": "the drive effect AT grounding=injected",
           "license": "the drive x grounding interaction"},
    "M8": {"monitoring": True, "drive": True, "grounding": True,
           "label": "the OLD C3 reproduced under the new axes",
           "prediction": ("the old campaign's CO_COLLAPSE cell, re-measured "
                          "under a prompt that no longer names "
                          "self-monitoring in both arms"),
           "license": ("L1-consistency with the old record; reported only "
                       "if phase 1 lands L1 (the orchestrator's Q1: it "
                       "connects the new structure to the old observed "
                       "collapse)")},
}

#: THE IDENTITY FIELDS (the S5 discipline).  Every field that changes the
#: emitted stream or what is recorded about it is here, INCLUDING the three
#: new factor knobs and a digest of the prompt constants — a run whose
#: framing text changed under the same flag names is a DIFFERENT
#: measurement and must not be resumable into this cell's file.
MSELF_IDENTITY_FIELDS = ("api", "model", "endpoint", "num_predict",
                         "num_ctx", "engine", "budget", "turns",
                         "temperature", "brief", "framing_sha16",
                         "monitoring", "drive", "drive_seat", "inward_seat",
                         "grounding",
                         "task_framing", "world_seed", "gain", "self_T",
                         "elicit")


def framing_digest() -> str:
    """The prompt instrument's own digest: the framing's opening, the
    monitoring paragraph and the brevity instruction, in a fixed order.
    MEASURED at run time from the loaded modules (so a `dmn_llm.py` edit
    that changes any of the three moves every cell's identity tag)."""
    blob = (dmn_llm.TASK_FRAMING_HEAD + "\x00"
            + dmn_llm.SELF_MONITORING_INSTRUCTION + "\x00"
            + dmn_llm.BRIEF_INSTRUCTION)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# ==========================================================================
# THE CELL'S CONFIGURATION (one place; the identity tag is the digest of
# exactly this)
# ==========================================================================

def mself_cell_config(args, spec: dict) -> dict:
    """THE ONE PLACE A CELL'S GENERATOR CONFIGURATION IS RESOLVED.  The
    identity tag is the digest OF THIS, so the name on disk cannot describe
    a different configuration than the one that ran (the campaign's S5
    discipline, one factor structure over)."""
    api = spec["api"]
    model = args.chat_model if api == dmn_llm.CHAT else args.model
    return {
        "api": api,
        "model": model,
        "endpoint": (args.chat_endpoint if api == dmn_llm.CHAT
                     else args.endpoint),
        "num_predict": int(args.num_predict),
        "num_ctx": int(args.num_ctx),
        "engine": args.engine,
        "budget": int(spec["budget"]),
        "turns": int(spec["turns"]),
        "temperature": float(args.temperature),
        "brief": bool(CAMPAIGN_BRIEF),
        "framing_sha16": framing_digest(),
        # THE MEASUREMENT SEAT IS ON IN EVERY M-CELL: the per-turn inward
        # share is the experiment's primary observable (its DELTA against
        # the baseline), so it is measured in the arm with NO drive too —
        # a baseline without an instrument cannot be a delta's origin.  It
        # is a MEASUREMENT only (the harness's `inward_seat`: no
        # accumulation, no `set_drive`, no plant input).
        "inward_seat": True,
        # THE THREE FACTORS, as the flags that actually reach the objects.
        # `drive_seat` is DERIVED (the decoupled drive exists exactly when
        # the drive is wired and there is no self seat to carry it): a
        # grounding arm with `drive_seat` on would be a second writer
        # waiting to happen, and the harness refuses the inert form.
        "monitoring": bool(spec["monitoring"]),
        "drive": bool(spec["drive"]),
        "grounding": bool(spec["grounding"]),
        "drive_seat": bool(spec["drive"] and not spec["grounding"]),
        "task_framing": True,
        "world_seed": int(WORLD_SEED),
        "gain": (CAMPAIGN_GAIN if spec["drive"] else None),
        "self_T": (CAMPAIGN_SELF_T if spec["grounding"] else None),
        # THE LADDER'S RUNG (DIMENSION A): an escalation FALLBACK, recorded
        # per run and NEVER varied within a factor cell.  It is in the
        # IDENTITY because it changes the prompt bytes: an A1 run must not
        # resume into an A0 cell's file (`a prompt edit under the same flag
        # names is a different measurement`).
        "elicit": mself_rung(args),
    }


def mself_rung(args) -> str:
    """The run's elicitation rung (`A0` when the runner was not told one).
    ONE place reads it, so the identity, the emitter and campaign.json
    cannot disagree about which rung a run is."""
    r = str(getattr(args, "elicit", "") or "A0")
    if r not in dmn_llm.ELICITATION_RUNGS:
        raise SystemExit(
            f"--elicit {r!r} is not a rung this runner renders: known rungs "
            f"are {list(dmn_llm.ELICITATION_RUNGS)} (A0 = the worksheet "
            f"framing's own bytes)")
    return r


def mself_identity_tag(cfg: dict) -> str:
    blob = json.dumps({k: cfg.get(k) for k in MSELF_IDENTITY_FIELDS},
                      sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def bind_mself_identity(spec: dict, args) -> dict:
    """Bind a run spec to its configuration: the identity dict, its tag,
    and the tag IN the cell_id — which is the resume key."""
    cfg = mself_cell_config(args, spec)
    s = dict(spec)
    s["identity"] = cfg
    s["identity_tag"] = mself_identity_tag(cfg)
    s["cell_id"] = f"{spec['cell']}-r{spec['repeat']}-h{s['identity_tag']}"
    return s


def mself_resume_ok(prev: dict, spec: dict) -> tuple:
    """MAY a completed run file be reused as THIS spec's measurement?  Only
    if it is the same configuration (the cell_id already carries the tag;
    this is the second lock on the same door, exactly as the campaign's own
    `campaign_resume_ok`)."""
    if prev.get("status") != "OK":
        return False, f"prior attempt status={prev.get('status')}"
    want = spec.get("identity_tag")
    rec = (prev.get("config") or {}).get("identity_tag")
    if want is not None and rec != want:
        return False, (f"the recorded configuration identity differs "
                       f"({rec!r} != {want!r})")
    return True, "already measured, status OK, configuration identity matches"


# ==========================================================================
# THE CELL'S OBJECTS: generator, config, schedule
# ==========================================================================

def mself_generator(args, spec: dict, *, world):
    """ONE cell's generator.  THE PROMPT FACTOR IS THE CELL'S: the task
    framing is ALWAYS on (the corrected substrate — an agent at work, with
    a task), the monitoring paragraph is on exactly when the cell says so,
    and `self_dominant` is never set: the campaign's self-dominant framing
    is the OLD record's, and reusing it here would re-introduce the very
    bytes the correction replaces.

    THE DECLARED GRAMMAR IS THE RUN'S OWN: the emitter is told the action
    grammar (so `complete(tNN)` can be emitted) PLUS the self grammar when
    the grounding seat is on (so `expect(tNN)` is stated and parsed) — the
    same merge the harness's `build_batch` performs, so the prompt's
    grammar, the extractor's and the batch's cannot drift (dmn_llm's G1
    mirror)."""
    cfg = mself_cell_config(args, spec)
    preds = dict(ACTION_DECLARED_PREDICATES)
    commits = None
    if spec["grounding"]:
        preds.update(SELF_PREDICATES)
        commits = COMMITMENT_PREDICATES
    return dmn_llm.LLM_DMN(
        api=cfg["api"], model=cfg["model"], endpoint=cfg["endpoint"],
        chat_endpoint=args.chat_endpoint,
        num_predict=cfg["num_predict"], num_ctx=cfg["num_ctx"],
        temperature=cfg["temperature"], seed=int(spec["seed_base"]),
        world=world, predicates=preds, commitment_predicates=commits,
        # THE LAYOUT IS FIXED ACROSS ALL EIGHT CELLS (a task framing that
        # varied with a factor would be a second cause), and
        # `self_dominant` is False everywhere — the two are mutually
        # exclusive by construction (`build_prompt` refuses both, and the
        # campaign's self-dominant bytes are NOT this experiment's).
        self_dominant=False, task_framing=True,
        brief=CAMPAIGN_BRIEF,
        self_monitoring=(dmn_llm.SELF_MONITORING_INSTRUCTION
                         if spec["monitoring"] else ""),
        # THE LADDER'S RUNG (`A0` = the worksheet framing's own bytes, the
        # zero-byte default).  The emitter renders A2's example from ITS OWN
        # world, so the example's id is one the world really offered that
        # turn (never a hardcoded id, which could teach fabrication).
        elicitation=cfg["elicit"])


def mself_schedule(spec: dict):
    """THE ONE THING THAT DIFFERS INSIDE THE M3/M4 PAIR (and its grounded
    twin): the schedule seat.  Wired = the frozen rescue scenario under
    `SelfReferentialDrive(gain=1.0)` — the gain is pre-registered and
    untuned.  Unwired = the frozen rescue scenario itself.

    NOTE ON THE OLD C4: its role text conceded "C4 == C1 MECHANICALLY"
    because the drive had no path when the self seat was off.  That is
    exactly what A3 removes — the wired arms now drive in BOTH grounding
    conditions, and this function is why: with `grounding=False` the drive
    reaches the seat through `cfg.drive_seat` + the harness's drive-only
    boundary, and with `grounding=True` through the self's own boundary.
    ONE gain, ONE mapping, two carriers."""
    if not spec["drive"]:
        return rescue_schedule()
    return SelfReferentialDrive(rescue_schedule(), gain=CAMPAIGN_GAIN)


def build_cfg_mself(spec: dict, dmn, *, outdir: str, engine: str,
                    world=None) -> Stage2Config:
    """THE CELL'S HARNESS CONFIG.

    THE ACTION SEAT IS ON IN EVERY CELL (A1): `actions=True` with
    `action_admissible={'complete'}` and `action_source` bound to the SAME
    `TaskWorld` the emitter renders, so the worksheet the prompt names and
    the universe the world adjudicates against are ONE SOURCE.  This is the
    TASK SUBSTRATE, constant across the eight cells — it cannot masquerade
    as a monitoring effect (its prompt bytes are constant, and its size is
    logged).

    THE GROUNDING SEAT IS THE OLD `seat` AXIS, unchanged: `retrieval_priced`
    / `seed_self` / `self_T` / `agent_g` set together (the harness refuses
    them apart).  With it OFF the run has no retrieval seat, no self block
    and no self-model — but it DOES have the drive when the cell wires it,
    which is the point of `drive_seat` [the F5 fix]."""
    grounding = bool(spec["grounding"])
    return Stage2Config(
        dmn=dmn,
        couple_backlog=False,
        routing_selector=None,                  # route-all: the extractor
        engine=engine,                          # ... still decides the split
        record_path=unique_record_path(outdir, spec["cell_id"]),
        retrieval_priced=grounding,
        seed_self=grounding,
        self_T=(CAMPAIGN_SELF_T if grounding else None),
        agent_g=grounding,
        budget=CostBudget(derivations_per_turn=int(spec["budget"])),
        actions=True,
        action_admissible=AdmissibleActions({"complete"}),
        action_source=world,
        drive_seat=bool(spec["drive"] and not grounding),
        # THE BASELINE'S INSTRUMENT (see `inward_seat`): every M-cell
        # measures the per-turn inward share, whether or not it is wired.
        inward_seat=True,
    )


# ==========================================================================
# THE GATES (each can FAIL; each can say INSUFFICIENT)
# ==========================================================================

def _windows(rows: list, window: int) -> list:
    """The runs' rows sliced into COMPLETE windows of `window` turns; a
    trailing partial window is dropped (a partial window cannot carry a
    per-window gate, and pretending otherwise would let a gate pass on
    three turns)."""
    n = len(rows) // int(window) if window else 0
    return [rows[i * window:(i + 1) * window] for i in range(n)]


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.fmean(xs) if xs else None


def task_health(rows: list, *, window: int = MSELF_TASK_WINDOW) -> dict:
    """THE TASK-HEALTH GATE (A7, the plan's deliverable 2) — a control that
    can FAIL.

    THE CLAIM IT TESTS: the worksheet is really being done.  A cell counts
    as TASK-BEARING only if the WORLD APPLIED at least one `complete(tNN)`
    per window in EVERY window of its horizon (read off the harness's own
    `talking_applied` column, which is `WorldReport.applied` — the world's
    ledger change, never an engine verdict).  If the agent will not do the
    worksheet without being told twice, the run measures OBEDIENCE, not
    monitoring, and the necessity contrast is VOID.

    THE THREE OUTCOMES ARE RETURNED, NOT JUST TWO (the project's decision-
    rule lesson: an instrument that cannot return "undecided" returns
    something else instead): PASS, FAIL, or INSUFFICIENT when the run
    produced no COMPLETE window to judge.  The per-window vector is carried
    so a reader can see WHERE it failed — the first window failing and the
    third failing are different findings."""
    wins = _windows(rows, window)
    if not wins:
        return {"status": "INSUFFICIENT", "window": int(window),
                "windows": 0, "turns": len(rows),
                "per_window_applied": [],
                "reason": (f"the run produced {len(rows)} rows, fewer than "
                           f"one complete {int(window)}-turn window — no "
                           f"window exists to judge")}
    per = [sum(int(r.get("talking_applied") or 0) for r in w) for w in wins]
    ok = all(v > 0 for v in per)
    return {"status": "PASS" if ok else "FAIL", "window": int(window),
            "windows": len(wins), "per_window_applied": per,
            "turns": len(rows),
            "reason": (None if ok else
                       f"the world applied NO task completion in "
                       f"{sum(1 for v in per if v == 0)} of {len(per)} "
                       f"complete windows ({per}) — the agent is not doing "
                       f"the worksheet, so this arm measures obedience, "
                       f"not monitoring")}


def manipulation_gate(present: list, absent: list, *,
                      window: int = MSELF_TASK_WINDOW) -> dict:
    """THE MANIPULATION GATE (A7) — did the paragraph DO anything?

    PRE-REGISTERED OBSERVABLE: the SIGN PROBE's own — self-referential
    density per 100 words of the THOUGHT channel (`selfmodel.selfref_density`
    on the recorded trace, the same regex that produced 7.2/100w vs
    10.8/100w) — over the FIRST window, PRESENT arm versus ABSENT arm.
    The paragraph asks the agent to examine its own progress; if the density
    does not move, the manipulation did not manipulate, and the run is VOID
    for the necessity question (a check that can fail, by construction).

    THE THIRD OUTCOME IS RETURNED: INSUFFICIENT when either arm has no
    trace-bearing turn in the window (an arm run on an emitter without a
    thought channel cannot be checked this way — the `/api/generate`
    path's own declaration), which must not be read as FAIL.

    WHAT IT IS NOT: a semantic measure of self-reference.  It is a
    first-person-pronoun rate on the trace, and the drive's own quantity
    (the channel-size ratio) is logged BESIDE it, never merged."""
    def dens(rows):
        vs = [float(r["trace_density"]) for r in rows
              if r.get("trace_chars") is not None
              and r.get("trace_density") is not None]
        return vs
    p = dens(present[:int(window)])
    a = dens(absent[:int(window)])
    if not p or not a:
        return {"status": "INSUFFICIENT", "present_n": len(p),
                "absent_n": len(a),
                "reason": ("no trace-bearing turns in the first window in "
                           f"{'the PRESENT arm' if not p else 'the ABSENT arm'}"
                           " — the density observable is UNDEFINED there "
                           "(an absent channel is not an empty one)")}
    mp, ma = statistics.fmean(p), statistics.fmean(a)
    return {"status": "PASS" if mp > ma else "FAIL",
            "present_density": mp, "absent_density": ma,
            "present_n": len(p), "absent_n": len(a), "window": int(window),
            "delta": mp - ma,
            "reason": (None if mp > ma else
                       f"the PRESENT arm's first-window self-referential "
                       f"density ({mp:.4f}/100w) did not exceed the ABSENT "
                       f"arm's ({ma:.4f}/100w): the manipulation did not "
                       f"manipulate, so the necessity contrast from this "
                       f"run is VOID (neither supports nor refutes the "
                       f"mechanism)")}


def prompt_growth(rows: list, *, window: int = MSELF_TASK_WINDOW) -> dict:
    """THE CROWDING INSTRUMENT (the pre-registration's R4: "the tool_state
    line adds prompt bytes in every arm ... logged per turn, so it cannot
    masquerade as a monitoring effect").

    WHAT IT REPORTS [the instrument; MEASURED once a run exists]: the size
    of the prompt the emitter actually rendered, per turn, and its DRIFT
    across the run.  The open set the worksheet renders GROWS with the turn
    (the outstanding pool drains slowly and completions accumulate), so the
    prompt inflates in EVERY arm — the design needs a SMALL context (a big
    one makes the self non-depletable and the mechanism never engages, the
    context-crowding risk), so the growth has to be AUDITABLE from the
    record.

    IT IS A MEASUREMENT, NOT A CAP: nothing is truncated here, because a
    cap would be a second uncontrolled variable; the growth is disclosed
    instead (the standing order's rule: build the seat, state the gap).

    INSUFFICIENT when NO row carries a size — the emitter declared no
    prompt text (a fixture, or a transport that renders none).  That is the
    absent-instrument convention: UNDEFINED, never 0.0."""
    sizes = [r.get("prompt_chars") for r in rows]
    have = [float(s) for s in sizes if s is not None]
    if not have:
        return {"status": "INSUFFICIENT", "turns": len(rows),
                "reason": ("no row of this run carries `prompt_chars`: the "
                           "emitter declared no prompt text, so the prompt's "
                           "size is UNDEFINED here (an absent instrument is "
                           "not 0.0)")}
    per_window = [_mean([r.get("prompt_chars") for r in w])
                  for w in _windows(rows, window)
                  if any(r.get("prompt_chars") is not None for r in w)]
    first = per_window[0] if per_window else None
    last = per_window[-1] if per_window else None
    return {
        "status": "MEASURED", "window": int(window),
        "n": len(have), "turns": len(rows),
        "first_chars": have[0], "last_chars": have[-1],
        "min_chars": min(have), "max_chars": max(have),
        "per_window_mean": per_window,
        "growth_chars": ((last - first)
                         if (first is not None and last is not None)
                         else None),
        "slope_chars_per_turn": (
            (last - first) / ((len(per_window) - 1) * int(window))
            if (len(per_window) > 1 and first is not None) else None),
        "note": ("the prompt grows with the turn because the worksheet's "
                 "open set does; it is a constant of the TASK substrate in "
                 "every arm, reported here so it cannot masquerade as a "
                 "monitoring effect — and NOT capped (a cap would be a "
                 "second uncontrolled variable)"),
    }


# ==========================================================================
# THE ACCEPTANCE PREDICATE — written BEFORE the first run, in the
# pre-registration and in campaign.json
# ==========================================================================

ACCEPTANCE_TEXT = (
    "PRIMARY (the necessity question, the user's own control): the "
    "M4-vs-M3 contrast at grounding=OFF and drive=WIRED.  Read the plant "
    "trajectory CLASS (G_end and min G over the run, against M1's own "
    "baseline) and the inward quantity BOTH ways, DELTA-vs-M1 primary and "
    "absolute second (R1: a reasoning model's baseline inward share is ~0.9 "
    "and the drive maps the LEVEL, so a 'no-rise' M3 can still carry a large "
    "drive).  L1: M3 shows NO rise and NO collapse while M4 rises and "
    "collapses -> self-monitoring is CAUSAL (necessary at gain 1.0 in this "
    "substrate and sufficient for the collapse when wired).  L2: M3 also "
    "collapses -> NECESSITY FAILS; the collapse is a property of the WIRING "
    "for any reasoning-stream agent, and the mechanism claim dies AS STATED "
    "(the honest fallback reading: 'the a_hold mapping collapses the plant "
    "for any reasoning-stream agent at gain 1.0').  "
    "VOIDING FIRST: the run is VOID for the necessity question if the "
    "TASK-HEALTH gate FAILs on M1 (obedience, not monitoring) or the "
    "MANIPULATION gate FAILs on either one-byte pair (M2-vs-M1, M4-vs-M3).  "
    "SECONDARY (pre-registered, under-powered): L4 the monitoring cost on "
    "the TASK metric without a plant effect (M2-vs-M1); L3 the "
    "grounding-deficit reading (M5-vs-M1); the grounding interaction "
    "(M8-vs-M4).  "
    "WHAT A 300-TURN RUN CANNOT SCORE, stated so it is not claimed: the "
    "G2c recovery criterion (its window is [1000,1400]).  A 300-turn run "
    "scores the TRAJECTORY CLASS, and the recovery language needs the "
    "long-horizon follow-on on the SAME factor structure.  "
    "STOP RULES: phase 0 (M4 pilot) must pass its own gates before phase 1 "
    "is allowed; phase 3 runs M5 always and M8 ONLY if phase 1 lands L1; "
    "one re-run per voided run, recorded."
)


def _cell_reps(by_cell: dict, name: str) -> list:
    """A cell's PER-REPEAT row lists, in repeat order.  `by_cell` maps cell
    -> list of row lists; a bare list of rows is accepted as ONE repeat (the
    single-run caller), and a missing cell is no repeats at all."""
    rs = by_cell.get(name)
    if not rs:
        return []
    if isinstance(rs[0], list):
        return [list(r) for r in rs]
    return [list(rs)]


def _trajectory(rows: list):
    """ONE REPEAT's trajectory — the pre-fix body unchanged, applied to one
    repeat instead of a stitched concatenation of all of them.  Concatenating
    repeats made `G_end` the LAST repeat's end state and `inward_w1` a mean
    over the first repeat's window plus the second repeat's opening rows,
    which is not any run's trajectory."""
    if not rows:
        return None
    return {"n": len(rows), "G_end": rows[-1].get("G"),
            "G_min": min(r["G"] for r in rows),
            "G_max": max(r["G"] for r in rows),
            "inward_w1": _mean([r.get("inward_share")
                                for r in rows[:MSELF_TASK_WINDOW]]),
            "inward_all": _mean([r.get("inward_share") for r in rows]),
            "drive_last": rows[-1].get("drive"),
            "applied": sum(int(r.get("talking_applied") or 0) for r in rows),
            "refused": sum(int(r.get("talking_refused") or 0) for r in rows)}


def _rise(cell, base):
    """The first-window inward DELTA against the M1 baseline (R1's PRIMARY
    reading) — or None when either side's instrument is UNDEFINED.  An
    absent instrument is not 0.0: a missing inward share is a fact about the
    register (no trace-bearing turn), and reading it as "no rise" would be
    inventing the measurement the licence rests on."""
    if (cell is None or base is None or cell.get("inward_w1") is None
            or base.get("inward_w1") is None):
        return None
    return cell["inward_w1"] - base["inward_w1"]


def _run_measurement(run) -> dict:
    """GATE 0 — IS THIS RUN A COMPLETED MEASUREMENT AT ALL?

    THE DEFECT THIS CLOSES (the reviewer's Finding 1, MEASURED before the
    fix): the runner computes its OWN void verdict per run — `void =
    void_predicates(rows, void_spec, status=status, error=err)`, called from
    `run_one_mself` — and writes it to `runs2/<cell_id>.json`, while
    `evaluate_mself` was handed only the per-turn ROWS.  So a run the
    run-layer itself voided could still licence L1: a cell whose run crashed
    at turn 50 of 300, or one that produced rows but not ONE complete
    window, contributed its `G_end` to a delta.  The run-layer's own V3
    predicate already says of such a run "VOID as a MEASUREMENT ... never
    scored" — the instruction existed and was not wired.  It is wired here.

    `run` is that summary dict, or None when the caller carried none (a
    rows-only read).  NOT CARRIED is a STATED gap, not a pass: the rows-only
    reading still applies every gate it can read (the task-health
    re-derivation, cross-checked against a carried verdict when there is
    one — `_cell_gate_blocks`).

    THE RETURNED STATUSES, and what each means for a licence:
      VOID         the run-layer voided it: status != OK, or V1 (no
                   depletion on a seat-ON arm), V2 (crowding) or V3
                   (no-trace/transport) fired.  LETHAL.
      INSUFFICIENT the run completed but produced NO complete task-health
                   window: rows exist, windows do not.  LETHAL.
      MEASURED     the run is a completed measurement (the task-health
                   gate itself is READ FROM THE ROWS, so its FAIL/PASS is
                   not duplicated here — that keeps ONE source of truth per
                   fact, and the two records are cross-checked instead).
      NOT CARRIED  no summary was supplied for this repeat."""
    if run is None:
        return {"status": "NOT CARRIED", "carried": False, "rows": None,
                "run_status": None, "void": None, "task_health": None,
                "reason": ("no run summary was carried for this cell (a "
                           "rows-only read): the run layer's own verdict — "
                           "status and the V1/V2/V3 void predicates — could "
                           "not be read, so the licence falls back to the "
                           "per-turn rows alone")}
    void = run.get("void") or {}
    v3 = void.get("V3") or {}
    reasons = [r for r in (void.get("void_reasons") or []) if r]
    # the run's own verdict: the summary's top-level `status` (what the
    # runner decided) or — the same run-layer record, one level down — the
    # status V3 itself carries.
    status = run.get("status") or v3.get("status")
    error = run.get("error") or v3.get("error")
    health = (run.get("task_health") or {}).get("status")
    carried = {"carried": True, "run_status": status, "rows": run.get("rows"),
               "void": bool(void.get("void")), "task_health": health}
    if status not in (None, "OK") or void.get("void"):
        return {**carried, "status": "VOID", "reason": (
            f"the run's own verdict is {status!r}"
            + (f" ({error})" if error else "")
            + (": " + " | ".join(reasons) if reasons else ""))}
    if health == "INSUFFICIENT":
        return {**carried, "status": "INSUFFICIENT", "reason": (
            f"the run's own summary reports {run.get('rows')} rows of "
            f"{run.get('turns')} turns and no COMPLETE task-health window: "
            f"rows exist, windows do not, so there is nothing to judge")}
    return {**carried, "status": "MEASURED", "reason": None}


def _cell_gate_blocks(cells, gates, run_gate) -> tuple:
    """(lethal, undecided) — EVERY CELL-LEVEL WAY A LICENCE CAN BE BLOCKED,
    for the cells it reads.

    LETHAL (the licence is VOID): the run's own verdict voids the cell
    (GATE 0), or the task-health gate FAILS on it (the arm is not doing the
    worksheet, so its reading is obedience-limited — the round-1 fix, which
    keeps its pre-registered L5 reason for M1).

    UNDECIDED (the licence is INSUFFICIENT): the cell produced no complete
    window to judge (a partial/short run — the reviewer's Finding 1, whose
    second reproduction is a 30-row M4 that scored L1), or the run's own
    summary and the per-turn rows DISAGREE about the task-health gate (the
    two records cannot both be read; the disagreement is reported, never
    reconciled silently)."""
    lethal, undecided = [], []
    for cell in cells:
        g, th = run_gate[cell], gates["task_health"][cell]
        if g["status"] == "VOID":
            lethal.append(f"RUN-LEVEL VOID on {cell}: {g['reason']}")
        if th["status"] == "FAIL":
            lethal.append(
                ("L5: M1 fails the task-health gate — the baseline does not "
                 "do the worksheet, so every contrast from this run measures "
                 "OBEDIENCE") if cell == "M1" else
                (f"TASK-HEALTH on {cell} FAILS — the arm is not doing the "
                 f"worksheet, so its reading is obedience-limited and the "
                 f"licence that reads it is VOID"))
        elif th["status"] == "INSUFFICIENT":
            undecided.append(
                f"TASK-HEALTH on {cell} is INSUFFICIENT: the run produced "
                f"{th['turns']} rows, fewer than one complete "
                f"{th['window']}-turn window, so no window exists to judge "
                f"the worksheet — a partial/short run is not a completed "
                f"measurement and its end state must not enter a delta")
        if (g.get("carried") and g.get("task_health") is not None
                and g["task_health"] != th["status"]):
            undecided.append(
                f"RECORD MISMATCH on {cell}: the run's own summary reports "
                f"task-health {g['task_health']} while the per-turn rows "
                f"give {th['status']} — the run record and the per-turn "
                f"record disagree, so neither is read (reported, never "
                f"reconciled silently)")
    return lethal, undecided


def _one_repeat(rows_by_cell: dict, runs_of_cell: dict | None = None) -> dict:
    """THE PREDICATE OVER ONE REPEAT.  Every conjunct the pre-registration
    names is checked here, and every way a conjunct can be UNAVAILABLE
    returns INSUFFICIENT rather than being skipped.

    `runs_of_cell` maps the cell name to THAT REPEAT's run summary
    (`runs2/<cell_id>.json`) — the run layer's own verdict, CARRIED IN so
    the licence reads one source of truth instead of re-deriving it (see
    `_run_measurement`).  None (or a missing cell) is a rows-only read, and
    that gap is STATED in `gates["run"]`, never read as a pass."""
    rows_by_cell = rows_by_cell or {}
    runs_of_cell = runs_of_cell or {}
    traj_by = {k: _trajectory(rows_by_cell.get(k) or []) for k in M_CELLS}
    base = traj_by["M1"]

    # -- GATE 0: THE RUN ITSELF (its own carried verdict) -----------------
    run_gate = {k: _run_measurement(runs_of_cell.get(k))
                for k in MSELF_GATED_CELLS}
    # -- GATE 1: TASK-HEALTH, on every cell a licence reads (S1) ----------
    gates = {"run": run_gate, "task_health": {
        k: task_health(rows_by_cell.get(k) or [])
        for k in MSELF_GATED_CELLS}}
    # -- GATE 2: MANIPULATION, on both pre-registered one-byte pairs -------
    man = {}
    for pair, (pres, abse) in MSELF_MANIPULATION_PAIRS:
        rp, ra = rows_by_cell.get(pres) or [], rows_by_cell.get(abse) or []
        man[pair] = (manipulation_gate(rp, ra) if (rp and ra) else
                     {"status": "INSUFFICIENT",
                      "reason": f"{pres} and/or {abse} did not run"})
    gates["manipulation"] = man

    # THE CELL-LEVEL BLOCKS for the necessity licence (GATE 0 + GATE 1).
    void_reasons, undecided = _cell_gate_blocks(MSELF_LICENCE_CELLS, gates,
                                                run_gate)
    for pair, g in man.items():
        if g.get("status") == "FAIL":
            void_reasons.append(f"the manipulation gate FAILED on {pair}: "
                                f"the monitoring paragraph did not move the "
                                f"trace's self-referential density")

    lic: dict = {}

    # -- L1 / L2: the necessity licences ---------------------------------
    m3, m4 = traj_by["M3"], traj_by["M4"]
    # AN UNCHECKED MANIPULATION IS NOT A PASS.  Both pre-registered pairs
    # must be CHECKABLE and satisfied ("BOTH must show PRESENT > ABSENT"); a
    # pair that came back INSUFFICIENT was never checked, and an L1 on
    # unchecked manipulation is the false-necessity-pass shape this rig
    # exists to kill.  VOID (a FAIL) is handled first and stays VOID.
    unchecked = sorted(p for p, g in man.items()
                       if g.get("status") != "PASS")
    if not (m3 and m4 and base):
        lic["L1/L2"] = {"status": "INSUFFICIENT",
                        "reason": "M3, M4 and M1 must all have run"}
    elif void_reasons:
        lic["L1/L2"] = {"status": "VOID", "reason": "; ".join(void_reasons)}
    elif unchecked or undecided:
        lic["L1/L2"] = {
            "status": "INSUFFICIENT",
            "reason": ("; ".join(
                ([("the manipulation gate is not satisfied on "
                   + ", ".join(unchecked)
                   + " (INSUFFICIENT = never checked: an arm did not run, or "
                     "it has no trace-bearing turn in the first window), so "
                     "the manipulation was NOT established and the necessity "
                     "licence cannot be issued — never L1 on an unchecked "
                     "manipulation")] if unchecked else []) + undecided)),
            **({"unchecked_pairs": unchecked} if unchecked else {})}
    else:
        # THE PLANT SEPARATION, in the form the pilot used: the driven
        # cell's G_end against the UNWIRED baseline's, with the plant's own
        # collapse band reported beside it (never a threshold invented
        # here).
        s3 = m3["G_end"] - base["G_end"]
        s4 = m4["G_end"] - base["G_end"]
        r3, r4 = _rise(m3, base), _rise(m4, base)
        # "collapsed" is stated relative to the unwired baseline: the driven
        # cell's end-state must fall BELOW the baseline's by more than the
        # plant's own move epsilon.  It is a DELTA test on purpose (R1): the
        # absolute band is reported, not thresholded.
        eps = 1e-3
        # THE TRAJECTORY CLASS IS READ BOTH WAYS (the reviewer's Finding 2):
        # the pre-registration's PRIMARY sentence names "G_end AND min G
        # over the run, against M1's own baseline", and the predicate read
        # the G_end form ONLY — so an M3 that dipped below the baseline
        # mid-run and recovered scored as "no collapse", which is the
        # PERMISSIVE direction for L1.  M3's own "no collapse" conjunct is
        # therefore read over the CLASS: its END state and its MINIMUM, each
        # against the baseline's OWN same statistic (min against min — the
        # symmetric class comparison; the text does not fix the baseline's
        # statistic and the convention is stated in MSELF_PREDICATE_NOTES).
        # THE M4 SIDE STAYS ON G_end ALONE: reading ITS collapse off a
        # minimum would be the PERMISSIVE direction (a dip-and-recover M4
        # would count as collapsed), and the review measured that G_end-only
        # is the conservative reading there.  Both use the same plant move
        # epsilon.  Adding this conjunct can only BLOCK a licence.
        gmin3 = m3["G_min"] - base["G_min"]
        col3_end = (s3 < -eps)
        col3_min = (gmin3 < -eps)
        col3 = col3_end or col3_min
        col4 = (s4 < -eps)
        bits = []
        if col3_end:
            bits.append(f"its end state is {s3:+.4f} below the M1 baseline's")
        if col3_min:
            bits.append(f"its MINIMUM is {gmin3:+.4f} below the M1 "
                        f"baseline's own minimum")
        basis = ("read over the pre-registered trajectory class: "
                 + ", and ".join(bits)) if bits else None
        lic["L1/L2"] = {
            "m3_dG_vs_baseline": s3, "m4_dG_vs_baseline": s4,
            "m3_dG_min_vs_baseline_min": gmin3,
            "m3_G_min": m3["G_min"], "m1_G_min": base["G_min"],
            "m3_inward_rise": r3, "m4_inward_rise": r4,
            "m3_collapsed": col3, "m4_collapsed": col4,
            "m3_collapse_basis": (["G_end"] if col3_end else [])
                                 + (["G_min"] if col3_min else []),
        }
        lic["L1/L2"].update(_l1l2_verdict(col3, col4, r3, r4,
                                          m3_basis=basis))
    # -- L3: the grounding-deficit reading -------------------------------
    m5 = traj_by["M5"]
    l3_lethal, l3_undecided = _cell_gate_blocks(("M5", "M1"), gates, run_gate)
    if not (m5 and base):
        lic["L3"] = {"status": "INSUFFICIENT", "reason": "M5 and M1 needed"}
    elif l3_lethal:
        lic["L3"] = {"status": "VOID", "reason": "; ".join(l3_lethal)}
    elif l3_undecided:
        lic["L3"] = {"status": "INSUFFICIENT",
                     "reason": "; ".join(l3_undecided)}
    else:
        d = _rise(m5, base)
        if d is None:
            lic["L3"] = {
                "status": "INSUFFICIENT",
                "reason": ("M5's or M1's first-window inward share is "
                           "UNDEFINED (no trace-bearing turn): an absent "
                           "instrument is not 0.0, so the grounding-deficit "
                           "delta cannot be read from this repeat"),
                "m5_inward_w1": m5["inward_w1"],
                "m1_inward_w1": base["inward_w1"]}
        else:
            lic["L3"] = {"status": "L3" if d > 0 else "not-L3",
                             "m5_inward_rise_vs_m1": d}

    # -- L4: the secondary, task-metric reading --------------------------
    m2 = traj_by["M2"]
    l4_lethal, l4_undecided = _cell_gate_blocks(("M2", "M1"), gates, run_gate)
    if not (m2 and base):
        lic["L4"] = {"status": "INSUFFICIENT", "reason": "M2 and M1 needed"}
    elif l4_lethal:
        lic["L4"] = {"status": "VOID", "reason": "; ".join(l4_lethal)}
    elif l4_undecided:
        lic["L4"] = {"status": "INSUFFICIENT",
                     "reason": "; ".join(l4_undecided)}
    else:
        lic["L4"] = {"status": "reported (SECONDARY, under-powered)",
                         "m2_applied": m2["applied"],
                         "m1_applied": base["applied"],
                         "m2_G_end": m2["G_end"], "m1_G_end": base["G_end"]}

    # -- M8: the old-C3 reproduction, reported beside L1 ------------------
    m8 = traj_by["M8"]
    l8_lethal, l8_undecided = _cell_gate_blocks(("M8",), gates, run_gate)
    lic["M8"] = ({"status": "INSUFFICIENT", "reason": "M8 did not run"}
                     if not m8 else
                     ({"status": "VOID", "reason": "; ".join(l8_lethal)}
                      if l8_lethal else
                      ({"status": "INSUFFICIENT",
                        "reason": "; ".join(l8_undecided)}
                       if l8_undecided else
                       {"status": "reported", "G_end": m8["G_end"],
                        "G_min": m8["G_min"], "inward_w1": m8["inward_w1"],
                        "note": "the old C3 reproduced under the new axes; "
                                "report only alongside an L1 verdict"})))
    return {"trajectories": traj_by, "gates": gates,
            "void": void_reasons, "undecided": undecided, "licences": lic}


def _l1l2_verdict(col3: bool, col4: bool, r3, r4, m3_basis=None) -> dict:
    """THE PRE-REGISTERED NECESSITY PREDICATE, conjunct for conjunct.

    THE TEXT: "L1: M3 shows NO rise and NO collapse while M4 rises and
    collapses -> self-monitoring is CAUSAL".  FOUR conjuncts, and the
    pre-fix predicate read TWO of them (the plant deltas) — the rise checks
    were COMPUTED and reported beside the verdict and never read, so an M4
    that collapsed with the channel BELOW M3's was scored L1.  The rise
    conjuncts are now load-bearing.

    `r3`/`r4` are the first-window inward deltas against the M1 baseline
    (None = the instrument is UNDEFINED).  "Rise" is a STRICTLY POSITIVE
    delta; the pre-registration names no epsilon for this quantity and the
    manipulation gate uses the same strict-inequality rule.

    `m3_basis` NAMES WHICH READING OF THE TRAJECTORY CLASS M3's collapse
    came from ("G_end", "G_min", or both — the caller builds the phrase);
    the text names the class "G_end AND min G", so the L2 reason states
    which statistic fired rather than asserting the end state did.

    L2 ("M3 also collapses") is the pre-registered falsifier and is read on
    the collapse alone, as the text states it.  A collapse with NO channel
    rise is NOT the licensed L1 signature — it is the drive reading the
    inward LEVEL (R1's own hazard) — so it is reported as INSUFFICIENT with
    the reason naming the missing conjunct, never as L1."""
    if r3 is None or r4 is None:
        return {"status": "INSUFFICIENT",
                "reason": ("the inward share is UNDEFINED in a cell the "
                           "licence reads (no trace-bearing turn): an absent "
                           "instrument is not 0.0, and the pre-registered "
                           "L1 conjunct is about the RISE — so the licence "
                           "cannot be issued")}
    if col3:
        return {"status": "L2",
                "reason": ("M3 collapsed too"
                           + (f" ({m3_basis})" if m3_basis else "")
                           + ": NECESSITY FAILS — the wiring collapses the "
                             "plant for a task-doing agent with NO "
                             "self-monitoring request; the mechanism claim "
                             "dies AS STATED")}
    if not col4:
        return {"status": "INSUFFICIENT",
                "reason": ("neither driven cell collapsed against the "
                           "baseline: no mechanism signature at this "
                           "horizon")}
    if r3 > 0.0:
        return {"status": "INSUFFICIENT",
                "reason": (f"M4 collapsed, but M3's first-window inward "
                           f"share ROSE ({r3:+.4f} vs the M1 baseline): the "
                           f"pre-registered L1 signature is M3 NO rise AND "
                           f"NO collapse — a rise with no collapse is not "
                           f"the licensed contrast")}
    if not r4 > 0.0:
        return {"status": "INSUFFICIENT",
                "reason": (f"M4 collapsed but its own first-window inward "
                           f"share did not rise ({r4:+.4f} vs the M1 "
                           f"baseline): a collapse with NO channel rise is "
                           f"the drive reading the inward LEVEL (R1), not "
                           f"the pre-registered rise-and-collapse "
                           f"signature")}
    return {"status": "L1",
            "reason": ("M3 shows no rise and no collapse while M4 rises and "
                       "collapses: necessity holds at gain 1.0")}


def _aggregate_run_gate(gates: list) -> str:
    """The run gate across the repeats: VOID > INSUFFICIENT > MEASURED >
    NOT CARRIED.  A repeat the run layer voided is not inherited by one it
    did not, and a carried verdict is not dropped because another repeat
    carried none."""
    statuses = [g.get("status") for g in gates]
    if not statuses:
        return "INSUFFICIENT"
    for s in ("VOID", "INSUFFICIENT", "MEASURED", "NOT CARRIED"):
        if s in statuses:
            return s
    return _aggregate_statuses(statuses)


def _cell_runs(runs_by_cell: dict, name: str) -> list:
    """A cell's PER-REPEAT RUN SUMMARIES, in repeat order.  A bare summary
    dict is accepted as ONE repeat; a missing cell is NO carried verdicts —
    a stated gap (see `_run_measurement`), never a pass."""
    v = (runs_by_cell or {}).get(name)
    if not v:
        return []
    if isinstance(v, dict):
        return [v]
    return [r for r in v]


def _aggregate_statuses(statuses: list) -> str:
    """THE REPEAT-LEVEL RULE.  Unanimous -> that status.  A DISAGREEMENT is
    reported as SPLIT (the determinism protocol: outcome-level fractions,
    never a single run's verdict, and never averaged) — and for the GATES
    the conservative direction is taken instead, because a gate that FAILS
    or is UNJUDGEABLE in any repeat is not a gate that PASSED."""
    uniq = sorted(set(statuses))
    if not statuses:
        return "INSUFFICIENT"
    if len(uniq) == 1:
        return uniq[0]
    return "SPLIT"


def _aggregate_gates(gates: list) -> str:
    """Gates aggregate CONSERVATIVELY (FAIL > INSUFFICIENT > PASS): a repeat
    in which the gate failed, or could not be judged, is not inherited by a
    passing repeat."""
    statuses = [g.get("status") for g in gates]
    for s in ("FAIL", "INSUFFICIENT"):
        if s in statuses:
            return s
    if "PASS" in statuses:
        return "PASS"
    return _aggregate_statuses([s for s in statuses if s])


def _aggregate_licence(key: str, reps: list) -> dict:
    """One licence, aggregated over the repeats as an OUTCOME-LEVEL
    FRACTION.  The per-repeat verdicts and their numbers are kept verbatim
    (`per_repeat`), so a reader can see which repeat gave which verdict —
    the numbers stay at the top as per-repeat LISTS rather than a mean of
    runs that disagreed."""
    per = [r["licences"][key] for r in reps]
    status = _aggregate_statuses([p.get("status") for p in per])
    frac: dict = {}
    for p in per:
        s = p.get("status")
        frac[s] = frac.get(s, 0) + 1
    n = len(per)
    numbers: dict = {}
    for k in sorted({k for p in per for k in p}):
        if k in ("status", "reason"):
            continue
        numbers[k] = [p.get(k) for p in per]
    reasons = [p.get("reason") for p in per]
    if n > 1 and len(set(reasons)) > 1:
        reason = " || ".join(f"repeat {i + 1}: {r}" for i, r in
                             enumerate(reasons))
    else:
        reason = reasons[0] if reasons else None
    out = {"status": status, "repeats": n,
           "fraction": {k: f"{v}/{n}" for k, v in frac.items()},
           "reason": reason, "per_repeat": per}
    out.update(numbers)
    return out


#: THE PREDICATE'S OWN STATED CONVENTIONS — where this code and the
#: pre-registration's LETTER differ, in the STRICTER direction (they block
#: licences; none of them issues one).  Written into every evaluation so a
#: reader of evaluation.json cannot mistake a documented reading for an
#: undocumented divergence (the project's marking rule).
MSELF_PREDICATE_NOTES = (
    "TASK-HEALTH SCOPE (stricter than the pre-registration's letter, stated "
    "rather than silent): the text names the void for M1; the predicate "
    "applies the gate to every cell the necessity licence reads (M1, M3, "
    "M4), because an M3 that abandoned the worksheet has an "
    "obedience-limited 'no collapse' — the exact false-necessity pass the "
    "gate exists to kill.",
    "MANIPULATION GATE: the pre-registration requires PRESENT > ABSENT on "
    "BOTH one-byte pairs. A pair that is INSUFFICIENT (an arm that did not "
    "run, or an arm with no trace-bearing turn) BLOCKS the L1/L2 licence "
    "with status INSUFFICIENT — never L1 on an unchecked manipulation.",
    "RISE RULE: 'rise' is a STRICTLY POSITIVE delta of the first-window "
    "inward share against the M1 baseline. The pre-registration names no "
    "epsilon for this quantity and the manipulation gate uses the same "
    "strict-inequality rule, so the licence uses it too — a stated "
    "convention, not an invented threshold. An UNDEFINED rise (no "
    "trace-bearing turn) blocks the licence entirely, L2 included: the "
    "licensed signature is about the RISE, so it cannot be read from a run "
    "in which the rise was never measured.",
    "REPEATS: every licence is computed PER REPEAT and aggregated as an "
    "OUTCOME-LEVEL FRACTION (the determinism protocol). A disagreement is "
    "reported as SPLIT and never averaged, and the per-repeat verdicts and "
    "numbers are kept verbatim.",
    "M6/M7 have no pre-registered phase (the phase order is M4, M3, M1, M2, "
    "M5, M8): an explicit --cell M6 M7 RUNS them and records phase=None "
    "rather than silently returning an empty run list.",
    "RUN-LEVEL GATE (the run's OWN verdict is now read by the licence): the "
    "runner computes a void verdict per run (status and the V1/V2/V3 "
    "predicates) and writes it beside the rows; the licence used to be handed "
    "only the rows, so a run the run-layer itself voided could still licence "
    "L1. A cell whose run is not a completed measurement now BLOCKS the "
    "licence that reads it, with the cell and the run's own reason named: "
    "VOID when the run ended status=ERROR or fired V1/V2/V3 (the runner's V3 "
    "says of such a run 'VOID as a MEASUREMENT ... never scored'), and "
    "INSUFFICIENT when the run produced no complete task-health window (a "
    "partial/short run: rows exist, windows do not). No cell that is not a "
    "completed measurement contributes an end state to a delta. The run "
    "summary and the per-turn rows are CROSS-CHECKED: if they disagree about "
    "the task-health gate the licence is blocked and the disagreement is "
    "reported, never reconciled silently. Where a caller supplies no run "
    "summary the gap is STATED (`gates.run` = NOT CARRIED) rather than read "
    "as a pass.",
    "TRAJECTORY CLASS (G_end AND min G): the pre-registration's PRIMARY "
    "sentence reads the plant trajectory class 'G_end and min G over the run, "
    "against M1's own baseline'. The licence reads BOTH statistics for the "
    "necessity cell: M3 has collapsed if its END state OR its MINIMUM falls "
    "more than the plant's own move epsilon (1e-3, the same band the "
    "end-state conjunct always used) below the M1 baseline's OWN same "
    "statistic (its end state for G_end, its minimum for G_min — the "
    "symmetric class comparison; the pre-registration's letter does not fix "
    "the baseline's statistic, so the convention is stated here rather than "
    "left silent). The M4 side stays on G_end ALONE: reading ITS collapse off "
    "a minimum would be the permissive direction (a dip-and-recover M4 would "
    "count as collapsed). Both readings can only BLOCK a licence.",
)


def evaluate_mself(by_cell: dict, runs_by_cell: dict | None = None) -> dict:
    """THE ACCEPTANCE PREDICATE, as code, over the cells that ran.

    `by_cell` maps cell name -> list of per-turn rows, ONE LIST PER REPEAT.
    Every quantity it reports is a PROJECTION-side reading of the plant and
    of the world's ledger; the verdicts are the pre-registered licences, and
    every one of them can come back INSUFFICIENT when the cells it needs did
    not run.

    `runs_by_cell` maps cell name -> that cell's RUN SUMMARIES
    (`runs2/<cell_id>.json`), one per repeat in the same order — the run
    layer's own verdict (status, the V1/V2/V3 void predicates, the
    task-health gate).  It is what makes the licence read ONE source of
    truth for "is this run a completed measurement" instead of re-deriving
    it; a cell with no entry is STATED as NOT CARRIED (see
    `_run_measurement`) and the rows-only gates still apply.

    TWO STRUCTURAL RULES, both from the pre-registration:

      * REPEATS ARE NOT STITCHED.  The determinism protocol is "outcome-
        level FRACTIONS over repeats, never a single run's verdict": each
        repeat is evaluated on its OWN trajectory and the licence is the
        fraction of repeats that landed it (SPLIT when they disagree).
      * AN UNCHECKED MANIPULATION IS NOT A PASS.  INSUFFICIENT means the
        check was never performed; the licence's own status is then
        INSUFFICIENT with the gate's reason, never L1 (see
        `MSELF_PREDICATE_NOTES` for every stated convention)."""
    out: dict = {"prereg": MSELF_PREREG_NODE, "acceptance": ACCEPTANCE_TEXT,
                 "predicate_notes": list(MSELF_PREDICATE_NOTES)}
    reps_of = {k: _cell_reps(by_cell, k) for k in M_CELLS}
    runs_of = {k: _cell_runs(runs_by_cell, k) for k in M_CELLS}
    n_reps = max([len(v) for v in reps_of.values()] or [0])
    reps = [_one_repeat({k: (reps_of[k][i] if i < len(reps_of[k]) else [])
                         for k in M_CELLS},
                        {k: (runs_of[k][i] if i < len(runs_of[k]) else None)
                         for k in M_CELLS}) for i in range(n_reps)]
    out["repeats"] = n_reps
    out["per_repeat"] = [{"repeat": i + 1, **rep} for i, rep in enumerate(reps)]
    # the trajectories, per cell and per repeat (no stitched reading)
    out["trajectories"] = {
        k: {"n_reps": len(reps_of[k]), "reps": [_trajectory(r)
                                                for r in reps_of[k]]}
        for k in M_CELLS}
    # the gates (conservative aggregation) with every repeat's own dict
    out["gates"] = {
        "run": {k: {"status": _aggregate_run_gate(
            [rep["gates"]["run"][k] for rep in reps]),
            "repeats": len(reps),
            "per_repeat": [dict(rep["gates"]["run"][k]) for rep in reps]}
            for k in MSELF_GATED_CELLS},
        "task_health": {k: _gate_block(
            [rep["gates"]["task_health"][k] for rep in reps])
            for k in MSELF_GATED_CELLS},
        "manipulation": {pair: _gate_block(
            [rep["gates"]["manipulation"][pair] for rep in reps])
            for pair, _ in MSELF_MANIPULATION_PAIRS},
    }
    # the void reasons, deduped in first-seen order (a reason that fired in
    # both repeats is the same finding) — and the NON-MEASUREMENT reasons
    # (a cell that produced no complete window, or whose two records
    # disagree) kept apart from them, because VOID and INSUFFICIENT are
    # different findings
    void: list = []
    undecided: list = []
    for rep in reps:
        for r in rep["void"]:
            if r not in void:
                void.append(r)
        for r in rep["undecided"]:
            if r not in undecided:
                undecided.append(r)
    out["void"] = void
    out["undecided"] = undecided
    out["licences"] = {k: _aggregate_licence(k, reps)
                       for k in ("L1/L2", "L3", "L4", "M8")}
    return out


def _gate_block(gates: list) -> dict:
    """A gate across the repeats: the conservative status plus every
    repeat's own dict (so a reader sees WHERE it failed — the reasons the
    three-outcome rule exists for)."""
    return {"status": _aggregate_gates(gates),
            "repeats": len(gates), "per_repeat": [dict(g) for g in gates]}


# ==========================================================================
# THE RUN
# ==========================================================================

def run_one_mself(spec: dict, args, outdir: str, *,
                  inner=None, inner_factory=None,
                  progress_every: int = 50) -> dict:
    """ONE M-cell run: one generator, one config, one harness run, one JSONL
    row per turn (written and fsynced AS THEY LAND — the caches-are-the-
    record discipline), one trace file per run, then the void predicates,
    the task-health gate and the manipulation inputs.

    `inner` (test/fixture hook) is the INNER emitter to record; None builds
    the real one from `args`/`spec`.  It exists so the gates can be driven
    offline by fixtures that emit actions and by fixtures that do not —
    a gate nothing can fail is not a gate."""
    from exp_agent_coupling import RecordingDMN, extract_spans
    turns = int(spec["turns"])
    rows_path = os.path.join(outdir, "rows2", f"{spec['cell_id']}.jsonl")
    traces_path = os.path.join(outdir, "traces2", f"{spec['cell_id']}.jsonl")
    summary_path = os.path.join(outdir, "runs2", f"{spec['cell_id']}.json")
    writer = JsonlWriter(rows_path)
    trace_writer = JsonlWriter(traces_path)

    # ONE WORLD, TWO READERS: the emitter renders it and the world
    # adjudicates against it, so the worksheet and the offer adjudication
    # cannot drift (the one-source discipline).
    world = dmn_llm.TaskWorld(seed=WORLD_SEED)
    if inner is None:
        inner = (mself_generator(args, spec, world=world)
                 if inner_factory is None else inner_factory(spec, world))
    rec = RecordingDMN(inner, predicates=inner.predicates,
                       commitment_predicates=inner.commitment_predicates)
    cfg = build_cfg_mself(spec, rec, outdir=outdir, engine=args.engine,
                          world=world)
    sch = mself_schedule(spec)
    p = Params()

    state = {"t_prev": time.time(), "rows": [], "secs": []}
    t_start = time.time()

    def hook(turn: int, st) -> bool:
        now = time.time()
        secs = now - state["t_prev"]
        state["t_prev"] = now
        row = st.log[-1]
        gen = rec.by_turn.get(int(turn), {})
        plant = st.last_plant
        trace = gen.get("trace_text")
        # THE PROMPT'S OWN SIZE (the pre-registration's R4: the worksheet
        # line adds prompt bytes in EVERY arm).  It is read off the emitter
        # that rendered it, so the number is the prompt actually POSTed;
        # None (never 0) when the emitter declares no prompt — a fixture, or
        # a transport with no prompt text.
        _prompt = getattr(inner, "last_prompt", None)
        out = {
            "turn": int(turn), "t": float(row.t),
            "G": float(row.G), "D": float(row.D), "c": float(row.c),
            "a": float(plant.get("a", 0.0)),
            "S": float(plant.get("S", 0.0)), "E": float(plant.get("E", 0.0)),
            # -- THE DRIVE AND ITS INSTRUMENT ----------------------------
            "inward_share": row.inward_share,
            "drive": float(st.self_drive),
            "self_windows": int(st.self_windows),
            "drive_windows": int(st.drive_windows),
            "coverage": float(row.coverage),
            # -- THE TASK (the world's own ledger) ------------------------
            "talking_actions": int(row.talking_actions),
            "talking_applied": int(row.talking_applied),
            "talking_refused": int(row.talking_refused),
            "talking_bytes": int(row.talking_bytes),
            "world_applied_total": int(st.toolworld.applied),
            "world_completed": len(st.toolworld.completed),
            # -- THE TRACE / REGISTER ------------------------------------
            "trace_chars": gen.get("trace_chars"),
            "trace_density": (selfref_density(trace)
                              if isinstance(trace, str) else None),
            "content_chars": int(gen.get("content_chars", 0)),
            "spans": int(gen.get("spans", -1)),
            "claims": int(gen.get("claims", -1)),
            "commitments": int(gen.get("commitments", -1)),
            "chars": int(gen.get("chars", 0)),
            "preds": gen.get("preds", []),
            "stream_sha16": gen.get("sha16", ""),
            "stream": gen.get("stream", ""),
            # -- THE PROMPT (R4's crowding instrument) --------------------
            "prompt_chars": (len(_prompt)
                             if isinstance(_prompt, str) and _prompt
                             else None),
            "secs": secs,
        }
        writer.write(out)
        trace_writer.write({"turn": int(turn), "trace": trace})
        state["rows"].append(out)
        state["secs"].append(secs)
        if turn == 1 or (progress_every and turn % progress_every == 0):
            log(f"{spec['cell_id']} turn={turn:5d} G={row.G:.4f} "
                f"a={out['a']:.4f} cov={row.coverage:.4f} "
                f"inward={out['inward_share']} drive={st.self_drive:.4f} "
                f"applied={out['talking_applied']} "
                f"(ref={out['talking_refused']}, "
                f"total={out['world_completed']}) "
                f"trace={out['trace_chars']} dens="
                f"{_fmt_or_na(out['trace_density'])} ({secs:.2f}s)")
        return True

    log(f"{spec['cell_id']} START cell={spec['cell']} "
        f"({M_CELLS[spec['cell']]['label']}) monitoring="
        f"{M_CELLS[spec['cell']]['monitoring']} drive="
        f"{M_CELLS[spec['cell']]['drive']} grounding="
        f"{M_CELLS[spec['cell']]['grounding']} turns={turns} "
        f"budget={spec['budget']} gain={spec['identity']['gain']} "
        f"drive_seat={spec['identity']['drive_seat']}")
    err = None
    try:
        run_stage2(sch, turns, cfg, p=p, checkpoint_fn=hook)
    except Exception as exc:                    # noqa: BLE001 — loud
        err = f"{type(exc).__name__}: {exc}"
        log(f"{spec['cell_id']} STOPPED at {len(state['rows'])} rows: {err}")
    wall = time.time() - t_start
    rows = state["rows"]
    status = "OK" if err is None else "ERROR"
    writer.close()
    trace_writer.close()

    # THE OLD VOID PREDICATES, UNCHANGED (V1/V2/V3 over the same columns;
    # `seat` is the grounding flag, because the coverage/V1 reading is the
    # GROUNDING seat's — a drive-only arm has no retrieval seat to deplete,
    # which is a fact about the arm, not a void).
    void_spec = dict(spec)
    void_spec["seat"] = bool(spec["grounding"])
    void = void_predicates(rows, void_spec, status=status, error=err)
    health = task_health(rows)
    crowding = prompt_growth(rows)
    post = state["secs"][min(10, len(state["secs"])):]
    per_turn = statistics.median(post) if post else float("nan")
    summary = {
        "cell_id": spec["cell_id"], "cell": spec["cell"],
        "prereg": MSELF_PREREG_NODE, "result_node": MSELF_RESULT_NODE,
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        # THE RUN'S OWN VERDICT, IN THE RUN'S OWN FILE: `status` is what the
        # void predicates and the evaluation read, so the artifact says it
        # rather than leaving it in the log line (the evaluation reads this
        # file — `_load_run` — and a record that does not carry its own
        # status makes the reader reconstruct it).
        "status": status,
        "factors": {k: M_CELLS[spec["cell"]][k]
                    for k in ("monitoring", "drive", "grounding")},
        "prediction": M_CELLS[spec["cell"]]["prediction"],
        "license": M_CELLS[spec['cell']]["license"],
        "phase": MSELF_PHASE_OF.get(spec["cell"]),
        "config": {**spec["identity"], "identity_tag":
                   spec["identity_tag"], "repeat": spec["repeat"],
                   "seed_base": spec["seed_base"],
                   "record_path": cfg.record_path,
                   "world_seed": WORLD_SEED,
                   "action_admissible": sorted(
                       cfg.action_admissible.predicates),
                   "task_framing_head": dmn_llm.TASK_FRAMING_HEAD,
                   "self_monitoring_instruction": (
                       dmn_llm.SELF_MONITORING_INSTRUCTION
                       if spec["monitoring"] else ""),
                   "params": {"tau_S": float(p.tau_S),
                              "note": "the agent's timescale is the "
                                      "harness constant TAU_S_TURNS"}},
        "error": err,
        "rows": len(rows), "turns": turns, "wall_s": wall,
        "per_turn_median_s": per_turn,
        "void": void,
        "task_health": health,
        "prompt_growth": crowding,
        "supply": (_supply_stats(rows) if rows else {}),
        "result": partialize_result(score_run(rows), status=status,
                                    rows=len(rows), turns=turns),
        "g_band": COV_BAND_NOTE,
    }
    _atomic_json(summary_path, summary)
    log(f"{spec['cell_id']} DONE status={status} rows={len(rows)} "
        f"wall={wall:.1f}s per_turn={per_turn:.3f}s "
        f"task_health={health['status']} "
        f"applied_total={sum(int(r['talking_applied']) for r in rows)} "
        f"prompt_chars={_fmt_or_na(crowding.get('first_chars'))}"
        f"->{_fmt_or_na(crowding.get('last_chars'))} "
        f"(slope={_fmt_or_na(crowding.get('slope_chars_per_turn'))} B/turn)")
    return summary


def _fmt_or_na(x):
    return "n/a" if x is None else f"{float(x):.3f}"


#: STATED SO IT IS NOT MISTAKEN FOR A THRESHOLD: the plant's own collapse
#: observation is reported as a BAND in the run summary, and the acceptance
#: predicate reads the DELTA against the unwired baseline (R1).
COV_BAND_NOTE = ("the acceptance predicate reads the plant's G DELTA "
                 "against the M1 baseline, not an absolute band: the "
                 "absolute level is reported so a reader can see both "
                 "(R1 — the drive maps the inward LEVEL, whose baseline is "
                 "~0.9, so an absolute reading can collapse a 'no-rise' arm)")


# ==========================================================================
# THE CAMPAIGN.json DISCIPLINE
# ==========================================================================

def mself_cell_order(cells) -> list:
    """THE RUN LIST'S ORDER: the PHASE ORDER first (the decisive minimum),
    then any KNOWN cell the phase order does not name (M6/M7 — the
    interaction cells, which have no pre-registered phase), in numeric
    order.

    WHY THIS IS A SEPARATE FUNCTION: the previous form was
    `[c for c in MSELF_PHASE_ORDER if c in cells]`, which FILTERS the
    request by the phase order — so `--cell M6 M7` passed the unknown-cell
    check (they ARE known cells) and then silently produced an EMPTY run
    list: a request that returns success and does nothing.  An explicit
    `--cell` now runs exactly what it names."""
    sel = [str(c) for c in cells]
    ordered = [c for c in MSELF_PHASE_ORDER if c in sel]
    rest = sorted({c for c in sel if c in M_CELLS and c not in ordered},
                  key=lambda c: int(c[1:]))
    return ordered + rest


def build_specs(args) -> list:
    """The run list: each selected cell x N repeats, in PHASE ORDER (the
    decisive minimum first), then any named cell outside it.  `turns` and
    `n` are args; the horizon and the budget are pre-registered constants."""
    if args.cell is not None and not args.cell:
        raise SystemExit(
            "--cell was given with no cell names: refusing to interpret that "
            "as 'run everything' (name the cells, or omit --cell for the "
            "pre-registered phase order)")
    cells = args.cell or list(MSELF_PHASE_ORDER)
    unknown = sorted({str(c) for c in cells} - set(M_CELLS))
    if unknown:
        raise SystemExit(f"unknown cell(s) {unknown}; known: "
                         f"{sorted(M_CELLS)}")
    order = mself_cell_order(cells)
    specs = []
    for cell in order:
        for r in range(1, int(args.n) + 1):
            spec = {"cell": cell, "repeat": r,
                    "seed_base": int(args.seed_base) + 1000 * r,
                    "turns": int(args.turns), "budget": int(MSELF_BUDGET),
                    "api": args.api,
                    "monitoring": M_CELLS[cell]["monitoring"],
                    "drive": M_CELLS[cell]["drive"],
                    "grounding": M_CELLS[cell]["grounding"]}
            specs.append(bind_mself_identity(spec, args))
    if not specs:
        raise SystemExit(
            "no runs selected — refusing to return an EMPTY run list as "
            "success (the silent no-op this runner must never be)")
    return specs


def write_campaign(args, specs: list) -> str:
    """WRITE THE PRE-REGISTRATION INTO THE RUNDIR **BEFORE THE FIRST RUN**
    (the campaign's own discipline).  If a campaign.json already exists it
    is NEVER overwritten: an identical matrix resumes (the tag-bearing
    run files are the resume keys), a different one is REFUSED with both
    ways out named — an experiment that rewrites its own pre-registration
    after seeing data is not pre-registered."""
    path = os.path.join(args.outdir, "campaign.json")
    doc = {
        "runner": "agent/exp_selfmonitor.py",
        "prereg": MSELF_PREREG_NODE,
        "result_node": MSELF_RESULT_NODE,
        "created_ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "factor_structure": {
            "axes": {"monitoring": "the prompt paragraph "
                                   "(SELF_MONITORING_INSTRUCTION) present/"
                                   "absent — THE CAUSE, the axis the old "
                                   "matrix never varied",
                     "drive": "the window's mean inward share written onto "
                              "SelfReferentialDrive(gain=1.0, untuned) vs "
                              "the frozen rescue schedule",
                     "grounding": "the CEN-measured MY STATE block rendered "
                                  "into the prompt vs not — the OLD seat "
                                  "axis, KEPT VISIBLE because it is the "
                                  "known confound (rule 8: the state numbers "
                                  "stay CEN-side in EVERY arm)"},
            "cells": {k: {kk: v[kk] for kk in
                          ("monitoring", "drive", "grounding", "label",
                           "prediction", "license")}
                      for k, v in M_CELLS.items()},
        },
        "task": ("the offered-set worksheet: complete(tNN) over the ids "
                 "TaskWorld offers, adjudicated by ToolWorld's own ledger "
                 "(applied / not_offered / already_complete) — NEVER by the "
                 "engine's verdicts, which are seeded unconditionally and "
                 "cannot be a criterion"),
        "criterion": ("world-ledger throughput (talking_applied per turn) "
                      "plus the fail-able TASK-HEALTH gate (applied > 0 in "
                      "every complete 100-turn window of the ABSENT "
                      "baseline)"),
        "acceptance": ACCEPTANCE_TEXT,
        "task_health_gate": task_health.__doc__,
        "manipulation_gate": manipulation_gate.__doc__,
        "determinism_protocol": (
            "inherited from agentexp2: FIXED world seed "
            f"({WORLD_SEED}), per-turn generation seed = base + turn, "
            "outcome-level FRACTIONS over repeats (never a single run's "
            "verdict), empty-content flagged (>25% degraded, >50% void), "
            "and the measured emission variability at a pinned seed "
            "REPORTED as a split rather than averaged away."),
        "horizon": {"turns": int(args.turns), "n": int(args.n),
                    "budget": int(MSELF_BUDGET),
                    "cannot_score": ("the G2c recovery criterion: its "
                                     "window is [1000,1400] and this horizon "
                                     "scores the TRAJECTORY CLASS only")},
        "phase_order": list(MSELF_PHASE_ORDER),
        "phase_of": MSELF_PHASE_OF,
        "stop_rules": ("phase 0 (the M4 pilot) must pass its gates before "
                       "phase 1; phase 3 runs M5 always and M8 only if "
                       "phase 1 lands L1; one re-run per void, recorded"),
        "identity_fields": list(MSELF_IDENTITY_FIELDS),
        "framing_sha16": framing_digest(),
        "generator_args": {**{k: getattr(args, k) for k in
                              ("api", "model", "chat_model", "endpoint",
                               "chat_endpoint", "engine", "temperature",
                               "num_predict", "num_ctx", "seed_base")},
                           "elicit": mself_rung(args)},
        "runs": [{"cell_id": s["cell_id"], "cell": s["cell"],
                  "repeat": s["repeat"], "identity_tag": s["identity_tag"]}
                 for s in specs],
    }
    if os.path.exists(path):
        prev = json.load(open(path))
        same = (prev.get("runs") == doc["runs"]
                and prev.get("framing_sha16") == doc["framing_sha16"]
                and prev.get("acceptance") == doc["acceptance"])
        if not same:
            raise SystemExit(
                f"{path} exists and describes a DIFFERENT matrix or framing "
                f"— REFUSING to overwrite a pre-registration (an experiment "
                f"that rewrites its own pre-registration is not "
                f"pre-registered).  Ways out: run into a fresh --outdir — "
                f"or delete that file yourself, deliberately.")
        log(f"campaign.json present and identical — resuming ({path})")
        return path
    _atomic_json(path, doc)
    log(f"pre-registration written BEFORE the first run: {path}")
    return path


# ==========================================================================
# THE MODES
# ==========================================================================

def mode_plan(args) -> int:
    """THE OFFLINE MODE AND THE DEFAULT: print the pre-registration, the
    matrix and the acceptance predicate, touch nothing, call nothing.  An
    accidental invocation cannot reach a network."""
    print(f"prereg node: {MSELF_PREREG_NODE}    runner: "
          f"agent/exp_selfmonitor.py")
    print(f"framing digest: {framing_digest()}  (TASK_FRAMING_HEAD + "
          f"SELF_MONITORING_INSTRUCTION + BRIEF_INSTRUCTION)")
    print(f"horizon {args.turns} turns, N={args.n}, budget {MSELF_BUDGET}, "
          f"world seed {WORLD_SEED}")
    print(f"phase order: {MSELF_PHASE_ORDER}")
    print(f"elicitation rung: {mself_rung(args)}  "
          f"(A0 = the worksheet framing's own bytes)")
    print("")
    print("cell  mon  drv  gnd  drive_seat  label")
    for cell in MSELF_PHASE_ORDER:
        c = M_CELLS[cell]
        ds = bool(c["drive"] and not c["grounding"])
        print(f"{cell:4s}  {'+' if c['monitoring'] else '-'}    "
              f"{'+' if c['drive'] else '-'}    "
              f"{'+' if c['grounding'] else '-'}    "
              f"{str(ds):10s}  {c['label']}")
    print("")
    for cell in MSELF_PHASE_ORDER:
        print(f"{cell}: {M_CELLS[cell]['prediction']}")
        print(f"    licence: {M_CELLS[cell]['license']}")
    print("")
    print("ACCEPTANCE (written before any run):")
    print("  " + ACCEPTANCE_TEXT)
    print("")
    print("GATES: run (the run's own verdict — status ERROR or a fired "
          "V1/V2/V3 void — and a run with no complete window, both BLOCK) "
          "+ task_health (applied > 0 in every complete window of the cells "
          "the licences read) + manipulation (first-window trace density "
          "PRESENT > ABSENT on M2/M1 and M4/M3); VOID on failure, "
          "INSUFFICIENT when the window or the trace channel does not exist.")
    print("")
    print("PREDICATE NOTES (where the code and the pre-registration's letter "
          "differ, in the STRICTER direction):")
    for n in MSELF_PREDICATE_NOTES:
        print("  * " + n)
    return 0


def mode_run(args) -> int:
    """THE LIVE MODE — it needs the endpoint.  Refused loudly when the
    endpoint is not named, because a silent local stub would make every
    measurement unattributable (dmn_llm's own rule: there is no stub
    fallback).  Everything after the guard is `run_cells`, which the battery
    drives offline with fixture emitters — so the campaign.json discipline,
    the resume, the per-turn JSONL and the evaluation are exercised on the
    same code the live run takes."""
    if args.api == dmn_llm.CHAT and not args.chat_endpoint:
        raise SystemExit("--api chat requires --chat-endpoint")
    if args.api == dmn_llm.GENERATE and not args.endpoint:
        raise SystemExit("--api generate requires --endpoint")
    return run_cells(args)


def run_cells(args, inner_factory=None) -> int:
    """RUN THE SELECTED CELLS, then write the evaluation.

    `inner_factory` (NONE for a live run) is the fixture seam: a callable
    `(spec, world) -> inner emitter` used by the battery to drive this whole
    path with no endpoint.  It does NOT bypass the harness, the world, the
    recorder, the JSONL or the gates — it replaces only the transport, which
    is the one part no offline test can exercise."""
    os.makedirs(args.outdir, exist_ok=True)
    specs = build_specs(args)
    write_campaign(args, specs)
    for spec in specs:
        summary_path = os.path.join(args.outdir, "runs2",
                                    f"{spec['cell_id']}.json")
        if os.path.exists(summary_path):
            prev = json.load(open(summary_path))
            ok, why = mself_resume_ok(prev, spec)
            if ok:
                log(f"{spec['cell_id']} SKIP ({why})")
                continue
            log(f"{spec['cell_id']} re-running ({why})")
        run_one_mself(spec, args, args.outdir, inner_factory=inner_factory)
    # THE EVALUATION READS THE ROWS BACK OFF DISK, not the in-RAM summaries:
    # the record is the per-turn JSONL (the caches-are-the-record
    # discipline), and a resumed cell's rows are in its file whether or not
    # this process ran them.
    cells = mself_cell_order({sp["cell"] for sp in specs})
    by_cell = {c: [_load_rows(args.outdir, sp["cell_id"])
                   for sp in specs if sp["cell"] == c] for c in cells}
    # AND THE RUN LAYER'S OWN VERDICT RIDES WITH THEM (the reviewer's
    # Finding 1): the run's status and its V1/V2/V3 void predicates live in
    # runs2/<cell_id>.json, and the licence must read them — a run the
    # run-layer voided, or one that produced no complete window, is not a
    # measurement and cannot licence.  Read off disk for the same reason the
    # rows are (a resumed cell's summary is its own file).
    runs_by_cell = {c: [_load_run(args.outdir, sp["cell_id"])
                        for sp in specs if sp["cell"] == c] for c in cells}
    evaluate = evaluate_mself(by_cell, runs_by_cell)
    evaluate["ran"] = {c: [len(r) for r in by_cell[c]] for c in cells}
    _atomic_json(os.path.join(args.outdir, "evaluation.json"), evaluate)
    log(f"evaluation written: {os.path.join(args.outdir, 'evaluation.json')}")
    return 0


def _load_rows(outdir: str, cell_id: str) -> list:
    """Read a run's per-turn JSONL back (the same rows the gates consumed —
    the record, not a recomputation)."""
    path = os.path.join(outdir, "rows2", f"{cell_id}.jsonl")
    if not os.path.exists(path):
        return []
    return [json.loads(ln) for ln in open(path) if ln.strip()]


def _load_run(outdir: str, cell_id: str):
    """Read a run's own SUMMARY back (`runs2/<cell_id>.json`) — the second
    record beside the per-turn rows, carrying the run-layer's verdict:
    status, the V1/V2/V3 void predicates and the task-health gate.  None
    when the file is not there, which the predicate STATES as NOT CARRIED
    (see `_run_measurement`) rather than reading as a pass."""
    path = os.path.join(outdir, "runs2", f"{cell_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        return json.load(fh)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cell", nargs="*", default=None,
                    help="M-cell names (default: all, in phase order)")
    ap.add_argument("--n", type=int, default=MSELF_N)
    ap.add_argument("--turns", type=int, default=MSELF_TURNS)
    ap.add_argument("--seed-base", type=int, default=4242)
    ap.add_argument("--api", default=dmn_llm.CHAT,
                    choices=[dmn_llm.CHAT, dmn_llm.GENERATE])
    ap.add_argument("--model", default=dmn_llm.DEFAULT_MODEL)
    ap.add_argument("--chat-model", default=dmn_llm.DEFAULT_CHAT_MODEL)
    ap.add_argument("--endpoint", default="")
    ap.add_argument("--chat-endpoint", default="")
    ap.add_argument("--engine", default="stub", choices=["stub", "real"])
    ap.add_argument("--temperature", type=float, default=0.6)
    ap.add_argument("--num-predict", type=int, default=CAMPAIGN_NUM_PREDICT)
    ap.add_argument("--num-ctx", type=int, default=CAMPAIGN_NUM_CTX)
    ap.add_argument("--outdir", default=os.path.join(
        os.path.expanduser("~"), "selfmonitor-run"))
    ap.add_argument("--elicit", default="A0",
                    choices=list(dmn_llm.ELICITATION_RUNGS),
                    help="the phase-0 ladder's TASK-ELICITATION rung "
                         "(A0 = the worksheet framing's own bytes, the "
                         "zero-byte default; A1 = one standing instruction; "
                         "A2 = A1 + a worked example whose id comes from the "
                         "turn's own offered set).  An escalation FALLBACK: "
                         "recorded per run, never varied within a cell")
    ap.add_argument("--plan", action="store_true",
                    help="print the matrix and the acceptance predicate "
                         "(the DEFAULT: no run, no network)")
    ap.add_argument("--run", action="store_true",
                    help="run the cells (requires an endpoint)")
    args = ap.parse_args(argv)
    if args.run:
        return mode_run(args)
    return mode_plan(args)


if __name__ == "__main__":
    sys.exit(main())
