"""THE OUT-OF-PROCESS BOUNDARY — THE CLIENT SHIM (TODO P4 item 13a /
design/architecture.md §3a R6, v1).

WHAT THIS FILE IS.  The MECHANISM-SIDE half of the boundary: a thin
client the harness uses INSTEAD OF holding the routing criterion and the
selector itself.  It speaks one length-prefixed JSON request per call to
agent/boundary_daemon.py over an AF_UNIX socket and returns what the
daemon decided.  It owns NO seat: it constructs no selector, reads no
criterion file, and holds no anchor key.

=================== R6 v1: WHAT IT CLOSES, AND WHAT IT DOES NOT ==========
READ THIS BEFORE CITING R6 AS SATISFIED.  R6's letter is that the
criterion, the held-out usefulness definition and the integrity anchor
may be owned out-of-process — "a separate process/privilege domain the
mechanism can neither READ nor WRITE" (design/architecture.md §3a R6).
v1 implements the ENFORCEABLE CORE and leaves the rest STATED, not
silently claimed (standing order §1a):

  CLOSED (against code running in the mechanism's process):
    * THE WRITE.  There is no publish/reset/ensure operation over the
      socket at all: publication is a daemon CLI operation run in the
      daemon's own privilege domain (`boundary_daemon.py --publish-*`),
      so the forged-writer_id publish (MEASURED: battery R11, a fresh
      store plus a token it NAMES "designer" publishes f_max=0.0 over
      the designer's sealed v1 and takes the loop 3/3 -> 0/0) has no
      code path to call from the mechanism's process.  The write path
      is also closed at the FILESYSTEM level in the dedicated-UID
      deployment (the criterion tree is 0700 in the daemon's uid).
    * THE ANCHOR.  The 32-byte anchor key never crosses the socket in
      either direction and never exists in the mechanism's process
      (the daemon's store objects hold it in the daemon's uid).  The
      read that made G5's rewrite-and-reseal possible in-process is not
      available to the mechanism.
    * THE SELECTOR EXECUTION.  `route` computes the extraction, the
      SpanState mapping and the selection INSIDE the daemon, so the
      harness process has no selector object to monkeypatch (MEASURED:
      review B2/N6c, an in-process `PrefixRoutingSelector` replacement
      steers turn parity past R3/R4).  The CLIP [f_min, f_max] is
      applied daemon-side too — the mechanism cannot hand the selector
      a number of its own choosing.
    * THE CRITERION FILE READ.  The harness never opens the criterion
      file (battery B6 asserts it with a construction spy), so the
      ENV-redirect handle (CEN_ROUTINGCRIT_DIR, MEASURED review R9
      note) no longer exists on the mechanism's side of the boundary.

  CLOSED BY v2 — THE TOOL EFFECT (the exec op; v1 had none, and
  `realtools.py:110-120` said so).  R6 is FORCED HARDEST by the tool
  surface: `write` authors code, `bash` and `run_tests` execute it, so
  the mechanism owning the executor is the thing R6 names.  The `tool`
  op hands ONE tool request to the daemon, which resolves it against a
  SANDBOX AND A SURFACE IT OWNS and returns the daemon's own typed
  record:
    * THE SANDBOX IS THE DAEMON'S.  The daemon constructs its own
      `realtools.ToolHarness` (Q3: it IMPORTS the audited seat and
      reimplements nothing) whose workspace root is a `mkdtemp` in the
      DAEMON's process.  No field of any request can name a root: a
      request carrying one is REFUSED (ALLOWED_FIELDS).  The caller
      cannot hand the daemon a different root.
    * THE CALLER NAMES A TARGET, NEVER A PATH.  A tool request's file
      argument is a TARGET name (`f1/sub/x`) resolved against the
      daemon's workspace by the harness's own target gate
      (`undeclared_target` / `outside_sandbox` on a raw or escaping
      path).  This is the SAME rule as v1's field-level refusal, one
      level down: a raw path is a namespace-redirect attempt, and it is
      refused with a TYPED code, not ignored.
    * THE EFFECT RUNS IN THE DAEMON'S PROCESS.  `bash` and `run_tests`
      execute in a subprocess of the DAEMON (its own uid, its own
      `unshare` sandbox, its own timeout), never in the mechanism's.
    * THE SURFACE IS DECLARED OUT OF BAND, DEFAULT EMPTY.  The tools the
      daemon will execute and the targets it will touch are the
      DESIGNER's argv (`--tool-allow` / `--tool-target`), fixed at
      construction; the schema (ALLOWED_FIELDS) offers the caller no
      field to widen either.  The daemon adds no policy of its own: it
      executes the declared surface and refuses anything outside it
      (`undeclared_tool`).  THE GATE STAYS THE MECHANISM'S INPUT, NOT
      THE DAEMON'S CHOICE, and it is DEFAULT EMPTY.
    * NO PATH CROSSES BACK.  A tool record is returned only after the
      daemon's sandbox root is scrubbed out of it (`<sandbox>`), so a
      refusal's detail cannot leak the daemon's namespace — the same
      path-free rule as the v1 refusals.

  NOT CLOSED — STATED, with every residual named (this list is the
  honest scope; R6 v2 must NOT be cited as closing these):
    (R-a) THE CRITERION AND THE HELD-OUT DEFINITION STAY
        MECHANISM-READABLE, BY DESIGN.  The mechanism must ROUTE ON the
        criterion and be SCORED BY the definition, so both CROSS the
        boundary as data (crit / heldout_def here).  R6 requires that
        the mechanism "may neither read nor write" the seats; what v1
        enforces is the WRITE-closed half plus the anchor, so the
        READ-closed clause is weakened to its enforceable core:
        WRITE-closed + anchor-unreadable + selector-executed-outside.
        The READ-closed clause for criterion/definition is NOT
        implemented.
    (R-b) THE OS-USER RESIDUAL IS RE-BASED, NOT REMOVED (C9's G5).
        Same-uid (no dedicated user): the mechanism uid can still
        read/write the criterion tree and its anchor, so the forged
        publish is closed only by the ABSENCE OF THE OP — the file-level
        half rests on filesystem permissions that a same-uid deployment
        does not have.  With a dedicated uid (the plan's Q1 deployment)
        the file half is closed by the OS (0700/0600 in another uid).
        THE BATTERY CANNOT EXERCISE THE UID SEPARATION (no root, no
        user creation on this host) and says so: it measures the
        socket/protocol/refusal half and reports the uid half as
        PROJECTION under the deployment, with the same-uid measured
        outcome recorded.
    (R-c) THE SHIM IS IN-PROCESS CODE.  A monkeypatched SHIM can lie
        about the positions it returns exactly as a monkeypatched
        selector could (review B2).  The boundary narrows the trust
        base from "every module the mechanism runs" to "the harness
        wiring plus this shim"; it does not reduce it to zero.  A
        CLIENT-side handle is equally replaceable: a client pointed at
        a fake daemon (CEN_BOUNDARY_SOCKET, or cfg.boundary_socket)
        gets whatever that daemon says.  Closing that needs an
        out-of-band trust anchor (a signature over the response, or a
        pinned peer credential) — NOT BUILT, not claimed.
    (R-d) THE DAEMON'S CODEBASE AT REST IS INSIDE THE RESIDUAL.  The
        daemon imports routingcrit/heldout/cen FROM DISK; an actor who
        can write those files (root, or the daemon's own uid) can
        restart the daemon with a patched seat.  A signed/hashed daemon
        image is future work.
    (R-e) DENIAL OF SERVICE IS UNCLOSED.  The mechanism uid can fill
        the socket backlog or delete a socket it owns and stop its own
        checking.  That is the monitored process silencing its monitor
        — a KNOWN, recorded residual (the plan's Q4), not a boundary
        failure — and it is bounded by the fail-closed direction below:
        a dead/blocked daemon STOPS the run rather than degrading it.
    (R-f) THE COMMITTAL HOLE (G1/G6) IS UNTOUCHED.  The ordering and
        supply channels are open BY DESIGN (R1's prose return path);
        the boundary is not their closure and does not price them.
    (R-g) THE LAW'S NUMBER CROSSES AS AN INPUT — SO THE BOUNDARY DOES
        NOT OWN f.  `route()` takes `law_f`, the routing law's own
        output (routing.py, the model-derived number), because the law's
        state is the HARNESS's (RoutingWindow, checkpointed per state,
        consolidated from the plant's own inputs).  The daemon applies
        the criterion's [f_min, f_max] CLIP and the rule, so a caller
        cannot escape the DESIGNER'S BAND — but a tampered caller can
        choose any f INSIDE that band, and the harness already chooses
        the law's inputs.  Moving the law (and its window state) into
        the daemon is NOT done in v1 (it would drag the plant's per-turn
        inputs across and would still be fed by harness-side numbers);
        the honest statement is: v1 closes the SELECTION and the CLIP,
        not the law's input.  Marked PROJECTION-adjacent: no adversary
        has been run against it.
    (R-h) THE TOOL EFFECT'S OWN RESIDUALS ARE `realtools`' STATED ONES,
        MOVED, NOT REMOVED.  The exec op relocates the SANDBOX and the
        EXECUTOR out of the mechanism's process; it does not close the
        residuals that sandbox already declares (`realtools.py` item 4):
        the daemon runs as the SAME uids as the caller here (G5 re-based,
        not removed — the mechanism's uid can read the daemon's tool
        sandbox under /tmp, and the daemon's codebase at rest is inside
        the same residual R-d); `bash`'s mount namespace is default-deny
        VIEW, not a mandatory boundary (an in-ns actor can `umount`); the
        rest of `~/thing` stays readable from the daemon's `bash`; and
        resource exhaustion other than wall time is bounded only by the
        timeout's process-group kill.  What the op DOES close is the
        OWNERSHIP: the harness object, its workspace root and its declared
        surface live in the daemon, and no request field can move them.
        `realtools`' IN-PROCESS path is NOT removed by this op — it stays
        exactly as it is, and the wiring choice (in-process vs the daemon)
        is the CALLER's (the loop task wires the in-process path); v2 adds
        the out-of-process OWNER and converts no existing behaviour.

THE FAILURE MODE (Q4): FAIL-CLOSED, ALWAYS.  Every boundary failure —
the socket absent, a refused connect, a short read, a malformed or
version-mismatched response, or a daemon-side refusal — raises
`BoundaryUnavailable` (a `ChainError` subclass).  There is deliberately
NO degraded mode and NO local fallback: falling back to reading the
criterion file in the mechanism's uid would be safe ONLY against the
non-in-process adversary, and a fallback behind a runtime flag is
exactly the class R6 exists to close (the project's fail-closed
precedent: the DMN raises rather than stubs; the anchor refuses on
absence).

MARKING.  MEASURED: the refusals this shim and the daemon produce, and
the R11/B2/S4 attacks they are demonstrated against (the battery,
stage2_boundary_tests.py); and, for v2, the exec op's round-trip, its
raw-path and root-redirect refusals, the version mismatch, and the
path-free record (B9).  INTERPRETATION: that the uid-separated
deployment closes the file-level half (an OS enforcement argument, not
a measurement on this host — no root here).  PROJECTION: that the split
suffices against a real adversarial generator (no SWE campaign has run),
and the RPC latency (unmeasured before this battery; see B2).
"""
from __future__ import annotations

