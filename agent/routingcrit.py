"""R5 — THE EXTERNALLY-OWNED ROUTING/VALIDITY SELECTOR
(design/architecture.md §3a R5, realized in §11d).

THE ONE RULE THIS MODULE ENFORCES.  Whichever component decides
checked-vs-unchecked for a given emission is selecting on the
mechanism's own operating state, and the fraction it realizes is what
R2's budget constrains — so the selector must not be the variable it
controls.  R5: "ANY VALIDITY SELECTOR MUST BE EXTERNALLY OWNED AND
STRUCTURALLY OUTSIDE THE MECHANISM'S WRITE DOMAIN.  It may be EXECUTED
inside the loop (per-emission, cheap), but its CRITERION IS DEFINED AND
VERSIONED EXTERNALLY and is not writable by the DMN, the CEN, or the
SN."  This is the FIFTH application of the project's external-ownership
rule — after the durable record's sole writer (C9), the integrity
anchor (C9), the usefulness definition (C22c, heldout.py), and role
assignment (C23) — and it REUSES the same machinery rather than
inventing a second boundary: RoutingCriterionStore is HeldoutStore's
discipline at a disjoint path, sealed by the SAME RecordAnchor, with
its OWN designer WriterToken.

WHY IT EXISTS.  routing.py derives f (R2's law) and holds it per
consolidation window; interleave.py splits a stream into valid spans
and prose.  Nothing joined them: build_batch turned EVERY valid span
into an Assertion (fraction 1 always), so the only checked/unchecked
decision the mechanism realized was the generator's own bracketing and
the closed grammar's accept/reject.  This module is the missing object:
among the generator's OWN committed valid spans, which route.

THE SELECTOR'S INPUT IS CONTENT-BLIND (Q1, resolved from the code).
`SpanState` carries exactly {predicate, arity, position, turn} — NO
args, NO prose.  Args are excluded because build_batch
(interleave.py:203-207) puts them straight into Assertion.terms and
the DMN already chooses them freely (the t57-to-encode-intent class),
so any arg-sensitive rule is a steering channel.  Predicate and arity
are included as GRAMMAR-LEVEL INTERFACE facts (E7's mirror: the
declared set is the engine's declarations), not content — but a
WEIGHTED predicate policy IS steerable (the generator picks which
predicate to write to land unchecked), so v1 fixes per-predicate
treatment EQUAL and the store REFUSES a treatment name it has not
implemented (IMPLEMENTED_TREATMENTS): the capability is carried by the
format, visibly and versionedly, never silently exercised.  Position
and turn are position/metadata; position is the non-evadable selection
key — the generator controls WHAT it writes and HOW MANY spans it
commits, but the ORDER-relative prefix of its own committed output is
not a per-span steering signal at a fraction it does not choose.

THE v1 REALIZATION: route the FIRST ceil(f*n) valid spans in position
order (rule name 'leading-prefix').  Deterministic POSITION/PROPORTION,
chosen over weighted policies by the steering argument above, not by
cost.  The law's f comes from routing.py (MODEL-DERIVED, nothing
tuned); the criterion BINDS the realization rule, the predicate
treatment, the theta arm, and the [f_min, f_max] CLIP — not the law.

THE SPLIT STAYS TOTAL AND BYTE-EXACT (Q2).  extract_spans keeps every
Span's original (start, end) offsets, and `apply_routing` re-inserts
the UNSELECTED valid spans' bytes into the prose IN PLACE VERBATIM —
indistinguishable from prose that was never committed: no error, no
count, no third state to game (interleave.py decision 1's discipline,
for the same adversarial reason).  Formally prose' + sum(selected span
bytes) == stream, byte-exact, and the selected spans splice back at
their offsets to reproduce the stream (E3's round trip, generalized to
the routed subset).  A valid span is therefore either routed (an
Assertion with terms) or byte-preserved prose — nothing else exists.
Assertion ids keep the ORIGINAL position index (span-<turn>-<i>):
routing never renames an emission.

THE CRITERION'S TIMESCALE (R2, the seat's own enforcement).  The
criterion is RELOADED ONLY AT CONSOLIDATION BOUNDARIES (tau_S = 100
t.u.; the harness's one turn = one tau_a step), never per turn.  A
mid-window designer publish is therefore INVISIBLE to the loop until
the next window — an intentional consequence of R2's timescale, tested
by the battery's R2 part, not an oversight.  The harness holds the
criterion OBJECT loaded at the last boundary; reading it per turn
costs no file read.

THE COMMITTAL HOLE IS OPEN BY DESIGN (Q3) — stated, not passed
silently (G1).  The generator can emit FEWER valid spans so that fewer
of its claims are checked (under-committal: write the claim as prose).
This is not the selector's to close: (i) R1 REQUIRES prose to be the
unchecked return path, so closing it would couple the attention and
demand axes in the exact way R1's testable form names; (ii) R5 makes
selection-on-operating-state the thing externalized — supply is an
INPUT the router compensates for, never a lever (§11d R2': "R5 FORBIDS
making it a lever"); (iii) the law prices the total (D = what the
generator OFFERS x f, and f FALLS as D rises — routing.py:14-22).

CORRECTION, ROUND 2 — THE SUPPLY -> ARMED WINDOW CAPTURE IS WITHDRAWN
[MEASURED, on the retained pre-change tree; /tmp/p2r2_probe.py].  The
R5-review B1 correction asserted, from this battery's part R10, that the
generator CAN lower the window's routed COUNT — to zero — by timing a
flood of its own claims around a consolidation boundary.  THAT
MEASUREMENT IS WITHDRAWN: it was taken on the round-1 wiring, in which
the router's D-analogue was built from the CEN's backlog STOCK while
the plant's attention pinning read the PLANT's own switch state c —
one model variable split into two (harness.py:52-64 and
dpdr/model.py:92-94 define ONE c: it is the switch state, and B =
EMA_tauD(c) is its lag).  The law's own docstring says what the
D-analogue must be — the SAME addend the plant's D carries — and the
plant's D carries B built from the plant's (E, S).  A checker's queue
is NOT one of the model's channels: nothing in dpdr/model.py reads a
backlog.

WHAT IS TRUE NOW (the same scenario, the same flood, MEASURED in R10):
the flood still accrues CEN debt (backlog 3960) and drives the CEN's
measured unchecked share (u/n EMA 0.8619) — but that number is
TELEMETRY (Stage2State.backlog_rate).  The law's addend is the plant's
own B (Stage2LogRow.edge_addend = 0.0000 there), so D-analogue 0.5455 <
the arming level 0.6913, the router stays UNARMED, f stays 1.0, and
every offered claim is checked.  The chain the round-1 text described
(supply -> backlog_ema -> D_analogue -> armed -> f = f_min) required a
wiring that no longer exists, so the generator CANNOT move f by supply
here — and the G6 wording it had displaced ('cannot lower the COUNT
routed') is restored as the measured truth, with this withdrawal as its
scope.

WHAT SURVIVES, UNCHANGED: the ordering channel (G6) — at a given f the
prefix rule tells the generator WHICH of its own committed claims sit in
the checked prefix; the forged-identity publish (G9/R11); and the fact
that the suppression this section once described would not be the
selector's to close.  The monitor the model names (the
TerminatorDeficit observable, routing.py:322-398) remains UNWIRED —
nothing in run_stage2 consumes it (no import in stage2_harness.py) — so
the DETECTION is PROJECTION, not a measurement (S5), and the router is
unchanged and never counters it.

THE GAPS, STATED (the standing order: implement the model, or build
the seat and state the gap — G1-G9 are carried in this docstring, in
the battery's R8, and in §11d):

  G1  THE COMMITTAL HOLE IS OPEN BY DESIGN (Q3 above): under-committal
      is prose, prose is R1's unchecked return path; closing it would
      violate R1.  WITHDRAWN (round 2, R10): the B1 claim that supply is
      also a WINDOW-TIMESCALE lever through the P2 coupling.  It was an
      artifact of the round-1 wiring (a substrate backlog STOCK fed as
      the model's B); the law's addend is now the plant's own B
      (Stage2LogRow.edge_addend) and the CEN's queue is not one of the
      model's channels, so a flood moves only TELEMETRY (backlog_rate)
      and leaves f = 1.0.  The generator never chooses the law's number
      f, and now it cannot move it by supply either.  The intended
      monitor (TerminatorDeficit) is UNWIRED — the observable exists,
      the detection does not — and the held-out pricing of
      under-committal is PROJECTION: heldout.py marks its own
      measurement semantics PROJECTION, and no SWE campaign has run.
  G2  THE PREDICATE-WEIGHT SEAT IS BUILT BUT UNEXERCISED: the criterion
      format carries per-predicate treatment; v1 fixes all-equal
      because a weighted policy is generator-steerable.  Introducing
      weights is a visible, versioned designer action (and the store
      refuses an unimplemented treatment name today).
  G3  THE G-ANALOGUE REMAINS UNSOLVED: the harness consolidates with
      G=None -> the maximally conservative arm
      (boundary='g_unsolved_conservative_arm'), exactly as routing.py
      requires.  A fabricated G would be the standing-order violation.
  G4  f_min = 0.0 IS THE SEAT, NOT A FLOOR: R4's floor is an open
      measurement.  The criterion carries f_min as a designer-set clip
      and every report keeps f_min_is_seat=True while it is 0.0.
  G5  THE OS-USER RESIDUAL (C9's, inherited): an attacker who can READ
      the criterion's anchor can rewrite and reseal consistently.  The
      boundary is 'outside the mechanism's write domain', not 'outside
      every attacker'.
  G6  THE ORDERING CHANNEL IS UNCLOSED AND STATED: the generator
      controls emission ORDER, so a prefix rule lets it choose WHICH of
      its own committed claims sit in the checked prefix — over its own
      committed claims only, at the window's f.  AT A GIVEN f IT CANNOT
      LOWER THE COUNT ROUTED.  The B1 correction asserted the opposite
      ("the generator CAN lower the routed count, to 0, by supply"); that
      is WITHDRAWN (round 2, G1 above and R10), and the pre-B1 wording is
      restored as the measured truth.  A version-keyed random tie-break
      is the visible fix for the ordering half.
  G7  INTERFACES CHANGED, listed: build_batch gains the keyword-only
      `selected` (default None = today's behaviour, byte-identical);
      interleave.__all__ re-exports apply_routing; Stage2Config grows
      three default-off fields (routing_selector / routing_law /
      routing_criterion_dir); Stage2LogRow grows `routed`; cen.py is
      UNTOUCHED — the selector runs at the harness/extractor layer
      BEFORE submit_batch, so the CEN receives an already-routed batch
      and needs no knowledge of selection at all.
  G8  THE NO-OFFERS BOUNDARY (f = None) FREEZES — DECIDED, STATED, AND
      MEASURED UNREACHABLE IN THE WIRED WINDOW.  RoutingWindow
      .consolidate stores the law's number only when it is not None, so
      a window in which the law has no offers keeps the LAST window's f
      in force.  DECISION: the freeze is INTENDED — it is routing.py's
      own clause ("BETWEEN WINDOWS THE LAST WINDOW'S f APPLIES",
      routing.py:26-28), and it is the conservative direction out of an
      armed window (f = f_min continues to apply).  It is also
      UNREACHABLE by construction, and that is measured, not assumed:
      consolidate maps the D-analogue from backlog_ema through
      demand_analogue, whose numerator carries D_base = 0.3 > 0, so
      D-analogue >= 0.5455 > 0 for EVERY non-negative backlog_ema and
      A; 'no_offers' (D == 0) is a routing_fraction boundary the window
      seat cannot produce (the battery's R5 asserts both halves,
      including a freeze arm).  The branch is DEFENSIVE and unexercised
      — stated rather than left as a silent latent semantic.  The
      dataclass default f = 1.0 is likewise never what a running window
      applies: the harness consolidates at windows == 0, so a fresh
      state's first turn IS a boundary (stage2_harness.run_stage2).
  G9  THE PERSISTED WRITER CLAIM IS A NAME, NOT A CAPABILITY — SO ITS
      SCOPE IS STATED, AND IT IS NARROWER THAN "THE DESIGNER ONLY" (R5
      fix round 2).  The check that refuses a foreign publish is a
      STRING: publish() overwrites the body's writer_id with
      token.writer_id, and _check_persisted_writer compares that string
      with the one sealed in the criterion in force.  WriterToken
      .writer_id is a CALLER-CHOSEN NAME and WriterToken.issue() is
      public (cen.py:239-249) — a name, not a capability — so the check
      DISCRIMINATES NAMES, NOT AUTHORITY.  CONSEQUENCE [MEASURED, this
      module's battery part R11]: a FRESH store instance holding a
      token it names "designer" PUBLISHES v2 (f_max = 0.0) over the
      designer's sealed v1 — the forged-identity publish SUCCEEDS, and
      it takes effect on the loop at the next consolidation boundary,
      disarming the routing budget.  THE CAPABILITY ASSUMPTION the
      boundary rests on, now stated rather than implied: it defends
      against a MIS-WIRED HARNESS (a caller publishing through the seat
      holding some other token — the CEN'S, the DMN's, a fresh store's;
      positions the round-1 fix DOES close) and against an actor that
      can WRITE the criterion file but not READ its anchor; it does NOT
      defend against code running IN THE MECHANISM'S PROCESS.  The
      in-process actor needs NO new capability to get there: every
      committed publish already reseals under the anchor key (publish ->
      _key_for -> the same 32-byte secret, R11 measures that the forged
      publish reseals under the ORIGINAL key), and the same actor can
      rewrite the body and reseal it directly (G5).  THE HONEST SCOPE:
      IN-PROCESS NO BOUNDARY CAN HOLD — the string check and the anchor
      both reduce to G5, and the only closure is OUT-OF-PROCESS (the
      anchor's secret outside the mechanism's process).  REACHABILITY,
      stated precisely because it is easy to over-claim: the DMN the
      harness takes is a PYTHON CALLABLE (Stage2Config.dmn), and
      stage2_harness.py:731-738 constrains what that callable RETURNS
      (a raw str) and not what it DOES — R10's own DMN callback reaches
      this seat from inside run_stage2 — so the string check is
      adequate-by-IRRELEVANCE only under a TEXT-ONLY, OUT-OF-PROCESS
      generator (a model behind a text channel), and for the in-process
      callable the harness actually accepts it is adequate by RELEVANCE
      ONLY, never by strength.  STRENGTHENING TO ANCHOR-KEY POSSESSION:
      NOT DONE, deliberately, and not because it is hard — it would be
      VACUOUS, because possession of the anchor key is ALREADY a
      precondition of every committed publication (the mark's HMAC is
      verified under that key), so a possession gate could refuse
      nothing the string check admits while the forgery works; R11
      measures both halves (the forged publish USED the original key;
      with the anchor file removed the same publish is REFUSED — the
      fail-closed direction G5's artifact already holds).

EVIDENCE MARKING.  MEASURED: this boundary's refusals (rollback, gap,
wrong writer token — including the PERSISTENT writer seal, which refuses
a FRESH store instance publishing over a criterion claimed by another
writer — unsealed edit, deleted anchor, unimplemented rule,
unimplemented treatment, inverted clip, absent criterion), the
totality/byte-exactness of the routed split, the count identity routed
== ceil(f*n), and the SUPPLY -> ARMED WINDOW CAPTURE end to end (R10) —
all reproducible, battery parts R1/R5/R6/R10.  AND, MEASURED as a KNOWN
LIMIT rather than a closed hole (G9, R11): the persisted writer seal is
a NAME comparison, so a fresh instance forging the name "designer"
PUBLISHES over the designer's criterion (the forgery reseals under the
ORIGINAL anchor key, and is refused with the anchor file absent) — the
boundary's domain is stated, not assumed.  PROJECTION: (P1) that
the leading-prefix rule plus equal treatment ADEQUATELY realize
"non-evadable" against a real adversarial generator — the steering
argument is a derivation over the code's own surfaces (args /
predicates / prose), not a measurement of an adversary, and the
content-blindness control tests the arms we constructed, not all
channels — and B1's measured capture DEMOTES this further: the split IS
evadable at window timescale by supply, so the selection's adequacy is
a projection over a channel the battery now measures against it; (P2)
that per-window criterion loading is the right timescale enforcement —
R2's timescale is model-derived, the load-at-boundary-only consequence
is ours, and the measured capture shows the window timescale is exactly
where the evasion lives; (P3) the selector's effect on LIVE loop
dynamics — nothing here gates the live turn loop until the config is
enabled, and enabling it changes the turn loop and needs its own gate
(§11d's NOT-WIRED, item 12); (P4) the under-committal PRICING — that
under-offering "forgoes the optimised metric without touching the
held-out score" rests on the held-out check whose OWN measurement
semantics is marked PROJECTION (heldout.py:45-46: no SWE campaign has
run) and on the TerminatorDeficit sensor, which is UNWIRED (no consumer
in run_stage2) — the observable exists, the DETECTION does not (S5).

Run the demonstration battery:  stage2_routingcrit_tests.py (R1-R11).
"""
from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, field, replace
from typing import Protocol, Sequence

