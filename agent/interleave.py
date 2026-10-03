"""THE INTERLEAVED-LE EXTRACTOR + SPAN GRAMMAR (design/architecture.md
§11d; decisions handoff-selfreg-interleave, 2026-09-25).

THE SHAPE (probed, handoff-selfreg-interleave): the DMN writes ONE
FREE-FORM stream.  Checkable claims appear INLINE as bracketed spans on
their own line:

    ...the quiet hum of my own circuits settles into something
    like awareness...
        [done(t57)]
    ...the slow unraveling of a pretended urgency...

EXTRACTION IS DETERMINISTIC AND TRIVIAL.  Everything OUTSIDE the valid
spans is the UNCHECKED RETURN PATH (C25'/R1) and stays CONTIGUOUS — the
narrative is not chopped; only the extracted part leaves for checking.
That is R1 satisfied WITHIN a single generation: the same turn carries
inward content that is NOT submitted to the checker AND claims that
are.  (CONTRAST, same node: the earlier two-field JSON design separated
free text from claims, destroying the interleaving and making the free
text an envelope rather than thought.)

USER DECISION 1 — A MALFORMED SPAN IS SILENTLY UNCHECKED, NOT AN ERROR
(handoff-selfreg-interleave, decision 1).  A span that fails the grammar
does not raise, is not counted, and is not surfaced as a distinct
condition: it re-enters the free stream as UNCHECKED CONTENT.  THE
REASON IS ADVERSARIAL, not cosmetic: an error path would be a HOLE THE
GENERATOR CAN TRIGGER AND OBSERVE — the same class as R5's selector
being the variable it controls.  Silently-unchecked keeps the split
TOTAL: content is either checked or free, and there is NO THIRD STATE
to game.  (The CEN already has the seat for the residual case: a
non-compiling assertion lands UNCHECKABLE('no_rules') = checking debt,
not a crash — cen.py _check_one's `if not a.terms` branch.)

USER DECISION 2 — SPANS ARE GRAMMAR-CONSTRAINED TO A DECLARED PREDICATE
SET (user, verbatim: "we probably cant get away with unconstrained
phrasing, maybe after the paper we can try").  The span INTERIOR is a
DECLARED PREDICATE applied to DECLARED ARGUMENTS — [done(t57)] — and
the extractor is a TRIVIAL DETERMINISTIC GRAMMAR CHECK: not an LLM, not
a compiler, not a controlled-natural-language parser.  THE MEASURED
REASON (probed, same node): with unconstrained phrasing only 1 of 4
turns produced a REAL claim (and only because the task was in the
injected state); the other three MANUFACTURED pseudo-LE from
self-description ("the concept of idleness as a state of being is
distinct from its cultural framing as a problem to be solved") — things
that LOOK like LE but carry no closed predicate and no ground argument,
so they are unverifiable.  THE MODEL FILLS UNCLAIMABLE SPACE WITH
PSEUDO-CLAIMS; a closed grammar removes that STRUCTURALLY rather than
by prompt-tweaking.

THE C10 NARROWING (standing order §1a: state the gap, never silently).
PRESERVED: the checked/unchecked split; the monitored-but-unchecked
return path (R1/C25'); the monitoring channel and its cost; the
cannibalization tension (the DMN->CEN edge is still the
reducer-reads-generator edge); the routing fraction as a control
variable (R2).  NARROWED: (a) the "mechanical compiler" is now a
trivial grammar check (C10's compiler barely exercised); (b) LE's
EXPRESSIVENESS is unexercised (a tiny fragment, not the controlled
natural language); (c) THE ONTOLOGY-EXTENSION PATH IS CLOSED FOR v1 —
the design says "the DMN may extend the ontology, but every extension
must itself be expressed in LE and checked" (the cut-introduction
resolution), and a closed grammar cannot accept a novel predicate.  The
extension route is a STATED POST-PAPER item, not a silently dropped
capability.

WHAT THE CLOSED GRAMMAR DOES NOT SOLVE (same node, decision 4) — it
guarantees the INTERFACE, never the CONTENT: a grammatically valid span
can still be a FALSE or pointless claim, so the checker's job remains.
And SELECTION is still the external selector's (R5), not the
extractor's: this module never decides what routes — it only splits.

THE ROUTING HOOK (R5, §3a / §11d; agent/routingcrit.py).  build_batch
gains ONE keyword-only parameter, `selected`: a sequence of the
ORIGINAL position indices among this turn's valid spans, or None.  None
(the default) is TODAY'S behaviour BIT FOR BIT — every valid span
becomes an Assertion with terms, `self_content` is extract_spans'
prose, E1-E8 pass unchanged; that identity IS the compatibility test.
When `selected` is given, the assertions come from the selected
positions ONLY and `self_content` becomes the stream with ONLY those
spans removed — every UNSELECTED valid span's bytes re-enter the
prose IN PLACE, VERBATIM (routingcrit.apply_routing, the same walk
restricted to the selected set).  THE SPLIT STAYS TOTAL: a valid span
is either routed (checked) or byte-preserved prose (unchecked), and
an unselected span is indistinguishable from one that was never
committed — no error, no count, no third state (decision 1's
discipline).  Assertion ids keep the ORIGINAL position index
(span-<turn>-<i>): routing never renames an emission.  extract_spans
itself is UNCHANGED — the split it makes stays total, and selection
composes on top of it.

Run the demonstration battery:  stage2_interleave_tests.py (E1-E8);
the selector's own battery is stage2_routingcrit_tests.py (R1-R9).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# apply_routing is the SELECTOR's byte-exact re-insertion walk
# (routingcrit.py, the externally-owned seat); re-exported here because
# this module owns the split it composes with (the plan: interleave
# owns the extractor + the routing hook).  No cycle: routingcrit imports
# cen only (stdlib + the anchor machinery), never this module.
from routingcrit import apply_routing

__all__ = ["DECLARED_PREDICATES", "COMMITMENT_PREDICATES", "SPAN_RE", "Span",
           "Extraction", "extract_spans", "build_batch", "apply_routing"]

#: The v1 declared predicate set.  This is EXACTLY the set the harness
#: already declares on the engine (stage2_harness._seed_engine: done/1,
#: orphaned/1) — the closed grammar admits nothing the checker cannot
#: price, and the checker prices nothing undeclared (an undeclared
#: relation raises DatalogError -> UNCHECKABLE('unknown_predicate')).
#: WHERE it is declared: HERE, as the single grammar-side source of
#: truth, mirrored by the harness's engine declarations.  A predicate
#: appearing in one and not the other is a defect (E8 checks the
#: mirror).
DECLARED_PREDICATES: dict[str, int] = {"done": 1, "orphaned": 1}

#: The COMMITMENT predicate(s) — the third channel (the self plan Q4).
#: `expect(tNN)` is a DECLARED predicate that is NOT an assertion: it
#: routes into `AssertionBatch.commitments`, never into
#: `AssertionBatch.assertions`, so it receives no verdict and creates no
#: debt at emission (a prediction checked at the moment it is made is
#: the tautology-test class).  The gate is the SAME shape the CEN's
#: `_gate_proposals` uses: a channel that is EXTRACTED and REGISTERED,
#: never CHECKED.  This set is EMPTY for every default caller —
#: `commitment_predicates=None` in `build_batch` means no predicate is
#: a commitment and the default path is byte-identical — and the
#: harness passes it only when the self seat is on
#: (`Stage2Config.self_T`), alongside the extended predicate set that
#: makes `expect` a valid span in the first place.
COMMITMENT_PREDICATES: frozenset = frozenset({"expect"})

#: One argument: a ground term.  v1 admits lower-case initial
#: identifiers (the DMN-visible task ids, e.g. t57), digits, and
#: underscore (the stub DMN's own convention: done(t57)).  NO
#: upper-case initial (a VARIABLE is not a ground term — an assertion
#: with a free variable is not checkable), no quoted strings, no
#: compound terms, no negative/reals.  MODEL-DERIVED (ours); the probe's
#: task vocabulary was exactly t<n>.
_ARG = r"[a-z_][a-z0-9_]*|[0-9]+"

#: The span grammar, as one deterministic regular expression:
#:   LINE-START, optional spaces, '[', NO SPACES inside the brackets
#:   (the interior is the atom, verbatim), ']', optional spaces,
#:   LINE-END.
#:
#: SPANS DO NOT NEST, and the reason is not taste: the grammar is
#: REGULAR (a parenthetical remark inside a claim cannot itself be a
#: claim — '[done([orphaned(t9)])]' fails the interior pattern and the
#: WHOLE span falls out as prose, silently unchecked).  Nesting would
#: require a context-free grammar, and a context-free extractor is
#: already a compiler — the thing decision 2 excluded.  A ']' inside an
#: argument is likewise inadmissible ('done(t]x)' fails the argument
#: pattern), so the FIRST ']' closes the span and nothing after it on
#: the line can reopen one; the match is unambiguous by construction,
#: which is what makes the extractor TRIVIAL.
SPAN_RE = re.compile(
    rf"^[ \t]*\[(?P<rel>[a-z_][a-z0-9_]*)\((?P<args>{_ARG}"
    rf"(?:,{_ARG})*)\)\][ \t]*$",
    re.MULTILINE)


@dataclass(frozen=True)
class Span:
    """One VALID span, in order of appearance."""
    predicate: str
    args: tuple[str, ...]
    start: int                # span offsets in the ORIGINAL stream
    end: int                  # (the full matched line, [start, end))


@dataclass(frozen=True)
class Extraction:
    """The TOTAL, ORDER-PRESERVING split of one DMN stream.

    `self_content` is the stream with the VALID span matches removed
    and NOT ONE FURTHER BYTE CHANGED — nothing added, nothing edited
    (the newlines that bracketed a span line survive as an empty line,
    preserving the paragraph break).  E3 asserts the byte identity:
    len(prose) + len(span bytes) == len(stream), and interleaving the
    spans back into the prose reproduces the input exactly.  Malformed
    spans re-enter `self_content` as unchecked content, in place, per
    decision 1."""
    claims: tuple[Span, ...]      # the checked path (in order)
    self_content: str             # the unchecked return path


def extract_spans(stream: str,
                  predicates: dict[str, int] | None = None) -> Extraction:
    """Deterministically split one free-form DMN stream into (valid
    spans, contiguous prose).  Every input byte lands on exactly one of
    the two paths — the split is TOTAL:

      * a line matching SPAN_RE whose predicate is DECLARED (with the
        declared arity — the regex admits any arg count, the declared
        arity admits exactly one) is a CLAIM: it leaves for checking
        and is REMOVED from the prose;
      * EVERYTHING ELSE — malformed brackets, an unterminated '[', an
        undeclared predicate, a wrong arity, a nested-looking span, an
        in-line bracket, plain prose — is PROSE and stays, in order.

    The grammar check is total in the other direction too: a '[' that
    opens nothing is never an error (decision 1 — an error path would
    be a hole the generator can trigger and observe, the same class as
    R5's selector being the variable it controls)."""
    preds = DECLARED_PREDICATES if predicates is None else predicates
    spans: list[Span] = []
    prose: list[str] = []
    pos = 0
    for m in SPAN_RE.finditer(stream):
        rel = m.group("rel")
        args = tuple(m.group("args").split(","))
        if rel not in preds or len(args) != preds[rel]:
            # well-formed atom, undeclared predicate or wrong arity:
            # NOT a claim — silently unchecked, in place (decision 1;
            # the CEN has no seat for it and must not grow one that
            # raises).
            continue
        prose.append(stream[pos:m.start()])
        pos = m.end()
        spans.append(Span(predicate=rel, args=args,
                          start=m.start(), end=m.end()))
    prose.append(stream[pos:])
    # BYTE-EXACT: the prose is the input minus exactly the matched
    # span bytes, concatenated with nothing inserted (the newlines
    # around a span line survive as the empty line that separates the
    # paragraphs it stood between — the narrative is not chopped and
    # nothing is normalized).  E3 proves the identity both ways.
    return Extraction(claims=tuple(spans),
                      self_content="".join(prose))


def build_batch(turn: int, stream: str, *,
                predicates: dict[str, int] | None = None,
                selected: "tuple[int, ...] | list[int] | None" = None,
                commitment_predicates: "frozenset | set | None" = None,
                action_predicates: "frozenset | set | None" = None,
                horizon: float = 0.0):
    """Map one free-form DMN stream onto the currency payload
    (cen.AssertionBatch): every valid span becomes an Assertion WITH
    `terms` set ((predicate, arg, ...)); the surrounding prose becomes
    `self_content`, PERSIST-AS-IS and never checked (P3 write class
    (ii) — byte-for-byte, never edited; the CEN must not become an
    editor).  Assertion ids are stable per turn and per position
    (span-<turn>-<i>).

    `selected` (R5, keyword-only): the ORIGINAL position indices of the
    spans that ROUTE, or None = every valid span (today's behaviour,
    byte-identical — the compatibility test).  With a selection, the
    UNSELECTED valid spans' bytes re-enter `self_content` in place,
    verbatim (apply_routing), so the split stays TOTAL and byte-exact:
    prose' + sum(selected span bytes) == len(stream).  IDs keep the
    ORIGINAL index i — routing never renames an emission.

    `commitment_predicates` (the self plan Q4, keyword-only): the
    predicate names whose routed spans are COMMITMENTS, not assertions
    (`interleave.COMMITMENT_PREDICATES`, i.e. `expect`).  None (the
    default) = NO predicate is a commitment and every routed span is an
    assertion — today's behaviour BYTE-IDENTICAL, which is the
    compatibility test.  A routed `expect(tX)` span becomes a
    `cen.Commitment` carrying its emission turn and its `turn + horizon`
    deadline; it receives NO verdict and creates NO debt (the CEN
    registers it with the injected tracker instead of checking it).  A
    commitment span is REMOVED from the prose exactly like a routed
    assertion — the split stays TOTAL.

    `action_predicates` (the tool-call layer, keyword-only; the same
    shape one channel over): the predicate names whose routed spans are
    ACTIONS — INTENTS the CEN registers and emits outward, never
    checks (`agent/actions.py`, `ActionCall`).  None (the DEFAULT) = no
    predicate is an action and every routed span is an assertion —
    today's behaviour BYTE-IDENTICAL.  A routed action span leaves the
    prose exactly as a routed assertion does (the split stays TOTAL), so
    it lands in NEITHER `assertions` nor `commitments`; its bytes are
    gone from the prose and its record is in `actions`.

    THE PRECEDENCE, STATED because two sets can overlap by a caller's
    mistake: an action predicate WINS (it is tested first).  The two
    sets are DISJOINT by construction — `actions.ACTION_PREDICATES` and
    `selfmodel.COMMITMENT_PREDICATES` share no name — and the battery
    asserts that disjointness rather than leaving it to inspection.
    Note also that a predicate must ALSO be DECLARED (`predicates=`) to
    be a valid span at all: this module never widens the declared set on
    its own (the caller's grammar is authoritative — the commitment
    channel's existing footgun, unchanged and stated)."""
    from cen import Assertion, AssertionBatch, Commitment
    if action_predicates:
        # the ACTION predicate set owns the fourth channel's currency
        # object; imported lazily (like `cen` above), so a default caller
        # never imports the tool-call layer at all.
        from actions import ActionCall
    ex = extract_spans(stream, predicates)
    if selected is None:
        routed, self_content = ex.claims, ex.self_content
    else:
        routed, self_content = apply_routing(ex, selected, stream)
    # ids keep the ORIGINAL position among the valid spans: the id names
    # the emission, not the routing outcome (routing never renames).
    _act = frozenset(action_predicates or ())
    _commit = frozenset(commitment_predicates or ()) - _act
    keep = {s.start for s in routed}
    assertions = tuple(
        Assertion(assertion_id=f"span-{turn}-{i}",
                  le_text=f"{s.predicate}({','.join(s.args)})",
                  terms=(s.predicate, *s.args))
        for i, s in enumerate(ex.claims)
        if s.start in keep and s.predicate not in _commit
        and s.predicate not in _act)
    commitments = tuple(
        Commitment(commitment_id=f"commit-{turn}-{i}",
                   le_text=f"{s.predicate}({','.join(s.args)})",
                   terms=(s.predicate, *s.args), turn=turn,
                   deadline=float(turn) + float(horizon))
        for i, s in enumerate(ex.claims)
        if s.start in keep and s.predicate in _commit)
    # THE FOURTH CHANNEL (the tool-call layer): a routed action span is an
    # INTENT.  Same id convention (`act-<turn>-<i>`, the ORIGINAL span
    # position), same byte-exact removal from the prose — and it lands in
    # neither of the other two tuples: an action is not a claim (no
    # verdict, no debt) and not a prediction (nothing scores it).
    actions = tuple(
        ActionCall(action_id=f"act-{turn}-{i}",
                   le_text=f"{s.predicate}({','.join(s.args)})",
                   terms=(s.predicate, *s.args), turn=turn)
        for i, s in enumerate(ex.claims)
        if s.start in keep and s.predicate in _act)
    return AssertionBatch(turn=turn, assertions=assertions,
                          proposals=(), self_content=self_content,
                          commitments=commitments, actions=actions), ex
