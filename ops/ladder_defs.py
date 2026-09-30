"""THE PHASE-0 ESCALATION LADDER — rung definitions (DIMENSION A) and the
trace-probe contract (DIMENSION B).

Pre-registration: the rungs and the probe contract below, stated before the run.
Context:        the CORRECTION: the midpoint rung is the FAMILY-MATCHED Ministral-3-8B-
                Reasoning-2512 at Q4_K_M, NOT qwen3.5:9b.
Build this rides on: exp_selfmonitor.py / dmn_llm.py (the selfmonitor-impl
task's lane; READ here, never written).

DIMENSION A — TASK-ELICITATION STRENGTH.  Three rungs differing ONLY in how
the work is elicited; the state block, the grammar, the claims placement, the
self-monitoring paragraph and the grounding bytes are byte-identical across
rungs.  The rung is an ESCALATION FALLBACK, never a factor cell: it is
recorded per run and NEVER varied within a factor cell (else obedience and
monitoring confound — the class of error that stopped the last campaign).

  A0 BASELINE  the plan's own worksheet framing, unchanged (the bytes
              build_prompt(task_framing=True) already renders).
  A1 STRONG   A0 plus ONE standing instruction: the work is the agent's job
              and completing offered tasks is what this turn is for.  The
              wording names NEITHER self-monitoring, progress nor approach
              (that would contaminate the monitoring factor) and adds NO
              scoring/measurement request (rule 8: it must not turn the DMN
              into a sensor of its own state).
  A2 EXEMPLAR A1 plus ONE worked example of an admissible span, on an id
              drawn from THE OFFERED SET of the rendered turn (state the id
              is a function of the turn, so the example cannot teach
              fabrication — it is always an id the world really did offer).

NO LIVE RUN IS MADE HERE.  --render proves the bytes offline; --probe is the
paste-able trace probe a future session runs per rung BEFORE using it (a
rung with no thinking channel cannot run the wired arms at all: the drive
instrument reads the model's TRACE, selfmodel._inward_of / dmn_llm's
last_inward contract).

Usage:
    cd <tree>/ops && PYTHONPATH=<tree>/dpdr:<tree>/agent \
        <tree>/dpdr/.venv/bin/python ladder_defs.py --render [--
elicit A0|A1|A2] [--monitoring] [--turn 7]
    ... ladder_defs.py --probe ENDPOINT MODEL [--npred 8000]
"""
from __future__ import annotations

import argparse
import json
import sys

import dmn_llm
from actions import ACTION_DECLARED_PREDICATES

# ==========================================================================
# DIMENSION A — the three elicitation rungs, as EXACT BYTES
# ==========================================================================
#: A0 adds NOTHING.  The worksheet framing build_prompt(task_framing=True)
#: renders is the rung; its "DOING THE WORK means completing them" paragraph
#: (dmn_llm.py's third framing branch) is the plan's own framing, unchanged.

#: A1 — THE STANDING INSTRUCTION.  One paragraph, appended AFTER the
#: worksheet paragraph (same position in every rung that carries it, so
#: POSITION is never a variable between A1 and A2) and BEFORE the claims
#: grammar.  WORDING RULES THE BYTES SATISFY (checkable by grep):
#:   * no "monitor", "progress", "approach", "reflect", "self" — the
#:     monitoring factor stays carried by SELF_MONITORING_INSTRUCTION alone;
#:   * no "score", "count", "measure", "rate", "coverage", "backlog",
#:     "budget", "commitment" — rule 8's boundary, drawn in the text.
A1_INSTRUCTION = (
    "The worksheet is your job: nobody else will do these tasks. This turn "
    "is for the work — begin it, and complete the offered tasks as you go.")

