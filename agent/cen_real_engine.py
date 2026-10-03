"""cen_real_engine.py — DatalogDatalogEngine: the REAL datalog-dafsa
engine behind the DatalogEngine Protocol (C10 substitution).

This is a SUBSTITUTION, NOT A REDESIGN: the CEN's logic does not change
(the Protocol's own words).  The adapter wraps the verified binding at
~/thing/dlb/ (READ-ONLY here; ~50 C symbols, 42 tests, measured
envelope) and restores, on top of the C surface, the exact semantics
StubDatalogEngine established — so the CEN, the harness and the Stage-2
tests run UNCHANGED over the real store:

  Protocol method          dlb call                        notes
  -----------------------  ------------------------------  ------
  declare(rel, arity)      Db.declare_relation             re-declaring the SAME arity is the engine's own no-op; a DIFFERENT arity for an existing name raises (adapter surfaces it)
  lookup(rel, args)        Db.lookup (on interned cols)    + the declaration/arity gate the C level does not have (dl_lookup on an undeclared relation returns 0 — the adapter raises DatalogError so errors SURFACE, the stub's rule)
  contradicted(rel, args)  Db.lookup("refutes", (key,))    POSITIVE refutes relation — Datalog has no negation-as-failure and the substrate stays MONOTONE (nothing is ever concluded from a LACK)
  txn_commit(token, facts) Db.transaction + txn.cas         ONE atomic txn; the revision is a CAS entity ("cen-rev") bumped exactly once per commit, so revision() is per-turn and survives reopen
  revision()               Db.rev_get("cen-rev")
  seed(facts)              Db.add_fact outside any txn     the loader layer's job (dlp); no write lock taken
  dump() / load()          reopen DIRECTIVE, not a copy    see the checkpoint/resume section — with a real durable store, resume = REOPEN

THE FIVE BINDING-SIDE CONSTRAINTS THIS ADAPTER HONOURS:

* (C19) NO DELETES.  dlb EXPOSES Db.delete_fact / Transaction.delete_fact
  and a cas_revision-based deletion path; THIS ADAPTER WRAPS NONE OF
  THEM.  There is deliberately no delete_* method, the underlying Db
  handle is not re-exported, and no code path here calls a delete
  surface.  The agent-level store is APPEND-ONLY WITH SUPERSESSION:
  correction adds a superseding fact and the read path resolves
  latest-wins; a delete would break C19's four independent grounds
  (the human reference, mu_M = 0, the write-suppression rule, and C9's
  hash chain).  tests part R4 asserts the absence structurally.

* (C13/C15) THE CEN IS THE SOLE WRITER.  The engine's fcntl LOCK is
  exclusive-vs-shared IN BOTH DIRECTIONS (measured, ENVELOPE.md §4):
  a second writer cross-process gets DL_E_LOCKED from dl_open2, and
  the binding's per-process registry refuses a same-process second
  handle the same way.  The adapter MAPS DlLockedError to the CEN's
  EXISTING lock semantics — SoleWriterError, the same exception class
  the stub's _own() raises and the Protocol's txn_commit docstring
  names ("rejected (LOCK semantics)") — and lets it PROPAGATE.  It is
  never swallowed and never retried: a locked store is a P3 violation
  to report, not to paper over.  Additionally txn_commit itself checks
  the WriterToken identity exactly like the stub (same-process,
  same-handle second writer), so both the engine's LOCK and the CEN's
  capability object are enforced on every write path.

* (C15) THE MECHANISM OWNS ITS OWN STORE DIRECTORY.  This is NOT the
  shared fx-agent-memory store (that store cannot even be opened
  read-only while fx-agent-memory holds its writer).  Resolution:
  explicit store_dir argument > $CEN_STORE_DIR > ~/.cen-store (created
  0700).  Same rule as the record anchor's default, same reason.

* NO NEGATION-AS-FAILURE.  contradicted() stays a lookup on the
  POSITIVE `refutes` relation (see table above).  The engine exposes
  no negation surface and the adapter invents none.

* (C11/C14) COST IS DERIVATIONS AND CUT DEPTH, PER-STEP READS ARE THE
  BUDGET.  The per-turn read path this adapter puts the CEN on is
  POINT READS ONLY: lookup via intern_find + dl_lookup, measured here
  at ~6.7 us per ground check (intern_find 1.5 us + lookup 3.5 us +
  Python glue) and ~10 us for the refutes pre-check — inside the
  <=10 us/step budget for point reads (ENVELOPE.md §2).  The per-turn
  WRITE path (one txn: 5 facts + interning + one CAS) measured ~186
  us/turn — a write, not a per-step read, and far under the C11
  derivation budget's granularity.  NO derived/recursive query is on
  the per-turn path (query_rules_ro 1.8 ms-35.9 s is explicitly off
  it); the adapter does not wrap a query surface at all, so the CEN
  cannot accidentally price a step in the wrong unit.  Cost REPORTING
  is the CEN's ledger, fed by the engine's OWN cost surface — the
  Protocol's `check_cost(relation, args)` method this adapter now
  populates.  A ground lookup reports (1, 0): one distinct stored fact
  consulted, cut depth 0 (a membership test has no proof tree).  That
  is the HONEST number, not a placeholder — the binding landed and it
  is the same as the stub's because both resolve a ground atom by a
  membership test.  Reuse accounting (circuit vs formula) and non-zero
  cut depths become live only when rules exist, which the P4 compiler
  bake-off still gates; with no rules circuit == formula == 1.

CHECKPOINT / RESUME (C8) — THE DESIGN QUESTION, ANSWERED FOR CURRENT
SEMANTICS.  The stub was an in-memory dict, so its dump()/load()
carried the facts.  With a real store the facts LIVE ON DISK: the
engine writes a per-relation WAL that replays at open (verified here:
a committed txn, then os._exit with NO close, is fully visible to the
next open — facts and revision).  So resume = REOPEN, and dump() is a
REOPEN DIRECTIVE, not a copy of the store: {"store_dir", "rev",
"declared", "kind": "DatalogDatalogEngine"}.  load() reopens the
store and restores the declaration map; the durable record's head
cross-check (already in Stage2State.from_checkpoint) still pins store
state to record state.  Carrying a full fact COPY beside the durable
store would be belt-and-braces that can silently DIVERGE (two sources
of truth); it is deliberately NOT done.  CURRENT-semantics caveats,
stated: (1) the batched-fsync / periodic-snapshot work in the engine
repo (occupied lane, in flight) may change WAL timing — the WAL
replay contract at open is what this design depends on and that is
the documented semantics; (2) between a txn commit and a checkpoint
write, further turns may advance the store — load() ACCEPTS a store
rev >= checkpoint rev (the record prefix is intact; only appends
happened) and REFUSES a store rev < checkpoint rev (the store lost
commits the record remembers — fail closed).  One deliberate same-
process nuance: the stub's dump/load ran INSIDE one process where the
old engine object stayed alive; a real store handle cannot coexist
with its reopen in one process (the LOCK excludes in both
directions), so load() performs a TAKEOVER — the prior handle is
closed first, the store is reopened RW by the resuming CEN, which
re-owns the writer exactly the way a resumed stub re-owned it through
its own token ("matching the real engine's lock-on-open semantics",
the stub docstring's own words).  The old handle must not be used
afterwards; the adapter marks it closed.

FAILURE MODE (NO SILENT STUB FALLBACK).  dlb loads libdatalog.so at
import; if it cannot, DlLibraryError propagates from THIS module's
import of dlb — loud, at the earliest moment.  Nothing here falls
back to StubDatalogEngine: a silent fallback would make every test
pass while testing nothing.

Usage (the harness does exactly this):
    sys.path.insert(0, "../dlb")   # or PYTHONPATH
    from cen_real_engine import DatalogDatalogEngine
    eng = DatalogDatalogEngine.open(store_dir)    # writer (sole)
    cen = CEN(engine=eng, record=..., token=tok)
"""
from __future__ import annotations

