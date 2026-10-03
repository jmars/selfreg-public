"""Variants: opt-in hypothesis-space extensions of the frozen model.

NOTHING in this module modifies the frozen Params or the canonical equations
(dpdr/model.py, sim0.py and the gates are untouched); the variant wraps the
frozen five-state RHS and adds one state.  Opt-in: importing dpdr alone never
activates any of this.

Variant "retune" — the PARAMETER-LEVEL vigilance hypothesis
----------------------------------------------------------
The plan fused two distinct claims into P5:

  H1 (STATE-level):    vigilance = a persistent offset g* > g0.  Requires a
      continuous inflow to survive the restoring term -mu*(g-g0) in dg/dt;
      agent-mediated ("conscious vigilance").  FALSIFIED in the frozen model:
      g* -> g0 exactly (fitted asymptote C ~ 0, relaxation tau = tau_g/mu
      ~ 667 t.u.; experiments/exp3_postrecovery.py, predictions.md P5).

  H2 (PARAMETER-level): vigilance = the loop's CONSTANTS change (faster
      error correction / higher damping) while g* stays = g0.  Automatic —
      needs no agent, no effort, no felt vigilance.  ABSENT from the frozen
      model: every constant is frozen by construction.

This module implements H2 as a sixth state kappa(t) — a dynamic multiplier on
the control correction term (the same g*tanh(E/Es)*(G+eps0)*(1-G) actuator the
frozen model already has; kappa = 1 leaves the five frozen equations
term-for-term identical, and RetuneParams(kappa_b=1, kmax=1) reproduces
dpdr.integrate.simulate to INTEGRATOR TOLERANCE, not bit-exactly — three
known code-level divergences, all inert in exp4's runs, are documented in
simulate_variant's docstring):

  dG/dt control term:   kappa * g * tanh(E/Es) * (G+eps0) * (1-G)
  dkappa/dt = ( pi_k * max(0, |dE/dt| - ref_k) * sat(kappa)
              - mu_k * (kappa - kappa_b) ) / tau_k
  sat(kappa) = max(0, (ln kmax - ln kappa) / (ln kmax - ln kappa_b))

Design points (each is a hypothesis-space choice, NOT a fit to any data):

  * The drive is the SAME volatility signal that already drives g — no new
    observability, no metaplasticity beyond one leaky integrator on a
    constant.  H2 says the loop retunes WHAT IT ALREADY MONITORS.
  * sat(kappa) -> 0 as kappa -> kmax: the retuning saturates.  This is the
    safety property that keeps the variant inside the frozen model's own
    phenomenology — the control term's coefficient can never exceed kmax,
    so the G2 stuck attractor / G2b no-self-recovery / G2c rescue structure
    is preserved (verified in experiments/exp4_discriminator.py; at frozen
    parameters the stuck state survives even kappa pinned at kmax).
  * mu_k = 0 (default) is the RATCHET: dkappa/dt >= 0, so kappa holds
    whatever it accumulated — persistence needs no continuous inflow, only
    the monotone floor (contrast H1: an offset with a restoring force
    decays, so it must be fed continuously).  SCOPE: this is a claim about
    the mu_k-FAMILY realized by this one extension, not "memory not
    effort" as a general mechanism — the ratchet is the mu_k = 0 member of
    a continuous family (N=2 kappa offset +2.14 / +2.05 / +1.97 / +1.67 /
    +0.95 / +0.21% at mu_k = 0 / 0.005 / 0.01 / 0.03 / 0.1 / 0.3), so the
    data-relevant question is the mu_k bound.  And nothing in the variant
    erases kappa, so mu_k = 0 cannot be adjudicated by internal evidence
    alone — only by the external accumulation prediction (exp4 part b3).
    mu_k > 0 is the symmetric negative control: kappa, like g, relaxes
    toward baseline — present-but-small at short delays (mu_k = mu leaves
    +0.21% at N=2, delay 1080) and decayed away at long ones.
  * Constants (pi_k=pi, ref_k=dEdt_ref, tau_k=tau_g) are copied from the
    frozen g-loop's own values rather than chosen: the ratchet integrates
    the same drive at the same rate the frozen model already integrates it.
    Nothing is tuned to produce any particular vigilance magnitude.

Measured consequence: faster closed-loop error correction with g* = g0 —
see experiments/exp4_discriminator.py for the separable signatures (a)
steady-state g*/g0, (b) post-rescue correction speed vs probe delay,
(c) second-episode response.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from .events import baseline_schedule, failure_schedule, rescue_schedule
from .model import Params, Schedule, cannibalization, cannibalization_vec

__all__ = ["RetuneParams", "RetunedParams", "simulate_variant",
           "check_gates_variant", "dkappa"]


@dataclass
class RetuneParams:
    """Constants of the parameter-level retuning state kappa(t).

    Defaults implement the persistent (ratchet) form; set mu_k > 0 for the
    symmetric-leak negative control.  Pin kappa at a constant K with
    RetuneParams(kappa_b=K, kmax=K) (sat and leak both vanish).
    """
    kappa_b: float = 1.0    # baseline multiplier (= frozen model)
    kmax: float = 1.25      # saturation ceiling (safety cap on the retuning)
    pi_k: float = 1.5       # volatility drive  (frozen pi)
    ref_k: float = 0.002    # volatility deadband (frozen dEdt_ref)
    tau_k: float = 200.0    # integration timescale (frozen tau_g)
    mu_k: float = 0.0       # leak: 0 = ratchet (persistent), >0 = relaxes
    kappa0: float = 1.0     # initial multiplier


@dataclass
class RetunedParams(Params):
    """Frozen Params + the variant's initial kappa (no other change)."""
    kappa_init: float = 1.0