from cen import (AnchorError, ChainError, RecordAnchor, SoleWriterError,
                 WriterToken)

__all__ = ["DEFAULT_ROUTINGCRIT_DIR", "CRITERION_FILENAME",
           "ANCHOR_SUBDIR", "ROUTINGCRIT_ANCHOR_ENV",
           "IMPLEMENTED_RULES", "IMPLEMENTED_TREATMENTS", "V1_PREDICATES",
           "RoutingCriterionError", "SpanState", "RoutingSelector",
           "PrefixRoutingSelector", "RoutingCriterion", "V1_CRITERION",
           "RoutingCriterionStore", "publish_criterion", "load_criterion",
           "apply_routing", "mechanism_write_paths"]

#: Where the criterion lives.  DELIBERATELY OUTSIDE every namespace the
#: mechanism writes (see mechanism_write_paths) and outside
#: ~/thing/agent itself.  Resolved: explicit arg > CEN_ROUTINGCRIT_DIR
#: env > ~/.cen-routingcrit (tests set the env per-run, exactly as
#: CEN_HELDOUT_DIR isolates the held-out definition).
DEFAULT_ROUTINGCRIT_DIR = os.path.join(os.path.expanduser("~"),
                                       ".cen-routingcrit")

CRITERION_FILENAME = "criterion.json"