import json
import os
import socket
import struct

from cen import ChainError

__all__ = ["BOUNDARY_PROTOCOL_VERSION", "BOUNDARY_SOCKET_ENV",
           "DEFAULT_BOUNDARY_SOCKET", "MAX_FRAME_BYTES", "HEADER",
           "OP_PING", "OP_CRIT", "OP_ROUTE", "OP_HELDOUT_DEF",
           "OP_HELDOUT_SCORE", "OP_TOOL_EXEC", "AUTH_PEER", "AUTH_DESIGNER",
           "CALL_AUTH", "ALLOWED_FIELDS", "NOT_SERVED_OPS",
           "REFUSE_BAD_FRAME", "REFUSE_BAD_JSON", "REFUSE_BAD_REQUEST",
           "REFUSE_UNKNOWN_OP", "REFUSE_NOT_SERVED", "REFUSE_UNAUTHORIZED",
           "REFUSE_CRITERION", "REFUSE_HELDOUT", "REFUSE_INTERNAL",
           "REFUSE_PROTOCOL", "REFUSE_UNEXPECTED_FIELD", "REFUSE_TOOL",
           "HELDOUT_SCORE_SEAT", "TOOL_TARGET_MODEL", "BoundaryUnavailable",
           "BoundaryClient"]

#: THE PROTOCOL VERSION.  Bumped on ANY change to a request/response
#: shape; a shim and a daemon that disagree REFUSE (fail-closed), they
#: never negotiate down.
#:
#: v1 -> v2 (2026-09-28, the exec op): the SERVED CALL SET changed —
#: `tool` joined it (OP_TOOL_EXEC), a request/response shape that did not
#: exist.  A v1 shim speaking to a v2 daemon (and the reverse) REFUSES
#: with REFUSE_PROTOCOL rather than meeting an op the other side may not
#: have; the bump is the record of that change, not a formality.
BOUNDARY_PROTOCOL_VERSION = 2

