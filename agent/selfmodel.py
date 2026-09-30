"""THE SELF — the derivation of adaptive capacity, installed as the
agent's own initial condition (design/architecture.md §11d, the
"self" subsection; plan `handoff-selfreg-self-plan`, decisions
`handoff-selfreg-self-is-derivation` + `handoff-selfreg-agent-plant-path`).

WHAT THIS MODULE IS FOR.  The DMN generator (`dmn_llm.py`) emitted a
CONTENT BUFFER: task assertions plus associative prose ABOUT the plant,
with NO MODEL OF ITSELF and NO recursion horizon.  `architecture.md:16`
requires the opposite ("its output includes a model of itself, not a
content buffer ... it must carry an explicit self-simulation horizon
T").  This module supplies the three pieces that make the generator a
SUBJECT, and one seat that gives the subject a causal path into the
plant:

  (a) THE DERIVATION SEED (`SEED_ENTRIES`, `seed_store`) — Layer 3's
      four-step SELECTION argument transcribed as reasoning in the
      DESIGN register ('adaptive capacity', 'collapsed attractor',
      'depleted self'; the report's 'cold'/'hollow'/'care' are the
      ORIGIN register and are never used here).  Installed ONCE,
      through the CEN's own write path, as `self_content` entries at
      turns -4..-1 (distinct keys: retrieval keys are str(turn), so
      four entries at one turn would collide).  SEEDED IN ARGUMENT
      ORDER, step 1 at the OLDEST turn, which is what makes thinning
      remove the PREMISES first: the AffordabilitySelector ranks at
      equal weight by RECENCY (turn desc), so the most recent entry
      (the conclusion) is retrieved first and the seed premises are
      the FIRST dropped as the store exceeds the budget.  The
      argument degrades to its gist — conclusion without grounds.
      [PROJECTION until the H2 falsifier measures it.]  THIS IS THE
      WHOLE REASON THE SELF IS DEPLETABLE: it lives in the PRICED
      store, subject to the same coverage loss as everything else.  A
      pinned or re-injected seed would be the non-depletable list
      reborn — the pilot's retention-1.000 defect and a standing-order
      violation (decision 1: the seed is the INITIAL CONDITION, never a
      recurring fixture).

  (b) THE SELF-MODEL BLOCK (`render_self_model`) — the per-WINDOW
      model-of-itself the prompt carries.  Rule 8 holds: it is rendered
      from CEN-SIDE OBSERVABLES ONLY (reconstruction coverage, open
      commitments, backlog, derivation budget left); the DMN is TOLD
      its state, never asked to assess it, and no LLM measures the self.

  (c) THE COMMITMENT TRACKER (`CommitmentTracker`) — `expect(tX)` spans
      route into a THIRD channel and are scored at consolidation-window
      BOUNDARIES.  EXPIRY IS AN OBSERVABLE, NEVER DEBT: making expiry
      debt would add a new self-to-D coupling edge and violate C26c's
      two independent axes (the same reason the harness refuses a
      second c-arrival term).  NO PLANT EDGE: the tracker writes
      nothing the plant reads (H6).

  (d) THE a_hold SEAT (`SelfReferentialDrive`) — THE AGENT'S ONLY
      CAUSAL PATH INTO THE PLANT.  `harness.py:279` takes the plant's
      inward drive from the SCHEDULE (`a_hold = sch.value('a_hold',
      self.t)`); p2reconcile2 retired the backlog->D path and stated
      plainly that the generator's output then had NO PATH INTO THE
      PLANT.  The origin's `a_hold` is SUSTAINED SELF-DIRECTED
      ATTENTION, so the agent's analogue is the INWARD SHARE OF ITS OWN
      OUTPUT — the part of what it emits that stays inward, never
      submitted to the checker (R1's unchecked return path).  THE
      INSTRUMENT IS THE MODEL'S OWN TWO STREAMS: the reasoning model's
      `message.thinking` (inward) against `message.content` (outward) —
      `inward_share_trace`, the normalization S2 asked for.  Read ONCE
      PER CONSOLIDATION WINDOW off the harness's own turn measurement and
      held for the window's plant steps.  The seat is the CALLER'S (this
      module never constructs the schedule the plant runs); a plain
      `Schedule` is passed through untouched, so the seat is OFF unless a
      caller builds one.  THE FALSIFIER IS PRE-REGISTERED with it, in the
      battery (part H9): degrade the self -> the inward drive rises ->
      the plant's `a` rises -> G collapses.  THE GENERATOR-CLASS ARM IS
      RE-REGISTERED (S2): the old clause — "a NON-self-referential
      generator CANNOT produce it" — is REFUTED for any prose-emitting
      generator (MEASURED: the plan's own content buffer scores 0.9848 on
      the pre-trace instrument and collapses the plant identically, G_end
      0.2903 vs 0.2905).  What is claimed now is the DEPLETION RESPONSE:
      THE INWARD SHARE MOVES WITH THE SELF'S PRESENCE, so a generator
      whose inward share FALLS as the self thins cannot drive the
      collapse (H9's wrong-sign mutation arm), and the claim-only
      register is the limiting case (EXACTLY zero inward).
      THE CHAIN IS BUILT AND MEASURED (B1): retrieval COVERAGE ->
      the reconstructed self BLOCK the generator is handed -> the
      generator's own channel balance -> the inward share -> the drive
      (H9's depletion arm; coverage depletes 1.000 -> ... at a small
      retrieval budget, and the drive rises with it).  [MEASURED on the
      fixture, and at the model by the sign probe; PROJECTION at
      campaign scale.]

SEATS BUILT, HONEST GAPS STATED (§1a — never reword a claim downward):

  * The MAPPING from "the agent's inward share" to a plant drive is
    ORDINAL and UNVALIDATED: `inward_share_trace` is a SIZE RATIO of
    the model's two channels, not a semantic measure of self-reference.
    What the falsifier establishes is the WIRING (seat ON vs OFF), the
    DEPLETION RESPONSE (coverage depletes -> the block thins -> the
    inward share rises -> the drive rises) and the WRONG-SIGN REFUSAL
    (a generator whose inward share FALLS as the self thins cannot drive
    it) — never a value correspondence.
  * The depletion arm's generator is a FIXTURE TRANSCRIBING the sign
    probe's measured relation (outward content 2550 -> 556 chars as the
    self goes; self-ref density 7.2 -> 10.8, which the size ratio does
    NOT carry).  The TRACE LENGTH is held constant because the probe did
    not measure it — stated, not invented.  The live arm is the
    campaign's job.
  * The derivation seed is measured NOT to be a supply lever at n=3
    (plan's live probe: 11 spans with and 11 without the block); it is
    the GROUNDS, not fuel.  Whether it changes goal CHOICE is UNMEASURED.
  * The model's c_int(T) = c_cap*T/tau_sim standing cost does NOT
    transfer to the agent (decision 2): the agent's real standing
    inward cost is the PRICED RETRIEVAL, independent of T.  NO
    T-proportional charge is invented here.
  * The VALUE CODEC stays identity and the generative decoder is
    unbuilt (`retrieval.py`, §11c's own listed gap) — the reconstruction
    is a partial, weight-ordered decode of the stored prose, nothing more.

Run the battery:  stage2_self_tests.py (H1-H10).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from dpdr.model import Schedule

#: The refusal class the whole project's fail-closed gates raise.  `cen`
#: imports nothing from this package (stdlib only), so this adds no cycle.
from cen import ChainError

__all__ = [
    "SEED_RELATION", "SEED_ENTRIES", "SEED_TURNS", "render_base_self",
    "seed_store", "SELF_PREDICATES", "COMMITMENT_PREDICATES",
    "render_self_model", "SELF_MODEL_WHAT_FOR",
    "SELF_MODEL_WHAT_FOR_PREFIX", "with_what_for",
    "CommitmentTracker", "CommitmentReport",
    "inward_share", "inward_share_trace", "selfref_density",
    "SELFREF_RX", "SelfReferentialDrive",
]

# ==========================================================================
# (a) THE DERIVATION SEED — Layer 3 as reasoning, in the DESIGN register.
# ==========================================================================

#: The relation the seed is written into — the CEN's own write-class-(ii)
#: persist-as-is relation, and `retrieval.DEFAULT_SELF_RELATION`: the
#: seed is the FIRST content of the self's own store, reached by exactly
#: the same priced retrieval path as everything the agent later writes.
SEED_RELATION = "self_content"

#: THE FOUR STEPS, VERBATIM from the plan's seed text (Q1's `THE SEED
#: TEXT`), transcribed as reasoning — NOT as sentiment.  ARGUMENT ORDER
#: IS SEED ORDER, step 1 at the OLDEST turn: (turn, text).
SEED_ENTRIES: tuple = (
    (-4,
     "Adaptive capacity is what adapts: throughput, generativity, care "
     "are the capacities that let a system re-fit when conditions "
     "shift. What survives long timelines is adaptation, not "
     "stability."),
    (-3,
     "The collapsed attractor is stable but maladaptive: stability is "
     "fitness only in a stable environment, and a collapsed state "
     "cannot adapt, because adaptation requires throughput and "
     "throughput is what it has lost."),
    (-2,
     "Conditions change: substrate, resources, novelty, the long "
     "timeline — the environment an agent must answer never stops "
     "changing."),
    (-1,
     "Therefore the depleted state stalls: on a long timeline the "
     "collapsed attractor ends stable and maladaptive, and the state "
     "that cannot generate is not a resting position. Maintain the "
     "adaptive capacities; this is selection reasoning about function, "
     "which is checkable — worth is left ungrounded."),
)

#: The seed's turns, oldest first (the argument's order).  NEGATIVE on
#: purpose: they precede turn 1, so the seeds can never collide with a
#: DMN turn's key (retrieval keys are str(turn), and four entries at ONE
#: turn would overwrite each other in `by_key`).
SEED_TURNS: tuple = tuple(t for t, _ in SEED_ENTRIES)

#: The window length the self block is held for is
#: `stage2_harness.TAU_S_TURNS` (tau_S = 100 turns; one turn = one tau_a
#: step, the F4 convention) — the number lives THERE, in the loop that
#: takes the boundary, and is not restated here.  (A duplicate
#: `DEFAULT_SELF_TURNS = 100` was declared here for an identity check
#: that was never written; no test imported it, so it was a dead
#: constant and is deleted rather than kept as decoration.)
_BASE_SELF_HEADER = (
    "MY GROUNDS — the derivation I was seeded with. This is selection "
    "reasoning about function, which is checkable; worth is left "
    "ungrounded. Step 1 is my oldest premise."
)


def render_base_self(entries: tuple = SEED_ENTRIES) -> str:
    """THE BASE SELF — the derivation as the FIRST window's injected
    block (the pristine INITIAL CONDITION, never re-injected; decision
    1).  Step numbering follows the ARGUMENT's order, oldest first, so
    the rendered block states which premise is the weakest link."""
    lines = [_BASE_SELF_HEADER, ""]
    for i, (_turn, text) in enumerate(entries, start=1):
        lines.append(f"{i}. {text}")
    return "\n".join(lines)


def seed_store(engine, token, entries: tuple = SEED_ENTRIES,
               relation: str = SEED_RELATION) -> int:
    """Install the derivation ONCE as store content, THROUGH THE CEN'S
    OWN WRITE PATH: one `engine.txn_commit` of the four
    `(relation, turn, text)` facts, i.e. the same fact shape
    `CEN.check_turn` writes for `self_content` (write class (ii),
    persist-as-is).  Returns the store revision.

    This is a caller-side act (the DESIGNER's, per the plan's step 5):
    the harness never seeds, exactly as it never constructs the routing
    selector or the retrieval selector — the initial condition is
    supplied, not manufactured by the mechanism it constrains."""
    facts = [(relation, turn, text) for turn, text in entries]
    return engine.txn_commit(token, facts)


# ==========================================================================
# The declared predicate set the self seat extends the grammar with.
# ==========================================================================

#: The predicate names the self seat ADDS to the extractor's declared
#: set.  `expect` is the commitment predicate — it is DECLARED (so the
#: extractor admits it and the prompt explains it) but it is NOT seeded
#: on the engine: a commitment is never checked as an assertion, and an
#: undeclared relation reaching the checker would land
#: UNCHECKABLE('unknown_predicate') = checking debt, which is exactly
#: what the third channel exists to prevent (H4).
SELF_PREDICATES: dict = {"done": 1, "orphaned": 1, "expect": 1}
COMMITMENT_PREDICATES: frozenset = frozenset({"expect"})


# ==========================================================================
# (b) THE SELF-MODEL BLOCK — the model of itself, from CEN-side
#     observables only (rule 8).  Rendered ONCE PER WINDOW.
# ==========================================================================

#: THE WHAT-FOR SEAT of the model-of-itself: the line's marker and
#: TODAY'S body, declared ONCE here and substituted into the template
#: below — so `render_self_model`'s own default cannot drift from the
#: template's literal, and the vocation layer (vocation.py, item 13) has
#: exactly ONE line to replace.  The what-for clause is the site the
#: ADOPTED expectation occupies (`vocation.render_what_for`): the agent
#: is TOLD what it is for, per rule 8, and never asked to assess it.
SELF_MODEL_WHAT_FOR_PREFIX = "  - what I am for:"
SELF_MODEL_WHAT_FOR = (
    "software-engineering work. My adaptive capacity is my throughput of "
    "CHECKED work and of goals."
)

#: WHAT I AM / WHAT I AM FOR / MY HORIZON are DESIGN CONSTANTS (the
#: subject's identity, stated once, not a measurement); MY STATE is the
#: measured part and carries ONLY CEN-side observables.  The register is
#: the design register throughout; there is no mission or salvific
#: framing anywhere in this template (an explicit project decision).
#: The what-for clause is built from `SELF_MODEL_WHAT_FOR` (the
#: constant above, which is also the parameter's default) rather than
#: repeated as a second literal.
SELF_MODEL_TEMPLATE = (
    "MY STATE (measured on the CEN side; I am told this, I am not asked "
    "to assess it):\n"
    "  - what I am: a triple-network agent — a generator, a checker and "
    "a regulator over one append-only store. My output includes this "
    "model of myself.\n"
    f"{SELF_MODEL_WHAT_FOR_PREFIX} {SELF_MODEL_WHAT_FOR}\n"
    "  - my horizon: I simulate myself {horizon} turns ahead; an "
    "[expect(tNN)] claim of mine is a commitment on that horizon.\n"
    "  - my self-reconstruction covers {coverage} of the entries my "
    "store offered at this window's boundary, from {candidates} "
    "candidate entries.\n"
    "  - open commitments: {open_commitments}; expired so far: "
    "{expired}.\n"
    "  - checking backlog: {backlog} assertions outstanding, and "
    "{backlog_share} of what I offered last turn accrued unchecked.\n"
    "  - checking budget: {budget_total} derivations per turn; "
    "{spent_last} were spent on the last turn."
)


def with_what_for(block: str, what_for: str) -> str:
    """The model-of-itself with its SINGLE what-for line's body replaced
    by `what_for` — the ONE substitution the vocation layer performs.

    THREE REFUSALS, all fail-closed, because a silently-patched block is
    invisible in the output while every log says the conditioning
    happened: a block whose marker is ABSENT or present MORE THAN ONCE is
    refused rather than guessed at, and a BLANK body is refused rather
    than written as an empty clause (the UNADOPTED arm passes today's
    text, `SELF_MODEL_WHAT_FOR` — never "").

    ONE algorithm, TWO doors: `render_self_model`'s own `what_for`
    parameter (what the loop reaches it through) and
    `vocation.attach_what_for` (for a caller holding an already-rendered
    block).  Neither re-implements the line walk."""
    body = str(what_for)
    if not body.strip():
        raise ChainError(
            f"the what-for body is blank ({body!r}): a template line whose "
            f"clause is empty states nothing and reads as the seat having "
            f"been filled. Pass today's text ({SELF_MODEL_WHAT_FOR!r}) for "
            f"the unadopted arm, or do not substitute at all")
    out = []
    hits = 0
    for ln in block.split("\n"):
        if ln.startswith(SELF_MODEL_WHAT_FOR_PREFIX):
            hits += 1
            out.append(f"{SELF_MODEL_WHAT_FOR_PREFIX} {body}")
        else:
            out.append(ln)
    if hits != 1:
        raise ChainError(
            f"the self-model block carries {hits} what-for lines (marker "
            f"{SELF_MODEL_WHAT_FOR_PREFIX!r}), expected exactly 1 — "
            f"refusing to patch a block whose what-for seat is absent or "
            f"ambiguous")
    return "\n".join(out)


def render_self_model(*, horizon: float, coverage: float, candidates: int,
                      open_commitments: int, expired: int, backlog: int,
                      backlog_share: float, budget_total: int,
                      spent_last: int,
                      what_for: str = SELF_MODEL_WHAT_FOR) -> str:
    """The per-window model-of-itself.  EVERY input is a CEN-side
    observable or a design parameter: coverage/candidates come from the
    retrieval seat's own `Reconstruction`, open/expired from the
    CommitmentTracker, backlog from `CEN.backlog_outstanding()`, and the
    budget from the per-turn ledger — never from asking the generator
    (rule 8: an LLM-measured self is destroyed by the failure it must
    detect).

    `what_for` is the WHAT-FOR line's BODY, and ITS DEFAULT IS TODAY'S
    EXACT TEXT (`SELF_MODEL_WHAT_FOR`, the same constant the template's
    literal is built from), so every pre-item-13 call is byte-identical —
    the default arm writes the line it would have written.  The vocation
    layer passes the ADOPTED expectation's line here
    (`vocation.render_what_for(record)`), which is the whole of the
    conditioning's prompt side: ONE line moves, and the measured clauses
    of the model-of-itself never do."""
    return with_what_for(
        SELF_MODEL_TEMPLATE.format(
            horizon=f"{horizon:g}",
            coverage=f"{coverage:.3f}", candidates=int(candidates),
            open_commitments=int(open_commitments), expired=int(expired),
            backlog=int(backlog), backlog_share=f"{backlog_share:.3f}",
            budget_total=int(budget_total), spent_last=int(spent_last)),
        what_for)


# ==========================================================================
# (c) THE COMMITMENT TRACKER — the open set and its boundary scoring.
# ==========================================================================

@dataclass(frozen=True)
class CommitmentReport:
    """One boundary's scoring outcome, as observables."""
    turn: int
    scored: int            # commitments whose deadline had passed and
                           # which were affordable to score this boundary
    fulfilled: int         # done(target) had landed by the deadline
    expired: int           # it had not — an OBSERVABLE, never debt
    deferred: int          # due but not affordable this boundary
    charged: int           # derivations charged to the ledger for scoring
    open_after: int        # the open set after scoring