def dkappa(kappa: float, absdE: float, vp: RetuneParams) -> float:
    """RHS of the kappa state (see module docstring)."""
    span = math.log(vp.kmax) - math.log(vp.kappa_b)
    sat = 0.0 if span <= 0.0 else max(
        0.0, (math.log(vp.kmax) - math.log(kappa)) / span)
    drive = vp.pi_k * max(0.0, absdE - vp.ref_k) * sat
    leak = vp.mu_k * (kappa - vp.kappa_b)
    return (drive - leak) / vp.tau_k


def deriv_retune(t, y, p: Params, vp: RetuneParams, sch: Schedule):
    """Six-state RHS: the frozen five states with kappa multiplying the
    control correction, plus dkappa/dt.

    NOTE: the five frozen terms are DUPLICATED from model.deriv, not
    wrapped: kappa multiplies a single term INSIDE dG (the control
    correction), so the frozen derivative cannot be rescaled post hoc —
    the term has to be rebuilt here.  The duplicate agrees with
    model.deriv bit-for-bit today (max |f - f_retune| = 0.0 over 3000
    random states at kappa=1); a future edit to model.py silently desyncs
    this copy, so re-verify that equivalence if model.py ever changes."""
    a, G, D, S, g, kap = y
    E = D - G
    c, _te = cannibalization(E, S, p)
    a_hold = sch.value("a_hold", t)
    A = sch.value("A", t)
    u_ext = sch.value("u_ext", t)
    dG = (p.beta_G * (1 - a) * G * (1 - G)
          - p.alpha_G * a * G
          - p.eta * c * G
          - p.gam_G * G
          + kap * g * math.tanh(E / p.Es) * (G + p.eps0) * (1 - G)) / p.tau_G
    dD = ((p.D_base + A) * p.beta_D * (1 - D) - p.delta_D * D) / p.tau_D
    dS = (p.k_s * ((1 - a) - S) - p.lam_S * (S - p.S_rest)) / p.tau_S
    da = (p.k_in * (a_hold + p.chi * c) * (1 - a)
          - p.k_ext * u_ext * a - p.rho_a * a) / p.tau_a
    dE = dD - dG
    dg = (p.pi * max(0.0, abs(dE) - p.dEdt_ref) - p.mu * (g - p.g0)) / p.tau_g
    dk = dkappa(kap, abs(dE), vp)
    return [da, dG, dD, dS, dg, dk]