#: The criterion's ANCHOR lives in its OWN tree (<dir>/.anchors), not in
#: the SHARED anchor namespace the mechanism's DurableRecords write (R5
#: review S4: the criterion's RecordAnchor used to resolve into
#: ~/.cen-anchors, so a mechanism RecordAnchor opened at the criterion's
#: own path could RESET the criterion's seal — count to 0, new key — and
#: launder a v2->v1 rollback through a mechanism write path).  Resolved:
#: explicit anchor_dir arg > CEN_ROUTINGCRIT_ANCHOR_DIR env >
#: <criterion dir>/.anchors.  A mechanism module has no reason to name
#: either env (the battery's R9 scans for that), and R1 checks the
#: resolved ANCHOR path, not just the criterion dir, against every
#: mechanism write namespace.
ANCHOR_SUBDIR = ".anchors"
ROUTINGCRIT_ANCHOR_ENV = "CEN_ROUTINGCRIT_ANCHOR_DIR"

#: THE RULE-NAME GATE.  A criterion naming a rule this module has not
#: implemented is REFUSED — at publish AND at load, never a silent
#: fallback to the prefix rule.  v1 has exactly one realization; a
#: future rule is added here only with its implementation and its test.
IMPLEMENTED_RULES: tuple[str, ...] = ("leading-prefix",)