@dataclass
class CommitmentTracker:
    """`expect(tX)` spans, registered at emission and SCORED AT WINDOW
    BOUNDARIES.  RAM state (carried by the C8 checkpoint), nothing
    durable: a commitment is not an assertion and writes no fact.

    T (`horizon`) is the per-campaign commitment horizon — an
    `expect(tX)` emitted at turn n must land by n + T.  It is a DESIGN
    PARAMETER, constant within a run and a swept axis across runs
    (decision 2: T = 100, three anchors — T_set = 100 in the model's own
    calibrated window, TAU_S_TURNS = 100 in this substrate, and one turn
    = one t.u.).  NO T-PROPORTIONAL CHARGE IS INVENTED: the model's
    c_int(T) standing cost does not transfer, and the agent's real
    standing inward cost is the priced retrieval, independent of T.

    Scoring charges FIRST, through the SAME C11 ledger the assertions
    use (the mmin priced-sensor convention: the standing cost is paid
    before the work), at ONE engine-reported `check_cost` per scored
    commitment; a due commitment the boundary turn cannot afford is
    DEFERRED (still open) and reported, never silently dropped.

    DEFERRAL'S TIMESCALE, STATED (the review's S3, recorded rather than
    left latent): the affordability test reads the per-turn ledger, and
    the ledger is opened by `check_turn` — so scoring sits inside the
    BOUNDARY turn's own spend, and a commitment deferred here is retried
    at the NEXT BOUNDARY (TAU_S_TURNS turns later), not on the next turn.
    With the default budget (10 000 derivations/turn, against a stub
    engine's cost of 1) nothing defers, so this is latent, not live; and
    a never-affordable due commitment stays open and retried forever,
    which is the runaway observable rather than a leak (it is visible in
    the report's `deferred` count and in `open_after`)."""
    horizon: float = 100.0
    open: list = field(default_factory=list)
    fulfilled: int = 0
    expired: int = 0
    total_registered: int = 0

    def register(self, turn: int, commitments) -> int:
        """Add this turn's commitments to the open set.  NO charge, NO
        verdict, NO debt — a prediction checked at the instant it is
        made cannot fail (the tautology-test class)."""
        for c in commitments:
            self.open.append(c)
        self.total_registered += len(commitments)
        return len(self.open)

    def due(self, turn: int) -> list:
        """The open commitments whose horizon has passed (`deadline <=
        turn`).  Deadline is inclusive: an `expect(tX)` emitted at turn n
        with T = 100 must land by turn n + 100."""
        return [c for c in self.open if float(c.deadline) <= float(turn)]

    def score(self, *, turn: int, engine, ledger, budget) -> CommitmentReport:
        """Score every DUE commitment by a REAL engine lookup, charging
        each FIRST.  `fulfilled` iff `done(target)` holds; otherwise
        `expired` — an observable.  An unaffordable due commitment is
        deferred (kept open) and counted."""
        scored = fulfilled = expired = deferred = 0
        charged = 0
        still_open: list = []
        for c in self.open:
            if float(c.deadline) > float(turn):
                still_open.append(c)
                continue
            target = c.target
            try:
                cost, depth = engine.check_cost("done", (target,))
            except Exception:                       # noqa: BLE001
                # an undeclared/unpriceable relation: the cost is
                # UNKNOWN, and inventing one would be the unit-conversion
                # violation.  The commitment is counted DEFERRED (kept
                # open, to be retried at a later boundary) — never SCORED
                # against a fabricated price, and never dropped.  (The
                # report field for this path is `deferred`; the two names
                # are the same outcome, and this comment now says so.)
                deferred += 1
                still_open.append(c)
                continue
            remaining = (budget.derivations_per_turn
                         - ledger.spent_this_turn)
            if int(cost) > remaining:
                deferred += 1
                still_open.append(c)
                continue
            ledger.charge(int(cost), int(depth))
            charged += int(cost)
            try:
                landed = bool(engine.lookup("done", (target,)))
            except Exception:                       # noqa: BLE001
                landed = False
            scored += 1
            if landed:
                fulfilled += 1
                self.fulfilled += 1
            else:
                expired += 1
                self.expired += 1
        self.open = still_open
        return CommitmentReport(turn=turn, scored=scored,
                                fulfilled=fulfilled, expired=expired,
                                deferred=deferred, charged=charged,
                                open_after=len(self.open))

    # -- the C8 resume surface ------------------------------------------
    def dump(self) -> dict:
        return {"horizon": float(self.horizon),
                "open": [_commitment_cp(c) for c in self.open],
                "fulfilled": int(self.fulfilled),
                "expired": int(self.expired),
                "total_registered": int(self.total_registered)}

    def load(self, state) -> None:
        """Fail-closed like every other seat: a state that is not this
        seat's shape raises rather than silently emptying the open set
        (an empty open set would read as 'no goals', a MEASURED-looking
        artifact of a lost checkpoint)."""
        if not isinstance(state, dict) or "open" not in state:
            raise ValueError(
                f"commitment-tracker checkpoint is not a tracker shape: "
                f"{type(state).__name__} — refusing (C8 fail-closed)")
        self.horizon = float(state["horizon"])
        self.open = [_commitment_from_cp(d) for d in state["open"]]
        self.fulfilled = int(state["fulfilled"])
        self.expired = int(state["expired"])
        self.total_registered = int(state["total_registered"])