def simulate_variant(p: Params, vp: RetuneParams, sch: Schedule, T: float,
                     dt: float = 0.05) -> dict:
    """Segmented RK45 on the six-state variant, same numerics as
    dpdr.integrate.simulate (rtol 1e-6, atol 1e-8, max_step 0.5, restarted
    at every schedule breakpoint).  Returns the frozen Solution dict plus
    'kappa'.  With vp = RetuneParams(kappa_b=1, kmax=1) this reproduces the
    frozen simulate() to integrator tolerance (dkappa = 0 identically).

    Three divergences from dpdr.integrate.simulate, all INERT in exp4's
    runs (documented, not fixed — fixing them means re-implementing more of
    the frozen integrator here):
      1. the frozen five RHS terms are duplicated in deriv_retune rather
         than wrapped (see its docstring) — bit-identical today;
      2. no terminal G < G_floor collapse event: the run continues below
         the frozen integrator's deep-collapse floor (min G in exp4's runs
         is 0.047 >> G_floor = 1e-4, so it never engages);
      3. no LSODA-stiffness fallback: segments always run RK45 (no exp4
         segment triggers the frozen driver's retry criterion).
    Segmentation, the breakpoint-on-grid check, t_eval handling and the
    tolerances are line-identical to integrate.simulate."""
    grid = np.arange(0.0, T + dt / 2, dt)
    bps = [b for b in sch.breakpoints() if 0.0 < b < T]
    for b in bps:
        if abs(b / dt - round(b / dt)) > 1e-9:
            raise ValueError(f"breakpoint {b} not on the dt={dt} grid")
    edges = [0.0] + bps + [T]
    y = np.array([p.a0, p.G0, p.D0, p.S0, p.g_init, vp.kappa0], float)
    ts, ys = [], []
    for t0, t1 in zip(edges[:-1], edges[1:]):
        tev = grid[(grid >= t0 - 1e-9) & (grid < t1 - 1e-9)] if t1 < T \
            else grid[(grid >= t0 - 1e-9) & (grid <= T + 1e-9)]
        sol = solve_ivp(deriv_retune, (t0, t1), y, args=(p, vp, sch),
                        rtol=1e-6, atol=1e-8, max_step=0.5, t_eval=tev)
        ts.append(sol.t)
        ys.append(sol.y)
        y = sol.y[:, -1]
    t = np.concatenate(ts)
    Y = np.concatenate(ys, axis=1)
    a, G, D, S, g, kap = Y
    E = D - G
    c, Theta_eff = cannibalization_vec(E, S, p)
    return dict(t=t, a=a, G=G, D=D, S=S, g=g, kappa=kap, E=E, c=c,
                Theta_eff=Theta_eff, u_loop=G / (D + 1e-9))


def check_gates_variant(vp: RetuneParams, p: Params | None = None,
                        T_base: float = 1000.0, T_fail: float = 600.0,
                        T_resc: float = 1400.0) -> dict:
    """G1-G2c gate checks on the variant, mirroring dpdr.metrics.check_gates
    (same scenarios, horizons and criteria).  Used to verify the variant
    preserves the frozen model's phenomenology; NOT a regression test."""
    from .metrics import EPISODE, RESCUE, stuck_duration
    p = p if p is not None else Params()
    out: dict[str, bool] = {}
    s = simulate_variant(p, vp, baseline_schedule(), T_base)      # G1
    out["G1"] = bool(0.0 < s["G"][-1] < 1.0 and s["E"][-1] < p.Theta
                     and s["c"][-1] < 0.05)
    s = simulate_variant(p, vp, failure_schedule(), T_fail)       # G2, G2b
    w = s["t"] >= EPISODE[1] + 10 * p.tau_G
    out["G2"] = bool(s["G"][-1] < 0.1 and s["E"][-1] > p.Theta
                     and s["c"][-1] > 0.5)
    out["G2b"] = bool(s["G"][w].max() < 0.1 and stuck_duration(s, p)
                      >= 10 * p.tau_G)
    s = simulate_variant(p, vp, rescue_schedule(), T_resc)        # G2c
    w = s["t"] >= RESCUE[1]
    out["G2c"] = bool(s["G"][-1] > 0.5 and s["G"][w].min() > 0.5)
    return out