import os
import sys
from typing import Sequence

# dlb must be importable.  The scaffold's path handling plus the
# explicit insert covers the default layout; PYTHONPATH works too.
_DLB_PATH = "../dlb"
if _DLB_PATH not in sys.path:
    sys.path.insert(0, _DLB_PATH)

# A missing/unloadable library must be LOUD (DlLibraryError), never a
# stub fallback — see the module docstring.  dlb loads the .so lazily
# (at first Db.open, not at import) and a MISSING file surfaces as a
# bare ctypes OSError there; the adapter's open/load paths re-raise
# that as DlLibraryError.  Here we additionally PROBE the library at
# import so a broken install fails before any store directory is
# created:
try:
    import dlb  # noqa: E402
    from dlb import DlError, DlLibraryError, DlLockedError  # noqa: E402
    from dlb._binding import load_library as _dlb_load  # noqa: E402
    _dlb_load()
except OSError as _e:   # ctypes CDLL failure — the .so is missing/bad
    raise DlLibraryError(
        f"libdatalog.so could not be loaded — the real engine cannot "
        f"start and there is NO stub fallback (set $DLBLIB or build "
        f"the canonical zig-out release): {_e}") from _e

from cen import DatalogError, SoleWriterError, WriterToken  # noqa: E402

__all__ = ["DatalogDatalogEngine", "DEFAULT_STORE_DIR",
           "CEN_REVISION_ENTITY"]