#: THE TREATMENT-NAME GATE (G2's seat, made loud).  The criterion format
#: carries a per-predicate treatment; v1 implements exactly one
#: ('equal' — every declared predicate is treated identically, the only
#: non-steerable policy).  A weighted/other treatment is refused until
#: it is implemented and tested, so a steerable policy cannot enter by
#: data alone.
IMPLEMENTED_TREATMENTS: tuple[str, ...] = ("equal",)

#: The theta arm the criterion may bind.  F7 settled the gate: the arm
#: the frozen mechanism actually arms at is the SIMULATION parameter
#: (Params().Theta = 0.4); THETA_MEASURED = 0.4418 is a parameter-space
#: failure boundary, carried as a diagnostic and NEVER the gate.  So a
#: criterion binding 'measured' is refused (it would make the router
#: more permissive than the mechanism it protects).
IMPLEMENTED_THETA_ARMS: tuple[str, ...] = ("simulation",)

#: The v1 DECLARED predicate set, MIRRORED from interleave.
#: DECLARED_PREDICATES (done/1, orphaned/1).  It is mirrored rather than
#: imported so this seat does not depend on the extractor's module (the
#: criterion is upstream of the extractor); the battery's R8 asserts the
#: mirror, exactly as E7 asserts the grammar-vs-engine mirror.
V1_PREDICATES: tuple[str, ...] = ("done", "orphaned")


class RoutingCriterionError(ChainError):
    """The criterion failed its gate — absent, corrupt, unsealed,
    rolled back, sealed-but-unimplemented, or written by a token that
    is not the sole writer.  Fail-closed: selection never runs against
    a criterion that cannot be authenticated."""


# ---------------------------------------------------------------------------
# THE SELECTOR'S INPUT — CONTENT-BLIND BY CONSTRUCTION (R5 / Q1)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SpanState:
    """One routing candidate AS THE SELECTOR SEES IT: the predicate
    symbol, its declared arity, its ORIGINAL position among this turn's
    valid spans, and the turn.  Deliberately NO args and NO prose: a
    selector that could read them would let the generator choose which
    of its claims go unchecked by shaping what it writes (the t57-to-
    encode-intent class, Q1).  `position` is the selection key that is
    NOT a content channel — the generator controls what it commits, not
    the order-relative prefix of its own committed output at a fraction
    it does not choose (G6 states the honest remainder)."""
    predicate: str
    arity: int
    position: int
    turn: int


class RoutingSelector(Protocol):
    """The externally-owned selection policy (R5).  Implemented by the
    DESIGNER (the harness config / the test) and INJECTED — the
    mechanism constructs none (the battery's R3 scans for that
    structurally, in the D6 shape).  `f` is the applied fraction for the
    current consolidation window (None = the law has no fraction: no
    offers at all -> nothing routes); the return value is the ORIGINAL
    position indices of the routed spans."""

    def plan(self, candidates: Sequence[SpanState],
             f: float | None) -> tuple[int, ...]: ...


