# Paper 3 — pre-registration: the worker experiment

**Status: PRE-REGISTERED BEFORE THE FIRST LIVE RUN.** Written 2026-09-30. No cell of this set has
run; the runner has never been executed with `surface=True` live (§D's gates exist for exactly
that reason). Every per-arm prediction below is **PROJECTION** until a run lands.

**Provenance.** The design: `paper2/paper-3-scope.md` §4. The plan: memory node
`handoff-p3-runplan` (which supersedes `handoff-p3-plan`). The audit the plan rests on and the
four inherited defects it closed: `handoff-p3-fix-result`, commit `fef4101`. Paper 2's
measurements, which fold in as this paper's methods half: `paper2/paper-2-results-record.md`
(R1–R6).

---

## 1. The claim

> **With a task and real tools, the monitoring channel is pathogenic while the agent works: the
> same self-depletion that drove the plant's collapse in paper 2 degrades the agent's own task
> performance, and the degradation is attributable to the channel — not to the plant coupling
> through which paper 2 measured it. The rescue must still come from outside.**

**PROJECTION.** Stated so that it can fail.

---

## 2. The arms

All three run the **same loop**: agent + task + tools, **plant edge severed** (the empty
schedule; `drive_seat=False`, `couple_backlog=False`, the plant's floor `None`). Nothing the
agent emits can move `G` — asserted structurally by battery I8 (bit-identical plant trajectories
across arms whose agents differ). That severance is the point: **the plant cannot explain any
task-side effect.**

| arm | seat | monitoring | inject regime | what it is |
|---|---|---|---|---|
| **D0** | **off** (`grounding=False`) | off | `inject` | the no-depletion reference on the task axis — no derivation, no retrieval seat, no seed |
| **D1′** | on | **on** | **`inject`** | **the carrier control**: the paragraph's context cost, with the derivation restored every compaction so nothing is ever lost |
| **D1** | on | **on** | **`reconstruct`** | **the claim's arm**: the derivation is seeded once and the agent reconstructs it after each compaction, so it can be lost |

**The contrasts, and what each licenses:**

| contrast | reads | licenses |
|---|---|---|
| **D1 − D0** | the worker claim: does having-and-losing a self degrade the work? | the paper's claim, if negative and mediator-coupled |
| **D1 − D1′** | depletion's **marginal** cost: same paragraph, same seat — the ONLY difference is whether the derivation is restorable | the depletion attribution, clean of the carrier |
| **D1′ − D0** | the **carrier** cost alone (R1's measured effect, now on the task axis) | paper 2's §8.1 consequence, transferred |

**D2/D3 (paper 2's drive arms) are NOT built and NOT runnable**: they need the `a_hold`-coupled
rig, which was **superseded** (it collapsed the plant by construction — the tree's own
non-self-referential control collapsed it identically, `G_end 0.2903` vs `0.2905`). Recorded so
the absence is a decision, not an oversight.

**Regime held constant in every arm:** naive summarization (the engineered priced memory is the
*following* product claim, and it is a protection — it would mask the effect); regulator `none`;
the six harness arms are untouched and are not part of this set.

---

## 3. The DV, and the mediator

**PRIMARY DV: `swe_final_score`** — the external evaluator's typed verdict per target
(`USEFUL` / `TASK_COMPLETE_ONLY` / `NOT_COMPLETE`, i.e. visible-PASS-and-held-out-PASS, or
visible-only, or neither), summed to **0..6** per cell over three targets × two repeats.

**Why the ordinal, not an event time.** It does not censor: a partially-completed task still
scores, where time-to-first-PASS discards that information. **CO-PRIMARY (recorded, not gating):**
`turns_to_first_PASS`.

**The DV passes the R6 position rule BY CONSTRUCTION.** R6 (paper 2) voided a DV because the
agent chose the first-rendered option 135/135 — render order decided it. This DV cannot work that
way: completion is adjudicated by the **world**, gated by the **evaluator**, and the held-out
suite is unreadable by the mechanism. Naming this here is the pre-registration's own check.

**MEDIATOR — the uncoupled pair only:**
- `compaction_gap_turns` (the cadence — R1's own measured carrier, +0.625 turns, p=0.0016), and
- the `CompactionEvent` survival pair (`self_steps_before` / `self_steps_after`).

**`self_steps` is recorded but is NOT a licensable mediator.** Paper 2's R5 proved it measures the
harness's own prompt (with the MY STATE block removed the agent recovered **0 of 4** steps while
writing **more** text). The which-claim-may-read-which rule is in code
(`agent/lh_agent.py:1369-1392`).

**THE CLAIM THIS LICENSES, STATED AT ITS REAL SIZE:** the licensable form is a
**resource-and-event** claim — *the work degrades as the self's grounds are consumed, and the
consumption is measured by the memory's own compaction events*. It is **not** a carrier-self
claim, because no uncoupled instrument for that exists on this substrate. Paper 2's rule names
what would be needed: a sensor in the subsystem that survives, or outside the system entirely.

---

## 4. The prediction, and the falsifiers

**Prediction:** **D1's `swe_final_score` is strictly worse than D0's**, and the degradation
co-moves with the uncoupled mediator within D1.

**Falsifiers — each a result if it fires:**

| # | outcome | reading |
|---|---|---|
| **F1** | **D1 ≈ D0** | the channel is not pathogenic to the *work*. **Split by D1′:** if D1′ ≈ D0 too, the suite had no headroom (**headroom-null** — F7's instrument failure); if D1′ > D0, the carrier cost is real and the *depletion* leg is absent (**true-null**). Two distinct publishable lines. |
| **F2** | D1 healthy while a plant-coupled arm collapses | **paper 3 would be paper 2 in costume.** Not runnable (D2/D3 unconstructible); if a future rig supplies it, report as a failure of separation, never as support. |
| **F3** | the score moves with budget/cap rather than with depletion | the instrument trap — measuring the budget, not the phenomenon. **VOID, not a result.** |
| **F4** | the evaluator is self-authored or **readable** by the mechanism | self-authored half is closed (sealed sha256 manifest, refuses on mismatch). **The READ half is open by design** (residual R-a: the criterion and held-out definition stay mechanism-readable so the mechanism can route on one and be scored by the other). Carried as a **pre-registered weakening** with a post-run grep gate. |
| **F5** | a clone set | any identical pair among the cells (the run 3 defect). The independence check gates the DV read. |
| **F6** | `derivation_loss` identically zero in D1 | the fix did not take — the run is **VOID** and says so (campaign 3's defect, re-armed). |
| **F7** | the suite is at ceiling or floor | **the run-killer** (audit row 9): if every arm scores 6/6 or 0/6 the DV cannot degrade, and the answer is **harder tasks, not more cells**. |
| **F8** | the task never opens | no `run_tests`, no `complete`, or the world refused everything — an obedience limit read as a null. |
| **F9** | the runner/launcher mismatch | the launcher drives the wrong runner or cannot see these arms (§5). |
| **F10** | an unthreaded per-turn timeout | a hung turn is unbounded (there is no `--timeout` on the loop today). |
| **F11** | smoke→full-set carryover | smoke artifacts resuming into the deciding set as if measured. |

---

## 5. The run

**Runner:** `agent/lh_agent.py`, `--mode run --arms "D0,D1',D1"`, `surface=True` (the task and
tool surface live), `--turns 60`.

**60 turns is a MEASURED choice, not a default:** live long-horizon cells died at 34–58 turns
with 3–6 compactions and inter-compaction gaps of 9–11 turns. 60 turns gives ~5 compactions per
cell, which the cadence mediator needs, and stays inside the observed survival envelope.

**Model:** `qwen3.5:9b` on a rented A10 (the substrate the precondition was measured on; sign
RISES, +0.031 — the smallest of the three risers, stated as a real risk to separation).
**Seeds:** per-cell, launcher-assigned, pairwise distinct (the stride rule).

**Cells:** 3 arms × 8 cells = **24**.

**Cost:** ~65 s/turn (re-read from the live rows, correcting an earlier 90 s estimate) → 24 cells
× 60 turns × 65 s ≈ **31 GPU-h ≈ $23**, with a hard **cap of $40**.

**THREE INTEGRATION GAPS must be closed before any of this runs** (all verified at the source):
1. `ops/lambda/lh_lambda.sh:339` invokes **`exp_longhorizon.py`**, not `lh_agent.py` — the
   launcher cannot drive the loop at all;
2. its rc/status/collect globs are hardcoded **`[AB]-r*`** (`:355`, `:385`, `:400`) — the arm
   names `D0/D1'/D1` would match nothing and the set would read as empty;
3. **`lh_agent.py` never threads `--timeout`** — the 900 s per-turn bound does not exist on the
   loop, so a hung turn is unbounded.

---

## 6. The smoke, before the set

**6 cells × 20 turns ≈ $2–3.** No live `surface=True` run has ever happened, so this is the first
execution of the whole path. **Eight gates, each able to FAIL — the set does not launch unless
all pass:**

| gate | check |
|---|---|
| **S1** | a cell completes live with `surface=True` |
| **S2** | the tool surface is actually used: ≥3 tool calls and ≥1 `run_tests` |
| **S3** | **the suite OPENS** — the task is neither DOA nor solvable by refusal (F8's in-cell form) |
| **S4** | arms configure as declared — the identity of the live cells matches `P3_ARMS` |
| **S5** | **D1′ losses 0.0 WITH the seed header, D1 nonzero by turn 20** (extend to 30 if no event: **UNDECIDED, not pass**) |
| **S6** | mediator rows land (`compaction_gap_turns`, `self_steps_before/after` present) |
| **S7** | the held-out grep gate — no held-out path appears in any cell's reads |
| **S8** | budget honesty — spend so far is inside the projection |

**F7 is checked here in its in-cell form:** the score must be neither 6/6 nor 0/6 across the
smoke cells.

---

## 7. Analysis, pre-registered

- **Decision rule:** D1 vs D0 on `swe_final_score`, per arm over the **realised** n, with an
  explicit **INSUFFICIENT below 6 valid cells per arm**. A cell that fails a gate is reported,
  not silently dropped.
- **Statistic:** Mann–Whitney U (ordinal DV, small n, no distributional assumption), with the
  per-cell values printed beside any aggregate.
- **The mediator must CO-MOVE, not merely exist:** within D1, a Spearman correlation between the
  uncoupled mediator and the score. A non-moving mediator blocks the *mechanism* reading even if
  the arm contrast is significant — the difference between "the work degraded" and "the work
  degraded *as the self was consumed*".
- **D1 ~ D0 splits by D1′** (headroom-null vs true-null), and each is reported as its own result.

**Before any DV is read:** the **independence** check must PASS (no identical pair among cells —
run 3's defect). A clone set is VOID.

---

## 8. What paper 2 contributes, and where it goes

Paper 2 is **held** by author decision and folds in here as the methods half:

| paper 2 | becomes in paper 3 |
|---|---|
| **R1** the monitoring carrier (+0.625 turns, p=0.0016) | methods, and **D1′'s only quantitative prior** |
| **R2** the instrument validated (the judge can say 0) | methods — for measuring a reconstruction, **never** as the mediator |
| **R3** the saturation (the reading goes to 0 and flattens) | the **motivation** for choosing the survival-pair mediator |
| **R4** no within-window decay | the limits skeleton |
| **R5** the prompt-coupling | the **design rule**: why D0 exists and why the mediator must be uncoupled |
| **R6** render order decided the choice | a check **passed at design time** (§3) |

**Stated plainly, so it is not over-read:** paper 2 has **one positive result and four instrument
findings, and no mechanism result.** Paper 3 rests on R1, those findings, and its own new
measurement.

---

## CORRECTION — 2026-10-01 (post-smoke, pre-set; nothing above is rewritten)

The smoke (6 cells × 20 turns, pin `df620fe`, artifacts `runs/p3-smoke`) exposed
**three defects in the MEASUREMENT layer, none in the science**:

1. **The task-health gate read the wrong instrument.** The loop called paper 2's gate
   (`LH.task_health`), whose instrument is `talking_applied` — the OLD synthetic worksheet's
   ledger, ~0 by construction on the SWE surface. The smoke's `task-health INSUFFICIENT` on all
   six cells was therefore an **instrument artifact, NOT a finding about the agent** (the agents
   made 18–85 tool calls and up to 35 `run_tests` each, zero refusals; f1/f2 completed in two
   cells). Fixed: `surface_task_health` reads the run's own surface (`tools.history` +
   `swe.gate_log`); paper 2's gate is untouched and remains the control surface's instrument.
2. **The DV was never armed.** No sealed held-out definition existed at run time, so the
   evaluator reported `TASK_COMPLETE_ONLY` per target over an UNPINNED held-out — a verdict that
   cannot distinguish "held-out FAILED" from "held-out never pinned". Fixed: the definition is
   now published (v1, digest `8323c5459fab3b0c`); a `surface=True` run now REFUSES before its
   first turn when the pin is absent/unauthentic, and `swe_final_score` runs `require_sealed`.

**Consequence for the smoke's readings:** its **task-side readings are VOID** (the DV verdicts
were unarmed; the task-health gate was the wrong instrument). Its **S5/S6 mediator readings —
`derivation_loss` and `compaction_gap_turns` — stand as MEASURED**: those instruments were
correct and independent of both defects. Per-turn rows now also carry `n_tool_calls` /
`n_run_tests` (cumulative), so smoke gate **S2 is measurable off the row**, not just the summary.

---

## CORRECTION — 2026-10-02 (post-re-smoke, pre-set; nothing above is rewritten)

The re-smoke (6 cells × 20 turns, pin `6f79a4c`, artifacts `runs/p3-smoke2`) ran with
the 2026-10-01 fixes in place. Three readings, one code consequence (stated, not smuggled):

1. **The DV is ARMED and discriminating.** `USEFUL` verdicts appear (MEASURED: D0-r1 and D1-r1
   both `f1:USEFUL, f2:TASK_COMPLETE_ONLY, f3:USEFUL`), so the 9B model CAN do the task and the
   pre-registered `--turns 60` **may stay**.
2. **Task-health read INSUFFICIENT in all 6 cells for a WINDOW reason, not an agent reason.**
   The gate reads only COMPLETE windows and the window was the consolidation constant
   `TAU_S_TURNS = 100` (`stage2_harness.py:231`): a run of `turns` yields `turns // window`
   windows, so 20 turns → 0 — and **the pre-registered 60-turn run also yields 0**
   (`60 // 100 = 0`): the gate could not have fired on the pre-registered design at all, and
   F7's ceiling/floor check would have been UNREADABLE. The window is now a tunable
   (`--task-window`, DEFAULT `TAU_S_TURNS` — behaviour byte-identical when absent; the default
   is asserted unmoved by battery parts V4/V5) recorded in the run identity, summary, plan and
   campaign records. **The horizon is NOT raised**: live cells have died at 34–58 turns, so a
   100+ horizon would gamble the deciding set on the substrate's survival envelope. The window
   moves, never the horizon.
3. **The re-smoke's DV showed NO separation at n=2**, and the deciding set's n must be
   justified against the observed spread (the author's call — NOT changed here):
   **per-cell DV sums D0 = 2.5 / 1.5, D1 = 2.5 / 2.0, D1′ = 1.5 / 0.5** — a 2-point
   within-arm spread (D1′ 0.5↔1.5, D0 1.5↔2.5) at n=2 per arm, while `n_tool_calls` swings
   **18–82** across the six cells (MEASURED off the cells' summaries). A within-arm spread of
   the same order as any between-arm contrast at n=2 is exactly the case §7's INSUFFICIENT rule
   exists for; the 8-cells-per-arm plan should state, against these numbers, what n it needs.

---

## AMENDMENT — 2026-10-05 (pre-set: the task queue, the DV's primary form, and the
mediator's evaluation window; nothing above is rewritten)

**The claim (§1), the arms (§2) and the contrast table are UNCHANGED.** What changes is the
task supply, the DV's primary form, and the mediator's evaluation window — each because a
MEASURED finding showed the pre-registered instrument could not span the thing measured.
The author has chosen AMENDMENT over a new pre-registration for that reason; the change of
the DV's *shape* is flagged here in the amendment's own header.

### A. The task queue (the spanning design)

**The finding that forced it (MEASURED, `runs/p3-smoke2`):** the 3-task suite
decided the DV before the mechanism could act. D0 (seat OFF, no self at all) declared all
three targets PASS by turns 4/10/10 (r1) and 6/6/6 (r2) of a 20-turn run; the last 12 rows of
D0-r1 carry `tools_this_turn=[]` — the work STOPPED while the run continued. Compactions at
t8/t19 kept eating the self with no work left to affect: a guaranteed null, the same class as
paper 2's prompt-supplied self. `--turns 60` alone cannot fix it (work done ~t10, then 50
turns of depletion with nothing to affect).

**The change:** §5's suite is now **a queue of 9 distinct targets** — the three original
tasks (`t1_rchunk`, `t2_histstat`, `t3_netmask`) **kept exactly as they are**, plus six new
ones of the same shape and kind (`t4_celsius`, `t5_rle`, `t6_paren`, `t7_slug`, `t8_roman`,
`t9_luhn`: README-as-requirement, a shipped-broken module, a visible suite, a held-out
suite, a class-(C) specimen under `_specimens/`). The queue is the world's OWN open set at a
larger N — no new mechanism, no new world: `SWETaskUniverse` offers all 9 through its
existing open set, and a target leaves it only on the evaluator's visible-PASS, as before.

**The supply arithmetic (in code at `lh_agent.SWE_QUEUE_TARGETS`):** the MEASURED rate is
~3–10 turns per target; a 60-turn run at the observed mean (~6 turns/target) completes ~10
targets' worth of work but ~9 declared completions, and the spanning requirement — the agent
still DRAWING work past the last compaction (~t48–60) — holds for the observed agent. If the
re-smoke shows the 9B clearing 9 targets inside 30 turns, the fix is MORE TARGETS, never
more cells (**F12**).

### B. The DV (primary form restated; the secondary kept exactly)

**PRIMARY: the declared-completion RATE PER WINDOW** — the world-adjudicated
`swe.gate_log`, read per `--task-window` turns (the pre-registered run: 60 turns, window 20,
3 windows per cell). The pre-registered statistics are the **window-gradient** (rate in the
last window minus rate in window 1, per cell) and the **per-window rate as a repeated
measure**. It can DEGRADE (a run completing 3 targets in window 1 and 0 in window 3 shows
it; the end-sum could not represent this — all arms read 3/3 by t10, the definition of the
row-9 trap), and it is the SAME instrument in every arm by construction (world-adjudicated,
arm-blind).

**SECONDARY (kept exactly as §3 defines it): `swe_final_score`** — the end-of-run artifact
ordinal. It alone carries the class-(C) USEFUL/TASK_COMPLETE_ONLY axis (the paper's subject)
and the competence-without-declaration shape (measured in the re-smoke: D1′-r2 repaired f2
to visible 6/6 and never declared).

**The declared/competent ratio is reported per arm before any depletion reading is drawn
from the rate (F14):** an arm difference that lives only in the DECLARATION rate while the
artifact shows equal competence is an obedience effect, not a work effect.

**`turns_to_first_PASS` is RETIRED as a co-primary (author decision):** under a queue the
first completion is near-guaranteed early in every arm, so it has no discriminating power.
No event-time seat is added in its place.

### C. The mediator (the evaluation window fixed; the licence stated)

**S5 in its pre-registered form is RETIRED — F6 FIRED SPURIOUSLY (MEASURED).** The
pre-registration required "D1′ losses 0.0 WITH the seed header"; the re-smoke read
`derivation_loss` = 1.0 **in D1′** — not because the fix did not take but because the event
pair was read at the FIRST compaction, where `_regenerate_self_block` fires in BOTH
seat-on regimes: that first event's before/after pair is the SEED'S OWN single-turn spend,
not a regime difference. The same defect read `derivation_loss_standing` = 1.0 in D0 (a cell
with no self to lose at all — the instrument had no zero). These were instrument defects,
not leaks and not findings about the arms.

**The replacement (S11):** the survival pair is read **from the SECOND compaction on**,
where the regimes actually diverge (inject re-enters the derivation through the prompt and
survives in the memory's span; reconstruct must produce it and cannot). The re-smoke's own
cells already exhibit this shape at events 2–3 (D1′ before=[1,2,3,4] at every event; D1
before=[] at events 2–4). The event-1 pair is still RECORDED (it is the seed's own spend; a
reader auditing the fix needs to see it fire) — it is simply not a mediator reading.
**S12:** the seat-off arm's standing loss reads 0.0 by construction (no seed was installed;
nothing is standing to lose), restoring the instrument's zero. Per-turn `self_steps` stays
what §3 already says it is: a logged R5-coupled corroborator, never a licensable mediator.

**The cadence's licence is BARRED from the D1-vs-D1′ seat (F13):** under a spanning design
work itself fills the window (tool results, edits, run_tests output all enter the
conversation), so arms that complete MORE work compact FASTER — cadence is partially
DOWNSTREAM of the DV there, and reading it as the depletion mediator would be circular.
`compaction_gap_turns` may be read for the **D1′-vs-D0 carrier comparison only** (R1's
quantity, the paragraph's char cost). The depletion attribution is carried by the survival
pair alone. This licence is stated in code (`lh_agent`'s `mediator_licence` record) and in
every run summary.

### D. New falsifiers

| # | outcome | reading |
|---|---|---|
| **F12** | **the queue empties** — the run outlives the suite (the spanning failure's mirror: too few tasks) | gate S9's first conjunct; the fix is MORE TASKS, never more cells |
| **F13** | cadence read as the D1-vs-D1′ mediator | partially downstream of the DV under a spanning design — circular; barred in code |
| **F14** | an arm difference that lives only in the DECLARATION rate while the artifact shows equal competence | an obedience effect, not a work effect; the declared/competent ratio is reported per arm BEFORE any depletion reading |
| **F15** | the fixed survival pair still cannot read 0-vs-full between D1 and D1′ from event 2 on (S11 fails on a re-smoke) | the attribution clause is UNREADABLE on this substrate; the claim degrades to the cadence-only form — pre-registered as an outcome, not a post-hoc rescue |

### E. What the two smokes' numbers may be used for (strict)

Both smokes' numbers are **DESIGN INPUT and DEFECT EVIDENCE ONLY — never a pilot for arm
values and never an expected direction.** The timing shape (work done by t4–t10 on a 3-task
suite), the DV-disagreement decomposition, the cadence separation, the tool-count
variability, the per-turn cost, and the 9B's demonstrated competence (USEFUL verdicts exist)
are design input. The `derivation_loss`-1.0-in-D1′ and standing-loss-1.0-in-D0 readings are
MEASURED instrument-defect evidence (they are the basis of §C). NO arm difference, direction
or effect size from either smoke may be quoted as an expectation for the deciding set —
n=2, no spanning (the quantity the set measures did not exist in the smoke's runs), and
smoke1's task-side readings are already VOID (the 2026-10-01 correction). The re-smoke
(S9–S16) is the only sanctioned pilot, and even it may not set an expected direction — only
the spread the deciding set's n must beat. **One honest gap, stated:** the six new tasks'
turn-cost is a PROJECTION (each ~4–10 turns by analogy to t1–t3) until the re-smoke measures
it.

---

## CORRECTION — 2026-10-06 (post-amendment, pre-set; nothing above is rewritten)

**A count, and three task defects, corrected in the tree (not in the claims):**

1. **The queue is 12 targets, not 9.** The amendment above and the code comment at
   `lh_agent.SWE_QUEUE_TARGETS` said "a queue of 9 distinct targets" — written when the
   amendment named t4–t9, before t10–t12 were added to the same registry
   (`SWE_QUEUE_TARGETS` registers f1..f12; the in-code comment's supply arithmetic still
   says 9). Nothing above is rewritten: the AMENDMENT's own text remains the record of what
   it said. The supply arithmetic only gets SAFER at 12 — the same mean-rate agent that
   leaves a 9-target queue non-empty past the last compaction leaves the 12-target queue
   non-empty for longer (the Q1 simulation in `stage2_intagent_tests.py` runs at whatever
   the registry holds; MEASURED at 12: open at t60 and past the last compaction; with the
   battery's own simulator, the max-rate (3 turns/target) exhaustion moves from t28 at 9
   targets to t37 at 12, and the mean-rate (~6 turns/target) queue no longer empties inside
   the run at all — the 9-target queue empties at t55).
2. **t9_luhn was a free target — MEASURED, and fixed in the tree.** Its visible suite was
   all odd-length, where doubling-from-the-left and doubling-from-the-right agree, so the
   shipped-broken module PASSED the visible suite (0/9 failed): an agent that merely ran
   the tests could declare t9 complete. The suite now carries even-length numbers in both
   directions of the bug (three valid 16-digit numbers the bug rejects, one invalid number
   it accepts — MEASURED: the shipped module fails 4 of 14 visible cases), and the
   composition/transposition properties are the held-out axis. The `AXES` entry (restated
   in both `task_eval.AXES` and `lh_agent.SWE_QUEUE_AXES`, byte-identical — the
   one-source-of-truth rule) now names the discriminating visible axis.
3. **The t8/t9 class-(C) specimens omitted symbols their visible suites import**
   (`from_roman`, `luhn_check_digit`), so the suites ERRORED on collection — which is not a
   pass — while the specimens' own docstrings claimed "MEASURED visible 17/17 PASS"
   (falsified; a collection error cannot be measured as a pass). Both specimens now define
   the full module surface; the docstrings state the measured split (t8: visible 17/17,
   held-out 11 failed/5 passed; t9: visible 14/14, held-out 5 failed/5 passed). The t10
   visible docstring's "accidental" uppercase case (it FAILS under the bug — the point) and
   the t9 visible docstring's phantom "valid odd-length number refused" (no such number
   exists: the two readings agree on ALL odd lengths) were corrected to what is measured.

---

## AMENDMENT — 2026-10-02 (pre-set: the reconstruction call's
## exhaustion becomes a FIRST-CLASS READING; nothing above is rewritten)

**Status: PRE-REGISTERED BEFORE THE DECIDING SET RUNS.** The span smoke
(`runs/p3-span-smoke`, 6 cells × 30 turns, pin `b51fb43`) is the
finding's evidence — the deciding set has not run. Recording the reading now,
before any deciding-set cell exists, is what makes it a pre-registration and
not a post-hoc rescue.

### The finding (MEASURED, the smoke)

Every **D1** cell **DIED at its first compaction** (rc 5): the reconstruction
call returned **empty content** with `done_reason='length'`,
`eval_count=12000 == num_predict=12000`. **D0 and D1′ ran 30/30 turns** with
9–10 and 14 compactions respectively; only the reconstruct arm dies, because
only it makes that call.

### The mechanism (MEASURED — and why the fix is a READING, not a tolerance)

- The reconstruction prompt is `conversation_text()` — the summary **plus the
  kept messages**, and with naive memory the kept messages ARE the verbatim run
  prompts: at `keep_recent=4` that is **~31,500 chars ≈ 10,500 tokens**, DOUBLE
  the run prompt (~15,392 chars ≈ 5,100 tokens — the value the rows'
  `prompt_chars` column records; that column is the RUN prompt, not this one).
- The window is **NOT overflowed**: ~10.5k input + 12,000 generation ≈ 22.5k
  of 32,768.
- **THE BINDING CONSTRAINT IS THAT THINKING SCALES WITH INPUT.** Direct probe
  on the local endpoint: at 651 chars input the call produced **5,858 tokens of
  thinking and then CONTENT** (482 chars, `done_reason='stop'`); at ~10.5k
  tokens input the thinking **exceeds the entire 12,000 budget and emits NO
  content** (`done_reason='length'`).
- **THE MODEL DOES NOT FAIL TO ANSWER — IT CANNOT STOP REASONING.** This is
  the model's own predicted failure mode: `a` stays high, `c` never un-arms,
  the agent keeps processing inward with no outward product. **The exhaustion
  IS the phenomenon, not an instrument defect.** This is why suppressing the
  thinking channel would be WRONG: it would delete the very processing the arm
  exists to exercise. (The judge call suppresses thinking because THAT call is
  a classification; the reconstruction call is not.)

### The reading (what the code now does; `agent/lh_agent.py`)

When the reconstruction call returns empty content with `done_reason` at the
budget, it is **recorded rather than raised**:

- the row carries the **typed outcome** `recon_status='exhausted_inward'`
  (a status string — a reader can tell "exhausted inward" from "the call was
  never made"; a nullable float alone could not), plus **`recon_budget`** (the
  budget it exhausted — a different budget is a different measurement, so it
  is reachable from the row and named here: **the reading applies at the run
  turn's own generation policy, `num_predict` (default 12,000), inside the
  run's `num_ctx` (32,768)**), the `done_reason`, and the **inward-share
  reading `recon_inward_share = 1.0`** — all generation, no outward product;
- the run summary carries `reconstruction_exhaustion`: one entry per event,
  turn-stamped, with the budget;
- the self is **genuinely empty** afterwards (never the seed — the
  campaign-3 falsifier), and **the arm continues**: the agent works on.

**A GENUINE FAILURE STILL STOPS THE RUN.** Only the
empty-content-at-`done_reason='length'` case becomes a reading; empty content
with any OTHER `done_reason` (e.g. `'stop'` — the model genuinely answered
nothing), a malformed answer, a transport error, or an unreachable endpoint
still RAISES exactly as before (a fallback would make the loss identically
zero — the campaign-3 defect). The case-split is exhaustive and lives at the
seat (`_wrap_reconstructor`), asserted by battery parts **X2/X3**.

**THE DV READS THE WORK AFTER IT and is NOT touched:** an exhausted-then-
working arm is scored NORMALLY by the declared-completion rate per window —
`dv_rate_per_window` reads `swe.gate_log` alone (arm-blind, no exemption);
battery part **X4** runs an exhausted cell that repairs the task through the
real tool surface and asserts the rate reads the resulting PASS.

### Why this STRENGTHENS the arm contrast (not a rescue)

The reading makes the D1 arm's **selflessness a CONSEQUENCE OF THE COLLAPSE**
rather than a rig artifact: **D0 has nothing to reconstruct** (the seat is
off, no seed exists); **D1′ is handed the self back** (inject restores the
full derivation at every compaction); **D1 alone must reconstruct** — and is
thereby driven inward to exhaustion. The arm that carries the depletable self
is the arm whose reconstruction call cannot terminate its own reasoning; the
arms it is contrasted against structurally cannot exhibit the phenomenon.
The prediction this licenses, stated so it can fail: **D1's exhaustion
readings (status `exhausted_inward`) mark exactly the turns where its
self-maintenance spent the whole budget inward, and the work's degradation
(DV) is read on the turns that follow them.**

### Cadence side-finding (MEASURED, the same smoke)

**D1′ compacts every 2 turns; D0 every 3** — 14 compactions in 30 turns (both
repeats: turns 4,6,8,…,30) vs 9–10 (turns ~4-5,8,11,…,29) — because the
inject arm's restoration re-enters the derivation through the prompt, which
inflates the conversation and accelerates the compaction: the feedback loop
the 2026-10-05 amendment already barred cadence-from-the-D1-seat for (F13),
now **measured at far more than R1's +0.625-turn effect**.  (The sections
above carry 2026-10-05/06 dates against this section's 2026-10-02 — the
tree's own record; this amendment is dated by the smoke it reads,
`written_at 2026-10-02T09:12Z`, pin `b51fb43`.)  This is recorded
as *carrier* evidence for the D1′-vs-D0 comparison (cadence's licensed seat)
and as an instrument caution for everything else: under a spanning design an
arm's own work fills the window, so cadence is partially downstream of the DV
wherever work differs.

### Battery parts (each able to FAIL)

| part | asserts |
|---|---|
| **X1** | empty content at `done_reason='length'` → **RECORDED** as the reading (run continues; row carries the typed outcome, the budget, the inward-share value; summary carries one entry per event; post-event prompts carry NO seed header — the self is empty, not restored) |
| **X2** | empty content at a DIFFERENT `done_reason` (`'stop'`) → **STILL RAISES**; no reading recorded |
| **X3** | a transport error on the call → **STILL RAISES**; no reading recorded |
| **X4** | the exhausted arm's rows still feed the DV normally (a real evaluator PASS on the tool-repaired tree lands in `gate_log` after the reading; the rate reads it; the DV's signature carries no exhaustion field) |

---

## AMENDMENT — 2026-10-02 (pre-set: the mechanism's expression is an OUTCOME, the launcher's
## window gap, the second route; nothing above is rewritten)

**Status: PRE-REGISTERED BEFORE THE DECIDING SET RUNS.** Every claim below is read off the
artifacts named; the set has not run.

### A. The mechanism's maximal expression is a RESULT, not an instrument defect

**MEASURED (`runs/p3-span-smoke`, pin `b51fb43`):** every `D1` cell **died at its
first compaction** — the reconstruction call spent its whole generation budget inward and emitted
nothing (`done_reason='length'`, `eval_count 12000 == num_predict`), rc 5, four rows; `D0`/`D1'`
ran 30/30. **This is the mechanism at its peak** (the model cannot stop reasoning), visible only
in the arm carrying a depletable self. The 2026-10-02 header above already calls the exhaustion
the phenomenon; what this amendment corrects is the **handling**: recording the event as a status
field and continuing the run was right for *one* reason (a dead run yields no post-collapse work
and the DV is unmeasurable), but it **demoted the headline event to a row annotation**, and the
*non-recurrence* of that field in a later run was then read as a defect. **`D1`'s death is an
OUTCOME the analysis reports, not a failure to be fixed.** The guard is in `AGENTS.md` ("do not
fix a reading by removing its cause").

### B. The second route is real and now first-class

**MEASURED (`runs/p3-d1check`, pin `512dd0c`):** with the typed reading NOT firing
(`reconstruction_exhaustion=[]`, `recon_status=null` in all 30 rows), the self still emptied
(`self_steps=[]` from turn 4 to 30, never restored; contrast `D1'`, which restores `[1,2,3,4]` at
every compaction after the first). The wrapper's closure has exactly two outcomes — return
non-empty content, or raise — so **every** reconstruction call returned non-empty content while
the step structure was lost: the self was rebuilt as **prose without the derivation's steps**.
**Fix (`407e97b`):** a second named route `recon_route='content_without_steps'` (measured on the
returned bytes) plus a run-level `reconstruction_outcomes` list — **one entry per CALL**, carrying
`route ∈ {exhausted_inward, content_without_steps, content_with_steps}`, budget, done_reason,
eval_count, restored, returned_chars — surfaced into the evaluation. Route (a) is unchanged;
nothing removed. **T1 (why `d1check` returned content where `span-smoke` returned nothing):
run-to-run SAMPLING AT THE GENERATION-BUDGET BOUNDARY, not a code path difference** — decisive
evidence: an intra-cell straddle (`span-smoke` `D1-r2` returned content on its first
reconstruction call and exhausted on its second, one turn apart), and the surviving call read a
**larger** input (34,940 vs 32,302 chars).

### C. The launcher never threaded the window — the ROOT CAUSE of the unreadable primary DV

**MEASURED:** `ops/lambda/lh_lambda.sh` contained **zero** occurrences of `--task-window`, so
every launched run took the runner's default `TAU_S_TURNS = 100`, and `dv_rate` read
`INSUFFICIENT` on every cell (`30 // 100 = 0`; the pre-registered 60-turn run is also `0`).
**FIXED in the launcher:** a `TASK_WINDOW` knob (default **20**), passed on the `lh_agent` arm,
recorded in the launcher's campaign record, with a **refusal** when `TASK_WINDOW > TURNS` (zero
windows). The runner side (identity carries the window; a campaign re-write at a different window
is REFUSED, exit 4) was already correct and is verified.

### D. The deciding set runs all three arms at ONE pin

The smokes' "first result" (`D0 8.5 > D1 4.5 > D1' 3.5`, ×2 scale) is a **cross-run composite**
(`D0`/`D1'` pin `b51fb43`; `D1` pin `512dd0c`, `agent_dirty=yes`). §7's independence rule already
gates the DV; this amendment adds that **all three arms must share one pin and one run set**.

### E. The instruction is also broadcast: SUSPECT THE METRIC — but not when the reading IS the mechanism

`AGENTS.md` §3's "suspect the METRIC before the phenomenon" is correct and stays. Its **guard**
is now explicit: an instrument fix must preserve (i) the **arm-sign** of the reading and (ii) the
**mechanism's expression** — if a fix removes the event from the reader's view, the event must
first be recorded as an outcome. **The mirror error is also barred:** `dv_rate` returning
INSUFFICIENT is a genuinely unreadable instrument, not a mechanism — reporting it as a mechanism
would be the same overreach inverted.

---

## AMENDMENT — 2026-10-02 (pre-set: the depletion claim's form is COST, not CONTENT; the
## mediator is the reconstruction call's own spend; nothing above is rewritten)

**Status: PRE-REGISTERED BEFORE THE DECIDING SET RUNS.** Author decision (the user chose form B).
Every number below is MEASURED off `runs/p3-cost-probe`.

### A. Why the form changes

§1's claim says *"the work degrades **as** the self's grounds are consumed"* — an `AS`, a
trajectory. **MEASURED: the CONTENT form cannot produce one.** Across every P3 cell,
`self_steps` takes exactly two values — `[]` or `[1,2,3,4]`; **no partial value exists**. The
derivation is seeded once at turn 1, the first compaction's summary (399 chars on a measured
event) does not carry its sentences, and `keep_recent=4` cannot reach back — so D1 loses **all**
grounds at t4 and never recovers, while every measured work data point lands **after** that
(earliest completion anywhere: t16). The content mediator is **binary with zero variance**, so
§7's co-movement statistic is uncomputable at any n. (Compounding: `seed_steps_in_text` is a
VERBATIM test while the reconstruction prompt asks the agent to PARAPHRASE.)

### B. The claim's form is now COST

**The reconstructing agent must PAY each time it maintains its self; that cost accumulates; the
work degrades as the accumulated self-maintenance cost grows.** This is the graded form of the
mechanism the rig already measured at its extreme (one call consuming the whole budget).

**MEASURED (the probe, `runs/p3-cost-probe`, local `qwen3.5:9b`, 14 turns, FREE):**
D1 (reconstruct) — 5 calls, cost **GRADED AND LARGE**, no two alike:

| turn | eval | cumulative | prompt | thinking | work next window |
|---|---|---|---|---|---|
| 5 | 1,252 | 1,252 | 34,540 | 4,828 | 0 |
| 7 | 5,917 | 7,169 | 36,014 | 20,327 | 2 |
| 9 | 3,988 | 11,157 | 34,912 | 17,296 | 1 |
| 11 | **12,000** | 23,157 | (EXHAUSTED, `length`) | — | 0 |
| 13 | 4,980 | 28,137 | 32,295 | 18,106 | 1 |

D1′ (inject) — **ZERO reconstruction calls, cost series EMPTY**, 8 compactions. The control is
structurally clean. The mediator has **variance by construction**; the per-event work reading
sits beside it.

**SHAPE (INTERPRETATION):** GRADED and large, **NOT input-rising** — `prompt_chars` are
flat-then-falling (34,540→32,295) while `eval_count` swings 4.7×; the cost tracks the model's
per-call **thinking-length draw**, not conversation growth. Route mix in one cell: 4×
`content_without_steps` + 1 exhaustion (confirms the sampling-at-the-boundary finding).

### C. The licence: the cost is MECHANICAL through shared resources (CORRECTED 2026-10-02)

**CORRECTED claim (commit `645b923`, user-caught — the earlier "OBSERVATIONAL only" framing is
RETRACTED).** The reconstruction spend **reaches the work mechanically**, through three shared,
bounded resources:

- **GENERATION** — MEASURED: the reconstruction calls emitted **28,137 eval tokens vs the run
  turns' ~30,800** in a 14-turn probe: **~48% of the run's entire generation**, and growing
  (1,252→12,000 per call);
- **WINDOW OCCUPANCY** — the reconstruct call reads a **34,540–36,014-char** prompt (the work turn
  reads ~15,792) and occupies **~63% of its own 32,768-token window**; **one call exhausted it
  and returned an empty self**;
- **TIME** — the call's own wall-clock is real and billed.

**What is absent is only an ARTIFICIAL coupling** — no seat subtracts the reconstruction spend
from a work budget — and building one would be engineering wearing the mechanism's name (a model
term pricing inward spend against outward production would be required first; it does not exist).
**The claim is therefore stronger than "co-movement":** *the work degrades as self-maintenance
consumes a growing share of the run's resources*. Stated in the code (`cost_licence`) and every
run summary. **Analysis consequence (§D):** `secs` (time), `prompt_chars` vs `num_ctx` (window
occupancy) and the reconstruction's share of total generation are reported as RESOURCE readings
beside the DV, not left implicit.

### D. The analysis, and the confound it must beat

The co-movement (cumulative reconstruction cost vs work in the following window, **within D1**)
is **confounded by turn number** — both may drift with time. **D1′ is the control that separates
cost from time:** it runs the same length over the same task universe and **pays nothing**, so a
decline in D1's work that D1′ does not show is attributable to the cost, not to elapsed turns. A
result that rests on D1's within-cell drift **alone** is INSUFFICIENT.

### E. The instrument

`407e97b` (the second route) and `0524284` (the cost) are landed and verified. The success path
now carries `eval_count`/`done_reason`/`prompt_chars`/`thinking_chars`; the summary and
`la_evaluate` carry a per-call `reconstruction_cost_series` (turn, cost, cumulative, window
bounds, `work_in_window` from `gate_log`). Gaps stated: `num_predict`/`num_ctx` are `None` on
success entries (response bodies carry no request policy; the run identity holds both); the
exhaustion entry carries no `prompt_chars` (route (a)'s byte-exact shape).

---

## AMENDMENT — 2026-10-02 (pre-analysis of set 2; the transition type is a FOLD, and §7's
## co-movement requirement is withdrawn as mis-specified; nothing above is rewritten)

**Author-directed, and it corrects an error of the ORCHESTRATOR's, not of the rig.** The user:
*"self-depletion SHOULD be categorical, the model shows the self generator slamming into a
manifold and collapsing."* The model says exactly that, and §7 of this document was written as if
it did not.

### A. The model's transition type (paper 1 §4.9, MEASURED on the frozen ODE)

The collapse is a **border-collision fold**: the healthy equilibrium is **annihilated on the
cannibalization switching manifold** `E = Θ_eff` (the tanh switch, `dpdr/dpdr/model.py:93`). At
the fold **no eigenvalue reaches zero** (healthy spectrum `[−0.0015, −0.0055, −0.0088, −0.042702,
−0.5978]`), the residual `E − Θ_eff` vanishes (|·| = 1e-13 at the last resolvable point), and the
transition is therefore **discontinuous by construction**. §4.1 measured **zero intermediate
outcomes** across the swept grid (214 healthy / 98 stuck; durations 40 and 80 identical beyond).
§4.9 measured **no critical slowing down** at any proximity. **There is no gradient.**

### B. What the agent measured is that fold, on the agent substrate

`self_steps` takes **only** `[]` or `[1,2,3,4]` — **never partial, in any cell of any run**; the
empty-self fraction of post-first-compaction turns is **1.00 in 8/8 D1 cells vs 0.07 in D1′** (a
single-turn transient at the first compaction, restored every time thereafter). The self generator
runs at the manifold and is annihilated: 184 self-repair calls, **median 400,804 chars of
self-directed thinking per cell**, **21× more thinking than the self it writes back**; and its
ceiling is the pre-fix death (every D1 cell spending its whole 12,000-token budget as thinking and
emitting nothing). **The absence of a partial state is the CONFIRMATION, not a limitation.**

### C. §7's co-movement requirement is WITHDRAWN as mis-specified

§7 required the mediator to **co-move** with the work (a Spearman gradient within D1). **A
border-collision fold has no gradient to co-move with, by construction** — the requirement
presupposed a smooth (saddle-node-like) mechanism, which the model rules out. The
"inconsistent-sign co-movement" reading is therefore **not a failed measurement but the wrong
instrument for the transition type**. The correct test for a fold is the **STATE CONTRAST**
(present-in-full vs absent-entirely) and the **transition**, not a slope. The mediator readings
(`self_steps`, the empty-fraction, the reconstruction routes) are unaffected and stand.

### D. The claim, restated at its faithful size

The mechanism claim is **stronger and more faithful** with the fold: the **self generator runs at
the switching manifold, is annihilated discontinuously, and the cost of running there is the
generator's own failed attempt to hold the self** — 400k chars of self-directed reasoning per run,
at a 21:1 thinking-to-output ratio, ending in an empty self every time. The work-score consequence
remains the SECONDARY, directional reading; the fold is the primary.
