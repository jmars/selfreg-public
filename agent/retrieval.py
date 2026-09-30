"""THE RETRIEVAL LAYER (item 'retrieval'; design/architecture.md 11c)
— how the self enters the context, AT A PRICE.

The piece this module closes: the agent had a durable store (C19), a
CEN, and NO retrieval layer — the self never entered the context at
all, which is paper 1's LIMITATION 15 ("the model has no memory
term").  The design's replacement is MEMORY AS A PRICED STANDING COST:
retrieval that grows with the store, so the self THINS when the budget
binds (failure class (D), design/architecture.md 5a).

THE SETTLED DESIGN (full-read literature pass, reference/lit-search.md
B7 — NOT re-opened here).  The three "candidates" the design once
listed were never three options:

  * CONSOLIDATION is offline PREDICTIVE COMPRESSION (Fountas et al.
    2603.04688: compression toward "a minimal sufficient statistic for
    predicting Y"; the encoder CANNOT retroactively modify a stored
    memory — "only an offline process that retrieves and refines the
    stored state can optimise the representation after the fact").
    That is C18 + C19's justification.  NOT this module's job: the
    consolidation SCHEDULE is item 12's reconciliation, and the
    predictive-compression codec does not exist yet (seat below).
  * INJECTION is RECONSTRUCTION (GENESIS, 2510.15828: QUERY ->
    retrieved key (pointer) -> retrieved value (COMPRESSED) -> cortex
    decoder DECODES the value -> reconstruction, behind an explicit
    capacity bottleneck).  The injected artifact is a reconstruction
    from retrieved values, NOT a copy of the record.  THIS module.
  * FORCED COMPACTION is DROPPED (a fixed-context-window artifact; the
    model has no capacity term — class (D) is explicitly "not any of
    A-C" — so a spatial trigger has nothing to bind to).

THE LOAD-BEARING REQUIREMENT: RETRIEVAL IS PRICED, AND THE CHARGE IS A
FUNCTION OF THE RETRIEVED SET — NOT A FLAT PER-CALL FEE (2506.01659:
dense coding "activates many overlapping neurons, increasing metabolic
cost"; sparse coding activates "small, distinct neurons" — cost scales
with the EXTENT brought back).  Implemented as: the seat asks the
ENGINE for each entry's cost through the EXISTING C11 surface
(check_cost -> (derivations, cut_depth)) and charges the SUM over the
retrieved set.  No constant is invented: the per-entry charge IS the
engine's own ground-consultation report (1 derivation at depth 0
today), and the aggregation over the retrieved set is the only
model-derived step.  If retrieval were free, G would be non-depletable
and the pilot's retention-1.000 defect ("nothing was consumed, so the
model's mechanism was never engaged", architecture.md:176) would be
reproduced — the free arm exists in this module ONLY as that control.

THE ONE REAL TENSION, RECONCILED EXPLICITLY.  Class (D) describes a
STANDING cost; CostBudget.within_turn is a PER-TURN gate.  Retrieval
happens EVERY turn (the self is NOT carried on the working set —
survivability.md:68 — so it must be re-established each turn from the
store), so a per-turn retrieval charge that GROWS WITH STORE SIZE is
the natural reconciliation: the standing cost is paid as a per-turn
charge inside the same per-turn ledger the assertions use (charged
FIRST, like the priced-sensor convention in mmin.py).  CONSEQUENCE,
stated plainly: at a fixed derivations_per_turn B and a store of N
self entries, the affordable retrieval is min(N, B) entries and the
reconstruction covers min(N, B)/N of the self — the per-turn budget
left for WORK is B - min(N, B), which reaches zero at N >= B.  From
that point the loop misses its own budget (class (D) made per-turn).
The model's predicted escape is attention redirection OUTWARD (5, rule
3) — the regulator's lever, not retrieval's; this module prices the
inward stream and does not engineer around the crowding out.

SEAT 2 — ACCESS EPOCHS + DECAY OF RETRIEVAL WEIGHT (C20, terms
DECIDED, implemented not reinvented): "the record stays immutable, the
retrieval weight decays; accesses recorded as EPOCHS in the RAM
working set, decay applied AT CONSOLIDATION; rate derivable from the
budget (decay_rate x steady_state <= budget); ERR SLOW — decaying
something needed is silent, explosion is loud."  Decay here reduces
REACHABILITY (the selector's rank), NEVER the record — C19: no
deletes, ever; the battery proves the record byte-identical across
decay.  Err slow is implemented as the DEFAULT rate 1.0 (no decay
until a budget-derived rate is supplied); derive_decay_rate() solves
C20's inequality for the largest admissible rate.

R5 — EXTERNAL OWNERSHIP OF THE SELECTOR.  The reconstruction must not
select its own evidence; any selector on the mechanism's own operating
state must be externally owned.  Here the selector is a designer-built
object injected at CEN construction, and it is CONTENT-BLIND: it plans
from (key, turn, weight, cost) only — it never sees entry content, so
the self cannot steer its own retrieval even indirectly by shaping
what it writes.  Battery part D6 asserts this structurally (AST).

EVIDENCE MARKING (the standing order: the model is the specification;
never weaken it to make engineering easier).
  LITERATURE-SUPPORTED (the FORM): reconstruction at injection;
    predictive compression at consolidation; retrieval priced by
    EXTENT.  [reference/lit-search.md B7.1-B7.4]
  MODEL-DERIVED / PROJECTION (the NUMBERS): the linear aggregation of
    per-entry engine-reported costs into a set charge; the decay rate
    (C20's own status: "rate accounting PROJECTION"); the reading of
    "metabolic cost" (neural-density cost in 2506.01659, snippet-level
    there) as our derivation units is OUR INTERPRETATION, not a
    measurement.
  UNEXERCISED SEATS, reported honestly (never silently dropped):
    ValueCodec.compress — the consolidation stage's predictive
    compression pass exists as a SEAT INJECTION (memory_codecs at the
    memory consolidation boundary, DEFAULT OFF) but is NOT the default:
    with no policy/registry injected the honest codec is IDENTITY,
    stated, not hidden.
    The retrieval CUE — today's cue is the fixed identity cue ("the
    self"); no similarity/embedding surface exists, so no content-based
    cueing is implemented (and content-blind selection is what R5
    wants anyway).

Run the demonstration battery:  stage2_retrieval_tests.py (D1-D8).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence

__all__ = [
    "DEFAULT_SELF_RELATION", "EntryState", "RetrievalSelector",
    "AffordabilitySelector", "ValueCodec", "IdentityCodec",
    "AccessEpochs", "derive_decay_rate", "RetrievalSeat",
    "RetrievalOutcome", "Reconstruction",
]

#: The relation whose entries are the SELF's store entries: the CEN's
#: write-class-(ii) persist-as-is relation, committed once per DMN turn
#: as ("self_content", turn, content).  Retrieval's default candidate
#: pool is exactly this relation (the identity cue).
DEFAULT_SELF_RELATION = "self_content"


# ==========================================================================
# The selector's input — CONTENT-BLIND by construction (R5).
# ==========================================================================

@dataclass(frozen=True)
class EntryState:
    """One retrieval candidate as the selector sees it: identity (key),
    recency (turn), decayed retrieval weight, and the ENGINE-REPORTED
    cost of retrieving it (C11 derivations, via DatalogEngine.
    check_cost on the entry's ground atom).  Deliberately NO content
    field: a selector that could read content would let the self choose
    its own evidence by shaping what it stores (R5).  `turn` is the
    store's own turn column: an int for ordinary entries, and a STRING
    for the codec layer's supersession entries ('-4c1', memory_codec_
    seat) — the selector ranks it beside its original (the string and
    numeric orderings agree by construction), never parses it."""
    key: str
    turn: int | str
    weight: float
    cost: int


class RetrievalSelector(Protocol):
    """The externally-owned selection policy (R5).  Implemented by the
    DESIGNER (the harness config / the test), injected into the CEN's
    retrieval seat; the reconstruction and the DMN have no path to it.
    `budget` is the remaining per-turn derivation budget (None = the
    unpriced CONTROL arm — take everything)."""

    def plan(self, candidates: Sequence[EntryState],
             budget: int | None) -> tuple[str, ...]: ...


def _rank_turn(turn) -> float:
    """Recency as a single comparable number for the selector's tie-
    break: the turn itself for ordinary (int) entries, and for the
    codec layer's STRING supersession keys ('-4c1' = the entry at turn
    -4, re-encoded at window 1) the NUMBER the key embeds — so a
    supersession entry ranks EXACTLY beside the original it replaces
    (same content, same recency), never parsed as prose and never
    pushed to an extreme of the order."""
    if isinstance(turn, bool) or not isinstance(turn, (int, float)):
        s = str(turn)
        head = s.split("c", 1)[0]
        try:
            return float(head)
        except ValueError:
            return 0.0
    return float(turn)


class AffordabilitySelector:
    """The default external selector: rank by DECAYED RETRIEVAL WEIGHT
    (desc), break ties by recency (turn desc) then key (canonical), and
    take the maximal affordable prefix — the prefix whose engine-
    reported costs sum within the budget.  This is where "the
    affordable retrieval shrinks as the store grows" is mechanical: at
    a fixed budget the prefix length is bounded by the budget, while
    the candidate pool grows with the store, so the covered FRACTION of
    the self falls.  MODEL-DERIVED: the weight-then-recency ranking and
    the prefix rule are ours (the literature fixes the price-by-extent
    form, not the ranking)."""

    def plan(self, candidates: Sequence[EntryState],
             budget: int | None) -> tuple[str, ...]:
        ranked = sorted(candidates,
                        key=lambda e: (-e.weight, -_rank_turn(e.turn),
                                       e.key))
        if budget is None:                    # the free-retrieval CONTROL
            return tuple(e.key for e in ranked)
        out: list[str] = []
        spent = 0
        for e in ranked:
            c = max(0, int(e.cost))
            if spent + c > budget:
                break
            out.append(e.key)
            spent += c
        return tuple(out)


# ==========================================================================
# The value codec — CONSOLIDATION's compression seat, IDENTITY by
# default; the codecs themselves live in memory_codecs.py (injected,
# never constructed here — this module stays the SEAT, not the
# implementations).
# ==========================================================================

class ValueCodec(Protocol):
    """compress() is CONSOLIDATION's predictive compression (C18: "a
    minimal sufficient statistic for predicting Y"); decode() is the
    INJECTION-side generative decoder (GENESIS: QUERY -> retrieved key
    -> retrieved compressed value -> decoder DECODES the value ->
    reconstruction).  The QUERY is part of GENESIS's own data path, and
    it is KEYWORD-ONLY with a default so every codec that cannot
    condition on it stays valid: IDENTITY passes the value through
    unchanged, and SCHEMA's decode is a deterministic instantiation
    that is EXACT by construction — the query is NOT part of its
    contract, and it ignores it (stated, never faked — a codec that
    pretended to need the query would be a fabricated dependency).
    Only the GIST codec's decode CONDITIONS on the query (the
    generative half: the reconstruction is rebuilt toward the retrieval
    cue).  A default `query=""` means "no retrieval cue in force" and
    every codec must treat it exactly as an ABSENT cue, never as a
    literal empty string to match against.

    THE SEAT'S HONEST DEFAULT: with no codec layer injected the codec
    is IDENTITY and both halves are trivial — the seat is built, the
    distinction is stated, nothing is fabricated.  The wiring that
    makes the query LOAD-BEARING (memory consolidation over a codec
    registry) lives in memory_codecs.py + stage2_harness, both DEFAULT
    OFF; this module is read-only with respect to that layer."""

    def compress(self, content: str) -> str: ...
    def decode(self, compressed: str, *, query: str = "") -> str: ...


class IdentityCodec:
    """The honest default codec: content passes through unchanged.  The
    query is accepted and IGNORED — identity has no generative step to
    condition (stated rather than faked); when the codec layer lands a
    real codec this is replaced and the reconstruction becomes
    generative from genuinely compressed values."""

    def compress(self, content: str) -> str:
        return content

    def decode(self, compressed: str, *, query: str = "") -> str:
        del query               # accepted for seat symmetry, unused
        return compressed


# ==========================================================================
# SEAT 2 — access epochs + decay of retrieval weight (C20).
# ==========================================================================

def derive_decay_rate(budget: int, steady_state: int) -> float:
    """C20's DECIDED rate rule, solved: the largest rate rho <= 1 with
    decay_rate x steady_state <= budget, i.e. min(1.0, budget /
    steady_state).  MODEL-DERIVED / PROJECTION (C20's own status):
    the inequality is the design's; reading it as "the per-entry rate
    times the steady-state reachable set must fit the budget" and
    solving for the LARGEST rate is ours — largest because C20 says
    ERR SLOW (decaying something needed is silent, explosion is loud).
    A budget at or above the steady-state size yields rho = 1.0: no
    decay until the store outgrows the budget.

    STEADY-STATE ACCOUNTING (stated, honest): `steady_state` is the
    designer's reachable-set target N_ss (the number of entries whose
    decayed weight keeps them rankable); with rho = B / N_ss and a
    retrieval floor of w >= rho^W (W consolidation windows since last
    access), the steady-state reachable set is K*(1-rho^(W+1))/(1-rho)
    for K accesses per window — at B=10, N_ss=20 (rho=0.5, W=4 at
    floor 1/16): K=1 -> ~2 reachable entries (charge ~2 <= 10), K=5 ->
    ~10 (== B), K=10 -> ~19 (> B: the budget binds and the selector
    truncates — which is the mechanism engaging, not a defect).  The
    accounting is PROJECTION: it is arithmetic on the decided
    inequality, not a measurement of a running system."""
    if steady_state <= 0:
        return 1.0
    return min(1.0, float(budget) / float(steady_state))


class AccessEpochs:
    """Accesses recorded as EPOCHS in the RAM working set (C20), with
    decay applied AT CONSOLIDATION.  An EPOCH is the consolidation-
    window index at access time; the retrieval weight of an entry is
    rho ** (consolidations_since_its_last_access), evaluated LAZILY —
    consolidate() only advances the window counter, so decay is exact,
    idempotent per window, and touches NOTHING on disk (the record
    stays byte-identical; battery part D5 proves it).

    WORKING-SET BOUND (the bound is part of the mechanism —
    architecture.md:176): per-key footprint is O(1) in RAM (the last
    access epoch plus an access count), regardless of how many times
    an entry was retrieved.  The epoch table is metadata, never the
    self: it carries no content.  Its own standing cost is O(N) small
    records for a store of N entries — a named consequence of C20's
    own design (epochs live in the working set); prune_below() is the
    matching C20 fix: an entry whose weight has fallen below a floor
    may have its epoch record dropped from the working set (reach-
    ability floor, NOT a delete — the store's bytes are untouched).
    Default floor 0.0 never prunes: ERR SLOW.

    Decay reduces REACHABILITY (the selector's rank), never the
    record (C19: no deletes).  Default decay_rate = 1.0 — NO decay
    until a budget-derived rate is supplied (err slow; the derived
    form is derive_decay_rate above and is exercised in the battery).
    """

    def __init__(self, decay_rate: float = 1.0):
        if not (0.0 < decay_rate <= 1.0):
            raise ValueError(
                f"decay_rate must be in (0, 1] (C20 err slow: 1.0 is "
                f"no decay); got {decay_rate!r}")
        self.decay_rate = float(decay_rate)
        self._last_epoch: dict[str, int] = {}
        self._count: dict[str, int] = {}
        self._consolidations = 0
        # salience's initial-weight seeds (item 'encoding'): key ->
        # (seed epoch, seeded weight); subordinate channel — see
        # set_initial for why it exists at all.
        self._init: dict[str, tuple[int, float]] = {}

    # -- recording (the mechanism's own act, at retrieval time) --------
    def record(self, key: str) -> None:
        """Record one access at the CURRENT epoch (the consolidation-
        window index).  Called by the retrieval seat when an entry is
        actually retrieved — never by the DMN."""
        self._last_epoch[key] = self._consolidations
        self._count[key] = self._count.get(key, 0) + 1
        # an accessed entry's weight is its own history from here on
        # (C20); the seed was the first-use bias and is spent.
        self._init.pop(key, None)

    # -- the decayed retrieval weight -----------------------------------
    def weight(self, key: str) -> float:
        last = self._last_epoch.get(key)
        if last is None:
            # selective encoding's subordinate channel (salience.
            # set_initial): an entry seeded at encoding time decays
            # from its SEED epoch exactly as an accessed one does; an
            # unseeded, unaccessed entry keeps the uniform 1.0 (the
            # pre-encoding behaviour, byte-identical).
            seed = self._init.get(key)
            if seed is not None:
                ep, w = seed
                return w * (self.decay_rate **
                            (self._consolidations - ep))
            return 1.0        # never accessed: full weight until decayed
        return self.decay_rate ** (self._consolidations - last)

    def access_count(self, key: str) -> int:
        return self._count.get(key, 0)

    # -- salience's initial-weight SEAT (item 'encoding'; salience.py --
    # -- is the caller; subordinate channel, see below) -----------------
    def set_initial(self, key: str, weight: float) -> None:
        """Seed an entry's INITIAL retrieval weight from its encoding
        salience (selective encoding's SECOND, subordinate channel:
        storage automatic, encoding selective — the weight seat is how
        salience initializes rank, beside the tier gate that is the
        mechanism of record).

        NOT A REWRITE OF AN ACCESSED ENTRY (C20: the record is
        immutable and so is the access history): refused for a key the
        table has already RECORDED (its weight is then the product of
        its own access history, and overwriting that would be exactly
        the silent re-weighting this module refuses to be), and refused
        for a weight outside (0, 1] (0 would rank the entry below
        every decayed tail — a delete-in-effect; a first access
        re-establishes full rank as usual).

        WHY THIS SEAT EXISTS AT ALL, stated honestly: a BINDING BUDGET
        LAUNDERS A SOFT WEIGHT (model-MEASURED: block 0.0481 vs
        down-weighted 0.7532 vs naive 0.7784 — paper-2-draft.md:276;
        node handoff-selfreg-values-result), so this channel is worth
        ~3% and is built ONLY beside the tier gate, never as the
        mechanism of record.  Implemented as a first-use bias: an
        unaccessed key's weight becomes the seeded value decayed by
        the windows since the seed, exactly as if that were its
        last-access epoch."""
        w = float(weight)
        if not (0.0 < w <= 1.0):
            raise ValueError(
                f"set_initial weight must be in (0, 1] (0 would be a "
                f"delete-in-effect on the entry's rank); got {weight!r}")
        if key in self._last_epoch or key in self._init:
            raise ValueError(
                f"set_initial refused for '{key}': the entry already "
                f"has an access/seed history (C20: weights are the "
                f"product of access history, never rewritten)")
        self._init[key] = (self._consolidations, w)

    def last_epoch(self, key: str) -> int | None:
        return self._last_epoch.get(key)

    @property
    def consolidations(self) -> int:
        return self._consolidations

    def keys(self) -> tuple[str, ...]:
        return tuple(sorted(self._last_epoch))

    # -- decay applied AT CONSOLIDATION (C20's decided placement) ------
    def consolidate(self) -> int:
        """Advance one consolidation window: every entry's weight is
        henceforth multiplied by decay_rate once more (lazily, through
        the window index — no state is rewritten, on disk or in RAM).

        THE SCHEDULE NOW EXISTS (item 12's schedule half).  The caller
        on the run path is the harness's THIRD, independent boundary
        window — `stage2_harness.Stage2State.memory_window_boundary`,
        taken at the first turn of a fresh state and every
        TAU_S_TURNS turns, wired OUTSIDE both the self seat (which
        returns early with `self_T=None`) and the routing seat (which
        this seat does not require).  Measured end-to-end on the live
        loop by the battery's D9 — before that wiring the ONLY caller in
        the tree was the battery itself, so `_consolidations` stayed 0,
        every weight was 1.0 and `Stage2Config.retrieval_decay` was
        inert.

        WHAT IS NOT RECONCILED, stated rather than implied: the TRIGGER
        is a fixed window, not a predictive criterion (the compression
        this placement exists for does not exist yet — the codec seat
        below), and eager per-turn consolidation is NOT run (the
        eager-vs-scheduled half of item 12 stays open).  The RATE is
        the caller's: 1.0 default = no decay, err slow."""
        self._consolidations += 1
        return self._consolidations

    # -- the working-set bound's own C20 fix (reachability floor) ------
    def prune_below(self, floor: float = 0.0) -> int:
        """Drop epoch RECORDS (working-set metadata only) for entries
        whose weight fell below `floor`.  NOT a delete: the store's
        record is untouched (C19/C20 — decay reduces reachability,
        never the record); a pruned entry that is retrieved again
        simply re-records at full rank.  Default floor 0.0 prunes
        nothing (err slow).  Returns how many epoch records dropped."""
        drop = [k for k in self._last_epoch if self.weight(k) < floor]
        for k in drop:
            del self._last_epoch[k]
            self._count.pop(k, None)
        return len(drop)

    # -- C8 resume surface ------------------------------------------------
    def dump(self) -> dict:
        return {"decay_rate": self.decay_rate,
                "last_epoch": dict(self._last_epoch),
                "count": dict(self._count),
                "consolidations": self._consolidations,
                "init": {k: [ep, w] for k, (ep, w)
                         in self._init.items()}}

    def load(self, state: dict) -> None:
        self.decay_rate = float(state["decay_rate"])
        self._last_epoch = {str(k): int(v)
                            for k, v in state["last_epoch"].items()}
        self._count = {str(k): int(v) for k, v in state["count"].items()}
        self._consolidations = int(state["consolidations"])
        # the seed table rides the checkpoint like every other piece
        # of working-set state (an empty table for every pre-encoding
        # checkpoint: the field is new, so absent reads empty).
        self._init = {str(k): (int(ep), float(w)) for k, (ep, w)
                      in state.get("init", {}).items()}


# ==========================================================================
# The reconstruction (the INJECTION artifact).
# ==========================================================================

@dataclass(frozen=True)
class Reconstruction:
    """What the reconstruction carries, as MEASURABLE quantities —
    coverage is a FRACTION (entries covered / candidate entries),
    deliberately unit-free so no token/derivation conversion ever
    happens here (the standing order: a unit conversion is a fidelity
    violation).  `text` is the injected artifact: the retrieved
    entries' decoded values in RETRIEVAL ORDER.  It differs from a
    copy of the record in three stated ways: it is PARTIAL (the
    affordable prefix only), it is WEIGHT-ORDERED (the working set's
    decay state, an ordering the record does not have — the record is
    append-only by turn), and each value passes through the codec's
    decode (identity by default: the codec seat's honest value; a
    codec layer may be injected at the memory consolidation boundary,
    DEFAULT OFF).  The record stays the
    anchor the reconstruction is measured against — it is ALLOWED to
    drift from it (that is the point of reconstruction-only)."""
    turn: int
    entries: int            # how many entries the reconstruction carries
    candidates: int         # how many the identity cue offered
    coverage: float         # entries / candidates (1.0 if no candidates)
    text: str
    keys: tuple[str, ...]   # the retrieved entries' keys, in order


def reconstruct(turn: int, values: Sequence[tuple[str, str]],
                candidates: int, codec: ValueCodec | None = None,
                *, query: str = "") -> Reconstruction:
    """Build the injected artifact FROM THE RETRIEVED VALUES ONLY (the
    GENESIS path: query -> retrieved value -> decoder -> reconstruction
    — the decoder sees the retrieval cue, which is what makes the
    query-conditioned half of the seat load-bearing for the codecs
    that condition).  R5: this function takes NO budget, NO selector,
    NO weights — it cannot choose what is retrieved; battery part D6
    asserts that structurally.  `values` is (key, compressed-value) in
    retrieval order; the codec decodes each (identity's decode ignores
    the query — stated at the codec).  `query` is the caller's
    retrieval cue ("" = none in force); it reaches the CODEC ONLY,
    never the selection, so it cannot become a selector the mechanism
    does not own."""
    codec = codec or IdentityCodec()
    keys = tuple(k for k, _v in values)
    text = "\n".join(codec.decode(v, query=query)
                     for _k, v in values)
    covered = len(values)
    cov = (covered / candidates) if candidates else 1.0
    return Reconstruction(turn=turn, entries=covered,
                          candidates=candidates, coverage=cov,
                          text=text, keys=keys)


# ==========================================================================
# SEAT 1 — the chargeable retrieval seat (price = a function of the
# retrieved set, in C11 units, reported by the ENGINE).
# ==========================================================================

@dataclass(frozen=True)
class RetrievalOutcome:
    """One turn's retrieval, fully observable for measurement.  All
    cost fields are C11 units (derivations / cut depth) exactly as the
    engine reported them — never wall time, never tokens."""
    turn: int
    priced: bool
    candidate_count: int
    retrieved: tuple[str, ...]        # keys, in retrieval order
    derivations: int                  # the charge: SUM of per-entry
                                      # engine-reported derivations
    cut_depth: int                    # max engine-reported depth (0)
    truncated: bool                   # a plan exceeding the remaining
                                      # budget was cut by the seat
    reconstruction: Reconstruction
    budget_before: int                # per-turn budget remaining just
                                      # before the charge (the
                                      # reconciliation observable)


class _EnvelopeCodec:
    """The decode-path ADAPTER the seat hands `reconstruct` when the
    codec layer's envelope is in play (item 'codec').  compress is the
    seat's OWN codec (per-turn, identity by default — the seat never
    re-encodes, encode belongs to the consolidation boundary); decode
    routes envelope-carrying values through the INJECTED decoder (with
    the query) and everything else through the seat's codec — the
    codec layer's own floor, that every pre-codec store byte stays
    decodable.  With no decoder injected the adapter is behaviourally
    the seat's codec (a bare-tag check neither codec can fail), so the
    default path is byte-identical."""

    _TAG = "CENCODE/1 "

    def __init__(self, codec, envelope_decoder):
        self._codec = codec
        self._decoder = envelope_decoder

    def compress(self, content: str) -> str:
        return self._codec.compress(content)

    def decode(self, compressed: str, *, query: str = "") -> str:
        if self._decoder is not None \
                and (compressed or "").startswith(self._TAG):
            return self._decoder(compressed, query=query)
        return self._codec.decode(compressed, query=query)


class RetrievalSeat:
    """The CEN-side seat: enumerate the cue's candidates, ask the
    ENGINE for each entry's cost (check_cost — the same surface
    _check_one uses), let the EXTERNAL selector plan under the
    remaining per-turn budget, reconstruct from the retrieved values,
    and charge the ledger the SUM of the engine-reported costs.

    Charged FIRST in the turn (before any assertion), like the priced
    sensor in mmin.py — the standing cost is paid before the work, so
    as the store grows the work sees a shrinking remainder.  `priced
    = False` is the CONTROL ARM ONLY (retrieval at zero price): it
    exists to reproduce the pilot's retention-1.000 defect and must
    never be a default.

    THE ENVELOPE DECODER (item 'codec'; DEFAULT None = off): the
    CONSOLIDATION side may store values in the codec layer's
    self-describing envelope (memory_codecs.ENVELOPE_TAG).  When
    `envelope_decoder` is injected (any callable `(stored) -> str`,
    e.g. memory_codec_seat.decode_value with a bound registry), the
    reconstruction's decode path routes envelope-carrying values
    through it — WITH THE QUERY (the retrieval cue, passed by callers
    that have one; the GIST reconstruction conditions on it, schema
    and identity ignore it by construction).  Values WITHOUT an
    envelope decode exactly as before (the codec layer's own floor:
    every pre-codec store byte stays decodable), so with no decoder
    injected — the default — the seat's behaviour is byte-identical to
    the pre-codec loop, envelopes or not (an envelope an old run
    cannot decode is an explicit, loud configuration gap, not a silent
    wrong value: it surfaces as the raw envelope bytes, the honest
    degraded read).

    The seat writes NOTHING durable: accesses land in the RAM epoch
    table, the charge in the ledger, the reconstruction on the turn's
    result (per-turn context — carrying it across turns would put the
    self on the working set, which is the trap survivability.md:68
    names)."""

    def __init__(self,
                 selector: RetrievalSelector | None = None,
                 epochs: AccessEpochs | None = None,
                 codec: ValueCodec | None = None,
                 relation: str = DEFAULT_SELF_RELATION,
                 priced: bool = True,
                 envelope_decoder=None,
                 query: str = ""):
        self.selector = selector or AffordabilitySelector()
        self.epochs = epochs if epochs is not None else AccessEpochs()
        self.codec = codec if codec is not None else IdentityCodec()
        self.relation = relation
        self.priced = bool(priced)
        # the codec layer's decode path, INJECTED (never imported or
        # constructed here — this module is the SEAT, memory_codecs is
        # the layer, and the two stay decoupled exactly as cen.py stays
        # import-free of this seat).  None (the default) = values
        # decode through `codec` only.
        self.envelope_decoder = envelope_decoder
        # THE RETRIEVAL CUE the decode path conditions on (GENESIS's
        # decoder sees the cue).  Fixed at construction for this seat:
        # the priced seat's cue is the IDENTITY cue ("the self"), a
        # constant, so a constant field is the honest form — the
        # assoc.py seat (whose cue is the CURRENT turn's context) owns
        # the per-turn variant and passes its own query at its own
        # reconstruct() call.  Empty (the default) = no cue in force.
        self.query = str(query)

    # -- the per-turn retrieval ------------------------------------------
    def retrieve(self, *, engine, ledger, budget, turn: int) \
            -> RetrievalOutcome:
        """One turn's retrieval.  `engine` is the CEN's DatalogEngine
        (needs iter_facts + check_cost); `ledger` the DerivationLedger
        (charged in C11 units); `budget` the CostBudget (the per-turn
        gate this standing cost reconciles onto)."""
        budget_before = (budget.derivations_per_turn
                         - ledger.spent_this_turn)
        # -- the identity cue's candidate pool: the self relation's
        #    entries, enumerated through the engine's own surface.
        #    (str_cols: the content column is interned on the real
        #    engine and plain on the stub — the caller names it.)
        str_cols = (1,) if self.relation == DEFAULT_SELF_RELATION else ()
        facts = engine.iter_facts(self.relation, str_cols)
        by_key: dict[str, tuple] = {}
        entries: list[EntryState] = []
        for f in facts:
            rel, t = f[0], f[1]
            # THE ENTRY KEY: the turn column as its own string, WHATEVER
            # its type — the codec layer's supersession entries carry
            # string keys ('-4c1' = the entry at turn -4, re-encoded at
            # window 1; memory_codec_seat), which int() would REFUSE.
            # `turn` stays the RAW value for the selector's recency
            # ranking: numeric where the caller wrote numbers, and for
            # the string-keyed supersession entries the string sort and
            # the numeric sort agree on ordering by construction (the
            # key embeds the turn first).  A mixed pool therefore ranks
            # the original and its supersession adjacently, which is
            # the honest order: they are the same content, twice.
            key = str(t)
            by_key[key] = f
            # the ENGINE reports each entry's retrieval cost — the CEN
            # charges what the engine reports, exactly as _check_one
            # does for assertions (asking the price is not charged).
            cost, _depth = engine.check_cost(self.relation, f[1:])
            entries.append(EntryState(key=key, turn=t,
                                      weight=self.epochs.weight(key),
                                      cost=cost))
        plan = self.selector.plan(
            entries, budget_before if self.priced else None)
        # defensive: a custom selector must not overspend the per-turn
        # gate — truncate to the affordable prefix and SAY SO (never a
        # silent over-budget charge).
        truncated = False
        if self.priced:
            total = sum(e.cost for e in entries if e.key in plan)
            if total > budget_before:
                keep: list[str] = []
                spent = 0
                for k in plan:
                    c = next(e.cost for e in entries if e.key == k)
                    if spent + c > budget_before:
                        break
                    keep.append(k)
                    spent += c
                plan = tuple(keep)
                truncated = True
        # -- values for the planned entries, codec-compressed at the
        #    store boundary (identity by default; the memory-codec
        #    layer, when injected, encodes at the CONSOLIDATION
        #    boundary — this per-turn re-compression is the seat's
        #    honest identity path).
        values = [(k, self.codec.compress(_content_of(by_key[k])))
                  for k in plan if k in by_key]
        derivations = sum(e.cost for e in entries if e.key in plan)
        cut_depth = 0
        recon = reconstruct(turn, values, len(entries),
                            _EnvelopeCodec(self.codec,
                                           self.envelope_decoder),
                            query=self.query)
        if self.priced and derivations > 0:
            ledger.charge(derivations, cut_depth)
        for k in plan:
            self.epochs.record(k)
        return RetrievalOutcome(
            turn=turn, priced=self.priced,
            candidate_count=len(entries), retrieved=tuple(plan),
            derivations=derivations if self.priced else 0,
            cut_depth=cut_depth, truncated=truncated,
            reconstruction=recon, budget_before=budget_before)

    # -- C8 resume surface ------------------------------------------------
    def dump(self) -> dict:
        return {"relation": self.relation, "priced": self.priced,
                "epochs": self.epochs.dump(),
                "selector": type(self.selector).__name__,
                "codec": type(self.codec).__name__}

    def load(self, state: dict) -> None:
        if state.get("relation") != self.relation:
            raise ValueError(
                f"checkpoint retrieval relation {state.get('relation')!r}"
                f" != seat relation {self.relation!r} — refusing (C8 "
                f"fail-closed)")
        self.priced = bool(state["priced"])
        self.epochs.load(state["epochs"])


def _content_of(fact: tuple) -> str:
    """The stored value of a self_content entry (relation, turn,
    content) — the COMPRESSED VALUE the decoder reconstructs from."""
    return str(fact[2]) if len(fact) > 2 else ""
