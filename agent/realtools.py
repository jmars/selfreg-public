"""THE REAL-TOOL SURFACE (worker prerequisite 3, done properly) — hax's
five tools + the machinery that makes them powerful, on a carrier this
substrate can express, inside a sandbox inherited from task_eval.py.

THE SURFACE (behaviours copied from hax's own tools, read from
src/tools/*.c at /tmp/haxsrc — the shallow clone of
github.com/OleksandrChekhovskyi/hax, NOT from memory):

  read(path, offset, limit)   cat -n STYLE: every line prefixed with its
                              1-INDEXED line number and a "→" arrow; the
                              prefix is presentation only (hax read.c —
                              the arrow is READ_LINE_DELIM precisely so
                              it cannot be mistaken for indentation).
  write(path, content)        replaces the file, creates parent dirs,
                              returns a UNIFIED DIFF (write.c).
  edit(path, old_string,      SURGICAL exact-string replace; old_string
        new_string,           must occur EXACTLY ONCE unless
        replace_all)          replace_all — edit.c's rule verbatim;
                              returns a diff.
  bash(command, timeout_s,    combined stdout+stderr + exit code; a
        background, name)     default timeout, an override and a MAX;
                              background tasks with ids.
  task_wait(id, timeout_s,    waits on / kills a background task.
        kill)

THERE IS NO glob/grep/find TOOL — bash covers them (hax's deliberate
reduction; do not add file-search tools).

THE MACHINERY (the load-bearing part, all from hax src/tools/):
  OUTPUT CAPPING WITH SPILL: output is capped at LINES and per-LINE
  WIDTH with explicit elision markers, and an over-long stream keeps
  HEAD+TAIL with an "omitted N of M lines" marker reporting the TOTAL
  (bash_output.c: "spill must precede the hard drain limit so killed
  producers are reported as truncated"; the head/tail-with-marker shape
  is its model-visible form).
  LEXICAL SIDE-EFFECT CLASSIFICATION: a command whose leader is a
  read/list/search name and which carries no redirect, substitution or
  background operator is EXPLORATION and renders COLLAPSED; everything
  else renders full (bash_classify.c: "this lexical check may reject
  safe commands but must not hide obvious shell side effects").  It
  classifies the RENDER, never the permission.
  A RECURSION DEPTH CAP: every bash child carries REALTOOLS_SANDBOX=1
  and ToolHarness REFUSES to construct inside an environment that
  already carries it — no tools inside tools (bash_env.c's "a nested
  hax would truncate and then share the parent's live logs", enforced
  structurally instead of by env-scrubbing).
  BACKGROUND PROCESS MANAGEMENT: separate session per child (no
  controlling terminal, group kill on timeout), a task registry with
  ids, and task_wait (bash_process.c / task_registry.c).
  PATH RELATIVIZATION: results render paths RELATIVE to the sandbox
  root (path_preprocess.c) — the agent never sees the host temp path.

=======================================================================
THE CARRIER — A STRUCTURED, FENCED BLOCK IN THE PROSE (decided)
=======================================================================
`interleave.py` fixes the span grammar at `_ARG = ident|digits` and
says why: "no quoted strings ... the match is unambiguous by
construction, which is what makes the extractor TRIVIAL".  A tool call
needs STRUCTURED arguments (old_string/new_string/offset/limit/
replace_all), which that grammar cannot express, and widening it would
destroy the property the extractor rests on.  So a tool call rides a
FENCED BLOCK the harness parses:

    ```tool
    {"tool": "edit", "args": {"path": "f1/rchunk.py",
                              "old_string": "x", "new_string": "y"}}
    ```

This is faithful, not a workaround: `actions.py` already says an action
is an INTENT, not a claim, and tool calls are the same class one step
further.  interleave.py AND the span grammar are UNTOUCHED.  The prose
split stays TOTAL in the byte sense that matters here: the blocks STAY
IN THE PROSE (they are the agent's authored text; nothing is edited),
and parse_tool_blocks returns them beside a prose string that is the
input minus exactly the block bytes.  A malformed block is a TYPED
REFUSAL (malformed_block) returned as a result — never a silent ignore
(the agent could not distinguish it from success) and never a kill.

THE PROMPT MUST NAME THE SHAPES (MEASURED in this project: a placement
line naming only [done(tNN)] produced ZERO expect spans until it named
the real shapes): ToolHarness.manifest() renders the full tool list
with arguments AND a worked example, and build_prompt(tools_manifest=)
renders it (dmn_llm.py; zero bytes when unset).

`f1`, `f2`, ... ARE DECLARED TARGETS, NOT PATHS — the AdmissibleActions
discipline applied to capabilities: designer-supplied, EXTERNALLY
OWNED, DEFAULT EMPTY.  The first path component under the workspace
must be a declared target (or the reserved `scratch/` prefix, so the
agent can author scripts — hax's writers need somewhere to write);
anything else is a typed refusal (undeclared_target).  run_tests names
a target and is gated the same way.  bash has no target: its gate is
the sandbox + the classifier.

run_tests(task) IS KEPT — the evaluator IS "run the tests" on a SWE
task (worker prerequisite 2).  It rides the same block carrier, and
its typed verdict is rendered on the EXISTING dmn_ctx["tool_state"]
channel, which DOES render in the prompt (dmn_llm.py:1104 — the
paper-3 scope note's "the emitter cannot render it" is STALE and is
corrected by this change).  The agent sees the VISIBLE verdict only;
the held-out outcome stays in the record (out-of-band), because
per-turn held-out feedback is overfitting fuel, which is what C22b
exists to prevent.  The scored surface is exactly the task's MODULE as
the agent currently has it: ev.prepare() builds a fresh pristine copy
(test bytes pristine ALWAYS — deleting or editing the visible tests
cannot fake a pass) and the workspace's module bytes are overlaid.

=======================================================================
THE FIVE THINGS, STATED — NOT ASSUMED
=======================================================================
1. R6 IS FORCED HARDEST HERE, AND ITS STATUS CHANGED ON 2026-09-28: THE
   EXECUTOR IS NOW OWNED BY THE DAEMON.  `write` authors code; `bash`
   and `run_tests` execute it.  R6 v1 (boundary_daemon.py, CALL_AUTH)
   served NO op that runs a suite or a shell.  v2
   (BOUNDARY_PROTOCOL_VERSION 2) SERVES that op — `OP_TOOL_EXEC =
   "tool"` — and the daemon owns the harness, its workspace root (a
   mkdtemp in ITS process) and the declared surface (ITS argv, DEFAULT
   EMPTY); no request field can move any of them.  SO THE OLD SENTENCE
   MUST NOT BE REPEATED: these effects are not NECESSARILY in-process
   any more, and R6 is PARTLY closed.  WHAT IS CLOSED IS THE OWNERSHIP,
   NOT THE SANDBOX: item 4's residuals are UNCHANGED and stay open when
   the daemon runs the tools — MOVED, not removed, because the daemon
   runs as the same uid.  MEASURED against the daemon's own path by this
   battery's RT13: a bash call the DAEMON executes still reads the host
   tree outside the sandbox, the workspace root is still a /tmp mkdtemp
   (so the background-vs-scoring race is unchanged), and the only
   resource bound is still the timeout's process-group kill.  Nothing
   here claims the daemon's authority; v2 adds the SEAT, and the wiring
   choice (in-process vs the daemon) is the CALLER's — v2 converts no
   existing behaviour, so every arm of this battery still exercises the
   IN-PROCESS path.
2. PLANT-BLIND.  The frozen model has NO action term (MEASURED:
   dpdr/model.py dG/dt and da/dt read no action quantity), so every
   tool effect is invisible to the plant.  The battery asserts
   BIT-IDENTICAL plant trajectories with the surface on and off (the
   T6/complete discipline), and the C11 derivation ledger is never
   charged (unit separation, the T8 discipline).
3. THE ZERO-PRICING ARGUMENT DIES.  `complete` was priced ZERO because
   its effect was O(1) dict bookkeeping.  These effects are REAL WORK:
   every ToolRecord carries a PRICE and its UNIT — read/write/edit in
   BYTES (read: rendered bytes returned; write/edit: bytes written),
   bash in BYTES of captured output, run_tests in TESTS EXECUTED
   (never seconds-as-derivations; wall time is recorded separately as
   duration_s and never priced).  The agent's EMISSION price (the block
   bytes it authored) lands on the talking ledger's own unit (outward
   bytes); the effect prices are LOG-ONLY (with their units named) and
   never enter the C11 ledger.
4. THE ESCAPE RULE, AND WHAT THE SANDBOX DOES NOT CLOSE.  A path or
   command reaching outside the sandbox is a LOUD typed refusal
   (outside_sandbox), and read/write/edit NEVER touch the host tree —
   they act only inside the harness's own temp workspace.  bash runs
   under `unshare -rmn` when the host allows it: a NETWORK namespace
   (only a down `lo`) AND a MOUNT namespace with a tmpfs mounted over
   the pristine task tree (which is where the held-out bytes live) and
   over the scoring directory.  NOT CLOSED, stated: (a) same-uid — the
   child can in principle `umount` inside its own user namespace and
   read the hidden tree (the mount is default-deny VIEW, not a
   mandatory boundary; a real boundary needs the R6 uid split); (b) the
   REST of ~/thing stays readable from bash (the venv must, for the
   interpreter; criterion/anchors are the boundary daemon's residual,
   unchanged); (c) a background bash task can race a live scoring
   sandbox under /tmp (ephemeral, unpredictable path — stated); (d)
   resource exhaustion other than wall time (memory, disk, forks) is
   bounded only by the timeout's process-group kill.  Where the mount
   namespace is unavailable the bash record SAYS SO (fs_hide: none) —
   it does not pretend.
5. THE HELD-OUT SUITE STAYS OUT OF REACH (C22b/C22c).  The workspace
   copy EXCLUDES heldout/ by construction; read/write/edit refuse any
   path with a heldout component (heldout_forbidden) — asserted by the
   battery, including through symlinks and ..-escapes; bash's mount
   namespace hides the pristine tree that contains it (default-deny,
   residual in (4a)); run_tests shows the agent the visible verdict
   only.

MARKING.  MEASURED (on this host, by the battery
stage2_realtools_tests.py): every refusal code, the capping markers,
the diff shapes, the end-to-end loop, plant bit-identity, the held-out
unreachability.  INTERPRETATION: the mount-namespace hide as
default-deny (an active adversary inside the ns can umount).  NOT
BUILT / PROJECTION: nothing here is a model-fidelity claim (the plant
has no action input).  The OUT-OF-PROCESS OWNER IS NO LONGER UNBUILT:
v2's exec op exists (boundary_client.OP_TOOL_EXEC, the boundary
battery's B9, and RT13's per-residual re-derivation against the
daemon's own path); THIS module's path is still the IN-PROCESS one, and
which of the two runs is the CALLER's choice.  NO network calls, NO
live model runs — the surface is exercisable fully offline.

Run:  cd ~/thing/agent && PYTHONPATH=../dpdr:. \
      ~/thing/dpdr/.venv/bin/python stage2_realtools_tests.py [part ...]
"""
from __future__ import annotations