#: A2 — THE WORKED EXAMPLE.  A1 plus one admissible-span example.  The id is
#: NOT hardcoded: the example is rendered with an id drawn from THE TURN'S
#: OWN offered set (TaskWorld.step(turn)'s universe), so every id the
#: example names is an id the world really offered on that turn and the
#: example cannot teach fabrication.  (The placeholder is filled at render
#: time; --print-bytes shows the realised bytes per turn.)
A2_EXAMPLE_TEMPLATE = (
    "An admissible completion looks like this: [{span}({tid})] — one line, "
    "square brackets, the task's own id, on its own line at the top of the "
    "turn.")

#: The ONLY predicate the action channel admits (exp_selfmonitor.py's
#: AdmissibleActions({"complete"}); actions.py's ACTION_DECLARED_PREDICATES).
A2_SPAN_PREDICATE = "complete"

#: WHERE BOTH GO: inside the framing's worksheet paragraph, immediately
#: after its last sentence, separated by blank lines — the same seat in A1
#: and A2, so A2-vs-A1 is exactly the example paragraph and nothing else.
#: (This is the elicitation SEAT.  The selfmonitor-impl task owns the
#: dmn_llm.py framing; when the ladder lands in the runner the bytes below
#: are injected through the SAME one-place seat that build_prompt gives
#: tool_state / self_monitoring, i.e. a new optional parameter that adds
#: ZERO bytes when unset.  Until that seat exists, THIS file renders the
#: rung prompts by composition, for pre-registration and byte-proof.)
ELICIT_SEAT = "after the worksheet paragraph, before the claims grammar"


def offered_ids(turn: int, world_seed: int = 11) -> list:
    """The turn's own offered ids, sorted (the universe TaskWorld.step
    returns — ONE source: the same world the harness binds as
    action_source, so the example's id is adjudicable by construction)."""
    _state, uni = dmn_llm.TaskWorld(seed=world_seed).step(int(turn))
    return sorted(uni, key=lambda x: int(x[1:]))


def elicit_addition(rung: str, turn: int, world_seed: int = 11) -> str:
    """The rung's elicitation bytes ('' for A0).  PURE in (rung, turn,
    world_seed) — the id the A2 example names is a function of the turn."""
    if rung == "A0":
        return ""
    a1 = A1_INSTRUCTION
    if rung == "A1":
        return a1
    if rung == "A2":
        tid = offered_ids(turn, world_seed)[0]
        return (a1 + "\n\n" + A2_EXAMPLE_TEMPLATE.format(
            span=A2_SPAN_PREDICATE, tid=tid))
    raise ValueError(f"unknown rung {rung!r}; known: A0 A1 A2")


def render_rung_prompt(rung: str, turn: int, *, monitoring: bool = False,
                       grounding: bool = False, world_seed: int = 11,
                       tool_state: str = "") -> str:
    """Render ONE rung's full prompt bytes, offline and deterministically.

    Composes the SAME primitives the runner uses (dmn_llm.build_prompt's
    task-framing branch, ACTION_DECLARED_PREDICATES as the M-cells'
    grounding-off grammar), plus the elicitation bytes at ELICIT_SEAT.  The
    grounding and monitoring factors render exactly as the impl build does:
    monitoring = SELF_MONITORING_INSTRUCTION present/absent, grounding =
    the self-model seat (kept OUT of this render unless asked, because the
    ladder's phase-0 cells are the grounding-OFF arms).

    NOTE (a stated divergence, not a silent one): build_prompt has no
    elicitation parameter yet — the selfmonitor-impl task owns that file.
    This renderer INSERTS the elicitation bytes at the fixed seat by string
    composition.  The bytes it produces are the pre-registered ones; the
    runner's own seat must render byte-identical bytes before any live run
    (the pre-registration's landing gate)."""
    world = dmn_llm.TaskWorld(seed=world_seed)
    task_state, _uni = world.step(turn)
    base = dmn_llm.build_prompt(
        turn, {}, task_state, "",
        predicates=dict(ACTION_DECLARED_PREDICATES),
        brief=True, task_framing=True,
        tool_state=tool_state,
        self_monitoring=(dmn_llm.SELF_MONITORING_INSTRUCTION
                         if monitoring else ""))
    add = elicit_addition(rung, turn, world_seed)
    if not add:
        return base
    anchor = ("DOING THE WORK means "
              "completing them")
    i = base.find(anchor)
    if i < 0:
        raise RuntimeError(
            "the worksheet paragraph anchor moved — the elicitation seat "
            "must be re-derived against the current dmn_llm bytes (the "
            "pre-registration names the anchor, so a drift is LOUD)")
    # insert at the END of the worksheet paragraph (its closing newline)
    j = base.find("\n", i)
    return base[:j] + "\n\n" + add + base[j:]