class PrefixRoutingSelector:
    """The v1 realization of the criterion rule 'leading-prefix': route
    the FIRST ceil(f*n) valid spans in position order (position is
    already the candidate order — the extractor's order of appearance).

    PURE AND STATELESS, and neither reads nor is given any content: no
    args, no prose, no predicate weighting (the predicate is carried in
    SpanState as the grammar-level fact the criterion's all-equal policy
    must cover, and the plan below reads `position` only).  f = None
    (no offers) or f <= 0 (the law's floor) routes NOTHING — the
    generator keeps everything as prose, which is R1's unchecked return
    path, not an error.

    THE GRID CONVENTION, stated where a threshold could be misread: the
    realized COUNT is the CEILING of f*n on the grid of 1/n, so the
    realized fraction routed/n lies in [f, f + 1/n).  The identity the
    battery asserts is the exact integer one — routed == ceil(f*n) —
    never an approximation of it.
    """

    rule = "leading-prefix"

    def plan(self, candidates: Sequence[SpanState],
             f: float | None) -> tuple[int, ...]:
        if f is None or f <= 0.0:
            return ()
        n = len(candidates)
        k = int(math.ceil(float(f) * n))
        if k <= 0:
            return ()
        return tuple(p.position for p in candidates[:k])


# ---------------------------------------------------------------------------
# THE CRITERION OBJECT + THE v1 INSTANCE
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RoutingCriterion:
    """The versioned routing criterion (Q4).  VERSIONED, not frozen:
    updateable by the designer/sole writer, never by the mechanism.
    Every field is plain JSON, so the file stays DATA, not code.

    WHAT IT BINDS, and what it deliberately does NOT: the LAW (f from
    routing.py, derived from the model, nothing tuned) lives in
    routing.py and is NOT settable here; the criterion binds the
    REALIZATION rule (which spans route at a given f), the per-predicate
    treatment, the theta arm, and the [f_min, f_max] clip applied to the
    law's number.  f_min is the SEAT for R4's undesigned floor (G4):
    0.0 means 'no floor derived', never 'the floor is zero'.
    """
    version: int
    vocation: str
    created_by: str
    created_ts: str
    rule: str = "leading-prefix"
    theta_arm: str = "simulation"
    f_min: float = 0.0
    f_max: float = 1.0
    predicate_policy: dict = field(default_factory=dict)
    #: THE PERSISTED WRITER IDENTITY (R5 review B3).  Written by publish
    #: from the TOKEN that published (the token is the authority; a value
    #: handed in on the criterion object is OVERWRITTEN), sealed into the
    #: body and therefore under the anchor's head_hash, and checked on
    #: every later publish: a criterion already claimed by writer 'X' can
    #: be re-published only by a token whose writer_id is 'X'.  Object
    #: identity alone was per-INSTANCE (RAM), so a FRESH store instance
    #: plus the CEN's own token could claim an already-published
    #: criterion; the claim now survives the process.
    writer_id: str = ""


#: The v1 criterion as the designer publishes it (rule = the only
#: implemented realization; treatment equal for every declared
#: predicate; theta arm = the simulation gate arm; f_min the R4 seat).
V1_CRITERION = RoutingCriterion(
    version=1,
    vocation="software-engineering",
    created_by="designer",
    created_ts="",
    rule="leading-prefix",
    theta_arm="simulation",
    f_min=0.0,
    f_max=1.0,
    predicate_policy={p: "equal" for p in V1_PREDICATES},
)


# ---------------------------------------------------------------------------
# THE STORE — HeldoutStore's discipline, at a disjoint path, with its
# own designer token (Q4: reuse the existing external boundary)
# ---------------------------------------------------------------------------

def mechanism_write_paths() -> tuple[str, ...]:
    """Every directory tree a MECHANISM write path can reach, stated so
    a test can assert the criterion's dir is disjoint from all of them
    (R1).  The mechanism's writes are exactly: the durable record
    (DurableRecord.path's tree), the engine store (C15: cfg.store_dir /
    CEN_STORE_DIR / ~/.cen-store), and the anchors.  This function does
    NOT enumerate the criterion's own dir (it is not a mechanism write
    path), nor the held-out definition's dir (same reason: the battery
    enumerates both as objects to keep disjoint).  PROJECTION-safe: if a
    new mechanism write surface appears, ADD it here and R1 fails until
    you do."""
    paths = [os.path.expanduser(p) for p in (
        os.environ.get("CEN_STORE_DIR", ""),
        os.path.join(os.path.expanduser("~"), ".cen-store"),
        os.path.join(os.path.expanduser("~"), ".cen-anchors"),
    ) if p]
    return tuple(os.path.abspath(p) for p in paths)