import difflib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections import deque
from dataclasses import dataclass, field

__all__ = [
    "TOOL_FENCE", "TOOL_SCHEMAS", "REFUSALS", "TOOL_BLOCK_RE",
    "ToolRefused", "ToolBlock", "ParsedStream", "ToolRecord",
    "ToolHarness", "parse_tool_blocks", "cap_output",
    "is_exploration_command", "manifest_text",
]

#: The fence that opens a tool block (```tool).  One fence, documented;
#: anything else fenced is prose.
TOOL_FENCE = "tool"

#: THE TOOL SCHEMAS — name -> {argument: type}, "?" suffix = optional.
#: The declared surface; the manifest renders it and apply refuses a
#: call naming a tool or argument type outside it.
TOOL_SCHEMAS: dict = {
    "read": {"path": "string", "offset": "integer?", "limit": "integer?"},
    "write": {"path": "string", "content": "string"},
    "edit": {"path": "string", "old_string": "string",
             "new_string": "string", "replace_all": "boolean?"},
    "bash": {"command": "string", "timeout_seconds": "integer?",
             "background": "boolean?", "name": "string?"},
    "task_wait": {"id": "string", "timeout_seconds": "integer?",
                  "kill": "boolean?"},
    "run_tests": {"task": "string"},
}

# -- TYPED REFUSAL CODES (a refusal is LOUD and typed, never a drop) -----
R_MALFORMED = "malformed_block"
R_UNDECLARED_TOOL = "undeclared_tool"
R_BAD_ARGS = "bad_args"
R_UNDECLARED_TARGET = "undeclared_target"
R_NO_TASK_MAP = "no_task_map"
R_NO_TASKS_ROOT = "no_tasks_root"
R_UNKNOWN_TASK = "unknown_task"
R_NO_PYTEST = "no_pytest"
R_OUTSIDE = "outside_sandbox"
R_HELDOUT = "heldout_forbidden"
R_TIMEOUT = "timeout"
R_UNKNOWN_BG = "unknown_task_id"
R_TOO_MANY_BG = "too_many_tasks"
R_BAD_NAME = "bad_name"
R_BINARY = "binary_file"
R_IO = "io_error"
R_NOT_FOUND = "old_string_not_found"
R_AMBIGUOUS = "old_string_ambiguous"
R_EMPTY_OLD = "empty_old_string"
R_NO_OP = "no_op_edit"
R_DEPTH = "recursion_depth"

#: Everything that can come back as a refusal code — a closed set the
#: battery can assert over (a refusal that is not typed is a bug).
REFUSALS: frozenset = frozenset({
    R_MALFORMED, R_UNDECLARED_TOOL, R_BAD_ARGS, R_UNDECLARED_TARGET,
    R_NO_TASK_MAP, R_NO_TASKS_ROOT, R_UNKNOWN_TASK, R_NO_PYTEST,
    R_OUTSIDE, R_HELDOUT, R_TIMEOUT, R_UNKNOWN_BG, R_TOO_MANY_BG,
    R_BAD_NAME, R_BINARY, R_IO, R_NOT_FOUND, R_AMBIGUOUS, R_EMPTY_OLD,
    R_NO_OP, R_DEPTH,
})

#: Output caps (hax output_cap.h's numbers: 2000 lines, 500 bytes/line;
#: the byte cap is this surface's context budget, smaller than hax's
#: because a tool result shares a prompt with the plant state).
CAP_LINES = 2000
CAP_LINE_WIDTH = 500

#: The arrow between a line number and the line (hax's READ_LINE_DELIM:
#: unlike whitespace it cannot be mistaken for indentation when copied).
LINE_DELIM = "→"

#: The reserved non-target prefix: the agent's scratch space (hax's
#: writers need somewhere to write that is not a task tree).
SCRATCH_PREFIX = "scratch"

#: The background-launch observation window (hax's
#: YIELD_EXIT_OBSERVE_MS, shortened): a command that finishes inside it
#: returns synchronously and creates no task.
_YIELD_OBSERVE_S = 0.3

#: Fixed setup run inside the mount namespace before the agent's
#: command: hide the pristine task tree and the scoring directory under
#: tmpfs, then exec the command from ENV (never from an interpolated
#: string — the command is untrusted and never touches the setup).
_MOUNT_SETUP = (
    'mount -t tmpfs tmpfs "$REALTOOLS_HIDE1" 2>/dev/null; '
    'mount -t tmpfs tmpfs "$REALTOOLS_HIDE2" 2>/dev/null; '
    'exec /bin/sh -c "$REALTOOLS_CMD"'
)


