"""STAGE-1 HARNESS — the control loop around the frozen five-state model.

This is the SN ANALOGUE's deployment surface: a per-step (h = 1 t.u. = one
DMN turn / tool call) loop around the frozen plant, built from NEW files
only (~/thing/agent/), importing dpdr read-only.  Per step:

  1. SENSE (cheap, scalar): the SN's collapse sensor reads the D-side
     backlog, the SURVIVING subsystem — never G's self-assessment.  The
     D/G dissociation (reasoning intact at 0.5455 while G collapses
     0.8855 -> 0.0485) means a sensor in G is destroyed by the failure it
     must detect.
  2. MONITOR (gated, cheap): the CLIPPED SIGMOID on the trigger — the
     frozen form m = 1/(1+exp((G-G_trig)/trig_w)) (regulator.py, trig_w =
     0.02) with its tail set to EXACT ZERO outside G_trig + 10*trig_w
     (the clipped value there is ~1.4e-11, below numerical relevance) —
     measured bit-identical to the full sigmoid on every structural
     boundary AND exactly zero in the healthy regime, so the max|dG| =
     0.00e+00 contract holds with the model's own functional form.  The
     cheap design pays c_mon = 0 (the floor is structurally free).
  3. ACTUATE: the attention-redirection actuator (outward pull
     -k_pull*m*a appended to the attention decay — same functional form
     as the frozen external term; ~6x more authority-efficient than a
     gain boost).  BLOCK, never down-weight: the write-path rule — during
     high inward attention the consolidation write channel is BLOCKED
     (weight 0), because a binding budget LAUNDERS a partial weight
     (measured: down-weighting achieves only ~3%, 0.7532 vs 0.7784).
     The block is REAL (Stage 1.5): it gates the selective write into
     the harness's own durable store (dpdr.consolidation imported
     read-only; see _consolidate); the block arms during collapse
     (measured M_self at the episode-2 start 0.0481 << M_INERT 0.1247).
     It deliberately does NOT gate the currency edge, which must keep
     reading the backlog during collapse — that reading is the loop
     closing.
  4. UPDATE (exact ZOH): the three SN states advance by the closed-form
     lag recursor; G advances by RK4 sub-steps with a(tau) and D(tau)
     analytic inside each sub-step (D's recursor is exact: linear ODE).

THE D-READS-G EDGE (arch-open-plan §2 — the loop closer), RE-DESIGNED
per the Stage-1 review.  The review's measured root cause: the original
form A_eff = A + max(0,E) drove the demand accumulator from E = D - G —
D's OWN INPUT — creating a D -> E -> D self-loop neither the frozen
model nor the planner's design has; measured consequence: the
border-collision fold moved eps_c 0.26519 -> 0.2007 (-24%) and the chi
regimes changed.  (A softplus(20) edge gave the IDENTICAL eps_c: the
kink was never the problem — the edge's EXISTENCE was.)  THE PLANNER'S
SPEC (§2): the CEN's VERDICT/BACKLOG drives the demand accumulator as a
SEPARATE STATE — "the normalized EMA of the unchecked-assertion
backlog ... smoothed at tau_D", zero free constants.  The harness now
instantiates exactly that, with a drive signal EXOGENOUS to D's
equation:

    backlog B:  dB/dt = (c - B)/tau_D        (the switch state c IS the
                                              unchecked-self-content
                                              arrival rate: cannibalis-
                                              ation = self-referential
                                              content generated faster
                                              than it is checked; c = 0
                                              exactly when nothing
                                              unchecked is accruing)
    A_eff = A + B,  B(0) = 0.

ZERO FREE CONSTANTS: one new state, tau_D reused, coefficient 1.  D's
equation reads the STATE B — never itself: no D -> E -> D loop.  And B
is EXACTLY ZERO wherever c = 0, which by the switch's own construction
(E < Theta_eff => c = 0) is the ENTIRE healthy regime INCLUDING the
marginal branch at the chronic fold (the healthy equilibrium dies ON
the manifold E = Theta_eff, handoff-selfreg-border-collision): there
the new edge is BIT-INERT and the frozen fold location is expected to
be preserved by construction (measured: see stage1_fix_tests.py part
X1).  The edge is live only in genuine collapse (c > 0), where the
backlog genuinely accrues — CEN-down semantics ("D rises during the
outage, which is correct", arch-open-plan L135).  THE CEN STILL DOES
NOT ACT: this edge is a wiring, not an actuator; actuator authority
stays with the SN (the attention pull and the write-block).  WITH THE
EDGE ON THE AGENT IS GENUINELY A DIFFERENT SYSTEM from the frozen ODE —
its D responds endogenously to what G produces; the frozen model's
kick-invariance (unchanged D under a G kick) becomes the WIRING
FALSIFIER (stage1_tests.py part C: degrade G -> D must move).

WITH THE REGULATOR DISABLED AND THE EDGE ZERO the RHS is term-for-term
the frozen RHS and the sub-step integrator reproduces
dpdr.integrate.simulate to INTEGRATOR TOLERANCE (<= 1e-3 on G over the
standard scenarios) — stated as tolerance, NOT bit-exact, because
solve_ivp's adaptive stepping differs from fixed RK4 sub-steps; verified
in stage1_tests.py part A.  (The exact ZOH recursor itself reproduces the
segmented integrator's ground truth on the planner's check schedule:
G(300) ZOH = G(300) full-ODE = 0.0467.)

NOT AN AGENT (stated plainly): a control loop around a deterministic
model.  No DMN substrate, no LLM, no values, no goals.  The model->agent
mapping is ORDINAL and unvalidated; four of five prior mappings failed.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from dpdr.consolidation import (ConsolParams, M_INERT, consolidation_gate,
                                store_drive)
from dpdr.model import Params, Schedule

from sn import SNConstants, SNState, S_target, g_target, zoh_lag

__all__ = ["AgentConfig", "StepLog", "Trajectory", "Agent", "run_agent"]

H_STEP = 1.0          # one harness step = 1 tau_a unit (the DMN-turn mapping)
SUBSTEPS = 40         # RK4 sub-steps per harness step for G (h_i = 0.025)


@dataclass
class AgentConfig:
    """Switches + constants.  DEFAULT = regulator ON, edge ON, store ON."""
    regulator_on: bool = True    # floor + actuator + gated monitor
    edge_on: bool = True         # the G->D currency edge (A_eff = A + B)
    sn: SNConstants = field(
        default_factory=lambda: SNConstants.from_params(Params()))
    # monitoring-cost ceiling honoured by construction: the gated addend is
    # c_mon*m, paid only while the trigger holds; the cheap design pays 0
    c_mon: float = 0.0
    # armed window: everything (floor, actuator, monitor) activates at
    # t >= t_engage (the review's settled assay engages at 600; 0.0 =
    # deployed)
    t_engage: float = 0.0
    # write-path BLOCK threshold: consolidation writes are blocked — not
    # down-weighted — while inward attention is high (the selection signal
    # is corrupted exactly then); the block gates the REAL write into the
    # harness's own durable store (see _consolidate).  block_on=False is
    # the measured ABLATION arm (down-weight/block contrast)
    block_a_thresh: float = 0.5
    block_on: bool = True
    # the durable store (Stage 1.5 wiring): dpdr.consolidation imported
    # READ-ONLY; None disables the store entirely (pure telemetry block)
    consol: ConsolParams | None = field(default_factory=ConsolParams)
    n_substeps: int = SUBSTEPS


@dataclass
class StepLog:
    t: float
    a: float
    G: float
    D: float
    S: float
    g: float
    E: float
    c: float
    m: float               # trigger gate (clipped sigmoid)
    A_eff: float           # demand drive actually used (incl. the edge)
    edge_addend: float     # the backlog B contributed by the G->D edge
    monitor_cost: float    # gated addend paid this step (0 in the cheap design)
    acted: bool
    write_block: bool      # consolidation writes BLOCKED this step (real gate)
    floor_active: bool
    B: float = 0.0         # the backlog state (0 iff the edge is inert)
    W_self: float = 0.0    # working-set fills (harness's own store)
    W_task: float = 0.0
    M_self: float = 0.0    # durable-store fills (harness's own store)
    M_task: float = 0.0
    store_on: bool = False
    kicked: bool = False   # a G-kick was applied this step (tests only)


class Trajectory:
    """Lightweight record of a run (lists -> arrays on demand)."""
    def __init__(self):
        self.log: list[StepLog] = []

    def add(self, s: StepLog):
        self.log.append(s)

    def arrays(self) -> dict:
        keys = ("t", "a", "G", "D", "S", "g", "E", "c", "m", "A_eff",
                "edge_addend", "monitor_cost", "B", "W_self", "W_task",
                "M_self", "M_task")
        out = {k: np.array([getattr(r, k) for r in self.log]) for k in keys}
        out["acted"] = np.array([r.acted for r in self.log])
        out["write_block"] = np.array([r.write_block for r in self.log])
        out["floor_active"] = np.array([r.floor_active for r in self.log])
        out["store_on"] = np.array([r.store_on for r in self.log])
        return out


# --------------------------------------------------------------------------
def switch_c(E: float, S: float, p: Params, floor: float | None) -> tuple:
    """The cannibalization switch with the floor clamp:
    Theta_eff = max(Theta*S/S_rest, floor) — touches ONLY the switch's
    belief; dS/dt still integrates the true S (state never falsified).
    The floor is a WRITTEN-DOWN CONSTANT: existence is what matters (any
    value in 0.5-1.3 escapes identically; floor_crit 0.4795 ~= stuck E*
    0.4969), and it is NEVER re-checked — a floor held with a
    discrepancy-monitoring cost kc fails at kc ~ 0.2 (knowingfloor).
    Returns (c, floor_active)."""
    Teff = p.Theta * S / p.S_rest
    active = False
    if floor is not None and Teff < floor:
        Teff = floor
        active = True
    return min(p.sigma_c * max(0.0, math.tanh((E - Teff) / p.w)), 1.0), active


def D_recursor_params(A_eff: float, p: Params) -> tuple:
    """D's linear recursor as (rate, target) — the frozen equation
    dD/dt = ((D_base + A_eff)*beta_D*(1-D) - delta_D*D)/tau_D
          = lam*(D* - D),  lam = ((D_base+A_eff)*beta_D + delta_D)/tau_D,
            D* = (D_base+A_eff)*beta_D / ((D_base+A_eff)*beta_D + delta_D).
    A_eff is whatever demand drive the schedule + edge supply."""
    r = (p.D_base + A_eff) * p.beta_D
    lam = (r + p.delta_D) / p.tau_D
    return lam, r / (r + p.delta_D)


class Agent:
    """The Stage-1 control loop.  One harness step = one call to step()."""

    def __init__(self, p: Params | None = None, cfg: AgentConfig | None = None):
        self.p = p if p is not None else Params()
        self.cfg = cfg if cfg is not None else AgentConfig()
        self.sn = SNState.initial(self.p)
        self.G = self.p.G0   # plant state (a, S, g live in the SN state)
        self.D = self.p.D0
        self.B = 0.0         # the backlog state (the edge's drive; B(0)=0)
        self.t = 0.0
        self.traj = Trajectory()
        # the harness's OWN store (never dpdr's): working-set + durable
        # fills advanced by the consolidation step below.  m0 defaults 0.
        self.W_self = self.cfg.consol.w0_self if (
            self.cfg.consol is not None
            and self.cfg.consol.w0_self is not None) else self.p.a0
        self.W_task = self.cfg.consol.w0_task if (
            self.cfg.consol is not None
            and self.cfg.consol.w0_task is not None) else (1.0 - self.p.a0)
        self.M_self = self.cfg.consol.m0_self if self.cfg.consol else 0.0
        self.M_task = self.cfg.consol.m0_task if self.cfg.consol else 0.0

    # ------------------------------------------------------------------
    def _edge(self, t: float, sch: Schedule) -> tuple:
        """(A_eff, edge_addend).  The edge is a pure READING of the
        backlog STATE B (the planner's verdict/backlog EMA, re-designed
        per the Stage-1 review): it is not blocked by the write-path
        rule — blocking it during collapse would sever the loop the edge
        exists to close."""
        A = sch.value("A", t)
        addend = self.B if self.cfg.edge_on else 0.0
        return A + addend, addend

    def _trigger(self) -> float:
        """The cheap scalar check on G: the FROZEN SIGMOID form
        (regulator.py: m = 1/(1+exp((G-G_trig)/trig_w)), trig_w = 0.02)
        with its tail set to EXACT ZERO outside G_trig + 10*trig_w — the
        review's clipped sigmoid, measured bit-identical to the full
        sigmoid on every structural boundary AND exactly zero in the
        healthy regime (healthy G ~ [0.70, 0.886] sits far above the
        clip point G_trig+10*trig_w = 0.5), so the max|dG| = 0.00e+00
        contract holds with the model's own functional form."""
        s = self.cfg.sn
        if self.G >= s.G_trig + 10.0 * s.trig_w:
            return 0.0
        return 1.0 / (1.0 + math.exp((self.G - s.G_trig) / s.trig_w))

    # ------------------------------------------------------------------
    def step(self, sch: Schedule, kick: float = 0.0) -> StepLog:
        """Advance one harness step (h = 1 t.u.).  `kick` is an optional
        exogenous G impulse (the wiring-falsifier probe; applied at the
        START of the step so its effect propagates through E).  Inputs are
        read at the step's start time (left-closed schedule intervals —
        the same ZOH convention as the segmented integrator)."""
        p = self.p
        s = self.cfg.sn
        cfg = self.cfg
        hsub = H_STEP / cfg.n_substeps

        kicked = kick != 0.0
        if kicked:
            self.G = min(max(self.G + kick, 0.0), 1.0)

        a_hold = sch.value("a_hold", self.t)
        u_ext = sch.value("u_ext", self.t)
        A_eff, edge_addend = self._edge(self.t, sch)
        E0 = self.D - self.G
        # armed window (exp6's settled assay engages at t=600; deployed = 0)
        armed = cfg.regulator_on and self.t >= cfg.t_engage
        floor = s.floor if armed else None
        c0, floor_active = switch_c(E0, self.sn.S, p, floor)
        # the trigger SENSOR is always computed (the SN is always alive; the
        # write-block below reads it); the actuator/monitor need `armed`
        m = self._trigger()
        mon_cost = cfg.c_mon * m if armed else 0.0

        # |dE/dt| input for g* (frozen deviation D4: instantaneous, tau_g
        # is the filter) — evaluated once per step with A_eff included
        dE0 = self._dEdt(A_eff, floor)

        # ---- coupled advance: a, D analytic; G RK4; S, g exact lags ------
        a_s, S_s, g_s = self.sn.a, self.sn.S, self.sn.g
        G_cur, D_cur = self.G, self.D
        B_s = self.B
        lam_B = 1.0 / p.tau_D        # the backlog EMA's rate (tau_D reused)
        lam_D, D_star = D_recursor_params(A_eff, p)
        g_star = g_target(abs(dE0), p)

        for _ in range(cfg.n_substeps):
            # a: exact ZOH over the substep, c re-evaluated at substep start
            c_sub = switch_c(D_cur - G_cur, S_s, p, floor)[0]
            drive = p.k_in * (a_hold + mon_cost + p.chi * c_sub)
            decay = p.k_ext * u_ext + (s.k_pull * m if armed else 0.0) \
                + p.rho_a
            lam_a = (drive + decay) / p.tau_a
            a_star = drive / (drive + decay) if (drive + decay) > 0.0 else a_s
            if s.quasi_steady_a:
                a_fun = lambda tau: a_star  # noqa: E731
            else:
                a_fun = lambda tau: zoh_lag(a_s, a_star, lam_a, tau)  # noqa: E731
            D_fun = lambda tau: zoh_lag(D_cur, D_star, lam_D, tau)    # noqa: E731

            def dGdtau(Gv, av, Dv):
                E = Dv - Gv
                cv, _fa = switch_c(E, S_s, p, floor)
                return (p.beta_G * (1 - av) * Gv * (1 - Gv)
                        - p.alpha_G * av * Gv
                        - p.eta * cv * Gv
                        - p.gam_G * Gv
                        + g_s * math.tanh(E / p.Es) * (Gv + p.eps0)
                        * (1 - Gv)) / p.tau_G

            k1 = dGdtau(G_cur, a_fun(0.0), D_fun(0.0))
            k2 = dGdtau(G_cur + 0.5 * hsub * k1,
                        a_fun(0.5 * hsub), D_fun(0.5 * hsub))
            k3 = dGdtau(G_cur + 0.5 * hsub * k2,
                        a_fun(0.5 * hsub), D_fun(0.5 * hsub))
            k4 = dGdtau(G_cur + hsub * k3, a_fun(hsub), D_fun(hsub))
            G_cur += (hsub / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
            # advance the analytic states to the substep boundary (their
            # recursors restart from the new values next substep)
            D_cur = zoh_lag(D_cur, D_star, lam_D, hsub)
            # the backlog state: EMA at tau_D toward the switch state c
            # (the unchecked-content arrival rate), advanced per substep
            # with the same exact ZOH recursor — never Euler
            B_s = zoh_lag(B_s, c_sub, lam_B, hsub)
            # S's target is LINEAR in a and a(tau) is exponential within the
            # substep, so the exact substep mean of a is closed-form; using
            # it removes the O(h*da) input-freezing error that would
            # otherwise shift the switch-on moment (w = 0.05 makes the
            # crossover time sensitive to S at the 2e-3 -> 0.7 t.u. level)
            if s.quasi_steady_a or lam_a <= 0.0:
                a_bar = a_star
            else:
                a_bar = a_star + (a_s - a_star) * (
                    (1.0 - math.exp(-lam_a * hsub)) / (lam_a * hsub))
            S_s = zoh_lag(S_s, S_target(a_bar, p), s.lam_S, hsub)
            g_s = zoh_lag(g_s, g_star, s.lam_g, hsub)
            a_s = a_fun(hsub)

        # ---- commit ----
        self.G = min(max(G_cur, 0.0), 1.0)
        self.D = D_cur
        self.B = B_s
        self.sn.a, self.sn.S, self.sn.g = a_s, S_s, g_s
        self.t += H_STEP

        # ---- the REAL write path (Stage 1.5 wiring) ----------------------
        # The block gates on the CLIPPED-SIGMOID TRIGGER's state (m > 0.5):
        # writes to the durable store are suppressed ENTIRELY — not
        # down-weighted; a binding budget launders a partial weight
        # (measured: down-weight achieves only ~3%).  This is deliberately
        # the TRIGGER's state rather than dpdr's a > a_block form: the
        # trigger fires at G < G_trig ~ 0.3, slightly BEFORE inward
        # attention pins (a > 0.5), so the harness block arms strictly
        # earlier in the descent — same stuck-state coverage, more
        # protective on the way in.
        write_block = bool(m > 0.5) and cfg.block_on
        store_on = self.cfg.consol is not None
        if store_on:
            self._consolidate(write_block)

        rec = StepLog(
            t=self.t, a=self.sn.a, G=self.G, D=self.D, S=self.sn.S,
            g=self.sn.g, E=self.D - self.G, c=c0, m=m, A_eff=A_eff,
            edge_addend=edge_addend, monitor_cost=mon_cost,
            acted=bool(armed and m > 0.5),
            write_block=write_block,
            floor_active=floor_active, B=self.B,
            W_self=self.W_self, W_task=self.W_task,
            M_self=self.M_self, M_task=self.M_task,
            store_on=store_on, kicked=kicked,
        )
        self.traj.add(rec)
        return rec

    # ------------------------------------------------------------------
    def _consolidate(self, write_block: bool) -> None:
        """One selective-write step into the harness's OWN durable store
        (dpdr.consolidation imported READ-ONLY: its gate, budget and
        constants; the harness's own state, never dpdr's).  Equations are
        dpdr/consolidation.py's — the working set fills with the model's
        own attention semantics, the durable store fills through the
        BUDGETED, BINDING selective write — advanced with the exact ZOH
        recursor over the step (never Euler).  RETRIEVAL IS NOT WIRED:
        store_drive enters da/dt in the consolidation variant, and wiring
        it here would change the plant — a dynamics change that needs its
        own fold measurement, out of scope for the write path.  With no
        'retrieve' channel and k_bg = 0 the store is DYNAMICALLY INERT by
        construction (verified in part X3: max|dG| store-on vs store-off
        = 0.00e+00)."""
        cp = self.cfg.consol
        p = self.p
        # working set: exact lag toward the attention semantics
        lam_W = 1.0 / cp.tau_W
        self.W_self = zoh_lag(self.W_self, self.sn.a, lam_W, H_STEP)
        self.W_task = zoh_lag(self.W_task, 1.0 - self.sn.a, lam_W, H_STEP)
        # selective write: dpdr's gate (policy weight; the BLOCK is the
        # harness's trigger rule above) -> budgeted, binding scale -> fill
        g_self = 0.0 if write_block else consolidation_gate(
            self.sn.a, ConsolParams(**{**cp.__dict__, "block": False}))
        g_task = 0.0 if write_block else (1.0 - self.sn.a)
        raw_s = cp.v_self * self.W_self * g_self
        raw_t = cp.v_task * self.W_task * g_task
        tot = raw_s + raw_t
        if tot <= 0.0:
            k_s = k_t = 0.0
        else:
            scale = min(1.0, cp.B / tot)
            k_s, k_t = raw_s * scale, raw_t * scale
        # dM/dt = k*(1-M) - mu_M*M with k held (ZOH): exact step
        for k, attr in ((k_s, "M_self"), (k_t, "M_task")):
            M0 = getattr(self, attr)
            if cp.mu_M == 0.0:
                setattr(self, attr, 1.0 - (1.0 - M0) * math.exp(-k * H_STEP))
            else:
                lam = k + cp.mu_M
                star = k / lam
                setattr(self, attr, star + (M0 - star) * math.exp(-lam * H_STEP))

    def _dEdt(self, A_eff: float, floor: float | None) -> float:
        """dE/dt = dD/dt - dG/dt at the current state (g*'s input)."""
        p = self.p
        a, G, D, S, g = self.sn.a, self.G, self.D, self.sn.S, self.sn.g
        E = D - G
        c, _ = switch_c(E, S, p, floor)
        dG = (p.beta_G * (1 - a) * G * (1 - G)
              - p.alpha_G * a * G - p.eta * c * G - p.gam_G * G
              + g * math.tanh(E / p.Es) * (G + p.eps0) * (1 - G)) / p.tau_G
        dD = ((p.D_base + A_eff) * p.beta_D * (1 - D)
              - p.delta_D * D) / p.tau_D
        return dD - dG

    # ------------------------------------------------------------------
    def _log_initial(self, sch: Schedule):
        """Record the t=0 state so the trajectory grid starts at 0."""
        A_eff, edge_addend = self._edge(0.0, sch)
        c0, fa = switch_c(self.D - self.G, self.sn.S, self.p,
                          self.cfg.sn.floor if self.cfg.regulator_on else None)
        m = self._trigger()
        self.traj.add(StepLog(
            t=0.0, a=self.sn.a, G=self.G, D=self.D, S=self.sn.S,
            g=self.sn.g, E=self.D - self.G, c=c0, m=m, A_eff=A_eff,
            edge_addend=edge_addend, monitor_cost=0.0,
            acted=bool(m > 0.5 and 0.0 >= self.cfg.t_engage),
            write_block=bool(m > 0.5), floor_active=fa, B=self.B,
            W_self=self.W_self, W_task=self.W_task,
            M_self=self.M_self, M_task=self.M_task,
            store_on=self.cfg.consol is not None))

    def run(self, sch: Schedule, T: float, kick_fn: Callable | None = None,
            log_initial: bool = True) -> Trajectory:
        """Run the loop for T time units (T/h steps).  kick_fn(t) -> float
        optionally injects a G impulse at the step beginning at t."""
        if log_initial and not self.traj.log:
            self._log_initial(sch)
        n = int(round(T / H_STEP))
        for _ in range(n):
            k = kick_fn(self.t) if kick_fn is not None else 0.0
            self.step(sch, kick=k)
        return self.traj


# --------------------------------------------------------------------------
def run_agent(sch: Schedule, T: float, p: Params | None = None,
              regulator: bool = True, edge: bool = True,
              **kw) -> dict:
    """Convenience: fresh Agent, run, return arrays."""
    cfg = AgentConfig(regulator_on=regulator, edge_on=edge, **kw)
    ag = Agent(p, cfg)
    ag.run(sch, T)
    return ag.traj.arrays()
