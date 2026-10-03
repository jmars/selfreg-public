"""Permissive two-axis AND-gate variant — opt-in, frozen model untouched.

CONTEXT (the discrepancy this addresses; see predictions.md §"two-axis
permissive gate"): the FROZEN model is single-factor-sufficient — sustained
inward attention ALONE collapses it (a_hold 0.35 held 1400 t.u. -> G stuck
at 0.0485; affect alone never collapses; see handoff-selfreg-conjunction).
The reported etiology was a CONJUNCTION of four factors (near-total
contemplation, strong affect, endurance load, pharmacology).  This module
makes the AND-gate structure EXPLICIT AND TESTABLE rather than asserted.

The two axes (from the resolved supplement composition — handoff-selfreg-pharma
— NOT invented here):

  FAST / serotonergic, recurring nightly:  the nightly capsule (5-HTP +
  Rhodiola rosea (a documented MAO inhibitor) + Ashwagandha KSM-66 =
  precursor + reduced degradation + modulation co-administered) gives a
  RECURRING PERMISSIVE WINDOW — this is the axis that accounts for
  late-at-night timing (the event is time-locked to the nightly peak).
  Represented by a new exogenous schedule channel 'ser': during a nightly
  window of width W the serotonergic tone amplitude is ser, else 0.

  SLOW / neurotrophic, accumulating over weeks and persisting:  daily
  Lion's Mane NGF induction.  Represented by the channel 'ngf': each daily
  dose adds one unit to an accumulator N (in units of a full-dose day);
  N is the "structural permission" that maps onto the model's G2b
  no-self-recovery property (mu_N = 0 below).

STRUCTURAL CHANGE: the allostatic weakening term becomes multiplicative in
two thresholded variables,

    dG/dt weakening:   - Phi(t) * alpha_G * a * G,
    Phi(t) = Phi_max * g_fast(A_ser(t)) * g_slow(N(t)),

    g_fast = A_ser / (A_ser + K_ser)           (Hill n=1; K_ser = 0.25)
    g_slow = 1 / (1 + exp(-(N - N50) / Nw))    (N50 = 14, Nw = 4)

so collapse requires inward drive a AND fast-axis tone AND slow-axis
accumulation.

IMPORTANT SEMANTICS (this is the tested claim, not a bug): the FROZEN model
is recovered at Phi = 1 (pin_phi = 1 below reproduces dpdr.integrate
.simulate to integrator tolerance, max |dG| <= 1.4e-5 over the standard
scenarios — the RHS is wrapped, not duplicated: only alpha_G is rescaled).  Phi = 0 — both axes
absent — REMOVES the weakening term entirely, so under this gate NO length
of inward attention alone can collapse the system.  That deliberate break
with the frozen model's single-factor sufficiency (a_hold 0.35 x 1400 t.u.)
is the conjunction claim made testable; see exp5 part (a).

pin_phi (default None) pins Phi at a constant: pin_phi = 1 is the
gate-disengaged control used by check_gates_perm; pin_phi = P > 0 is the
frozen RHS with alpha_G <- P*alpha_G — the constant-Phi dose-response assay
for the phase boundary (exp5 part b).

HYPOTHESIS-SPACE CHOICES (each principled, none fitted to any event):

  * Phi_max = 2.0 — "the fully expressed conjunction doubles the allostatic
    weakening rate".  Round number; the frozen model's single-factor
    behaviour is the Phi = 1 locus, so Phi_max = 2 spans sub-frozen
    (0 < Phi < 1, harder to collapse) and super-frozen (1 < Phi <= 2,
    easier) regimes.  The phase boundary (part b) is mapped over the full
    rectangle, so conclusions are not pegged to this value.
  * Hill n = 1 saturating g_fast — the minimal saturating dose-response;
    K_ser = 0.25 = half-max at a quarter-full nightly load.  Half-max
    semantics, not a fitted value.
  * Sigmoid g_slow with N50 = 14 days — "a couple of weeks of daily NGF
    induction before structural permission is meaningfully expressed";
    Nw = 4 days gives a graded (not switch-like) transition.  N50/Nw are
    read as week-scale physiology, not tuned to any observed onset.
  * mu_N = 0 — the G2b analog: nothing in the variant erases N
    (community reports describe persistence after cessation).  The
    symmetric control mu_N = 1/42 per day (~6-week washout) is provided;
    as with variants.RetuneParams, mu_N = 0 cannot be adjudicated by
    internal evidence alone — part (d) is the external test.
  * Timescale mapping: 1 t.u. = 5 real minutes (tau_a = 1 t.u. = 5 min is
    the physiological attentional timescale; fixates T_day = 288 t.u. = 24 h
    and W = 96 t.u. = 8 h nightly window).  The nightly period is a
    PHYSIOLOGICAL FACT, not a choice; W = 8 h is a nominal night's
    dosing window (5-HTP + MAO-I co-administration spanning sleep).

INFERRED-MECHANISM CAVEATS (documented, not resolvable here): the link from
serotonergic tone / NGF to this G pathway is INFERRED from composition +
timing, not established; sleep architecture (5-HTP -> melatonin shifts,
caffeine + endurance load -> sleep pressure; sleep deprivation is an
independent DPDR trigger) is an UNRESOLVABLE CONFOUND in this single case.

Numerics mirror variants.simulate_variant (segmented RK45, rtol 1e-6,
atol 1e-8, max_step 0.5, restarted at every schedule breakpoint, no
collapse event / LSODA fallback — see its docstring); see
experiments/exp5_permissive.py for the measurement battery.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np
from scipy.integrate import solve_ivp

from .events import baseline_schedule, failure_schedule, rescue_schedule
from .model import Params, Schedule, cannibalization, cannibalization_vec

__all__ = ["PermissiveParams", "phi", "deriv_perm", "simulate_perm",
           "check_gates_perm", "T_DAY", "NIGHT_W"]


# timescale mapping (physiological fact): 1 t.u. = 5 min -> 24 h = 288 t.u.
T_DAY = 288.0
# nightly serotonergic window width: 8 h = 96 t.u. (nominal night's dosing)
NIGHT_W = 96.0


@dataclass
class PermissiveParams:
    """Constants of the two-axis permissive gate (see module docstring)."""
    Phi_max: float = 2.0
    K_ser: float = 0.25
    N50: float = 14.0
    Nw: float = 4.0
    mu_N: float = 0.0
    N0: float = 0.0
    pin_phi: float | None = None   # None = the gate; 1 = frozen model

    def g_fast(self, ser: float) -> float:
        return ser / (ser + self.K_ser)

    def g_slow(self, N: float) -> float:
        return 1.0 / (1.0 + math.exp(-(N - self.N50) / self.Nw))


def phi(t: float, N: float, ser: float, q: PermissiveParams) -> float:
    """Permissive factor Phi(t) = Phi_max * g_fast(A_ser(t)) * g_slow(N(t))"""
    if q.pin_phi is not None:
        return q.pin_phi
    return q.Phi_max * q.g_fast(ser) * q.g_slow(N)


def deriv_perm(t, y, p: Params, q: PermissiveParams, sch: Schedule):
    """Six-state RHS: the frozen five states with Phi multiplying the
    allostatic weakening term, plus dN/dt = dosing - washout.

    The frozen RHS is WRAPPED, not duplicated: only the single weakening
    term alpha_G*a*G is rescaled, by Phi computed from the schedule value
    'ser' and the state N alone (no other frozen term is touched).
    """
    a, G, D, S, g, N = y
    E = D - G
    c, _te = cannibalization(E, S, p)
    a_hold = sch.value("a_hold", t)
    A = sch.value("A", t)
    u_ext = sch.value("u_ext", t)
    ser = sch.value("ser", t)
    ngf = sch.value("ngf", t)
    ph = phi(t, N, ser, q)
    dG = (p.beta_G * (1 - a) * G * (1 - G)
          - ph * p.alpha_G * a * G
          - p.eta * c * G
          - p.gam_G * G
          + g * math.tanh(E / p.Es) * (G + p.eps0) * (1 - G)) / p.tau_G
    dD = ((p.D_base + A) * p.beta_D * (1 - D) - p.delta_D * D) / p.tau_D
    dS = (p.k_s * ((1 - a) - S) - p.lam_S * (S - p.S_rest)) / p.tau_S
    da = (p.k_in * (a_hold + p.chi * c) * (1 - a)
          - p.k_ext * u_ext * a - p.rho_a * a) / p.tau_a
    dE = dD - dG
    dg = (p.pi * max(0.0, abs(dE) - p.dEdt_ref) - p.mu * (g - p.g0)) / p.tau_g
    dN = ngf - q.mu_N * N / T_DAY
    return [da, dG, dD, dS, dg, dN]


def simulate_perm(p: Params, q: PermissiveParams, sch: Schedule, T: float,
                  dt: float = 0.05) -> dict:
    """Segmented RK45 on the six-state variant; returns the frozen Solution
    dict plus the slow-axis state 'N' and 'phi' (Phi on the output grid).
    With q.pin_phi = 1 this reproduces the frozen dpdr.integrate.simulate
    to integrator tolerance (same numerics; see variants.simulate_variant's
    docstring for the same two inert divergences: no collapse event, no
    LSODA fallback).

    Grid note: the output grid is built as k*dt (integer multiples), NOT
    np.arange(0, T, dt) — arange's accumulated endpoint can land ~1e-13
    ABOVE the requested T (e.g. T = 556.55 -> 556.5500000000001), and
    solve_ivp's t_eval-within-t_span check is strict, so the final segment
    would raise.  The final segment edge is grid[-1] itself, which makes
    any on-grid horizon safe."""
    n = int(round(T / dt))
    grid = np.arange(n + 1) * dt
    T = float(grid[-1])
    bps = [b for b in sch.breakpoints() if 0.0 < b < T]
    for b in bps:
        if abs(b / dt - round(b / dt)) > 1e-9:
            raise ValueError(f"breakpoint {b} not on the dt={dt} grid")
    edges = [0.0] + bps + [T]
    y = np.array([p.a0, p.G0, p.D0, p.S0, p.g_init, q.N0], float)
    ts, ys = [], []
    for t0, t1 in zip(edges[:-1], edges[1:]):
        tev = grid[(grid >= t0 - 1e-9) & (grid < t1 - 1e-9)] if t1 < T \
            else grid[(grid >= t0 - 1e-9) & (grid <= T + 1e-9)]
        sol = solve_ivp(deriv_perm, (t0, t1), y, args=(p, q, sch),
                        rtol=1e-6, atol=1e-8, max_step=0.5, t_eval=tev)
        ts.append(sol.t)
        ys.append(sol.y)
        y = sol.y[:, -1]
    t = np.concatenate(ts)
    Y = np.concatenate(ys, axis=1)
    a, G, D, S, g, N = Y
    E = D - G
    c, Theta_eff = cannibalization_vec(E, S, p)
    if q.pin_phi is not None:
        phi_g = np.full_like(t, q.pin_phi)
    else:
        ser = np.array([sch.value("ser", float(tt)) for tt in t])
        phi_g = q.Phi_max * (ser / (ser + q.K_ser)) / (
            1.0 + np.exp(-(N - q.N50) / q.Nw))
    return dict(t=t, a=a, G=G, D=D, S=S, g=g, N=N, phi=phi_g, E=E, c=c,
                Theta_eff=Theta_eff, u_loop=G / (D + 1e-9))


def check_gates_perm(q: PermissiveParams, p: Params | None = None,
                     T_base: float = 1000.0, T_fail: float = 600.0,
                     T_resc: float = 1400.0) -> dict:
    """G1-G2c gate checks on the variant with Phi pinned at 1 (the frozen
    model): mirrors dpdr.metrics.check_gates line for line.  Used to verify
    the WRAP is faithful — with the gate engaged (pin_phi = None) the
    single-factor scenarios are no longer the frozen model's, by design.
    NOT a regression test."""
    from .metrics import EPISODE, RESCUE, stuck_duration
    p = p if p is not None else Params()
    q = replace(q, pin_phi=1.0)
    out: dict[str, bool] = {}
    s = simulate_perm(p, q, baseline_schedule(), T_base)      # G1
    out["G1"] = bool(0.0 < s["G"][-1] < 1.0 and s["E"][-1] < p.Theta
                     and s["c"][-1] < 0.05)
    s = simulate_perm(p, q, failure_schedule(), T_fail)       # G2, G2b
    w = s["t"] >= EPISODE[1] + 10 * p.tau_G
    out["G2"] = bool(s["G"][-1] < 0.1 and s["E"][-1] > p.Theta
                     and s["c"][-1] > 0.5)
    out["G2b"] = bool(s["G"][w].max() < 0.1 and stuck_duration(s, p)
                      >= 10 * p.tau_G)
    s = simulate_perm(p, q, rescue_schedule(), T_resc)        # G2c
    w = s["t"] >= RESCUE[1]
    out["G2c"] = bool(s["G"][-1] > 0.5 and s["G"][w].min() > 0.5)
    return out