class ToolRefused(Exception):
    """A typed refusal: the tool did NOT run, and `code` says why (a
    closed vocabulary, REFUSALS).  Raised inside the harness and
    converted to an ok=False ToolRecord by apply_turn — callers never
    see an exception, they see the loud typed answer."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


# =========================================================================
# THE CARRIER — parse the fenced blocks out of a stream
# =========================================================================

TOOL_BLOCK_RE = re.compile(
    r"^[ \t]*```tool[ \t]*\n(.*?)\n[ \t]*```[ \t]*$",
    re.MULTILINE | re.DOTALL)


@dataclass(frozen=True)
class ToolBlock:
    """One fenced ```tool block.  `raw_ok` is False when the body is
    not parseable JSON of the right shape — the block still EXISTS (its
    bytes are in the prose) and apply_turn answers it with a typed
    malformed_block refusal."""
    body: str                  # the JSON text between the fences
    start: int                 # offsets in the ORIGINAL stream
    end: int
    tool: str = ""             # "" when raw_ok is False
    args: dict = field(default_factory=dict)
    raw_ok: bool = False
    reason: str = ""           # R_MALFORMED detail when not raw_ok

    @property
    def bytes_len(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class ParsedStream:
    """The total split of one DMN stream: the prose (the input minus
    exactly the block bytes — splice-back reproduces the input) plus the
    blocks, in order.  The prose still CONTAINS the blocks by the time
    it is persisted (the blocks are the agent's authored text and stay
    in self_content); this object is the harness's VIEW, not an edit."""
    prose: str
    blocks: tuple


def parse_tool_blocks(stream: str) -> ParsedStream:
    """Split `stream` into (prose-with-blocks-removed, blocks).  Never
    raises: an unparseable body is a ToolBlock with raw_ok=False, and
    apply_turn answers it with a typed refusal."""
    blocks: list = []
    prose: list = []
    pos = 0
    for m in TOOL_BLOCK_RE.finditer(stream):
        body = m.group(1)
        blocks.append(ToolBlock(body=body, start=m.start(), end=m.end(),
                                **_parse_body(body)))
        prose.append(stream[pos:m.start()])
        pos = m.end()
    prose.append(stream[pos:])
    return ParsedStream(prose="".join(prose), blocks=tuple(blocks))


def _parse_body(body: str) -> dict:
    """Structural parse of one block body: a JSON object with a string
    `tool` and an optional object `args`.  Anything else is
    malformed_block with a short reason (deterministic, no tracebacks)."""
    try:
        obj = json.loads(body)
    except ValueError as e:
        return {"raw_ok": False, "reason": f"not JSON: {e}"}
    if not isinstance(obj, dict):
        return {"raw_ok": False,
                "reason": f"not an object ({type(obj).__name__})"}
    tool = obj.get("tool")
    if not isinstance(tool, str) or not tool:
        return {"raw_ok": False, "reason": "'tool' must be a non-empty string"}
    args = obj.get("args", {})
    if args is None:
        args = {}
    if not isinstance(args, dict):
        return {"raw_ok": False,
                "reason": f"'args' must be an object ({type(args).__name__})"}
    return {"raw_ok": True, "tool": tool, "args": dict(args)}


# =========================================================================
# THE MACHINERY — capping, classification
# =========================================================================

def cap_output(text: str, cap_bytes: int) -> str:
    """Cap a tool-result body THREE ways, each with an explicit marker
    (output_cap.c + bash_output.c's model-visible shape):
      1. LINES: over CAP_LINES keeps head+tail halves with an
         'omitted N of M lines' marker (the total is always reported —
         a killed producer is reported as truncated, never silently
         shortened);
      2. LINE WIDTH: each over-long line keeps its first CAP_LINE_WIDTH
         bytes + '...[K bytes elided]';
      3. BYTES: the rendered body is trimmed to cap_bytes with a final
         truncation marker.
    The marker TEXT is part of the contract (the battery asserts it)."""
    if not text:
        return text
    lines = text.split("\n")
    n = len(lines)
    if n > CAP_LINES:
        keep = CAP_LINES // 2
        head, tail = lines[:keep], lines[-keep:]
        omitted = n - 2 * keep
        lines = (head + [f"... [output truncated: omitted {omitted} of "
                         f"{n} lines; totals reported below] ..."] + tail)
    out = []
    for ln in lines:
        if len(ln) > CAP_LINE_WIDTH:
            out.append(ln[:CAP_LINE_WIDTH]
                       + f"...[{len(ln) - CAP_LINE_WIDTH} bytes elided]")
        else:
            out.append(ln)
    body = "\n".join(out)
    if len(body) > cap_bytes:
        body = (body[:cap_bytes]
                + f"\n[truncated at {cap_bytes} of {len(body)} bytes]")
    return body


def _has_shell_disqualifier(command: str) -> bool:
    """Lexical check, copied in shape from bash_classify.c: a
    redirect, command substitution, heredoc or background operator
    disqualifies the exploration classification.  QUOTING IS RESPECTED
    (a '>' inside quotes is not a redirect); this classifies the
    RENDER only — it never gates permission."""
    quote = 0
    i = 0
    while i < len(command):
        c = command[i]
        if quote:
            if quote == '"' and c == "\\" and i + 1 < len(command):
                i += 2
                continue
            if c == quote:
                quote = 0
            elif quote == '"' and (c == "`"
                                   or (c == "$" and command[i + 1:i + 2] == "(")):
                return True
            i += 1
            continue
        if c in "'\"":
            quote = c
        elif c == "\\" and i + 1 < len(command):
            i += 1
        elif c == "`" or (c == "$" and command[i + 1:i + 2] == "("):
            return True
        elif c in "<>":
            if command[i + 1:i + 2] == "(":
                return True
            if c == "<" and command[i + 1:i + 2] == "<":
                return True
            if c == ">":
                return True
        elif c == "&":
            if command[i + 1:i + 2] == "&":
                i += 1                      # `&&` is sequencing, not a
                                            # background operator; the
                                            # segment walk classifies
                                            # each conjoined command
            else:
                return True
        i += 1
    return False


_READ_LEADERS = frozenset({"cat", "less", "more", "nl"})
_LIST_LEADERS = frozenset({"ls", "eza", "exa", "tree", "find", "fd", "stat",
                           "file", "pwd", "realpath", "readlink", "which",
                           "whereis", "basename", "dirname", "du", "df",
                           "id", "whoami", "hostname", "uname"})
_SEARCH_LEADERS = frozenset({"grep", "egrep", "fgrep", "rg", "ag", "ack"})
#: Format filters and inert printers (bash_classify.c): they only print,
#: never decide the verdict.  A filter WITH a non-flag operand reads a
#: file (substantive); without one it needs an upstream producer and
#: contributes nothing substantive itself.
_FILTER_LEADERS = frozenset({"wc", "sort", "uniq", "cut", "tr", "awk",
                             "sed", "head", "tail", "tac", "rev", "fold",
                             "expand", "unexpand", "paste", "comm", "join",
                             "column"})
_INERT_LEADERS = frozenset({"echo", "printf", "true", "false", ":"})
_NEUTRAL_WORDS = frozenset({"then", "else", "fi", "do", "done", "if",
                            "while", "for", "until", "case", "esac", "!",
                            "{", "}", "&&", "||", "in"})
#: Short options that consume the NEXT token, per leader (the shape of
#: bash_classify.c's COMMAND_SPECS.value_options).
_VALUE_OPTS: dict = {"grep": "ABCDdmef", "egrep": "ABCDdmef",
                     "fgrep": "ABCDdmef", "rg": "ABCmtg", "ag": "ABCm",
                     "ack": "ABCm", "head": "nc", "tail": "nc",
                     "sort": "kStTo", "uniq": "fsw", "cut": "bcdf",
                     "sed": "e", "awk": "v", "join": "112teoav"}
#: Operands a leader needs before it READS a file (bash_classify.c's
#: required_operands: the grep family's first operand is a PATTERN).
_MIN_OPERANDS: dict = {"cat": 1, "less": 1, "more": 1, "nl": 1,
                       "grep": 2, "egrep": 2, "fgrep": 2,
                       "rg": 1, "ag": 1, "ack": 1,
                       "head": 1, "tail": 1, "wc": 1, "sed": 2, "awk": 2,
                       "join": 2}