class RoutingCriterionStore:
    """The criterion's home: `<dir>/criterion.json` sealed by a
    RecordAnchor at `<anchor_dir>/<sha16(dir/criterion.json)>.anchor`.
    The anchor's high-water mark carries (count=version,
    head_hash=sha256(criterion body)) — so a version ROLLBACK, a version
    GAP, or an unsealed content edit refuses the load, exactly as the C9
    record's mark refuses a truncated chain.  Fail-closed: an existing
    criterion whose anchor is absent/corrupt is REFUSED
    (RoutingCriterionError), never trusted.

    WHERE THE ANCHOR LIVES (R5 review S4).  In the criterion's OWN tree,
    `<dir>/.anchors` by default (explicit anchor_dir arg >
    CEN_ROUTINGCRIT_ANCHOR_DIR env > `<dir>/.anchors`) — NOT in the
    shared ~/.cen-anchors namespace the mechanism's DurableRecords
    write.  That sharing was a real hole: a DurableRecord opened at the
    criterion's own path resolves the SAME anchor file, and RecordAnchor
    .ensure() REPLACES its key and resets its count to 0, so a
    mechanism-reachable write path could reset the criterion's seal and
    launder a rollback.  The criterion dir was already disjoint; its
    ANCHOR was not.  The battery's R1 now enumerates the resolved anchor
    PATH (not only the dir) against every mechanism write namespace, so
    an env override that re-introduces the sharing FAILS the battery.

    Sole writer: the token identity handed to publish() at FIRST
    publication, and — since B3 — a claim that PERSISTS: the publishing
    token's writer_id is sealed into the criterion body (under the
    anchor's head_hash), and every later publish must present a token
    whose writer_id matches it (object identity is still enforced
    within one instance, on top).  So a FRESH instance plus the CEN's
    own token, or the DMN's mid-run token, is refused with
    SoleWriterError; the old per-instance check held only while the
    mechanism reused the designer's own store OBJECT, a property
    nothing enforced and no test exercised.

    THE SCOPE OF THAT CLAIM, STATED (G9, R5 fix round 2 — it is
    NARROWER than "the designer only").  What matches is a STRING:
    WriterToken.writer_id is a caller-chosen NAME and WriterToken
    .issue() is public, so this check refuses a DIFFERENT NAME, not an
    actor without authority.  [MEASURED — battery part R11]: a fresh
    instance holding a token named "designer" PUBLISHES v2 with
    f_max = 0.0 over the designer's sealed v1, and that takes effect on
    the loop at the next boundary.  The capability the forgery DOES
    need is the anchor key — publish reseals through _key_for, so it
    loads `<anchor_dir>/<sha16(path)>.anchor` — which is the READ G5
    already names; the capability assumption is therefore: THIS
    BOUNDARY DEFENDS AGAINST A MIS-WIRED HARNESS AND AGAINST AN ACTOR
    THAT CANNOT READ THE ANCHOR, and NOT against code running in the
    mechanism's process (which can also rewrite the body and reseal it
    directly — G5 — so in-process the string check and the anchor
    reduce to the SAME residual, and OUT-OF-PROCESS is the only
    closure).  The round-1 fix's refusals stand; what changes here is
    the claim's stated domain, not the mechanism (standing order §1a:
    state the gap rather than let the claim outrun it).
    """

    def __init__(self, routingcrit_dir: str | None = None,
                 anchor_dir: str | None = None):
        self.dir = os.path.abspath(
            routingcrit_dir or os.environ.get("CEN_ROUTINGCRIT_DIR")
            or DEFAULT_ROUTINGCRIT_DIR)
        self.path = os.path.join(self.dir, CRITERION_FILENAME)
        self.anchor = RecordAnchor(
            self.path,
            anchor_dir or os.environ.get(ROUTINGCRIT_ANCHOR_ENV)
            or os.path.join(self.dir, ANCHOR_SUBDIR))
        self._writer: WriterToken | None = None

    # -- sole writer ------------------------------------------------------
    def _require_writer(self, token: WriterToken) -> None:
        """First publication CLAIMS the writer identity for THIS instance;
        every later publish on it must present the same token OBJECT
        (identity check, like DurableRecord._check_writer /
        HeldoutStore._require_writer).  The mechanism's CEN token is a
        different instance -> SoleWriterError.  This is the RAM half;
        _check_persisted_writer below is the half that survives the
        process (B3)."""
        if self._writer is None:
            self._writer = token
        elif token is not self._writer:
            raise SoleWriterError(
                f"routing criterion at {self.path} is held by writer "
                f"'{self._writer.writer_id}'; '{token.writer_id}' is not "
                f"the sole writer (R5: the mechanism may not own the "
                f"selector it is measured by)")

    def claimed_writer(self) -> str | None:
        """The writer_id SEALED IN THE CRITERION IN FORCE (B3), or None
        when nothing is published.  Read from the AUTHENTICATED body:
        load() must pass first, so the anchor seal — not a forgeable
        sibling file — is what establishes the claim.  A criterion whose
        anchor is absent refuses here too (fail-closed: an existing body
        without its anchor is an attack, never a fresh start)."""
        if not os.path.exists(self.path):
            return None
        return self.load().writer_id

    def _check_persisted_writer(self, token: WriterToken) -> None:
        """REFUSE a publish whose token writer_id differs from the one the
        criterion IN FORCE was sealed by (B3).  This is the check that
        makes the boundary a PROPERTY OF THE CRITERION, not of the store
        object: a fresh RoutingCriterionStore plus the CEN's (or the
        DMN's) token cannot claim an already-published criterion.
        SCOPE (G9, [MEASURED, R11]): what it compares is the NAME the
        criterion is sealed to — so a fresh instance presenting THAT
        name publishes, and the only further thing it needs is the
        anchor key the reseal already requires (G5's read).  A
        DIFFERENT NAME is refused; the same name from in-process code is
        NOT, and in-process no boundary can hold (G9)."""
        claimed = self.claimed_writer()
        if claimed is None:
            return
        if not claimed:
            raise SoleWriterError(
                f"routing criterion at {self.path} carries NO writer claim "
                f"(published before writer identity was sealed) — refusing "
                f"to claim it with '{token.writer_id}'; republish the "
                f"criterion from its designer store, or remove it "
                f"deliberately")
        if claimed != token.writer_id:
            raise SoleWriterError(
                f"routing criterion at {self.path} is SEALED to writer "
                f"'{claimed}'; '{token.writer_id}' is not the sole writer "
                f"— a fresh store instance does not make a new writer "
                f"(R5: the mechanism may not own the selector it is "
                f"measured by)")

    # -- the designer-side gates -----------------------------------------
    @staticmethod
    def _gate(crit: RoutingCriterion) -> None:
        """Every refusal the criterion's CONTENT must pass, at publish
        AND at load (so a criterion that reaches the file by any other
        route is refused identically — never a silent fallback):
        an unimplemented rule name, an unimplemented predicate
        treatment, an unsupported theta arm, a clip outside [0,1] or
        inverted, and a policy that does not cover exactly the declared
        predicate set (an omitted predicate would leave its treatment
        undefined).  The writer claim is part of the same gate: a body
        with no writer_id is refused at publish AND at load, so a
        criterion that reached the file by any other route still does
        not route."""
        if not crit.writer_id:
            raise RoutingCriterionError(
                "criterion carries NO writer_id — the seal must name the "
                "writer that published it (B3: an unclaimed criterion "
                "would let any fresh store instance claim it)")
        if crit.rule not in IMPLEMENTED_RULES:
            raise RoutingCriterionError(
                f"criterion rule {crit.rule!r} is NOT IMPLEMENTED "
                f"(implemented: {list(IMPLEMENTED_RULES)}) — refusing "
                f"loudly rather than falling back to "
                f"{IMPLEMENTED_RULES[0]!r} (a silent fallback would be "
                f"selection by the mechanism's convenience)")
        if crit.theta_arm not in IMPLEMENTED_THETA_ARMS:
            raise RoutingCriterionError(
                f"criterion theta arm {crit.theta_arm!r} is not the gate "
                f"arm (implemented: {list(IMPLEMENTED_THETA_ARMS)}; F7: "
                f"the measured 0.4418 is a boundary diagnostic, never the "
                f"gate — binding it makes the router more permissive "
                f"than the mechanism it protects)")
        if set(crit.predicate_policy) != set(V1_PREDICATES):
            raise RoutingCriterionError(
                f"criterion predicate policy must cover EXACTLY the "
                f"declared predicate set {list(V1_PREDICATES)}; got "
                f"{sorted(crit.predicate_policy)} — an omitted predicate "
                f"would have no defined treatment")
        for p, t in crit.predicate_policy.items():
            if t not in IMPLEMENTED_TREATMENTS:
                raise RoutingCriterionError(
                    f"predicate {p!r}: treatment {t!r} is NOT IMPLEMENTED "
                    f"(implemented: {list(IMPLEMENTED_TREATMENTS)}) — a "
                    f"weighted/other policy is generator-steerable (the "
                    f"generator picks the predicate); it may enter only "
                    f"as a visible, versioned, implemented change (G2)")
        if not (0.0 <= crit.f_min <= crit.f_max <= 1.0):
            raise RoutingCriterionError(
                f"criterion clip is not a subinterval of [0,1]: "
                f"f_min={crit.f_min}, f_max={crit.f_max}")

    # -- designer-side write (the ONLY write) -----------------------------
    def publish(self, token: WriterToken, crit: RoutingCriterion) -> None:
        """Write version N + advance the sealed mark.  Monotone: the new
        version must be exactly old+1; anything else is refused.  The
        writer identity is enforced FIRST — the in-RAM object check
        (_require_writer) AND the persisted claim (_check_persisted_writer,
        B3) — then the content gates, and the anchor's mark
        (count=version, head=body hash) is committed AFTER the file is
        fsync'd — the ordering discipline DurableRecord.append_decision
        and HeldoutStore.publish use.  The TOKEN is the authority for the
        writer identity: whatever the criterion object carries is
        overwritten with token.writer_id, so a forged claim on the data
        cannot enter the seal."""
        self._require_writer(token)
        self._check_persisted_writer(token)
        crit = replace(crit, writer_id=token.writer_id)
        if os.path.exists(self.path):
            cur = self._read_body()
            if crit.version != cur["version"] + 1:
                raise RoutingCriterionError(
                    f"criterion version must be exactly "
                    f"{cur['version'] + 1}, got {crit.version} — monotone, "
                    f"no rollbacks, no gaps (Q4)")
        self._gate(crit)
        body = {
            "version": crit.version,
            "vocation": crit.vocation,
            "created_by": crit.created_by,
            "created_ts": crit.created_ts,
            "rule": crit.rule,
            "theta_arm": crit.theta_arm,
            "f_min": crit.f_min,
            "f_max": crit.f_max,
            "predicate_policy": dict(crit.predicate_policy),
            "writer_id": crit.writer_id,
        }
        os.makedirs(self.dir, mode=0o700, exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(body, sort_keys=True))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.path)
        os.chmod(self.path, 0o600)
        self.anchor.commit(self._key_for(token), body["version"],
                           _body_hash(body))

    def _key_for(self, token: WriterToken) -> bytes:
        """The anchor key, obtainable only by the CURRENT sole writer
        (identity-checked) or at first publication (fresh mint)."""
        if os.path.exists(self.path) and os.path.exists(self.anchor.path):
            return self.anchor.load()["key"]
        if not os.path.exists(self.anchor.path):
            return self.anchor.ensure()
        return self.anchor.load()["key"]

    # -- everyone-side read (the mechanism MAY read) ----------------------
    def _read_body(self) -> dict:
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            raise RoutingCriterionError(
                f"no routing criterion at {self.path} — publish one first "
                f"(R5: the mechanism cannot invent its own selector "
                f"criterion)") from None
        except ValueError as e:
            raise RoutingCriterionError(
                f"criterion {self.path} is CORRUPT ({e}) — refusing "
                f"(fail-closed)") from None

    def load(self) -> RoutingCriterion:
        """Load + authenticate.  The anchor must exist, seal, and match
        the file's (version, body-hash) — a criterion edited without the
        writer, rolled back, or gap-skipped is REFUSED.  This is the
        READ the mechanism is allowed: it routes by the criterion; it
        changes nothing.  Called ONLY at a consolidation boundary (the
        harness's discipline; the battery's R2 part tests it)."""
        body = self._read_body()
        try:
            a = self.anchor.load()
        except AnchorError as e:
            raise RoutingCriterionError(
                f"criterion anchor failed for {self.path}: {e} — refusing "
                f"to route on an unauthenticatable criterion "
                f"(fail-closed)") from e
        if a["count"] != body["version"] \
                or a["head_hash"] != _body_hash(body):
            raise RoutingCriterionError(
                f"criterion {self.path}: anchor mark "
                f"(v{a['count']}, {a['head_hash'][:12]}..) does not match "
                f"the file (v{body['version']}, "
                f"{_body_hash(body)[:12]}..) — the criterion was EDITED "
                f"WITHOUT ITS WRITER or rolled back; refusing "
                f"(fail-closed)")
        crit = RoutingCriterion(
            version=body["version"], vocation=body["vocation"],
            created_by=body["created_by"], created_ts=body["created_ts"],
            rule=body["rule"], theta_arm=body["theta_arm"],
            f_min=body["f_min"], f_max=body["f_max"],
            predicate_policy=dict(body["predicate_policy"]),
            writer_id=body.get("writer_id", ""))
        # the SAME content gates as publish: a criterion that reached the
        # file by any other route is refused here too (a designer-sealed
        # unimplemented rule still does not route).
        self._gate(crit)
        return crit


