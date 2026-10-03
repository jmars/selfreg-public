"""VALUES variant — adoption and value-based selection for the dpdr model.
Opt-in; the frozen model and dpdr/consolidation.py are untouched (imported).

WHY THIS MODULE EXISTS (handoff-selfreg-weak-demand / -values / -consol-budget
/ -warmth-test / -novelty-source / -liminal): the frozen model has NO
value/preference/care term at all (verified — the only 'value' in the frozen
code is Schedule.value()).  Three independent empirical motivations:

  * M1 ADOPTION — u_ext is a RAW SCALAR, so an imposed obligation and an
    adopted vocation are IDENTICAL in the model.  Measured (frozen model,
    settled ICs, S0 = 0.8): dwell limit 98.9 -> 171.7 -> 384.7 t.u. as u_ext
    rises 0 -> 0.05 -> 0.10, protection complete only at u_ext >= 0.15.  No
    variable can carry the adopted/imposed difference.
  * M2 CONSOLIDATION SELECTION — dpdr/consolidation.py writes to the durable
    store under a BINDING budget, so something must select; there the
    selector is a per-class ATTENTION factor.  The literature (value-directed
    remembering, Castel et al.; the self-reference effect, Serbun) says the
    selector should be VALUE.
  * M3 GENERATION DIRECTION — G has no criterion, so generation is undirected
    and the warmth/adaptivity claim could not even be expressed.  NOT BUILT
    HERE — see DEFERRAL below.

ARCHITECTURE — a values state in TWO components (and why not one):

  A(t) in [0,1] — the ADOPTION state: whether the concurrent external
  expectation is HELD AS A VALUE (vocation) rather than imposed (job).
        dA/dt = [ beta_G*adopt(t)*(1-A) - eta*c*A - gam_G*A ] / tau_v
  V(t) in [0,1] — the VALUES/criterion state: the self's standing valuation
  capacity (the self IS the values substrate, handoff-selfreg-values), so it
  inherits the generator's OWN maintenance economics term-for-term, MINUS the
  control term (values are HELD, not re-derived — the floor result: the
  protective thing is an UNEXAMINED value; a knowingly-held floor fails):
        dV/dt = [ beta_G*(1-a)*V*(1-V) - alpha_G*a*V - eta*c*V - gam_G*V
                  + beta_G*adopt(t)*(1-V) ] / tau_v

  WHY TWO STATES (a design finding, not over-building): the two jobs need
  incompatible rest points.  The adoption gate must read ~0 for an imposed
  demand (else every demand is amplified by standing values and the anchor
  curve shifts for everyone — contradicted by the measurement: the boring job
  stays weak DESPITE the person having values), while the selection criterion
  must read ~high in health (the self-reference effect: self-referential
  encoding is BETTER in the healthy state).  One state cannot rest at both 0
  and 0.9; adoption (a property of the expectation-relation) and values (a
  property of the self) are genuinely different variables.

  CONSTANTS — the design goal is ONE new constant.  Every rate is IMPORTED
  from the frozen Params (beta_G = 3 growth-by-engagement, alpha_G = 1.2
  erosion-under-inward-attention, eta = 1.2 cannibalization, gam_G = 0.3
  turnover) and tau_v = tau_G = 20 (values change on the self's timescale).
  The ONLY new constant is kappa_ad = 1.0 (round number: full adoption at
  most DOUBLES the effective pull).  tau_v and kappa_ad are mapped as
  sensitivity axes in exp9 part D; nothing is pegged to either.

THE TWO COUPLINGS:

  (1) ADOPTION GATING of u_ext (job 1 / M1).  u_ext enters the frozen RHS at
  exactly one site (-k_ext*u_ext*a in da/dt), so the gate is implemented as a
  SCHEDULE WRAPPER: the variant passes deriv/deriv_consol a schedule whose
  'u_ext' channel returns u_eff = u_ext * (1 + kappa_ad*A(t)).  The frozen
  five and all seven non-write consolidation lines are then computed by the
  FROZEN/CONSOLIDATION code, unmodified; with A = 0 the factor is exactly 1.0
  and u_eff is bit-identical to u_ext.  An adopted expectation (A -> 1 in
  ~3*tau_v = 60 t.u. of being held) pulls at up to 2x its nominal level; an
  imposed one (A = 0) pulls at exactly its nominal level = the frozen model.
  The gate is DYNAMIC, not a reparameterization: capture erodes A (the -eta*c
  term), so a vocation's protection can ERODE under sustained collapse —
  measurable, and beyond anything a rescaled u_ext could express.

  (2) VALUE-BASED CONSOLIDATION SELECTION (job 2 / M2), coupled to
  dpdr/consolidation.py WITHOUT modifying it: deriv_values calls deriv_consol
  for everything except the two durable-write lines, whose per-class value
  weight v_self (consolidation.py's own documented-but-untested 'content-class
  value weight', asserted 1.0 there) becomes the VALUES STATE:
        raw_self = cp.v_self * V(t) * W_self * g_att(a)     (value-sel on)
        raw_self = cp.v_self * W_self * g_att(a)            (value-sel off)
  The attention policy axis (naive/guarded/block) survives unchanged via the
  imported consolidation_gate.  With value_sel off (or V pinned at 1) the
  write is consolidation.py's exactly.  The mechanism claim: the ATTENTION
  selector is corrupted because a is PINNED HIGH during collapse (naive share
  0.97) and a static down-weight is LAUNDERED by the binding budget (guarded
  share 0.86 — exp8's honest partial).  A VALUE selector is a STATE THAT
  DIES WITH THE SYSTEM: cannibalization crashes V (e-fold ~ tau_v/eta ~ 17
  t.u. at c = 1), so the self-share of the write collapses DURING the
  collapse window — the budget launders magnitudes, not a crashing ratio.

(3) DEFERRAL, STATED PLAINLY: GENERATION DIRECTION IS NOT BUILT.  Giving G a
  criterion is cheap to state but UNTESTABLE here: the frozen u_ext cannot be
  met or unmet (it is a pull, not a task), D is a scalar level, and there is
  no content set, so 'responds to NOVEL demands better' (P3) is INEXPRESSIBLE
  without a novelty/unmet-demand mechanism.  Building one is a separate
  variant; smuggling a novelty term in under the values heading is forbidden.
  P3 is DEFERRED, and nothing in this module touches dG/dt.

FIDELITY: vp.enabled = False dispatches to the frozen simulate (memory off)
or dpdr.consolidation.simulate_consol (memory on) — bit-exact in both cases.
With the values states integrated but inert (A0 = V0 = 0, no adopt channel,
value_sel off) every values flux is an exact zero and the gate factor is
exactly 1.0, so the variant reproduces the frozen/consolidation trajectory to
integrator tolerance (same class of divergence as consolidation.py's own
zero-flux wrap; verified in exp9 part 0).

PRE-REGISTERED PREDICTIONS AND FALSIFIERS (fixed before any exp9 run; the
predictions are the ctx node's, upstream of this build):

  P1 ADOPTION.  At the matched protocol (settled ICs, S0 = 0.8, u_ext standing
  from t = 0, a 300-t.u. pre-period, a_hold 0.9 episode of bisected dwell D,
  collapse judged G_end < 0.1 at D_onset + D + 300), the ADOPTED arm
  (adopt = 1) will show a HIGHER dwell limit than the IMPOSED arm (adopt = 0)
  at every nominal u_ext in {0.05, 0.08, 0.10}; specifically at u_ext = 0.10
  the adopted arm will show NO COLLAPSE to the 700-t.u. ceiling (u_eff = 2u
  = 0.20 lands in the measured protected regime u_eff >= 0.15) while the
  imposed arm stays finite at the same protocol.  Secondary: at u_ext = 0.05
  the adopted arm EXTENDS but does not protect (u_eff = 0.10 = the finite
  regime).  FALSIFIER: adopted dwell within one bisection cell (~0.7 t.u.) of
  imposed at matched u_ext — the adoption channel is inert.

  P2 SELECTION.  On the exp8 partG protocol (one canonical episode + rescue,
  default ICs, V0 = 0.9 = V's healthy attractor, A0 = 0), the VALUE-BASED arm
  (value_sel on, naive attention) will show M_self@ep2 < 0.39 (< 50% of the
  attention-based naive arm's measured 0.7784, and well below the down-weight
  arm guarded = 0.7532 whose failure the budget laundered).  FALSIFIER:
  M_self@ep2 > 0.7 (within ~10% of the attention-based selector) — the value
  selector is not load-bearing.  REFINEMENT QUESTION (reported either way, no
  pass/fail): does value-based selection WITHOUT the block reach the
  structural-inertness bound M_INERT = 0.1247 — which would CHANGE the guard
  result (the block would no longer be the only sufficient guard) — or does
  the hard block remain load-bearing for the last mile?

  P3 GENERATION DIRECTION: DEFERRED (see above).  No prediction registered.

HONEST STATUS, STATED PLAINLY: this is a DETERMINISTIC model; the values term
is a DESIGN CHOICE with NO GROUND TRUTH (the frozen model has none — every
constant here is imported from the frozen Params or is the single documented
round number kappa_ad = 1.0, and both are mapped as sensitivity axes); and
the enabled variant is GENUINELY DIFFERENT from the frozen model, so its
results are a FOLLOW-UP, not findings of the frozen model or the paper.  This
module does NOT claim the model 'explains' value loss or adaptivity — only
that the values term makes those claims EXPRESSIBLE and testable in-model.

Numerics mirror dpdr/consolidation.simulate_consol (segmented RK45, rtol
1e-6, atol 1e-8, max_step 0.5, restarted at every schedule breakpoint; grid
arange(n+1)*dt).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from .consolidation import (ConsolParams, consolidation_gate, deriv_consol,
                            simulate_consol)
from .integrate import simulate
from .model import Params, Schedule, cannibalization, cannibalization_vec, \
    deriv

__all__ = ["ValuesParams", "GatedSchedule", "deriv_values", "simulate_values"]


class GatedSchedule:
    """Schedule wrapper that rescales the 'u_ext' channel by the adoption
    gate 1 + kappa_ad*A, leaving every other channel (and the breakpoint
    structure) untouched.  The factor is read from a mutable cell that
    deriv_values sets from the state A at the top of every RHS call — the
    frozen code's single u_ext site (-k_ext*u_ext*a) then computes the gated
    pull without modification.  With factor exactly 1.0 the returned value is
    bit-identical to the wrapped channel."""

    def __init__(self, base: Schedule, cell: list):
        self.base = base
        self.cell = cell          # [factor], mutated by deriv_values

    def value(self, ch: str, t: float) -> float:
        v = self.base.value(ch, t)
        return v * self.cell[0] if ch == "u_ext" else v

    def breakpoints(self) -> list:
        return self.base.breakpoints()


@dataclass
class ValuesParams:
    """Constants of the values variant (see module docstring).

    Rates are NOT stored here — they are imported from the frozen Params at
    every RHS call (beta_G, alpha_G, eta, gam_G), so the variant can never
    drift from the frozen model's own semantics.  The two new degrees of
    freedom are kappa_ad (the only new constant) and tau_v (the imported
    timescale choice); both are exp9 part D sensitivity axes.

    Defaults: memory OFF (the minimal frozen+values system the P1 adoption
    battery runs), value selection OFF, values states at rest.
    """
    enabled: bool = True
    memory: bool = False      # integrate the consolidation states too
    value_sel: bool = False   # v_self -> V(t)*v_self in the write rule
    kappa_ad: float = 1.0     # adoption gate gain (the ONE new constant)
    tau_v: float = 20.0       # = tau_G (imported; values ride the self)
    a0_val: float = 0.0       # A(0): adoption state (0 = imposed/rest)
    v0_val: float = 0.0       # V(0): values state (0.9 = healthy attractor,
                              # 1.0 = initially-held values, the Layer-3
                              # 'values must be initial' reading)
    # initial state override for the frozen five (None = p.* defaults) —
    # lets an experiment start from SETTLED ICs (the P1 protocol) without
    # touching Params; same opt-in pattern as ConsolParams.w0_self
    a0: float | None = None
    G0: float | None = None
    D0: float | None = None
    S0: float | None = None
    g_init: float | None = None

    def __post_init__(self):
        if self.kappa_ad < 0.0 or self.tau_v <= 0.0:
            raise ValueError("kappa_ad >= 0 and tau_v > 0 required")


def _values_rhs(a: float, c: float, A: float, V: float, adopt: float,
                p: Params, vp: ValuesParams):
    """dA/dt, dV/dt — every rate imported from the frozen Params (see module
    docstring).  A: adopted expectation builds it, capture and turnover eat
    it, NO free maintenance (A_rest = 0 — nothing pays for an unadopted
    pull).  V: the generator's own maintenance algebra (outward engagement
    grows it, inward attention / cannibalization / turnover erode it — so
    V_rest = 1 - gam_G/beta_G = 0.9 in health) PLUS the adoption source, and
    MINUS G's control term (values are held, not re-derived)."""
    dA = (p.beta_G * adopt * (1.0 - A)
          - p.eta * c * A - p.gam_G * A) / vp.tau_v
    dV = (p.beta_G * (1.0 - a) * V * (1.0 - V)
          - p.alpha_G * a * V - p.eta * c * V - p.gam_G * V
          + p.beta_G * adopt * (1.0 - V)) / vp.tau_v
    return dA, dV


