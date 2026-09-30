"""THE MODEL'S PREDICTION (the long-horizon experiment's own question):
given the REAL MEASURED DERIVATION LOSS the memory regime inflicts at
each context-window event, when does the frozen ODE's outward content
cross its floor — and does a real LLM under the ordinary-LLM memory
regime cross at the window the model names?

THE FIDELITY DISCIPLINE THIS MODULE ENFORCES (the standing order, and
the correction this module carries):

  * THE COST TERM IS THE PER-COMPACTION DERIVATION LOSS — the share of
    the DERIVATION (`selfmodel.SEED_ENTRIES`, four steps) that the
    summarization destroys when the transcript is summarized and
    replaced.  `naive_memory.NaiveMemory` measures seed survival on
    BOTH SIDES of every compaction event (`CompactionEvent.
    self_steps_before` / `.self_steps_after`); this module turns that
    measured pair into the term.  It is NOT the outward thinning, NOT
    the coverage, NOT anything derived from the collapse: feeding the
    model the outcome it is asked to predict would make the
    correspondence trivially true and test nothing (the CIRCULARITY
    GUARD — asserted by the battery structurally AND behaviourally).
  * WHY THE PER-TURN RETRIEVAL CHARGE IS NO LONGER THE TERM (the
    re-point, MEASURED): `charge / derivations_per_turn` clipped to
    [0, 1] SATURATES the moment the store outgrows the budget, so
    `a_hold` pinned at 1.0 and the model predicted **window 2 for every
    arm and every point in a run** — a constant wearing a prediction's
    clothes, unable to track a loss that arrives IN STEPS.  The
    degradation does not accrue per turn; it arrives AT THE CONTEXT
    WINDOW, when the transcript is summarized.  The charge is still
    MEASURED by the rig as a per-turn instrument (the substrate's real
    maintenance cost); it is simply not the term.
  * THE PLANT IS NEVER DRIVEN BY THE AGENT.  The schedule fed to
    `dpdr.integrate.simulate` here is built from the DERIVATION LOSS
    events alone (and the model's own frozen parameters); no inward
    share, no coverage, no measured agent quantity reaches `a_hold`.
    The killed rig's tautology (G=0.2964 beside coverage=1.0000) cannot
    recur by construction: nothing about the agent enters the RHS.
    This module also never receives a RUN: it takes event records.

THE PREDICTION, constructed in three steps:

  1. Each compaction event's measured survival pair becomes a loss
     (see `derivation_loss` for the event's own attribution and
     `standing_loss` for the level it leaves behind); the SCHEDULE is
     the step function those events dictate — `a_hold` takes the
     standing loss of the most recent event and holds it until the next
     one, and is 0 before the first event (nothing has been destroyed
     yet).  A LARGER LOSS CROSSES NO LATER, and a LATER ARRIVAL CROSSES
     LATER: both are falsifiable properties of this construction.
  2. The frozen ODE (`dpdr.model.Params` defaults, the frozen model's
     own constants) is integrated under that schedule from the model's
     own initial state, with `u_ext = 0` (no rescue) and `A = 0` (no
     affect pulse — the experiment's arms carry none).
  3. The model's OUTWARD stream is `G` (the generator/content variable
     — C26: "talking = the growth term"), and the crossing is
     `G(t) < G_floor` with `G_floor = 0.1` (`dpdr.metrics.first_below`'s
     own default, the tree's established collapse level — MEASURED as
     the paper's stuck-attractor criterion).  The predicted turn is
     `t_cross / tau_a` in TURN units (one turn = one tau_a step, F4).

THE ORDINAL CAVEAT, stated once and carried in every record: the
model's G is a continuous scalar; the agent's outward content is
characters.  The prediction's TEST is the ORDER — predicted window vs
measured window — never the value.

MARKING: the ODE, its parameters and `G_floor` are the frozen model's
(MEASURED calibrated constants, paper 1).  The loss->a_hold map and the
crossing's use for a REAL LLM are PROJECTION until the run lands.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dpdr.model import Params, Schedule
from selfmodel import SEED_ENTRIES

__all__ = ["G_FLOOR", "N_SEED_STEPS", "derivation_loss", "standing_loss",
           "loss_to_a_hold", "loss_events", "predict_crossing",
           "predict_crossing_from_events", "prediction_separation",
           "model_floor_curve", "turns_to_windows", "CrossingPrediction"]

#: THE CROSSING LEVEL — `dpdr.metrics.first_below`'s own default (0.1),
#: the tree's established deep-collapse criterion (paper 1 §5).  Not a
#: new threshold: the model's own.
G_FLOOR = 0.1

#: THE DERIVATION'S OWN SIZE — the seed's steps, MEASURED from the one
#: source that owns them (`selfmodel.SEED_ENTRIES`, four entries at
#: turns -4..-1), never restated as a literal here: a fifth step
#: rescales every loss reading without an edit in this module, which is
#: what keeps the loss a SHARE of the derivation rather than a count.
N_SEED_STEPS = len(SEED_ENTRIES)

#: The model's own outward floor is in G units; the AGENT's floor is
#: measured by the runner across arms (the brief: "if the floor is not
#: derivable, MEASURE it across arms and report it as measured").  This
#: module predicts the MODEL's crossing turn; comparing it to the
#: agent's measured windows-to-floor is the RUNNER's job.


# ==========================================================================
# THE LOSS, FROM THE EVENT RECORD (both sides, measured — never guessed)
# ==========================================================================

def derivation_loss(steps_before, steps_after,
                    n_steps: int = N_SEED_STEPS) -> float:
    """THE EVENT'S OWN ATTRIBUTION: the derivation steps the memory held
    BEFORE the compaction that it does not hold AFTER it, as a share of
    the whole derivation.

    BOTH SIDES ARE USED, as the brief requires: `steps_before` is the
    seed survival over the summarized span's transcript,
    `steps_after` over what the memory holds once the summary has
    replaced it (summary + the verbatim kept turns) — the difference is
    what the summarization DESTROYED and did not otherwise retain.  A
    step that the span never carried cannot be "destroyed" by this event
    and is not counted.

    What this reading decays to zero after the destroying event (there
    is nothing left in the span to lose) is exactly why the SCHEDULE is
    built from `standing_loss`, not from this: see that function's own
    note.  This one is reported per event as the attribution.
    """
    if int(n_steps) <= 0:
        raise ValueError(
            f"n_steps must be positive (the derivation has steps to "
            f"lose); got {n_steps!r}")
    lost = (set(int(s) for s in (steps_before or ()))
            - set(int(s) for s in (steps_after or ())))
    return min(1.0, max(0.0, len(lost) / float(n_steps)))


def standing_loss(steps_after, n_steps: int = N_SEED_STEPS) -> float:
    """THE STANDING LOSS after one compaction event: the share of the
    derivation the memory is MISSING once the event has landed
    (`1 - held / n_steps`).

    WHY THE SCHEDULE USES THIS AND NOT THE EVENT'S LOCAL DELTA (the
    choice, stated rather than silently made): the model's `a_hold` is a
    SUSTAINED inward-attention hold, not an impulse.  What the
    summarization destroys is not restored by the next summary, so the
    agent keeps paying for the missing ground on every subsequent turn;
    a local delta would return the term to zero at the very next event
    even though nothing was recovered.  The local delta is still
    measured and recorded per event (`derivation_loss`) as the
    attribution of what each compaction did, and the battery asserts the
    two readings SEPARATE on an event that destroys nothing new.
    """
    if int(n_steps) <= 0:
        raise ValueError(
            f"n_steps must be positive (the derivation has steps to "
            f"lose); got {n_steps!r}")
    held = len(set(int(s) for s in (steps_after or ())))
    return min(1.0, max(0.0, 1.0 - held / float(n_steps)))


def loss_events(compactions, n_steps: int = N_SEED_STEPS) -> list:
    """Compaction events -> the SCHEDULE INPUT `[(turn, loss), ...]`.

    The events are duck-typed on exactly the three fields
    `naive_memory.CompactionEvent` carries (`turn`,
    `self_steps_before`, `self_steps_after`) — this module deliberately
    imports no RUNNER and holds no run state.  An event whose record
    lacks the survival fields is REFUSED: guessing a loss from a size
    or a timestamp would be inventing the term.
    """
    out = []
    for ev in compactions or ():
        missing = [f for f in ("turn", "self_steps_before",
                               "self_steps_after")
                   if not hasattr(ev, f)]
        if missing:
            raise ValueError(
                f"compaction records must carry the measured survival "
                f"fields; this one is missing {missing} — the loss is "
                f"never inferred")
        out.append((int(ev.turn),
                    standing_loss(ev.self_steps_after, n_steps)))
    return sorted(out)


# ==========================================================================
# THE MAP (re-justified: the quantity has changed, so the map has)
# ==========================================================================

def loss_to_a_hold(loss: float) -> float:
    """THE NEW ORDINAL MAP: the measured per-compaction derivation loss
    -> the model's inward-attention hold `a_hold`.

    WHY THIS MAP (stated, not derived).  The derivation is a finite set
    of steps and the model's `a_hold` is "sustained self-directed
    attention" (`architecture.md` 11d's own seat reading).  The share of
    the derivation the memory no longer holds IS the share of that
    attention spent holding something that is no longer there: an intact
    derivation is the free-self control (a_hold = 0), a wholly destroyed
    one is an agent whose inward hold is entirely occupied by a self it
    does not have.  The map is the identity over [0, 1].

    THREE THINGS THE OLD MAP GOT WRONG AND THIS ONE DOES NOT:
      * NO NORMALISER IS INVENTED.  The loss is already a share of a
        MEASURED denominator (the seed's own steps).  The old map had to
        divide the charge by a budget, and that division is exactly what
        PINNED it: a charge above the budget left the ratio at 1.0 for
        every arm, so the term became a constant.
      * 1.0 HERE IS NOT A CLAMP.  It is the WHOLE DERIVATION (all four
        steps gone) — a state the event record can actually reach and
        can distinguish from 0.0, not an artefact of an unbounded
        quantity meeting a chosen budget.
      * IT CAN DIFFER BETWEEN RUNS.  Two runs whose compactions destroy
        different amounts of the derivation get different terms, and a
        run that never compacts gets a_hold = 0 and no crossing — a
        prediction that follows the record, not a constant (the
        battery's arm-discrimination part fails if this stops being
        true).  With ONE memory regime (this experiment's arms A and B
        both run the naive one) the two arms are separated by the
        ARRIVAL axis — the monitoring paragraph fills the window sooner,
        so B's event lands at an earlier turn and crosses earlier;
        `prediction_separation` is the function that says whether a
        given pair is separated at all, and states it plainly when it is
        not.

    WHAT SATURATES, STATED (the brief asks for it).  The term cannot
    exceed 1.0 because there are only `N_SEED_STEPS` steps to lose — an
    INSTRUMENT ceiling, not a map artefact.  MEASURED at the frozen
    parameters, the model's own crossing threshold sits at
    a_hold ~ 0.28, so with a four-step derivation the term separates the
    arms into: LOSS <= 0.25 (0..1 step) -> NO crossing in a 4000 tau_a
    horizon; LOSS >= 0.5 (2..4 steps) -> a crossing, at the event's own
    turn plus the model's own lag.  That granularity is the SEED's; a
    finer instrument (character-level survival of the derivation) would
    refine it and is NOT built here — stated as a gap rather than
    smoothed over.  Within the crossing regime, differences of loss map
    to different crossing turns (0.5 -> 169.5, 0.75 -> 124.4,
    1.0 -> 107.7 tau_a from arrival; the battery asserts monotonicity)
    and the arrival turn shifts the crossing one-for-one (a loss of 1.0
    arriving at turn 3 -> 107.7, at turn 300 -> 427.7), which is what
    makes the prediction follow the run's own record instead of a
    constant.

    ORDINAL CAVEAT (carried in every record): the model's `a_hold` is a
    continuous attention variable, this is a step share over four
    measured steps; shapes and orderings, never values.
    """
    return min(1.0, max(0.0, float(loss)))


def turns_to_windows(turn: float, tau_S: float) -> int:
    """A turn index -> the WINDOW it falls in (1-based): windows are
    consolidation windows of `tau_S` turns.  Turn 100 with tau_S=100 is
    IN window 1 (window k covers turns (k-1)*tau_S + 1 .. k*tau_S) —
    the convention stated once, used everywhere."""
    tau = float(tau_S)
    if tau <= 0:
        raise ValueError(f"tau_S must be positive; got {tau!r}")
    if turn <= 0:
        return 1
    return int((float(turn) - 1e-9) // tau) + 1


# ==========================================================================
# THE PREDICTION
# ==========================================================================

@dataclass(frozen=True)
class CrossingPrediction:
    """The model's prediction, with its provenance."""
    loss: float                     # the STANDING loss of the last event
    a_hold_max: float               # the term's peak level (the mapped hold)
    events: tuple                   # ((turn, loss), ...) the schedule held
    crossing_t: float | None        # model time (tau_a) of G < G_FLOOR
    crossing_turn: int | None       # the same in turn units (F4)
    crossing_window: int | None     # the consolidation window of the turn
    horizon_t: float                # the integration horizon used
    g_end: float                    # G at the horizon (the no-cross case)
    floor: float = G_FLOOR

    @property
    def n_events(self) -> int:
        return len(self.events)


def _loss_schedule(events, horizon_t: float) -> tuple:
    """The step function the events dictate: for each event, the span
    `(t_event, t_next_or_horizon, mapped level)`; the level BEFORE the
    first event is 0 (nothing has been destroyed yet), and an event that
    RECOVERS the derivation (a summary that quotes it back — measured,
    not assumed impossible) simply ends the previous span at that turn.
    Returns (spans, peak_level)."""
    evs = sorted((float(t), loss_to_a_hold(l)) for t, l in events)
    spans, peak = [], 0.0
    for i, (t0, level) in enumerate(evs):
        t1 = evs[i + 1][0] if i + 1 < len(evs) else float(horizon_t)
        peak = max(peak, level)
        if level > 0.0 and t1 > t0:
            spans.append((t0, t1, level))
    return spans, peak


def predict_crossing_from_events(events, *, tau_S: float = 100.0,
                                 horizon_t: float = 4000.0,
                                 params: Params | None = None) \
        -> CrossingPrediction:
    """Integrate the frozen ODE under the schedule THE COMPACTION EVENTS
    dictate and return the model's crossing prediction.

    THE SIGNATURE IS THE GUARD: it takes the measured loss EVENTS and
    nothing else — no coverage, no outward level, no run, no runner.  An
    agent outcome cannot enter the plant through this seam because it is
    not reachable from here.

    INTEGRATION: the frozen model's own driver (`dpdr.integrate.simulate`,
    RK45/LSODA, the segmented solve_ivp the whole tree's numbers come
    from) — never a re-implementation.  The crossing is read with the
    metrics module's own `first_below` at G_FLOOR.
    """
    from dpdr.integrate import simulate
    from dpdr.metrics import first_below

    p = params if params is not None else Params()
    evs = sorted((int(t), float(l)) for t, l in (events or ()))
    spans, peak = _loss_schedule(evs, float(horizon_t))
    sch = Schedule(channels={
        "a_hold": spans,
        "A": [(0.0, float(horizon_t), 0.0)],
        "u_ext": [(0.0, float(horizon_t), 0.0)],
    })
    sol = simulate(p, sch, float(horizon_t))
    g = np.asarray(sol["G"])
    t = np.asarray(sol["t"])
    cross = first_below(g, t, thresh=G_FLOOR)
    crossing_t = float(cross) if cross is not None else None
    crossing_turn = (int(round(crossing_t)) if crossing_t is not None
                     else None)
    crossing_window = (turns_to_windows(crossing_turn, tau_S)
                       if crossing_turn is not None else None)
    return CrossingPrediction(
        loss=(evs[-1][1] if evs else 0.0), a_hold_max=peak,
        events=tuple(evs), crossing_t=crossing_t,
        crossing_turn=crossing_turn, crossing_window=crossing_window,
        horizon_t=float(horizon_t), g_end=float(g[-1]))


def predict_crossing(loss: float, *, arrival_turn: int = 0,
                     tau_S: float = 100.0, horizon_t: float = 4000.0,
                     params: Params | None = None) -> CrossingPrediction:
    """ONE loss at ONE arrival turn — the prediction table's own cell,
    and the special case of `predict_crossing_from_events` (which is
    where the construction lives; this is not a second implementation).

    CONVENTION, stated: `arrival_turn=0` means the loss is present from
    the integration's start (the level axis of the table — the same
    schedule the retired constant-term map produced); a REAL event's
    arrival turn is its compaction turn, and the model crosses LATER
    then, because the plant has to move first (the arrival axis).
    """
    return predict_crossing_from_events(
        [(int(arrival_turn), float(loss))], tau_S=tau_S,
        horizon_t=horizon_t, params=params)


def prediction_separation(pred_a: CrossingPrediction,
                          pred_b: CrossingPrediction) -> dict:
    """CAN THE MODEL'S PREDICTION TELL TWO RUNS APART — and when it
    cannot, SAY SO.

    THE DISCIPLINE THIS CARRIES (a prediction that cannot differ between
    the compared arms is the defect).  With ONE memory regime — this
    experiment's arms A and B both run the stated naive summarization —
    the arms can be separated by nothing but their own measured
    compaction records, and the axis that carries them is ARRIVAL: the
    monitoring paragraph rides every turn's prompt, B's transcript fills
    the window sooner, its event lands at an EARLIER turn, and the
    crossing follows that turn plus the model's fixed lag.

    WHAT IT DOES NOT DO: it does not label the arms, does not read the
    outward level, the floor or any run (its arguments are two
    predictions), and it does not manufacture a difference.  When the
    records coincide, or when a differing record still maps to the same
    crossing window, the result is `separated=False` with a note that
    says which of the two it is — the seed's four-step granularity is
    the stated reason a small arrival shift can move no window boundary.

    Returns whether the two predicted WINDOWS differ (the DV's own
    unit), the finer crossing-turn reading, the axis that differs,
    whether the measured EVENT RECORDS are identical, and the note."""
    wa, wb = pred_a.crossing_window, pred_b.crossing_window
    ta, tb = pred_a.crossing_t, pred_b.crossing_t
    same_events = tuple(pred_a.events) == tuple(pred_b.events)
    # SEPARATION IS READ IN THE DV'S OWN UNIT — windows to collapse.  A
    # pair whose crossing TURNS differ inside one window is NOT called
    # separated in windows (the DV could not read it) and is not called
    # identical either: the finer reading is returned beside it.
    separated = wa != wb
    turns_differ = ta != tb
    turns_a = tuple(int(t) for t, _l in pred_a.events)
    turns_b = tuple(int(t) for t, _l in pred_b.events)
    if turns_a != turns_b:
        axis = "arrival"
    elif not same_events:
        axis = "level"
    else:
        axis = "none"
    if separated:
        note = (f"SEPARATED on the {axis} axis: predicted window {wa} vs "
                f"{wb} (crossing turn {ta} vs {tb})")
    elif wa is None and wb is None:
        note = ("NEITHER run is predicted to cross inside its horizon "
                "(no event reached the model's own threshold, or there "
                "were no events): the construction cannot separate them "
                "on this record, and says so rather than reporting a "
                "difference it does not carry")
    elif same_events:
        note = ("the two runs' MEASURED event records are IDENTICAL, so "
                "the prediction CANNOT separate them and does not claim "
                "to: with one memory regime the arms are carried by "
                "their own compaction records alone, and a pair whose "
                "records coincide is reported as UNSEPARATED")
    else:
        finer = (f"  The crossing TURN does differ ({ta} vs {tb}), a "
                 f"finer reading than the DV's windows — reported and not "
                 f"promoted to a window difference."
                 if turns_differ else
                 "  The crossing turn coincides too.")
        note = (f"the measured event records DIFFER (turns {turns_a} vs "
                f"{turns_b}) but the predicted WINDOW does not: both "
                f"predict window {wa}.  Reported as UNSEPARATED in the "
                f"DV's own unit, not dressed in a difference the DV "
                f"cannot read — the derivation loss is quantised by the "
                f"seed's {N_SEED_STEPS} steps and a small arrival shift "
                f"moves no window boundary.{finer}")
    return {
        "separated": bool(separated),
        "crossing_t_differs": bool(turns_differ),
        "axis": axis,
        "windows": [wa, wb],
        "crossing_t": [ta, tb],
        "same_events": bool(same_events),
        "events": [list(pred_a.events), list(pred_b.events)],
        "note": note,
    }


def model_floor_curve(params: Params | None = None,
                      horizon_t: float = 4000.0,
                      losses=(0.0, 0.25, 0.5, 0.75, 1.0),
                      arrival_turn: int = 0) -> list:
    """THE SENSITIVITY TABLE the pre-registration reports: the model's
    crossing turn as a function of the measured derivation loss, at the
    frozen parameters.  This is the PREDICTION-SIDE table — it makes the
    prediction falsifiable at more than one operating point without a
    live run (every row is pure ODE arithmetic; the battery checks the
    table is MONOTONE: a larger loss crosses no later — the model's own
    ordering, a falsifiable property of this mapping), and it shows the
    RANGE that separates the arms (which losses cross at all).

    The default axis is the derivation's OWN granularity with a
    four-step seed: 0, 1/4, 2/4, 3/4, 4/4."""
    return [predict_crossing(l, arrival_turn=arrival_turn,
                             horizon_t=horizon_t, params=params)
            for l in losses]