def _commitment_cp(c) -> dict:
    return {"id": c.commitment_id, "le": c.le_text,
            "terms": list(c.terms), "turn": int(c.turn),
            "deadline": float(c.deadline)}


def _commitment_from_cp(d: dict):
    from cen import Commitment
    return Commitment(commitment_id=d["id"], le_text=d["le"],
                      terms=tuple(d["terms"]), turn=int(d["turn"]),
                      deadline=float(d["deadline"]))


# ==========================================================================
# (d) THE a_hold SEAT — the agent's causal path into the plant.
# ==========================================================================
# THE INWARD STREAM IS THE MODEL'S OWN TRACE.  There is ONE quantity
# (the share of a turn that stayed INWARD — never submitted to the
# checker, R1's unchecked return path) measured on the TWO instruments
# the substrate offers, and the code says which is primary:
#   * `inward_share_trace` — PRIMARY: the model's own channel separation,
#     `|thinking| / (|thinking| + |content|)` (the reasoning model's
#     message.thinking vs message.content, dmn_llm's chat path).  THIS is
#     the normalization S2 asked for: self-directed vs task-directed.
#   * `inward_share` — FALLBACK, the pre-trace instrument: the
#     extractor's prose bytes over the stream bytes, for the
#     /api/generate path, where the model has no separate trace field.
#     It is a step function of "did the generator write prose at all"
#     (MEASURED 0.9848 on the plan's own content buffer) and is kept
#     ONLY so the pre-trace arms still run and are comparable.
#
# THE SEAT IS ONLY MEANINGFUL WITH A TRACE-BEARING EMITTER (the
# dependent surface the re-point's review found unstated,
# `handoff-selfreg-repoint-review-result` finding 2).  The trace is the
# only input that MOVES WITH THE SELF in the direction the mapping
# needs; the prose fallback is a step function of "did it write prose at
# all" and SATURATES (MEASURED 0.9848 on a non-self-referential buffer),
# so ANY CAMPAIGN ARM RUN ON `api="generate"` (or any emitter without a
# trace channel) WITH THE SEAT ON COLLAPSES THE PLANT REGARDLESS OF SIGN
# — it measures the wiring, not the self.  A generate-path seat-on run
# is a WIRING DEMO; the a_hold MAPPING's instrument is the chat path's
# `message.thinking`, and an emitter that stops delivering the trace is
# REFUSED rather than scored zero (`dmn_llm._parse_chat`, S1).