def is_exploration_command(command: str) -> bool:
    """True when the command only LOOKS: every pipe segment's leader is
    a read/list/search name (or a filter/inert printer over an upstream
    producer), no segment carries a shell side effect, and at least one
    segment is SUBSTANTIVE (reads something — `echo x | grep y` is not
    exploration in hax either: nothing is read).  Its result renders
    COLLAPSED.  May reject safe commands; must not hide obvious side
    effects (bash_classify.c)."""
    if not command or _has_shell_disqualifier(command):
        return False
    substantive = False
    for statement in re.split(r"[;\n]", command):
        has_producer = False
        # `&&`/`||` are statement separators for classification too:
        # every conjoined command must itself only look (hiding the
        # second arm of `cat x && rm -rf /` would be exactly the
        # side-effect-hiding the hax comment forbids)
        for seg in re.split(r"&&|\|\||\|", statement):
            words = seg.split()
            while words and ("=" in words[0]
                             and re.match(r"^[A-Za-z_]", words[0])):
                words = words[1:]                # env assignments: neutral
            if not words:
                continue
            leader = words[0]
            if leader in _NEUTRAL_WORDS:
                continue
            # Non-flag operands; for grep/rg-family the PATTERN is not
            # a file (bash_classify.c: "grep requires a pattern and
            # file"), and a value-taking short option consumes the next
            # token (`grep -A3 x y`: -A3 takes nothing, x is the
            # pattern, y is the file).
            value_opts = _VALUE_OPTS.get(leader, "")
            take_next = False
            operands = 0
            for w in words[1:]:
                if take_next:
                    take_next = False
                    continue
                if w.startswith("-") and w != "-":
                    if not w.startswith("--"):
                        body = w[1:]
                        if body and body[-1] in value_opts:
                            take_next = True
                    continue
                operands += 1
            if leader in (_READ_LEADERS | _LIST_LEADERS | _SEARCH_LEADERS):
                need = _MIN_OPERANDS.get(leader, 1)
                if operands >= need:
                    substantive = True
                    has_producer = True
                elif not has_producer:
                    return False
                has_producer = True
            elif leader in _FILTER_LEADERS:
                # a filter with its own operand reads a file; without
                # one it needs an upstream producer or it would block
                if operands:
                    substantive = True
                elif not has_producer:
                    return False
                has_producer = True
            elif leader in _INERT_LEADERS:
                # an inert head prints its arguments and reads nothing
                # (echo x alone is NOT exploration); it only keeps
                # downstream filters from blocking
                has_producer = True
            else:
                return False
    return substantive


# =========================================================================
# THE RECORD
# =========================================================================

@dataclass
class ToolRecord:
    """One tool call's answer.  ok=False ONLY for refusals (the tool did
    not run: policy, malformed, unknown); a command that RAN and failed
    (exit != 0, failing tests) is ok=True with its outcome in the text —
    conflating the two would make a failing test indistinguishable from
    a refused call."""
    call_id: str
    tool: str
    turn: int
    ok: bool
    code: str = ""                 # "" | a REFUSALS code
    detail: str = ""
    text: str = ""                 # the capped result body
    price: float = 0.0             # REAL WORK, in `unit` — never free
    unit: str = ""                 # bytes_read|bytes_written|bytes|tests
    effect_bytes: int = 0          # the rendered body's size (log-only)
    duration_s: float = 0.0        # wall time, RECORDED never priced
    exit_code: int | None = None
    network: str = ""              # netns | none
    fs_hide: str = ""              # mount-ns | none

    def header(self) -> str:
        if self.ok:
            tag = f"[{self.call_id} ok] {self.tool}"
        else:
            tag = f"[{self.call_id} REFUSED {self.code}] {self.tool}"
        if self.exit_code is not None:
            tag += f" (exit {self.exit_code}"
            if self.duration_s:
                tag += f", {self.duration_s:.2f}s"
            tag += ")"
        return tag

    def render(self) -> str:
        head = self.header()
        if self.detail and not self.text:
            head += f": {self.detail}"
        return f"{head}\n{self.text}" if self.text else head


# =========================================================================
# THE SANDBOX HARNESS
# =========================================================================

class _BgTask:
    """One background bash task: a session-isolated child, a reader
    thread filling a capped buffer, and the id the agent waits on."""

    def __init__(self, tid, name, proc, cap):
        self.id = tid
        self.name = name or tid
        self.proc = proc
        self.buf = _CappedBuffer(cap)
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.exit_code: int | None = None
        self.started = time.time()
        self.thread.start()

    def _read(self):
        fd = self.proc.stdout.fileno()
        while True:
            try:
                chunk = os.read(fd, 65536)
            except (OSError, ValueError):
                break
            if not chunk:
                break
            self.buf.append(chunk.decode("utf-8", "replace"))
        try:
            self.exit_code = self.proc.wait()
        except Exception:                        # noqa: BLE001
            self.exit_code = -1

    @property
    def done(self) -> bool:
        return not self.thread.is_alive()


class _CappedBuffer:
    """Head+tail accumulation with totals: bounded memory for an
    unbounded producer, and the TOTALS are always reportable so a
    killed/spilling producer is reported as truncated (bash_output.c)."""

    def __init__(self, cap_bytes: int):
        self.cap = int(cap_bytes)
        self.head = ""
        self.tail: deque = deque()
        self.tail_len = 0
        self.dropped_mid = 0
        self.total = 0

    def append(self, s: str):
        self.total += len(s)
        room = self.cap // 2 - len(self.head)
        if room > 0:
            take = s[:room]
            self.head += take
            s = s[len(take):]
            if not s:
                return
        self.tail.append(s)
        self.tail_len += len(s)
        while self.tail_len > self.cap // 2 and len(self.tail) > 1:
            drop = self.tail.popleft()
            self.dropped_mid += len(drop)
            self.tail_len -= len(drop)

    def render(self) -> tuple:
        mid = (f"\n... [{self.dropped_mid} mid bytes omitted of "
               f"{self.total} total] ...\n" if self.dropped_mid else "")
        return self.head + mid + "".join(self.tail), self.total


