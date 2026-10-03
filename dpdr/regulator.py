"""Self-rescue regulator — opt-in, frozen model untouched.

CONTEXT (the deliverable of the whole simulator; see handoff-selfreg-floor /
-regulator): the frozen model's cannibalization switch tracks the collapsed
state: Theta_eff = Theta*S/S_rest falls as chronic inward attention drags S
down, so the switch stays ON and the positive feedback (c captures attention
a -> a weakens G and drags S -> Theta_eff falls -> c stays on) seals the G2b
stuck attractor.  The measured design principle is that ONE CHEAP CONSTANT
severs that loop: clamping the switch's threshold from below (a FLOOR) keeps
Theta_eff >= E, hence c = 0, hence attention is no longer captured (a -> 0
via rho_a) and G is no longer eaten — G regrows through beta_G.  The floor
does not need to track the real internal state — post-collapse the real
Theta_eff is ~0.13 while a floor at 0.5/0.6/0.7/0.9 all work identically —
so the floor is FALSE as a belief and CHEAP as a mechanism (one constant,
zero observation).  Conversely, self-monitoring is itself inward attention:
a regulator that must continuously watch G pays a monitoring cost c_mon.
SCOPE: the sharp cheap-vs-elaborate monitoring-cost threshold (~0.5 at
k_pull = 2.0) is a property of the POST-COLLAPSE SETTLED assay — engaging
the regulator only after the stuck attractor has consolidated.  In the
deployed configuration (always armed, t_engage = 0) that gated threshold
VANISHES: the trigger gate fires early in the descent (G crosses G_trig at
t ~ 121, before capture consolidates), so the actuator releases attention
before the loop seals and k_pull = 1.0 escapes at every gated c_mon in
[0, 1.5] — see exp6 (d).  What survives in deployment is the UNGATED
(always-on vigilance) cost axis and the floor's structural zero cost.

This module makes that regulator explicit and testable.  It wraps the frozen
five-state RHS (nothing in dpdr/model.py, dpdr/integrate.py, dpdr/metrics.py
or dpdr/events.py is modified; importing dpdr alone never activates any of
this).  Three orthogonal pieces, each individually switchable:

  FLOOR (structural, zero cost): the effective threshold of the
  cannibalization switch is clamped from below,
      Theta_eff_reg = max(Theta*S/S_rest, floor)          (mode 'theta')
  or equivalently the setpoint ENTERING that switch is clamped,
      Theta_eff_reg = Theta*max(S, floor)/S_rest          (mode 'S')
  Both are the same clamp in different units (mode 'S' at value s is mode
  'theta' at value Theta*s/S_rest).  This touches ONLY the switch: dS/dt
  still integrates the true S, so the state is never falsified — only the
  switch's belief is.  floor = None is the frozen model exactly.

  ATTENTION ACTUATOR (event-driven): while armed, a scalar threshold check
  on G (the cheap check — one comparison, no introspection) gates an
  outward attention pull appended to da/dt in the same functional form as
  the frozen external-demand term:
      da/dt += -k_pull * m(G) * a,    m(G) = 1/(1+exp((G - G_trig)/trig_w))
  The sigmoid (trig_w = 0.02, i.e. a threshold to within ~0.04 in G) keeps
  the RHS smooth within integration segments, matching the segmented
  integrator's design.  Measured on the frozen dynamics this actuator needs
  only k_pull >= ~0.5, ~6x less authority than a gain boost (k >= 3.0),
  because it acts on the capture state a directly.

  MONITORING COST (the elaborateness axis): acting on the trigger means
  attending to the internal state, so while the trigger condition holds the
  regulator pays an inward-drive addend:
      da/dt inward drive: k_in * (a_hold + c_mon*m(G) + chi*c) * (1-a)
  GATED by the same trigger gate m(G) (mon_gated=True, default): the scalar
  check itself is free, but ACTING on a positive check is sustained
  introspection, paid for exactly as long as the condition persists.
  In the POST-COLLAPSE SETTLED assay (engage after the stuck state has
  consolidated) this makes the cheap/elaborate contrast SHARP: at
  k_pull = 2.0, rescue succeeds for c_mon <= 0.5 and fails for
  c_mon >= 0.7.  That threshold is an assay property, NOT a deployment
  fact: ALWAYS ARMED (t_engage = 0) the gate fires during the descent
  itself and a gated cost of any size up to 1.5 cannot kill the rescue —
  exp6 (d) measures both.  The UNGATED variant (mon_gated=False — vigilance
  paid always, while merely armed) degrades G smoothly with no threshold in
  EITHER geometry (defeated at c_mon ~ 0.2 even with the floor held; exp6
  (d)), matching the knowing-floor result kc ~ 0.2.
  THE FLOOR PAYS NOTHING: it needs no observation of G at all, so its cost
  is structurally zero and cannot become expensive.  Note the floor only
  severs the cannibalization loop; it does not touch the direct allostatic
  weakening term -alpha_G*a*G, so a large c_mon still degrades G even with
  the floor engaged (measured in exp6).

Armed window: everything (floor, actuator, monitoring cost) activates at
t >= t_engage, which becomes an integration breakpoint — before that the
RHS is term-for-term the frozen one, so the post-collapse self-rescue assay
(engage after the stuck attractor has settled) is well posed.  With floor
off, k_pull = 0 and c_mon = 0 the RHS is the frozen RHS exactly; the
integrator below then reproduces dpdr.integrate.simulate to integrator
tolerance (verified in experiments/exp6_regulator.py part 0), with the same
two inert divergences as dpdr/permissive.py: no terminal collapse event and
no LSODA fallback (neither fires on these scenarios; the stuck attractor
sits at G ~ 0.05 >> G_floor = 1e-4).

CAVEATS (in-model only; restated with the exp6 results): deterministic
model, so all thresholds are loci not distributions; the "false belief" is
a clamped constant, not a belief system; the monitoring cost is a scalar
addend standing in for whatever real introspection costs; the success
criterion throughout is FUNCTIONAL (does the agent stay functional), not
phenomenological match.

Numerics mirror dpdr/permissive.simulate_perm (segmented RK45, rtol 1e-6,
atol 1e-8, max_step 0.5, restarted at every schedule breakpoint plus
t_engage; grid built as k*dt — arange's accumulated endpoint can land
~1e-13 above T and solve_ivp's t_eval check is strict).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from .model import Params, Schedule

__all__ = ["RegulatorParams", "deriv_reg", "simulate_reg", "floor_theta_eff"]


@dataclass
class RegulatorParams:
    """Constants of the self-rescue regulator (see module docstring)."""
    # cheap fixed floor on the cannibalization switch (None = off)
    floor: float | None = 0.7      # clamp value
    floor_mode: str = "theta"      # 'theta' (on Theta_eff) | 'S' (on S)
    # attention-redirection actuator (k_pull = 0 = off)
    k_pull: float = 0.0            # authority of the outward pull
    G_trig: float = 0.3            # cheap scalar trigger level on G
    trig_w: float = 0.02           # trigger smoothing width (in G units)
    # self-monitoring cost: inward-drive addend paid while armed.  The cost
    # is GATED by the trigger (mon_gated=True, the measured design point):
    # the scalar check on G is free, but ACTING on a positive check means
    # sustained attention to the internal state, so the addend is paid only
    # while the trigger condition holds.  In the post-collapse settled assay
    # this makes the cheap/elaborate contrast SHARP (rescue below
    # c_mon ~ 0.5, failure above, at k_pull = 2.0); ALWAYS ARMED
    # (t_engage = 0) that gated threshold vanishes — the gate fires during
    # the descent before capture consolidates.  An UNGATED constant cost
    # (mon_gated=False, vigilance paid always) degrades G smoothly with no
    # threshold in either geometry — see exp6 (d).
    c_mon: float = 0.0
    mon_gated: bool = True
    # engagement time (everything activates at t >= t_engage)
    t_engage: float = 0.0


def floor_theta_eff(S: float, p: Params, r: RegulatorParams) -> float:
    """Effective (regulated) threshold of the cannibalization switch."""
    if r.floor is None:
        return p.Theta * S / p.S_rest
    if r.floor_mode == "theta":
        return max(p.Theta * S / p.S_rest, r.floor)
    if r.floor_mode == "S":
        return p.Theta * max(S, r.floor) / p.S_rest
    raise ValueError(f"unknown floor_mode {r.floor_mode!r}")


def deriv_reg(t, y, p: Params, r: RegulatorParams, sch: Schedule):
    """Five-state RHS: the frozen equations with the regulator's three
    pieces wrapped in.  The frozen RHS is wrapped, not duplicated: with
    floor off, k_pull = 0, c_mon = 0 this is term-for-term dpdr.model.deriv.

    Only three frozen terms can be touched: the cannibalization switch c
    (the floor), the inward drive of da/dt (the monitoring cost), and the
    outward drive of da/dt (the actuator).  dG/dt's other four terms, dD/dt,
    dS/dt (the TRUE setpoint still integrates), dE/dt and dg/dt are
    untouched.
    """
    a, G, D, S, g = y
    E = D - G
    armed = 1.0 if t >= r.t_engage else 0.0
    Teff_reg = floor_theta_eff(S, p, r) if armed else p.Theta * S / p.S_rest
    c = min(p.sigma_c * max(0.0, math.tanh((E - Teff_reg) / p.w)), 1.0)
    a_hold = sch.value("a_hold", t)
    A = sch.value("A", t)
    u_ext = sch.value("u_ext", t)
    m = armed / (1.0 + math.exp((G - r.G_trig) / r.trig_w))
    c_mon = armed * r.c_mon * (m if r.mon_gated else 1.0)
    dG = (p.beta_G * (1 - a) * G * (1 - G)
          - p.alpha_G * a * G
          - p.eta * c * G
          - p.gam_G * G
          + g * math.tanh(E / p.Es) * (G + p.eps0) * (1 - G)) / p.tau_G
    dD = ((p.D_base + A) * p.beta_D * (1 - D) - p.delta_D * D) / p.tau_D
    dS = (p.k_s * ((1 - a) - S) - p.lam_S * (S - p.S_rest)) / p.tau_S
    da = (p.k_in * (a_hold + c_mon + p.chi * c) * (1 - a)
          - p.k_ext * u_ext * a - r.k_pull * m * a - p.rho_a * a) / p.tau_a
    dE = dD - dG
    dg = (p.pi * max(0.0, abs(dE) - p.dEdt_ref) - p.mu * (g - p.g0)) / p.tau_g
    return [da, dG, dD, dS, dg]


def simulate_reg(p: Params, r: RegulatorParams, sch: Schedule, T: float,
                 dt: float = 0.05) -> dict:
    """Segmented RK45 on the regulated five-state system; returns the frozen
    Solution dict (so dpdr.metrics' classify/is_stuck/summarize work
    unmodified — 'c' and 'Theta_eff' report the values actually used by the
    switch) plus 'Theta_eff_frozen' (the unregulated threshold), 'mon' (the
    trigger gate m(t)) and 'floor_active' (the clamp's engagement)."""
    n = int(round(T / dt))
    grid = np.arange(n + 1) * dt
    T = float(grid[-1])
    # de-duplicate: t_engage landing on a schedule breakpoint would create a
    # zero-length segment (empty t_eval -> sol.y a list, not an array)
    bps = sorted(set([b for b in sch.breakpoints() if 0.0 < b < T]
                     + ([r.t_engage] if 0.0 < r.t_engage < T else [])))
    for b in bps:
        if abs(b / dt - round(b / dt)) > 1e-9:
            raise ValueError(f"breakpoint {b} not on the dt={dt} grid")
    edges = [0.0] + bps + [T]
    y = np.array([p.a0, p.G0, p.D0, p.S0, p.g_init], float)
    ts, ys = [], []
    nfev = 0
    for t0, t1 in zip(edges[:-1], edges[1:]):
        tev = grid[(grid >= t0 - 1e-9) & (grid < t1 - 1e-9)] if t1 < T \
            else grid[(grid >= t0 - 1e-9) & (grid <= T + 1e-9)]
        sol = solve_ivp(deriv_reg, (t0, t1), y, args=(p, r, sch),
                        rtol=1e-6, atol=1e-8, max_step=0.5, t_eval=tev)
        ts.append(sol.t)
        ys.append(sol.y)
        y = sol.y[:, -1]
        nfev += sol.nfev
    t = np.concatenate(ts)
    Y = np.concatenate(ys, axis=1)
    a, G, D, S, g = Y
    E = D - G
    Teff_frozen = p.Theta * S / p.S_rest
    if r.floor is None:
        Teff_reg = Teff_frozen
    elif r.floor_mode == "theta":
        Teff_reg = np.maximum(Teff_frozen, r.floor)
    else:
        Teff_reg = p.Theta * np.maximum(S, r.floor) / p.S_rest
    armed = (t >= r.t_engage).astype(float)
    Teff_reg = np.where(armed > 0, Teff_reg, Teff_frozen)
    c = np.minimum(p.sigma_c * np.maximum(0.0, np.tanh((E - Teff_reg) / p.w)),
                   1.0)
    mon = armed / (1.0 + np.exp((G - r.G_trig) / r.trig_w))
    c_mon_t = armed * r.c_mon * (mon if r.mon_gated else 1.0)
    return dict(t=t, a=a, G=G, D=D, S=S, g=g, E=E, c=c,
                Theta_eff=Teff_reg, Theta_eff_frozen=Teff_frozen, mon=mon,
                c_mon=c_mon_t, u_loop=G / (D + 1e-9), collapsed_at=None,
                nfev=nfev, methods=[f"reg(t_engage={r.t_engage:g})"])