def _body_hash(body: dict) -> str:
    import hashlib
    return hashlib.sha256(json.dumps(body, sort_keys=True)
                          .encode()).hexdigest()


def publish_criterion(store: RoutingCriterionStore, token: WriterToken,
                      *, rule: str = "leading-prefix",
                      theta_arm: str = "simulation",
                      f_min: float = 0.0, f_max: float = 1.0,
                      predicate_policy: dict | None = None,
                      vocation: str = "software-engineering",
                      created_by: str = "designer") -> RoutingCriterion:
    """The designer's one-call publish of the NEXT version (v1 first,
    then +1 per call — each bump is visible and attributable).  Every
    argument is a DESIGNER decision recorded in the versioned body; none
    of them is the law (f's derivation stays in routing.py).

    RETURNS THE STORED CRITERION, loaded back through the seal, NOT the
    in-memory object handed to publish().  publish() is the authority on
    the body it writes (it overwrites writer_id with the TOKEN's id), so
    the in-memory `crit` — whose writer_id is the dataclass default ''
    — would describe a criterion that was never written: a caller
    reading `.writer_id` off the return would get a value that
    disagrees with the seal [MEASURED pre-fix; R1 pins it].  Loading it
    back makes drift structurally impossible: the returned object is
    the authenticated body itself, so it is what publish() wrote or the
    call raises."""
    if os.path.exists(store.path):
        v = store._read_body()["version"] + 1
    else:
        v = 1
    crit = RoutingCriterion(
        version=v, vocation=vocation, created_by=created_by,
        created_ts=time.strftime("%Y-%m-%dT%H:%M:%S"), rule=rule,
        theta_arm=theta_arm, f_min=f_min, f_max=f_max,
        predicate_policy=(dict(predicate_policy) if predicate_policy
                          is not None
                          else {p: "equal" for p in V1_PREDICATES}))
    store.publish(token, crit)
    return store.load()


