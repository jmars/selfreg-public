"""dpdr package — control-theoretic self-regulation model (Step B extraction).

Modules mirror plan §2: model (Params + RHS), events (schedule builders),
integrate (segmented solve_ivp), metrics (regime classification, gate checks),
sweep (grid sweeps), plots (figure builders).
"""
from .model import Params, Schedule, cannibalization, deriv
from .integrate import simulate
from .metrics import classify, check_gates

__all__ = ["Params", "Schedule", "cannibalization", "deriv", "simulate",
           "classify", "check_gates"]