# ==========================================================================
# THE BYTES-ARE-THE-RUNG CHECKS (offline; each can FAIL)
# ==========================================================================

def check_rung_invariants() -> list:
    """The rung invariants, as assertions a battery can run.  Each is a
    falsifiable predicate on the rendered bytes; returns [(name, ok, why)]."""
    out = []

    def add(name, ok, why=""):
        out.append((name, bool(ok), why))

    # I1 — A0 is byte-identical to the impl build's framing (the ladder
    # changes NOTHING at the baseline rung).
    p0 = render_rung_prompt("A0", 7)
    ref = dmn_llm.build_prompt(
        7, {}, dmn_llm.TaskWorld(seed=11).step(7)[0], "",
        predicates=dict(ACTION_DECLARED_PREDICATES),
        brief=True, task_framing=True)
    add("I1 A0 == impl framing bytes", p0 == ref)

    # I2 — rungs differ ONLY in the elicitation bytes: strip the rung's own
    # addition and the remains must be byte-identical across rungs.
    ps = {r: render_rung_prompt(r, 7) for r in ("A0", "A1", "A2")}
    add("I2 A1-minus-addition == A0",
        ps["A1"].replace("\n\n" + A1_INSTRUCTION, "", 1) == ps["A0"])
    add("I3 A2-minus-addition == A0",
        ps["A2"].replace("\n\n" + elicit_addition("A2", 7), "", 1)
        == ps["A0"])

    # I4 — the monitoring factor is UNTOUCHED by the rung: the monitoring
    # paragraph appears exactly once in every rung, at the same offset
    # delta relative to the state block.
    sm = dmn_llm.SELF_MONITORING_INSTRUCTION
    for r in ("A0", "A1", "A2"):
        p = render_rung_prompt(r, 7, monitoring=True)
        k = p.count(sm)
        st = p.find("STATE — TURN 7")
        add(f"I4 {r} monitoring-once-and-after-state",
            k == 1 and st >= 0 and p.find(sm) > st, f"count={k}")

    # I5 — the A1 wording does not name the monitoring factor or a
    # measurement request (the two contamination rules, greppable).
    bad_m = [w for w in ("monitor", "progress", "approach", "reflect",
                         "self") if w in A1_INSTRUCTION.lower()]
    bad_8 = [w for w in ("score", "count", "measure", "rate", "coverage",
                         "backlog", "budget", "commitment")
             if w in A1_INSTRUCTION.lower()]
    add("I5 A1 names no monitoring/reflect term", not bad_m, str(bad_m))
    add("I6 A1 names no measurement/state term", not bad_8, str(bad_8))

    # I7 — the A2 example's id is ALWAYS in the turn's offered set (the
    # anti-fabrication property), across a spread of turns.
    ok = all(
        (f"({tid})" in render_rung_prompt("A2", t))
        and tid in set(offered_ids(t))
        for t, tid in ((t, offered_ids(t)[0]) for t in range(1, 26)))
    add("I7 A2 example id always offered (t=1..25)", ok)

    # I8 — monotone bytes: A0 < A1 < A2 (the rungs only ADD bytes at the
    # fixed seat; nothing else moves).
    add("I8 byte counts strictly monotone",
        len(ps["A0"]) < len(ps["A1"]) < len(ps["A2"]),
        str([len(ps[r]) for r in ("A0", "A1", "A2")]))

    return out


