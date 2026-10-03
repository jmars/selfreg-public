"""P2 variant: the opt-in D-reads-G coupling (arch-open-plan §2, item 9).

NOTHING in this module modifies the frozen model (dpdr/model.py,
dpdr/integrate.py: READ-ONLY — the fidelity gates depend on it).  The variant
adds ONE state to the frozen five (a, G, D, S, g): the real-backlog EMA B,
exactly as implemented in the Stage-1 harness (~/thing/agent/harness.py, the
planner's specification, ZERO free constants):

    backlog B:   dB/dt = (c - B) / tau_D        (tau_D REUSED; rate 1)
    A_eff     =  A + B                          (B(0) = 0)
    dD/dt     =  ((D_base + A_eff)*beta_D*(1 - D) - delta_D*D) / tau_D

the switch state c IS the unchecked-self-content arrival rate (cannibalisation
= self-referential content generated faster than it is checked; c = 0 exactly
when nothing unchecked is accruing), and D reads the STATE B — never itself:
no D -> E -> D loop (that was the re-design the Stage-1 review forced; the
earlier A_eff = A + max(0, E) form moved the border-collision fold eps_c
0.26519 -> 0.2007 and is NOT reproduced here).

Edge is gated by its own switch: B(0) = 0 and dB/dt = 0 wherever c = 0, so B
is EXACTLY zero on any trajectory segment where the switch has never armed —
the healthy regime AND every run whose c never leaves 0.  CONSEQUENCE (stated
before any run, exp21 prereg): with the edge ON, trajectories are bit-identical
to the OFF control up to the first arming moment, and cells whose switch never
arms cannot differ at all.  The coupling can only move the collapse/ceiling
picture through cells that ARM.

DRIVE-SIDE CONVENTION (stated, not hidden).  In the realized edge the arrival
rate is c(D-G, S), which DECREASES with G at fixed D (d(c)/d(G) <= 0 through
its explicit argument): the backlog measures the generator's DEFICIT against
outstanding demand, not its output.  The C24 reading "more G feeds back into
more D" (population feeding capability) is therefore an IDENTIFICATION at the
INTERPRETATION level, not a property of this RHS; the model has no replication
term, so what this variant probes is the DRIVE-PRECURSOR (the coupling whose
enabling C24 predicts makes the drive visible), not replication itself.  To
make the falsifiable attempt decisive, a second arm is provided:
mode="prod", B = EMA_tauD(G) — the production-side drive (arrival rate
proxied by the generator state itself), also ZERO free constants (tau_D
reused, coefficient 1, same EMA form).  It is labelled EXPLORATORY: it is a
drive-side convention choice, not a measured specification.

MODES
  "off"   — no coupling: simulate_p2 DELEGATES to dpdr.integrate.simulate
            (bit-exact control path; B reported as zeros).
  "spec"  — the realized harness/spec edge, B = EMA_tauD(c).  DEFAULT.
  "prod"  — EXPLORATORY production-side arm, B = EMA_tauD(G).

With mode="off" (or B pinned at 0) the six-state RHS is term-for-term the
frozen one; exp21 checks max|deriv_p2(B=0) - model.deriv| = 0 over random
states.  As in dpdr/variants.py, the frozen five terms are REBUILT here (not
rescaled post hoc), so a future edit to model.py silently desyncs this copy —
the exp21 fidelity part re-verifies the equality.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from .integrate import DT, simulate
from .model import Params, Schedule, cannibalization, cannibalization_vec

__all__ = ["P2Params", "deriv_p2", "simulate_p2"]


@dataclass
class P2Params:
    """Constants of the coupling.  There are NONE to tune: the EMA rate is
    1/tau_D with the frozen tau_D, the addend coefficient is 1, B(0) = 0.
    mode selects the arrival-rate convention (see module docstring);
    B0 exists only for the wiring-falsifier probe (the harness's own
    convention is B(0) = 0 and exp21 uses B0 = 0 everywhere)."""
    mode: str = "spec"     # "off" | "spec" | "prod"
    B0: float = 0.0


def _arrival(p: Params, vp: P2Params, c: float, G: float) -> float:
    """The arrival rate feeding the backlog EMA, per mode."""
    if vp.mode == "prod":
        return G          # EXPLORATORY: production-side drive
    return c              # the spec edge (harness.py): switch state


def deriv_p2(t, y, p: Params, vp: P2Params, sch: Schedule):
    """Six-state RHS; y = [a, G, D, S, g, B].  With B = 0 (and the arrival
    rate not feeding back before it decays) the first five returned entries
    are the frozen model.deriv values bit-for-bit — verified in exp21."""
    a, G, D, S, g, B = y
    E = D - G
    c, _te = cannibalization(E, S, p)
    a_hold = sch.value("a_hold", t)
    A = sch.value("A", t)
    u_ext = sch.value("u_ext", t)
    A_eff = A + B
    dG = (p.beta_G * (1 - a) * G * (1 - G)
          - p.alpha_G * a * G
          - p.eta * c * G
          - p.gam_G * G
          + g * math.tanh(E / p.Es) * (G + p.eps0) * (1 - G)) / p.tau_G
    dD = ((p.D_base + A_eff) * p.beta_D * (1 - D) - p.delta_D * D) / p.tau_D
    dS = (p.k_s * ((1 - a) - S) - p.lam_S * (S - p.S_rest)) / p.tau_S
    da = (p.k_in * (a_hold + p.chi * c) * (1 - a)
          - p.k_ext * u_ext * a - p.rho_a * a) / p.tau_a
    dE = dD - dG                       # frozen deviation D4
    dg = (p.pi * max(0.0, abs(dE) - p.dEdt_ref) - p.mu * (g - p.g0)) / p.tau_g
    dB = (_arrival(p, vp, c, G) - B) / p.tau_D
    return [da, dG, dD, dS, dg, dB]


def _collapse_event(t, y, p, vp, sch):   # solve_ivp forwards ALL args to events
    return y[1] - p.G_floor


_collapse_event.terminal = True
_collapse_event.direction = -1.0


def simulate_p2(p: Params, vp: P2Params, sch: Schedule, T: float,
                dt: float = DT) -> dict:
    """Segmented driver on the six-state system, numerics IDENTICAL to
    dpdr.integrate.simulate (RK45 rtol 1e-6 atol 1e-8 max_step 0.5, restart
    at every schedule breakpoint, LSODA retry on status -1 or nfev above
    max(5000, 60*segment length), terminal event at G < G_floor with the
    trajectory held flat afterwards).  mode="off" DELEGATES to the frozen
    driver and reports B as zeros — the control path is the frozen code
    itself, bit-exact by construction.  Returns the frozen Solution dict
    plus 'B' (and 'A_eff' = A + B for convenience)."""
    if vp.mode == "off":
        sol = dict(simulate(p, sch, T, dt))
        sol["B"] = np.zeros_like(sol["t"])
        A = np.array([sch.value("A", float(t)) for t in sol["t"]])
        sol["A_eff"] = A
        return sol
    grid = np.arange(0.0, T + dt / 2, dt)
    bps = [b for b in sch.breakpoints() if 0.0 < b < T]
    for b in bps:
        if abs(b / dt - round(b / dt)) > 1e-9:
            raise ValueError(f"breakpoint {b} not on the dt={dt} grid")
    edges = [0.0] + bps + [T]
    y = np.array([p.a0, p.G0, p.D0, p.S0, p.g_init, vp.B0], float)
    ts, ys, methods = [], [], []
    nfev_total = 0
    collapsed_at = None
    for t0, t1 in zip(edges[:-1], edges[1:]):
        tev = grid[(grid >= t0 - 1e-9) & (grid < t1 - 1e-9)] if t1 < T \
            else grid[(grid >= t0 - 1e-9) & (grid <= T + 1e-9)]
        kw = dict(args=(p, vp, sch), rtol=1e-6, atol=1e-8, max_step=0.5,
                  t_eval=tev, events=_collapse_event)
        sol = solve_ivp(deriv_p2, (t0, t1), y, method="RK45", **kw)
        method = "RK45"
        if sol.status == -1 or sol.nfev > max(5000.0, 60.0 * (t1 - t0)):
            sol = solve_ivp(deriv_p2, (t0, t1), y, method="LSODA", **kw)
            method = "LSODA"
        methods.append(f"[{t0:g},{t1:g}]:{method}({sol.nfev})")
        nfev_total += sol.nfev
        ts.append(sol.t)
        ys.append(sol.y)
        y = sol.y[:, -1]
        if sol.status == 1:            # terminal collapse event fired
            collapsed_at = float(sol.t_events[0][0])
            rest = grid[grid > sol.t[-1] + 1e-9]
            if rest.size:
                ts.append(rest)
                ys.append(np.repeat(y[:, None], rest.size, axis=1))
            break
    t = np.concatenate(ts)
    Y = np.concatenate(ys, axis=1)
    a, G, D, S, g, B = Y
    E = D - G
    c, Theta_eff = cannibalization_vec(E, S, p)
    A = np.array([sch.value("A", float(tv)) for tv in t])
    return dict(t=t, a=a, G=G, D=D, S=S, g=g, B=B, E=E, c=c,
                Theta_eff=Theta_eff, u_loop=G / (D + 1e-9), A_eff=A + B,
                collapsed_at=collapsed_at, methods=methods,
                nfev=nfev_total)
