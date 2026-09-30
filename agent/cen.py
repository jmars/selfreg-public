"""STAGE-2 SCAFFOLD — the CEN component boundary (the checking half).

Stage 2 is the other half of the agent: Stage 1 (sn.py + harness.py, both
READ-ONLY here) built the regulator / control loop; this module fixes the
ARCHITECTURE of the executive side — the component boundaries, interfaces
and invariants — so the parts still pending a measurement can drop in
later.  It is a SCAFFOLD, largely PROJECTION by construction: the
dynamical claims live in Stage 1; nothing here has been near a collapse
trajectory.

The design is NOT re-derived here.  arch-open-plan.md P1-P5 is the spec,
reconciled against the later substrate decision (C10,
handoff-selfreg-cen-datalog): the CEN is a DATALOG ENGINE (datalog-dafsa,
/home/jaye/fixpoint-linux/datalog-dafsa/, C sources, no Python binding
yet — being built in a PARALLEL task) and the currency is LOGICAL ENGLISH
<-> DATALOG.  Reconciliations, stated once:

* P3 (CEN sole writer, two write classes, one txn per turn, FIFO queue,
  SN never writes, DMN proposes only) — implemented below as code-level
  invariants, not comments.
* P2 (the G->D coupling via the currency) — the CEN exposes the REAL
  backlog signal (assertions outstanding + checking debt) and advances
  its EMA with the exact ZOH recursor.  WIRING it into the plant's edge
  is deliberately default-OFF in stage2_harness.Stage2Config: Stage 1's
  edge B = EMA_tauD(c) is the verified, fold-preserving form, and
  changing its drive is a dynamics change that needs its own fold
  measurement (same discipline Stage 1 applied to retrieval wiring).
* P4 (LE tooling by bake-off) — the bake-off still gates the COMPILER;
  the ENGINE side is decided (C10).  Until both the binding and the
  compiler exist, assertions carry their LE text plus a trivial
  term form, and StubDatalogEngine checks the term form only.
* C11 — cost is accounted in DERIVATIONS and CUT DEPTH, never tokens.
* C8 — the harness asserts on the INTEGRATED state, never on a log
  (the artifact-1 failure: gen-2 M_self[0] = 0.000000 against a
  recorded 0.286782 because the test read the carry LOG).
* C9 — the durable record lives OUTSIDE any compactable channel, is
  append-only, hash-chained, and single-writer; DECISIONS (not results)
  are the unrecoverable class, so the reason is a required field.
* C5 — the class-discriminator interface (two cheap signals) with the
  rule-based stub from the constraint table; the in-vivo signal
  SUPPLY is pending exp15/exp16.
* C3/C12 — the controller knob set is EXCLUDED from the self-modifiable
  levers, and admitting it is structurally impossible until an
  evidence-widener has passed the Boundary Correspondence Test.

Run the invariant battery:  stage2_tests.py (parts S1-S9).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar, Iterable, Protocol, Sequence

__all__ = [
    "AssertionStatus", "Verdict", "Assertion", "AssertionBatch",
    "BatchResult", "TurnRecord", "LeverProposal", "Commitment",
    "CostBudget", "DerivationLedger",
    "WriterToken", "SoleWriterError",
    "DecisionRecord", "DurableRecord", "ChainError",
    "RecordAnchor", "AnchorError", "DEFAULT_ANCHOR_DIR",
    "DatalogError", "DatalogEngine", "StubDatalogEngine",
    "DiscriminatorSignals", "CollapseClass", "ClassDiscriminator",
    "StubClassDiscriminator",
    "BoundarySpec", "BoundaryCorrespondence", "EvidenceWidener",
    "PendingEvidenceWidener", "boundary_correspondence",
    "CONTROLLER_LEVERS", "LeverRejected", "AdmissibleLevers",
    "CEN",
]


# ==========================================================================
# The currency objects (P2/P4): what a DMN turn produces and what the
# CEN hands back.  The LE text is the DMN's actual product; `terms` is
# the mechanical compilation target (predicate + ground args) the engine
# consumes.  The compiler that turns one into the other is PENDING the
# P4 bake-off gate + the datalog-dafsa binding (C10).
# ==========================================================================

class AssertionStatus(Enum):
    VERIFIED = "VERIFIED"
    REFUTED = "REFUTED"
    UNCHECKABLE = "UNCHECKABLE"   # open ontology: no applicable rules, or
                                  # budget exceeded -> checking DEBT (P2)


UNCHECKABLE_REASONS = ("no_rules", "budget", "unknown_predicate")


@dataclass(frozen=True)
class Assertion:
    """One claim, in the currency's two layers.  `assertion_id` is the
    DMN's stable id; `le_text` is the Logical-English sentence; `terms`
    is (predicate, args...) after compilation.  Terms may be empty (the
    compiler does not exist yet) — such assertions check UNCHECKABLE."""
    assertion_id: str
    le_text: str
    terms: tuple = ()            # (predicate_name, arg, arg, ...)

    @property
    def predicate(self) -> str | None:
        return self.terms[0] if self.terms else None


@dataclass(frozen=True)
class LeverProposal:
    """A self-modification proposal from the DMN.  NOTHING is admissible
    by default (no lever has passed any test); the controller knob set
    is excluded outright (C3/C12 — see CONTROLLER_LEVERS)."""
    lever_id: str
    new_value: object
    reason: str


@dataclass(frozen=True)
class Commitment:
    """ONE `expect(tX)` span — the self-model made CHECKABLE, and the
    GOAL-GENERATION surface (design/architecture.md §11d; the self plan
    Q4, `handoff-selfreg-self-plan`).

    A commitment is NEITHER an assertion NOR a proposal: it is a THIRD
    channel.  It gets NO verdict and NO debt at emission (checking a
    prediction against the store the moment it is made is the
    tautology-test class — a test that cannot fail); the injected
    CommitmentTracker registers it and scores it at a consolidation
    BOUNDARY, by which time `done(target)` either landed or did not.
    Scoring the OPEN-SET is the goal-generation observable; EXPIRY IS AN
    OBSERVABLE, NEVER DEBT — making expiry debt would add a new
    self-to-D coupling edge and violate C26c's two independent axes (the
    harness already refuses a second c-arrival term for exactly this
    reason, stage2_harness.py's coupling docstring).

    `deadline` is the horizon: an `expect(tX)` emitted at turn `n` must
    land by `n + T` (T the per-campaign commitment horizon, the plan's
    decision 2).  The tracker owns T; the batch carries only what the
    span said."""
    commitment_id: str
    le_text: str
    terms: tuple = ()            # ("expect", "tNN")
    turn: int = 0                # the emission turn
    deadline: float = 0.0        # turn + T (the horizon, set by the caller)

    @property
    def target(self) -> str | None:
        """The task id the commitment predicts about (`expect(tNN)`)."""
        return self.terms[1] if len(self.terms) > 1 else None


@dataclass(frozen=True)
class AssertionBatch:
    """The DMN's per-turn product: assertions-to-be-checked, optional
    self-modification proposals, its self-summary content — which is
    persisted BYTE-FOR-BYTE, never checked, never edited (P3 write
    class ii: persist-as-is keeps the CEN from becoming an editor) —
    the COMMITMENTS channel (the `expect(tX)` spans; see `Commitment`),
    and the ACTIONS channel (the `complete(tX)` spans; see
    `agent/actions.py`, `ActionCall`).

    FOUR CHANNELS, FOUR TREATMENTS, and the difference is the point:
    assertions are CHECKED (reduction demand, priced in derivations),
    proposals are GATED (C3/C12, nothing admissible by default),
    commitments are REGISTERED and scored at a boundary (never checked
    — the tautology class), and actions are REGISTERED and EMITTED
    outward (never checked: an intent is not a claim; never charged to
    the derivation ledger: expression is not reduction — the standing
    order).  `commitments` and `actions` both default to () so every
    pre-existing caller is byte-identical; `actions` holds
    `actions.ActionCall` objects and is typed loosely here on purpose —
    the CEN hosts the channel and never constructs, checks or executes
    its payload (the `retrieval`/`commitments` seating precedent)."""
    turn: int
    assertions: tuple[Assertion, ...] = ()
    proposals: tuple[LeverProposal, ...] = ()
    self_content: str = ""
    commitments: tuple[Commitment, ...] = ()
    actions: tuple = ()


@dataclass(frozen=True)
class Verdict:
    """P2's per-assertion return: {id, status, provenance}.  Cost fields
    are C11's units — derivations consumed and deepest cut used — NEVER
    tokens (a token count cannot bound a proof-search engine's cost)."""
    assertion_id: str
    status: AssertionStatus
    provenance: tuple[str, ...] = ()   # which facts/rules fired
    reason: str = ""                   # set for UNCHECKABLE
    derivations: int = 0
    cut_depth: int = 0


@dataclass
class BatchResult:
    verdicts: list[Verdict] = field(default_factory=list)
    derivations_total: int = 0
    cut_depth_max: int = 0
    backlog_outstanding: int = 0       # queue depth + debt, AFTER the turn
    rejected_proposals: tuple[LeverProposal, ...] = ()


@dataclass
class TurnRecord:
    """What one DMN turn produced.

    THE ACTUATION CLAIM, CORRECTED IN PLACE (2026-09-27).  This
    docstring used to say "the CEN checks, it does not act (arch rule
    9; P2 topology constraint 3)".  That reading predates the recorded
    design decision (`handoff-selfreg-cen-tools-entailment`, decision
    3): THE CEN HANDLES TOOL CALLS AND ITS OUTPUT IS THE 'talking'
    STREAM TO THE HARNESS, so the executive side DOES have an outward
    path.  WHAT REMAINS TRUE, and is what the old sentence was
    protecting (arch rule 9 is about the REGULATOR - "the regulator
    must have actuator authority, not just sensors" - and is
    mis-cited as a CEN rule here): the CEN holds NO ACTUATOR AUTHORITY
    OVER THE PLANT.  Actuator authority stays with the SN, and the
    frozen model has no action input at all (dpdr/model.py:107-124
    reads no action quantity), so the tool-call layer's effect lands on
    a THIRD surface - the harness's own task bookkeeping
    (`agent/actions.py`, `ToolWorld`) - and never on `a/G/D/S/g`.  The
    talking seat is an EMISSION seat, not an actuation one: the CEN
    registers an intent and emits it; the WORLD applies it.
    (`talking` is the outward stream's sole seat; it is None - the
    default - whenever no action seat is attached, so every
    pre-tool-call caller is byte-identical.)"""
    turn: int
    result: BatchResult
    decisions: tuple[str, ...] = ()    # decision_ids appended to the record
    txn_rev: int = -1                  # store revision after commit
    ts: str = ""
    retrieval: object = None           # the per-turn RetrievalOutcome
                                       # (present only when a retrieval
                                       # seat is attached; the self's
                                       # per-turn context — carried on
                                       # the turn's record, never on
                                       # the working set)
    encoding: object = None            # the per-turn GateOutcome
                                       # (salience.EncodingGate;
                                       # present only when an ENCODING
                                       # GATE seat is attached — the
                                       # tier decision, its signals and
                                       # its reason; None (the default)
                                       # is the pre-encoding behaviour)
    talking: object = None             # the per-turn TalkingEmission
                                       # (actions.TalkingEmission;
                                       # present only when an ACTION
                                       # seat is attached — see the
                                       # corrected actuation claim
                                       # above)


# ==========================================================================
# C11 — the cost budget, in derivations and cut depth, not tokens.
# The ODE phase's bound is cost-not-capability throughout (c_mon ceiling,
# standing-cost budget); the Datalog leg shows the cost object is
# derivation reuse and cut depth.  A check that would exceed the budget
# is NOT run: it returns UNCHECKABLE(reason='budget') and becomes
# checking debt — the same seat P2 gives coinage (kappa_u < kappa_fail).
# The COST SURFACE is DatalogEngine.check_cost(relation, args): the
# engine reports (derivations, cut_depth) in the model's units, and the
# CEN charges what it reports instead of hardcoding a constant.  For a
# ground-fact lookup the honest report is (1, 0) — one distinct stored
# fact consulted, no proof tree (cut depth 0).  Reuse accounting
# (circuit vs formula) is UNEXERCISED while there are no rules: the seat
# is built, the distinction is stated, nothing is fabricated.
# ==========================================================================

@dataclass(frozen=True)
class CostBudget:
    derivations_per_turn: int = 10_000
    derivations_per_assertion: int = 1_000
    cut_depth_max: int = 8

    def within_turn(self, spent: int, cost: int) -> bool:
        return spent + cost <= self.derivations_per_turn


@dataclass
class DerivationLedger:
    """Cumulative derivation accounting (C11).  `debt_assertions` is the
    UNCHECKABLE set — assertions awaiting/resisting verification; the
    P2 discharge path (supply a checked LE definition) is not built."""
    spent_total: int = 0
    spent_this_turn: int = 0
    max_cut_depth: int = 0
    debt_assertions: list[str] = field(default_factory=list)

    def charge(self, derivations: int, cut_depth: int = 0) -> None:
        self.spent_total += derivations
        self.spent_this_turn += derivations
        self.max_cut_depth = max(self.max_cut_depth, cut_depth)

    def begin_turn(self) -> None:
        self.spent_this_turn = 0


# ==========================================================================
# C9 — the durable record: outside any compactable channel, append-only,
# hash-chained, sole writer.  DECISIONS are the unrecoverable class
# (measured in vivo this session: compaction destroyed the design
# context; results were re-derivable, decisions and their reasons were
# not), so `reason` is required and the record is written BEFORE the
# store txn commits — a crash can orphan a decision (the recoverable
# direction) but can never commit an action whose reason is gone.
# ==========================================================================

class SoleWriterError(RuntimeError):
    """P3: the CEN is the SOLE writer.  A second writer handle on the
    same record (or store) is rejected, not serialized."""


class ChainError(RuntimeError):
    """C9: the durable record failed verification — a decision was
    rewritten or dropped, the chain is not contiguous, or the integrity
    anchor is absent/corrupt (fail-closed: absence refuses the open)."""


@dataclass(frozen=True)
class WriterToken:
    """Capability object handed to the ONE writer.  Records and engines
    compare identity, so a second CEN on the same artifacts fails fast."""
    writer_id: str
    _serial: int = 0
    _ISSUE: ClassVar[int] = 0

    @classmethod
    def issue(cls, writer_id: str) -> "WriterToken":
        cls._ISSUE += 1
        return cls(writer_id, cls._ISSUE)


@dataclass(frozen=True)
class DecisionRecord:
    """One durable decision with its reason (required — C9).

    The chain is KEYED: `_digest` is an HMAC-SHA256 under the anchor key
    (see `RecordAnchor`), not a bare sha256 of the public fields.  An
    unkeyed chain detects accidents (torn writes, naive edits) but not
    adversaries: anyone who can read the record can recompute a bare
    sha256 and rewrite history that reopens clean.  With a key that
    never lives in the record's own namespace, recomputation requires
    the anchor's secret."""
    seq: int
    turn: int
    decision_id: str
    kind: str                 # 'reject_proposal' | 'commit' | ...
    content: str
    reason: str
    ts: str
    prev_hash: str
    hash: str

    def to_line(self) -> str:
        return json.dumps({
            "seq": self.seq, "turn": self.turn,
            "decision_id": self.decision_id, "kind": self.kind,
            "content": self.content, "reason": self.reason, "ts": self.ts,
            "prev_hash": self.prev_hash, "hash": self.hash,
        }, sort_keys=True)

    @staticmethod
    def _digest(prev_hash: str, seq: int, turn: int, decision_id: str,
                kind: str, content: str, reason: str, ts: str,
                key: bytes | None = None) -> str:
        """HMAC-SHA256(key, fields) when a key is supplied (the C9
        integrity anchor); bare sha256 otherwise, so the function stays
        usable for hash utilities that are NOT chain links.  Production
        paths (DurableRecord append/verify) always supply the key."""
        blob = json.dumps([prev_hash, seq, turn, decision_id, kind,
                           content, reason, ts], sort_keys=True)
        if key is not None:
            return hmac.new(key, blob.encode(),
                            hashlib.sha256).hexdigest()
        return hashlib.sha256(blob.encode()).hexdigest()


class AnchorError(ChainError):
    """C9 fail-closed: the integrity anchor is absent, unreadable, or
    corrupt, so the record's integrity cannot be established.  The open
    is REFUSED — the file is never trusted on the anchor's absence."""


#: Where anchors live.  DELIBERATELY OUTSIDE the store namespace (the
#: record's directory): a guard introduced to fix a gap must not be
#: placed where the thing it guards can rewrite it.  Resolved at
#: construction time: explicit arg > CEN_ANCHOR_DIR env > ~/.cen-anchors
#: (tests set the env or the arg per-run to stay isolated).
DEFAULT_ANCHOR_DIR = os.path.join(os.path.expanduser("~"), ".cen-anchors")


class RecordAnchor:
    """The out-of-namespace integrity anchor for one DurableRecord.

    WHERE THE SECRET LIVES: a per-record file `<anchor_dir>/<sha16(abs
    record path)>.anchor` (default anchor dir `~/.cen-anchors/`, mode
    0600, directory 0700), holding a 32-byte random HMAC key generated
    once at record creation, plus the sealed high-water mark (count,
    head_hash) committed after every append.  Each record gets its own
    key (the anchor file is keyed by the record's absolute path), so
    two records never share a chain even by accident.  The mark itself
    is sealed: mark_mac = HMAC(key, count|head_hash), so an attacker
    who can WRITE the anchor file but not READ it still cannot forge a
    valid rolled-back mark.

    WHY THE RECORD'S NAMESPACE CANNOT REACH IT: the record's own writes
    are confined to its path and its parent directory; the anchor dir
    is a DIFFERENT directory tree, and no code path from DurableRecord
    or the CEN writes anywhere under the record's directory except the
    record file itself.  A tamperer who can rewrite the record file and
    everything beside it still cannot read or write the anchor without
    stepping outside that namespace (different directory, 0600/0700).

    WHAT HAPPENS WHEN IT IS ABSENT: REFUSE TO OPEN (AnchorError, a
    ChainError subclass) — never "trust the file", never re-derive the
    anchor from the record.  Absence is indistinguishable from
    deletion, and deletion is an attack (review B2), so absence is
    treated as one.

    ATOMICITY: the anchor file is written tmp+rename+fsync(dir), so a
    crash mid-commit leaves either the old or the new mark, never a
    torn one.

    RESIDUAL RISK (recorded, not closed in-process): same-OS-user
    compromise, or theft of an old anchor-file copy, defeats both the
    key secrecy and the high-water mark.  A same-namespace adversary
    (can read/write the record's directory only) is defeated.  This is
    the strongest form available without an external service/KMS; it
    trades the v1 sidecar's self-contained portability for tamper
    evidence against the record's own namespace.  Records whose anchor
    must move between machines require a deliberate re-anchoring step
    (not built) — we record that as a cost, not a closure claim."""

    def __init__(self, record_path: str, anchor_dir: str | None = None):
        self.record_path = os.path.abspath(record_path)
        self.anchor_dir = (anchor_dir
                           or os.environ.get("CEN_ANCHOR_DIR")
                           or os.path.join(os.path.expanduser("~"),
                                           ".cen-anchors"))
        h = hashlib.sha256(self.record_path.encode()).hexdigest()[:16]
        self.path = os.path.join(self.anchor_dir, f"{h}.anchor")

    # -- lifecycle ---------------------------------------------------------
    def ensure(self) -> bytes:
        """Create the anchor (fresh key, empty mark) and return it.

        Called ONLY when the record file does not exist.  If a prior
        anchor remains at this path it is REPLACED with a fresh key:
        the prior record is gone (deleted by the operator's own hand —
        an attacker who could delete it needed no anchor trick), so a
        fresh chain starts.  The fail-closed direction is the other
        one: an EXISTING file whose anchor is absent refuses to open
        (see load()); that is where truncation-laundering lived (B2).
        Consequence, recorded: deleting file+anchor together destroys
        the record — same-namespace authority over BOTH artifacts is
        outside what an in-process anchor can bound; the residual risk
        section states this."""
        os.makedirs(self.anchor_dir, mode=0o700, exist_ok=True)
        key = secrets.token_bytes(32)
        self._write(key, 0, "0" * 64)
        return key

    def load(self) -> dict:
        """Read and validate the anchor.  ANY failure is AnchorError:
        absent, unreadable, wrong version, wrong record, torn content,
        or a mark whose seal does not verify under its own key.
        Fail-closed throughout — there is no trusted-file branch."""
        try:
            with open(self.path, "rb") as fh:
                raw = fh.read()
        except FileNotFoundError:
            raise AnchorError(
                f"integrity anchor {self.path} for record "
                f"{self.record_path} is ABSENT — refusing to open the "
                f"record (C9 fail-closed; an anchor is created only "
                f"with a brand-new record)") from None
        except OSError as e:
            raise AnchorError(
                f"integrity anchor {self.path} unreadable ({e}) — "
                f"refusing to open (C9 fail-closed)") from None
        try:
            a = json.loads(raw)
            key = bytes.fromhex(a["key_hex"])
            cnt = a["count"]
            hh = a["head_hash"]
            ver = a["version"]
            rp = a["record_path"]
            seal = a["mark_mac"]
        except (ValueError, KeyError, TypeError) as e:
            raise AnchorError(
                f"integrity anchor {self.path} is CORRUPT ({e}) — "
                f"refusing to open (C9 fail-closed)") from None
        if ver != 2 or not isinstance(cnt, int) or cnt < 0 \
                or not isinstance(hh, str) or len(hh) != 64 \
                or rp != self.record_path or len(key) < 32:
            raise AnchorError(
                f"integrity anchor {self.path} failed validation — "
                f"refusing to open (C9 fail-closed)")
        if not hmac.compare_digest(self._seal(key, cnt, hh), seal):
            raise AnchorError(
                f"integrity anchor {self.path}: the high-water mark's "
                f"seal does not verify — the anchor was FORGED or "
                f"rolled back; refusing to open (C9 fail-closed)")
        return {"key": key, "count": cnt, "head_hash": hh}

    def commit(self, key: bytes, count: int, head_hash: str) -> None:
        """Advance the high-water mark (called only by DurableRecord,
        after the record line is fsync'd).  Monotonic by construction:
        the caller only ever appends."""
        self._write(key, count, head_hash)

    @staticmethod
    def _seal(key: bytes, count: int, head_hash: str) -> str:
        return hmac.new(key, f"{count}|{head_hash}".encode(),
                        hashlib.sha256).hexdigest()

    def _write(self, key: bytes, count: int, head_hash: str) -> None:
        obj = {
            "version": 2,
            "record_path": self.record_path,
            "key_hex": key.hex(),
            "count": count,
            "head_hash": head_hash,
            "mark_mac": self._seal(key, count, head_hash),
        }
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, sort_keys=True))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, self.path)
        os.chmod(self.path, 0o600)
        dfd = os.open(self.anchor_dir, os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)