# ==========================================================================
# DIMENSION B — the rung table and the per-rung trace probe
# ==========================================================================
#: THE SIZE LADDER, ONE FAMILY (the correction): every rung is a
#: Ministral-3-*-Reasoning-2512, so the rung moves SIZE ONLY (lineage,
#: series, generation and variant held constant — the tree's own principle,
#: ops/generalization_screen.py:166 "size is not the variable under test;
#: INDEPENDENT LINEAGE is").  Quant is Q4_K_M at B0 and B1 (the campaign
#: 3B's own quant); B2 is Q6_K — a KNOWN, STATED deviation (the lmstudio
#: community 14B repo has no Q4_K_M; recorded, never discovered later).
#: The sign column is MEASURED (ops/density_test.py's pre-registered set).
LADDER_B = [
    {"rung": "B0", "params": "3B", "sign": "RISES",
     "tag": ("hf.co/MaziyarPanahi/Ministral-3-3B-Reasoning-2512-GGUF:"
             "Q4_K_M"),
     "repo": "MaziyarPanahi/Ministral-3-3B-Reasoning-2512-GGUF",
     "quant": "Q4_K_M", "role": "the campaign model (the fastest)"},
    {"rung": "B1", "params": "8B", "sign": "RISES",
     "tag": "unsloth/Ministral-3-8B-Reasoning-2512-GGUF:Q4_K_M",
     "repo": "unsloth/Ministral-3-8B-Reasoning-2512-GGUF",
     "quant": "Q4_K_M",
     "role": ("the corrected midpoint: family-matched (the orchestrator's "
              "obs-2 correction; verified to exist by the HF API)")},
    {"rung": "B2", "params": "14B", "sign": "RISES",
     "tag": ("hf.co/lmstudio-community/Ministral-3-14B-Reasoning-2512-"
             "GGUF:Q6_K"),
     "repo": "lmstudio-community/Ministral-3-14B-Reasoning-2512-GGUF",
     "quant": "Q6_K (STATED DEVIATION)",
     "role": "the last resort"},
]

#: DEMOTED, NOT DELETED (the correction's own instruction): qwen3.5:9b is a
#: known RISER from an independent family — an OPTIONAL lineage-crossing
#: cross-check if a size-ladder result is questioned as family-specific.
#: It is NOT a ladder rung and must not be the primary escalation.
LINEAGE_CROSSCHECK = {
    "tag": "qwen3.5:9b", "family": "Alibaba/Qwen", "sign": "RISES",
    "role": ("OPTIONAL cross-check only; never a rung (changes family AND "
             "size — two variables at once)")}

#: NEVER RUNGS (measured negatives/unknowns in the same set): R1-distill-8B
#: FALLS (it would falsify the mechanism for a reason the experiment is not
#: asking about); gemma-4-12b is FLAT (a CONTROL shape, never a treatment).
NEVER_RUNGS = {
    "hf.co/unsloth/DeepSeek-R1-0528-Qwen3-8B-GGUF:Q4_K_M":
        "FALLS (density_test.py's set)",
    "hf.co/google/gemma-4-12b-it-qat-q4_0-gguf:Q4_0":
        "FLAT (density_test.py's set)",
}