def deriv_values(t, y, p: Params, vp: ValuesParams, cp: ConsolParams,
                 sch: Schedule):
    """RHS of the values variant.  Memory OFF: y = [a, G, D, S, g, A, V] —
    the frozen five come from dpdr.model.deriv on the GATED schedule plus the
    two values states.  Memory ON: y = [a, G, D, S, g, W_s, W_t, M_s, M_t,
    A, V] — everything except the two durable-write lines comes from
    dpdr.consolidation.deriv_consol on the GATED schedule; the two write
    lines are recomputed with the value-based class weight (v_self*V(t) when
    value_sel, else consolidation.py's v_self exactly)."""
    A, V = (y[5], y[6]) if not vp.memory else (y[9], y[10])
    cell = [1.0 + vp.kappa_ad * A]
    gsch = GatedSchedule(sch, cell)
    a = y[0]
    c, _te = cannibalization(y[2] - y[1], y[3], p)
    adopt = sch.value("adopt", t)
    dA, dV = _values_rhs(a, c, A, V, adopt, p, vp)
    if not vp.memory:
        f5 = deriv(t, y[:5], p, gsch)
        return [f5[0], f5[1], f5[2], f5[3], f5[4], dA, dV]
    f9 = deriv_consol(t, y[:9], p, cp, gsch)
    W_s, W_t, M_s, M_t = y[5], y[6], y[7], y[8]
    g_self = consolidation_gate(a, cp)
    v_s = cp.v_self * V if vp.value_sel else cp.v_self
    raw_s = v_s * W_s * g_self
    raw_t = cp.v_task * W_t * (1.0 - a)
    tot = raw_s + raw_t
    scale = 0.0 if tot <= 0.0 else min(1.0, cp.B / tot)
    dM_s = raw_s * scale * (1.0 - M_s) - cp.mu_M * M_s
    dM_t = raw_t * scale * (1.0 - M_t) - cp.mu_M * M_t
    return [f9[0], f9[1], f9[2], f9[3], f9[4], f9[5], f9[6], dM_s, dM_t,
            dA, dV]


