"""Sweep: grid parameter sweeps with multiprocessing and .npz caching.

A sweep runs `simulate` over a grid of parameter overrides against one fixed
schedule, summarizes each run via metrics.summarize, and caches the result
table in cache/<hash>.npz keyed by (grid, schedule, T).  Deterministic; no
seeds involved (the model is deterministic — noise is a Step-E variant).
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, replace
from multiprocessing import Pool

import numpy as np

from .integrate import simulate
from .metrics import REGIME_CODES, summarize
from .model import Params, Schedule

CACHEDIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "cache")

FIELDS = ["G_end", "D_end", "S_end", "g_end", "E_end", "c_end",
          "Theta_eff_end", "u_loop_end", "G_min", "c_max", "t_collapse",
          "t_recover", "T_stuck", "relapsed", "t_relapse", "regime",
          "collapsed_at", "nfev"]


def run_case(job):
    """One sweep cell (top-level for Pool): (overrides, schedule, T)."""
    ov, sched, T = job
    p = replace(Params(), **ov)
    sol = simulate(p, sched, T)
    return summarize(sol, p)


def _hash(base: Params, grid: dict, sched: Schedule, T: float) -> str:
    payload = json.dumps(dict(base=asdict(base), grid=grid,
                              sched=sched.channels, T=T), sort_keys=True,
                         default=str)
    return hashlib.sha1(payload.encode()).hexdigest()[:16]


def _to_rec(rows: list) -> np.ndarray:
    arr = np.zeros(len(rows), dtype=[(f, "f8") for f in FIELDS])
    for i, r in enumerate(rows):
        for f in FIELDS:
            arr[f][i] = r[f]
    return arr


def sweep(base: Params | None = None, grid: dict = None, sched: Schedule = None,
          T: float = 1200.0, nproc: int | None = None,
          use_cache: bool = True) -> dict:
    """Sweep over a grid {param_name: [values]} (Cartesian product).

    Returns dict(grid=..., values={key: np.array}, table=record array,
    hash=...).  Cells are independent; results cached across runs.
    """
    base = base if base is not None else Params()
    grid = grid or {}
    sched = sched if sched is not None else Schedule()
    h = _hash(base, grid, sched, T)
    os.makedirs(CACHEDIR, exist_ok=True)
    path = os.path.join(CACHEDIR, f"sweep-{h}.npz")
    if use_cache and os.path.exists(path):
        z = np.load(path)
        return dict(grid=grid, table=z["table"], hash=h, cached=True)

    keys = list(grid)
    combos = [dict(zip(keys, v))
              for v in np.array(np.meshgrid(*[grid[k] for k in keys],
                                            indexing="ij")).reshape(
                                              len(keys), -1).T] \
        if keys else [{}]
    jobs = [(ov, sched, T) for ov in combos]
    if len(jobs) > 1 and nproc != 1:
        with Pool(nproc) as pool:
            rows = pool.map(run_case, jobs)
    else:
        rows = [run_case(j) for j in jobs]

    table = _to_rec(rows)
    if use_cache:
        np.savez(path, table=table)
    return dict(grid=grid, table=table, hash=h, cached=False)