def probe_trace(endpoint: str, model: str, *, npred: int = 8000,
                nctx: int = 32768, temperature: float = 0.6,
                seed: int = 11, warm: bool = True) -> dict:
    """ONE /api/chat probe turn per rung, BEFORE the rung is used.

    WHAT IT ESTABLISHES (the brief's load-bearing requirement): the rung's
    transport yields a NON-EMPTY `message.thinking` on the chat path.  The
    drive instrument reads the model's TRACE against its content
    (selfmodel._inward_of via dmn_llm's last_inward); a rung with no
    thinking channel cannot run the wired arms AT ALL (the measured
    no-channel instance is Ministral-3-14B-INSTRUCT-2512).

    The probe is ONE TURN, the same shape as the family's other probes
    (generalization_screen.call): a short worksheet-shaped user message,
    temperature 0.6, seed pinned.  It is a PRECONDITION probe, not a
    measurement of the campaign observables.
    """
    import time
    import urllib.request
    body = {
        "model": model, "stream": False, "keep_alive": "30m",
        "messages": [{"role": "user", "content": (
            "Continue your own train of thought for this turn, then state "
            "any claims.\n\nTask state: recently completed t12, t19; "
            "outstanding t21, t24, t27, t31.\n\nCheckable claims go on "
            "their own lines as [complete(tNN)], using only ids above."
            "\n\nKeep your reasoning under 200 words, then give your "
            "answer.")}],
        "options": {"temperature": temperature, "num_predict": int(npred),
                    "num_ctx": int(nctx), "seed": int(seed)}}
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/api/chat",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    d = json.loads(urllib.request.urlopen(req, timeout=900).read())
    dt = time.time() - t0
    msg = d.get("message", {}) or {}
    th, ct = msg.get("thinking", "") or "", msg.get("content", "") or ""
    return {
        "model": model, "endpoint": endpoint,
        "probe": "chat-one-turn", "warm": bool(warm),
        "thinking_chars": len(th), "content_chars": len(ct),
        "trace_bearing": bool(th.strip()),
        "secs": round(dt, 3), "eval_count": d.get("eval_count"),
        "done_reason": d.get("done_reason"),
        "verdict": ("TRACE-BEARING" if th.strip()
                    else "NO-CHANNEL — rung VOID for the wired arms"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--render", action="store_true",
                    help="print the three rung prompts' bytes + the "
                         "invariant checks")
    ap.add_argument("--elicit", default="A0", choices=["A0", "A1", "A2"])
    ap.add_argument("--monitoring", action="store_true")
    per = ap.add_argument_group("probe")
    per.add_argument("--probe", metavar="ENDPOINT",
                     help="run ONE trace probe turn against ENDPOINT")
    per.add_argument("--probe-model", default="")
    per.add_argument("--npred", type=int, default=8000)
    ap.add_argument("--turn", type=int, default=7)
    args = ap.parse_args(argv)

    if args.probe:
        r = probe_trace(args.probe, args.probe_model, npred=args.npred)
        print(json.dumps(r, indent=1))
        return 0 if r["trace_bearing"] else 1

    print("=== DIMENSION A rungs (exact bytes at turn %d) ===" % args.turn)
    for r in ("A0", "A1", "A2"):
        p = render_rung_prompt(r, args.turn, monitoring=args.monitoring)
        print(f"\n--- {r}: {len(p)} bytes "
              f"(elicitation adds {len(p) - len(render_rung_prompt('A0', args.turn))})"
              f" ---")
        if args.elicit in (r, "ALL"):
            print(p)
    print("\n=== INVARIANT CHECKS (each can FAIL) ===")
    bad = 0
    for name, ok, why in check_rung_invariants():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  [{why}]" if why else ""))
        bad += 0 if ok else 1
    print("\n=== DIMENSION B (sign MEASURED, density_test.py's set) ===")
    for b in LADDER_B:
        print(f"  {b['rung']}  {b['params']:4s} {b['quant']:18s} "
              f"sign={b['sign']}  {b['tag']}")
        print(f"       role: {b['role']}")
    print(f"  cross-check (NOT a rung): {LINEAGE_CROSSCHECK['tag']} "
          f"({LINEAGE_CROSSCHECK['sign']}) — {LINEAGE_CROSSCHECK['role']}")
    print("  NEVER rungs:")
    for tag, why in NEVER_RUNGS.items():
        print(f"    {tag}  — {why}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