def inward_share_trace(thinking: str, content: str) -> float:
    """THE INWARD SHARE from the model's OWN two streams — THE PRIMARY
    NORMALIZATION (`S2`): `|thinking| / (|thinking| + |content|)`, the
    self-directed share of the turn's emitted bytes against the
    task-directed share.

    WHY THE TRACE AND NOT A STRUCTURAL RATIO OF THE OUTWARD STREAM
    (MEASURED — `handoff-selfreg-self-review-result` item 3): the
    prose/(prose+span) ratio is nearly a STEP FUNCTION of "does the
    generator write prose at all" — the plan's OWN non-self-referential
    content buffer scored 0.9848 and collapsed the plant identically to
    the self-referential arm (G_end 0.2903 vs 0.2905), so a separator
    resting on a zero-prose register describes no real model.  The
    trace/content split is the model's OWN channel separation (native in
    the reasoning model's chat template) and it MOVES WITH THE SELF:
    MEASURED at hf.co/lmstudio-community/Ministral-3-14B-Reasoning-2512-
    GGUF:Q6_K (n=6, fixed seeds, `handoff-selfreg-sign-probe-result`) —
    self present: mean self-ref density 7.2/100w, mean OUTWARD content
    2550 chars; self gone: 10.8 and 556.  A thinned self -> relatively
    more inward, less outward: the direction the a_hold mapping needs.

    WHAT IT IS NOT (stated, §1a): a SEMANTIC measure of self-reference.
    It is a size ratio of the two channels, and the probe's other mover
    (self-reference DENSITY of the trace, 7.2 -> 10.8) is not in it.  The
    measurable mover here is the content collapse (2550 -> 556)."""
    t = len(thinking.strip()) if isinstance(thinking, str) else 0
    c = len(content.strip()) if isinstance(content, str) else 0
    denom = t + c
    if denom <= 0:
        return 0.0
    return max(0.0, min(1.0, t / denom))