#: Where the engine's own store lives by default (C15: the mechanism's
#: OWN directory — never the shared fx-agent-memory store, whose writer
#: excludes every other handle while it is open).
DEFAULT_STORE_DIR = os.path.join(os.path.expanduser("~"), ".cen-store")

#: The CAS entity that carries the store revision.  The C engine's
#: revisions are per-entity (dl_rev_get), not global; the CEN's txn
#: discipline (exactly one commit per DMN turn, FIFO) is what makes a
#: single entity the right stand-in for the stub's counter — and it
#: survives reopen, which a Python-side int would have to be coaxed
#: into.
CEN_REVISION_ENTITY = "cen-rev"


#: In-process engine registry, realpath(store_dir) -> the engine whose
#: dlb handle is live.  The binding refuses a second same-process
#: handle per directory (fcntl cannot self-arbitrate — measured), so a
#: NEW engine for the same store TAKES OVER: the prior handle is closed
#: (with its dump snapshotted first, so the superseded state object
#: still reports the last state it saw) and the new engine re-opens.
#: This is the real-engine form of the stub's documented resume rule —
#: "the writer-lock identity resets; a resumed CEN re-owns the store
#: through its own token" — and it cannot bypass P3: cross-process, the
#: engine's fcntl LOCK still excludes every other writer absolutely.
_ENGINES: dict[str, "DatalogDatalogEngine"] = {}


