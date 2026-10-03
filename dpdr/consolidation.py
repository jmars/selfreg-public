"""CONSOLIDATION variant — a memory term for the frozen five-state model.
Opt-in, frozen model untouched.

WHY THIS MODULE EXISTS (see handoff-selfreg-attn-gate / -poisoned /
-consol-budget / -survivability / -hybrid-store / -protection): the frozen
model has NO memory term (verified — 'memory' does not even appear as a
limitation in paper.md), so two derived phenomena are UNREPRESENTABLE:

  * MULTI-EPISODE CONTAMINATION — repeated collapses progressively
    contaminating the layer that is supposed to survive (the frozen model
    shows collapse as a fixed point with the same G every episode; P4
    measured second-episode threshold 66.0 vs first 66.3 t.u. — FLAT).
  * SELF-TRIGGERING RELAPSE — retrieval of stored self-referential content
    re-supplying the inward-attention fuel (chi*c) with NO new external
    episode (the frozen model needs an external second episode at all).

This module adds the minimal memory term that makes both representable.
Like dpdr/variants.py / permissive.py / regulator.py / window.py it is
OPT-IN: importing dpdr alone never activates any of it, and with the term
disabled the variant IS the frozen model exactly (see FIDELITY below).

ARCHITECTURE (from the survivability / hybrid-store design work):

  TWO GRADES.  A WORKING SET (fast, in-module, expected to scramble) and a
  DURABLE STORE (slow, consolidated, survivors only).  The working set is
  represented by two content-class fills, W_self and W_task; the durable
  store by two class fills, M_self and M_task.  Content classes, not items:
  the frozen model has no item dimension, so the variant tracks the two
  CLASSES the guard story needs — self-referential content (the contaminant,
  the relapse substrate) and task-directed content (the benign class).

  The working set's fills track the model's OWN attention semantics
  (deviation D3 is the precedent for using (1-a) as the outward signal):
      dW_self/dt = (a       - W_self)/tau_W     (inward attention fills the
                                                  self class — inward
                                                  capture is exactly
                                                  "attention on the self")
      dW_task/dt = ((1 - a) - W_task)/tau_W     (outward attention fills
                                                  the task class; under
                                                  capture the task content
                                                  STARVES — this IS the
                                                  "working set scrambles"
                                                  property, and its
                                                  asymmetry with the self
                                                  class is the contamination
                                                  channel: during collapse
                                                  the working set does not
                                                  empty, it FILLS with self)
  tau_W = 5 (convention: the fast grade, between tau_a = 1 and the slow
  machinery tau_G = 20; sensitivity in exp8 part D).

  CONSOLIDATION = A BUDGETED, SELECTIVE WRITE from working set to durable
  store.  FINITE and BINDING (handoff-selfreg-consol-budget: "if the budget
  never binds, nothing is selected"; arXiv 2605.12978: unbounded
  consolidation degrades the store):
      raw_self = v_self * W_self * g_att      (policy-weighted demand)
      raw_task = v_task * W_task * g_att
      scale    = min(1, B/(raw_self+raw_task))          (budget caps TOTAL)
      dM_class/dt = raw_class*scale*(1 - M_class) - mu_M*M_class
  B = 1/tau_cons = 0.005 store-units/t.u. with tau_cons = tau_g = 200
  (both imported/derived, not fitted: "consolidation runs at ~tau_g", and
  the budget lets the survivor layer absorb its full capacity in one
  consolidation timescale of continuous writing).  The (1 - M) factor is
  the bounded capacity fill (each store in [0,1]); mu_M = 0 is the SURVIVOR
  LAYER (nothing erases it — the same persistence semantics as
  permissive.py's mu_N = 0); mu_M > 0 is a washout control.
  NOTE: the identification "consolidation budget = the model's measured
  self-application budget (c_cap*T_max/tau_sim = 0.1122)" is an UNTESTED
  HYPOTHESIS from handoff-selfreg-consol-budget and is NOT claimed here —
  the values differ (0.005 vs 0.1122) and exp8 part D maps the B-axis so
  no conclusion is pegged to B.

THE GUARD — the central design point (handoff-selfreg-attn-gate), and it
is implemented BOTH ways.  The consolidation attention factor g_att is a
PER-CLASS choice (attention-on-content):

      policy    self class            task class
      ----      --------------------  --------------------
      naive     a        (inward —    (1 - a)
                the corrupted
                selector)
      guarded   (1 - a)  (outward)    (1 - a)

  NAIVE is the standard attention-weighted-consolidation reading (Muzzio:
  attention is necessary for consolidation; attention selects the reference
  frame) applied without direction: what gets written is what attention is
  ON, at the attended magnitude.  During collapse a is PINNED at 0.882, so
  the naive policy writes self-referential content to the survivor layer
  exactly when the system is worst — the cannibalization structure
  recursing at the memory layer.

  GUARDED replaces the corrupted variable: the self-class write is weighted
  by OUTWARD/task-directed engagement only (never inward), the form the
  literature and the model's own variable semantics both demand.

  BLOCK RULE (handoff-selfreg-attn-gate design consequence (c)): writes to
  the survivor layer are BLOCKED ENTIRELY (g_att = 0), not merely
  down-weighted, while a > a_block = 0.5 (the a-semantics midpoint: an
  inward-dominant state) — "the selector must not be the corrupted
  variable".  block=True/False is switchable so exp8 measures blocked vs
  merely-down-weighted.

  PRE-REGISTERED EXPECTATION FROM THE BUDGET ALGEBRA (written before any
  run; exp8 part D measures it): under a BINDING shared budget the write
  is decided by the DEMAND SHARE, not the weight magnitude.  At the
  collapse state (a = 0.882, W_self = 0.882, W_task = 0.118) the self
  share is raw_self/(raw_self+raw_task) = 0.982 under naive but still
  0.882 under guarded — the down-weight is largely LAUNDERED by the
  binding budget (guarded-without-block contaminates at ~90% of the naive
  rate).  The BLOCK, not the down-weight, is predicted to be the
  load-bearing guard.

RETRIEVAL — recall is modelled as an inward-attention pulse SOURCED from
the durable store, entering da/dt in EXACTLY the a_hold slot:
      drive(t) = M_self * (A_ret*m_ret(t) + a_hold(t) + k_bg)
      da/dt inward drive += k_in * drive(t) * (1-a)
  The CUE is external, the CONTENT internal.  Three cue sources:
    * m_ret(t) — the 'retrieve' schedule channel (an externally-cued
      recall gate, amplitude [0,1]).  A_ret = 0.9 = the canonical episode
      intensity (IMPORTED from events.inward_episode): a fully-retrieved
      full store reproduces the measured 0.9 recall pulse exactly (the
      validation anchor).
    * a_hold(t) — RIDE-ALONG co-retrieval: an externally-driven inward
      hold IS a self-focus cue, and the stored self-referential loop is
      retrieved along with any externally imposed self-focus, at the same
      retrieval amplitude per unit cue (no new constant — the store's
      cue response is linear in the total external self-focus cue).  This
      is the only channel through which stored contamination can make a
      LATER EPISODE worse (episode k's effective inward intensity is
      a_hold*(1 + M_self)), i.e. it is what makes the multi-episode
      prediction P-A representable at all — the frozen model's P4
      flatness (66.3 vs 66.0 t.u.) is exactly the M_self = 0 locus.
      WITHOUT it the store would be dynamically inert during episodes and
      P-A would be falsified vacuously by a design choice, not by the
      mechanism.
    * k_bg (default 0) — an optional STANDING presence in a_hold units.
      OFF at the design point because a standing pull CONTRADICTS the
      protection measurement this module must validate ("recall must be
      SUSTAINED to hurt; a memory VISITED and LEFT is safe" —
      handoff-selfreg-protection): with k_bg > 0 a full store is never
      inert, and k_bg = 0.05 measurably shifts the dwell limit off its
      anchor (92.2 vs 118.7 t.u., exp8 part V — kept as the quantified
      sensitivity axis, not the design point).
  A store with M_self*A_ret < 0.1122 (M_self < M_INERT = 0.1247 at full
  retrieval amplitude) is STRUCTURALLY INERT under sustained retrieval —
  no dwell length can trigger relapse from it (its sustained retrieval
  drive is sub-chronic-critical vs the model's measured 0.1122, exp7
  part_b a_hold_crit_healthy = 0.11213).  That bound is the guard's
  quantitative success criterion in exp8.

FIDELITY (the prerequisite, verified in exp8 part 0): with cp.enabled =
False, simulate_consol dispatches to dpdr.integrate.simulate — the variant
IS the frozen model, max|dG| = 0 bit-exact.  With the memory states
integrated but every memory flux zero (B = 0, k_bg = 0, A_ret = 0) the RHS
is term-for-term dpdr.model.deriv (the frozen five are WRAPPED — deriv is
called, not duplicated — and the additions are exact zeros), so the
variant's own integrator path reproduces the frozen simulate to integrator
tolerance, with the same two inert divergences as dpdr/permissive.py (no
terminal collapse event, no LSODA fallback; the stuck attractor sits at
G ~ 0.0485 >> G_floor = 1e-4).

PRE-REGISTERED PREDICTIONS AND FALSIFIERS (written before any exp8 run):

  P-A MULTI-EPISODE CONTAMINATION.  With the memory term on and the NAIVE
  policy, the bisected episode-duration collapse threshold T_thr(k)
  declines over k = 1..4 (non-increasing; saturation allowed) relative to
  the same-protocol frozen reference, which P4 measured as FLAT (66.3 vs
  66.0 t.u.).  FALSIFIER: T_thr(k) flat across k (within one bisection
  cell of the frozen reference at every k) — then the contamination
  mechanism does not exist in this realization and P4's flatness stands.

  P-B SELF-TRIGGERING RELAPSE.  After ONE canonical episode (consolidation
  on) + rescue + recovery, retrieval ALONE (the 'retrieve' gate; no
  a_hold/A after the rescue) triggers collapse (G < 0.1) at some bounded
  dwell D in the naive arm.  FALSIFIER: no collapse at any dwell
  <= 700 t.u. in ANY arm — then the self-triggering mechanism is absent
  and the frozen model's external-episode requirement stands.

  GUARD CONTRAST (the headline).  NAIVE contaminates (M_self at the
  episode-2 start > 0.3); GUARDED+BLOCK does not (M_self stays under the
  structural-inertness bound 0.1247).  FALSIFIERS: naive does not
  contaminate, or guarded+block does.

  RETRIEVAL VALIDATION (prerequisite for P-A/P-B).  The retrieval term at
  full store with k_bg = 0 reproduces the frozen a_hold = 0.9 recall pulse
  exactly (max|dG| = 0 to integrator tolerance); the full configuration's
  dwell limit lands within one bisection cell of the independently
  measured 118.7 t.u. (any deviation attributed to the standing pull
  0.05 and quantified); u_ext >= 0.1 makes sustained retrieval safe.
  FAILURE OF ANY OF THESE IS REPORTED AS A FAILURE.

HONEST STATUS, STATED PLAINLY: this is a DETERMINISTIC model; the memory
term is a DESIGN CHOICE (the frozen model has none, so there is no ground
truth to match — every constant above is imported from the frozen model's
own semantics/measurements or documented as a round-number convention);
and the enabled variant is A DIFFERENT SYSTEM whose results are a
FOLLOW-UP, not findings of the frozen model or the paper.

Numerics mirror dpdr/window.simulate_window (segmented RK45, rtol 1e-6,
atol 1e-8, max_step 0.5, restarted at every schedule breakpoint; grid
built as k*dt; no terminal event / LSODA fallback — see FIDELITY above).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

from .integrate import simulate
from .model import Params, Schedule, cannibalization_vec, deriv

__all__ = ["ConsolParams", "deriv_consol", "simulate_consol",
           "store_drive", "consolidation_gate", "A_EPISODE", "T_CHRONIC",
           "M_INERT"]

# IMPORTED anchors (see module docstring):
A_EPISODE = 0.9      # canonical episode intensity (events.inward_episode);
                     # = the retrieval amplitude A_ret
T_CHRONIC = 0.1122   # measured chronic inward-drive critical
                     # (exp7 part_b a_hold_crit_healthy = 0.11213)
M_INERT = T_CHRONIC / A_EPISODE   # 0.1247: a store below this is
                                  # structurally inert under sustained
                                  # full retrieval


@dataclass
class ConsolParams:
    """Constants of the consolidation variant (see module docstring).

    Defaults are the design point: guarded policy WITHOUT the block (the
    down-weight form) — exp8 runs all four policy x block arms plus the
    frozen reference.  enabled=False (or B=0 with k_bg=A_ret=0) is the
    frozen model exactly.
    """
    enabled: bool = True
    policy: str = "guarded"   # 'naive' (raw/inward attention on the self
                              # class) | 'guarded' (outward engagement only)
    block: bool = False       # block rule: writes suppressed ENTIRELY
                              # while a > a_block
    a_block: float = 0.5      # inward-dominant boundary (a-semantics
                              # midpoint)
    # working set (fast grade)
    tau_W: float = 5.0        # fill timescale (convention; the fast grade)
    # consolidation budget (finite, binding)
    B: float = 0.005          # total write-rate cap = 1/tau_cons
    tau_cons: float = 200.0   # = tau_g (imported); B = 1/tau_cons derived
    v_self: float = 1.0       # content-class value weights (NO asymmetry
    v_task: float = 1.0       # asserted — the tested axis is the
                              # attention policy, not class value)
    mu_M: float = 0.0         # durable-store washout (0 = survivor layer)
    # retrieval (the store's inward-attention drive, in a_hold units)
    A_ret: float = 0.9        # retrieval amplitude = A_EPISODE (imported);
                              # fully-retrieved full store = the measured
                              # 0.9 recall pulse
    k_bg: float = 0.0         # optional STANDING presence (a_hold units) —
                              # 0 at the design point: a standing pull
                              # contradicts the protection measurement
                              # (see module docstring)
    # initial memory states
    w0_self: float | None = None   # default p.a0
    w0_task: float | None = None   # default 1 - p.a0
    m0_self: float = 0.0
    m0_task: float = 0.0

    def __post_init__(self):
        if self.policy not in ("naive", "guarded"):
            raise ValueError(f"unknown policy {self.policy!r}")
        if self.k_bg < 0.0 or self.A_ret < 0.0:
            raise ValueError("k_bg and A_ret must be >= 0")


def store_drive(M_self: float, a_hold: float, m_ret: float,
                cp: ConsolParams) -> float:
    """The durable store's inward-attention drive, in a_hold units (it
    enters da/dt in exactly the frozen a_hold slot — that is what makes
    the retrieval validation exact).  The store responds LINEARLY to the
    total external self-focus cue (m_ret gate + ride-along a_hold +
    optional standing presence) at retrieval amplitude A_ret; see the
    module docstring for why each cue source is there."""
    return M_self * (cp.A_ret * m_ret + a_hold + cp.k_bg)


def consolidation_gate(a: float, cp: ConsolParams) -> float:
    """The attention factor g_att on the consolidation write (per-class
    semantics live at the call site; this returns the SELF-class factor —
    the task class is always (1-a), outward attention on task content).

    naive:   a       (raw INWARD attention magnitude — the corrupted
                     selector: during collapse, attention is ON the self)
    guarded: 1 - a   (outward/task-directed engagement only)
    block:   0       (writes suppressed entirely in inward-dominant
                     states, either policy)
    """
    if cp.block and a > cp.a_block:
        return 0.0
    return a if cp.policy == "naive" else (1.0 - a)


def deriv_consol(t, y, p: Params, cp: ConsolParams, sch: Schedule):
    """Nine-state RHS: the frozen five (WRAPPED — dpdr.model.deriv is
    called directly, so the frozen terms are bit-identical, not
    duplicated) plus four memory states [W_self, W_task, M_self, M_task].

    The only frozen term touched is da/dt's inward drive, which gains the
    store's drive k_in*store_drive*(1-a)/tau_a — exactly the a_hold slot.
    dG/dt, dD/dt, dS/dt, dg/dt and the cannibalization switch are
    untouched.  With M_self = 0 (or k_bg = A_ret = 0) the additions are
    exact zeros and this is term-for-term dpdr.model.deriv.
    """
    f5 = deriv(t, y[:5], p, sch)
    a = y[0]
    W_s, W_t, M_s, M_t = y[5], y[6], y[7], y[8]
    a_hold = sch.value("a_hold", t)
    m_ret = sch.value("retrieve", t)
    da = (f5[0] + p.k_in * store_drive(M_s, a_hold, m_ret, cp) * (1.0 - a)
          / p.tau_a)
    dW_s = (a - W_s) / cp.tau_W
    dW_t = ((1.0 - a) - W_t) / cp.tau_W
    g_self = consolidation_gate(a, cp)
    raw_s = cp.v_self * W_s * g_self          # naive: a | guarded: (1-a)
    raw_t = cp.v_task * W_t * (1.0 - a)       # outward attention on task
    tot = raw_s + raw_t
    scale = 0.0 if tot <= 0.0 else min(1.0, cp.B / tot)
    dM_s = raw_s * scale * (1.0 - M_s) - cp.mu_M * M_s
    dM_t = raw_t * scale * (1.0 - M_t) - cp.mu_M * M_t
    return [da, f5[1], f5[2], f5[3], f5[4], dW_s, dW_t, dM_s, dM_t]


def simulate_consol(p: Params, cp: ConsolParams, sch: Schedule, T: float,
                    dt: float = 0.05) -> dict:
    """Segmented RK45 on the nine-state variant; returns the frozen
    Solution dict (dpdr.metrics works unmodified) plus the memory states
    ('W_self','W_task','M_self','M_task') and per-trajectory diagnostics
    ('m_ret','store_drive','g_att','scale','share_self','flux_self',
    'flux_task' — recomputed on the stored samples).

    cp.enabled = False dispatches to dpdr.integrate.simulate: the variant
    IS the frozen model (bit-exact).  The memory-flux-zero wrap check
    (B = 0, k_bg = A_ret = 0, memory states integrated) reproduces the
    frozen simulate to integrator tolerance on this path instead.
    """
    if not cp.enabled:
        return simulate(p, sch, T, dt)
    n = int(round(T / dt))
    grid = np.arange(n + 1) * dt
    T = float(grid[-1])
    bps = [b for b in sch.breakpoints() if 0.0 < b < T]
    for b in bps:
        if abs(b / dt - round(b / dt)) > 1e-9:
            raise ValueError(f"breakpoint {b} not on the dt={dt} grid")
    edges = [0.0] + bps + [T]
    w0s = p.a0 if cp.w0_self is None else cp.w0_self
    w0t = (1.0 - p.a0) if cp.w0_task is None else cp.w0_task
    y = np.array([p.a0, p.G0, p.D0, p.S0, p.g_init,
                  w0s, w0t, cp.m0_self, cp.m0_task], float)
    ts, ys = [], []
    nfev = 0
    for t0, t1 in zip(edges[:-1], edges[1:]):
        tev = grid[(grid >= t0 - 1e-9) & (grid < t1 - 1e-9)] if t1 < T \
            else grid[(grid >= t0 - 1e-9) & (grid <= T + 1e-9)]
        sol = solve_ivp(deriv_consol, (t0, t1), y, args=(p, cp, sch),
                        rtol=1e-6, atol=1e-8, max_step=0.5, t_eval=tev)
        ts.append(sol.t)
        ys.append(sol.y)
        y = sol.y[:, -1]
        nfev += sol.nfev
    t = np.concatenate(ts)
    Y = np.concatenate(ys, axis=1)
    a, G, D, S, g = Y[:5]
    W_s, W_t, M_s, M_t = Y[5], Y[6], Y[7], Y[8]
    E = D - G
    c, Theta_eff = cannibalization_vec(E, S, p)
    # diagnostics recomputed on the stored trajectory (same formulas as the
    # RHS, evaluated at the stored samples)
    m_ret = np.array([sch.value("retrieve", float(tt)) for tt in t])
    a_hold_g = np.array([sch.value("a_hold", float(tt)) for tt in t])
    drive = M_s * (cp.A_ret * m_ret + a_hold_g + cp.k_bg)
    g_att = np.array([consolidation_gate(float(ai), cp) for ai in a])
    raw_s = cp.v_self * W_s * g_att
    raw_t = cp.v_task * W_t * (1.0 - a)
    tot = raw_s + raw_t
    scale = np.where(tot > 0.0, np.minimum(1.0, cp.B / np.maximum(tot, 1e-12)),
                     0.0)
    share_s = np.where(tot > 0.0, raw_s / np.maximum(tot, 1e-12), 0.0)
    flux_s = raw_s * scale * (1.0 - M_s)
    flux_t = raw_t * scale * (1.0 - M_t)
    return dict(t=t, a=a, G=G, D=D, S=S, g=g, E=E, c=c,
                Theta_eff=Theta_eff, u_loop=G / (D + 1e-9),
                collapsed_at=None, nfev=nfev,
                methods=[f"consol({cp.policy}{'+block' if cp.block else ''
                                   },B={cp.B:g})"],
                W_self=W_s, W_task=W_t, M_self=M_s, M_task=M_t,
                m_ret=m_ret, store_drive=drive, g_att=g_att, scale=scale,
                share_self=share_s, flux_self=flux_s, flux_task=flux_t)