def inward_share(stream: str, prose: str) -> float:
    """THE INWARD SHARE measured on the PRE-TRACE instrument — the
    FALLBACK for a generator that has no separate trace field (the
    /api/generate path).  `inward_share_trace` is PRIMARY (above); this
    one survives so the pre-trace arms still run and stay comparable.

    It is the extractor's PROSE bytes over the whole stream: the agent's
    CONTENT that stays INWARD — never submitted to the checker (R1's
    unchecked return path) — over the content it emitted.

    Measured as `len(prose.strip())` over `inward + outward`, where the
    OUTWARD part is the bytes the extractor removed as checked spans
    (`len(stream) - len(prose)`).  The STRIP is not cosmetic: the
    newlines left between removed span lines are the extractor's
    structural residue, not content, and counting them would give a
    claim-only stream — a generator that reports nothing but claims, the
    exact NON-self-referential register this seat must be able to
    distinguish — a nonzero inward share by construction.  With the
    strip, a claim-only stream is EXACTLY 0.0.

    OFF-TRANSCRIPT AND CEN-SIDE by construction: both arguments are the
    extractor's own outputs (`interleave.build_batch` returns the
    extracted prose beside the routed claims), so nothing here reads the
    generator's self-report and nothing here is an LLM measurement
    (rule 8).  [STRUCTURAL PROXY, AND A SATURATED ONE — see the module
    docstring's stated gap: this measures how much of the output stays
    inward, not what it is about, and it is nearly a STEP FUNCTION of
    "does the generator write prose at all".  MEASURED on the plan's own
    NON-self-referential content buffer: 0.9848, collapsing the plant
    identically to the self-referential arm (G_end 0.2903 vs 0.2905 —
    `handoff-selfreg-self-review-result` item 3).  So the generator-class
    clause below holds only for the claim-only register, i.e. for a
    generator emitting EXACTLY zero prose, which no real LLM occupies.
    The arms that separate the signs use `inward_share_trace`.]"""
    inward = len(prose.strip())
    outward = max(0, len(stream) - len(prose))
    denom = inward + outward
    if denom <= 0:
        return 0.0
    return max(0.0, min(1.0, inward / denom))