def load_criterion(store: RoutingCriterionStore) -> RoutingCriterion:
    return store.load()


# ---------------------------------------------------------------------------
# APPLYING THE SELECTION — the split stays TOTAL and BYTE-EXACT (Q2)
# ---------------------------------------------------------------------------

def apply_routing(extraction, selected: Sequence[int], stream: str) -> tuple:
    """Restrict a TOTAL split to the SELECTED spans, keeping the split
    total: returns (selected_spans, prose') where prose' is the stream
    with ONLY the selected spans' bytes removed — every UNSELECTED valid
    span's bytes re-enter the prose IN PLACE, VERBATIM, at their
    original offsets, indistinguishable from prose that was never
    committed (no error, no count, no third state — interleave.py
    decision 1's discipline, for the same adversarial reason).

    `stream` is REQUIRED and is the byte source: interleave.Span carries
    (start, end, predicate, args) and NOT the matched bytes, so the
    unselected spans' verbatim re-insertion needs the original stream.
    (The plan's sketch wrote apply_routing(extraction, selected); the
    signature here adds the stream for exactly this reason — without it
    the byte-exactness requirement cannot be met.)

    The walk is extract_spans' own walk, restricted to the selected set:
    the complement bytes are appended untouched.  Byte-exactness
    follows: prose' + sum(selected span bytes) == stream, and splicing
    the selected spans back at their offsets reproduces the stream.
    Content-blind in the only sense that matters here: the walk reads
    the spans' OFFSETS, never what they say.
    """
    claims = extraction.claims
    want = sorted({int(p) for p in selected})
    for p in want:
        if p < 0 or p >= len(claims):
            raise RoutingCriterionError(
                f"selected position {p} is outside this turn's "
                f"{len(claims)} valid spans — the selector returned a "
                f"position the extractor never emitted")
    # the totality guard: the extraction must BE the total split of this
    # stream.  A mismatch would silently emit prose with bytes moved
    # (the failure R6 exists to catch), so it is refused here instead.
    _pos = 0
    _pieces: list[str] = []
    for s in claims:
        _pieces.append(stream[_pos:s.start])
        _pos = s.end
    _pieces.append(stream[_pos:])
    if "".join(_pieces) != extraction.self_content:
        raise RoutingCriterionError(
            "apply_routing: the stream and the extraction disagree — "
            "removing every valid span from the stream does not "
            "reproduce self_content, so the routed split would not be "
            "byte-exact; refusing")
    chosen = sorted((claims[p] for p in want), key=lambda s: s.start)
    out: list[str] = []
    pos = 0
    for s in chosen:
        out.append(stream[pos:s.start])
        pos = s.end
    out.append(stream[pos:])
    return tuple(chosen), "".join(out)
