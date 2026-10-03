# Self-Application Is Not Free — paper 3's deposit

**Paper 3 of three: the model applied to a self-referential substrate (a measurement rig)
and to a working agent, unified.**

> *Self-Application Is Not Free: the Monitoring Channel Is Part of the Failure Channel,
> and the Self Does Not Survive Its Own Reconstruction*

**Published: [doi:10.5281/zenodo.23128114](https://doi.org/10.5281/zenodo.23128114)**
(concept DOI [10.5281/zenodo.23128113](https://doi.org/10.5281/zenodo.23128113), which always
resolves to the latest version) — cite the paper by the concept DOI.

This repository is paper 3's **evidence deposit**: the unified paper, the methods half it
folds in, the worker's code, the pre-registration, the held-out task suite, and the run
data from which every headline number is re-derivable. It is one of three public artifacts.

| | |
|---|---|
| **the model** | the five-state control model of self-regulation ([published](https://doi.org/10.5281/zenodo.22943642)) |
| **the mechanism** | the model applied to a self-referential substrate, in a measurement rig — paper 2's content, folded here as the methods half |
| **the worker** | **this repository** — the unified paper: the rig's cost finding + the worker's self-loss finding + the honest work-score null — *paper 3* ([doi:10.5281/zenodo.23128114](https://doi.org/10.5281/zenodo.23128114)) |

## What is here

| path | what it is |
|---|---|
| `paper-3.md` | the paper (markdown — the source of truth) |
| `paper-3.pdf` | the paper rendered to PDF: `pandoc paper-3.md --pdf-engine=typst -o paper-3.pdf` |
| `paper2/` | the methods half's record — `paper-2-results-record.md` (R1–R6, the measurements the methods half rests on), `future-work-axis-hunt.md` (a falsified predictor, kept as the record), `cult-induction-lit.md` (the coercive-induction literature note the paper's boundary section cites) |
| `agent/` | the worker's code: `lh_agent.py`, `task_eval.py`, `harness.py`, the CEN, the boundary, the memory codecs, the stage-2 batteries, and `tasks/` (the 12-task suite with visible `tests/` and sealed `heldout/` tests) |
| `ops/` | the rig's instruments: `density_test.py`, `generalization_screen.py`, `ladder_defs.py`, `check_tracked_set.sh`, and `ops/lambda/P3-PREREG.md` (the pre-registration, cited twice by the paper) |
| `runs/` | the run data — for each cited run set: `campaign.json`, `state/` (.tsv), per-cell `evaluation.json`, `cell-*/runs/*.json` (summaries), `cell-*/rows/*.jsonl` (per-turn rows), `logs/*.rc` (exit codes). No `pinned/`, no `*.out`/`*.log`, no tunnels, no `*.tmp`. |
| `dpdr/` | the frozen five-state model package, at the revision the agent build imports (paper 1's deposit is the model's canonical home; it predates the opt-in variants — `consolidation`, `p2_backlog`, `values`, `composed*` — that this deposit carries) |
| `dlb/` | the datalog-dafsa engine binding, needed by the CEN's `engine=real` path (the engine's own repository is `fixpoint-linux/datalog-dafsa`) |
| `held-out-task-suite.json` | the sealed held-out task suite definition (the v2 definition covering all 12 tasks) |
| `README.md`, `LICENSE`, `LICENSE-paper` | this file and the licences |
| `SNAPSHOT` | the revision of the working tree this deposit was taken from — the pin |

**Not included, by design:** the held methods-half *draft* (`paper-2-draft.md`, whose full description of the rig's components lives on), the *design record* for an unbuilt experiment (`load-bearing-self-design.md`), and the agent's internal *design record* (the constraint set and the
open design decisions behind the long-horizon build) is **not part of this deposit** — it is the
product's design record rather than this paper's evidence, and several comments and the methods
draft refer to it by path. The paper's own claims do not depend on it: each cites shipped code or
a shipped run.

## How to run it

The shipped code imports as packages, so the deposit root, the agent directory and the model
package go on the path (the exact line used to verify this deposit):

```sh
cd <deposit>
PYTHONPATH="$PWD:$PWD/agent:$PWD/dpdr" python -c "import lh_agent, task_eval, cen_real_engine"
```

A cell is one `lh_agent.py --mode run` invocation (see `ops/lambda/P3-PREREG.md` §5 for the
pre-registered argv and `runs/*/campaign.json` for the exact per-set configuration). The
batteries that verify the shipped modules are under `agent/` (`stage2_intagent_tests.py`,
`stage2_taskeval_tests.py`); run them with the same `PYTHONPATH`.

## The held-out task suite

The paper's evaluator is **sealed against a held-out task suite** whose definition lives at
`held-out-task-suite.json` (the v2 definition covering all 12 tasks). Each task's
`agent/tasks/<task>/heldout/` directory contains the held-out tests themselves. **These are
included so a reader can re-run the evaluator.** A public deposit that includes them is normal
and correct: a reader is not the agent under test, and the paper's design depends on the *agent*
not reading them, not on a public reader not reading them. The README-as-requirement design
(visible suites the agent can run, held-out suites it cannot read) is enforced at runtime by the
boundary, not by withholding the tests from the deposit.

## Where the headline numbers live

Every headline number is re-derivable from `runs/` alone:

| quantity | where in `runs/` |
|---|---|
| empty-self fraction (1.000 in every D1 cell) | `p3-set/*/cell-*/runs/*.json` → `reconstruction_outcomes` / `survival_pair_events` |
| reconstruction calls/cell (184 + 258) | `p3-set/*/cell-*/runs/*.json` → `reconstruction_cost_series` |
| self-directed thinking chars (medians ~400k) | `p3-set/*/cell-*/runs/*.json` → `reconstruction_cost_series[].thinking_chars` |
| thinking:returned ratio (21.2x / 20.5x) | same series, `thinking_chars` vs `returned_chars` medians |
| the DV (ordinal work score 0–12) | `p3-set/*/evaluation.json` → `dv` / `contrast_d1_d0` |
| the finer held-out DV (set 2) | `p3-set2/*/evaluation.json` → `dv` (held-out pass fraction) |
| the 3,123-row fold (1,358 + 1,765) | `p3-set/` + `p3-set2/` per-cell `rows/*.jsonl` |
| the fold signature (present-in-full or absent-entirely) | same rows, `self_steps` / `compaction` columns |
| cell exit codes (the two dead cells) | `p3-set/logs/*.rc`, `p3-set2/logs/*.rc` |
| the pre-fix smoke (D1 dies at first compaction) | `p3-span-smoke/*/cell-*/rows/*.jsonl` |
| the route check (two routes to self-loss) | `p3-d1check/*/cell-*/runs/*.json` |
| the cost probe | `p3-cost-probe/*/cell-*/runs/*.json` |
| the rig's R1–R6 (lambda-official, audit-rec, nocrutch, choice-go) | the matching `runs/<set>/` |

## What is deliberately NOT here, and why

- **`pinned/`** — the per-set code snapshots, redundant with `agent/` (~3.5 MB each).
- **`logs/*.out` and `logs/*.log`** — the raw stdout and tunnel logs (large, not re-analyzable;
  the `*.rc` exit-code files are kept, as they are tiny and record each cell's exit code).
- **The paper's process notes** — `report/`, `staged-report.md`, `practical.md`,
  `reference/transcripts/` (raw first-person source material). None of these are in the deposit.

## This deposit is DERIVED — do not hand-edit it

Every file here is materialised from a private working tree. Edit a file here and the next sync
overwrites it: the working tree is the source. But this repository is a **snapshot taken at a
stated revision** of that tree, not a live mirror of it. The revision is recorded in
[`SNAPSHOT`](SNAPSHOT) at the root.

## Licence

MIT — see `LICENSE`. The paper (`paper-3.md`, `paper-3.pdf`) and the companion records under
`paper2/` are [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) — see `LICENSE-paper`,
the same split paper 1's deposit uses.