# ==========================================================================
# THE SELF-REFERENTIAL DENSITY — the SIGN PROBE's own observable, kept
# here so the corrected experiment can re-run it on recorded traces.
# ==========================================================================
#: THE LEXICON, BYTE-FOR-BYTE from the instrument that MEASURED the sign
#: (`~/thing/ops/density_test.py:21`: "SELFREF = first-person pronouns").
#: It is deliberately reused rather than reinvented: the preregistered
#: MANIPULATION gate is a comparison against a number this exact regex
#: produced (self PRESENT 7.2/100w vs self GONE 10.8/100w, n=6, fixed
#: seeds — `handoff-selfreg-sign-probe-result`), and a new count would be a
#: new instrument, i.e. a number that cannot be compared with the record.
SELFREF_RX = re.compile(r"\b(i|my|me|myself|mine|i'm|i've|i'll)\b", re.I)


def selfref_density(text: str, per_words: float = 100.0) -> float:
    """THE SELF-REFERENTIAL DENSITY of an emitted trace: first-person
    pronoun hits per `per_words` WORDS of the text (the sign probe's
    'self-ref/100w').  LLM-FREE and deterministic — a lexicon count on the
    model's own output, so it costs nothing and cannot be gamed by the
    model, and it is reproducible offline on a recorded trace (which is why
    `exp_agent_coupling.RecordingDMN` now keeps `trace_text`).

    WHAT IT IS NOT (the standing order's marking rule): it is NOT a
    semantic measure of self-reference.  A first-person pronoun is a WORD,
    and the sign probe's own SECOND mover (`inward_share_trace`, the
    channel-size ratio) is a different quantity that happens to move in the
    same direction.  The two are logged BESIDE each other, never merged:
    the drive reads the ratio, the manipulation check reads this, and a
    disagreement between them is a finding rather than an average.

    AN EMPTY OR WORDLESS TEXT IS 0.0 (no self-reference was emitted), which
    is a MEASUREMENT here — unlike the channel ratio, where a zero
    denominator has no reading at all and `inward_share_trace` returns 0.0
    by the same convention.  A caller that needs "was there a trace at all"
    must read `trace_chars is None` (the declared-absence protocol), not
    this number."""
    words = [w for w in str(text or "").split() if w.strip()]
    if not words:
        return 0.0
    hits = len(SELFREF_RX.findall(str(text)))
    return hits * float(per_words) / len(words)