#: Where the socket lives when the caller names none.  The CLIENT is the
#: only side that resolves this: it is the replaceable HANDLE, and a
#: client pointed elsewhere gets another daemon's answers (residual
#: R-c above) — the DAEMON resolves its own namespace at construction
#: and refuses a request that carries a path (ALLOWED_FIELDS).
BOUNDARY_SOCKET_ENV = "CEN_BOUNDARY_SOCKET"
DEFAULT_BOUNDARY_SOCKET = "/run/cenboundary.sock"

#: The frame cap (a length prefix is an attacker-controlled integer).
MAX_FRAME_BYTES = 1 << 20
HEADER = struct.Struct("!I")

# -- THE CALL SET (Q2) ---------------------------------------------------
OP_PING = "ping"
OP_CRIT = "crit"
OP_ROUTE = "route"
OP_HELDOUT_DEF = "heldout_def"
OP_HELDOUT_SCORE = "heldout_score"
#: THE EXEC OP (v2).  Named `tool` (the tool-execution op) rather than
#: `tool_exec` so the op name matches the `tool` field it takes and the
#: `realtools` vocabulary it serves; it IS the seat `realtools.py:110-120`
#: named as "the daemon is the seat to extend".
OP_TOOL_EXEC = "tool"

#: PER-CALL AUTH (Q2).  route/crit/heldout_def/tool are READ/PLAN/EXECUTE
#: — no auth beyond the peer credential the daemon checks on every
#: accepted connection (SO_PEERCRED: euid must be an allowed agent uid).
#: The table exists so the auth of each call is a DECLARED fact rather
#: than an absence: a call that is not here is refused by name.
AUTH_PEER = "peer-uid"
AUTH_DESIGNER = "designer-uid+token"
CALL_AUTH: dict = {
    OP_PING: AUTH_PEER,
    OP_CRIT: AUTH_PEER,
    OP_ROUTE: AUTH_PEER,
    OP_HELDOUT_DEF: AUTH_PEER,
    OP_HELDOUT_SCORE: AUTH_PEER,
    OP_TOOL_EXEC: AUTH_PEER,
}

