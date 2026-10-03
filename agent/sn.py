"""SN MODULE — one rule-based reflex, three explicit scalar lag states.

The a/S/g control loop of the frozen five-state model, transcribed for
per-step (h = tau_a = 1) use by the harness.  arch-open-plan.md §1 is the
spec; the constraints it imposes:

* ONE module, not three.  The three states are one control loop with
  specific internal couplings (a feeds S through (1-a); |dE/dt| feeds g;
  g acts on G's control correction; c captures a).  Fragmenting them into
  sub-modules would re-create the coordination problem the SN exists to
  solve.  ~3 FMAs of arithmetic per step — comfortably under the
  monitoring-cost ceiling's intent (cheap and non-deliberative).

* THREE EXPLICIT SCALAR STATES, each the SAME OBJECT — a first-order lag
  toward a known target (arch-open-plan §0-B):
      a:  da/dt  = (drive*(1-a) - k_ext*u_ext*a - rho_a*a) / tau_a,
           drive = k_in*(a_hold + chi*c);  rate up to ~7.2 / t.u.
           (the all-channels-maxed bound k_in*(1+1)+k_ext+rho_a; the
           dataclass field lam_a_max = 5.7 is the no-load bound
           (k_in+k_ext+rho_a)/tau_a — see SNConstants)
      S:  dS/dt  = (k_s*(1-a) - k_s*S - lam_S*(S - S_rest)) / tau_S
         = ((k_s+lam_S)/tau_S) * (S*(a) - S),   S*(a) = (k_s(1-a)+lam_S*S_rest)/(k_s+lam_S)
           rate (k_s+lam_S)/tau_S = 0.0055 / t.u.
      g:  dg/dt  = (mu/tau_g) * (g*(dEdt) - g), g*(dEdt) = g0 + (pi/mu)*max(0,|dE/dt|-dEdt_ref)
           rate mu/tau_g = 0.0015 / t.u.
  THE 200x TIMESCALE SEPARATION IS THREE WRITTEN-DOWN CONSTANTS (the
  attention rate bound 5.7 / 0.0055 / 0.0015), not a substrate property: the separation holds by
  construction in step counts (one harness step = 1 tau_a unit).

* THE EXACT ZOH UPDATE, NEVER FORWARD EULER.  The attention equation is
  linear in a with input-dependent coefficients; its mode rate reaches
  ~7.2/t.u., so per-step Euler (h = 1) has amplification |1-lambda| ~ 6 and
  DIVERGES (G(300) = NaN, arch-open-plan §0 Run A).  The closed-form
  zero-order-hold recursor
      x <- x + (1 - exp(-lambda*h)) * (x* - x)
  is unconditionally stable at any h and reproduces the segmented
  integrator's ground truth (G(300): ZOH 0.0467 = full-ODE 0.0467).  This
  module supplies the exact forms for a, S, g so the harness can advance
  them at arbitrary sub-step h.  (A quasi-steady substitution a := a* is
  ALSO validated — exact at attractors, ~4 decimals on the failure
  schedule — and is exposed as a flag; the explicit state is kept because
  the actuator acts on the attention path and its transient matters.)

Substrate status: rule-based reflex, nothing trained.  The GRU upgrade is
pre-registered (arch-open-plan T1c) and triggers ONLY if this fails a
fidelity test — see stage1_tests.py part A; no silent switches.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from dpdr.model import Params

__all__ = ["SNConstants", "SNState", "zoh_lag", "S_target", "g_target"]


# --------------------------------------------------------------------------
# The SN's own constants — measured, then written down and never re-derived.
# The floor is a FIXED CLAMP with existence semantics (any value in
# 0.5–1.3 escapes identically; floor_crit 0.4795 ~= the stuck error E*
# 0.4969).  Its value is not tuned because the model says the value does
# not matter above critical — only that it exists (handoff-selfreg-floor,
# -regulator-result).  This is the "any cheap floor" principle.
FLOOR = 0.7  # the value the repo's own experiments used everywhere
# Actuator: attention redirection, NOT gain — ~6x more authority-efficient
# (post-collapse escape needs k_pull >= ~0.5 vs gain k >= 3.0,
# handoff-selfreg-regulator).  Same functional form as the frozen external
# term -k_ext*u_ext*a appended to da/dt.
K_PULL = 1.0        # >= 0.5, the measured requirement
G_TRIG = 0.3        # cheap scalar trigger level on G
TRIG_W = 0.02       # trigger smoothing width (the repo's own regulator value)


@dataclass
class SNConstants:
    """The three lag rates + the measured regulator constants."""
    # written-down lag rates (per t.u.), from Params by default — the
    # 200x separation is these three numbers, not a substrate property
    lam_a_max: float = 5.7     # attention mode-rate bound (k_in+k_ext+rho_a)/tau_a;
                               # the live per-substep lam_a is computed in the
                               # harness (drive+decay)/tau_a; the planner's
                               # all-channels-maxed bound 7.2 is the docstring
                               # worst case, not this expression's value
    lam_S: float = 0.0055      # (k_s + lam_S)/tau_S
    lam_g: float = 0.0015      # mu / tau_g
    # regulator constants (measured; see module docstring)
    floor: float = FLOOR
    k_pull: float = K_PULL
    G_trig: float = G_TRIG
    trig_w: float = TRIG_W
    quasi_steady_a: bool = False  # validated fallback a := a* (arch-open-plan §0-A)

    @classmethod
    def from_params(cls, p: Params, **kw) -> "SNConstants":
        return cls(
            lam_a_max=(p.k_in + p.k_ext + p.rho_a) / p.tau_a,  # 5.7 at Params()
            lam_S=(p.k_s + p.lam_S) / p.tau_S,                  # 0.0055
            lam_g=p.mu / p.tau_g,                               # 0.0015
            **kw,
        )


@dataclass
class SNState:
    """The three explicit scalar states + the per-step monitor record."""
    a: float
    S: float
    g: float
    monitor_cost: float = 0.0   # gated monitoring addend actually paid this step

    def copy(self) -> "SNState":
        return SNState(self.a, self.S, self.g, self.monitor_cost)

    @classmethod
    def initial(cls, p: Params) -> "SNState":
        return cls(a=p.a0, S=p.S0, g=p.g_init)


# --------------------------------------------------------------------------
# Exact ZOH recursors.  Each advances one scalar lag over a hold interval
# of length h during which the INPUTS (target and/or rate) are constant.

def zoh_lag(x: float, target: float, lam: float, h: float) -> float:
    """Exact step of  dx/dt = lam*(target - x)  over h (ZOH inputs):
    x(h) = target + (x - target)*exp(-lam*h)  =  x + (1-e^{-lam h})(target-x).
    Unconditionally stable at ANY h (Gershgorin/monotone: |x(h)-target| is
    non-increasing) — the property forward Euler lacks at lam*h > 2.
    """
    return x + (1.0 - math.exp(-lam * h)) * (target - x)


def attention_rate_and_target(a_hold: float, u_ext: float,
                              c: float, p: Params):
    """The attention equation as (rate, target):
        da/dt = (drive*(1-a) - k_ext*u_ext*a - rho_a*a)/tau_a
              = lam*(a* - a),
        lam = (drive + k_ext*u_ext + rho_a)/tau_a,
        a*   = drive/(drive + k_ext*u_ext + rho_a),
        drive = k_in*(a_hold + chi*c).
    c enters the drive because the model's own coupling (chi*c captures
    attention inward) is part of the loop the SN closes — the SN is the
    loop, not a visitor to it.  (The harness calls this inline per
    substep; exported for tests and telemetry.)
    """
    drive = p.k_in * (a_hold + p.chi * c)
    decay = p.k_ext * u_ext + p.rho_a
    lam = (drive + decay) / p.tau_a
    a_star = drive / (drive + decay) if (drive + decay) > 0.0 else 0.0
    return lam, a_star


def S_target(a: float, p: Params) -> float:
    """S* = (k_s*(1-a) + lam_S*S_rest)/(k_s + lam_S) — the setpoint lags
    toward the context (1-a); rate (k_s+lam_S)/tau_S = 0.0055."""
    return (p.k_s * (1.0 - a) + p.lam_S * p.S_rest) / (p.k_s + p.lam_S)


def g_target(abs_dEdt: float, p: Params) -> float:
    """g* = g0 + (pi/mu)*max(0, |dE/dt| - dEdt_ref); rate mu/tau_g = 0.0015.
    |dE/dt| is passed in (deviation D4 of the frozen model: the filter IS
    tau_g)."""
    return p.g0 + (p.pi / p.mu) * max(0.0, abs_dEdt - p.dEdt_ref)
