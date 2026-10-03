"""Plots: figure builders for plan §5 (f01-f08 series).

Each builder takes a Solution dict (or sweep table) and writes a PNG to
figs/.  Only the builders needed by Steps A-B are fully exercised here; the
sweep-figure builders (sweep_heatmap, bifurcation_diagram, rescue_map) are
used by the Step C experiment drivers.
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIGDIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "figs")

PANELS = ["a", "G", "D", "S", "c", "E", "g", "u_loop", "Theta_eff"]


def _span_labels(ax, spans):
    for (t0, t1, col, lab) in spans:
        ax.axvspan(t0, t1, color=col, alpha=0.15,
                   label=lab if ax is None else None)


def time_series(name, sol, spans=(), path=None):
    """f01/f02/f08-style 3x3 grid of all state and algebraic variables."""
    os.makedirs(FIGDIR, exist_ok=True)
    path = path or os.path.join(FIGDIR, f"{name}.png")
    fig, axs = plt.subplots(3, 3, figsize=(13, 8), sharex=True)
    for ax, lab in zip(axs.flat, PANELS):
        ax.plot(sol["t"], sol[lab], lw=0.8)
        ax.set_ylabel(lab)
        for (t0, t1, col, leg) in spans:
            ax.axvspan(t0, t1, color=col, alpha=0.15)
        if spans:
            from matplotlib.patches import Patch
            ax.legend(handles=[Patch(color=c, alpha=0.3, label=l)
                               for (_t0, _t1, c, l) in spans],
                      fontsize=6, loc="best")
    fig.suptitle(name)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def phase_diagram(name, sol, nullclines=None, path=None):
    """f03: G x E plane, trajectory colored by c."""
    os.makedirs(FIGDIR, exist_ok=True)
    path = path or os.path.join(FIGDIR, f"{name}.png")
    fig, ax = plt.subplots(figsize=(7, 6))
    s = ax.scatter(sol["G"], sol["E"], c=sol["c"], s=2, cmap="coolwarm")
    ax.plot(sol["G"][::50], sol["E"][::50], lw=0.3, color="k", alpha=0.3)
    fig.colorbar(s, ax=ax, label="c")
    ax.set_xlabel("G"); ax.set_ylabel("E")
    ax.set_title(name)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return path


def sweep_heatmap(name, table, xkey, ykey, value="regime", path=None,
                  regime_names=None):
    """f04/f06-style heatmap over a 2-param grid (needs the sweep table plus
    the grid axes; xkey/ykey index into the grid values)."""
    os.makedirs(FIGDIR, exist_ok=True)
    path = path or os.path.join(FIGDIR, f"{name}.png")
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(table[value].reshape(len(ykey), len(xkey)),
                   origin="lower", aspect="auto",
                   extent=[min(xkey), max(xkey), min(ykey), max(ykey)],
                   interpolation="nearest")
    fig.colorbar(im, ax=ax, label=value)
    ax.set_title(name)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return path


def bifurcation_diagram(name, xvals, G_end, T_stuck=None, xlabel="",
                        path=None):
    """f05: final G (and optionally T_stuck, twin axis) vs a swept parameter."""
    os.makedirs(FIGDIR, exist_ok=True)
    path = path or os.path.join(FIGDIR, f"{name}.png")
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(xvals, G_end, "o-", ms=3)
    ax.set_xlabel(xlabel); ax.set_ylabel("G(T)")
    if T_stuck is not None:
        ax2 = ax.twinx()
        ax2.plot(xvals, T_stuck, "s--", ms=3, color="tab:orange", alpha=0.7)
        ax2.set_ylabel("T_stuck", color="tab:orange")
    ax.set_title(name)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return path


def postrecovery(name, sol, t0, path=None):
    """f07: E(t) after rescue + g(t) overlay (overshoot -> retune)."""
    os.makedirs(FIGDIR, exist_ok=True)
    path = path or os.path.join(FIGDIR, f"{name}.png")
    w = sol["t"] >= t0
    fig, axs = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    axs[0].plot(sol["t"][w], sol["E"][w], lw=0.8)
    axs[0].axhline(0, color="k", lw=0.5)
    axs[0].set_ylabel("E")
    axs[1].plot(sol["t"][w], sol["g"][w], lw=0.8, color="tab:green")
    axs[1].set_ylabel("g"); axs[1].set_xlabel("t")
    fig.suptitle(name)
    fig.tight_layout(); fig.savefig(path, dpi=110); plt.close(fig)
    return path


def rescue_map(name, table, xkey, ykey, path=None):
    """f06: (timing x strength) -> {full recovery, relapse, failure} 3-color."""
    return sweep_heatmap(name, table, xkey, ykey, value="regime", path=path)