#: THE REQUEST SCHEMA, PER OP — and therefore the list of what a caller
#: may NOT inject.  A request carrying a key outside its op's set is
#: REFUSED (REFUSE_UNEXPECTED_FIELD), never ignored: a path handed to
#: the daemon is a namespace-redirect attempt (the review R9 handle,
#: CEN_ROUTINGCRIT_DIR), and the daemon resolved its own paths at
#: construction.  `protocol` is on every request.
#:
#: `tool` takes exactly TWO fields.  `tool` is the tool NAME (a string)
#: and `args` is the tool's own argument OBJECT — and it carries TARGET
#: names, never host paths: the daemon's harness resolves `f1/sub/x`
#: against ITS OWN workspace (the same target gate `realtools` documents
#: at :85).  A raw or escaping path is refused BY THE HARNESS with a
#: typed code; a top-level field naming a ROOT (`tool_root`,
#: `sandbox_root`, `workspace`, ...) is not in this set and is refused by
#: the schema.  There is deliberately NO field that can move the daemon's
#: sandbox root, because the root never crosses.
ALLOWED_FIELDS: dict = {
    OP_PING: frozenset(),
    OP_CRIT: frozenset(),
    OP_ROUTE: frozenset({"turn", "stream", "law_f", "seat", "boundary"}),
    OP_HELDOUT_DEF: frozenset(),
    OP_HELDOUT_SCORE: frozenset({"checkpoint"}),
    OP_TOOL_EXEC: frozenset({"tool", "args"}),
}

#: OPERATIONS THAT DELIBERATELY DO NOT EXIST OVER THE SOCKET (Q2's
#: design-mode split, and the closure of the forged-publish path).  A
#: request naming one of these is refused BY NAME, so a client that
#: thinks it can publish learns it cannot (an `unknown_op` would leave
#: the door's absence implicit).
NOT_SERVED_OPS: frozenset = frozenset({
    "publish", "publish_criterion", "publish_heldout", "publish_definition",
    "reset", "ensure", "anchor", "key", "env", "reload_paths",
})

