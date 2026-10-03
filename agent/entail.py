"""entail.py — the DERIVE seat (paper-3 prerequisite 1: entailment).

THE GAP THIS CLOSES (paper2/paper-3-scope.md 3.1, MEASURED there):
CEN._check_one prices a check through check_cost and then resolves it by
DIRECT FACT LOOKUP — contradicted() -> REFUTED, lookup() -> VERIFIED,
else UNCHECKABLE('no_rules').  A task whose completion must be DERIVED
from world state is unscorable, the declared-but-never-seeded `orphaned`
predicate can never verify, and the cost surface is flat at (1, 0) so
C11's derivation/cut-depth accounting is unexercised.  The engine's rule
machinery is real (dlb: load_rules/compile_rules/query_rules_ro/
query_magic; measured 0.74 ms for a recursive closure at fixture scale)
— this module is the WIRING, not an engine build.

SCOPE, STATED HONESTLY (the standing order: never call a subset the
thing).  This is NOT full Logical English.  It is an LE->Datalog
TRANSDUCER for exactly the SPAN GRAMMAR the extractor already emits
(interleave.py: ground atoms `pred(arg, ...)` over the declared
predicate set, arguments matched by the extractor's own argument
grammar), plus a THEORY written directly in the engine's Datalog (the
datalog-dafsa language: Horn clauses, body arithmetic).  What the
transducer does: it validates a claim's ground atom against the span
grammar and maps it onto a query of the theory's WITNESS relation.
DEFERRED (not covered, deliberately): the controlled-natural-language
surface of LE (LE rule text, full LE sentences), ontology extension by
the DMN, negation-as-failure (the substrate stays monotone — refutation
is a POSITIVE derived witness, never a conclusion from an absence),
aggregates in the theory, the generative decoder, and the persisted
compile path (load_rules + compile_rules materialize INTO the store;
this seat uses the THROWAWAY-CLONE path query_rules_ro, which leaves the
store byte-untouched — measured, dlb tests test_query_rules_ro_leaves_
db_untouched).

THE SEMANTICS THE CEN APPLIES (cen._check_derived):
  * STORED FACTS WIN FIRST.  contradicted() then lookup() run before the
    theory is consulted; the theory adjudicates only what the store
    cannot answer.  A designer-supplied theory can therefore never
    un-verify the world's own record — it can only decide misses.
  * EVIDENCE-GROUNDED, NEVER TAUTOLOGICAL.  Every rule body is anchored
    in EVIDENCE RELATIONS (facts in the store, e.g. abandoned/blocks).
    A claim about an id no evidence touches is NOT derived — it stays
    UNCHECKABLE('no_rules') debt.  This is what keeps the R10 flood
    class (orphaned(o7_3), arbitrary ids) undecidable even with a theory
    attached: a rule set that derived `orphaned(X)` for any X would be a
    lookup wearing a rule's clothes.
  * THE THREE-OUTCOME CONTRACT SURVIVES.  Entailed -> VERIFIED with
    provenance naming the RULES that fired; refuted -> REFUTED likewise;
    undecidable -> UNCHECKABLE with its typed reason intact ('no_rules'
    — the theory ran and no rule decides the atom — or 'budget').
  * C11 PRICING.  `derivations` = the number of distinct witness tuples
    in the claim's proof chain (the witness relation carries its own
    arithmetic depth D; a decided claim at depth D consulted the D chain
    tuples — depths 1..D); `cut_depth` = D, the proof tree's depth.
    UNDECIDED claims are charged the witness rows they consulted (the
    membership scan reads the goal relation).  MARKED CONVENTION: these
    are counted on the WITNESS RELATION by this seat — the engine does
    not expose per-query derivation counters, so this is the checker's
    own accounting over engine-derived rows, stated, not the engine's
    reported unit.  The circuit-vs-formula reuse distinction stays
    UNEXERCISED for the same reason.
  * THE BUDGET GATES BOTH SIDES.  Pre-run: the theory's DECLARED bound
    (max_derivations, max_depth — a designer guarantee about the fixture)
    must fit the per-assertion/per-turn ceilings or the check is not run
    (UNCHECKABLE('budget'), nothing charged).  Post-run: the MEASURED
    cost must fit too; an under-declared theory (measured depth over its
    own declaration) is refused as 'budget' and CHARGED the measured
    cost (the work happened; hiding it would under-charge the ledger).

WALL-COST NOTE (dlb ENVELOPE.md): query_rules_ro is 0.74 ms at fixture
scale — 74x over the <=10 us per-step read budget.  The derive path is
therefore NOT on the point-read path: it fires only on a lookup MISS
with a theory ATTACHED (the default run attaches none and keeps the
measured point-read path).  Its cost is priced in the model's units
(derivations), not hidden in wall time.

THE THEORY THAT MAKES DERIVATION LIVE ON THE FIXTURE: the orphan
closure (`orphan_closure` below).  Vocabulary provenance, stated: the
SPAN predicates (done/1, orphaned/1) come from the extractor's declared
set (interleave.DECLARED_PREDICATES); the EVIDENCE predicates
(abandoned/1, blocks/2) are DESIGNER-SUPPLIED world vocabulary — the
TaskWorld already models an abandonment event (dmn_llm.step_detail's
per-turn abandoned draw), and the blocker relation is this theory's own
extension.  The harness does NOT seed the evidence relations by default:
attaching the theory without seeding evidence derives nothing, which is
the honest grounding (seeding the orphaned universe outright was refused
mid-campaign as an input change — handoff-selfreg-cen-tools-entailment
stage=warning; DERIVING it from evidence is different in kind: the
verdict still requires the world to have said something).  The bridge
that writes real world events into the evidence relations belongs to
prerequisites 2-3 (the task, real tool execution) and is NOT built here.

Run the battery:  stage2_entail_tests.py (parts T1-T7).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["Rule", "Seat", "DerivedVerdict", "Theory", "orphan_closure",
           "ARG_RE"]

#: The span grammar's ARGUMENT form, MIRRORED from interleave._ARG (the
#: extractor's own convention: lower-case-initial identifiers, digits,
#: underscore — the DMN-visible task ids, e.g. t57; NO upper-case initial
#: = no free variables, no quoted strings, no compound terms).  A mirror,
#: not an import, so this module stays importable beside cen.py without
#: dragging the extractor's routing re-export; the battery asserts the
#: mirror against interleave._ARG on a fixed sample so drift is loud.
ARG_RE = re.compile(r"[a-z_][a-z0-9_]*|[0-9]+")


@dataclass(frozen=True)
class Rule:
    """One theory rule: a stable id (verdict provenance names it) and the
    rule text in the engine's Datalog."""
    rule_id: str
    text: str