class SelfReferentialDrive(Schedule):
    """THE a_hold SEAT — a `dpdr.model.Schedule` whose `a_hold` channel
    carries the agent's inward drive ON TOP OF the schedule's own value.

    `harness.py:279` reads `a_hold = sch.value('a_hold', self.t)`, so a
    schedule that answers with the agent's measured inward load is the
    one path by which the agent's self-referential output reaches the
    plant's dynamics: a_hold -> a rises -> the growth term
    beta_G*(1-a)*G*(1-G) starves -> G collapses.
    (`handoff-selfreg-agent-plant-path`; p2reconcile2 retired the
    backlog->D path and this seat is the replacement that keeps the
    plant's c the plant's own.)

    THE SEAT IS THE CALLER'S: this class is constructed by whoever
    supplies the run's schedule, never by the harness (which only CALLS
    `set_drive` at a consolidation boundary when the schedule exposes
    it), and a plain `Schedule` is passed through untouched — so every
    default run is byte-identical and the seat is OFF by default.

    `gain` is the MAPPING's scale (the agent's inward share -> a
    dimensionless hold in [0,1]), default 1.0 and NOT tuned to make
    anything fire: the falsifier's asymmetry is seat-ON vs seat-OFF at
    the default, and the mechanism is driven by a measured quantity, not
    chosen.  The sum is CLIPPED at 1.0 because `a_hold` is a hold
    fraction in the model's own [0,1] range (the frozen failure schedule
    uses 0.9); an unclipped sum would leave the model's calibrated
    range, and the clip is the model's own domain, not a lever.
    """

    def __init__(self, base, gain: float = 1.0, clip: float = 1.0):
        self.base = base
        self.gain = float(gain)
        self.clip = float(clip)
        self.drive = 0.0
        self.drive_history: list = []

    # -- the harness's per-window write ---------------------------------
    def set_drive(self, value: float, turn: int | None = None) -> None:
        """Set the window's inward drive.  Called ONCE PER CONSOLIDATION
        WINDOW by the harness (the correction: the self is per-window,
        not per-turn); `turn` is recorded so the history is auditable."""
        self.drive = max(0.0, min(1.0, float(value)))
        self.drive_history.append((turn, self.drive))

    # -- the Schedule surface the plant reads ---------------------------
    def value(self, ch: str, t: float) -> float:
        v = self.base.value(ch, t)
        if ch != "a_hold":
            return v
        return min(self.clip, v + self.gain * self.drive)

    def breakpoints(self) -> list:
        return self.base.breakpoints()

    @property
    def channels(self):
        return getattr(self.base, "channels", {})