# -- TYPED REFUSAL CODES (never a traceback, never a daemon path) --------
REFUSE_BAD_FRAME = "bad_frame"
REFUSE_BAD_JSON = "bad_json"
REFUSE_BAD_REQUEST = "bad_request"
REFUSE_UNEXPECTED_FIELD = "unexpected_field"
REFUSE_UNKNOWN_OP = "unknown_op"
REFUSE_NOT_SERVED = "op_not_served"
REFUSE_UNAUTHORIZED = "unauthorized_peer"
REFUSE_PROTOCOL = "protocol_mismatch"
REFUSE_CRITERION = "criterion_refused"
REFUSE_HELDOUT = "heldout_refused"
REFUSE_TOOL = "tool_seat_refused"
REFUSE_INTERNAL = "internal"

#: WHAT THE EXEC OP'S FILE ARGUMENT IS.  A TARGET NAME (`f1`, `f1/sub/x`),
#: resolved by the DAEMON against its own workspace — never a host path.
#: Stated as a constant so the model is a DECLARED fact a reader can
#: check, not an inference from the code: `realtools.py:85-92` is the
#: discipline ("`f1`, `f2`, ... ARE DECLARED TARGETS, NOT PATHS") and this
#: op is that discipline at the socket.
TOOL_TARGET_MODEL = "target_name_resolved_by_daemon"

#: What the daemon's `heldout_score` refusal says — a STABLE TOKEN, not
#: prose (the seat-with-gap of the plan's Q6: held-out scoring executes
#: designer-side in v1, daemon-side when a campaign needs it).  The
#: daemon refuses the call rather than scoring against a state it cannot
#: rebuild: a score computed over a FRESH daemon-side engine would be a
#: silently different MEASUREMENT, which is worse than a refusal.
HELDOUT_SCORE_SEAT = "designer_side_in_v1"


class BoundaryUnavailable(ChainError):
    """FAIL-CLOSED (Q4).  The boundary could not answer: the socket is
    absent or refused the connect, the exchange failed or timed out, the
    response was malformed or spoke another protocol version, or the
    daemon refused the call.  `code` carries the typed refusal string
    (the daemon's own code on a refusal, else the shim's).  This is a
    ChainError because the run must STOP: no local fallback exists, and
    a silently degraded routing seat is the artifact R6 exists to
    prevent."""

    def __init__(self, message: str, code: str = "unavailable"):
        super().__init__(message)
        self.code = code


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    """A short read is a FAILURE, not a substring: the frame is
    length-prefixed, so a truncated body must refuse rather than be
    parsed as whatever JSON `json.loads` can salvage."""
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise OSError(f"peer closed after {len(buf)} of {n} bytes")
        buf += chunk
    return bytes(buf)