class DurableRecord:
    """The append-only, hash-chained decision log (C9).  It lives in its
    own FILE (default outside agent/ — pass a path), never inside a
    transcript, context window, or anything a summarizer rewrites; the
    harness's DMN-facing context holds no reference to it.  Every append
    re-verifies the tail; open() re-verifies the whole chain.

    Root of trust (v2 — replaces the in-directory `.head` sidecar): a
    `RecordAnchor` holding (i) the SECRET HMAC key the chain is keyed
    with and (ii) a high-water mark (count, head_hash), stored OUTSIDE
    this record's mutable namespace.  The v1 `.head` sidecar sat BESIDE
    the file it guarded, so deleting or rolling it back laundered
    truncation (review B2) and the unkeyed sha256 chain could be
    recomputed by any rewriter (review B3).  Both are closed by the
    anchor's design:

    * ABSENCE IS FAIL-CLOSED — a record file whose anchor is missing
      (or unreadable, or corrupt) REFUSES TO OPEN.  It is never
      "trusted" and the anchor is never re-derived from the file.
    * The chain is KEYED (HMAC-SHA256 under the anchor's key), so
      rewriting history and recomputing hashes reopens DIRTY unless the
      rewriter holds the anchor secret — which never enters the record's
      directory, its file content, or any log.
    * The high-water mark: the anchor's count may lag the file (the
      crash window between the record fsync and the anchor commit) only
      when the anchor's head_hash still authenticates the file's prefix
      at that count; it may never EXCEED the file, and an anchor head
      that no longer matches the file at the anchor's count is a
      rewrite, not a crash window.

    RESIDUAL RISK (recorded, NOT claimed closed — see RecordAnchor):
    an attacker who runs as the same OS user, or who has captured an
    old copy of the anchor file itself, can read the secret / roll the
    anchor back and defeat the high-water mark.  That requires reaching
    OUTSIDE the store's namespace; nothing in-process closes it."""

    def __init__(self, path: str, token: WriterToken,
                 anchor_dir: str | None = None):
        self.path = path
        self.anchor = RecordAnchor(path, anchor_dir)
        self._token = token
        self._key: bytes | None = None
        self._head_hash = "0" * 64
        self._seq = 0
        self._turns: set[int] = set()
        self._by_id: dict[str, DecisionRecord] = {}
        if os.path.exists(path):
            # FAIL-CLOSED: an existing record opens only against its
            # anchor.  No anchor -> AnchorError (a ChainError): the
            # record is NEVER trusted on the anchor's absence, and the
            # anchor is never re-derived from the file (review B2).
            a = self.anchor.load()
            self._key = a["key"]
            self._load()
            self._reconcile_anchor(a)
        else:
            self._key = self.anchor.ensure()
            # a brand-new record: the chain starts empty; the anchor's
            # empty mark was committed by ensure()

    # -- sole writer ----------------------------------------------------
    def _check_writer(self, token: WriterToken) -> None:
        if token is not self._token:
            raise SoleWriterError(
                f"record at {self.path} is owned by writer "
                f"'{self._token.writer_id}'; "
                f"'{token.writer_id}' is not the sole writer (P3)")

    # -- the root-of-trust anchor -----------------------------------------
    def _reconcile_anchor(self, a: dict) -> None:
        """Reconcile the anchor's sealed high-water mark with the
        chain-verified file.  anchor.count == file count and the head
        hashes match: clean.  anchor.count > file count: decisions were
        DROPPED/truncated — refuse.  anchor.count < file count: only
        acceptable if it is the crash window between the record fsync
        and the anchor commit, which requires the file's line at
        anchor.count to be exactly the anchor's head (the prefix was
        already committed); anything else is a rewrite.  The anchor is
        then brought up to date — an APPEND the anchor did not see,
        never a re-derivation of a rolled-back mark."""
        cnt, hh = a["count"], a["head_hash"]
        if cnt > self._seq:
            raise ChainError(
                f"integrity anchor says {cnt} decisions but the file "
                f"holds {self._seq} — decisions were DROPPED (C9)")
        if cnt == self._seq:
            if hh != self._head_hash:
                raise ChainError(
                    f"integrity anchor head {hh[:12]}.. != file head "
                    f"{self._head_hash[:12]}.. at the same count "
                    f"{cnt} — the file was REWRITTEN (C9)")
            return
        # cnt < self._seq: the crash window.  The committed prefix must
        # still be where the anchor left it.
        prefix_head = self._hash_at(cnt)
        if prefix_head is None or prefix_head != hh:
            raise ChainError(
                f"integrity anchor remembers head {hh[:12]}.. at count "
                f"{cnt}, but the file's chain there is "
                f"{(prefix_head or '??')[:12]}.. — the committed prefix "
                f"was REWRITTEN, not merely extended (C9)")
        self.anchor.commit(self._key, self._seq, self._head_hash)

    def _hash_at(self, count: int) -> str | None:
        """The chain hash of the count-th line, or None if the file has
        fewer lines (the chain walk already verified every line)."""
        if count == 0:
            return "0" * 64
        if count > self._seq:
            return None
        with open(self.path, "r", encoding="utf-8") as fh:
            for k, line in enumerate(fh, start=1):
                if k == count:
                    return json.loads(line.strip())["hash"]
        return None

    # -- load / verify ----------------------------------------------------
    def _load(self) -> None:
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except ValueError as e:
                        raise ChainError(
                            f"torn/corrupt line in {self.path} "
                            f"({e}) — refusing (C9 fail-closed)") from None
                    self._ingest(d, verify_from_disk=True)
        except ChainError:
            raise
        self.verify()

    def _ingest(self, d: dict, verify_from_disk: bool) -> DecisionRecord:
        rec = DecisionRecord(
            seq=d["seq"], turn=d["turn"], decision_id=d["decision_id"],
            kind=d["kind"], content=d["content"], reason=d["reason"],
            ts=d["ts"], prev_hash=d["prev_hash"], hash=d["hash"])
        if verify_from_disk:
            expect = DecisionRecord._digest(
                rec.prev_hash, rec.seq, rec.turn, rec.decision_id,
                rec.kind, rec.content, rec.reason, rec.ts,
                key=self._key)
            if expect != rec.hash:
                raise ChainError(
                    f"seq {rec.seq}: keyed-hash mismatch — record was "
                    f"REWRITTEN (or the chain key is not the anchor's)")
            if rec.seq != self._seq + 1:
                raise ChainError(
                    f"seq {rec.seq} after {self._seq}: not contiguous — "
                    f"a decision was DROPPED")
            if rec.prev_hash != self._head_hash:
                raise ChainError(
                    f"seq {rec.seq}: chain does not link to the head")
        if rec.decision_id in self._by_id:
            raise ChainError(f"duplicate decision_id {rec.decision_id}")
        self._seq = rec.seq
        self._head_hash = rec.hash
        self._turns.add(rec.turn)
        self._by_id[rec.decision_id] = rec
        return rec

    def verify(self) -> None:
        """Re-verify the whole chain from the file (C9's test surface),
        under the ANCHOR KEY.  An unkeyed recompute cannot produce a
        valid chain (review B3)."""
        if self._key is None:
            raise ChainError("cannot verify without the anchor key")
        head, seq = "0" * 64, 0
        with open(self.path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                if d["seq"] != seq + 1 or d["prev_hash"] != head:
                    raise ChainError(f"chain broken at seq {d['seq']}")
                if DecisionRecord._digest(
                        d["prev_hash"], d["seq"], d["turn"],
                        d["decision_id"], d["kind"], d["content"],
                        d["reason"], d["ts"], key=self._key) != d["hash"]:
                    raise ChainError(f"hash mismatch at seq {d['seq']}")
                head, seq = d["hash"], d["seq"]
        if seq != self._seq:
            raise ChainError("file shorter than the loaded chain")

    # -- append -----------------------------------------------------------
    def append_decision(self, token: WriterToken, turn: int,
                        decision_id: str, kind: str, content: str,
                        reason: str) -> DecisionRecord:
        """The ONLY write.  `reason` is required and non-empty (C9:
        decisions and their reasons are the unrecoverable class)."""
        self._check_writer(token)
        if not reason or not reason.strip():
            raise ValueError("a decision without a reason is not a "
                             "durable record (C9)")
        rec = DecisionRecord(
            seq=self._seq + 1, turn=turn, decision_id=decision_id,
            kind=kind, content=content, reason=reason,
            ts=time.strftime("%Y-%m-%dT%H:%M:%S"),
            prev_hash=self._head_hash, hash="")
        rec = DecisionRecord(
            seq=rec.seq, turn=rec.turn, decision_id=rec.decision_id,
            kind=rec.kind, content=rec.content, reason=rec.reason,
            ts=rec.ts, prev_hash=rec.prev_hash,
            hash=DecisionRecord._digest(
                rec.prev_hash, rec.seq, rec.turn, rec.decision_id,
                rec.kind, rec.content, rec.reason, rec.ts,
                key=self._key))
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(rec.to_line() + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        self._seq = rec.seq
        self._head_hash = rec.hash
        self._turns.add(rec.turn)
        self._by_id[rec.decision_id] = rec
        # C9 ordering: line fsync -> anchor commit fsync.  A crash in
        # the window leaves the anchor BEHIND, which reconciliation
        # accepts only for a genuine APPEND (the committed prefix must
        # still hash to the anchor's sealed head).
        self.anchor.commit(self._key, self._seq, self._head_hash)
        return rec

    # -- queries ------------------------------------------------------------
    @property
    def head_hash(self) -> str:
        return self._head_hash

    @property
    def count(self) -> int:
        return self._seq

    def has_turn(self, turn: int) -> bool:
        return turn in self._turns

    def get(self, decision_id: str) -> DecisionRecord | None:
        return self._by_id.get(decision_id)


# ==========================================================================
# The engine port — the interface the DECIDED substrate (C10:
# datalog-dafsa) exposes.  The verified C surface (dl-binding-brief.md,
# measured 1.6 us/lookup, 225x headroom vs a <=10 us/step budget) is:
#   dl_open/_ro/_close, dl_lookup(rel, cols, arity), dl_query*,
#   dl_txn_begin/commit/rollback, dl_cas_revision, dl_add_fact,
#   dl_rev_get, dl_iter_*  — one writer (LOCK), readers never block.
# The Python BINDING is being built in a parallel task; design against
# this port, do not build or vendor the engine.  StubDatalogEngine is
# the stand-in: ground facts only, lookup = 1 derivation, cut depth 0.
# ==========================================================================

class DatalogError(RuntimeError):
    """Errors must SURFACE (DL_E_LOCKED / DL_E_CONFLICT class), never
    silently return 0/False — the binding brief's explicit requirement."""


class DatalogEngine(Protocol):
    """The minimal surface the CEN uses.  A real implementation wraps
    the datalog-dafsa binding when it lands; the CEN's logic does not
    change."""

    def declare(self, relation: str, arity: int) -> None: ...
    def lookup(self, relation: str, args: Sequence) -> bool:
        """Ground-fact membership (dl_lookup)."""
    def contradicted(self, relation: str, args: Sequence) -> bool:
        """Explicit `refutes` fact holds (Datalog has no negation:
        contradiction is a POSITIVE relation, not negation-as-failure)."""
    def check_cost(self, relation: str, args: Sequence) -> tuple[int, int]:
        """C11's cost surface, in the model's units: (derivations,
        cut_depth) for checking the ground atom `relation(args...)` —
        never tokens, never microseconds.  A ground-fact membership test
        costs (1, 0): one distinct stored fact is consulted and a
        membership test has no proof tree.  When rules exist this is
        where the engine reports reuse-accounted derivation counts (the
        CIRCUIT: each derivable fact counted once, however many ways it
        is derived) and the proof's cut depth."""
    def iter_facts(self, relation: str,
                   str_cols: Sequence[int] = ()) -> list[tuple]:
        """The retrieval layer's enumeration seat (item 'retrieval'):
        every stored ground fact of `relation`, as (relation, *args)
        tuples with the columns named in `str_cols` decoded back to
        strings (the real engine interns string columns to u32 symbol
        ids; the stub stores them as-is).  ENUMERATION, NOT QUERY: it
        lists what exists so the retrieval seat can price and the
        external selector can plan; it is called ONCE PER TURN from the
        retrieval seat (campaign-priced), never from the per-step read
        path.  Engines without an enumeration surface raise
        DatalogError (errors surface; a retrieval layer that silently
        saw an empty store would price zero and thin the self for no
        reason)."""
    def txn_commit(self, token: WriterToken,
                   facts: Sequence[tuple]) -> int:
        """One atomic txn (dl_txn_begin/commit); returns the new store
        revision.  Sole-writer: any token other than the opener's is
        rejected (LOCK semantics)."""
    def revision(self) -> int: ...


class StubDatalogEngine:
    """In-memory stand-in for the datalog-dafsa binding (C10).  Ground
    facts only: no rules, no recursion, so every check costs 1
    derivation at cut depth 0.  That is the HONEST cost for a ground
    membership test — one distinct stored fact is consulted and there is
    no proof tree — NOT a placeholder awaiting the binding: the binding
    landed and the number is the same because a membership test has the
    same cost behind either engine.  Reuse accounting (circuit vs
    formula) and non-zero cut depths become live only when rules exist;
    `check_cost` reports them, and with no rules circuit == formula == 1
    and depth == 0.  Semantics used by the CEN:
      fact present                      -> VERIFIED (provenance: the fact)
      `refutes` fact present            -> REFUTED
      predicate undeclared / no terms   -> UNCHECKABLE('unknown_predicate'
                                            / 'no_rules') -> checking debt

    Serializable for the C8 resume path: dump()/load() carry declared
    relations and facts; the writer-lock identity resets (a resumed CEN
    re-owns the store through its own token, matching the real engine's
    lock-on-open semantics)."""

    def __init__(self):
        self._declared: dict[str, int] = {}
        self._facts: set[tuple] = set()
        self._rev = 0
        self._token: WriterToken | None = None

    def _own(self, token: WriterToken) -> None:
        if self._token is None:
            self._token = token
        elif token is not self._token:
            raise SoleWriterError(
                f"store is locked by writer '{self._token.writer_id}' "
                f"(P3 sole writer; DL_E_LOCKED class)")

    def seed(self, facts: Sequence[tuple]) -> None:
        """Bulk-load initial facts WITHOUT a txn — the loader/
        preprocessor layer's job in datalog-dafsa (dlp); does not take
        the write lock (initial data, not a writer's commit)."""
        self._facts.update(tuple(f) for f in facts)

    def dump(self) -> dict:
        return {"declared": dict(self._declared),
                "facts": sorted(self._facts), "rev": self._rev}

    def load(self, state: dict) -> None:
        self._declared = dict(state["declared"])
        self._facts = set(tuple(f) for f in state["facts"])
        self._rev = state["rev"]

    def declare(self, relation: str, arity: int) -> None:
        """`arity` counts the ARGUMENTS (the relation name is not part
        of it); facts are stored as (relation, *args)."""
        self._declared[relation] = arity

    def lookup(self, relation: str, args: Sequence) -> bool:
        if relation not in self._declared:
            raise DatalogError(
                f"relation '{relation}' undeclared — errors surface, "
                f"they do not return False")
        if len(args) != self._declared[relation]:
            raise DatalogError(
                f"relation '{relation}' arity {self._declared[relation]}, "
                f"got {len(args)} args")
        return (relation, *args) in self._facts

    def contradicted(self, relation: str, args: Sequence) -> bool:
        key = f"{relation}({','.join(map(str, args))})"
        return ("refutes", key) in self._facts

    def check_cost(self, relation: str, args: Sequence) -> tuple[int, int]:
        """Ground membership: (1, 0) — one distinct stored fact is
        consulted and a membership test has no proof tree.  Reuse
        accounting is unexercised with no rules (circuit == formula == 1,
        depth == 0).  The same declaration/arity gate as `lookup` so
        errors surface here too."""
        if relation not in self._declared:
            raise DatalogError(
                f"relation '{relation}' undeclared — errors surface, "
                f"they do not return False")
        if len(args) != self._declared[relation]:
            raise DatalogError(
                f"relation '{relation}' arity {self._declared[relation]}, "
                f"got {len(args)} args")
        return (1, 0)

    def iter_facts(self, relation: str,
                   str_cols: Sequence[int] = ()) -> list[tuple]:
        """The retrieval enumeration seat: every stored fact of
        `relation` as (relation, *args).  Facts are stored natively
        here (no interning), so `str_cols` is accepted for interface
        parity and ignored.  Sorted for determinism (the selector's
        tie-break needs a canonical order).  The sort is the RAW one
        wherever the relation's key columns are one comparable type —
        every pre-codec relation, byte-identically — and falls back to
        a STRING-keyed sort only when the relation carries MIXED key
        types (the codec layer's supersession entries are string keys
        '<turn>c<window>' beside the int turns; memory_codec_seat),
        where the raw sort would raise TypeError on the first mixed
        relation."""
        if relation not in self._declared:
            raise DatalogError(
                f"relation '{relation}' undeclared — errors surface, "
                f"they do not return False")
        rows = [(relation, *f[1:]) for f in self._facts
                if f[0] == relation]
        try:
            return sorted(rows)
        except TypeError:
            return sorted(rows,
                          key=lambda r: tuple(str(a) for a in r[1:]))

    def txn_commit(self, token: WriterToken,
                   facts: Sequence[tuple]) -> int:
        self._own(token)
        for f in facts:
            rel = f[0]
            if rel not in self._declared:
                raise DatalogError(f"txn writes undeclared '{rel}'")
        self._facts.update(facts)
        self._rev += 1
        return self._rev

    def revision(self) -> int:
        return self._rev


# ==========================================================================
# C5 — the class discriminator.  Three collapse classes, each with a
# distinguishing signal and a DIFFERENT fix family; the fix must match
# the class.  The two cheap signals (measured on the evaluation context):
#   (i)  switch_accurate — is the loop's alarm/switch estimate accurate
#        (model side: c is ACCURATE during the base collapse)?
#   (ii) evaluator_blind — is the evaluator blind at the attractor (a
#        region the assessment cannot reach where the outcome is decided;
#        model side: V == 0 exactly on the rescue arc)?
# A vs C needs ONE more cheap comparison: the same signals measured on
# the OUTCOME context (the transfer gap — exp16's hypothesis, PENDING).
# ==========================================================================

class CollapseClass(Enum):
    A_SOUND_UNSTABLE = ("A", "sound evaluator + unstable loop",
                        "FIX: feedback structure (the floor — cheap, "
                        "zero observation)")
    B_BLIND = ("B", "misjudging / blind evaluator",
               "FIX: evidence-widening (close the blind boundary)")
    C_NON_REPRESENTATIVE = ("C", "sound but non-representative evaluator",
                            "FIX: context/transfer (re-anchor the proxy)")
    A_OR_C_UNDECIDED = ("A|C", "sound evaluator in-context; transfer gap "
                         "unmeasured (PENDING exp16)", "no fix chosen")


@dataclass(frozen=True)
class DiscriminatorSignals:
    switch_accurate: bool | None = None
    evaluator_blind: bool | None = None
    transfer_gap: bool | None = None   # outcome-context divergence; the
                                       # A-vs-C tiebreak, PENDING exp16


class ClassDiscriminator(Protocol):
    def classify(self, s: DiscriminatorSignals) -> CollapseClass: ...


class StubClassDiscriminator:
    """The rule table straight from C5 — this IS the stub; what is
    pending is not the table but the in-vivo SUPPLY of the signals
    (blind boundary: exp15; transfer gap: exp16)."""

    def classify(self, s: DiscriminatorSignals) -> CollapseClass:
        if s.evaluator_blind is None or s.switch_accurate is None:
            return CollapseClass.A_OR_C_UNDECIDED
        if s.evaluator_blind:
            return CollapseClass.B_BLIND
        # sound in-context: A unless the proxy diverges across contexts
        if s.transfer_gap is None:
            return CollapseClass.A_OR_C_UNDECIDED
        if s.transfer_gap:
            return CollapseClass.C_NON_REPRESENTATIVE
        return CollapseClass.A_SOUND_UNSTABLE


# ==========================================================================
# C4/C12 — the boundary objects and the evidence-widening port.  exp15
# (running) must output B_failure = the (lever, T) -> V-margin matrix
# with the invisible set (|margin| <= atol_tau) marked; the widening
# component must output B_fix = the set whose margin moves beyond
# atol_tau once assessment is widened.  THE TEST IS B_failure == B_fix:
#   exact closure | partial (B_fix strictly contains B_failure) |
#   superficial (B_fix does not contain B_failure).
# The component itself is a STUB (PENDING exp15 + the BCT): interface
# only, no invented behaviour.
# ==========================================================================

@dataclass(frozen=True)
class BoundarySpec:
    """The shared boundary object (handoff-selfreg-blindlever-ctx): the
    set of (lever_id, horizon_T) the assessment cannot reach, plus the
    region description (e.g. rollout reach '{t > t_a + T}')."""
    invisible: frozenset[tuple[str, float]]
    region: str = ""

    @classmethod
    def empty(cls, region: str = "") -> "BoundarySpec":
        return cls(frozenset(), region)


class BoundaryCorrespondence(Enum):
    EXACT_CLOSURE = "exact: levers invisible before become visible; " \
                    "visible before stay visible"
    PARTIAL = "partial: B_fix strictly contains B_failure"
    SUPERFICIAL = "superficial: B_fix does not contain B_failure"


def boundary_correspondence(b_failure: BoundarySpec,
                            b_fix: BoundarySpec) -> tuple[BoundaryCorrespondence, str]:
    """The Boundary Correspondence Test as a runnable comparison (the
    measurement is pending; the comparison is not).  Returns (verdict,
    human-readable diff)."""
    f, x = set(b_failure.invisible), set(b_fix.invisible)
    if f == x:
        return BoundaryCorrespondence.EXACT_CLOSURE, "B_failure == B_fix"
    if f < x:
        extra = sorted(x - f)
        return BoundaryCorrespondence.PARTIAL, \
            f"B_fix closes MORE than the failure uses: {extra}"
    missing = sorted(f - x)
    return BoundaryCorrespondence.SUPERFICIAL, \
        f"B_fix does NOT close the exploitable boundary: {missing}"


class EvidenceWidener(Protocol):
    """The assessment / evidence-widening component (queue step 4)."""

    def boundary_fix(self) -> BoundarySpec:
        """B_fix: the (lever, T) whose V-margin moves beyond atol_tau
        once the assessment is widened, plus the region now covered."""


class PendingEvidenceWidener:
    """STUB — PENDING.  Its design depends on exp15's B_failure output
    and the Boundary Correspondence Test (handoff-selfreg-blindlever-ctx,
    handoff-selfreg-mechanism-constraints C4).  Interface only; no
    behaviour is invented here."""

    PENDING = ("exp15 (the blind-lever positive control, RUNNING in "
               "~/thing/dpdr) must first output B_failure; the widening "
               "component is then designed against it and checked by "
               "boundary_correspondence(B_failure, B_fix)")

    def boundary_fix(self) -> BoundarySpec:
        raise NotImplementedError(
            f"evidence-widening is PENDING: {self.PENDING}")


# ==========================================================================
# C3/C12 — the self-modifiable lever gate.  The controller knob set is
# EXCLUDED: the evaluator cannot see the controller (all 240 controller
# margins exactly 0.0; the rollout's attention carries no k_pull/c_mon/
# G_trig terms), so admitting it BEFORE the evidence channel is widened
# gives a blind chooser.  Admitting it requires a widener whose B_fix
# passed the BCT against B_failure — enforced structurally in CEN.
# ==========================================================================

#: controller knobs, named from SNConstants + AgentConfig (the measured
#: regulator constants: floor/k_pull/G_trig/trig_w are the load-bearing
#: written-down values; c_mon/t_engage/block_* are deployment switches)
CONTROLLER_LEVERS = frozenset({
    "sn.floor", "sn.k_pull", "sn.G_trig", "sn.trig_w", "sn.lam_a_max",
    "sn.lam_S", "sn.lam_g", "sn.quasi_steady_a",
    "cfg.c_mon", "cfg.t_engage", "cfg.block_a_thresh", "cfg.block_on",
    "cfg.regulator_on", "cfg.edge_on", "cfg.n_substeps",
})


class LeverRejected(RuntimeError):
    """A proposal was refused at the gate (recorded as a DECISION with
    its reason — C9)."""


class AdmissibleLevers:
    """The admission gate.  DEFAULT: NOTHING is admissible — no lever
    has passed any test.  The controller set is excluded by construction
    until `open_controller` succeeds, which requires a widener that
    passed the Boundary Correspondence Test (C12's ORDER: widen the
    evidence channel FIRST, then admit)."""

    def __init__(self, admissible: Iterable[str] = (),
                 controller_enabled: bool = False):
        self._admissible = set(admissible)
        self._controller_enabled = controller_enabled

    @property
    def controller_enabled(self) -> bool:
        return self._controller_enabled

    def is_admissible(self, lever_id: str) -> bool:
        if lever_id in CONTROLLER_LEVERS:
            return self._controller_enabled
        return lever_id in self._admissible

    @staticmethod
    def open_controller(b_failure: BoundarySpec, widener: EvidenceWidener
                        ) -> "AdmissibleLevers":
        """The ONLY path to a controller-admitting lever set (C12).
        Runs the BCT live; exact closure is required — partial or
        superficial correspondence keeps the controller excluded."""
        b_fix = widener.boundary_fix()
        verdict, _ = boundary_correspondence(b_failure, b_fix)
        if verdict is not BoundaryCorrespondence.EXACT_CLOSURE:
            raise LeverRejected(
                f"controller levers stay EXCLUDED (C3/C12): the "
                f"evidence channel does not close the boundary — "
                f"{verdict.value}")
        return AdmissibleLevers(controller_enabled=True)


# ==========================================================================
# The CEN — sole writer, one txn per turn; it CHECKS, it REGISTERS and it
# EMITS OUTWARD, and it never actuates: the plant has no edge from here
# (see TurnRecord's corrected actuation note), and the tool-call layer's
# effects land on the harness's own world.
# ==========================================================================

class CEN:
    """The executive component boundary (P3): the SOLE writer to the
    store and the durable record; the DMN is a pure client whose only
    durable product is assertions-to-be-checked (they flow through the
    currency, never written directly); the SN never touches this side.
    Per DMN turn, exactly one txn: (i) checked relations (assertion +
    verdict + provenance), (ii) persist-as-is relations (the DMN's
    self_content, byte-for-byte), in that order, atomically — and the
    DECISIONS are appended to the DurableRecord BEFORE the commit, so a
    crash may orphan a decision (recoverable) but never commits an
    action whose reason is gone (the unrecoverable class, C9).

    IT ALSO EMITS (the tool-call layer, `agent/actions.py`): the turn's
    registered `complete(tX)` intents leave on `TurnRecord.talking` —
    the outward stream's seat, and the ONLY thing here that leaves the
    agent — while the PLANT stays untouched (no actuator authority:
    see TurnRecord's corrected note).  The action seat is None by
    default, so the pre-tool-call behaviour is unchanged."""

    def __init__(self, engine: DatalogEngine, record: DurableRecord,
                 budget: CostBudget | None = None,
                 levers: AdmissibleLevers | None = None,
                 widener: EvidenceWidener | None = None,
                 token: WriterToken | None = None,
                 retrieval=None, commitments=None, actions=None,
                 rules=None, encoding_gate=None):
        self.token = token if token is not None else WriterToken.issue("cen")
        self.engine = engine
        self.record = record
        self.budget = budget or CostBudget()
        self.levers = levers or AdmissibleLevers()
        self.widener = widener
        self.ledger = DerivationLedger()
        # the retrieval seat (item 'retrieval'; retrieval.RetrievalSeat,
        #  typed loosely to keep cen.py import-free of the layer it
        #  hosts — the seat is INJECTED, never constructed here, so the
        #  selector stays EXTERNALLY OWNED: R5, the self must not choose
        #  its own evidence).  None (the default) = the seat is off and
        #  retrieval is not charged — the pre-retrieval behaviour,
        #  unchanged.
        self.retrieval = retrieval
        # the COMMITMENTS seat (the self plan, decision 4's grammar; a
        # CommitmentTracker from agent/selfmodel.py, typed loosely for
        # the same reason `retrieval` is: the CEN hosts the channel but
        # never constructs the tracker, and the tracker itself is RAM
        # state carried by the C8 checkpoint).  None (the default) = the
        # channel is inert and the batch's `commitments` (always ())
        # changes nothing — the pre-self behaviour, byte-identical.
        self.commitments = commitments
        # the ACTIONS seat (the tool-call layer; an ActionTracker from
        # agent/actions.py, typed loosely for the same reason: the CEN
        # hosts the outward channel and never constructs the seat, never
        # checks its payload and never executes it — the WORLD does).
        # None (the default) = the channel is inert, `batch.actions` is
        # (by the caller's construction) empty, `TurnRecord.talking`
        # stays None and the pre-tool-call behaviour is byte-identical.
        self.actions = actions
        # the RULES seat (paper-3 prerequisite 1: the DERIVE path).  An
        # entail.Theory, typed loosely for the same reason `retrieval`
        # and `actions` are: the CEN hosts the seat, never constructs
        # it.  None (the default) = no theory attached and _check_one's
        # behaviour is BYTE-IDENTICAL to the pre-entailment checker —
        # which is what keeps every default run (including the R10
        # flood's ungrounded orphaned claims, which must stay debt) on
        # the fact-lookup semantics.  See entail.py's module note.
        self.rules = rules
        # THE ENCODING GATE (item 'encoding'; salience.EncodingGate,
        # typed loosely for the same reason `retrieval` is: the CEN
        # hosts the seat, NEVER constructs it — the POLICY is a frozen
        # designer object injected with the gate, so the mechanism
        # cannot set its own novelty threshold (R5 applied to the
        # encoder: a self-owned threshold would encode only what it
        # already thinks about).  None (the default) = no gate and the
        # write class (ii) lands in the consolidating tier exactly as
        # before, byte-identical.  THE GATE IS THE MECHANISM OF
        # RECORD: a below-threshold emission is TIERED to the policy's
        # named lower relation, never deleted (C19) — and never
        # re-weighted, because a binding budget launders a soft weight
        # (block 0.0481 vs down-weighted 0.7532 vs naive 0.7784,
        # model-MEASURED; salience.py's module note).
        self.encoding_gate = encoding_gate
        # the FIFO queue of per-turn batches (P3: one txn per turn,
        # FIFO by turn number).  The queue is not just plumbing: its
        # depth + debt IS the D-analogue (P2: problems 2+3 merge).
        self.queue: list[AssertionBatch] = []
        self._turn = 0
        # relations the CEN owns (declared on the engine at init)
        for rel, ar in (("asserts", 3), ("verdict_of", 3),
                        ("self_content", 2), ("refutes", 1)):
            try:
                engine.declare(rel, ar)
            except Exception:
                pass   # already declared (shared stub in tests)
        # the encoding gate's LOWER TIER (item 'encoding'): declared
        # iff a gate is attached, and named BY THE POLICY (the designer
        # owns the tier name; the gate's own validation refused a name
        # equal to the consolidating tier).  Declared here so the
        # tiered write in check_turn finds a declared relation on both
        # engines; absent (never declared) when no gate is attached —
        # the default path declares nothing new.
        if self.encoding_gate is not None:
            try:
                engine.declare(self.encoding_gate.policy.low_tier, 2)
            except Exception:
                pass   # already declared (resume / shared stub)

    # -- the real backlog signal (P2) -------------------------------------
    def backlog_outstanding(self) -> int:
        """Assertions awaiting or resisting verification: queued (not yet
        checked this turn) + UNCHECKABLE debt.  Verified/refuted leave.
        This — not the plant's switch state — is what Stage 2's D reads
        once the coupling is wired (see Stage2Config.couple_backlog)."""
        debt = len(self.ledger.debt_assertions)
        return sum(len(b.assertions) for b in self.queue) + debt

    # -- the encoding gate's own read (item 'encoding') -------------------
    def _iter_tier(self, relation: str) -> list[tuple]:
        """Every stored fact of `relation`, through the engine's own
        ENUMERATION seat (iter_facts — the same surface the retrieval
        layer uses, never a new one).  Used once per gated turn for the
        reuse signal's duplicate join; raises DatalogError on an engine
        without the surface (errors surface — a gate that silently saw
        an empty tier would read reuse 0.0 for a reason it cannot
        name)."""
        str_cols = (1,) if relation == "self_content" else ()
        return self.engine.iter_facts(relation, str_cols)

    # -- DMN is a pure client: submit only enqueues ------------------------
    def submit_batch(self, batch: AssertionBatch) -> None:
        self.queue.append(batch)   # FIFO by turn number is enforced by
                                   # check_turn (the caller drives turns)

    # -- the lever gate (C3/C12) -------------------------------------------
    def _gate_proposals(self, batch: AssertionBatch) -> tuple[LeverProposal, ...]:
        rejected = []
        for pr in batch.proposals:
            if not self.levers.is_admissible(pr.lever_id):
                why = ("controller lever — evaluator cannot see the "
                       "controller (C3); evidence channel must be "
                       "widened first (C12)" if pr.lever_id in
                       CONTROLLER_LEVERS else
                       "not in the admitted lever set (default: nothing "
                       "is admissible — no lever has passed a test)")
                self.record.append_decision(
                    self.token, batch.turn,
                    decision_id=f"reject:{batch.turn}:{pr.lever_id}",
                    kind="reject_proposal",
                    content=f"{pr.lever_id} -> {pr.new_value!r}",
                    reason=why)
                rejected.append(pr)
        return tuple(rejected)

    # -- one turn = one txn --------------------------------------------------
    def check_turn(self, batch: AssertionBatch) -> TurnRecord:
        """Check the batch, write the two classes atomically, return the
        verdicts (the DMN's next-turn context — the repair path).  The
        CEN does not actuate: nothing here touches the plant.  What
        leaves outward (when an ACTION seat is attached) is the TALKING
        emission — the turn's registered intents, which the WORLD
        applies and answers (see TurnRecord's corrected note)."""
        if batch.turn != self._turn + 1:
            raise ValueError(
                f"batch turn {batch.turn} != next turn {self._turn + 1} "
                f"(one txn per DMN turn, FIFO by turn number — P3)")
        self.ledger.begin_turn()
        rejected = self._gate_proposals(batch)
        # the retrieval charge is paid FIRST (item 'retrieval'): the
        # standing cost reconciles onto the per-turn gate by being paid
        # inside the same per-turn ledger, before any work assertion —
        # so as the store grows the work sees a shrinking remainder
        # (class (D) made per-turn; see retrieval.py's module note).
        retrieval_outcome = None
        if self.retrieval is not None:
            retrieval_outcome = self.retrieval.retrieve(
                engine=self.engine, ledger=self.ledger,
                budget=self.budget, turn=batch.turn)
        verdicts: list[Verdict] = []
        # THE COMMITMENTS CHANNEL (the self plan Q4): `expect(tX)` spans
        # are REGISTERED, never checked.  No engine write, no verdict, no
        # debt — expiry is an OBSERVABLE, never debt (a second arrival
        # term beside the plant's c would split the model's one variable;
        # see the module's coupling docstring in stage2_harness).  The
        # tracker scores the open set at the next consolidation BOUNDARY.
        if self.commitments is not None and batch.commitments:
            self.commitments.register(batch.turn, batch.commitments)
        # THE ACTIONS CHANNEL (the tool-call layer): `complete(tX)` spans
        # are REGISTERED as INTENTS and emitted on the turn's `talking`
        # seat — never checked (an intent is not a claim: checking
        # complete(t57) by looking up done(t57) at emission is the same
        # tautology class the commitments channel refuses), and NEVER
        # charged to the C11 ledger (derivations price REDUCTION;
        # expression is priced in outward bytes, on the harness's own
        # log-only talking ledger — the standing order forbids mixing the
        # two units).  The emission is built BY THE SEAT (one call site,
        # so registration and emission cannot drift) and the CEN stays
        # import-free of the layer it hosts — the `retrieval` precedent.
        talking = None
        if self.actions is not None:
            talking = self.actions.emission(batch)
        for a in batch.assertions:
            v = self._check_one(a)
            verdicts.append(v)
            if v.status is AssertionStatus.UNCHECKABLE \
                    and v.assertion_id not in self.ledger.debt_assertions:
                self.ledger.debt_assertions.append(v.assertion_id)
        result = BatchResult(
            verdicts=list(verdicts),
            derivations_total=self.ledger.spent_this_turn,
            cut_depth_max=self.ledger.max_cut_depth,
            rejected_proposals=rejected)
        # write class (i): checked relations.  Provenance is REQUIRED
        # (P2: the assertion-with-dependencies form is what constrains
        # the architecture); a verdict without provenance does not land.
        facts: list[tuple] = [("verdict_of", batch.turn, v.assertion_id,
                               v.status.value) for v in verdicts]
        facts += [("asserts", batch.turn, a.assertion_id, a.le_text)
                  for a in batch.assertions]
        # *** SELECTIVE ENCODING (item 'encoding') — THE GATE AT THE
        # *** WRITE.  Storage is automatic, encoding is selective: the
        # *** CEN-side salience function (existing signals ONLY: the
        # *** verdict stream, the commitment tracker's open targets,
        # *** the retrieval-hit counts — rule 8, the DMN is never the
        # *** sensor) scores the turn's self emission, the INJECTED
        # *** policy's threshold decides, and a below-threshold
        # *** emission lands in the policy's NAMED LOWER TIER instead
        # *** of the consolidating one.  THE BLOCK, NOT A REWEIGHT:
        # *** the measured trap (block 0.0481 vs down-weighted 0.7532
        # *** vs naive 0.7784 — a binding budget LAUNDERS a soft
        # *** weight) is why the gate is a tier decision and why the
        # *** salience's second use (seeding the entry's INITIAL
        # *** retrieval weight) is the subordinate channel, not the
        # *** mechanism.  C19: nothing is deleted or rewritten — the
        # *** denied emission is STORED in the lower tier (auditable,
        # *** recoverable by a later policy version), it just does not
        # *** consolidate.  The decision is appended to the durable
        # *** record with its reason (C9) BEFORE the commit, like
        # *** every other decision.
        gate_outcome = None
        if self.encoding_gate is not None:
            # the prior consolidated entries with their retrieval-hit
            # counts (the reuse signal's own source — the working
            # set, never a fresh engine enumeration on this path)
            epochs = getattr(self.retrieval, "epochs", None) \
                if self.retrieval is not None else None
            prior = []
            if epochs is not None:
                prior = [(str(f[1]), epochs.access_count(str(f[1])))
                         for f in self._iter_tier("self_content")]
            open_targets = []
            if self.commitments is not None:
                open_targets = [c.target for c in self.commitments.open
                                if c.target is not None]
            gate_outcome = self.encoding_gate.evaluate(
                turn=batch.turn, content=batch.self_content,
                verdicts=[v.status.value for v in verdicts],
                open_targets=open_targets, prior=prior)
            self.record.append_decision(
                self.token, batch.turn,
                decision_id=f"encode:{batch.turn}",
                kind="encode_decision",
                content=(f"tier={gate_outcome.tier} "
                         f"salience={gate_outcome.salience:.3f} "
                         f"(s={gate_outcome.scores.surprise:.3f},"
                         f"g={gate_outcome.scores.goal:.1f},"
                         f"r={gate_outcome.scores.reuse:.1f})"),
                reason=gate_outcome.reason)
            # the subordinate channel: the salience seeds the ENCODED
            # entry's initial retrieval weight (refused by the epoch
            # table for an already-accessed key — C20, never a
            # rewrite; a binding budget launders this, which is why it
            # is the second channel).
            if gate_outcome.admitted and gate_outcome.seed_weight \
                    and 0.0 < gate_outcome.initial_weight <= 1.0 \
                    and epochs is not None:
                try:
                    epochs.set_initial(str(batch.turn),
                                       gate_outcome.initial_weight)
                except ValueError:
                    pass   # already seeded/accessed this turn (resume)
        # write class (ii): persist-as-is, byte-for-byte, never edited
        # — into the tier the gate chose (the consolidating tier when
        # no gate is attached, exactly the pre-encoding behaviour).
        tier = ("self_content" if gate_outcome is None
                else gate_outcome.tier)
        facts.append((tier, batch.turn, batch.self_content))
        # C9 ordering: decisions BEFORE the commit
        dec_ids: list[str] = []
        if verdicts or rejected:
            d = self.record.append_decision(
                self.token, batch.turn,
                decision_id=f"commit:{batch.turn}", kind="commit",
                content=(f"{len(verdicts)} verdicts "
                         f"({sum(1 for v in verdicts if v.status is AssertionStatus.VERIFIED)}V/"
                         f"{sum(1 for v in verdicts if v.status is AssertionStatus.REFUTED)}R/"
                         f"{sum(1 for v in verdicts if v.status is AssertionStatus.UNCHECKABLE)}U), "
                         f"{len(rejected)} proposals rejected"),
                reason="one txn per DMN turn (P3): checked relations + "
                       "persist-as-is self content")
            dec_ids.append(d.decision_id)
        rev = self.engine.txn_commit(self.token, facts)
        self._turn = batch.turn
        self.queue = [b for b in self.queue if b.turn != batch.turn]
        result.backlog_outstanding = self.backlog_outstanding()
        return TurnRecord(turn=batch.turn, result=result,
                          decisions=tuple(dec_ids), txn_rev=rev,
                          ts=time.strftime("%Y-%m-%dT%H:%M:%S"),
                          retrieval=retrieval_outcome,
                          encoding=gate_outcome,
                          talking=talking)

    def _check_one(self, a: Assertion) -> Verdict:
        # C11: budget in the model's units.  The CEN ASKS the engine for
        # the cost of the check — DatalogEngine.check_cost -> (derivations,
        # cut_depth) — and charges what it reports, never a hardcoded
        # constant and never tokens.  An over-budget check (per-assertion
        # ceiling, depth ceiling, or per-turn total) is not run and
        # becomes debt (UNCHECKABLE 'budget'), not a silent unbounded
        # derivation.
        if not a.terms:
            return Verdict(a.assertion_id, AssertionStatus.UNCHECKABLE,
                           reason="no_rules",
                           derivations=0, cut_depth=0)
        rel, args = a.terms[0], a.terms[1:]
        try:
            derivations, cut_depth = self.engine.check_cost(rel, args)
        except DatalogError:
            return Verdict(a.assertion_id, AssertionStatus.UNCHECKABLE,
                           reason="unknown_predicate",
                           derivations=0, cut_depth=0)
        if derivations > self.budget.derivations_per_assertion:
            return Verdict(a.assertion_id, AssertionStatus.UNCHECKABLE,
                           reason="budget", derivations=0, cut_depth=0)
        if cut_depth > self.budget.cut_depth_max:
            return Verdict(a.assertion_id, AssertionStatus.UNCHECKABLE,
                           reason="budget", derivations=0, cut_depth=0)
        if not self.budget.within_turn(self.ledger.spent_this_turn,
                                       derivations):
            return Verdict(a.assertion_id, AssertionStatus.UNCHECKABLE,
                           reason="budget", derivations=0, cut_depth=0)
        try:
            if self.engine.contradicted(rel, args):
                self.ledger.charge(derivations, cut_depth)
                return Verdict(a.assertion_id, AssertionStatus.REFUTED,
                               provenance=(f"refutes({rel})",),
                               derivations=derivations, cut_depth=cut_depth)
            if self.engine.lookup(rel, args):
                self.ledger.charge(derivations, cut_depth)
                return Verdict(a.assertion_id, AssertionStatus.VERIFIED,
                               provenance=(f"{rel} fact",),
                               derivations=derivations, cut_depth=cut_depth)
        except DatalogError:
            return Verdict(a.assertion_id, AssertionStatus.UNCHECKABLE,
                           reason="unknown_predicate",
                           derivations=0, cut_depth=0)
        # THE DERIVE PATH (paper-3 prerequisite 1).  The store cannot
        # answer this atom by membership: no refutes fact, no stored
        # fact.  If a THEORY is attached, it gets the question next — a
        # claim that is not a stored fact but IS entailed by rules over
        # the store's evidence resolves VERIFIED, and one the rules
        # refute resolves REFUTED, with provenance naming the rules and
        # cost in the model's units (entail.py; no theory attached
        # falls straight through to the unchanged 'no_rules' verdict).
        if self.rules is not None:
            return self._check_derived(a, rel, args, derivations)
        self.ledger.charge(derivations, cut_depth)
        return Verdict(a.assertion_id, AssertionStatus.UNCHECKABLE,
                       reason="no_rules", derivations=derivations,
                       cut_depth=cut_depth)

    def _check_derived(self, a: Assertion, rel: str, args: tuple,
                       lookup_cost: int) -> Verdict:
        """Adjudicate a lookup miss through the attached theory (the
        DERIVE step; entail.py owns the semantics, this applies the CEN's
        budget gates and ledger charges).  CONVENTION: the verdict's
        cost fields report exactly what the LEDGER was charged for this
        assertion — the lookup miss that brought us here plus the
        theory's cost — matching the fact path, where verdict cost ==
        ledger charge.  The theory's own declared bound gates the run
        BEFORE it happens; the measured cost gates the verdict; both
        charges land in the same C11 ledger as the fact path."""
        th = self.rules
        # the declared-bound pre-gate: a theory that DECLARES a bound
        # beyond the budget's ceilings would be an unrunnable check by
        # declaration — refuse before evaluating (nothing charged but
        # the lookup miss; the theory is not consulted).
        if th.max_depth > self.budget.cut_depth_max \
                or th.max_derivations > self.budget.derivations_per_assertion:
            self.ledger.charge(lookup_cost, 0)
            return Verdict(a.assertion_id, AssertionStatus.UNCHECKABLE,
                           reason="budget", derivations=lookup_cost,
                           cut_depth=0)
        try:
            d = th.check(self.engine, rel, args)
        except DatalogError:
            return Verdict(a.assertion_id, AssertionStatus.UNCHECKABLE,
                           reason="unknown_predicate",
                           derivations=0, cut_depth=0)
        if not d.ran:
            # gated before evaluation (grammar / no seat / no engine
            # surface): charge the lookup miss only.
            self.ledger.charge(lookup_cost, 0)
            return Verdict(a.assertion_id, AssertionStatus.UNCHECKABLE,
                           reason=d.reason, derivations=lookup_cost,
                           cut_depth=0, provenance=d.provenance)
        # the theory ran: charge the lookup miss plus the theory's
        # reported cost, gated by the ceilings (a derived verdict that
        # does not fit is budget debt, not a silent unbounded check —
        # the same seat the fact path gives over-cost checks).
        cost = lookup_cost + d.derivations
        over = (d.derivations > self.budget.derivations_per_assertion
                or d.cut_depth > self.budget.cut_depth_max
                or not self.budget.within_turn(self.ledger.spent_this_turn,
                                               cost))
        self.ledger.charge(cost, d.cut_depth)
        if over or d.status == "UNCHECKABLE" and d.reason == "budget":
            return Verdict(a.assertion_id, AssertionStatus.UNCHECKABLE,
                           reason="budget", derivations=cost,
                           cut_depth=d.cut_depth,
                           provenance=d.provenance)
        status = AssertionStatus.VERIFIED if d.status == "VERIFIED" \
            else (AssertionStatus.REFUTED if d.status == "REFUTED"
                  else AssertionStatus.UNCHECKABLE)
        reason = d.reason if status is AssertionStatus.UNCHECKABLE else ""
        return Verdict(a.assertion_id, status,
                       provenance=d.provenance,
                       derivations=cost, cut_depth=d.cut_depth,
                       reason=reason)

    # -- C8 surface: the INTEGRATED state, readable at the boundary --------
    def integrated_state(self) -> dict:
        """The live state the NEXT turn reads — the object C8 says to
        assert on.  A log (TurnRecords) is intent; this is behaviour."""
        out = {
            "turn": self._turn,
            "queue": [(b.turn, tuple(a.assertion_id for a in b.assertions))
                      for b in self.queue],
            "debt": list(self.ledger.debt_assertions),
            "derivations_total": self.ledger.spent_total,
            "record_head": self.record.head_hash,
            "record_count": self.record.count,
            "engine_rev": self.engine.revision(),
        }
        if self.retrieval is not None:
            # the retrieval observables (item 'retrieval'): the epoch
            # table is the working-set metadata C20 says lives in RAM —
            # CONTENT-FREE, bounded (one record per key), and never a
            # carrier for the self itself.
            out["retrieval"] = self.retrieval.dump()
        if self.actions is not None:
            # the ACTION seat's state (the tool-call layer): the
            # registered-but-unanswered set and the applied/refused
            # counters.  NO verdict and NO debt enter here — a tool
            # action is an intent, and a tool RESULT is the world's
            # answer, not an assertion the agent made (conflating them
            # would corrupt the backlog/debt accounting's input).
            out["actions"] = self.actions.dump()
        return out