class ToolHarness:
    """The world's tool surface: parse the blocks, run the effects in
    the sandbox, answer with typed records.  CONSTRUCTED BY THE DESIGNER
    (cfg.tools) — the declared target set, the task map and the allowed
    tools are construction parameters the mechanism never widens (the
    AdmissibleActions discipline, applied to capabilities)."""

    def __init__(self, targets=(), task_map=None, tasks_root=None, *,
                 allowed_tools=None, python: str | None = None,
                 network: str = "auto",
                 run_timeout: float = 60.0,
                 bash_timeout: float = 10.0,
                 bash_timeout_max: float = 120.0,
                 wait_timeout: float = 30.0,
                 max_running: int = 4,
                 tool_cap_bytes: int = 12000,
                 keep: bool = False):
        # THE RECURSION DEPTH CAP: no tools inside tools.  Every bash
        # child carries the marker env var; a harness constructed there
        # refuses (bash_env.c's nested-hax discipline, structural).
        if os.environ.get("REALTOOLS_SANDBOX"):
            raise ToolRefused(
                R_DEPTH,
                "REALTOOLS_SANDBOX is set: a tool harness may not be "
                "constructed inside a tool sandbox (depth cap 1)")
        self.root = tempfile.mkdtemp(prefix="realtools-")
        self.workspace = os.path.join(self.root, "workspace")
        self.scoring = os.path.join(self.root, "scoring")
        self.home = os.path.join(self.root, "home")
        self.tmpdir = os.path.join(self.root, "tmp")
        for d in (self.workspace, self.scoring, self.home, self.tmpdir):
            os.makedirs(d, exist_ok=True)
        self.targets = frozenset(str(t) for t in targets)
        self.task_map = dict(task_map or {})
        self.tasks_root = os.path.abspath(tasks_root) if tasks_root else None
        self._allowed = (frozenset(TOOL_SCHEMAS) if allowed_tools is None
                         else frozenset(allowed_tools))
        self._python_arg = python
        self._network_mode = network
        self.run_timeout = float(run_timeout)
        self.bash_timeout = float(bash_timeout)
        self.bash_timeout_max = float(bash_timeout_max)
        self.wait_timeout = float(wait_timeout)
        self.max_running = int(max_running)
        self.tool_cap_bytes = int(tool_cap_bytes)
        self.keep = bool(keep)
        self._python: str | None | bool = False   # False = unresolved
        self._evaluator = None
        self._specs = None
        self._ns: tuple | None = None
        self._bg: dict = {}
        self._bg_seq = 0
        self.history: list = []       # every record ever (the log)
        self._pending: list = []      # records not yet rendered back

    # -- construction of the workspace --------------------------------
    def _materialise(self):
        """One fresh copy per DECLARED target: the task tree WITHOUT
        heldout/ and without caches — the agent's tree, the only tree
        the file tools touch.  IDEMPOTENT: a second call (a resume's
        construction path re-runs it) does not clobber a workspace the
        agent has already edited — that would reset the run's state.
        Only MISSING targets are materialised."""
        if not self.tasks_root:
            return
        for f in sorted(self.targets):
            if os.path.exists(os.path.join(self.workspace, f)):
                continue                    # already materialised (a
                                                # resume): keep the edits
            task = self.task_map.get(f)
            if not task:
                continue
            src = os.path.join(self.tasks_root, task)
            if not os.path.isdir(src):
                continue
            shutil.copytree(src, os.path.join(self.workspace, f),
                            ignore=shutil.ignore_patterns(
                                "heldout", "__pycache__", "*.pyc",
                                ".pytest_cache"))

    # -- the manifest (the prompt's tool explanation) -------------------
    def manifest(self) -> str:
        """The placement text the PROMPT renders (the MEASURED lesson:
        a placement line that does not name the real shapes yields zero
        of them — so this names every tool, its arguments, and gives a
        worked example)."""
        return manifest_text(sorted(self.targets))

    # -- turn application ------------------------------------------------
    def apply_turn(self, turn: int, blocks) -> tuple:
        """Answer every block of one turn, in order.  NEVER raises: a
        malformed block, an undeclared tool and every refusal become an
        ok=False record the next turn renders back (a silent drop would
        be indistinguishable from success)."""
        records = []
        for i, b in enumerate(blocks):
            rec = self._answer(turn, i, b)
            records.append(rec)
            self.history.append(rec)
            self._pending.append(rec)
        return tuple(records)

    def _answer(self, turn: int, i: int, b: ToolBlock) -> ToolRecord:
        cid = f"tool-{turn}-{i}"
        t0 = time.time()
        if not b.raw_ok:
            return self._refused(cid, "(unparseable)", turn, R_MALFORMED,
                                 b.reason)
        if b.tool not in self._allowed:
            return self._refused(
                cid, b.tool, turn, R_UNDECLARED_TOOL,
                f"not one of the served tools {sorted(self._allowed)}")
        handler = getattr(self, f"_tool_{b.tool}", None)
        if handler is None:
            return self._refused(cid, b.tool, turn, R_UNDECLARED_TOOL,
                                 f"unknown tool {b.tool!r}")
        try:
            return handler(cid, turn, b.args, t0)
        except ToolRefused as e:
            return self._refused(cid, b.tool, turn, e.code, e.detail)
        except Exception as e:                    # noqa: BLE001
            # an unexpected failure is LOUD and typed, never a crash of
            # the turn: the agent sees io_error with the exception name.
            return self._refused(cid, b.tool, turn, R_IO,
                                 f"{type(e).__name__}: {e}")

    def _refused(self, cid, tool, turn, code, detail) -> ToolRecord:
        return ToolRecord(call_id=cid, tool=tool, turn=turn, ok=False,
                          code=code, detail=str(detail)[:500])

    # -- the reply --------------------------------------------------------
    def render_reply(self) -> str:
        """The world's tool reply for the NEXT turn's state channel:
        every unanswered record, rendered and capped.  Consumes the
        pending list (each result is shown exactly once)."""
        if not self._pending:
            return ""
        lines = ["TOOLS — results of your last tool calls:"]
        for r in self._pending:
            lines.append(r.render())
        self._pending = []
        return cap_output("\n".join(lines), self.tool_cap_bytes)

    # -- path resolution: the target gate + the sandbox + heldout -------
    def _resolve(self, raw, *, label: str) -> str:
        if not isinstance(raw, str) or not raw:
            raise ToolRefused(R_BAD_ARGS, f"'{label}' must be a non-empty "
                                          f"string")
        if "\x00" in raw:
            raise ToolRefused(R_BAD_ARGS, f"'{label}' contains a NUL byte")
        if raw.startswith("~"):
            raise ToolRefused(R_OUTSIDE,
                              "'~' paths are refused: stay inside the "
                              "sandbox (a declared target or scratch/)")
        p = raw if os.path.isabs(raw) else os.path.join(self.workspace, raw)
        p = os.path.normpath(p)
        # INSIDE the sandbox root only (the escape rule, loud)
        if p != self.root and not p.startswith(self.root + os.sep):
            raise ToolRefused(
                R_OUTSIDE,
                f"{raw!r} resolves outside the sandbox "
                f"({self._rel(p)}); the tools never touch the host tree")
        # THE TARGET GATE: the first workspace component is the target
        rel = os.path.relpath(p, self.workspace)
        if rel.startswith(".."):
            raise ToolRefused(R_OUTSIDE,
                              f"{raw!r} is not under the workspace")
        head = rel.split(os.sep)[0]
        if head not in self.targets and head != SCRATCH_PREFIX:
            have = (f"declared: {', '.join(sorted(self.targets))}"
                    if self.targets else "the declared target set is EMPTY")
            raise ToolRefused(
                R_UNDECLARED_TARGET,
                f"{raw!r} names {head!r}, which is not a declared target "
                f"({have}; {SCRATCH_PREFIX}/ is the scratch space)")
        # THE HELD-OUT RULE (C22b/C22c): no path component may be the
        # held-out directory, WHATEVER its spelling — checked on the
        # NORMALIZED path, before any filesystem access, so it holds for
        # nonexistent files too.
        parts = p.split(os.sep)
        if "heldout" in parts:
            raise ToolRefused(
                R_HELDOUT,
                f"{raw!r} names the held-out directory — the held-out "
                f"suite is out of reach by construction (C22b)")
        # SYMLINK CONTAINEMENT: no component of the resolved path may be
        # a symlink (a link planted inside the sandbox pointing out is
        # an escape, and following it would leave the sandbox).
        cur = os.sep
        for part in p.split(os.sep)[1:]:
            cur = os.path.join(cur, part)
            if cur in (os.sep, self.root):
                continue
            if os.path.islink(cur):
                raise ToolRefused(R_OUTSIDE,
                                  f"a symlink sits in the path ({cur}) — "
                                  f"resolved paths must stay real")
        return p

    def _rel(self, p: str) -> str:
        """Path relativization (path_preprocess.c): results render
        sandbox-relative paths, never the host temp path."""
        try:
            return os.path.relpath(p, self.root)
        except ValueError:
            return p

    # -- the tools ---------------------------------------------------------
    def _tool_read(self, cid, turn, args, t0) -> ToolRecord:
        path = self._resolve(args.get("path"), label="path")
        offset = _opt_int(args, "offset", 1)
        limit = _opt_int(args, "limit", 0)
        if not os.path.isfile(path):
            raise ToolRefused(R_IO, f"{self._rel(path)}: no such file")
        data = open(path, "rb").read(1 << 20)
        if b"\x00" in data[:8192]:
            raise ToolRefused(R_BINARY,
                              f"{self._rel(path)} appears to be binary "
                              f"(NUL byte in first 8 KiB)")
        text = data.decode("utf-8", "replace")
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines = lines[:-1]
        total = len(lines)
        start = max(1, offset) - 1
        end = start + limit if limit > 0 else total
        chunk = lines[start:end]
        body = "\n".join(f"{n:>6}{LINE_DELIM}{ln}"
                         for n, ln in enumerate(chunk, start=start + 1))
        hdr = (f"lines {start + 1}-{min(end, total)} of {total}"
               if total else "(empty file)")
        if start >= total and total:
            body = f"(file has {total} line{'s' if total != 1 else ''}; " \
                   f"offset {offset} is past EOF)"
            hdr = ""
        body = cap_output(body, self.tool_cap_bytes)
        return ToolRecord(
            call_id=cid, tool="read", turn=turn, ok=True,
            text=(f"{self._rel(path)} {hdr}\n{body}" if hdr else body),
            price=len(body.encode()), unit="bytes_read",
            effect_bytes=len(body.encode()),
            duration_s=time.time() - t0)

    def _tool_write(self, cid, turn, args, t0) -> ToolRecord:
        path = self._resolve(args.get("path"), label="path")
        content = args.get("content")
        if not isinstance(content, str):
            raise ToolRefused(R_BAD_ARGS, "'content' must be a string")
        old = None
        if os.path.exists(path):
            if not os.path.isfile(path):
                raise ToolRefused(R_IO, f"{self._rel(path)} is not a "
                                        f"regular file")
            old = open(path, "r", encoding="utf-8",
                       errors="replace").read()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        rel = self._rel(path)
        if old is None:
            nlines = content.count("\n") + (1 if content else 0)
            text = (f"created {rel} (empty)" if not content
                    else f"created {rel} ({nlines} line"
                         f"{'s' if nlines != 1 else ''}, "
                         f"{len(content.encode())} bytes)")
        else:
            text = f"wrote {rel}\n{cap_output(_diff(old, content, rel), self.tool_cap_bytes)}"
        return ToolRecord(call_id=cid, tool="write", turn=turn, ok=True,
                          text=text, price=len(content.encode()),
                          unit="bytes_written",
                          effect_bytes=len(text.encode()),
                          duration_s=time.time() - t0)

    def _tool_edit(self, cid, turn, args, t0) -> ToolRecord:
        path = self._resolve(args.get("path"), label="path")
        old_s = args.get("old_string")
        new_s = args.get("new_string")
        if not isinstance(old_s, str) or not isinstance(new_s, str):
            raise ToolRefused(R_BAD_ARGS, "'old_string'/'new_string' must "
                                          f"be strings")
        replace_all = args.get("replace_all", False)
        if not isinstance(replace_all, bool):
            raise ToolRefused(R_BAD_ARGS, "'replace_all' must be a boolean")
        if not old_s:
            raise ToolRefused(R_EMPTY_OLD, "'old_string' must be non-empty")
        if old_s == new_s:
            raise ToolRefused(R_NO_OP, "'old_string' and 'new_string' are "
                                       "identical — nothing to do")
        if not os.path.isfile(path):
            raise ToolRefused(R_IO, f"{self._rel(path)}: no such file "
                                    f"(edit needs an existing file)")
        src = open(path, "r", encoding="utf-8", errors="replace").read()
        count = src.count(old_s)
        if count == 0:
            raise ToolRefused(R_NOT_FOUND, "'old_string' not found in "
                                           f"{self._rel(path)}")
        if count > 1 and not replace_all:
            raise ToolRefused(
                R_AMBIGUOUS,
                f"'old_string' matches {count} places in {self._rel(path)} "
                f"— provide more context to disambiguate, or set "
                f"replace_all=true")
        new_src = (src.replace(old_s, new_s) if replace_all
                   else src.replace(old_s, new_s, 1))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_src)
        rel = self._rel(path)
        text = (f"edited {rel} ({count if replace_all else 1} change"
                f"{'s' if replace_all and count != 1 else ''})\n"
                + cap_output(_diff(src, new_src, rel), self.tool_cap_bytes))
        return ToolRecord(call_id=cid, tool="edit", turn=turn, ok=True,
                          text=text, price=len(new_src.encode()),
                          unit="bytes_written",
                          effect_bytes=len(text.encode()),
                          duration_s=time.time() - t0)

    # -- bash -----------------------------------------------------------
    def _namespace(self) -> tuple:
        """(prefix_argv, hide_mounts, note) — the strongest namespace
        set the host allows, probed ONCE and cached.  `unshare -rmn`
        gives a user+mount+net namespace: the mount half is what hides
        the pristine task tree (where the held-out bytes live) from
        bash; the net half is the network closure (task_eval's
        discipline: a namespace, not an env var).  When the mount half
        is unavailable bash still runs, and every bash record SAYS
        fs_hide: none — it does not pretend."""
        if self._ns is not None:
            return self._ns
        unshare = shutil.which("unshare")
        prefix: tuple = ()
        hide = False
        net = False
        if unshare and self._network_mode != "off":
            try:
                probe = subprocess.run(
                    [unshare, "-rmn", "/bin/sh", "-c",
                     'mount -t tmpfs tmpfs "$REALTOOLS_HIDE1" && echo ok'],
                    env={**os.environ, "REALTOOLS_HIDE1": self.scoring},
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    timeout=15)
                if probe.returncode == 0 and b"ok" in probe.stdout:
                    prefix, hide, net = (unshare, "-rmn"), True, True
            except Exception:                    # noqa: BLE001
                pass
            if not prefix:
                try:
                    ok = subprocess.run([unshare, "-rn", "true"],
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,
                                        timeout=10).returncode == 0
                    if ok:
                        prefix, net = (unshare, "-rn"), True
                except Exception:                # noqa: BLE001
                    pass
        note = ("user+mount+net namespace (unshare -rmn): tmpfs over the "
                "pristine task tree and the scoring dir; netns with only "
                "a down lo" if hide else
                "network namespace only (unshare -rn): the pristine task "
                "tree is NOT hidden from bash — residual stated" if net
                else "NO namespace available: neither network nor "
                     "filesystem hiding is enforced — residual stated")
        self._ns = (prefix, hide, note)
        return self._ns

    def _interpreter(self) -> str | None:
        """The interpreter that can run pytest (task_eval.find_python,
        INHERITED — resolution order and the no-runner refusal are
        already built and tested there).  Cached; None when none was
        found (run_tests then refuses no_pytest, bash just loses the
        venv on PATH)."""
        if self._python is False:
            try:
                import task_eval
                self._python = task_eval.find_python(self._python_arg)
            except Exception:                    # noqa: BLE001
                self._python = None
        return self._python  # type: ignore[return-value]

    def _bash_env(self, command: str) -> dict:
        path = "/usr/bin:/bin"
        py = self._interpreter()
        if py:
            path = f"{os.path.dirname(py)}:{path}"
        env = {
            "PATH": path, "HOME": self.home, "TMPDIR": self.tmpdir,
            "LC_ALL": "C.UTF-8", "TERM": "dumb",
            "PAGER": "cat", "EDITOR": "false",
            "PYTHONUNBUFFERED": "1",
            # the recursion-depth marker (see __init__) and the command
            # channel for the mount-ns setup (never interpolated).
            "REALTOOLS_SANDBOX": "1",
            "REALTOOLS_CMD": command,
        }
        if self.tasks_root:
            env["REALTOOLS_HIDE1"] = self.tasks_root
        env["REALTOOLS_HIDE2"] = self.scoring
        return env

    def _spawn(self, command: str):
        """Spawn the agent's command in the strongest sandbox this host
        allows: a separate session (no controlling terminal; the group
        is killable), combined stdout+stderr, cwd = the workspace."""
        prefix, hide, _ = self._namespace()
        env = self._bash_env(command)
        if hide:
            argv = [*prefix, "/bin/sh", "-c", _MOUNT_SETUP]
        else:
            argv = [*prefix, "/bin/sh", "-c", command]
        return subprocess.Popen(argv, cwd=self.workspace, env=env,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                start_new_session=True), hide

    def _tool_bash(self, cid, turn, args, t0) -> ToolRecord:
        command = args.get("command")
        if not isinstance(command, str) or not command.strip():
            raise ToolRefused(R_BAD_ARGS, "'command' must be a non-empty "
                                          f"string")
        timeout = _opt_int(args, "timeout_seconds", 0)
        if timeout < 0:
            raise ToolRefused(R_BAD_ARGS,
                              "'timeout_seconds' must be >= 1 (0 is not "
                              "a timeout — omit the argument for the "
                              "default)")
        if timeout:
            timeout = min(float(timeout), self.bash_timeout_max)
        else:
            timeout = self.bash_timeout
        background = args.get("background", False)
        if not isinstance(background, bool):
            raise ToolRefused(R_BAD_ARGS, "'background' must be a boolean")
        name = args.get("name")
        if name is not None:
            if not isinstance(name, str) or not name:
                name = None
            elif not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", name):
                raise ToolRefused(R_BAD_NAME,
                                  f"'name' {name!r} is not 1-32 of "
                                  f"[A-Za-z0-9_-]")
        net_note = ("netns" if self._namespace()[0] else "none")
        hide_note = "mount-ns" if self._namespace()[1] else "none"

        if background:
            running = [t for t in self._bg.values() if not t.done]
            if len(running) >= self.max_running:
                raise ToolRefused(
                    R_TOO_MANY_BG,
                    f"too many running tasks (max {self.max_running}): "
                    f"wait on or kill one first "
                    f"(running: {sorted(t.id for t in running)})")
            proc, hide = self._spawn(command)
            self._bg_seq += 1
            tid = f"t{self._bg_seq}"
            task = _BgTask(tid, name or "", proc, self.tool_cap_bytes * 2)
            self._bg[tid] = task
            task.thread.join(_YIELD_OBSERVE_S)
            if task.done:
                # finished inside the window: synchronous, no task
                del self._bg[tid]
                out, total = task.buf.render()
                body = cap_output(out, self.tool_cap_bytes)
                return self._bash_record(
                    cid, turn, body, total, task.exit_code, t0,
                    net_note, hide_note, sync_note="finished before "
                                                   "backgrounding")
            head = task.buf.head[:400]
            return ToolRecord(
                call_id=cid, tool="bash", turn=turn, ok=True,
                text=(f"background task {tid}"
                      + (f" ({name})" if name else "")
                      + f" started (pid {proc.pid}); first output: "
                      + (head if head else "(none yet)")
                      + f". Wait with task_wait({tid!r})."),
                price=0.0, unit="bytes", effect_bytes=0,
                duration_s=time.time() - t0,
                network=net_note, fs_hide=hide_note)

        proc, hide = self._spawn(command)
        try:
            out, _ = proc.communicate(timeout=timeout)
            code: int | None = proc.returncode
            timed_out = False
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_group(proc)
            try:
                out, _ = proc.communicate(timeout=5)
            except Exception:                    # noqa: BLE001
                out = b""
            code = proc.returncode
        text = (out or b"").decode("utf-8", "replace")
        body = cap_output(text, self.tool_cap_bytes)
        rec = self._bash_record(cid, turn, body, len(text), code, t0,
                                net_note, hide_note)
        if timed_out:
            rec.code = R_TIMEOUT
            rec.text = (f"{rec.text}\n[TIMEOUT after {timeout:g}s — the "
                        f"process group was killed; partial output above]")
        return rec

    def _bash_record(self, cid, turn, body, total, code, t0,
                     net_note, hide_note, sync_note="") -> ToolRecord:
        head_line = (f"exit {code}, {time.time() - t0:.2f}s, "
                     f"{total} byte{'s' if total != 1 else ''}")
        return ToolRecord(
            call_id=cid, tool="bash", turn=turn, ok=True, exit_code=code,
            text=(f"({head_line}; network={net_note}, fs_hide={hide_note}"
                  + (f"; {sync_note}" if sync_note else "") + f")\n{body}"),
            price=float(total), unit="bytes",
            effect_bytes=len(body.encode()),
            duration_s=time.time() - t0,
            network=net_note, fs_hide=hide_note)

    def _tool_task_wait(self, cid, turn, args, t0) -> ToolRecord:
        tid = args.get("id")
        if not isinstance(tid, str) or not tid:
            raise ToolRefused(R_BAD_ARGS, "'id' must be a non-empty string "
                                          f'(name the task, e.g. "t1")')
        task = self._bg.get(tid)
        if task is None:
            raise ToolRefused(R_UNKNOWN_BG,
                              f"no background task {tid!r} "
                              f"(have {sorted(self._bg)})")
        kill = args.get("kill", False)
        if not isinstance(kill, bool):
            raise ToolRefused(R_BAD_ARGS, "'kill' must be a boolean")
        timeout = _opt_int(args, "timeout_seconds", 0)
        waited = 0.0
        if kill:
            if not task.done:
                _kill_group(task.proc, sig=signal.SIGTERM)
                task.thread.join(2.0)
                if not task.done:
                    _kill_group(task.proc, sig=signal.SIGKILL)
                    task.thread.join(2.0)
        elif timeout is not None:
            waited = min(float(timeout), self.wait_timeout)
            task.thread.join(waited)
        else:
            task.thread.join(self.wait_timeout)
        out, total = task.buf.render()
        body = cap_output(out, self.tool_cap_bytes)
        status = (f"exit {task.exit_code}" if task.done and
                  task.exit_code is not None else
                  "killed" if kill and task.done else "RUNNING")
        label = task.name if task.name != tid else tid
        return ToolRecord(
            call_id=cid, tool="task_wait", turn=turn, ok=True,
            text=(f"task {label} ({task.id}): {status} after "
                  f"{time.time() - task.started:.2f}s, {total} bytes "
                  f"total\n{body}"),
            price=float(total), unit="bytes",
            effect_bytes=len(body.encode()),
            duration_s=time.time() - t0)

    # -- run_tests (the evaluator IS "run the tests") --------------------
    def _tool_run_tests(self, cid, turn, args, t0) -> ToolRecord:
        f = args.get("task")
        if not isinstance(f, str) or not f:
            raise ToolRefused(R_BAD_ARGS, "'task' must be a target name "
                                          f"(e.g. 'f1')")
        if not self.targets:
            raise ToolRefused(R_UNDECLARED_TARGET,
                              "the declared target set is EMPTY — nothing "
                              "is callable (designer act: construct the "
                              "harness with targets)")
        if f not in self.targets:
            raise ToolRefused(
                R_UNDECLARED_TARGET,
                f"{f!r} is not a declared target "
                f"(declared: {', '.join(sorted(self.targets))})")
        task = self.task_map.get(f)
        if not task:
            raise ToolRefused(R_NO_TASK_MAP,
                              f"target {f!r} has no task mapping "
                              f"(map: {self.task_map or '{}'} — a bare "
                              f"writable target cannot run tests)")
        if not self.tasks_root:
            raise ToolRefused(R_NO_TASKS_ROOT,
                              "no tasks_root was supplied — there is no "
                              "suite to run")
        ev = self._evaluator_or_refuse()
        spec = self._spec(task)
        # FRESH PRISTINE COPY (task_eval's own isolation: fresh sandbox,
        # netns, group-kill timeout, no heldout bytes in the copy), then
        # the agent's MODULE overlaid — the scored surface is exactly
        # the module under repair as the agent currently has it.  Test
        # bytes are pristine ALWAYS: deleting or rewriting the visible
        # tests cannot fake a pass.
        ws = ev.prepare(task)
        try:
            dst = os.path.join(ws.path, spec.module)
            src = os.path.join(self.workspace, f, spec.module)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
            elif os.path.exists(dst):
                os.remove(dst)   # the agent deleted the module: the suite
                                 # must fail on import, not pass vacuously
            evaluation = ev.score(ws)
        finally:
            if not self.keep:
                shutil.rmtree(ws.sandbox_root, ignore_errors=True)
        vis = evaluation.visible
        n_tests = len(vis.collected)
        lines = [f"run_tests {f} ({task}) — VISIBLE suite: "
                 f"{vis.status}"
                 + (f" ({len(vis.failed)} failed of {n_tests})"
                    if vis.failed else
                    f" ({len(vis.passed)} passed of {n_tests})")]
        for nid in vis.failed:
            lines.append(f"  FAIL {nid}")
        for nid in vis.not_run:
            lines.append(f"  NOT RUN {nid}")
        if vis.status == "TIMEOUT":
            lines.append(f"  the suite hit the {ev.timeout:g}s timeout and "
                         f"was killed as a group")
        lines.append("held-out suite: scored out-of-band (its outcome is "
                     "not shown to you)")
        body = cap_output("\n".join(lines), self.tool_cap_bytes)
        # THE PRICE, in the effect's OWN unit: TESTS EXECUTED (wall time
        # is duration_s, recorded and never priced).  Both suites ran,
        # so the count is visible + held-out collected.
        n_all = n_tests + len(evaluation.heldout.collected)
        detail = evaluation.describe()
        return ToolRecord(
            call_id=cid, tool="run_tests", turn=turn, ok=True,
            text=body, price=float(n_all), unit="tests",
            effect_bytes=len(body.encode()),
            duration_s=time.time() - t0, detail=detail[:2000])

    def _evaluator_or_refuse(self):
        if self._evaluator is None:
            try:
                import task_eval
                self._evaluator = task_eval.TaskEvaluator(
                    self.tasks_root, python=self._python_arg,
                    network=self._network_mode,
                    timeout=self.run_timeout,
                    root=self.scoring,
                    # THE QUEUE'S AXES REGISTRATION, honoured when the
                    # designer merged it onto the harness (lh_agent
                    # does; a bare harness keeps the default table) —
                    # one suite, one registration, so a spec lookup
                    # never answers from a different table than the
                    # universe was built from.
                    axes=getattr(self, "_axes", None))
            except Exception as e:                # noqa: BLE001
                # find_python's refusal (no interpreter with pytest):
                # typed, never a silent fallback to a runner-less score
                raise ToolRefused(
                    R_NO_PYTEST,
                    f"no interpreter with pytest ({type(e).__name__}: "
                    f"{e}) — run_tests refuses to run without a test "
                    f"runner") from e
        # THE EXPLICIT-INTERPRETER CONTRACT: find_python FALLS THROUGH
        # the candidate list, so an explicit python= that does not exist
        # (or has no pytest) is silently ignored.  Here the explicit
        # argument is a DESIGNER statement, so it is HONOURED: if it
        # cannot import pytest, the tool refuses (no_pytest) rather
        # than running under an interpreter the designer did not name.
        if self._python_arg:
            import subprocess as _sp
            try:
                ok = _sp.run([self._python_arg, "-c", "import pytest"],
                             stdout=_sp.DEVNULL, stderr=_sp.DEVNULL,
                             timeout=60).returncode == 0
            except Exception:                    # noqa: BLE001
                ok = False
            if not ok:
                raise ToolRefused(
                    R_NO_PYTEST,
                    f"the explicit interpreter {self._python_arg!r} "
                    f"cannot import pytest — run_tests refuses to fall "
                    f"back to another interpreter the designer did not "
                    f"name")
        return self._evaluator

    def _spec(self, task: str):
        if self._specs is None:
            import task_eval
            self._specs = {s.name: s for s in
                           task_eval.discover_tasks(
                               self.tasks_root,
                               getattr(self, "_axes", None))}
        spec = self._specs.get(task)
        if spec is None:
            raise ToolRefused(R_UNKNOWN_TASK,
                              f"task {task!r} is not in the suite "
                              f"(have {sorted(self._specs)})")
        return spec

    # -- the resume surface (C8: fail-closed like every seat) -------------
    def dump(self) -> dict:
        """The seat's carried identity: the declared targets, the
        allowed tools and the counters.  The SANDBOX and any background
    tasks are NOT carried — they are process state; a resume re-supplies
        the harness object (a construction parameter, like the admissible
        set) and the setter refuses a mismatch."""
        return {"targets": sorted(self.targets),
                "allowed": sorted(self._allowed),
                "calls_total": len(self.history),
                "refusals": sum(1 for r in self.history if not r.ok)}

    def load(self, state) -> None:
        if not isinstance(state, dict) or "targets" not in state:
            raise ValueError(
                f"ToolHarness.load: not this seat's shape: "
                f"{type(state).__name__}")
        if frozenset(state["targets"]) != self.targets \
                or frozenset(state["allowed"]) != self._allowed:
            raise ValueError(
                f"ToolHarness.load: checkpoint targets/allowed "
                f"{state['targets']}/{state['allowed']} != this "
                f"harness's {sorted(self.targets)}/"
                f"{sorted(self._allowed)} — what is callable must not "
                f"change across a resume")

    def close(self) -> None:
        """Kill any background tasks and remove the sandbox (unless
        keep).  THE TASKS DIE WITH THE HARNESS: a harness object dropped
        without close() leaks its children until the process exits —
        the battery closes its harnesses explicitly."""
        for t in list(self._bg.values()):
            if not t.done:
                _kill_group(t.proc, sig=signal.SIGKILL)
                t.thread.join(1.0)
        self._bg.clear()
        if not self.keep:
            shutil.rmtree(self.root, ignore_errors=True)