class BoundaryClient:
    """The mechanism-side shim (Q3).  One connection per call —
    stateless, so there is no session to drift and no cached criterion
    to serve a stale read: the R2 timescale (the criterion is read ONLY
    at a consolidation boundary) is enforced by WHERE the harness calls
    `crit()`, exactly as it was when the harness opened the file."""

    def __init__(self, socket_path: str | None = None, *,
                 timeout: float = 10.0,
                 protocol_version: int | None = None):
        self.path = (socket_path or os.environ.get(BOUNDARY_SOCKET_ENV)
                     or DEFAULT_BOUNDARY_SOCKET)
        self.timeout = float(timeout)
        self.protocol_version = int(protocol_version
                                    if protocol_version is not None
                                    else BOUNDARY_PROTOCOL_VERSION)

    # -- the transport ----------------------------------------------------
    def _exchange(self, req: dict) -> dict:
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        except OSError as e:                       # pragma: no cover
            raise BoundaryUnavailable(
                f"cannot create an AF_UNIX socket ({e})",
                code="socket_unavailable") from None
        sock.settimeout(self.timeout)
        try:
            try:
                sock.connect(self.path)
            except OSError as e:
                raise BoundaryUnavailable(
                    f"the boundary daemon is not reachable at "
                    f"{self.path!r} ({type(e).__name__}: {e}) — FAIL-CLOSED "
                    f"(Q4): no local fallback, the run stops",
                    code="connect_failed") from None
            payload = json.dumps(req, sort_keys=True).encode("utf-8")
            try:
                sock.sendall(HEADER.pack(len(payload)) + payload)
                (n,) = HEADER.unpack(_recv_exact(sock, HEADER.size))
                if n > MAX_FRAME_BYTES:
                    raise BoundaryUnavailable(
                        f"the daemon announced a {n}-byte frame (cap "
                        f"{MAX_FRAME_BYTES}) — refusing to read it",
                        code="bad_response_frame")
                body = _recv_exact(sock, n)
            except BoundaryUnavailable:
                raise
            except (OSError, socket.timeout) as e:
                raise BoundaryUnavailable(
                    f"the exchange with {self.path!r} failed "
                    f"({type(e).__name__}: {e}) — FAIL-CLOSED (Q4)",
                    code="io_failed") from None
        finally:
            try:
                sock.close()
            except OSError:                        # pragma: no cover
                pass
        try:
            resp = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise BoundaryUnavailable(
                "the daemon's response is not JSON — FAIL-CLOSED (Q4): a "
                "malformed answer is an unavailable boundary, never a "
                "silently-ignored one",
                code="malformed_response") from None
        if not isinstance(resp, dict) or "ok" not in resp:
            raise BoundaryUnavailable(
                "the daemon's response is not a boundary response "
                "(no 'ok' field) — FAIL-CLOSED (Q4)",
                code="malformed_response")
        if resp.get("protocol") != self.protocol_version:
            raise BoundaryUnavailable(
                f"protocol mismatch: the shim speaks "
                f"v{self.protocol_version}, the daemon answered "
                f"v{resp.get('protocol')!r} — refusing (no downgrade "
                f"negotiation; fail-closed)",
                code=REFUSE_PROTOCOL)
        if not resp["ok"]:
            raise BoundaryUnavailable(
                f"the boundary daemon refused {req.get('op')!r}: "
                f"{resp.get('error')!r} "
                f"(detail={resp.get('detail')!r}; daemon-side detail is "
                f"logged BY the daemon and is deliberately never returned "
                f"— a refusal must not leak the daemon's paths into the "
                f"mechanism's context)",
                code=str(resp.get("error")))
        return resp

    def _call(self, op: str, **fields) -> dict:
        req = {"op": op, "protocol": self.protocol_version}
        req.update(fields)
        return self._exchange(req)

    # -- the call set -----------------------------------------------------
    def ping(self) -> dict:
        """Liveness + the peer/daemon credential, for the runbook and the
        battery.  Returns no path or key."""
        return self._call(OP_PING)

    def crit(self) -> "object":
        """READ the criterion in force (R2: call this at a consolidation
        boundary, never per turn).  The body crosses as DATA — the
        mechanism routes on the criterion, so this read is BY DESIGN
        (residual R-a); what does NOT cross is the anchor, the ability
        to write, or any path.  Returns a routingcrit.RoutingCriterion
        reconstructed from the daemon's JSON, carrying the daemon's
        version — the object the checkpoint's `_routing_crit_version`
        reads."""
        from routingcrit import RoutingCriterion
        resp = self._call(OP_CRIT)
        body = resp.get("criterion")
        if not isinstance(body, dict):
            raise BoundaryUnavailable(
                "the daemon's crit response carries no criterion body",
                code="malformed_response")
        known = set(RoutingCriterion.__dataclass_fields__)
        missing = sorted(known - set(body))
        if missing:
            raise BoundaryUnavailable(
                f"the daemon's criterion body is missing "
                f"{missing} — refusing a partially-specified criterion",
                code="malformed_response")
        return RoutingCriterion(**{k: body[k] for k in known})

    def route(self, turn: int, stream: str, law_f,
              *, self_seat: bool = False, boundary: bool = False):
        """PLAN (Q2): hand the RAW STREAM over and receive the routed
        POSITIONS.  The EXTRACTION, the SpanState mapping, the selection
        rule and the [f_min, f_max] CLIP all happen in the daemon, so
        this process holds no selector to patch and chooses no fraction:
        `law_f` is the LAW's number (routing.py, model-derived) and it is
        an INPUT the daemon clips, never a selection the caller makes.
        `self_seat` names the grammar (the daemon resolves WHICH
        predicate set that means from ITS OWN tree) and `boundary` says
        "this turn is a consolidation boundary", i.e. RELOAD the
        criterion (R2's timescale, preserved across the boundary).

        Returns (positions, predicates): the positions AND the predicate
        set the daemon actually extracted with, so the caller can refuse
        a cross-tree grammar drift instead of mis-indexing its own
        extraction."""
        if not isinstance(stream, str):
            # never coerce: a non-str stream would be a DIFFERENT byte
            # sequence on the wire than the one the harness slices
            raise BoundaryUnavailable(
                f"route() takes the RAW stream (str); got "
                f"{type(stream).__name__} — refusing rather than coercing "
                f"(the extraction must be over the harness's own bytes)",
                code="bad_argument")
        resp = self._call(OP_ROUTE, turn=int(turn), stream=stream,
                          law_f=(None if law_f is None else float(law_f)),
                          seat=("self" if self_seat else "declared"),
                          boundary=bool(boundary))
        pos = resp.get("positions")
        preds = resp.get("predicates")
        if not isinstance(pos, list) or not all(
                isinstance(p, int) and not isinstance(p, bool) for p in pos):
            raise BoundaryUnavailable(
                f"the daemon's route response carries a non-integer "
                f"position list ({pos!r})",
                code="malformed_response")
        if not isinstance(preds, dict):
            raise BoundaryUnavailable(
                "the daemon's route response carries no predicate set",
                code="malformed_response")
        return tuple(pos), dict(preds)

    def heldout_definition(self) -> dict:
        """READ the held-out definition in force (the campaign-report
        read; residual R-a: the definition is mechanism-readable BY
        DESIGN, because the mechanism must be scored by it)."""
        return dict(self._call(OP_HELDOUT_DEF).get("definition") or {})

    def heldout_score(self, checkpoint) -> dict:
        """SCORE against the held-out definition.  v1's daemon REFUSES
        this call with the typed code HELDOUT_SCORE_SEAT (the plan's Q6
        seat-with-gap: the check needs the mechanism's CURRENT state and
        rebuilding a Stage2State inside the daemon would drag the
        harness's internals into the boundary process), so this method
        raises BoundaryUnavailable.  It exists — and forwards — so the
        seat is explicit and the wire format is fixed BEFORE the daemon
        grows the handler."""
        return self._call(OP_HELDOUT_SCORE, checkpoint=checkpoint)

    def tool(self, tool: str, args: dict | None = None) -> dict:
        """EXECUTE one tool request IN THE DAEMON'S PROCESS (v2), and
        return the daemon's own typed record as a dict.

        `tool` is a tool NAME (`read`/`write`/`edit`/`bash`/`run_tests`/
        `task_wait`) and `args` is that tool's argument object.  THE FILE
        ARGUMENTS ARE TARGET NAMES, NOT HOST PATHS (`f1/sub/x`): the
        daemon's harness resolves them against the workspace the DAEMON
        owns, and a raw or escaping path is REFUSED by that gate.  This
        process cannot name a root — there is no field for one.

        The record is `{"ok": bool, "tool": str, "turn": int, "code": str
        (a realtools REFUSALS code when refused), "text": str, "price": …,
        "unit": …, ...}` — the SAME shape `realtools.ToolHarness`
        produces, because the daemon runs that seat.

        TWO FAILURE CLASSES, deliberately distinct:
          * A BOUNDARY failure (transport, protocol, an unknown op, an
            unexpected field, an unauthorized peer, or the daemon's tool
            seat refusing the CALL) RAISES `BoundaryUnavailable` — the
            Q4 discipline: no local fallback, the run stops.
          * A TOOL refusal (the tool ran into its own policy/gate:
            `undeclared_tool`, `undeclared_target`, `outside_sandbox`, …)
            does NOT raise: it is a SUCCESSFUL boundary call whose
            executed tool refused, and it comes back as a record with
            `ok=False` and a typed `code` — exactly as `apply_turn` answers
            it in-process.  Raising here would make a refused tool
            indistinguishable from a dead daemon.
        """
        if not isinstance(tool, str) or not tool:
            raise BoundaryUnavailable(
                f"tool() takes a tool NAME (str); got "
                f"{type(tool).__name__} — refusing rather than coercing",
                code="bad_argument")
        if args is None:
            args = {}
        if not isinstance(args, dict):
            raise BoundaryUnavailable(
                f"tool() args must be an object (dict); got "
                f"{type(args).__name__}",
                code="bad_argument")
        resp = self._call(OP_TOOL_EXEC, tool=tool, args=args)
        rec = resp.get("record")
        if not isinstance(rec, dict) or "ok" not in rec:
            raise BoundaryUnavailable(
                f"the daemon's tool response carries no record "
                f"({sorted(resp)}); refusing a partially-specified answer",
                code="malformed_response")
        return dict(rec)
