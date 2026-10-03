"""GENERATIONAL variant — the N-generation compounding realization of
Zhang's operator f = M o V o f_T.  Opt-in, frozen model untouched; this
module IMPORTS read-only (dpdr.integrate.simulate, dpdr.window.rollout_self
and _v_plus) and modifies nothing upstream.

WHY THIS MODULE EXISTS (handoff-selfreg-generational): the project has a
genuine f_T (window.py:rollout_self) and a genuine V (the one-sided
counterfactual-error evaluation, window.py:_v_plus), but its "M" is FAKE —
window.py credits a correction to dG/dt and never touches Params, so it
modifies the STATE transiently, not the SYSTEM.  Nothing in the project
has persistent, compounding self-modification.  This module supplies it:

  A single agent carries MODIFIABLE PARAMETERS (a subset of Params).
  Each generation: (1) the agent LIVES one canonical task (inward episode
  + rescue, the metrics.py rescue-scenario geometry) under the FROZEN
  driver dpdr.integrate.simulate, imported unmodified; (2) at the moment
  its bounded self-simulation certifies the largest deficit (argmax over
  the episode of V at horizon T — "act at the moment of maximal certified
  deficit"), it runs f_T on each CANDIDATE modification of its own source
  and evaluates each with V; (3) M: it ADOPTS the single modification V
  most certifies (most negative V-margin) — a PERSISTENT change to its
  own Params — and the change COMPOUNDS: the next generation runs the
  modified system, which modifies itself again, from the carried setpoint.
  Capacity T enters ONLY through this decision (the variant never touches
  the RHS while living: no standing cost, no credited correction — those
  are window.py's channels and stay there).

  THE MODIFICATION RULE, DERIVED NOT DIALLED.  M is "hill-climb the
  certified verdict": candidates = every lever in DEFAULT_LEVERS x {x
  step, / step} with step = 1.15 (the fixed 15% increment the landscape
  was mapped with in the design scans experiments/_gen_scan{,2,3}.py);
  adopt argmin of the V-margin if it is below -atol_tau (atol_tau = 1e-4,
  a numerical floor — adopt sets are insensitive to it across 1e-6..1e-3,
  checked in exp12 part 1).  The lever set is every ENDOGENOUS-machinery
  Params field; exogenous demand/world fields (D_base, beta_D, delta_D —
  the agent cannot modify the world), all timescales, numerics and
  initial conditions are excluded IN PRINCIPLE (timescales additionally
  because rollout_self's inner step delta_roll = tau_G/2 is frozen with
  the frozen model — modifying timescales would invalidate the rollout's
  numerics; a constraint of the read-only reuse, disclosed, not a
  performance choice).  NO constant was chosen for outcome: whether a
  given T adopts a harmful move is a property of the FROZEN LANDSCAPE,
  not of this rule.

  *** THE TWO ARMS (handoff-selfreg-gen-twoarm).  The certified rule
  above REFUSES TO MOVE unless the certifier V approves, so its monotone
  improvement is GUARANTEED BY THE ACCEPTANCE FILTER, not produced by
  the mechanism — and a self-improver that only accepts certified
  improvements is optimizing against a trusted oracle, not
  self-improving.  GenParams.adopt_policy therefore selects the arm:
  "certified" (ARM A, the infallible-by-construction baseline described
  above — the default, so all cached arm-A numbers stay reproducible)
  or "always" (ARM B, the fallible agent: adopt argmin V whatever the
  margin's sign, with atol_tau used ONLY to detect an exact tie with
  the no-op, never as an acceptance gate).  Degradation is possible
  only in arm B, and arm B is the only arm that can expose an
  ACCUMULATION trap (a walk whose every step looks no worse to V yet
  whose sequence lands worse in truth — arm A halts at the first
  non-improving candidate).  See experiments/exp12_preregistration.md
  for the arm-B registration and the pre-stated degradation criterion. ***

  *** THE REGULATOR COMPOSITION (handoff-selfreg-compose; exp13).  The
  regulator is the project's only CONDITIONAL actuator, and it is NOT
  orthogonal to the self-modifier: modify_once chooses its move by
  certify_state evaluated AT THE ALARM STATE (argmax over the episode of
  V), so anything that changes the state TRAJECTORY changes the agent's
  EVIDENCE and hence which move it adopts.  GenParams.reg (a
  RegulatorParams | None, default None) runs the LIVE episode under
  dpdr.regulator.simulate_reg instead of dpdr.integrate.simulate — the
  floor/k_pull/c_mon pieces change a, G, S and therefore the alarm state
  and every candidate margin.  GenParams.self_model_regulated (default
  False) additionally lets the agent's SELF-MODEL foresee the regulator:
  the rollout inside certify_state then evaluates its cannibalization
  switch at the regulated threshold (dpdr.regulator.floor_theta_eff),
  which is rollout_self's ONLY regulator channel — its Teff_sw argument.
  The other regulator pieces (k_pull, c_mon, G_trig) have NO channel in
  rollout_self: the agent's f_T cannot represent them, so their V-margins
  are zero BY CONSTRUCTION (measured, not assumed, in exp13 part 1).
  With self_model_regulated=False the agent ACTS UNDER PROTECTION IT
  CANNOT FORESEE — the asymmetry between the two settings is itself a
  measurement (R1 vs R2 in experiments/exp13_compose.py), not a bug.
  reg=None / self_model_regulated=False is the two-arm system of exp12
  EXACTLY, so every cached exp12 number stays reproducible. ***

  *** THE HAZARD — A THRESHOLD CAN BE MANUFACTURED BY CONSTRUCTION. ***
  If the modification rule were chosen so that low T yields a bad
  modification, a "critical capacity threshold" would appear BY DESIGN —
  monotonicity-by-construction inverted, the same error class as the
  original claim.  Two traps, specifically avoided:
  (a) "short rollouts are less accurate" is FALSE in a deterministic ODE
      — a shorter rollout predicts the NEAR future BETTER; nothing here
      builds on that premise;
  (b) no constant was tuned to produce a threshold.  The design scans
      (BEFORE the rule was fixed) found the landscape's decisive
      structure: certification is NESTED in T (every move a short rollout
      certifies as an improvement, a longer rollout certifies at least as
      strongly; 0 trap-direction sign flips in ~1200 (state, lever, sign)
      evaluations at frozen-trajectory states, plus dynamic walks), and
      V is EXACTLY ZERO at both attractors and on the whole rescue/settle
      arc (the rollout of a recovering trajectory foresees no error
      growth), so the settle-erosion cost of a modification is
      structurally INVISIBLE to the evaluator at every T.  The
      pre-registered prediction is therefore the NO-LOWER-THRESHOLD side
      (see experiments/exp12_generational.py, PREREGISTRATION, dumped to
      cache BEFORE the battery ran).  A genuine local-vs-global structure
      DOES exist (the correction machinery: certified-adoptive at every
      T, lifts the episode dip, erodes the settle over generations) — but
      it travels with adoption at ALL T, so it cannot manufacture a low-T
      threshold; it is reported as the realization's honest inversion:
      degradation grows WITH capacity, not below it.

  *** THE BLIND LEVERS (handoff-selfreg-blindlever; exp15).  The
  two-arm result established the negative (no trap of either kind; arm B
  never made an uncertified adoption) and the STRUCTURAL REASON: all 18
  DEFAULT_LEVERS act on ONE inward-drive / weakening channel, so a
  short rollout's gradient aligns with the global outcome.  exp15
  constructs the missing object — a lever whose effect the evaluator V
  CANNOT see — and asks whether the walk then degrades.  GenParams.
  blind_levers (default (), OPT-IN so every existing cache stays
  reproducible) appends rescue-window-only Params fields to the
  candidate set; BLIND_LEVERS = ("k_ext",) is the registered set.  The
  invisibility is BY HORIZON ARITHMETIC, not by tuning (see the comment
  at BLIND_LEVERS): the alarm state is at t = 100.0 exactly, the
  rollout reaches t_a + T <= 740 < 800 = RESCUE_T0 at the grid's
  T_max = 640, and — a second, independent mechanism — certify_state
  evaluates the self-model at u_ext = 0.0, where k_ext has identically
  zero effect, so its V-margin is EXACTLY 0.0 in floating point.  An
  exactly-zero margin is an exact tie with the no-op, which BOTH arms'
  rules refuse (arm A needs a certified negative margin; arm B's tie
  gate |m| > atol_tau exists precisely so the agent never acts on a
  move with no self-assessed basis) — the argmin semantics, arms,
  atol_tau, step and modify_once's rules are UNCHANGED, per the brief.
  ***

  *** THE TRAIN/TEST SPLIT (handoff-selfreg-exp16; exp16).  exp15
  showed that a lever invisible to V is STRUCTURALLY refused (margin
  exactly 0.0 -> the tie rule rejects it, 0 blind adoptions), so the
  failure mechanism the ODE could still host is MISJUDGMENT: a NONZERO
  apparent improvement that is harmful in truth.  A train/test gap
  supplies exactly that by construction: V is evaluated in one context
  (the TRAIN task the agent lives and self-modifies on) while the
  outcome is realised in another (the TEST task the result is measured
  on) — the class-(C) shape (sound but non-representative evaluator).
  GenParams.schedule_override (Schedule | None, default None, OPT-IN so
  every existing cache — exp12's, exp13's, exp14's, exp15's — stays
  reproducible bit-for-bit) replaces the canonical generation task for
  the LIVE episode of every generation.  Default None = the published
  system exactly (generation_schedule(), unchanged).  The registered
  exp16 pair is TRAIN = the canonical schedule, TEST = the SAME episode
  with the external rescue REMOVED (the exogenous-help-removal
  generalisation; see experiments/exp16_preregistration.md — both
  geometries were fixed on a principled criterion BEFORE the first
  run, per the anti-tuning rule).  The split NEVER enters the agent's
  decision: modify_once sees only the TRAIN episode; the TEST
  evaluation is a measurement taken outside the loop.
  ***

EPISTEMIC STATUS: this variant is a DIFFERENT SYSTEM — follow-up work,
not a finding of the frozen model or the published paper.  The frozen
model is never modified: importing dpdr alone activates nothing,
generation 1 of every run IS the frozen canonical rescue run (exp12
part 0 verifies bit-exactness against dpdr.integrate.simulate), and with
M disabled (enabled=False) every generation is a frozen simulate call.
Between generations the five-state setpoint carries (same agent, no
state reset — the modification is in the SYSTEM, not the state).
Deterministic model: every threshold is a locus, not a distribution.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from itertools import chain

import numpy as np

from .integrate import simulate
from .model import Params, Schedule
from .regulator import RegulatorParams, floor_theta_eff, simulate_reg
from .window import WindowParams, _v_plus, rollout_self

__all__ = ["GenParams", "DEFAULT_LEVERS", "BLIND_LEVERS", "ALL_LEVERS",
           "generation_schedule", "certify_state", "modify_once",
           "run_generational"]

# The modifiable set: every ENDOGENOUS-machinery Params field (generator,
# cannibalization switch, control loop, setpoint tracking, attention
# gains).  Exclusions are principled, not performance-driven (docstring).
DEFAULT_LEVERS = (
    "alpha_G", "beta_G", "gam_G", "eta", "eps0",       # generator
    "Theta", "w", "sigma_c",                           # switch
    "g0", "Es", "pi", "mu", "dEdt_ref",                # control loop
    "k_s", "lam_S",                                    # setpoint
    "k_in", "chi", "rho_a",                            # attention
)

# BLIND LEVERS (exp15, handoff-selfreg-blindlever) — OPT-IN, appended via
# GenParams.blind_levers; the default lever set above is UNCHANGED so every
# existing cache stays reproducible.  A blind lever is a Params field whose
# effect is confined to the RESCUE WINDOW (t >= RESCUE_T0 = 800), which the
# agent's evaluator V cannot reach from the decision point at any horizon in
# the registered grid — INVISIBILITY BY HORIZON ARITHMETIC, not by tuning:
# the alarm state is measured at episode ONSET (argmax over t in [100, 200),
# generational.py:_alarm_state, and the alarm is at t = 100.0 exactly),
# certify_state rolls the agent's own source forward T from there, and at
# T_max = 640 the rollout reaches only t = 100 + 640 = 740 < 800.  Second,
# independent mechanism (verified in exp15, not assumed): the standard
# self-model assumption of window.py:rollout_self holds the exogenous
# channels at their CURRENT values, and certify_state passes u_ext = 0.0
# (the alarm is in the pre-rescue episode), so a lever acting only through
# u_ext has an EXACTLY ZERO V-margin in floating point at every T.  Neither
# mechanism was tuned; both are structural consequences of the frozen code.
# The one registered blind lever is the external-pull gain k_ext: in the
# frozen RHS it enters only as -k_ext*u_ext*a in da/dt (dpdr/model.py:121),
# so k_ext = 0 identically when u_ext = 0 — its window is [800, 1000) and
# its sign is not engineered.  The rescue onset/offset times are NOT
# registered: generation_schedule() fixes them as module constants
# (RESCUE_T0/T1), they are not Params fields, and hacking the schedule to
# parameterize them is out of bounds — stated and dropped per the brief.
# OUT-OF-BOUNDS NOTE (the construction's own boundary): if T were raised
# above 800 - 100 = 700 the rollout would reach the rescue window and the
# lever would become VISIBLE, DESTROYING the construction; the registered
# grid T <= 640 respects this (with a 60 t.u. margin), and exp15 never
# raises T to make the blind lever reachable.
BLIND_LEVERS = ("k_ext",)
# the full opt-in lever set: plant levers first, then blind levers
ALL_LEVERS = tuple(chain(DEFAULT_LEVERS, BLIND_LEVERS))

# Canonical generation task (metrics.py rescue-scenario geometry):
# inward episode [100,200) a_hold 0.9 + affect pulse 0.5 to 160, external
# rescue u_ext 0.8 on [800,1000).  The agent lives it with the FROZEN
# driver; the schedule repeats identically every generation.
EP_T0, EP_T1, PULSE_END = 100.0, 200.0, 160.0
RESCUE_T0, RESCUE_T1, RESCUE_U = 800.0, 1000.0, 0.8


@dataclass
class GenParams:
    """Constants of the generational loop (see module docstring).

    Defaults are the design point; enabled=False (or step=1.0) is the
    FROZEN model exactly (no adoption ever happens, every generation is
    a frozen dpdr.integrate.simulate call).
    """
    enabled: bool = True
    T: float = 40.0                # self-simulation horizon at the decision
    levers: tuple = DEFAULT_LEVERS
    # blind levers (exp15): Params fields acting ONLY inside the rescue
    # window, appended to `levers` when non-empty.  The DEFAULT () keeps
    # every existing run and cache bit-reproducible (exp15 part 0 checks
    # this); ALL_LEVERS = DEFAULT_LEVERS + BLIND_LEVERS is the opt-in set.
    blind_levers: tuple = ()
    step: float = 1.15             # multiplicative adoption step (=1+15%)
    atol_tau: float = 1e-4         # numerical floor (tie / no-op detection)
    adopt_policy: str = "certified"   # "certified" | "always" (two-arm)
    horizon: float = 1010.0        # generation length (task + settle)
    dt: float = 0.5                # integration grid (exp7/e protocol)
    wp: WindowParams = field(default_factory=WindowParams)
    # regulator composition (exp13): None = the exp12 two-arm system
    # exactly; a RegulatorParams runs the LIVE episode under
    # dpdr.regulator.simulate_reg (imported read-only)
    reg: RegulatorParams | None = None
    # when True the agent's self-model (the rollout inside certify_state)
    # ALSO sees the regulator — its only f_T channel, the switch threshold
    # Teff_sw (floor_theta_eff).  False = the agent acts under protection
    # it cannot foresee.  The asymmetry is itself a measurement (R1 vs R2).
    self_model_regulated: bool = False
    # train/test split (exp16): when not None this Schedule replaces the
    # canonical generation task for the LIVE episode of every generation
    # (the agent LIVES and SELF-MODIFIES on this task).  Default None =
    # generation_schedule(), the published system exactly — every existing
    # cache stays reproducible.  The override does NOT touch the agent's
    # decision machinery: modify_once is unchanged and evaluates the same
    # live trajectory it always did.
    schedule_override: Schedule | None = None

    def effective_levers(self) -> tuple:
        """The candidate set for this run: plant levers plus any blind
        levers (exp15).  Order is plant-then-blind so the lever index in
        a margin table is stable whether or not blind levers are on."""
        if not self.blind_levers:
            return self.levers
        return tuple(self.levers) + tuple(self.blind_levers)


def generation_schedule() -> Schedule:
    """The canonical generation task (see module docstring)."""
    return Schedule({"a_hold": [(EP_T0, EP_T1, 0.9)],
                     "A": [(EP_T0, PULSE_END, 0.5)],
                     "u_ext": [(RESCUE_T0, RESCUE_T1, RESCUE_U)]})


def certify_state(y, p: Params, gp: GenParams, T: float, A: float) -> float:
    """V at one state: rollout the agent's own (current) source forward T
    with exogenous held at current values (the standard self-model
    assumption of window.py:rollout_self) and evaluate the one-sided
    counterfactual-error verdict.  Used INSIDE the episode, so a_hold is
    the episode's 0.9 and A is its value at the evaluation time (0.5
    before PULSE_END, 0 after).  Under the composition
    (gp.self_model_regulated and gp.reg is not None) the rollout's
    cannibalization switch is evaluated at the REGULATED threshold
    (floor_theta_eff) — the self-model foresees the regulator through
    rollout_self's ONLY regulator channel, its Teff_sw argument."""
    teff_sw = p.Theta * y[3] / p.S_rest
    if gp.self_model_regulated and gp.reg is not None:
        teff_sw = floor_theta_eff(y[3], p, gp.reg)
    _a, G_ol, D_ol = rollout_self(y, p, gp.wp, T, 0.9, A, 0.0, teff_sw)
    return _v_plus((D_ol - G_ol) - (y[2] - y[1]), gp.wp.w_v)


