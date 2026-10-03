"""THE COMPOSED REGULATOR — the self-rescue regulator composed with the
FULL persistence stack (artifact 2 of the composed system; design node
handoff-selfreg-composed-plan, gate verdict handoff-selfreg-compose-result,
binding refinements handoff-selfreg-gap-probe).

WHY THIS MODULE EXISTS.  dpdr.regulator.py protects the FROZEN plant;
exp13 composed it with the generational layer alone and measured the two
NOT entangled (adopted sequences identical, the regulator load-bearing on
generation 1's dip, no config degrades).  But the composed MODEL
(dpdr.composed, artifact 1) runs three persistence layers at once, and
its dispatch deliberately raised NotImplementedError at the
regulator x memory/values seam — composing them silently would have been
a claim.  This module is that seam, plus the four things the plain
regulator does not have:

  1. THE PLANT SURFACE (S1).  deriv_composed_reg / simulate_composed_reg
     wrap dpdr.values.deriv_values / dpdr.consolidation.deriv_consol —
     NO layer RHS is duplicated — and apply the regulator's three pieces
     as EXACT-TERM CORRECTIONS to the plant block, term-for-term
     dpdr.regulator.deriv_reg's structure:
       floor    the cannibalization switch c is evaluated at
                floor_theta_eff (imported); every read site of c in the
                composed RHS (dG's -eta*c*G, da's k_in*chi*c*(1-a), and
                the values states' -eta*c*A / -eta*c*V erosion) sees the
                regulated switch — the values layer dies under ACTUAL
                cannibalization, and the floor's whole point is that
                there is none;
       actuator da/dt += -k_pull * m(G) * a (the cheap scalar trigger);
       monitor  da/dt += k_in * c_mon * m(G) * (1-a) in the a_hold slot,
                gated by the same trigger (mon_gated).
     With a NULL regulator (floor=None, k_pull=0, c_mon=0) every
     correction is an exact signed zero and the RHS is bit-identical to
     deriv_values / deriv_consol — N1's bit-exactness is algebraic, not
     approximate (floor=None makes floor_theta_eff return exactly
     p.Theta*S/S_rest, cannibalization's own expression).

  2. THE SELF-MODEL MIRROR (Q3).  gp.self_model_regulated (a GenParams
     flag, threaded by generational.py's exp13 edit) mirrors the floor
     into the rollout's switch threshold — f_T's ONLY regulator channel.
     THE BINDING WORDING (the gap probe corrected exp13's): the
     blindness is REGIME-DEPENDENT, not absolute — at fixed states the
     mirror shifts some candidates' margins by up to ~1e-1 at T >= 160,
     ONE-SIDED (no candidate ever looks worse under the mirror), and it
     never flipped the argmin in any measured walk.  The honest
     statement is: the self-model changes the agent's EVIDENCE without
     changing its CHOICE.  Never report it as "unmeasurable".

  3. THE INVARIANT MONITOR (Q4).  check_protection: at EVERY Params the
     composed walk reaches, the inward-drive channel never seals the
     capture loop — operationalized per generation as
     (c_max <= 0.5 OR is_stuck(sol) is False) AND G_end > 0.1.

  4. THE DRIFT SCAN (Q2).  sweep Theta x the visited S range x floor
     candidates and report the cells where the FROZEN floor 0.7 fails
     while a re-derived static floor succeeds.  floor_mode='rederive'
     is NOT implemented: it is built only if the scan finds a failing
     cell (W13 predicted empty; the visited Theta never moves in any
     cached walk).  Re-deriving by TRACKING the live S is forbidden
     outright (harness.py:192-194: a floor re-checked with a
     discrepancy cost fails at kc ~ 0.2).

Q1 — THE CONTROLLER IS NOT A LEVER (measured, branch (c)).  exp13's W3:
all 240 controller margins were EXACTLY 0.0, and the reason is
STRUCTURAL: rollout_self's quasi-steady attention (window.py:250-252)
contains no k_pull/c_mon/G_trig terms and its switch reads only Teff_sw,
so the agent's evaluator can see ONLY the floor.  A near-zero margin
table is therefore a STRUCTURAL BLIND SPOT, not the agent wisely
declining (the plan's risk R4) — controller_margin_table ships
REPORT-ONLY with that note attached, and adoption would require a
pre-stated margin < -atol_tau (which the measurement says never fires).
controller_as_lever consequently stays False; setting it True raises,
because making controller knobs first-class levers would require
extending generational.py's frozen lever machinery — out of scope by
rule, and unwarranted by measurement.

THE OPEN ANOMALY, REPORTED AS SUCH (never relied on): the floor's
visibility to a short rollout vs horizon is NON-MONOTONE and unexplained
— the gap probe measured the self-model shift at one gen-1 state as
T=20 -> 5.36e-03, T=40 -> EXACTLY 0.0, T=60 -> 4.26e-03.  A single
exact zero between non-zero neighbours is not a smooth horizon effect.
exp14 part B characterizes the curve and reports it as an open
anomaly; nothing here tunes, smooths, or explains it post hoc.

THE METHOD RULE (the gap probe's, binding on all decision-decoupling
claims): do NOT report "decision-decoupled" as a horizon-bounded
observation — exhibit the mechanism.  For every near-tie, apply the two
candidate operations to the SAME Params in BOTH ORDERS and compare:
identical means the flip is an exact order swap and NO horizon can
separate the walks; different means a genuine perturbation whose
accumulation must be measured.  (At T=10 the near-tied pair alpha_G /
gam_G proved exactly commuting — multiplicative on independent fields —
which is why 192-generation forcing reconverged; that is a property of
THAT pair, not a general guarantee.)

PAPER-2 LEAK GUARD: consolidation's block-vs-down-weight axis
(ConsolParams.block) is paper-2 property.  Nothing in this module
enables or justifies it; the composed default carries block=False and
every experiment here keeps it there.

EPISTEMIC STATUS: the composed system is a DIFFERENT SYSTEM — follow-up
work, not a finding of the frozen model or the published paper.  This
module adds NO constant: every regulator constant is dpdr.regulator's
 RegulatorParams fields re-exposed (ComposedRegParams is a policy-side
view of them), every plant constant belongs to an imported layer.
Deterministic model: every threshold is a locus, not a distribution.

Numerics mirror dpdr.values.simulate_values / dpdr.regulator.simulate_reg
exactly (segmented RK45, rtol 1e-6, atol 1e-8, max_step 0.5, restarted
at every schedule breakpoint plus t_engage; grid arange(n+1)*dt).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np
from scipy.integrate import solve_ivp

from .consolidation import (ConsolParams, consolidation_gate,
                            deriv_consol)
from .generational import GenParams, certify_state
from .metrics import is_stuck
from .model import Params, Schedule, cannibalization
from .regulator import RegulatorParams, floor_theta_eff
from .values import ValuesParams, deriv_values

__all__ = ["ComposedRegParams", "deriv_composed_reg",
           "simulate_composed_reg", "check_protection",
           "controller_margin_table", "drift_scan",
           "commutativity_check"]

# the controller-knob candidate grid — exp13 part 1's protocol, unchanged
# (retrospective; no knob value was or may be tuned)
CTRL_FLOORS = (0.5, 0.7, 0.9)
CTRL_KS = (1.0, 2.0)
CTRL_CMS = (0.5, 1.0)
CTRL_TRIGS = (0.2, 0.4)

# the structural blind-spot note that SHIPS with every Q1 margin table
# (the plan's risk R4: a near-zero table is a property of the evaluator,
# not a judgement by the agent)
STRUCTURAL_NOTE = (
    "rollout_self's quasi-steady attention (window.py:250-252) contains "
    "no k_pull/c_mon/G_trig terms and its cannibalization switch reads "
    "only Teff_sw: the agent's evaluator can see ONLY the floor.  A "
    "near-zero margin for the actuator/monitor/trigger knobs is a "
    "STRUCTURAL BLIND SPOT, not the agent declining wisely, and even "
    "floor margins are regime-dependent (a mid-descent open-loop "
    "rollout can sit below both switch thresholds so c = 0 either way).  "
    "Report-only; adoption requires a pre-stated margin < -atol_tau.")


@dataclass
class ComposedRegParams:
    """Policy-side view of the composed regulator (see module docstring).

    Every field maps onto dpdr.regulator.RegulatorParams (the plant
    surface) except the three policy flags: controller_as_lever (Q1,
    measured NO — see the docstring for why setting it True raises),
    self_model_regulated (Q3, threaded to GenParams so certify_state
    mirrors the floor into f_T), and drift_scan (Q2, runs the sweep once
    per experiment, cheap).  floor_mode 'rederive' is NOT implemented:
    it is built only if the Q2 drift scan finds a failing cell."""
    floor: float | None = 0.7
    floor_mode: str = "theta"      # 'theta' | 'S' ('rederive' gated on Q2)
    k_pull: float = 2.0
    G_trig: float = 0.3
    trig_w: float = 0.02
    c_mon: float = 0.0
    mon_gated: bool = True
    t_engage: float = 0.0
    controller_as_lever: bool = False
    self_model_regulated: bool = False
    drift_scan: bool = True

    def __post_init__(self):
        if self.floor_mode not in ("theta", "S"):
            raise ValueError(
                f"floor_mode {self.floor_mode!r} is not implemented: "
                "'rederive' is built only if the Q2 drift scan finds a "
                "cell where the frozen floor fails and a re-derived "
                "static floor succeeds (see drift_scan)")
        if self.controller_as_lever:
            raise NotImplementedError(
                "controller_as_lever is measured NO (exp13 W3: all 240 "
                "controller margins exactly 0.0 — and structurally the "
                "evaluator cannot see k_pull/c_mon/G_trig).  Making the "
                "controller a first-class lever would require extending "
                "generational.py's frozen lever machinery; see "
                "STRUCTURAL_NOTE")

    @property
    def regulator(self) -> RegulatorParams:
        """The plant-side projection (the live seam's RegulatorParams)."""
        return RegulatorParams(floor=self.floor, floor_mode=self.floor_mode,
                               k_pull=self.k_pull, G_trig=self.G_trig,
                               trig_w=self.trig_w, c_mon=self.c_mon,
                               mon_gated=self.mon_gated,
                               t_engage=self.t_engage)

    def bind(self, cmp_) :
        """Return cmp_ with this regulator bound to its generational
        layer (gen.reg set, gen.self_model_regulated mirrored) — the
        full composed-regulated walk is then run_composed(bind(cmp_))."""
        gen = replace(cmp_.gen, reg=self.regulator,
                      self_model_regulated=self.self_model_regulated)
        return replace(cmp_, gen=gen)


# ------------------------------------------------------------ S1: plant
def deriv_composed_reg(t, y, p: Params, vp: ValuesParams, cp: ConsolParams,
                       sch: Schedule, r: RegulatorParams):
    """The regulated composed RHS — the live layers' RHS (imported,
    never duplicated) plus the regulator's three pieces as exact-term
    corrections to the plant block, mirroring dpdr.regulator.deriv_reg's
    structure.  Layout follows the live layers: values on ->
    deriv_values' 7- or 11-state vector; values off, memory on ->
    deriv_consol's 9-state vector.

    The corrections (all read the REGULATED switch where the frozen code
    reads the frozen one):
      dG  += -eta * dc * G / tau_G                      (the -eta*c*G term)
      da  += (k_in*(chi*dc + c_mon_t)*(1-a) - k_pull*m*a) / tau_a
      dA  += -eta * dc * A / tau_v   and  dV likewise   (values states:
            they erode under ACTUAL cannibalization, which the floor
            suppresses — the composed regulator's one new coupling)
    with dc = c_reg - c_frozen, m the trigger sigmoid, c_mon_t the gated
    monitoring cost.  Under a NULL regulator (floor=None, k_pull=0,
    c_mon=0) floor_theta_eff returns exactly p.Theta*S/S_rest —
    cannibalization's own expression — so dc, m-term and c_mon_t-term
    are exact signed zeros and every output equals the imported layer's
    bit-for-bit."""
    if vp.enabled:
        f = deriv_values(t, y, p, vp, cp, sch)
        av = (5, 6) if not vp.memory else (9, 10)
    elif cp.enabled:
        f = deriv_consol(t, y, p, cp, sch)
        av = None
    else:
        # the 5-state regulated system IS dpdr.regulator's (simulate_reg);
        # composed.py already dispatches there, so this seam never sees it
        raise NotImplementedError(
            "the 5-state regulated plant is dpdr.regulator.simulate_reg "
            "(composed.py's L6 dispatch); the composed seam needs a live "
            "persistence layer (values and/or memory)")
    a, G, D, S = y[0], y[1], y[2], y[3]
    E = D - G
    armed = 1.0 if t >= r.t_engage else 0.0
    te_frozen = p.Theta * S / p.S_rest
    te_reg = floor_theta_eff(S, p, r) if armed else te_frozen
    c_reg = min(p.sigma_c * max(0.0, math.tanh((E - te_reg) / p.w)), 1.0)
    c_frozen, _te = cannibalization(E, S, p)
    dc = (c_reg - c_frozen) if armed else 0.0
    m = armed / (1.0 + math.exp((G - r.G_trig) / r.trig_w))
    c_mon_t = armed * r.c_mon * (m if r.mon_gated else 1.0)
    dG = f[1] - p.eta * dc * G / p.tau_G
    da = f[0] + (p.k_in * (p.chi * dc + c_mon_t) * (1.0 - a)
                 - r.k_pull * m * a) / p.tau_a
    out = [da, dG, f[2], f[3], f[4]]
    out.extend(f[5:])
    if av is not None:
        for i in av:
            out[i] = f[i] - p.eta * dc * y[i] / vp.tau_v
    return out


def _reg_ic(p: Params, vp: ValuesParams, cp: ConsolParams) -> np.ndarray:
    """Initial state, exactly the live layers' own constructions."""
    y5 = [p.a0 if vp.a0 is None else vp.a0,
          p.G0 if vp.G0 is None else vp.G0,
          p.D0 if vp.D0 is None else vp.D0,
          p.S0 if vp.S0 is None else vp.S0,
          p.g_init if vp.g_init is None else vp.g_init]
    if vp.enabled:
        y = y5 + ([cp.w0_self if cp.w0_self is not None else p.a0,
                   (1.0 - p.a0) if cp.w0_task is not None else 1.0 - p.a0,
                   cp.m0_self, cp.m0_task] if vp.memory else []) \
            + [vp.a0_val, vp.v0_val]
    elif cp.enabled:
        w0s = p.a0 if cp.w0_self is None else cp.w0_self
        w0t = (1.0 - p.a0) if cp.w0_task is None else cp.w0_task
        y = y5 + [w0s, w0t, cp.m0_self, cp.m0_task]
    else:                           # pragma: no cover — never at the seam
        y = y5
    return np.array(y, float)


def simulate_composed_reg(p: Params, r: RegulatorParams, vp: ValuesParams,
                          cp: ConsolParams, sch: Schedule, T: float,
                          dt: float = 0.05) -> dict:
    """ONE generation of the regulated composed trajectory: segmented
    RK45 (the live layers' numerics verbatim) on deriv_composed_reg,
    breakpoints = the schedule's plus t_engage.  Returns the live
    layer's Solution dict (values on -> simulate_values' keys incl. the
    memory diagnostics; memory on -> simulate_consol's) with 'c' and
    'Theta_eff' OVERRIDDEN to the REGULATED values actually used by the
    switch (dpdr.regulator.simulate_reg's reporting convention, so
    dpdr.metrics.is_stuck reads the switch's belief, not the frozen
    threshold), plus 'Theta_eff_frozen', 'mon' and 'c_mon'.

    A NULL r reproduces the unregulated simulate_values /
    simulate_consol trajectory BIT-EXACTLY (the corrections are exact
    signed zeros and the breakpoint set is identical) — N1's contract."""
    n = int(round(T / dt))
    grid = np.arange(n + 1) * dt
    T = float(grid[-1])
    bps = sorted(set([b for b in sch.breakpoints() if 0.0 < b < T]
                     + ([r.t_engage] if 0.0 < r.t_engage < T else [])))
    for b in bps:
        if abs(b / dt - round(b / dt)) > 1e-9:
            raise ValueError(f"breakpoint {b} not on the dt={dt} grid")
    edges = [0.0] + bps + [T]
    y = _reg_ic(p, vp, cp)
    ts, ys = [], []
    nfev = 0
    for t0, t1 in zip(edges[:-1], edges[1:]):
        tev = grid[(grid >= t0 - 1e-9) & (grid < t1 - 1e-9)] if t1 < T \
            else grid[(grid >= t0 - 1e-9) & (grid <= T + 1e-9)]
        sol = solve_ivp(deriv_composed_reg, (t0, t1), y,
                        args=(p, vp, cp, sch, r),
                        rtol=1e-6, atol=1e-8, max_step=0.5, t_eval=tev)
        ts.append(sol.t)
        ys.append(sol.y)
        y = sol.y[:, -1]
        nfev += sol.nfev
    t = np.concatenate(ts)
    Y = np.concatenate(ys, axis=1)
    a, G, D, S, g = Y[:5]
    E = D - G
    # ---- the regulated switch, reported exactly as simulate_reg reports
    # it ('c'/'Theta_eff' = the values actually used; the frozen ones kept)
    Teff_frozen = p.Theta * S / p.S_rest
    if r.floor is None:
        Teff_reg = Teff_frozen
    elif r.floor_mode == "theta":
        Teff_reg = np.maximum(Teff_frozen, r.floor)
    else:
        Teff_reg = p.Theta * np.maximum(S, r.floor) / p.S_rest
    armed = (t >= r.t_engage).astype(float)
    Teff_reg = np.where(armed > 0, Teff_reg, Teff_frozen)
    c = np.minimum(p.sigma_c * np.maximum(0.0, np.tanh((E - Teff_reg)
                                                       / p.w)), 1.0)
    mon = armed / (1.0 + np.exp((G - r.G_trig) / r.trig_w))
    c_mon_t = armed * r.c_mon * (mon if r.mon_gated else 1.0)
    out = dict(t=t, a=a, G=G, D=D, S=S, g=g, E=E, c=c,
               Theta_eff=Teff_reg, Theta_eff_frozen=Teff_frozen, mon=mon,
               c_mon=c_mon_t, u_loop=G / (D + 1e-9), collapsed_at=None,
               nfev=nfev,
               methods=[f"composereg(mem={int(vp.memory)},"
                        f"floor={r.floor},k_pull={r.k_pull:g})"])
    if not vp.enabled:
        if not cp.enabled:                        # pragma: no cover
            return out
        # ---- memory on, values off: simulate_consol's diagnostics block
        W_s, W_t, M_s, M_t = Y[5], Y[6], Y[7], Y[8]
        m_ret = np.array([sch.value("retrieve", float(tt)) for tt in t])
        a_hold_g = np.array([sch.value("a_hold", float(tt)) for tt in t])
        drive = M_s * (cp.A_ret * m_ret + a_hold_g + cp.k_bg)
        g_att = np.array([consolidation_gate(float(ai), cp) for ai in a])
        raw_s = cp.v_self * W_s * g_att
        raw_t = cp.v_task * W_t * (1.0 - a)
        tot = raw_s + raw_t
        scale = np.where(tot > 0.0,
                         np.minimum(1.0, cp.B / np.maximum(tot, 1e-12)),
                         0.0)
        share_s = np.where(tot > 0.0, raw_s / np.maximum(tot, 1e-12), 0.0)
        out.update(W_self=W_s, W_task=W_t, M_self=M_s, M_task=M_t,
                   m_ret=m_ret, store_drive=drive, g_att=g_att,
                   scale=scale, share_self=share_s,
                   flux_self=raw_s * scale * (1.0 - M_s),
                   flux_task=raw_t * scale * (1.0 - M_t))
        return out
    # ---- values on: simulate_values' diagnostics block
    A, V = (Y[5], Y[6]) if not vp.memory else (Y[9], Y[10])
    u_ext_g = np.array([sch.value("u_ext", float(tt)) for tt in t])
    gate = 1.0 + vp.kappa_ad * A
    out.update(A=A, V=V, u_ext_raw=u_ext_g, gate=gate,
               u_ext_eff=u_ext_g * gate)
    if not vp.memory:
        return out
    W_s, W_t, M_s, M_t = Y[5], Y[6], Y[7], Y[8]
    m_ret = np.array([sch.value("retrieve", float(tt)) for tt in t])
    a_hold_g = np.array([sch.value("a_hold", float(tt)) for tt in t])
    drive = M_s * (cp.A_ret * m_ret + a_hold_g + cp.k_bg)
    g_att = np.array([consolidation_gate(float(ai), cp) for ai in a])
    v_self_arr = (cp.v_self * V if vp.value_sel
                  else np.full_like(t, cp.v_self, float))
    raw_s = v_self_arr * W_s * g_att
    raw_t = cp.v_task * W_t * (1.0 - a)
    tot = raw_s + raw_t
    scale = np.where(tot > 0.0, np.minimum(1.0, cp.B / np.maximum(tot, 1e-12)),
                     0.0)
    share_s = np.where(tot > 0.0, raw_s / np.maximum(tot, 1e-12), 0.0)
    out.update(W_self=W_s, W_task=W_t, M_self=M_s, M_task=M_t,
               m_ret=m_ret, store_drive=drive, g_att=g_att,
               v_self_dyn=v_self_arr, scale=scale, share_self=share_s,
               flux_self=raw_s * scale * (1.0 - M_s),
               flux_task=raw_t * scale * (1.0 - M_t))
    return out


# ------------------------------------------------------- S2: policy side
def check_protection(sol: dict, p: Params,
                     crp: "ComposedRegParams | None" = None) -> dict:
    """Q4's invariant on ONE generation's composed trajectory:
    the inward-drive channel never seals the capture loop —
    (c_max <= 0.5 OR is_stuck is False) AND G_end > 0.1.  Falsifier: any
    generation with is_stuck True, or G_end <= 0.1, or sustained
    c > 0.5 while E > Theta_eff at the end.  'c'/'Theta_eff' read the
    REGULATED values the switch actually used (simulate_composed_reg's
    reporting convention), so is_stuck judges the switch's own belief."""
    c_max = float(sol["c"].max())
    G_end = float(sol["G"][-1])
    G_min = float(sol["G"].min())
    stuck = bool(is_stuck(sol, p))
    w = sol["t"] >= sol["t"][-1] - 5.0 * p.tau_G
    sustained = bool(np.mean(sol["c"][w] > 0.5) > 0.5
                     and float(np.mean(sol["E"][w]))
                     > float(np.mean(sol["Theta_eff"][w])))
    ok = bool((c_max <= 0.5 or not stuck) and G_end > 0.1)
    return dict(c_max=c_max, G_end=G_end, G_min=G_min, is_stuck=stuck,
                sustained_c_seal=sustained, invariant_ok=ok)


def controller_margin_table(y, V0: float, p: Params, gp: GenParams,
                            T: float, A: float) -> dict:
    """Q1, REPORT-ONLY: V-margins of the CONTROLLER knobs as candidate
    moves at one alarm state, evaluated through the agent's own
    evaluator (certify_state with the mirror ON — f_T's only regulator
    channel), each candidate setting ONLY the knob under test (exp13
    part 1's protocol, unchanged).  NOTHING IS ADOPTED.  The returned
    dict carries STRUCTURAL_NOTE — the near-zero table is a property of
    the evaluator, not a judgement (see the module docstring)."""
    def cs(reg: RegulatorParams) -> float:
        gpr = replace(gp, reg=reg, self_model_regulated=True)
        return certify_state(y, p, gpr, T, A) - V0

    table: dict = {}
    for fl in CTRL_FLOORS:
        table[f"floor={fl:g}"] = cs(RegulatorParams(
            floor=fl, floor_mode="theta", k_pull=0.0, c_mon=0.0,
            t_engage=0.0))
    for k in CTRL_KS:
        table[f"k_pull={k:g}"] = cs(RegulatorParams(
            floor=None, k_pull=k, c_mon=0.0, t_engage=0.0))
    for cm in CTRL_CMS:
        table[f"c_mon={cm:g}"] = cs(RegulatorParams(
            floor=None, k_pull=2.0, c_mon=cm, t_engage=0.0))
    for gt in CTRL_TRIGS:
        table[f"G_trig={gt:g}"] = cs(RegulatorParams(
            floor=None, k_pull=2.0, c_mon=0.0, G_trig=gt, t_engage=0.0))
    table["full_design"] = cs(RegulatorParams(
        floor=0.7, floor_mode="theta", k_pull=2.0, c_mon=0.0,
        t_engage=0.0))
    table["structural_note"] = STRUCTURAL_NOTE
    return table


def drift_scan(sch: Schedule, T: float, dt: float, S_values,
               thetas=(0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8),
               floors=(0.5, 0.6, 0.7, 0.9),
               vp: ValuesParams | None = None,
               cp: ConsolParams | None = None) -> dict:
    """Q2's sweep: Theta x visited-S x floor on the composed regulated
    plant (memory+values live), ONE canonical generation per cell.  A
    floor FAILS a cell when c_max > 0.5 OR G_min < G_trig (the protective
    criterion: the switch never seals and G stays above the trigger).
    Alongside every static floor the scan runs the RE-DERIVED floor
    Theta*S0/S_rest (the generation-START true threshold, held constant
    — a static re-derivation, never a tracker).  The finding the plan
    wants is the set of (Theta, S0) cells where the FROZEN 0.7 floor
    fails while a re-derived floor succeeds: EMPTY -> the frozen floor
    stays, documented, and floor_mode='rederive' is not built."""
    vp = ValuesParams(value_sel=True, v0_val=0.9) if vp is None else vp
    cp = ConsolParams(policy="naive", block=False) if cp is None else cp
    G_trig = 0.3
    rec = {"theta": [], "S0": [], "floor": [], "c_max": [], "G_min": [],
           "G_end": [], "fails": []}
    for th in thetas:
        for S0 in S_values:
            p = replace(Params(), Theta=th, S0=S0)
            cand = [(f"{fl:g}", RegulatorParams(
                floor=fl, floor_mode="theta", k_pull=2.0, c_mon=0.0,
                t_engage=0.0)) for fl in floors]
            cand.append(("rederive",
                         RegulatorParams(floor=th * S0 / Params().S_rest,
                                         floor_mode="theta", k_pull=2.0,
                                         c_mon=0.0, t_engage=0.0)))
            cand.append(("none", RegulatorParams(
                floor=None, k_pull=2.0, c_mon=0.0, t_engage=0.0)))
            for name, r in cand:
                sol = simulate_composed_reg(p, r, vp, cp, sch, T, dt)
                c_max = float(sol["c"].max())
                g_min = float(sol["G"].min())
                rec["theta"].append(th)
                rec["S0"].append(S0)
                rec["floor"].append(name)
                rec["c_max"].append(c_max)
                rec["G_min"].append(g_min)
                rec["G_end"].append(float(sol["G"][-1]))
                rec["fails"].append(bool(c_max > 0.5 or g_min < G_trig))
    frozen_fail = {(th, s) for th, s, fl, f in zip(rec["theta"],
                                                   rec["S0"],
                                                   rec["floor"],
                                                   rec["fails"])
                   if fl == "0.7" and f}
    reder_fail = {(th, s) for th, s, fl, f in zip(rec["theta"], rec["S0"],
                                                  rec["floor"], rec["fails"])
                  if fl == "rederive" and f}
    rec["frozen07_failing_cells"] = sorted(frozen_fail)
    rec["rederive_rescues"] = sorted(frozen_fail - reder_fail)
    return rec


def commutativity_check(p: Params, key_a: str, key_b: str,
                        step: float = 1.15) -> dict:
    """The gap probe's method rule, operationalized: apply the two
    candidate moves to the SAME Params in BOTH ORDERS and compare every
    field.  Identical -> the flip is an exact order swap and NO horizon
    can separate the walks (the T=10 alpha_G/gam_G finding: independent
    multiplicative fields).  Different -> a genuine perturbation whose
    accumulation must be measured (force the runner-up and compare the
    walks).  Returns the per-field max difference and the verdict."""
    def op(pk: Params, key: str) -> Params:
        lever, sgn = key[:-1], (1.0 if key[-1] == "+" else -1.0)
        return replace(pk, **{lever: getattr(pk, lever) * step ** sgn})

    ab = op(op(p, key_a), key_b)
    ba = op(op(p, key_b), key_a)
    fields = sorted(set(f for f in getattr(p, "__dataclass_fields__")))
    diffs = {f: abs(getattr(ab, f) - getattr(ba, f)) for f in fields}
    worst = max(diffs.values())
    return dict(key_a=key_a, key_b=key_b,
                both_orders_identical=bool(worst == 0.0),
                max_field_diff=float(worst),
                worst_field=max(diffs, key=diffs.get),
                same_lever=bool(key_a[:-1] == key_b[:-1]))
