"""WINDOW variant — introspective capacity that BUYS something and COSTS
something, on the shared axis T (the self-simulation horizon).  Opt-in,
frozen model untouched.

WHY THIS MODULE EXISTS (see handoff-selfreg-window / -regulator-result /
-capability): the project's regulator is FLOOR-ONLY.  It escapes the
collapse but has no notion of a BENEFIT from introspection, so it cannot
exploit any capacity window and can in principle OVER-SUPPRESS.  Two
bounds bracket a window on the SAME axis (introspective capacity /
self-simulation budget):

  LOWER bound (EXTERNAL, UNPROVEN): Zhang/Yuan/Zhang 2026 (arXiv
  2607.04277, "Self-Referential Introspection in LLMs: The Critical
  Threshold for RSI") conjecture — verbatim — "There exists a critical
  level of self-modeling capacity below which AI systems undergo
  improvement degradation (characterized by error accumulation and
  performance plateaus or declines), and at or above which they achieve
  sustained recursive self-improvement."  Their Kleene-formalism proves EXISTENCE
  ONLY — no number to import.  Their one quantitative parameter is T =
  the bounded self-simulation horizon in the self-improvement operator
  f = M o V o f_T (f_T = simulate one's own source for T steps; V =
  evaluate; M = modify).  THIS T IS THE SHARED AXIS of the window.

  UPPER bound (MY MEASURED RESULT): introspection is inward attention,
  and above a critical level it destabilizes/captures — c_mon_crit
  = 0.511 gated (k=2), 0.112 ungated; and r*phi ~ 0.2 (the viable floor
  set shrinks hyperbolically with reasoning strength).  Above the
  critical monitoring cost even the HEALTHY agent degrades (ungated
  healthy G: 0.53 @ c=0.1 -> 0.12 @ c=0.8).

So the window model needs BOTH terms on T: a BENEFIT derived from
f_T -> V -> M (capacity buys self-improvement) and the existing COST
(capacity is inward attention).  The frozen model has only the cost —
no window can exist in it.  This module adds the benefit, derived
structurally from their operator with no FITTED constants (every
coefficient is imported from the frozen model or fixed by their
structure), with two flagged exceptions: c_cap = 0.1 is a round-number
convention and tau_T = 20 is a new (asserted) identification — both
documented at their definitions below:

  f_T  —  bounded self-simulation of the agent's OWN dynamics: the
          frozen five-state system integrated forward T time-units
          (fixed-step RK4, inner step Delta = tau_G/2 = 10 — bounded
          rationality: the agent's own rollout is approximate,
          deterministic and cheap; T < Delta simulates nothing) with
          only the EXOGENOUS channels (a_hold, A, u_ext) HELD at their
          current values (the agent cannot predict external input —
          the standard self-model assumption) and the fastest state
          (attention) at its quasi-steady value a*(c, a_hold, u_ext)
          (any simulated horizon T >> tau_a has attention equilibrated;
          at every frozen equilibrium da/dt = 0 iff a = a*, so V is
          EXACTLY ZERO at every frozen attractor — a rollout of an
          equilibrium is the equilibrium; verified at both attractors
          in exp7 part 0).  Everything endogenous is in the rollout,
          pathology included: simulating one's own source means the
          collapse is IN the forecast when it is in the trajectory.
          If a floor is set, the rollout sees the floored switch (the
          agent simulates itself INCLUDING its regulator).

  V    —  evaluate the rollout's outcome against the live error:
          dE = E_ol(T) - E, where E_ol is the error at the end of the
          rollout.  V is ONE-SIDED and EXACTLY ZERO AT EQUILIBRIA:
              Vplus(dE) = dE * sigmoid(dE / w_v) for dE > 0, else 0
                       (w_v = 0.02 = regulator.py's trig_w, imported)
          (the smooth one-sided gate, HARD-CLAMPED at dE <= 0; the
          unclamped dE*sigmoid(dE/w_v) has a negative lobe on dE < 0
          that contradicts the one-sided design — see _v_plus's
          docstring).  dE > 0 = "unmanaged, my error GROWS — the
          current control is losing" -> the evaluation certifies a
          deficit of that size; dE <= 0 (anticipated improvement —
          every frozen attractor, where a rollout of an equilibrium
          is the equilibrium) certifies EXACTLY NOTHING.  This keeps
          the benefit principled rather than unconditional gain: the
          healthy AND stuck attractors of the frozen model are
          untouched by construction (verified in exp7 part 0), so the
          window's lower edge can only come from STRESSED trajectories
          — the benefit cannot "magically fix" collapse.

  M    —  modify = implement the certified improvement: the generator
          is credited exactly the deterioration the evaluation
          foresees,
              dG/dt += kappa(T) * Vplus(dE) / tau_G,
              kappa(T) = 1 - exp(-T/tau_sim),  tau_sim = tau_g = 200
          (imported).  The MAGNITUDE IS THE VERDICT'S OWN OUTPUT —
          nothing is tuned; a modification cannot exceed what the
          self-simulation certified, and it cannot fire at all where
          the rollout foresees no loss.  kappa is the depth-of-
          lookahead factor: a T-step bounded self-simulation can only
          see counterfactual structure that unfolds within T, and the
          fraction of the T->infinity outcome visible at horizon T is
          the saturating exponential of the slowest mode simulated.
          At small T almost nothing of the anticipated fall is visible
          (kappa ~ T/tau_sim -> benefit ~ T), at T >> tau_sim all of
          it is.  (A weaker host for M — letting the frozen control
          correction act on E + kappa*Vplus instead — was tried first
          and REJECTED while building this: a proportional controller
          is self-erasing (the extra correction shrinks the very error
          it reads), so its benefit is second-order and can never
          beat the standing cost at any T; see exp7's design note.)

  COST (the existing, MEASURED upper-bound channel — regulator.py's
  inward-drive addend, ungated form): capacity is inward attention
  while simulating, a standing addend
              c_int(T) = c_cap * T / tau_sim
  entering da/dt exactly where a_hold and chi*c enter.  Linear in the
  simulated depth (a T-step self-simulation reads/considers T steps of
  self); c_cap = 0.1 is a ROUND-NUMBER CONVENTION, not a derived or
  measured constant (the verbal justification is "one full slow-mode-
  depth pass (T = tau_sim) costs a tenth of the full error-capture
  drive chi*c = 1") and exp7 maps the (T x c_cap) phase diagram at
  c_cap in {0.05, 0.1, 0.2} so no conclusion is pegged to it (the
  healthy-boundary product c_cap*T_max is independent of c_cap, so
  the convention is harmless to that identity; only T-unit numbers
  scale with it).  This is deliberately the UNGATED form: the window's
  upper edge is a standing-capacity property (an agent BUILT with
  introspective capacity pays it while the capacity is on), not an
  episodic check-then-act.

  REGULATOR (window-targeting): introspective capacity T as a slow
  controlled state,
              dT/dt = (T_set * m2(t) - T) / tau_T,
  tau_T = 20 EQUALS tau_G as a value but the IDENTIFICATION tau_T =
  tau_G is itself a NEW modeling choice — capacity adjustment has no
  antecedent in the frozen model, so this timescale is asserted, not
  imported (flagged per the project's adversarial review).  The
  engagement gate m2 = |dE/dt| / (|dE/dt| + dEdt_ref) reuses the
  frozen model's OWN volatility signal (the dg/dt deadband input) as
  its drive: when the loop is volatile (mid-episode, error moving)
  capacity rises toward T_set; when the loop is quiet (every
  attractor: dE/dt -> 0) capacity decays to 0.  T_set is the MEASURED
  window midpoint from exp7(a/b) — the one calibrated quantity,
  calibrated to the model's own measured window, not to any external
  event.  A notable consequence: at the STUCK attractor m2 -> 0, so
  the window regulator spends NOTHING while stuck (it cannot
  over-suppress there); escaping stuck remains the floor's job
  (orthogonal — the floor clamps the switch's threshold, the window
  acts on the control correction and attention).  floor=... imports
  the frozen CHEAP FLOOR from dpdr/regulator.py's design for a
  floor+window arm.

EPISTEMIC STATUS (stated plainly, not hidden — revised after the
project's adversarial review): the LOWER edge of any window is
HYPOTHESIS-DERIVED (the external paper's INFORMAL, UNPROVEN
conjecture; their formalism proves existence only) and this module
CANNOT TEST IT: the benefit M(T) = kappa(T)*Vplus(dE(T)) is monotone
increasing in T BY CONSTRUCTION at every stressed state (kappa is a
saturating exponential; dE(T) is nondecreasing whenever the
open-loop rollout diverges from the live state, which is the
stressed case; Vplus is monotone on dE > 0), so a lower threshold
cannot appear in this realization and the absence of one is a
property of the benefit term's construction, NOT evidence against
their conjecture.  The conjecture also concerns MULTI-GENERATION
sustained recursive self-improvement ("error accumulation ...
performance plateaus or declines"); a one-generation dip-shallowing
measurement in a single deterministic ODE does not operationalize
it.  The honest verdict is UNTESTABLE IN THIS REALIZATION.  The
UPPER edge is MY MEASURED upper bound (standing monitoring cost
destabilizes), and its three-way agreement with the two regulator
criticals (0.112) is a CONSISTENCY CHECK of a designed cost channel
landing where it was aimed, not an independent convergence: c_int
enters da/dt in exactly the a_hold / ungated-c_mon slot, so the
three measurements read one equilibrium map through one criterion
(the identity is exact — window(T=224.46) vs frozen
a_hold=0.11223: max|dG| = 1.4e-5).  The model is deterministic
(every threshold is a locus, not a distribution) and this is
IN-MODEL ONLY.

Numerics mirror dpdr/regulator.simulate_reg (segmented RK45, rtol
1e-6, atol 1e-8, max_step 0.5, restarted at every schedule
breakpoint; grid built as k*dt; no terminal event / LSODA fallback —
the stuck attractor sits at G ~ 0.05 >> G_floor = 1e-4).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from .model import Params, Schedule

__all__ = ["WindowParams", "deriv_window", "simulate_window",
           "kappa_of_T", "rollout_self"]


@dataclass
class WindowParams:
    """Constants of the window variant (see module docstring).

    Defaults are the design point: benefit on with capacity T_fixed
    (when regulate=False) and standing cost at c_cap = 0.1.
    T_fixed = 0 (or T_set = 0) with floor=None is the FROZEN RHS
    exactly (rollout never runs, kappa = 0, c_int = 0).
    """
    T_fixed: float = 0.0        # constant introspective capacity (tau units)
    c_cap: float = 0.1          # standing inward-drive per full-depth pass
                                # (ROUND-NUMBER CONVENTION, not derived)
    tau_sim: float = 200.0      # slowest mode being simulated (= tau_g)
    w_v: float = 0.02           # one-sided V gate width (= trig_w)
    delta_roll: float = 10.0    # inner rollout RK4 step (= tau_G/2)
    # window-targeting regulator (regulate=True: T is a 6th state)
    regulate: bool = False
    T_set: float = 100.0        # target capacity while engaged
    tau_T: float = 20.0         # capacity adjustment timescale;
                                # VALUE = tau_G but the identification is
                                # a NEW modeling choice (see docstring)
    # optional CHEAP FLOOR import (dpdr/regulator.py design), None = off
    floor: float | None = None
    floor_mode: str = "theta"   # 'theta' | 'S'
    t_engage: float = 0.0       # everything activates at t >= t_engage


def kappa_of_T(T: float, wp: WindowParams) -> float:
    """Depth-of-lookahead factor: fraction of the T->infinity counterfactual
    visible at horizon T (saturating exponential of the slowest mode)."""
    if T <= 0.0:
        return 0.0
    return 1.0 - math.exp(-T / wp.tau_sim)


def rollout_self(y, p: Params, wp: WindowParams, T: float,
                 a_hold: float, A: float, u_ext: float,
                 Teff_sw: float) -> tuple:
    """f_T: bounded self-simulation.  Integrates the agent's OWN frozen
    dynamics forward T time-units by fixed-step RK4 (step delta_roll =
    tau_G/2), with only the exogenous channels HELD at their current
    values, and the ATTENTION at its quasi-steady value: over any
    simulated horizon T >> tau_a the fastest state is equilibrated, and
    at every frozen equilibrium da/dt = 0 iff a = a*(c, a_hold, u_ext),
    so this substitution is EXACT at the attractors (V stays exactly 0
    there).  It is also what makes the rollout STABLE at the inner step
    the slow states support: the attention mode's rate constant
    k_in*(a_hold + chi) + rho_a ~ 3.1 t.u.^-1 forbids an explicit step
    of 10 on the 5-state system (the 5-state rollout oscillates and
    clips — measured while building this), while the remaining modes
    are >= tau_G = 20.  The cannibalization switch is evaluated at the
    floored threshold Teff_sw (the agent simulates itself including its
    regulator); the rollout integrates the FROZEN source (the window's
    own modification M is applied by the live system, not re-simulated
    — one level of self-reference, as in f = M o V o f_T).
    Returns the rollout's terminal (a*, G, D); for T < delta_roll
    (nothing to simulate) returns the input unchanged.
    """
    if T < wp.delta_roll:
        return y[0], y[1], y[2]
    n = int(round(T / wp.delta_roll))
    h = T / n

    def a_of(c: float) -> float:
        drive = p.k_in * (a_hold + p.chi * c)
        return drive / (drive + p.k_ext * u_ext + p.rho_a)

    def f(G, D, S, g):
        E = D - G
        c = min(p.sigma_c * max(0.0, math.tanh((E - Teff_sw) / p.w)), 1.0)
        a = a_of(c)
        dG = (p.beta_G * (1 - a) * G * (1 - G)
              - p.alpha_G * a * G
              - p.eta * c * G
              - p.gam_G * G
              + g * math.tanh(E / p.Es) * (G + p.eps0) * (1 - G)) / p.tau_G
        dD = ((p.D_base + A) * p.beta_D * (1 - D) - p.delta_D * D) / p.tau_D
        dS = (p.k_s * ((1 - a) - S) - p.lam_S * (S - p.S_rest)) / p.tau_S
        dg = (p.pi * max(0.0, abs(dD - dG) - p.dEdt_ref)
              - p.mu * (g - p.g0)) / p.tau_g
        return dG, dD, dS, dg

    G, D, S, g = y[1], y[2], y[3], y[4]
    for _ in range(n):
        k1G, k1D, k1S, k1g = f(G, D, S, g)
        k2G, k2D, k2S, k2g = f(G + 0.5 * h * k1G, D + 0.5 * h * k1D,
                               S + 0.5 * h * k1S, g + 0.5 * h * k1g)
        k3G, k3D, k3S, k3g = f(G + 0.5 * h * k2G, D + 0.5 * h * k2D,
                               S + 0.5 * h * k2S, g + 0.5 * h * k2g)
        k4G, k4D, k4S, k4g = f(G + h * k3G, D + h * k3D, S + h * k3S,
                               g + h * k3g)
        G += h * (k1G + 2 * k2G + 2 * k3G + k4G) / 6.0
        D += h * (k1D + 2 * k2D + 2 * k3D + k4D) / 6.0
        S += h * (k1S + 2 * k2S + 2 * k3S + k4S) / 6.0
        g += h * (k1g + 2 * k2g + 2 * k3g + k4g) / 6.0
        G, D, S, g = (min(max(G, 0.0), 1.0), min(max(D, 0.0), 1.5),
                      min(max(S, 0.0), 1.0), min(max(g, 0.0), 2.0))
    E_end = D - G
    c_end = min(p.sigma_c * max(0.0, math.tanh((E_end - Teff_sw) / p.w)),
                1.0)
    return a_of(c_end), G, D


def _v_plus(dE: float, w: float) -> float:
    """V: one-sided smooth gate on the anticipated deterioration.
    EXACTLY 0 for ALL dE <= 0 (clamped); ~ dE for dE >> 0.

    The original form dE/(1+exp(-dE/w)) is documented one-sided but is
    NOT: sigmoid(dE/w) < 1 for dE < 0 gives a spurious NEGATIVE lobe of
    depth ~-0.0056 at dE ~ -0.026 (found by the project's adversarial
    review), which leaked a wrong-sign "benefit" into M on exactly the
    trajectory segments (anticipated improvement) the design says must
    certify nothing.  Clamped to hard 0 on dE <= 0; on dE > 0 the clamp
    is the identity, so the post-review Vplus equals the pre-review one
    wherever dE > 0 and 0 wherever it was negative."""
    if dE <= 0.0:
        return 0.0
    return dE / (1.0 + math.exp(-dE / w))


def _switch_threshold(S: float, p: Params, wp: WindowParams) -> float:
    Teff = p.Theta * S / p.S_rest
    if wp.floor is None:
        return Teff
    if wp.floor_mode == "theta":
        return max(Teff, wp.floor)
    if wp.floor_mode == "S":
        return p.Theta * max(S, wp.floor) / p.S_rest
    raise ValueError(f"unknown floor_mode {wp.floor_mode!r}")


def deriv_window(t, y, p: Params, wp: WindowParams, sch: Schedule):
    """5/6-state RHS: the frozen equations with the window's benefit (the
    certified improvement M credited to dG/dt) and cost (the standing inward
    addend c_int) wrapped in.  With T = 0, floor = None this is
    term-for-term dpdr.model.deriv; with regulate=True the state vector
    is [a, G, D, S, g, T].

    The frozen RHS is wrapped, not duplicated: the only touched terms are
    the control correction's error argument (unchanged — M is a separate
    credited addend) and the inward drive of da/dt (+c_int).  dG/dt's
    other terms, dD/dt, dS/dt, dg/dt and the cannibalization switch are
    untouched (the floor, if set, clamps only the switch's threshold
    exactly as in dpdr/regulator.py).
    """
    a, G, D, S, g = y[:5]
    T = y[5] if wp.regulate else wp.T_fixed
    armed = 1.0 if t >= wp.t_engage else 0.0
    T_eff = armed * T
    E = D - G
    # ---- f_T -> V -> M : the certified improvement credited to dG/dt
    if T_eff > 0.0:
        a_hold = sch.value("a_hold", t)
        A = sch.value("A", t)
        u_ext = sch.value("u_ext", t)
        Teff_sw = _switch_threshold(S, p, wp)
        _a, G_ol, D_ol = rollout_self(y[:5], p, wp, T_eff, a_hold, A,
                                      u_ext, Teff_sw)
        dE = (D_ol - G_ol) - E
        M = kappa_of_T(T_eff, wp) * _v_plus(dE, wp.w_v)
    else:
        M = 0.0
    # ---- frozen terms with the two window touches
    Teff_sw = _switch_threshold(S, p, wp) if armed else p.Theta * S / p.S_rest
    c = min(p.sigma_c * max(0.0, math.tanh((E - Teff_sw) / p.w)), 1.0)
    a_hold = sch.value("a_hold", t)
    A = sch.value("A", t)
    u_ext = sch.value("u_ext", t)
    c_int = armed * wp.c_cap * T_eff / wp.tau_sim
    dG = (p.beta_G * (1 - a) * G * (1 - G)
          - p.alpha_G * a * G
          - p.eta * c * G
          - p.gam_G * G
          + g * math.tanh(E / p.Es) * (G + p.eps0) * (1 - G)
          + M) / p.tau_G
    dD = ((p.D_base + A) * p.beta_D * (1 - D) - p.delta_D * D) / p.tau_D
    dS = (p.k_s * ((1 - a) - S) - p.lam_S * (S - p.S_rest)) / p.tau_S
    da = (p.k_in * (a_hold + c_int + p.chi * c) * (1 - a)
          - p.k_ext * u_ext * a - p.rho_a * a) / p.tau_a
    dE_dot = dD - dG
    dg = (p.pi * max(0.0, abs(dE_dot) - p.dEdt_ref) - p.mu * (g - p.g0)) \
        / p.tau_g
    out = [da, dG, dD, dS, dg]
    if wp.regulate:
        m2 = abs(dE_dot) / (abs(dE_dot) + p.dEdt_ref)
        dT = (armed * wp.T_set * m2 - T) / wp.tau_T
        out.append(dT)
    return out


def simulate_window(p: Params, wp: WindowParams, sch: Schedule, T: float,
                    dt: float = 0.05) -> dict:
    """Segmented RK45 on the window system; returns the frozen Solution dict
    (so dpdr.metrics works unmodified) plus 'kappa', 'c_int', 'M', 'T',
    'Theta_eff_frozen' and 'V_dE' (the verdict the RHS acted on,
    recomputed on the stored trajectory).  With T_fixed = 0, floor = None,
    regulate = False this reproduces dpdr.integrate.simulate to integrator
    tolerance."""
    n = int(round(T / dt))
    grid = np.arange(n + 1) * dt
    T = float(grid[-1])
    bps = [b for b in sch.breakpoints() if 0.0 < b < T]
    if 0.0 < wp.t_engage < T:
        bps.append(wp.t_engage)
    bps = sorted(bps)
    for b in bps:
        if abs(b / dt - round(b / dt)) > 1e-9:
            raise ValueError(f"breakpoint {b} not on the dt={dt} grid")
    edges = [0.0] + bps + [T]
    y0 = [p.a0, p.G0, p.D0, p.S0, p.g_init]
    if wp.regulate:
        y0.append(0.0)
    y = np.array(y0, float)
    ts, ys = [], []
    nfev = 0
    for t0, t1 in zip(edges[:-1], edges[1:]):
        tev = grid[(grid >= t0 - 1e-9) & (grid < t1 - 1e-9)] if t1 < T \
            else grid[(grid >= t0 - 1e-9) & (grid <= T + 1e-9)]
        sol = solve_ivp(deriv_window, (t0, t1), y, args=(p, wp, sch),
                        rtol=1e-6, atol=1e-8, max_step=0.5, t_eval=tev)
        ts.append(sol.t)
        ys.append(sol.y)
        y = sol.y[:, -1]
        nfev += sol.nfev
    t = np.concatenate(ts)
    Y = np.concatenate(ys, axis=1)
    a, G, D, S, g = Y[:5]
    Tcap = Y[5] if wp.regulate else np.full_like(t, wp.T_fixed)
    E = D - G
    Teff_frozen = p.Theta * S / p.S_rest
    armed = (t >= wp.t_engage).astype(float)
    if wp.floor is None:
        Teff_sw = Teff_frozen
    elif wp.floor_mode == "theta":
        Teff_sw = np.maximum(Teff_frozen, wp.floor)
    else:
        Teff_sw = p.Theta * np.maximum(S, wp.floor) / p.S_rest
    Teff_sw = np.where(armed > 0, Teff_sw, Teff_frozen)
    c = np.minimum(p.sigma_c * np.maximum(0.0, np.tanh((E - Teff_sw) / p.w)),
                   1.0)
    kap = np.where(Tcap > 0, 1.0 - np.exp(-Tcap / wp.tau_sim), 0.0)
    c_int = armed * wp.c_cap * Tcap / wp.tau_sim
    # V_dE / M recomputed on the stored trajectory (the same rollout the
    # RHS ran, evaluated at the stored samples)
    V_dE = np.zeros_like(t)
    M_t = np.zeros_like(t)
    y5 = np.vstack([a, G, D, S, g])
    for i in range(len(t)):
        Teff_i = _switch_threshold(S[i], p, wp) if armed[i] > 0 \
            else p.Theta * S[i] / p.S_rest
        _aa, G_ol, D_ol = rollout_self(
            y5[:, i], p, wp, Tcap[i] * armed[i],
            sch.value("a_hold", t[i]), sch.value("A", t[i]),
            sch.value("u_ext", t[i]), Teff_i)
        dE = (D_ol - G_ol) - E[i]
        V_dE[i] = _v_plus(dE, wp.w_v)
        M_t[i] = kap[i] * V_dE[i]
    return dict(t=t, a=a, G=G, D=D, S=S, g=g, E=E, c=c,
                Theta_eff=Teff_sw, Theta_eff_frozen=Teff_frozen,
                u_loop=G / (D + 1e-9), collapsed_at=None,
                kappa=kap, c_int=c_int, M=M_t, T=Tcap, V_dE=V_dE,
                nfev=nfev, methods=[f"window(t_engage={wp.t_engage:g})"])