class DatalogDatalogEngine:
    """The real datalog-dafsa store behind the DatalogEngine Protocol.

    Same observable semantics as StubDatalogEngine (the CEN cannot tell
    them apart on the per-turn path), except the facts are REAL,
    DURABLE (WAL replay at open), and locked against a second writer by
    the ENGINE (fcntl), not just by the token check.

    NOT WRAPPED (deliberately): delete_fact / Transaction.delete_fact /
    any cas-based deletion (C19 — no deletes, ever); every vector
    surface (semantic recall, not per-step; the CEN has no use for it).

    WRAPPED SINCE PREREQUISITE 1 (the rules seat): `query_rules` — the
    DERIVE path's READ surface over the engine's own rule machinery
    (dl_query_rules_ro: parse+compile+evaluate a self-contained rule
    source against a THROWAWAY SHALLOW CLONE of the store, discard the
    clone).  This is the one deliberate addition to the adapter's old
    "no query surface" stance, which predates rules existing; the C11
    note below is updated to match.  It is NOT on the point-read path:
    it fires only on a lookup miss with a theory attached (measured
    0.74 ms at fixture scale, ENVELOPE.md — 74x over the per-step budget,
    priced in derivations, not hidden in wall time).
    """

    kind = "DatalogDatalogEngine"

    def __init__(self, db: "dlb.Db", store_dir: str,
                 declared: dict[str, int] | None = None):
        self._db = db
        self.store_dir = store_dir
        self._declared: dict[str, int] = dict(declared or {})
        self._token: WriterToken | None = None
        self._sym: dict[str, int] = {}
        self._closed = False
        self._superseded = False
        self._last_dump: dict | None = None

    # -- lifecycle ------------------------------------------------------

    @classmethod
    def _takeover(cls, d: str) -> None:
        """Same-process writer hand-off for one store directory: the
        prior engine's handle is closed (its dump captured first)."""
        real = os.path.realpath(d)
        prior = _ENGINES.get(real)
        if prior is not None and not prior._closed:
            prior._last_dump = prior._dump_raw()
            prior._db.close()
            prior._closed = True
            prior._superseded = True

    @classmethod
    def open(cls, store_dir: str | None = None) -> "DatalogDatalogEngine":
        """Open (or create) the store READ-WRITE — the CEN's sole-writer
        handle.  Raises SoleWriterError if another writer (any process)
        holds the LOCK; DlLibraryError if the .so cannot load (the
        binding itself raises DlLibraryError only on ABI mismatch — a
        MISSING file is a bare ctypes OSError at CDLL time, which the
        adapter re-raises as DlLibraryError so the failure is always
        unmistakably a library-load failure, never a silent fallback).
        """
        d = store_dir or os.environ.get("CEN_STORE_DIR") or DEFAULT_STORE_DIR
        os.makedirs(d, mode=0o700, exist_ok=True)
        cls._takeover(d)
        try:
            db = dlb.Db.open(d)
        except DlLockedError as e:
            # C13/C15: the ENGINE's lock, mapped onto the CEN's EXISTING
            # lock semantics (the stub raises SoleWriterError for the
            # same condition; P3's txn_commit docstring names "LOCK
            # semantics").  Surfaced, never swallowed.
            raise SoleWriterError(
                f"store at {d} is locked by another writer "
                f"(P3 sole writer; DL_E_LOCKED class): {e}") from e
        except DlLibraryError:
            raise
        except OSError as e:
            raise DlLibraryError(
                f"libdatalog.so could not be loaded — the real engine "
                f"cannot start and there is NO stub fallback (set "
                f"$DLBLIB or build the canonical zig-out release): "
                f"{e}") from e
        except DlError as e:
            raise DatalogError(f"dl_open({d}) failed: {e}") from e
        eng = cls(db, d)
        _ENGINES[os.path.realpath(d)] = eng
        eng._recover_declared()
        return eng

    def close(self) -> None:
        if not self._closed:
            if self._db is not None:
                self._db.close()
            self._closed = True
            real = os.path.realpath(self.store_dir)
            if _ENGINES.get(real) is self:
                del _ENGINES[real]

    @property
    def closed(self) -> bool:
        return self._closed

    def _require_open(self, what: str) -> None:
        if self._closed:
            why = ("taken over by a newer engine for the same store"
                   if self._superseded else
                   "closed (shut down or resumed elsewhere)")
            raise DatalogError(
                f"{what}: engine handle is {why} — errors surface, "
                f"they do not return False")

    #: The in-store declaration journal.  The C engine persists
    #: declarations but offers no enumeration, and a lookup on an
    #: UNdeclared relation returns 0 — indistinguishable from a miss —
    #: so the adapter records every declare() as a fact and replays the
    #: journal at open.  (name_sym, arity) rows; append-only like
    #: everything else (C19).
    _DECL_JOURNAL = "__cen_declared__"

    def _recover_declared(self) -> None:
        """Rebuild the declaration map after a (re)open: the CEN's fixed
        relation set, then the journal.  Re-declaring (name, arity) for
        an existing name with the SAME arity is the engine's own no-op;
        a DIFFERENT arity fails and surfaces."""
        try:
            self._db.declare_relation(self._DECL_JOURNAL, 2)
        except DlError as e:
            raise DatalogError(
                f"declare_relation({self._DECL_JOURNAL},2) failed: {e}"
            ) from e
        self._declared.setdefault(self._DECL_JOURNAL, 2)
        for rel, ar in (("asserts", 3), ("verdict_of", 3),
                        ("self_content", 2), ("refutes", 1)):
            self._declare_raw(rel, ar)
        try:
            it = self._db.iter(self._DECL_JOURNAL)
        except DlError as e:
            raise DatalogError(f"declaration journal scan failed: {e}"
                               ) from e
        with it:
            for name_sym, arity in it:
                name = self._db.sym_of(name_sym)
                if name is None:
                    raise DatalogError(
                        f"declaration journal holds symbol {name_sym} "
                        f"with no name — surfacing, not guessing")
                self._declared.setdefault(name, int(arity))

    def _declare_raw(self, relation: str, arity: int) -> None:
        try:
            self._db.declare_relation(relation, arity)
            self._db.add_fact(self._DECL_JOURNAL,
                              (self._sym_of(relation), arity))
        except DlError as e:
            raise DatalogError(f"declare_relation({relation},{arity}) "
                               f"failed: {e}") from e
        self._declared[relation] = arity

    # -- the Protocol surface --------------------------------------------

    def declare(self, relation: str, arity: int) -> None:
        """`arity` counts the ARGUMENTS (the relation name is not part
        of it); facts are stored as (relation, *args) — stub rule."""
        self._require_open("declare")
        self._declare_raw(relation, arity)

    def seed(self, facts: Sequence[tuple]) -> None:
        """Bulk-load initial facts WITHOUT a txn (the loader/preprocessor
        layer's job in datalog-dafsa; initial data, not a writer's
        commit — stub docstring's rule, now against the real store)."""
        self._require_open("seed")
        for f in facts:
            rel = f[0]
            if rel not in self._declared:
                raise DatalogError(f"seed writes undeclared '{rel}'")
            try:
                self._db.add_fact(rel, self._cols(rel, f[1:]))
            except DlError as e:
                raise DatalogError(f"seed add_fact({rel}) failed: {e}") from e

    def lookup(self, relation: str, args: Sequence) -> bool:
        """Ground-fact membership (dl_lookup on interned columns).  The
        C level has NO undeclared/arity error for reads (it returns 0),
        so the ADAPTER enforces the stub's surface-error contract."""
        self._require_open("lookup")
        if relation not in self._declared:
            raise DatalogError(
                f"relation '{relation}' undeclared — errors surface, "
                f"they do not return False")
        if len(args) != self._declared[relation]:
            raise DatalogError(
                f"relation '{relation}' arity {self._declared[relation]}, "
                f"got {len(args)} args")
        try:
            return self._db.lookup(relation, self._cols(relation, args))
        except DlError as e:
            raise DatalogError(f"lookup({relation}) failed: {e}") from e

    def contradicted(self, relation: str, args: Sequence) -> bool:
        """Explicit `refutes` fact holds — a POSITIVE relation (Datalog
        has no negation-as-failure; the substrate stays monotone).  The
        key is the rendered atom, exactly the stub's encoding."""
        key = f"{relation}({','.join(map(str, args))})"
        try:
            return self._db.lookup("refutes", (self._sym_of(key),))
        except DlError as e:
            raise DatalogError(f"refutes lookup failed: {e}") from e

    def check_cost(self, relation: str, args: Sequence) -> tuple[int, int]:
        """C11's cost surface, populated honestly for the REAL engine:
        a ground membership check reports (1, 0) — one distinct stored
        fact consulted, cut depth 0 (a membership test has no proof
        tree).  This is a Python-side declaration/arity gate ONLY; it
        performs NO C call, so the per-step read path (contradicted +
        lookup) keeps its measured cost.  Reuse accounting (circuit vs
        formula) and non-zero cut depths become live when rules exist;
        with no rules circuit == formula == 1 and depth == 0."""
        self._require_open("check_cost")
        if relation not in self._declared:
            raise DatalogError(
                f"relation '{relation}' undeclared — errors surface, "
                f"they do not return False")
        if len(args) != self._declared[relation]:
            raise DatalogError(
                f"relation '{relation}' arity {self._declared[relation]}, "
                f"got {len(args)} args")
        return (1, 0)

    def query_rules(self, source: str, goal_rel: str,
                    str_cols: Sequence[int] = ()) -> list[tuple]:
        """The DERIVE path's read surface (prerequisite 1): evaluate a
        self-contained Datalog rule source against a THROWAWAY shallow
        clone of the store and return the goal relation's tuples as
        (relation, *args) rows — the iter_facts convention, so the
        theory's membership scan reads decoded strings not raw symbol
        ids.  The STORE is never mutated (dl_query_rules_ro discards the
        clone; dlb's own test test_query_rules_ro_leaves_db_untouched
        pins it).  The rule source may reference the store's relations
        (done/orphaned/evidence relations) by name — the clone carries
        their facts.  NOT a per-step path (see the class note)."""
        self._require_open("query_rules")
        sc = set(int(c) for c in str_cols)
        try:
            raw = self._db.query_rules_ro(source, goal_rel)
        except DlError as e:
            raise DatalogError(
                f"query_rules({goal_rel}) failed: {e}") from e
        out: list[tuple] = []
        for cols in raw:
            vals: list = []
            for i, v in enumerate(cols):
                if i in sc:
                    name = self._db.sym_of(int(v))
                    if name is None:
                        raise DatalogError(
                            f"query_rules({goal_rel}): symbol {v} in "
                            f"column {i} has no name — surfacing, not "
                            f"guessing")
                    vals.append(name)
                else:
                    vals.append(int(v))
            out.append((goal_rel, *vals))
        return out

    def iter_facts(self, relation: str,
                   str_cols: Sequence[int] = ()) -> list[tuple]:
        """The retrieval enumeration seat (dl_iter_open/next over the
        relation, sorted by construction).  String columns named in
        `str_cols` are decoded back from interned symbol ids through
        sym_of (a symbol with no name surfaces as DatalogError, never
        a silent wrong value).  Called ONCE PER TURN by the retrieval
        seat — campaign-priced, never on the per-step read path."""
        self._require_open("iter_facts")
        if relation not in self._declared:
            raise DatalogError(
                f"relation '{relation}' undeclared — errors surface, "
                f"they do not return False")
        arity = self._declared[relation]
        sc = set(int(c) for c in str_cols)
        out: list[tuple] = []
        try:
            it = self._db.iter(relation)
        except DlError as e:
            raise DatalogError(f"iter({relation}) failed: {e}") from e
        with it:
            for cols in it:
                vals: list = []
                for i, sym in enumerate(cols):
                    if i in sc:
                        name = self._db.sym_of(sym)
                        if name is None:
                            raise DatalogError(
                                f"iter({relation}): symbol {sym} in "
                                f"column {i} has no name — surfacing, "
                                f"not guessing")
                        vals.append(name)
                    else:
                        vals.append(self._dec_int(sym))
                out.append((relation, *vals))
        return out

    def txn_commit(self, token: WriterToken,
                   facts: Sequence[tuple]) -> int:
        """One atomic txn (dl_txn_begin/commit).  Sole-writer: the token
        identity is checked HERE exactly as the stub does, and the
        engine's LOCK has already excluded every OTHER process's writer
        at open.  The revision is the CAS entity, bumped once inside
        the SAME txn — so rev and facts commit or roll back together."""
        self._require_open("txn_commit")
        if self._token is None:
            self._token = token
        elif token is not self._token:
            raise SoleWriterError(
                f"store is locked by writer '{self._token.writer_id}' "
                f"(P3 sole writer; DL_E_LOCKED class)")
        for f in facts:
            if f[0] not in self._declared:
                raise DatalogError(f"txn writes undeclared '{f[0]}'")
        try:
            with self._db.transaction() as tx:
                for f in facts:
                    tx.add_fact(f[0], self._cols(f[0], f[1:]))
                cur = self._db.rev_get(CEN_REVISION_ENTITY)
                tx.cas(CEN_REVISION_ENTITY, cur, cur + 1)
        except DlLockedError as e:
            raise SoleWriterError(
                f"txn rejected — another writer holds the store "
                f"(P3; DL_E_LOCKED class): {e}") from e
        except DlError as e:
            raise DatalogError(f"txn_commit failed: {e}") from e
        return self._db.rev_get(CEN_REVISION_ENTITY)

    def revision(self) -> int:
        self._require_open("revision")
        try:
            return self._db.rev_get(CEN_REVISION_ENTITY)
        except DlError as e:
            raise DatalogError(f"revision() failed: {e}") from e

    # -- the C8 resume surface: reopen, not reload ------------------------

    def _dump_raw(self) -> dict:
        return {"kind": self.kind,
                "store_dir": self.store_dir,
                "rev": self._db.rev_get(CEN_REVISION_ENTITY),
                "declared": dict(self._declared)}

    def dump(self) -> dict:
        """A REOPEN DIRECTIVE, not a copy of the store (see the module
        docstring's checkpoint section): the durable store IS the facts;
        the checkpoint carries where it lives and what was declared.
        A SUPERSEDED engine (its handle was taken over by a newer
        engine for the same store) reports the last dump captured at
        takeover — the state it last saw — instead of raising."""
        if self._superseded:
            if self._last_dump is None:
                raise DatalogError(
                    "superseded engine has no dump snapshot — internal "
                    "inconsistency (report this)")
            return dict(self._last_dump)
        self._require_open("dump")
        return self._dump_raw()

    def load(self, state: dict) -> None:
        """Resume = REOPEN.  Takes over this process's prior handle (a
        real store cannot be opened twice in one process — the LOCK
        excludes in both directions), reopens RW, restores the
        declaration map, and fail-closes on a store that is BEHIND the
        checkpoint (commits the record remembers are gone).  A store
        AHEAD of the checkpoint is an append-only extension — accepted,
        the same prefix rule the durable record's own cross-check
        applies."""
        if state.get("kind") != self.kind:
            raise DatalogError(
                f"checkpoint engine kind {state.get('kind')!r} is not "
                f"{self.kind!r} — refusing to load (fail-closed)")
        d = state["store_dir"]
        want_rev = state["rev"]
        if self._superseded:
            # a load() onto an already-superseded engine is a
            # programming error: the state object owning THIS engine
            # was itself superseded by a newer one
            raise DatalogError(
                "load() on an engine superseded by a newer engine "
                "for the same store — the newer engine owns the "
                "writer; refusing (P3)")
        real = os.path.realpath(d)
        prior = _ENGINES.get(real)
        if prior is not None and prior is not self and not prior._closed:
            self._takeover(d)
        self._declared = dict(state.get("declared") or {})
        try:
            self._db = dlb.Db.open(d)
        except DlLockedError as e:
            raise SoleWriterError(
                f"resume: store at {d} is locked by another writer "
                f"(P3 sole writer; DL_E_LOCKED class): {e}") from e
        except DlLibraryError:
            raise
        except OSError as e:
            raise DlLibraryError(
                f"libdatalog.so could not be loaded — the real engine "
                f"cannot resume and there is NO stub fallback: {e}"
            ) from e
        except DlError as e:
            raise DatalogError(f"resume dl_open({d}) failed: {e}") from e
        self.store_dir = d
        self._closed = False
        self._superseded = False
        self._last_dump = None
        _ENGINES[os.path.realpath(d)] = self
        got_rev = self._db.rev_get(CEN_REVISION_ENTITY)
        if got_rev < want_rev:
            raise DatalogError(
                f"resume: store rev {got_rev} < checkpoint rev {want_rev} "
                f"— the store LOST commits the checkpoint remembers "
                f"(fail-closed)")
        # re-assert the CEN's own relations exist in the reopened store
        self._recover_declared()
        # a resumed CEN re-owns the store through its own token (the
        # stub's rule: lock identity resets on load)
        self._token = None

    # -- internals ---------------------------------------------------------

    def _sym_of(self, s: str) -> int:
        """Intern with a Python-side cache (intern is idempotent; the
        cache saves one C call per repeated ground atom).  dl_intern
        never returns 0 (0 is intern_find's miss sentinel)."""
        sid = self._sym.get(s)
        if sid is None:
            try:
                sid = self._db.intern(s)
            except DlError as e:
                raise DatalogError(f"intern({s!r}) failed: {e}") from e
            if sid == 0:
                raise DatalogError(
                    f"intern({s!r}) returned the reserved 0 symbol "
                    f"— surfacing, not guessing")
            self._sym[s] = sid
        return sid

    #: The INT BIAS (loopwire, 2026-09-28): the C columns are u32 and
    #: the Protocol carries SIGNED turns — selfmodel.SEED_TURNS are
    #: -4..-1 (the derivation seed's pre-history), which used to CRASH
    #: here ('must be str or u32, got -4'; first caller of
    #: seed_self=True x engine='real', MEASURED).  Encoding: a negative
    #: int n is stored as 2^32 + n (the TOP of the u32 space, an
    #: otherwise-refused range), so the map is order-preserving and
    #: injective against every non-negative int; decode is the exact
    #: inverse in iter_facts.  Ints >= 2^31 - 1 stay refused (the head-
    #: room keeps the two ranges disjoint by construction, not by
    #: convention).
    _INT_BIAS = 0x1_0000_0000

    def _enc_int(self, a: int) -> int:
        if a < 0:
            return self._INT_BIAS + int(a)
        return int(a)

    def _dec_int(self, u: int) -> int:
        # threshold 2^31, not 2^32: the biased negatives land in
        # [2^32-|n|] which for small |n| sits JUST UNDER 2^32, so a
        # 2^32 threshold never fires; the non-negative range is capped
        # below 2^31-1 in _cols, which makes 2^31 the exact separator.
        return int(u) - self._INT_BIAS if int(u) >= 0x8000_0000 \
            else int(u)

    def _cols(self, relation: str, args: Sequence) -> tuple:
        """Map Protocol args (strings or signed ints) to C u32 columns:
        strings are interned, ints pass through the SIGNED encoding
        (negatives biased into the top of the u32 space — see
        _INT_BIAS; order and distinctness are preserved exactly)."""
        out = []
        arity = self._declared[relation]
        if len(args) != arity:
            raise DatalogError(
                f"relation '{relation}' arity {arity}, got {len(args)} args")
        for a in args:
            if isinstance(a, str):
                out.append(self._sym_of(a))
            elif isinstance(a, int) and not isinstance(a, bool) \
                    and -self._INT_BIAS < a < 0x7FFF_FFFF:
                out.append(self._enc_int(a))
            else:
                raise DatalogError(
                    f"fact column for '{relation}' must be str or a "
                    f"signed int in (-2^32, 2^31-1), got {a!r}")
        return tuple(out)