def _alarm_state(sol: dict, p: Params, gp: GenParams):
    """argmax over the episode samples of V(y, T): the moment of maximal
    certified deficit — the agent's decision point.  Returns
    (index, t, y, V, A) or None when V = 0 on the whole episode (an
    equilibrium-grade trajectory certifies nothing, so M does not fire)."""
    i0 = int(np.searchsorted(sol["t"], EP_T0))
    i1 = int(np.searchsorted(sol["t"], EP_T1))
    best_v, bi = 0.0, None
    for i in range(i0, max(i0 + 1, i1)):
        y = np.array([sol["a"][i], sol["G"][i], sol["D"][i], sol["S"][i],
                      sol["g"][i]])
        A = 0.5 if float(sol["t"][i]) < PULSE_END else 0.0
        v = certify_state(y, p, gp, gp.T, A) \
            if gp.T >= gp.wp.delta_roll else 0.0
        if v > best_v:
            best_v, bi = v, i
    if bi is None:
        return None
    y = np.array([sol["a"][bi], sol["G"][bi], sol["D"][bi], sol["S"][bi],
                  sol["g"][bi]])
    A = 0.5 if float(sol["t"][bi]) < PULSE_END else 0.0
    return bi, float(sol["t"][bi]), y, best_v, A


def modify_once(p: Params, sol: dict, gp: GenParams) -> dict:
    """M: choose and apply ONE persistent Params change, per the arm.

    Evaluates every candidate (lever, sign) by running f_T on the
    modified source at the alarm state and comparing V against the
    unmodified source, then adopts argmin of the V-margin under the
    arm's ADOPTION POLICY:

      adopt_policy="certified"  (ARM A, the conservative baseline):
        adopt only when the margin is below -atol_tau — the walk refuses
        to move unless the certifier V approves.  INFALLIBLE BY
        CONSTRUCTION: monotone improvement is guaranteed by this
        acceptance filter, not produced by the mechanism.

      adopt_policy="always"  (ARM B, the fallible agent): ALWAYS adopt
        argmin V whatever the margin's sign.  The agent acts on its
        best guess WITHOUT knowing whether it is right — fallibility is
        the mechanism, degradation is POSSIBLE, and this is the only arm
        that can expose an accumulation trap (a walk whose every step
        looks no worse to V yet whose sequence lands worse in truth).

    In BOTH arms atol_tau serves only to detect an exact tie / no-op
    (margin within atol of the null move) — never as a sign gate on
    fallible adoption.  The ADOPTION DECISION USES THE ROLLOUT ONLY —
    the true effect on the next generation is not available to the
    agent (that is the point).
    """
    alarm = _alarm_state(sol, p, gp)
    if alarm is None:
        return dict(adopted="", lever="", sign=0.0, margin=0.0, V=0.0,
                    t_eval=None, p_new=p, margins={})
    _i, t_eval, y, V0, A = alarm
    margins: dict = {}
    for lever in gp.effective_levers():   # exp15: + blind levers when opted in
        for sgn in (+1.0, -1.0):
            pc = replace(p, **{lever: getattr(p, lever)
                               * (gp.step ** sgn)})
            margins[f"{lever}{'+' if sgn > 0 else '-'}"] = \
                certify_state(y, pc, gp, gp.T, A) - V0
    # argmin over the LEVER moves only (the no-op is not a candidate for
    # the fallible arm: "always adopt argmin V" means the best GUESS, and
    # when every guess looks worse the least-bad one is still the guess)
    best_k = min(margins, key=margins.get)
    best_m = margins[best_k]
    if gp.adopt_policy == "always":
        # adopt regardless of sign.  atol_tau detects ONLY an exact tie
        # with the no-op (|margin| <= atol): a V-indistinguishable-from-
        # no-op move is not a fallible judgement, it is a coin flip with
        # no self-assessed basis, so the agent does not act on it.
        adopt = abs(best_m) > gp.atol_tau
    elif gp.adopt_policy == "certified":
        adopt = best_m < -gp.atol_tau
    else:
        raise ValueError(f"unknown adopt_policy {gp.adopt_policy!r}")
    if adopt:
        lever = best_k[:-1]
        sgn = 1.0 if best_k[-1] == "+" else -1.0
        p_new = replace(p, **{lever: getattr(p, lever) * (gp.step ** sgn)})
        return dict(adopted=best_k, lever=lever, sign=sgn, margin=best_m,
                    V=V0, t_eval=t_eval, p_new=p_new, margins=margins)
    return dict(adopted="", lever="", sign=0.0, margin=best_m, V=V0,
                t_eval=t_eval, p_new=p, margins=margins)


