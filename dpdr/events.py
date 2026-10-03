"""Events: builders for piecewise-constant exogenous schedules (plan §2).

Each builder returns a Schedule (piecewise-constant channels + breakpoint
list).  Integration is segmented at every breakpoint so the RHS stays smooth
within each segment (plan §3).
"""
from __future__ import annotations

from .model import Schedule


def baseline_schedule() -> Schedule:
    """No episode, no affect, no external demand."""
    return Schedule()


def inward_episode(t0: float = 100.0, t1: float = 200.0,
                   intensity: float = 0.9) -> Schedule:
    """Inward-attention hold (the trigger)."""
    return Schedule({"a_hold": [(t0, t1, intensity)]})


def affect_pulse(base: Schedule, t0: float, dur: float, amp: float) -> Schedule:
    """Add a strong-affect pulse feeding D on top of an existing schedule."""
    ch = dict(base.channels)
    ch["A"] = [(t0, t0 + dur, amp)]
    return Schedule(ch)


def external_demand(base: Schedule, t0: float, dur: float,
                    level: float) -> Schedule:
    """Add an external-demand span (the rescue) on top of an existing schedule."""
    ch = dict(base.channels)
    ch["u_ext"] = [(t0, t0 + dur, level)]
    return Schedule(ch)


def failure_schedule(a_hold: float = 0.9, t0: float = 100.0, t1: float = 200.0,
                     pulse: float = 0.5, pulse_end: float = 160.0) -> Schedule:
    """Standard failure scenario: inward episode + affect pulse (§3 scenario
    block: a_hold 0.9 for 100 tau_a, affect amp 0.5)."""
    s = inward_episode(t0, t1, a_hold)
    return affect_pulse(s, t0, pulse_end - t0, pulse)


def rescue_schedule(a_hold: float = 0.9, ep_t0: float = 100.0,
                    ep_t1: float = 200.0, pulse: float = 0.5,
                    pulse_end: float = 160.0, u_ext: float = 0.8,
                    rescue_t0: float = 800.0, rescue_dur: float = 200.0
                    ) -> Schedule:
    """Standard rescue scenario: failure schedule + u_ext 0.8 for 200 tau_a at
    t_rescue = 800 (§3 scenario block)."""
    s = failure_schedule(a_hold, ep_t0, ep_t1, pulse, pulse_end)
    return external_demand(s, rescue_t0, rescue_dur, u_ext)
