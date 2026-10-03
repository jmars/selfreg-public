"""COMPOSED model — the frozen five-state ODE with the three PERSISTENCE
layers live at once (artifact 1 of the composed system; design node
handoff-selfreg-composed-plan, gate verdict handoff-selfreg-compose-result).
Opt-in, frozen model untouched: this module IMPORTS read-only
(dpdr.integrate.simulate, dpdr.consolidation, dpdr.values, dpdr.generational,
dpdr.regulator) and modifies nothing upstream.

WHY THIS MODULE EXISTS: the project's layers were built and tested one at
a time — memory (dpdr/consolidation.py), values (dpdr/values.py),
self-modification (dpdr/generational.py), the regulator
(dpdr/regulator.py).  The composed model is the three PERSISTENCE layers
live SIMULTANEOUSLY on one trajectory: consolidation = CONTENT layer
(what survives), values = SELECTION layer (what is held worth keeping),
generational = SYSTEM layer (what the agent is).  The one genuinely new
object is the L5 loop (below): store -> a -> trajectory -> alarm state ->
M -> Params -> store, closed through modify_once.  Nothing tested that
loop before this module.

KEY DESIGN RULE — NO RHS IS DUPLICATED HERE.  dpdr.values.deriv_values IS
the composed per-step RHS: values WRAPS consolidation, which WRAPS the
frozen five, exactly as values.py:234-264 already defines (with the
GatedSchedule inside), so the composed 11-state per-step dynamics are
the existing verified code, not a re-implementation.  This module
supplies only what none of the layers has: (i) the generational loop
around the live RHS, (ii) the per-generation schedule, (iii) the
regulator channel, (iv) the interfaces and observability.

STATE VECTOR (11 states, the values-with-memory layout):
    y = [a, G, D, S, g,  W_self, W_task,  M_self, M_task,  A_val, V_val]
  frozen five | working set | durable store | values (adoption, criterion)
With memory off and values on: 7 states [...five, A, V].  With memory on
and values off: 9 states (dpdr.consolidation's).  With both off: the
frozen five, and the live call dispatches to dpdr.integrate.simulate
LITERALLY (fidelity F1 is bit-exactness against that call).

CARRY-vs-RESET TABLE (what crosses a generation boundary):
  row  quantity              across a boundary   why (measurable)
  ---  --------------------  ------------------  ------------------------
  1    a,G,D,S,g (five)      CARRY, clipped      the generational contract
       to [0,1]/[0,1]/       exactly as run_generational does
       [0,1.5]/[0,1]/[0,2]   (verified by exp12 part-0 gen-2+ IC
                             reproduction)
  2    Params p              CARRY               p = rec['p_new'] — this IS
                             the persistent SYSTEM modification
  3    calendar/schedule     RESET               generation_schedule()
                             rebuilt fresh each generation: episode
                             [100,200), rescue [800,1000) repeat
                             identically
  4    W_self, W_task        RESET to the        tau_W = 5 << horizon 1010:
                             attention-rest      they re-equilibrate within
                             fills of the        ~15 t.u. of the next
                             CARRIED a, i.e.     generation; carrying them
                             (a_ic, 1 - a_ic)    would be a no-op with
                             (composed sets      extra state.  FALSIFIER:
                             cp.w0_* = None      end-of-generation
                             every generation)   |W_self - a| > 0.01 would
                             WRONG and carry must be tested
  5    M_self, M_task        CARRY               the point of consolidation:
                             the survivor layer (mu_M = 0); carrying them
                             is what lets memory bias the next
                             generation's alarm state through the
                             retrieval drive (the L5 loop)
  6    A_val, V_val          CARRY               the self's standing
                             valuation (tau_v = 20) — the substrate the
                             next generation inherits
  7    alarm/decision point  RESET               recomputed per generation
                             from the new trajectory
  8    integrator grid/state RESET               segmented solver restarts
                             at t = 0 of each generation
  9    monitor/regulator     no internal state   RegulatorParams are
                             constants; the derived floor_theta_eff is
                             recomputed from S at every RHS call
  10   adoption record/      APPEND-ONLY log     out['adopted'] etc. are
       margins                                   never fed back
ORDERING RULE: memory/values states are NEVER updated between generations
except by their own dynamics inside the live integration — this module
does not re-normalize, clip or reset M/A/V; the only cross-generation
writes are y_carry (five states), p (levers) and the append-only log.

LAYER INTERFACE LIST (every coupling point; L-numbers from the plan):
  L1  consolidation -> frozen:  deriv_consol reads y[:5]+p and writes da
      via +k_in*store_drive(M_s, ...)*(1-a)/tau_a.  One-directional
      memory -> plant.
  L2  values -> consolidation write: deriv_values rewrites the self-class
      write under v_self*V(t) (value_sel).  One-directional values ->
      store.
  L3  values -> frozen u_ext: the GatedSchedule rescales the u_ext channel
      by 1 + kappa_ad*A(t).  One-directional values -> plant.
  L4  generational -> everything: run_composed replace()s p each
      generation; p is read by deriv_consol/deriv_values/rollout_self at
      call time — a BROADCAST write, read-only for all layers.  There is
      exactly ONE p per generation; memory and values drift WITH the
      plant automatically, and the self-model (certify_state) verifies on
      the SAME drifted p, so no extra sync exists or is needed.
  L5  generational self-model reads the LIVE state: _alarm_state reads the
      composed trajectory (including memory's effect on a via L1) and
      modify_once evaluates candidates with certify_state -> rollout_self
      on the same drifted p.  This is the ONLY site where memory feeds
      back into the SYSTEM layer: store -> a -> trajectory -> alarm state
      -> M -> Params -> store — the composed model's new loop.
  L6  regulator -> plant: when gen.reg is set AND no persistence layer is
      live, the live call dispatches to dpdr.regulator.simulate_reg (the
      exp13 composition, reproduced exactly).  With a persistence layer
      live the regulated composed RHS is ARTIFACT 2's seam
      (dpdr/composed_regulator.py) and dispatches there — a NULL
      regulator reproduces this module's unregulated paths bit-exactly.
  L7  window self-model: certify_state uses rollout_self/_v_plus
      read-only; window.py's live M/c_int channels are NOT part of the
      composed model (its benefit is monotone-by-construction and would
      double-count the generational M).
  L8  values adoption cue: the schedule's 'adopt' channel.  The composed
      default is NO adopt channel (A decays to its rest 0; the rescue
      u_ext is NOT auto-adopted); ComposedParams.adopt/retrieve expose
      optional extra spans, identical every generation.

ORDERING (per generation, exact; T5 is the canary that pins it):
  (1) rebuild sch = generation_schedule() (+adopt/retrieve if configured);
  (2) set ICs: frozen five from the y_carry clips, W reset (row 4), M and
      A/V from carry;  (3) integrate ONE generation through
      simulate_composed (deriv_values is the RHS when values are on);
  (4) record G_min/G_end/E_end/c_max and the carry observables;
  (5) IF gen.enabled: modify_once(pk, sol, gp) — the alarm state reads
      the COMPOSED trajectory;  (6) candidates are certified on the SAME
      drifted p and wp;  (7) p = rec['p_new'];  (8) y_carry = end five;
  (9) M/A/V carry; append the log record.

FIDELITY (the contract F1-F5, non-negotiable): F1 — every layer disabled,
one generation, gen-1 ICs: the dispatch path LITERALLY calls
dpdr.integrate.simulate, so max|dG| vs that call is 0.0 EXACTLY (a hard
stop: any nonzero value is a dispatch bug, not a tolerance question).
F2 — all layers enabled but inert (value_sel on with V0 = 0, A0 = 0, no
adopt channel, m0_self = 0: every memory/values flux on the frozen five
is then an exact zero) reproduces the frozen trajectory to integrator
tolerance 1e-3, the values/consolidation precedent for adaptive-stepper
divergence.  F3 — the all-disabled generation loop reproduces exp12
part-0's disabled control.  F4 — single-layer additivity: memory-only is
simulate_consol bit-exact, values-only is simulate_values bit-exact,
generational-only (memory off) reproduces the cached exp12 adopted
sequences.  F5 — the frozen test suite still passes.

THE REGULATOR SEAM AND THE MEASURED BRANCH (exp13's verdict, which this
implementation follows rather than re-derives): the R1-vs-R0 coupling is
TRAJECTORY-ONLY (adopted sequences identical, 0 differences), W2 is
FALSIFIED (self_model_regulated is INERT — R2 == R1 bit-identical), W3
TRUE (controller margins all 0.0 — the controller is outside the agent's
evidence), W4 TRUE (the regulator is LOAD-BEARING on gen-1's dip; the
walk never rescues it), W5 TRUE (no config degrades).  Consequences
wired in here: gen.self_model_regulated is threaded through to
certify_state for completeness and documented MEASURED-INERT (no
behaviour is built around it); the regulator channel is exposed only at
the L6 seam (all-off live episodes under reg reproduce exp13 exactly);
the regulated composed RHS is left to artifact 2.

PAPER-2 LEAK GUARD: consolidation's block-vs-down-weight axis
(ConsolParams.block) is PAPER-2 property.  ComposedParams exposes cp only
as a passed-in object, the DEFAULT carries block=False, and NO code path
in this module enables or justifies block — the guard axis is
deliberately not asserted here (continuity.md section 5).

EPISTEMIC STATUS: the composed system is a DIFFERENT SYSTEM — follow-up
work, not a finding of the frozen model or the published paper.  Every
constant belongs to an imported layer; this module adds NONE.  The model
is deterministic: every threshold is a locus, not a distribution.

Numerics: the live integration IS dpdr.values.simulate_values /
dpdr.consolidation.simulate_consol / dpdr.integrate.simulate (segmented
RK45, rtol 1e-6, atol 1e-8, max_step 0.5, restarted at every schedule
breakpoint; grid arange(n+1)*dt) — imported, not copied.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

from .consolidation import ConsolParams, simulate_consol
from .generational import GenParams, generation_schedule, modify_once
from .integrate import simulate
from .model import Params, Schedule
from .regulator import RegulatorParams, simulate_reg
from .values import ValuesParams, simulate_values

try:                      # artifact 2's seam (dpdr/composed_regulator.py);
    from .composed_regulator import (  # pragma: no cover - import path
        simulate_composed_reg)
except ImportError:       # pragma: no cover - composed_regulator absent
    simulate_composed_reg = None


__all__ = ["ComposedParams", "simulate_composed", "run_composed"]

# the carry clips are run_generational's exactly (generational.py:279-286
# per the plan's corrected line numbers) — the generational contract
_CARRY_BOUNDS = ((0.0, 1.0), (0.0, 1.0), (0.0, 1.5), (0.0, 1.0), (0.0, 2.0))


def _layers(cmp_: "ComposedParams") -> tuple[ValuesParams, ConsolParams]:
    """Effective per-layer params: layer flags -> the enabled/memory bits
    the imported layers dispatch on, plus the row-4 W reset (cp.w0_* = None
    every generation: the working set re-fills from the CARRIED a)."""
    vp = replace(cmp_.vp, enabled=cmp_.values, memory=cmp_.memory)
    cp = replace(cmp_.cp, enabled=cmp_.memory, w0_self=None, w0_task=None)
    return vp, cp


@dataclass
class ComposedParams:
    """Constants of the composed model (see module docstring).

    Every layer object (gen/cp/vp) is passed in as-is; this dataclass adds
    NO constant of its own, only the layer ON/OFF flags and the optional
    per-generation schedule spans (L8).  Defaults: all persistence layers
    OFF (the composed loop degenerates to the exp12 two-arm system),
    cp.block False (the paper-2 leak guard), no adopt/retrieve channel.
    """
    # live persistence layers (content / selection)
    memory: bool = False            # consolidation states live
    values: bool = False            # values states live
    # the system layer (self-modification), the regulator channel (L6) and
    # the self-model foresight flag (measured INERT by exp13's W2) both
    # live in gen — they are threaded through, not duplicated here
    gen: GenParams = field(default_factory=GenParams)
    cp: ConsolParams = field(default_factory=ConsolParams)
    vp: ValuesParams = field(default_factory=ValuesParams)
    # optional extra schedule spans (t0, t1, value), identical every
    # generation (L8): the adoption cue / retrieval gate channels
    adopt: tuple = ()
    retrieve: tuple = ()
    # initial plant Params (generation 1); None = Params() defaults
    p0: Params | None = None


def _generation_schedule(cmp_: "ComposedParams") -> Schedule:
    """The canonical generation task, rebuilt fresh every generation (row
    3), plus the optional adopt/retrieve spans (L8) if configured."""
    sch = generation_schedule()
    if cmp_.adopt:
        sch.channels["adopt"] = [tuple(s) for s in cmp_.adopt]
    if cmp_.retrieve:
        sch.channels["retrieve"] = [tuple(s) for s in cmp_.retrieve]
    return sch


def simulate_composed(p: Params, cmp_: ComposedParams, sch: Schedule,
                      T: float, dt: float | None = None,
                      _vp_ov: ValuesParams | None = None,
                      _cp_ov: ConsolParams | None = None) -> dict:
    """ONE generation's LIVE integration, dispatched on the live layers —
    no RHS is duplicated: values on -> dpdr.values.simulate_values (its
    deriv_values IS the composed per-step RHS, memory or not); else memory
    on -> dpdr.consolidation.simulate_consol; else the FROZEN
    dpdr.integrate.simulate, literally (F1's bit-exact dispatch); with a
    regulator and NO live persistence layer -> dpdr.regulator.simulate_reg
    (the exp13 composition, L6).  A regulator with a live persistence
    layer is artifact 2 and raises here rather than mis-composing."""
    gp = cmp_.gen
    if dt is None:
        dt = gp.dt
    vp, cp = _layers(cmp_)
    if _vp_ov is not None:
        vp = replace(vp, a0_val=_vp_ov.a0_val, v0_val=_vp_ov.v0_val)
    if _cp_ov is not None:
        cp = replace(cp, m0_self=_cp_ov.m0_self, m0_task=_cp_ov.m0_task)
    if gp.reg is not None and (vp.enabled or cp.enabled):
        # artifact 2's seam (dpdr/composed_regulator.py): the regulated
        # composed dispatch.  A regulator with NO live persistence layer
        # never reaches here (simulate_reg below, exp13's composition).
        if simulate_composed_reg is None:
            raise NotImplementedError(
                "regulated composed integration (regulator x "
                "memory/values) needs dpdr/composed_regulator.py")
        return simulate_composed_reg(p, gp.reg, vp, cp, sch, T, dt)
    if vp.enabled:
        return simulate_values(p, vp, cp, sch, T, dt)
    if cp.enabled:
        return simulate_consol(p, cp, sch, T, dt)
    if gp.reg is not None:
        return simulate_reg(p, gp.reg, sch, T, dt)
    return simulate(p, sch, T, dt)


def run_composed(cmp_: ComposedParams, n_gen: int,
                 keep_sol: bool = False) -> dict:
    """The composed generational loop (ORDERING steps 1-9, module
    docstring).  Each generation: rebuild the schedule; set ICs per the
    carry-vs-reset table; integrate ONE generation through
    simulate_composed; record; then modify_once on the composed
    trajectory (the L5 loop) applies at most one persistent Params change
    the next generation inherits.  Returns run_generational's per-
    generation arrays plus the carry observables ('ic_*' initial states
    and 'end_*' final states per generation, NaN for off-layer states),
    params_final, T, n_gen and (keep_sol=True) the per-generation sols."""
    gp = cmp_.gen
    p = Params() if cmp_.p0 is None else cmp_.p0
    keys = ("G_min", "G_end", "E_end", "c_max", "adopted", "margin", "V",
            "t_eval", "ic_a", "ic_G", "ic_D", "ic_S", "ic_g",
            "end_a", "end_G", "end_D", "end_S", "end_g",
            "ic_W_self", "ic_W_task", "end_W_self", "end_W_task",
            "ic_M_self", "ic_M_task", "end_M_self", "end_M_task",
            "ic_A", "ic_V", "end_A", "end_V")
    out = {k: [] for k in keys}
    sols = []
    y_carry = None            # the five frozen states (row 1)
    M_carry = None            # (M_self, M_task) (row 5)
    AV_carry = None           # (A, V) (row 6)
    for _k in range(n_gen):
        # (1) fresh calendar each generation (row 3) + L8 channels
        sch = _generation_schedule(cmp_)
        # (2) ICs: five from carry (row 1, run_generational's clips);
        # W resets to the attention-rest fills of the carried a (row 4);
        # M / A / V carry (rows 5-6)
        vp, cp = _layers(cmp_)
        if y_carry is None:
            pk = p
        else:
            pk = replace(p, **{n: float(np.clip(v, lo, hi)) for n, v, (lo, hi)
                               in zip(("a0", "G0", "D0", "S0", "g_init"),
                                      y_carry, _CARRY_BOUNDS)})
            if cmp_.memory:
                cp = replace(cp, m0_self=float(M_carry[0]),
                             m0_task=float(M_carry[1]))
            if cmp_.values:
                vp = replace(vp, a0_val=float(AV_carry[0]),
                             v0_val=float(AV_carry[1]))
        # (3) one generation of the LIVE composed trajectory, with the
        # row-5/6 carry (M and A/V) THREADED through the layer params —
        # the recorded ic_* log and the solver ICs must agree (artifact
        # 2's carry fix; artifact 1 computed these and dropped them)
        sol = simulate_composed(pk, cmp_, sch, gp.horizon,
                                _vp_ov=vp if cmp_.values else None,
                                _cp_ov=cp if cmp_.memory else None)
        # (4) record + the carry observables
        out["G_min"].append(float(sol["G"].min()))
        out["G_end"].append(float(sol["G"][-1]))
        out["E_end"].append(float(sol["E"][-1]))
        out["c_max"].append(float(sol["c"].max()))
        for n, key in zip(("a", "G", "D", "S", "g"),
                          ("ic_a", "ic_G", "ic_D", "ic_S", "ic_g")):
            out[key].append(float(getattr(pk, {"a": "a0", "G": "G0",
                                               "D": "D0", "S": "S0",
                                               "g": "g_init"}[n])))
            out["end_" + n].append(float(sol[n][-1]))
        for key in ("ic_W_self", "ic_W_task", "end_W_self", "end_W_task",
                    "ic_M_self", "ic_M_task", "end_M_self", "end_M_task"):
            if not cmp_.memory:
                out[key].append(float("nan"))
                continue
            fld = {"ic_W_self": pk.a0, "ic_W_task": 1.0 - pk.a0,
                   "end_W_self": sol["W_self"][-1],
                   "end_W_task": sol["W_task"][-1],
                   "ic_M_self": cp.m0_self, "ic_M_task": cp.m0_task,
                   "end_M_self": sol["M_self"][-1],
                   "end_M_task": sol["M_task"][-1]}[key]
            out[key].append(float(fld))
        for key in ("ic_A", "ic_V", "end_A", "end_V"):
            if not cmp_.values:
                out[key].append(float("nan"))
                continue
            fld = {"ic_A": vp.a0_val, "ic_V": vp.v0_val,
                   "end_A": sol["A"][-1], "end_V": sol["V"][-1]}[key]
            out[key].append(float(fld))
        # (5)-(7) M on the COMPOSED trajectory, on the same drifted p and
        # the same wp (L5); adopt per the arm; p = rec['p_new'] (row 2)
        if gp.enabled and gp.step != 1.0:
            rec = modify_once(pk, sol, gp)
        else:
            rec = dict(adopted="", lever="", sign=0.0, margin=0.0, V=0.0,
                       t_eval=None, p_new=pk, margins={})
        out["adopted"].append(rec["adopted"])
        out["margin"].append(float(rec["margin"]))
        out["V"].append(float(rec["V"]))
        out["t_eval"].append(np.nan if rec["t_eval"] is None
                             else float(rec["t_eval"]))
        p = rec["p_new"]
        # (8)-(9) the ONLY cross-generation writes: the five states, the
        # carried M / A / V, the levers — and the log is append-only
        y_carry = np.array([sol["a"][-1], sol["G"][-1], sol["D"][-1],
                            sol["S"][-1], sol["g"][-1]])
        if cmp_.memory:
            M_carry = (float(sol["M_self"][-1]), float(sol["M_task"][-1]))
        if cmp_.values:
            AV_carry = (float(sol["A"][-1]), float(sol["V"][-1]))
        if keep_sol:
            sols.append(sol)
    res = {k: (np.array(v, dtype=object) if k == "adopted" else np.array(v))
           for k, v in out.items()}
    res["params_final"] = p
    res["T"] = gp.T
    res["n_gen"] = n_gen
    if keep_sol:
        res["sols"] = sols
    return res