def run_generational(gp: GenParams, n_gen: int, p0: Params | None = None,
                     keep_sol: bool = False) -> dict:
    """The generational loop.  Each generation: live the canonical task
    with the frozen driver under the CURRENT Params; measure performance
    (episode dip G_min, functional end G_end, end error E_end); then M
    (modify_once) applies at most one persistent Params change that the
    next generation inherits.  ALL FIVE STATES carry between generations
    (same agent, next task — only the parameters and the calendar reset),
    so the persistent change is in the SYSTEM, not the state.

    Returns per-generation arrays (G_min, G_end, E_end, c_max, adopted
    lever names, margins, certified V, decision times), the final Params,
    and (keep_sol=True) the per-generation solution dicts.
    """
    p = Params() if p0 is None else p0
    # exp16: the live task is the canonical schedule unless overridden
    # (OPT-IN; the default keeps every existing cache bit-reproducible)
    sch = (gp.schedule_override if gp.schedule_override is not None
           else generation_schedule())
    out = {k: [] for k in ("G_min", "G_end", "E_end", "c_max", "adopted",
                           "margin", "V", "t_eval", "margins")}
    sols = []
    y_carry = None
    for k in range(n_gen):
        if y_carry is None:
            pk = p
        else:                   # full five-state carry: the same agent
            pk = replace(p, a0=float(np.clip(y_carry[0], 0.0, 1.0)),
                         G0=float(np.clip(y_carry[1], 0.0, 1.0)),
                         D0=float(np.clip(y_carry[2], 0.0, 1.5)),
                         S0=float(np.clip(y_carry[3], 0.0, 1.0)),
                         g_init=float(np.clip(y_carry[4], 0.0, 2.0)))
        sol = (simulate_reg(pk, gp.reg, sch, gp.horizon, dt=gp.dt)
               if gp.reg is not None
               else simulate(pk, sch, gp.horizon, dt=gp.dt))
        out["G_min"].append(float(sol["G"].min()))
        out["G_end"].append(float(sol["G"][-1]))
        out["E_end"].append(float(sol["E"][-1]))
        out["c_max"].append(float(sol["c"].max()))
        if gp.enabled and gp.step != 1.0:
            rec = modify_once(pk, sol, gp)
        else:
            rec = dict(adopted="", lever="", sign=0.0, margin=0.0, V=0.0,
                       t_eval=None, p_new=pk, margins={})
        out["adopted"].append(rec["adopted"])
        out["margin"].append(float(rec["margin"]))
        out["V"].append(float(rec["V"]))
        out["t_eval"].append(np.nan if rec["t_eval"] is None
                             else float(rec["t_eval"]))
        # exp15: the full per-decision margin dict (read-only record; the
        # walk itself uses only rec["margin"]/"adopted" as before)
        out["margins"].append(rec["margins"])
        p = rec["p_new"]
        y_carry = np.array([sol["a"][-1], sol["G"][-1], sol["D"][-1],
                            sol["S"][-1], sol["g"][-1]])
        if keep_sol:
            sols.append(sol)
    res = {k: (np.array(v, dtype=object) if k in ("adopted", "margins")
               else np.array(v))
           for k, v in out.items()}
    res["params_final"] = p
    res["T"] = gp.T
    res["n_gen"] = n_gen
    if keep_sol:
        res["sols"] = sols
    return res