def simulate_values(p: Params, vp: ValuesParams, cp: ConsolParams,
                    sch: Schedule, T: float, dt: float = 0.05) -> dict:
    """Segmented RK45 on the values variant; returns the frozen Solution
    dict (dpdr.metrics works unmodified) plus the values states ('A', 'V'),
    the realized gate ('u_ext_eff', 'gate'), the value-based class weight
    ('v_self_dyn') and, with memory on, consolidation.py's memory states and
    diagnostics (recomputed on the stored samples, share/flux under the
    VALUE-based weights).

    vp.enabled = False dispatches to the frozen simulate (memory off) or
    simulate_consol (memory on): the variant IS that system, bit-exact."""
    if not vp.enabled:
        return (simulate_consol(p, cp, sch, T, dt) if vp.memory
                else simulate(p, sch, T, dt))
    n = int(round(T / dt))
    grid = np.arange(n + 1) * dt
    T = float(grid[-1])
    bps = [b for b in sch.breakpoints() if 0.0 < b < T]
    for b in bps:
        if abs(b / dt - round(b / dt)) > 1e-9:
            raise ValueError(f"breakpoint {b} not on the dt={dt} grid")
    edges = [0.0] + bps + [T]
    y5 = [p.a0 if vp.a0 is None else vp.a0,
          p.G0 if vp.G0 is None else vp.G0,
          p.D0 if vp.D0 is None else vp.D0,
          p.S0 if vp.S0 is None else vp.S0,
          p.g_init if vp.g_init is None else vp.g_init]
    y = np.array(y5 + ([cp.w0_self if cp.w0_self is not None else p.a0,
                        (1.0 - p.a0) if cp.w0_task is not None else 1.0 - p.a0,
                        cp.m0_self, cp.m0_task] if vp.memory else [])
                 + [vp.a0_val, vp.v0_val], float)
    ts, ys = [], []
    nfev = 0
    for t0, t1 in zip(edges[:-1], edges[1:]):
        tev = grid[(grid >= t0 - 1e-9) & (grid < t1 - 1e-9)] if t1 < T \
            else grid[(grid >= t0 - 1e-9) & (grid <= T + 1e-9)]
        sol = solve_ivp(deriv_values, (t0, t1), y, args=(p, vp, cp, sch),
                        rtol=1e-6, atol=1e-8, max_step=0.5, t_eval=tev)
        ts.append(sol.t)
        ys.append(sol.y)
        y = sol.y[:, -1]
        nfev += sol.nfev
    t = np.concatenate(ts)
    Y = np.concatenate(ys, axis=1)
    a, G, D, S, g = Y[:5]
    E = D - G
    c, Theta_eff = cannibalization_vec(E, S, p)
    A, V = (Y[5], Y[6]) if not vp.memory else (Y[9], Y[10])
    u_ext_g = np.array([sch.value("u_ext", float(tt)) for tt in t])
    gate = 1.0 + vp.kappa_ad * A
    out = dict(t=t, a=a, G=G, D=D, S=S, g=g, E=E, c=c,
               Theta_eff=Theta_eff, u_loop=G / (D + 1e-9),
               collapsed_at=None, nfev=nfev,
               methods=[f"values(mem={int(vp.memory)},"
                        f"valsel={int(vp.value_sel)},k={vp.kappa_ad:g})"],
               A=A, V=V, u_ext_raw=u_ext_g, gate=gate,
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
               v_self_dyn=v_self_arr,
               scale=scale, share_self=share_s,
               flux_self=raw_s * scale * (1.0 - M_s),
               flux_task=raw_t * scale * (1.0 - M_t))
    return out