@dataclass(frozen=True)
class Seat:
    """One question a theory can answer about one SPAN relation.

    kind: 'entail' — witness rows PROVE the atom (row arg == atom arg ->
          VERIFIED at the row's depth);
          'refute' — witness rows REFUTE it (a done(X) claim about an
          unfinishable X; the verdict's provenance renders the refuted
          atom with the store's own refutes-key encoding).
    witness_rel: the derived relation to query (it carries the proof
          chain's arithmetic depth in depth_col — querying the witness
          directly gives membership AND depth in one call; the theory's
          span-facing projection clause exists for documentation and
          future bound queries, not as a second evaluation).
    provenance: the rule ids that establish the seat, in order.
    """
    kind: str                      # 'entail' | 'refute'
    relation: str                  # the SPAN relation it answers for
    witness_rel: str
    arg_col: int = 1               # index into the (relation, *cols) row
    depth_col: int = 2             # (the adapter's iter_facts/query_rules
                                   # convention: col 0 is the name)
    decode_cols: tuple = (0,)      # SYMBOL columns, indexed over the
                                   # raw args (0-based) — the str_cols
                                   # convention, not row indexing
    provenance: tuple = ()


@dataclass(frozen=True)
class DerivedVerdict:
    """The theory's answer for one ground atom (the CEN applies its
    budget gates and ledger charges on top; cen._check_derived).

    `ran` is True when the theory actually evaluated a query for this
    atom (entailed, refuted, or ran-and-undecided) and False when it was
    gated before evaluation (grammar gate, no seat, no engine surface,
    under-declared bound) — the CEN charges accordingly."""
    status: str                    # 'VERIFIED' | 'REFUTED' | 'UNCHECKABLE'
    reason: str = ""               # set for UNCHECKABLE
    provenance: tuple = ()
    derivations: int = 0
    cut_depth: int = 0
    ran: bool = False