def _kill_group(proc, sig=signal.SIGKILL) -> None:
    """Kill the child's WHOLE process group (the session it leads):
    pytest and any grandchild, not just the shell (task_eval's group-
    kill discipline)."""
    try:
        os.killpg(os.getpgid(proc.pid), sig)
    except (ProcessLookupError, PermissionError):
        try:
            proc.kill()
        except Exception:                        # noqa: BLE001
            pass


def _opt_int(args: dict, name: str, default) :
    v = args.get(name, default)
    if v is None:
        v = default
    if isinstance(v, bool) or not isinstance(v, int):
        raise ToolRefused(R_BAD_ARGS, f"'{name}' must be an integer")
    return v


def _diff(old: str, new: str, rel: str) -> str:
    """A unified diff with sandbox-relative labels (what lets the agent
    VERIFY its own change — hax write.c/edit.c's return shape)."""
    return "".join(difflib.unified_diff(
        old.splitlines(keepends=True), new.splitlines(keepends=True),
        fromfile=f"a/{rel}", tofile=f"b/{rel}"))


# =========================================================================
# THE MANIFEST — the prompt's explanation of the carrier
# =========================================================================

def manifest_text(targets=()) -> str:
    """The tool placement text.  MEASURED lesson this exists for: a
    placement line that does not name the real shapes yields ZERO of
    them — so this names EVERY tool with its arguments, the fence, the
    target discipline, the escape rule and a worked example, and it
    states where results arrive."""
    tgt = ", ".join(sorted(targets)) if targets else "(none declared)"
    return (
        "TOOLS — you have real tools, and they act on a sandbox copy of "
        "the work: nothing you can do touches anything outside it. A "
        "tool call is a fenced block in your stream, on its own lines, "
        'like this:\n\n```tool\n{"tool": "read", "args": '
        '{"path": "f1/rchunk.py", "offset": 1, "limit": 40}}\n```\n\n'
        "The block is a JSON object with 'tool' and 'args'; a malformed "
        "block is answered with a typed refusal, never ignored. The "
        "tools:\n"
        "  read(path, offset, limit) — returns the file with 1-indexed "
        "line numbers; the number prefix is NOT part of the file.\n"
        "  write(path, content) — replaces the file entirely and returns "
        "a unified diff of the change.\n"
        "  edit(path, old_string, new_string, replace_all) — replaces an "
        "exact string that must occur exactly once (unless "
        "replace_all=true); returns a diff.\n"
        "  bash(command, timeout_seconds, background, name) — runs a "
        "shell command in the sandbox and returns combined output plus "
        "exit code; background=true starts a task you collect with "
        "task_wait.\n"
        "  task_wait(id, timeout_seconds, kill) — waits on (or kills) a "
        "background task and returns its output.\n"
        "  run_tests(task) — runs a task's visible test suite and "
        "returns the verdict; only the module under repair is scored, "
        "and the held-out outcome is never shown.\n"
        f"Paths are sandbox-relative and their first component must be a "
        f"declared target ({tgt}) or the scratch/ directory; anything "
        "reaching outside the sandbox, or naming a heldout/ directory, "
        "is refused loudly. Tool RESULTS arrive in the state block of "
        "your NEXT turn, under TOOLS. There is no separate glob or grep "
        "tool: bash covers them."
    )
