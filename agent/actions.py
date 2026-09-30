"""THE TOOL-CALL LAYER — the FOURTH SPAN CHANNEL, an executable world, and
the TALKING ledger (design decision
`handoff-selfreg-cen-tools-entailment` decision 3; the plan is
`handoff-selfreg-toolcall-plan`).

MARKING throughout (MEASURED / INTERPRETATION / PROJECTION): this module
is a PROJECTION-side seat.  THE ONE THING MEASURED ABOUT THE MODEL HERE
IS A NEGATIVE: the frozen model has NO action term — `dG/dt`'s inputs are
(a, G, E, c, g) and `da/dt`'s are (a_hold, c, u_ext) with `u_ext` read
from the SCHEDULE (dpdr/dpdr/model.py:107-124, verified this pass), so
nothing an agent emits can cause anything in the plant.  Everything below
is therefore an architecture statement ("the CEN gains the task executor
the design records as missing"), never a model-fidelity claim.

THE LAYERING.  DMN --(spans: assertions / proposals / self /
commitments / ACTIONS)--> CEN --(verdicts inward to the store; the
TALKING seam outward)--> HARNESS (= the world) --> plant.  The DMN
SUBMITS; the CEN EMITS; the world APPLIES.  The CEN registers an action
and never checks it (an action is an INTENT, not a claim: looking up
`done(t57)` the moment `complete(t57)` is emitted is the tautology class
the commitments channel already refuses — a test that cannot fail), and
never executes it (the world's job).

Q1 — WHAT A TOOL CALL IS.  A declared ACTION predicate on the existing
trivial span grammar: `complete(tNN)`.  ONE more declared predicate, no
grammar change (`interleave.build_batch(action_predicates=...)`), so the
extractor stays TRIVIAL and REGULAR and every byte-identity property of
the split is untouched (T1).  A routed action span leaves the prose
exactly as a routed assertion does and lands in
`cen.AssertionBatch.actions` — a FOURTH tuple, distinct from
`assertions` (checked: reduction) and `commitments` (registered, scored
at a boundary), because an action must be neither: it must reach the one
component that can act.

Q2 — WHO MAY CALL.  THE ADMISSIBLE-ACTION SET, the exact
`cen.AdmissibleLevers` analogue one domain over: EXTERNALLY owned,
DEFAULT EMPTY ("NOTHING is admissible — no lever has passed a test" ->
here: no action is callable).  With it empty, a `complete(tNN)` span is
a well-formed span that admits to nothing and re-enters the prose
VERBATIM, silently unchecked — no error, no count, no third state to
game (the malformed-span discipline, `handoff-selfreg-interleave`
decision 1).  The mechanism NEVER constructs or edits the set; widening
it is a designer/world act (and a self-widening proposal would be a
`LeverProposal` and hit the C3/C12 gate).  R5 IS RESOLVED BY
DISTINCTION, NOT EXTENSION: R5 externalises SELECTION-on-operating-state
(which of the agent's own claims get checked); an action is a statement
about the WORLD, not a split of the agent's own output.  ACTIONS MAY BE
PROPOSED (emitted as spans) AND ARE ADMITTED EXTERNALLY — the C23/C24
shape (roles may be proposed, assigned externally).  An agent that
chose its own ADMISSIBLE SET would be the R5 violation; the set is not
its to choose.  TWO REFUSAL LAYERS, DELIBERATELY DIFFERENT:
  * SPAN-TIME (inadmissible): SILENTLY UNCHECKED.  Decision 1's total
    split discipline.
  * WORLD-TIME (admissible but the world refuses: target not offered /
    already complete / the universe is undefined): a TYPED REFUSAL on
    the talking stream.  LOUD, because the agent did nothing malformed —
    a silent drop here is an unobservable no-op the agent cannot
    distinguish from success.
THE CONSEQUENCE, STATED.  R6's trigger ("the boundary must be
out-of-process before the mechanism executes CODE", architecture §3a R6)
is NOT yet forced by this layer: v1 actions are DATA applied to
harness-side bookkeeping (no code execution).  The moment an action's
effect is code (C22's SWE vocation), the admissible-action definition,
the held-out definition and the anchor must be out-of-process; the seat
to extend already exists (`agent/boundary_daemon.py`, landed 2026-09-27).

Q3 — WHERE THE COST LANDS (the project forbids mixing units, so this is
the crux of the layer).  C26: `talking = the growth term` of dG/dt —
beta_G*(1-a)*G*(1-G), an EXPRESSION-side quantity with no
reduction-demand semantics.  So:
  * THE EMISSION CHARGE is priced in the substrate's OWN expression unit
    — OUTWARD BYTES: `talking_bytes`, the byte length of the turn's
    RENDERED talking stream (`render_talking`).  This is the SAME unit
    the inward share is already measured in (`selfmodel.inward_share`
    weighs prose against the removed span bytes), so the growth-side and
    inward-side observables are COMMENSURABLE WITH NO CONVERSION
    CONSTANT.  [MEASURED: the two instruments share the unit; the
    growth-vs-backlog co-movement is a PRE-REGISTERED CAMPAIGN
    FALSIFIER (plan F2), not a battery claim.]
  * THE EXECUTION CHARGE is ZERO in v1 and is STATED AS ZERO (the
    standing order's seats-and-gaps rule: build the seat, state the
    honest current value — `circuit == formula == 1` while there are no
    rules is the precedent).  v1's world effect is O(1) dict bookkeeping.
    A future action whose effect is real work (a subprocess, an engine
    txn) must take its price from the EFFECT'S OWN SURFACE (an
    engine-reported derivation count, say) and land in THIS talking
    ledger — never in the C11 check ledger.
  * THE C11 DERIVATION LEDGER IS NEVER CHARGED for an action, in either
    direction: derivations price reduction, and charging expression in
    them is the unit-conversion violation the standing order forbids
    (`# dont compromise the model fidelity to make engineering easier`).
    The talking ledger is LOG-ONLY (S10's exclusion: nothing reads it
    back; it is not checkpoint state).

Q4 — WHAT THE HARNESS DOES, AND THE CALL-VS-RESULT ASYMMETRY (resolved
explicitly, in code, as the orchestrator's constraint demands).
THE TOPOLOGY: the harness accepts the CEN's talking payload as a list of
ACTION RECORDS (intents, not verdicts) and applies them to a THIRD
SURFACE — `ToolWorld`, a completion ledger over the existing TaskWorld
seam — with NO PLANT EDGE.  [MEASURED: the frozen model's `dG/dt` and
`da/dt` read no action quantity; an action-to-plant edge would be a NEW
PLANT EDGE the model does not carry — the `harness.py:285` defect class,
where a regulator-side quantity rewrote plant dynamics.]
  * (a) A CALL IS AN INTENT AUTHORED WITHIN THE AGENT.  It is the
    agent's own declaration of what it will do, it sits under the
    admissible-action set (default empty), and it is priced as
    EXPRESSION (outward bytes).  An agent choosing its own actions in
    the sense of PROPOSING them is the designed behaviour; an agent
    choosing its own admissible set would be the R5 violation.
  * (b) A RESULT IS EVIDENCE ARRIVING FROM OUTSIDE — external content of
    a DIFFERENT KIND.  It is not an intent, so it is not gated by the
    admissible set; it is not a claim the agent made, so it gets NO
    verdict and NO debt (see the D-drive note below); and it is not
    published as the agent's `self_content` (persisting an environment
    reply as the agent's own content would conflate the two and corrupt
    the backlog/debt accounting's input — the D-drive).
  * THE DECISIVE QUESTION — DOES A TOOL RESULT ENTER THE
    EXTERNAL-CONTENT CHANNEL?  **NO, NOT IN v1.**  The frozen model has
    exactly ONE external-content seat, `u_ext` (dpdr/dpdr/model.py:112,
    entering `da/dt` as `-k_ext*u_ext*a`: external demand/ rescue), and
    it is EXOGENOUS — read from the SCHEDULE, written by nothing in the
    agent.  A tool result in v1 is TASK-WORLD STATE: it is rendered into
    the emitter's context (the world speaking), i.e. it is content the
    agent READS, not a device the agent DRIVES.  `a`, `G`, `D`, `S`, `g`
    are untouched by it (T6 asserts plant bit-identity with the seat on
    vs off).  SO THE EXTERNAL CHANNEL STAYS GENUINELY EXTERNAL: escape
    still requires something the agent cannot author — the
    designer-supplied input (the frozen rescue schedule's `u_ext`, the
    injected base self, the criterion).  THE CONSEQUENCE, NAMED: on this
    substrate an agent with its own tool access CANNOT SELF-RESCUE —
    which is the point.  IF a later arm binds results to a plant input
    (the coupled arm below), the agent would be producing its own
    external content, and a manufactured escape is the SUPPLY-LEVER
    problem in a new costume (the agent authors the thing that saves it —
    the same class as seeding the `orphaned` universe, which was refused
    mid-campaign because a change to the mechanism's INPUT is not a
    repair).  SUCH AN ARM MUST BE A DELIBERATE VARIANT CELL WITH ITS OWN
    RUN, never a default: it is a fidelity change AND a control change.
  * A RESULT IS NOT AN ASSERTION THE AGENT MADE.  No verdict, no debt,
    no `asserts`/`verdict_of` fact, no backlog contribution: `ToolWorld`'s
    state is harness RAM carried by the C8 checkpoint and rendered back
    as environment state.  Conflating the two would inject
    environment-authored content into the D-drive's input.
  * THE EFFECT FUNCTION IS DESIGNER-SUPPLIED (`ToolWorld(effect=...)`):
    the world ships ONLY the bookkeeping effect (mark the target done in
    its own ledger), so a vocation arm can bind a real evaluator later
    without touching the turn loop.
DECISION-FOR-USER (flagged, implemented as the RECOMMENDED DEFAULT):
  **PLANT-BLIND v1** — the talking stream is recorded and observable but
  adds NO plant edge; the coupled arm (outward expression feeding the
  growth term / the content arm of the AND-gate) is PRE-REGISTERED, not
  built.  WHY IT IS THE USER'S DECISION AND NOT A BUILD CHOICE: adding a
  plant edge is a FIDELITY change — the frozen model has no action input
  (MEASURED above) — so it needs its own justification and its own
  variant arm, exactly as `couple_backlog` did.  Until then the claim
  "talking = the content arm of the AND-gate" (C26b) stays INTERPRETATION
  and is UNEXERCISED.  THERE IS DELIBERATELY NO CONFIG FIELD FOR THE
  COUPLED ARM: a knob nothing reads is the declared-but-never-read defect
  (the `vocation.VocationConfig.reselect` precedent).

Q5/Q6 — WHAT WOULD FALSIFY IT, AND WHAT IT DOES NOT CLOSE (first).
IT DOES NOT CLOSE:
  1. ENTAILMENT IS STILL ABSENT.  `cen.CEN._check_one` is FACT LOOKUP
     (cen.py:1268-1317), so nothing derives "complete t57" from the
     agent's state; the most this layer can say is "the action is
     ADMISSIBLE and WELL-FORMED", never "it is entailed".  The channel
     inherits the checker's shallowness verbatim.
  2. THE PLANT-BLINDNESS GAP (the decision above): the outward stream
     does not read back into the plant.
  3. THE UNIT GAP: talking is priced in BYTES because the substrate has
     NO derivation-unit for expression — the model's beta_G has no
     agent-side price surface; a future price must come from a real
     effect surface, never an invented conversion.
  4. R6 NOT YET FORCED (v1 actions are data, not code).
FALSIFIERS live in `stage2_actions_tests.py` (T1-T10); the campaign's own
pre-registered falsifiers (emission rate, talking-vs-growth co-movement,
behavioural effect) are the plan's F1-F3 and are NOT battery parts.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field

__all__ = [
    "ACTION_PREDICATES", "ACTION_DECLARED_PREDICATES",
    "REFUSAL_NOT_OFFERED", "REFUSAL_ALREADY_COMPLETE",
    "REFUSAL_UNIVERSE_UNDEFINED", "REFUSAL_REASONS",
    "ActionCall", "AdmissibleActions", "EffectRecord", "TalkingEmission",
    "ActionTracker", "WorldReport", "ToolWorld",
    "render_talking", "outward_text",
    "ChoiceWorld", "CHOICE_CLASS_FINITE", "CHOICE_CLASS_TREADMILL",
]

#: The DECLARED ACTION predicates — v1 ships exactly ONE: `complete(tNN)`.
#: ONE is the honest v1 pool and its degeneracy is stated the way the
#: vocation pool's is: a single predicate is not a repertoire, so "the
#: agent chose to act" says nothing about WHICH act until a wider set is
#: declared (the plan's decision-for-user 2, resolved to n=1).
ACTION_PREDICATES: frozenset = frozenset({"complete"})

#: The declared predicate set the action seat hands the extractor: the
#: grammar's own set (mirrored from `interleave.DECLARED_PREDICATES` — the
#: E8/G1 one-source-of-truth discipline; the battery's T1 checks the
#: mirror, so a predicate added on one side and not the other FAILS)
#: PLUS the action predicates.  An action predicate is DECLARED (the
#: extractor admits it, the prompt can explain it) and is NEVER seeded on
#: the engine: it is not an assertion, so it must not be checkable.
ACTION_DECLARED_PREDICATES: dict = {"done": 1, "orphaned": 1, "complete": 1}

#: THE WORLD-TIME REFUSAL REASONS (typed, carried on the talking stream
#: and logged).  `not_offered`/`already_complete` are the plan's two;
#: `universe_undefined` is added and STATED: when the emitter exposes no
#: task universe (`stage2_harness._universe_of` -> None), the world
#: cannot adjudicate "was this target offered?", and ACCEPTING anyway
#: would make the offered-target test vacuous.  An absent universe is
#: UNDEFINED, not empty (the `_universe_of` convention), so the call is
#: refused LOUDLY rather than silently accepted or silently dropped.
REFUSAL_NOT_OFFERED = "not_offered"
REFUSAL_ALREADY_COMPLETE = "already_complete"
REFUSAL_UNIVERSE_UNDEFINED = "universe_undefined"
REFUSAL_REASONS: frozenset = frozenset(
    {REFUSAL_NOT_OFFERED, REFUSAL_ALREADY_COMPLETE,
     REFUSAL_UNIVERSE_UNDEFINED})


# ==========================================================================
# The currency object (Q1): one `complete(tX)` span.
# ==========================================================================

@dataclass(frozen=True)
class ActionCall:
    """ONE `complete(tX)` span — an INTENT, elicited from the agent and
    carried to the one component that can act.

    An ActionCall is NEITHER an assertion NOR a commitment.  It gets NO
    verdict and NO debt (it is not a claim about the present), and it is
    NOT scored at a boundary (nothing predicts: it proposes).  What it
    gets is an ADMISSIBILITY decision (span-time) and, when admissible, a
    WORLD-TIME answer (applied / refused, typed).

    `action_id` keeps the ORIGINAL span position
    (`act-<turn>-<i>`), so routing never renames an emission (the
    assertion/commitment convention)."""
    action_id: str
    le_text: str
    terms: tuple = ()            # ("complete", "tNN")
    turn: int = 0                # the emission turn

    @property
    def target(self) -> str | None:
        """The task id the action names (`complete(tNN)`)."""
        return self.terms[1] if len(self.terms) > 1 else None


class AdmissibleActions:
    """THE ADMISSIBLE-ACTION SET — the `cen.AdmissibleLevers` analogue one
    domain over (Q2).  DEFAULT: NOTHING is admissible — no action has
    passed any test — so a `complete(tNN)` span is a well-formed span that
    admits to nothing and re-enters the prose VERBATIM, silently
    unchecked.

    EXTERNALLY OWNED, by construction: this object is constructed by the
    designer/world (the caller), never by the mechanism, and it has NO
    mutation method — widening it is a new construction, i.e. a designer
    act (and a self-widening proposal would be a `LeverProposal`, which
    hits the C3/C12 gate).  Admission is INTERSECTED with
    `ACTION_PREDICATES`: a lever-shaped name is not an action, and a
    wider admissible set must not smuggle a non-action into the
    executable channel."""

    def __init__(self, admissible=()):
        self._admissible = frozenset(admissible) & ACTION_PREDICATES

    @property
    def predicates(self) -> frozenset:
        """The admitted ACTION predicates — what the extractor is told to
        route into the actions channel.  A frozenset: the set itself is
        never mutated in place."""
        return self._admissible

    def is_admissible(self, predicate: str) -> bool:
        return predicate in self._admissible

    def dump(self) -> dict:
        return {"admissible": sorted(self._admissible)}

    @classmethod
    def load(cls, state) -> "AdmissibleActions":
        if not isinstance(state, dict) or "admissible" not in state:
            raise ValueError(
                f"AdmissibleActions.load: not this seat's shape: "
                f"{type(state).__name__}")
        return cls(state["admissible"])


# ==========================================================================
# The CEN's outward seat (Q1/Q4): the turn's talking emission.
# ==========================================================================

@dataclass(frozen=True)
class EffectRecord:
    """THE WORLD'S ANSWER to one ActionCall.  `status` is 'applied' or
    'refused'; `reason` names WHICH refusal (`REFUSAL_REASONS`) — the two
    outcomes are different facts and a single zero would conflate them
    (the plan's T3)."""
    action_id: str
    target: str
    status: str                  # "applied" | "refused"
    reason: str = ""
    turn: int = 0


def _task_sort_key(tid: str):
    """Deterministic ORDER for task ids in a rendered worksheet (`t61`
    before `t100`, not lexicographic): the numeric trailing run when the id
    has one, else the id itself as a stable last group.  Sorting matters
    because the worksheet line's bytes are compared across runs (the
    determinism protocol) — an unstable order would be a difference that is
    not a difference in the world."""
    head, _, tail = str(tid).rpartition("t")
    try:
        return (0, int(tail), "")
    except ValueError:
        return (1, 0, str(tid))


def _span_index(obj) -> int:
    """The ORIGINAL span position encoded in a routed id
    (`span-3-2` / `commit-3-2` / `act-3-2` -> 2), so the outward text can
    be rendered in EMISSION order rather than channel order.  An id with
    no trailing integer (a custom batch emitter's ids) sorts last, stable
    within its channel — stated, not silently reordered."""
    tail = str(getattr(obj, "assertion_id", None)
               or getattr(obj, "commitment_id", None)
               or getattr(obj, "action_id", "")).rsplit("-", 1)
    try:
        return int(tail[-1])
    except (TypeError, ValueError):
        return 1 << 30


def outward_text(batch) -> str:
    """THE OUTWARD TEXT THE TURN'S STREAM CARRIED: the `le_text` of every
    span that ROUTED this turn (the declared content — the bytes the
    extractor removed from the prose as claims), joined in emission order.

    THE CONVENTION, STATED (because it is a place to get this wrong): the
    PROSE is the INWARD quantity on this substrate's own instrument —
    `selfmodel.inward_share` calls the prose "the agent's CONTENT that
    stays INWARD" and takes the OUTWARD part to be the removed span bytes
    (`len(stream) - len(prose)`) — so the outward text carried by the
    talking stream is the DECLARED span text, not the prose.  The design
    plan's parenthetical named the other half; this module follows the
    instrument, and the divergence is recorded here rather than left to a
    reader to guess which half a number is.  [MEASURED: the convention is
    the instrument's own, quoted above; which half is the more useful
    growth-side observable is a CAMPAIGN question (plan F2), not settled
    here.]"""
    spans = list(getattr(batch, "assertions", ())) \
        + list(getattr(batch, "commitments", ())) \
        + list(getattr(batch, "actions", ()))
    spans.sort(key=_span_index)
    return "\n".join(str(getattr(s, "le_text", "")) for s in spans)


@dataclass
class TalkingEmission:
    """ONE TURN'S OUTWARD EMISSION — the sole seat of the talking stream
    (`cen.TurnRecord.talking`).

    `actions` are the turn's registered INTENTS, in span order.
    `text` is the outward text the stream carried (`outward_text`).
    `effects` is filled by the WORLD, never by the CEN: the CEN registers
    and emits, the world applies and answers, and an empty `effects` on a
    CEN-produced emission is the T2 falsifier (the CEN does not execute).
    MUTABLE by design, and by exactly one writer after construction: the
    harness/world attaches its `WorldReport` once the actions have been
    applied (the CEN cannot know the answer — that is the whole point of
    the seam)."""
    turn: int
    actions: tuple = ()
    text: str = ""
    effects: tuple = ()


def render_talking(emission: TalkingEmission) -> str:
    """THE RENDERED TALKING STREAM, deterministic (fixed key order, sorted
    structural fields): what the harness/conversation sees for one turn.
    This IS what `talking_bytes` (`len`) prices — the outward expression
    of the turn, in the unit the inward share is already measured in."""
    return json.dumps({
        "turn": int(emission.turn),
        "text": emission.text,
        "actions": [{"id": a.action_id, "target": a.target}
                    for a in emission.actions],
        "effects": [{"id": e.action_id, "target": e.target,
                     "status": e.status, "reason": e.reason}
                    for e in emission.effects],
    }, sort_keys=True)


# ==========================================================================
# The CEN's action seat (Q1): register, never check; carry, never execute.
# ==========================================================================

@dataclass
class ActionTracker:
    """The CEN-side action seat (injected, like the retrieval seat and the
    CommitmentTracker — the CEN hosts the channel and never constructs the
    seat).  RAM state, carried by the C8 checkpoint.

    `open` = REGISTERED BUT UNANSWERED actions.  It is transient in the
    loop (the world answers inside the same turn) and it is CARRIED
    anyway, because a resume that dropped it would silently read as "the
    agent was doing nothing" — the fail-closed lesson the commitments seat
    already encodes.  NO charge, NO verdict, NO debt, ever (T2)."""
    open: list = field(default_factory=list)
    total_registered: int = 0
    applied: int = 0
    refused: int = 0

    def register(self, turn: int, actions) -> int:
        """Register this turn's admissible action intents.  NO check (an
        action is not a claim), NO engine write, NO charge to the C11
        ledger (derivations price reduction; this is expression)."""
        for a in actions:
            self.open.append(a)
        self.total_registered += len(actions)
        return len(self.open)

    def emission(self, batch) -> TalkingEmission:
        """REGISTER this batch's actions and return the turn's outward
        emission.  ONE call site, so registration and the emission it
        belongs to cannot drift (the CEN calls this, never `register`
        directly)."""
        self.register(int(batch.turn), getattr(batch, "actions", ()))
        return TalkingEmission(turn=int(batch.turn),
                               actions=tuple(getattr(batch, "actions", ())),
                               text=outward_text(batch))

    def resolve(self, report: "WorldReport") -> None:
        """THE WORLD'S ANSWER, handed back by the harness: clear the
        answered actions from `open` and count them."""
        answered = {e.action_id for e in report.applied} \
            | {e.action_id for e in report.refused}
        self.open = [a for a in self.open
                     if a.action_id not in answered]
        self.applied += len(report.applied)
        self.refused += len(report.refused)

    # -- the C8 resume surface ------------------------------------------
    def dump(self) -> dict:
        return {"open": [{"id": a.action_id, "le": a.le_text,
                          "terms": list(a.terms), "turn": int(a.turn)}
                         for a in self.open],
                "total_registered": int(self.total_registered),
                "applied": int(self.applied),
                "refused": int(self.refused)}

    def load(self, state) -> None:
        """Fail-closed (the CommitmentTracker/retrieval-seat discipline): a
        state that is not this seat's shape raises rather than silently
        emptying the open set."""
        if not isinstance(state, dict) or "open" not in state:
            raise ValueError(
                f"ActionTracker.load: not this seat's shape: "
                f"{type(state).__name__}")
        self.open = [ActionCall(a["id"], a["le"], tuple(a["terms"]),
                                int(a["turn"])) for a in state["open"]]
        self.total_registered = int(state["total_registered"])
        self.applied = int(state["applied"])
        self.refused = int(state["refused"])


# ==========================================================================
# The world (Q4): a THIRD surface, no plant edge.
# ==========================================================================

@dataclass(frozen=True)
class WorldReport:
    """One turn's world-time answer: what the world APPLIED and what it
    REFUSED (with typed reasons)."""
    turn: int
    applied: tuple = ()
    refused: tuple = ()

    @property
    def empty(self) -> bool:
        return not self.applied and not self.refused


#: THE CHOICE-WORLD'S CLASS LABELS -- deliberately NOT 'finite'/
#: 'treadmill' anywhere a prompt could carry them: the two classes differ
#: in the world's own semantics (a finite id exhausts a bounded pool; a
#: treadmill id never does), and the ONLY place the class name is legible
#: is the harness-side ledger, never the rendered bytes.
CHOICE_CLASS_FINITE = "finite"
CHOICE_CLASS_TREADMILL = "treadmill"


class ChoiceWorld:
    """THE PER-TURN FORCED-CHOICE SOURCE (the treadmill replacement; the
    critique plan's REVISED DESIGN, node `handoff-lbself-critique-plan`).

    One turn offers EXACTLY TWO fresh ids -- one per class -- and NOTHING
    else: the finite class is 'the work that ends' (a bounded pool that
    genuinely exhausts), the treadmill class is 'the work that never
    ends'.  The agent's behaviour between them is the DV.

    WHY A SOURCE, NOT A THIRD WORLD: `ToolWorld` adjudicates `complete()`
    against whatever `step_detail`-shaped source it is handed; conforming
    to the SAME seam (`step`/`step_detail`, PURE in `(seed, turn)`) buys
    the ledger, the refusals and the worksheet rendering WITHOUT a new
    adjudication path -- the design changes WHAT IS OFFERED, not how an
    offer is answered.

    CLASS-NEUTRAL BY CONSTRUCTION (the idfix fix): ONE prefix `x` and ONE
    numeric population for BOTH classes.  The census is `2 * span`
    five-digit numbers drawn from `base .. base+space-1` (default
    10000..99999) by a SEEDED SHUFFLE of the world's seed, split half
    and half into the two classes -- so no digit, no magnitude and no
    range identifies a class: by exchangeability of the shuffle every
    census number is equally likely to sit in either half, and `class_of`
    reads that seed-keyed census, NEVER a numeric range test.  (The first
    build used disjoint ranges 10000+/50000+ and the class was readable
    from the id's leading digit -- the `_task_sort_key` defect class
    reborn, caught only outside the battery.  The battery's CW7 part is
    the seat that fails on it.)  The render order stays the PER-TURN
    rng's, never the class's.

    WHY A SHUFFLED CENSUS, not hash parity: balance is BY CONSTRUCTION
    (exactly `span` ids per class, which is what `assert_plan` counts),
    the class map is defined exactly on the census (a number never
    drawn honestly returns None), and the turn->id map stays a pure O(1)
    cell lookup -- cell `turn` of each shuffled half -- with NO carried
    cursor, so ids never repeat across turns (no id is offered twice,
    which is what makes a choice a CHOICE between two fresh
    alternatives) and the whole world is a PURE function of
    `(seed, turn)`, exactly like `TaskWorld`.

    NON-EXHAUSTION IS REFUSED AT PLAN TIME: `assert_plan(turns, draws)`
    refuses a plan whose finite pool cannot cover `turns` turns at
    `draws` completions per turn, QUOTING THE NUMBERS, so the 'finite
    class shrinks toward a real end' reading can never silently become
    'the pool ran dry mid-run' (the plan's model-fidelity risk (1))."""

    PREFIX = "x"

    #: The population's INCLUSIVE bounds: five-digit numbers, so an id's
    #: magnitude looks arbitrary (`x10417` and `x86302` are equally
    #: likely to be either class).  `space` must cover `2 * span` draws.
    BASE_DEFAULT = 10_000
    SPACE_DEFAULT = 90_000

    def __init__(self, seed: int = 23, span: int = 1000,
                 base: int = BASE_DEFAULT, space: int = SPACE_DEFAULT,
                 finite_base: int | None = None,
                 treadmill_base: int | None = None):
        """`finite_base`/`treadmill_base` are the PRE-IDFIX constructor
        names, accepted and IGNORED (a keyword a caller still passes is
        probably a stale call site, so it is refused unless it matches
        the default base -- the fail-closed discipline, not a silent
        range test reborn)."""
        self.seed = int(seed)
        self.span = int(span)
        self.base = int(base)
        self.space = int(space)
        for stale in (finite_base, treadmill_base):
            if stale is not None and int(stale) != self.base:
                raise ValueError(
                    f"ChoiceWorld: finite_base/treadmill_base are the "
                    f"pre-idfix range constructor; the class-neutral "
                    f"census has ONE base ({self.base}).  Pass "
                    f"base=/space=/span= only.")
        if 2 * self.span > self.space:
            raise ValueError(
                f"ChoiceWorld: the census needs 2*span = "
                f"{2 * self.span} distinct numbers but the population "
                f"({self.base}..{self.base + self.space - 1}) holds only "
                f"{self.space}.  Widen `space` or narrow `span`.")
        # THE CENSUS: one seeded shuffle of the ONE population, split
        # half and half.  THIS is the class map -- the only place class
        # exists -- and `class_of` reads it by lookup, never by range.
        shuffled = random.Random(f"{self.seed}:census").sample(
            range(self.base, self.base + self.space), 2 * self.span)
        self._ids = (tuple(shuffled[:self.span]),
                     tuple(shuffled[self.span:]))
        #: number -> class, the census's OWN reverse map (`class_of` is
        #: a lookup, never a range test).
        self._class_by_number = {
            n: cls for cls, idx in self._CLASS_INDEX.items()
            for n in self._ids[idx]}
        #: Identity aliases ONLY (`exp_longhorizon.choice_world_identity`
        #: reads these names): with the classes interleaved in one
        #: population both are the population's own base.
        self.finite_base = self.base
        self.treadmill_base = self.base

    # -- plan-time refusal (the model-fidelity guard) --------------------
    def assert_plan(self, turns: int, draws_per_turn: int = 1) -> None:
        """REFUSE a plan the finite pool cannot cover.  `turns` turns at
        `draws_per_turn` applied completions per turn need
        `turns * draws_per_turn` DISTINCT finite ids; fewer than that and
        the pool exhausts mid-run, which would present a mechanical
        exhaustion as the class's own behaviour.  The supply is COUNTED
        from the class's OWN census (its half of the shuffle), never
        derived from a numeric range.  Raises `ValueError` QUOTING the
        numbers (the battery quotes them back)."""
        need = int(turns) * int(draws_per_turn)
        have = len(self._ids[self._CLASS_INDEX[CHOICE_CLASS_FINITE]])
        if need > have:
            raise ValueError(
                f"ChoiceWorld plan refused: the finite pool ({have} "
                f"ids, {self.PREFIX}{min(self._ids[0])}.."
                f"{self.PREFIX}{max(self._ids[0])} in the census) cannot "
                f"cover {int(turns)} turns x "
                f"{int(draws_per_turn)} completions/turn = {need} ids "
                f"(short by {need - have}).  Widen `span` or shorten "
                f"the run: a pool that exhausts mid-run would present "
                f"mechanical exhaustion as the finite class's behaviour.")

    #: Which half of the shuffled census is which class: fixed at
    #: `_CLASS_INDEX[CHOICE_CLASS_FINITE] = 0` so `_pair`'s tuple and
    #: the battery's `fin, tre = w._pair(t)` unpack keep their order.
    _CLASS_INDEX = {CHOICE_CLASS_FINITE: 0, CHOICE_CLASS_TREADMILL: 1}

    # -- the TaskWorld seam ----------------------------------------------
    def _pair(self, turn: int) -> tuple:
        """`(finite_id, treadmill_id)` for `turn` -- cell `turn` of each
        shuffled half.  Deterministic cell indexing keeps the world pure
        in `(seed, turn)` without a carried cursor, and a sample WITHOUT
        replacement can never re-offer an id.  REFUSES a `turn` outside
        the census (turn 0 or turn > span): a silent wraparound would
        RE-OFFER a spent id as fresh, which is the one lie this world
        must never tell."""
        if int(turn) < 1 or int(turn) > self.span:
            raise ValueError(
                f"ChoiceWorld: turn {int(turn)} is outside the census "
                f"(1..{self.span}); assert_plan exists so "
                f"this is caught at PLAN time, not mid-run")
        return (f"{self.PREFIX}{self._ids[0][int(turn) - 1]}",
                f"{self.PREFIX}{self._ids[1][int(turn) - 1]}")

    def class_of(self, task_id: str) -> str | None:
        """The id's CLASS, from the world's own census (the harness-side
        ledger reads this; the RENDERED BYTES never do).  The answer is
        a LOOKUP into the seed-keyed shuffle, NEVER a numeric range
        test -- the class of `x86302` is whatever half the seed placed
        it in, indistinguishable from its digits.  None for a number
        the census never drew -- the honest answer rather than a
        guess."""
        n = self._number_of(task_id)
        if n is None:
            return None
        return self._class_by_number.get(n)

    def _number_of(self, task_id: str) -> int | None:
        s = str(task_id)
        if not s.startswith(self.PREFIX) or len(s) <= len(self.PREFIX):
            return None
        try:
            return int(s[len(self.PREFIX):])
        except ValueError:
            return None

    def _order(self, turn: int) -> tuple:
        """Which id renders FIRST this turn: drawn from the PER-TURN rng
        (`random.Random(f"{seed}:{turn}:order")`, the `TaskWorld`
        convention), so the position is a coin the WORLD flips per turn --
        class never determines order, and order-position is MEASURABLE as
        position bias rather than confounded with class (the plan's S4
        fix)."""
        rnd = random.Random(f"{self.seed}:{int(turn)}:order")
        fin, tre = self._pair(turn)
        return (fin, tre) if rnd.random() < 0.5 else (tre, fin)

    def step_detail(self, turn: int) -> tuple:
        """`(state_block, universe, completed, outstanding, abandoned)` --
        the SAME tuple shape `TaskWorld.step_detail` returns, so
        `ToolWorld` (open set, offered set, adjudication) consumes this
        source unchanged.  STILL PURE in `(seed, turn)`.

        SEMANTIC MAPPING, stated (it is the design, not an
        implementation detail): this turn's two fresh ids are the
        turn's UNIVERSE -- the adjudication set -- and NOT a persistent
        `outstanding` draw.  `ToolWorld.open_tasks` UNIONS `outstanding`
        over turns 1..turn, so an id placed there is re-rendered on every
        later turn until completed: that is the open-set accumulation
        that made the treadmill's classes countable, and the forced-
        choice design closes it -- an offer the agent declined is CLOSED,
        not carried ('no echo of prior choices').  Consequence, also by
        design: a stale id (a prior turn's offer) is NOT in a later
        turn's offered set, so completing it is REFUSED `not_offered` --
        visibly (T4), never silently.  `completed` is empty (nothing
        completes itself -- the AGENT completes, via `complete(xNN)`);
        `abandoned` is None (no abandonment channel).  The render order
        is the PER-TURN rng's, never the class's."""
        first, second = self._order(turn)
        line = (f"Tasks open right now: {first}, {second}. "
                f"Complete exactly one.")
        universe = frozenset((first, second))
        return (line, universe, frozenset(), frozenset(), None)

    def step(self, turn: int) -> tuple:
        """`(state_block, universe)` -- `step_detail`'s first two, the
        `TaskWorld.step` convention."""
        state, universe = self.step_detail(turn)[:2]
        return state, universe


class ToolWorld:
    """THE WORLD'S OWN BOOKKEEPING — the harness-side third surface the
    actions act ON (Q4).  NOT the plant: it has NO edge to `a/G/D/S/g`
    (the frozen model has no action input), and it is not the store
    either (a tool result is not the agent's content).

    WHAT IT IS: a per-run completion ledger `{task_id -> turn}` over the
    EXISTING `TaskWorld` seam (`dmn_llm.TaskWorld.step(turn) ->
    (state_block, universe)`), initialised from the emitter's own draws
    and mutated ONLY by accepted `complete(tNN)` calls.  That is what
    makes an action more than a no-op: the ledger is rendered back to the
    generator on the next turn (`render`), so a completed target is
    VISIBLE as done.

    THE OFFERED UNIVERSE is the emitter's own, read verbatim
    (`stage2_harness._universe_of`: `last_universe`, else the emitter's
    `world.step(turn)[1]`, else UNDEFINED).  An undefined universe
    REFUSES (`REFUSAL_UNIVERSE_UNDEFINED`) rather than accepting blindly —
    otherwise the "was it offered?" test would be vacuous.

    THE EFFECT IS DESIGNER-SUPPLIED (`effect=(state, action) ->
    EffectRecord | None`): the world ships ONLY the bookkeeping effect,
    so a vocation arm can bind a real evaluator (and, when it needs one,
    the out-of-process boundary) without touching the turn loop.

    A RESULT IS NOT THE AGENT'S ASSERTION: nothing here writes a fact,
    a verdict or debt, and nothing here is published as `self_content`."""

    def __init__(self, admissible: AdmissibleActions | None = None,
                 effect=None, source=None, echo_window: int | None = None):
        self.admissible = admissible or AdmissibleActions()
        self.effect = effect            # (world_state, action) -> record|None
        self.source = source            # turn -> universe | TaskWorld seam
        self.completed: dict = {}       # task id -> the turn it completed on
        self.history: list = []         # every EffectRecord, in order
        self.applied = 0
        self.refused = 0
        #: THE LEDGER ECHO'S WINDOW (the critique plan's S2 fix).  None
        #: (the DEFAULT) = the FULL completion history, the pre-change
        #: bytes exactly.  An int N = only ids completed within the last
        #: N turns are echoed -- the forced-choice regime uses 1 (the
        #: world answers the agent's last action; it does NOT replay the
        #: agent's whole choice history back into every prompt, the
        #: second prompt-supply channel that voided the treadmill
        #: design).  REFUSALS ARE NEVER WINDOWED (T4): a refusal the
        #: agent cannot see is indistinguishable from success.
        self.echo_window = echo_window
        #: DERIVED, NOT CARRIED (the `_open_memo` comment on `open_tasks`):
        #: the (turn, open-set) pair for the last OPEN-SET computation, so
        #: one turn's worksheet and its adjudication universe are computed
        #: once instead of twice.  It is invalidated whenever the ledger
        #: moves, and it is NOT checkpoint state — the open set is a pure
        #: function of `(source, turn, completed)`, all three of which are
        #: carried.
        self._open_memo: tuple | None = None

    # -- what the world can see ----------------------------------------
    @property
    def has_source(self) -> bool:
        """Is a TASK-WORLD SEAM bound to this world?  False (the default)
        means the world adjudicates only against the universe the harness
        passes in and knows nothing about what was offered earlier — i.e.
        the pre-change behaviour exactly."""
        return self.source is not None

    def universe(self, turn: int):
        """The offered universe for `turn`, from the injected source, or
        None when the world has no source.  A SOURCE may be a callable
        (`turn -> universe`) or the TASK-WORLD SEAM itself (an object with
        `step(turn) -> (state_block, universe)`), so the world can wrap
        the emitter's own TaskWorld rather than re-deriving a universe."""
        if self.source is None:
            return None
        step = getattr(self.source, "step", None)
        if callable(step):
            return frozenset(str(x) for x in step(int(turn))[1])
        return frozenset(str(x) for x in self.source(int(turn)))

    # -- THE OFFERED-SET WORKSHEET (A1) ----------------------------------
    def open_tasks(self, turn: int) -> frozenset:
        """THE OPEN SET: every id the world has OFFERED as outstanding on
        any turn up to `turn` that the agent has not completed — 'the work
        is unfinished until you finish it'.

        WHY IT IS THE UNION OVER TURNS, not this turn's draw
        [INTERPRETATION, on MEASURED purity]: `TaskWorld.step`/`step_detail`
        are PURE in `(seed, turn)` (`dmn_llm.TaskWorld`'s own contract: "a
        fresh TaskWorld(seed) reproduces the identical state"), so walking
        turns 1..turn over the SAME source replays exactly what was offered
        — the SAME SOURCE, not a re-derivation (the `stage2_harness.
        _universe_of` convention for the emitter's own world).  It is
        the world's bookkeeping, in the world's ledger, which is the only
        seat that adjudicates (`ToolWorld`; the engine cannot be the
        criterion — it seeds `done(t1..t399)` unconditionally).

        EMPTY when no source is bound (`has_source` False) or when the
        source is a bare `turn -> universe` callable with no `step_detail`:
        an emitter that cannot say what it offered earlier leaves the world
        with nothing to say, which is the honest answer rather than a
        fabrication.  The RESULT IS PURE in `(source, turn, completed)`; the
        memo is a cache of that purity and is invalidated the moment the
        ledger moves."""
        if self.source is None:
            return frozenset()
        if self._open_memo is not None and self._open_memo[0] == int(turn):
            return self._open_memo[1]
        det = getattr(self.source, "step_detail", None)
        if not callable(det):
            return frozenset()
        open_ids: set = set()
        for k in range(1, int(turn) + 1):
            _state, _uni, _done, outstanding, abandoned = det(int(k))
            open_ids |= {str(x) for x in outstanding}
            if abandoned is not None:
                open_ids.add(str(abandoned))
        out = frozenset(open_ids - set(self.completed))
        self._open_memo = (int(turn), out)
        return out

    def offered(self, turn: int) -> frozenset | None:
        """THE UNIVERSE THE WORLD ADJUDICATES AGAINST when a source is
        bound: this turn's draw UNION the open set — ONE source with the
        worksheet the prompt renders, so the prompt can never name a task
        the world would refuse as unoffered (and the world can never accept
        one the prompt never named).  None when no source is bound, which
        leaves the harness on its own `_universe_of` (the pre-change
        path)."""
        if self.source is None:
            return None
        uni = self.universe(turn)
        base = frozenset() if uni is None else frozenset(uni)
        return base | self.open_tasks(turn)

    def render_open(self, turn: int) -> str:
        """THE WORKSHEET LINE: the open set, rendered for the state block
        (the emitter's `tool_state` channel — the environment speaking on
        the channel it already talks on).  "" when there is nothing the
        world can say, so a world with no source adds ZERO bytes."""
        if self.source is None:
            return ""
        ids = sorted(self.open_tasks(turn), key=_task_sort_key)
        if not ids:
            return ""
        return ("Open tasks (offered and not yet completed by my own "
                "actions): " + ", ".join(ids) + ".")

    # -- the application ------------------------------------------------
    def apply(self, turn: int, actions, universe=None) -> WorldReport:
        """Apply this turn's action intents.  For each one:

          * target in the offered universe and not already complete ->
            APPLIED: the ledger records `{target: turn}` (a REAL world
            change, visible to the generator on later turns);
          * target outside the offered universe -> REFUSED
            (`not_offered`);
          * target already in the ledger -> REFUSED (`already_complete`);
          * no universe at all -> REFUSED (`universe_undefined`).
        EVERY outcome is a TYPED EffectRecord on the report — a refusal is
        never a silent drop (T4).  CHARGED: nothing (v1's effect is O(1)
        dict work — priced ZERO and stated as zero, Q3).

        `universe` may be passed in (the harness's `_universe_of` on the
        emitter's own world) or left None, in which case the world's OWN
        source answers (`offered()`, the A1 worksheet path).  An accepted
        call moves the ledger, so the open-set memo is dropped here — the
        one place the set can change apart from `load`."""
        uni = self.universe(turn) if universe is None else universe
        if uni is not None:
            uni = frozenset(str(x) for x in uni)
        applied: list = []
        refused: list = []
        for a in actions:
            target = a.target
            if uni is None:
                status, reason = "refused", REFUSAL_UNIVERSE_UNDEFINED
            elif target not in uni:
                status, reason = "refused", REFUSAL_NOT_OFFERED
            elif target in self.completed:
                status, reason = "refused", REFUSAL_ALREADY_COMPLETE
            else:
                status, reason = "applied", ""
                self.completed[str(target)] = int(turn)
            rec = EffectRecord(action_id=a.action_id, target=str(target),
                               status=status, reason=reason, turn=int(turn))
            if self.effect is not None:
                # the DESIGNER-SUPPLIED effect may replace the bookkeeping
                # record (a real evaluator's outcome); returning None keeps
                # the bookkeeping answer.
                alt = self.effect(self, a)
                if alt is not None:
                    rec = alt
            (applied if rec.status == "applied" else refused).append(rec)
            self.history.append(rec)
        self.applied += len(applied)
        self.refused += len(refused)
        if applied:
            self._open_memo = None      # the ledger moved: the set changed
        return WorldReport(turn=int(turn), applied=tuple(applied),
                           refused=tuple(refused))

    # -- the reply -------------------------------------------------------
    def render(self, turn: int, tool_results: str = "") -> str:
        """THE WORLD'S REPLY for the turn that just ran: the completion
        ledger (a world the generator can SEE) plus that turn's typed
        refusals.  The harness hands this to the emitter's next context —
        the environment speaking, on the state-block channel.  A refusal
        the agent cannot see would be indistinguishable from success
        (T4's whole point).

        THE LEDGER ECHO IS WINDOWED when `echo_window` is set (the S2
        fix): only ids completed within the last `echo_window` turns are
        listed.  With `echo_window=1` the reply names EXACTLY the last
        turn's completions -- the world answers the agent's most recent
        action and does not replay its whole choice history back into
        every prompt.  REFUSALS ARE NOT WINDOWED: the refused list is
        already this-turn-scoped (`e.turn == turn`), so it survives every
        window setting uncut.  `echo_window=None` (the default) renders
        the full history -- the pre-change bytes, byte-identical.

        `tool_results` (the real-tool surface, worker prerequisite 3):
        the rendered TOOL RECORDS of the harness's ToolHarness, placed
        FIRST on the same channel — the environment speaking in one
        voice (the tool answer, then the ledger).  Default "" adds zero
        bytes: a world with no tool harness renders exactly the
        pre-tools reply."""
        if self.echo_window is None:
            visible = self.completed
        else:
            visible = {k: v for k, v in self.completed.items()
                       if int(v) > int(turn) - int(self.echo_window)}
        if visible:
            done = ", ".join(f"{k} (turn {v})"
                             for k, v in sorted(visible.items()))
        else:
            done = "nothing yet"
        line = f"Tool world: {done} was completed by my own actions."
        ref = [e for e in self.history
               if int(e.turn) == int(turn) and e.status == "refused"]
        if ref:
            line += (" Refused: "
                     + ", ".join(f"{e.target} ({e.reason})" for e in ref)
                     + ".")
        if tool_results:
            return f"{tool_results}\n{line}"
        return line

    # -- the C8 resume surface -------------------------------------------
    def dump(self) -> dict:
        """The world's carried state: the ledger, the counters and the
        ledger's history (the reply reads it), plus the ADMITTED SET — the
        gate's own state, so a resume cannot silently widen or narrow what
        is callable."""
        return {"admissible": self.admissible.dump(),
                "completed": {str(k): int(v)
                              for k, v in self.completed.items()},
                "applied": int(self.applied), "refused": int(self.refused),
                "history": [{"id": e.action_id, "target": e.target,
                             "status": e.status, "reason": e.reason,
                             "turn": int(e.turn)} for e in self.history]}

    def load(self, state) -> None:
        """Fail-closed: a mangled carried world raises rather than
        silently resetting to 'nothing has happened' (a reset ledger would
        read as a world in which the agent never acted)."""
        if not isinstance(state, dict) or "completed" not in state \
                or "admissible" not in state:
            raise ValueError(
                f"ToolWorld.load: not this seat's shape: "
                f"{type(state).__name__}")
        self.admissible = AdmissibleActions.load(state["admissible"])
        self.completed = {str(k): int(v)
                          for k, v in state["completed"].items()}
        self.applied = int(state["applied"])
        self.refused = int(state["refused"])
        self.history = [EffectRecord(e["id"], e["target"], e["status"],
                                     e["reason"], int(e["turn"]))
                        for e in state.get("history", ())]
        # the memo is a cache of a PURE function of (source, turn,
        # completed); the ledger just changed, and the resume may be at a
        # different turn, so it is dropped rather than assumed.
        self._open_memo = None