class Theory:
    """A rule set plus the seats that map span atoms onto witness
    queries.  The CEN holds one of these as its `rules` seat (injected,
    never constructed by the CEN — the retrieval/actions precedent).

    The CONTRACT the CEN relies on (AttributeError is loud by design):
      check(engine, rel, args) -> DerivedVerdict
      max_derivations, max_depth   — the declared bound (C11 pre-gate)
    """

    def __init__(self, rules, seats, *, max_derivations: int,
                 max_depth: int, evidence: dict | None = None):
        self.rules = tuple(rules)
        self.seats = tuple(seats)
        self.max_derivations = int(max_derivations)
        self.max_depth = int(max_depth)
        #: evidence relations the theory's bodies are anchored in; the
        #: CALLER declares and seeds them on the engine (the world-bridge
        #: is prerequisites 2-3, not this seat).
        self.evidence: dict[str, int] = dict(evidence or {})

    def source(self) -> str:
        return "\n".join(r.text for r in self.rules)

    def declare_evidence(self, engine) -> None:
        """Declare the theory's evidence relations on the engine (idempotent
        at the engine level; does NOT seed facts — evidence comes from the
        world, and a theory with no evidence derives nothing)."""
        for rel, ar in self.evidence.items():
            engine.declare(rel, ar)

    def check(self, engine, rel: str, args: tuple) -> DerivedVerdict:
        """The DERIVE step for one ground atom.  Never raises on the
        happy path; DatalogError from the engine propagates (the CEN
        maps it to UNCHECKABLE('unknown_predicate') — e.g. the theory
        names an evidence relation the store never declared)."""
        # the transducer's grammar gate: an atom outside the span
        # grammar (free variable, quoted string, compound term) cannot
        # be transduced onto a goal — no rule can decide it.
        if not args or not all(ARG_RE.fullmatch(str(a)) for a in args):
            return DerivedVerdict(
                "UNCHECKABLE", reason="no_rules",
                provenance=("atom outside the span grammar — no goal",))
        q = getattr(engine, "query_rules", None)
        if q is None:
            # the stub engine has no rule machinery; the seat exists but
            # cannot run.  Debt, not a crash (the extractor's own
            # malformed-span discipline).
            return DerivedVerdict(
                "UNCHECKABLE", reason="no_rules",
                provenance=("engine has no rule surface (query_rules "
                            "absent) — theory attached but unrunnable",))
        ent = next((s for s in self.seats
                    if s.kind == "entail" and s.relation == rel), None)
        ref = next((s for s in self.seats
                    if s.kind == "refute" and s.relation == rel), None)
        if ent is None and ref is None:
            return DerivedVerdict(
                "UNCHECKABLE", reason="no_rules",
                provenance=(f"theory silent on {rel}/{len(args)}",))
        src = self.source()
        consulted = 0

        def _hit(rows):
            # MECHANICAL positional matching: the atom's args match the
            # witness row's leading columns after the relation name (the
            # row is (relation, *args..., depth); the unary convention
            # orphan_closure set is the len(args)==1 case, and arity-2+
            # heads from the LE adapter match the same way).
            want = tuple(str(a) for a in args)
            return [r for r in rows
                    if tuple(str(r[1 + i]) for i in range(len(want)))
                    == want]

        if ent is not None:
            rows = q(src, ent.witness_rel, ent.decode_cols)
            consulted += len(rows)
            hit = _hit(rows)
            if hit:
                d = max(int(r[ent.depth_col]) for r in hit)
                if d > self.max_depth:
                    # under-declared theory: refuse, charge the measured
                    # cost (the work happened)
                    return DerivedVerdict(
                        "UNCHECKABLE", reason="budget",
                        provenance=(f"theory under-declared: witness depth "
                                    f"{d} > declared max_depth "
                                    f"{self.max_depth}",),
                        derivations=d, cut_depth=d, ran=True)
                return DerivedVerdict(
                    "VERIFIED",
                    provenance=ent.provenance + (
                        f"witness {ent.witness_rel}({args[0]},{d}) — chain "
                        f"of {d} derived tuples",),
                    derivations=d, cut_depth=d, ran=True)
        if ref is not None:
            rows = q(src, ref.witness_rel, ref.decode_cols)
            consulted += len(rows)
            hit = _hit(rows)
            if hit:
                d = max(int(r[ref.depth_col]) for r in hit)
                if d > self.max_depth:
                    return DerivedVerdict(
                        "UNCHECKABLE", reason="budget",
                        provenance=(f"theory under-declared: witness depth "
                                    f"{d} > declared max_depth "
                                    f"{self.max_depth}",),
                        derivations=d, cut_depth=d, ran=True)
                key = f"{rel}({','.join(map(str, args))})"
                return DerivedVerdict(
                    "REFUTED",
                    provenance=ref.provenance + (
                        f"refutes({key}) by witness depth {d}",),
                    derivations=d, cut_depth=d, ran=True)
        # the theory RAN and no rule decides the atom: checking debt,
        # charged the witness rows the membership scan consulted.
        return DerivedVerdict(
            "UNCHECKABLE", reason="no_rules",
            provenance=(f"theory ran: no witness proves or refutes "
                        f"{rel}({','.join(map(str, args))})",),
            derivations=consulted, cut_depth=0, ran=True)


def orphan_closure(*, max_depth: int = 8,
                   max_derivations: int = 64) -> Theory:
    """The fixture theory that makes derivation live: the ORPHAN CLOSURE.

    One concept, UNFINISHABILITY, answering two span predicates:
      abandoned(X)                        -> X is unfinishable at depth 1
      pw_dead(X,D0), blocks(X,Y)          -> Y is unfinishable at D0+1
    so
      orphaned(X)  :- pw_dead(X, D)       (the ENTAIL seat: the declared
                                          but never-seeded predicate
                                          becomes derivable FROM EVIDENCE
                                          — a claim about an id no
                                          abandonment or blocker chain
                                          touches still derives nothing)
      refutes done(X) for pw_dead(X, D)   (the REFUTE seat: a done claim
                                          about an unfinishable task is
                                          false; reported through the
                                          verdict, never by writing a
                                          refutes fact — the clone is
                                          discarded and the store stays
                                          untouched)

    DESIGNER-SUPPLIED, MARKED [C]: the closure step (blocked-by-
    unfinishable is unfinishable) is this theory's own extension of the
    TaskWorld's abandonment event, not a measured world fact.  The
    declared bounds (max_depth 8, max_derivations 64 by default) are the
    DESIGNER's guarantee about the fixture — the closure the fixture's
    evidence relations can produce; a store with deeper or wider
    blocker chains must RAISE the declaration (the post-hoc gate
    refuses under-declaration loudly).  NOTE the shape of the CEN's
    pre-gate: it refuses a theory whose DECLARED bound exceeds the
    budget's ceilings, so tightening the budget below the theory's
    declaration also refuses EVERY derived check (the default theory
    declares depth 8 — under the default ceiling 8 — while a ceiling of
    4 refuses even a depth-4 check because the theory still DECLARES 8).
    That is the honest direction: a budget cannot quietly assume the
    theory will happen to stay shallower than it declares.
    """
    rules = (
        Rule("pw-dead-base",
             "pw_dead(X, D) :- abandoned(X), D = 1."),
        Rule("pw-dead-step",
             "pw_dead(Y, D) :- pw_dead(X, D0), blocks(X, Y), D = D0 + 1."),
        Rule("orphaned-proj",
             "orphaned(X) :- pw_dead(X, D)."),
    )
    seats = (
        Seat(kind="entail", relation="orphaned", witness_rel="pw_dead",
             provenance=("rule pw-dead-base", "rule pw-dead-step",
                         "rule orphaned-proj (orphan closure, designer "
                         "theory [C])")),
        Seat(kind="refute", relation="done", witness_rel="pw_dead",
             provenance=("rule pw-dead-base", "rule pw-dead-step",
                         "designed theory: an unfinishable task refutes "
                         "a done claim [C]")),
    )
    return Theory(rules, seats, max_derivations=max_derivations,
                  max_depth=max_depth,
                  evidence={"abandoned": 1, "blocks": 2})


# ===========================================================================
# stage=correction (2026-09-27, the LE adapter handoff-selfreg-le-wiring):
# the DEFERRED list above said "the controlled-natural-language surface of
# LE (LE rule text, full LE sentences)" is NOT covered.  That statement is
# now SUPERSEDED IN PART, and by APPEND (the original is left verbatim
# above; this correction states the new boundary, not a rewrite of the old
# claim).  The compiler at ~/thing/logical-english/ (v1: the DECLARATIVE
# subset, 106 tests incl. 7 real-engine round-trips) plus the adapter
# agent/le_theory.py now cover, THROUGH THE REAL COMPILER, on this seat:
#
#   * LE sentence surface: article/ordinal variable binding (a/the/
#     first/second/another/the other), ground fact sentences, and the
#     closed declared lexicon ([sorts]/[names]/[predicates]);
#   * comparison copulas (is before/on or after/on or before -> <, >=, <=)
#     and the `N days before` arithmetic producer;
#   * stratified negation (`it is not the case that` -> !atom, engine
#     checked, unsafe forms refused by the compiler);
#   * arity-2+ head predicates (this seat's matcher was extended from the
#     unary orphan_closure convention to positional multi-arg matching —
#     identical behaviour for unary witnesses, measured);
#   * RECURSIVE rules, with the depth column the CEN charges derived from
#     the adapter's mechanical witness transformation (a chain a->b->c->d
#     reports depth 3 for d, the real proof-tree depth).
#
# STILL NOT COVERED (unchanged from the original statement, plus the
# compiler's own v1 refusals — see its README's gap table): LPS reactive
# rules, fluent updates/event calculus, the meta-level `states that`
# embedding, relative clauses, plurals/quantifiers, conjunctive
# conclusions, existential head variables (skolemization), ontology
# extension (the predicate set stays closed), aggregates, the generative
# decoder, and the persisted compile path (this seat still uses the
# throwaway-clone query_rules_ro surface; the store stays byte-untouched).
# Negation over a WITNESS relation is refused by the engine's unsafe-
# negation check (a depth variable in a negated atom is unbindable), so
# refuted-by-absence remains out of reach for transformed witnesses —
# stated, not worked around.
# ===========================================================================
