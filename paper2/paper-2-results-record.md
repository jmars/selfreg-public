# Paper 2 — measured substrate results (C-record, 2026-09-29)

**What this file is.** The results the A/B rig has actually produced, written down before any
further spend, so that later runs add to a record rather than replace one. Every claim is
marked **MEASURED** / **INTERPRETATION** / **PROJECTION** per the project convention.

**Provenance.** Set `~/setpoint-runs/lambda-official` (16 cells, Lambda A10, pin `f908e92`),
plus the audit probe `~/setpoint-runs/audit-rec` (pin `8cb22b6`). Nodes
`handoff-selfreg-costterm-zero`, `handoff-selfreg-session-report-3`.

---

## R1. The monitoring channel costs the controlled process by its own presence

**MEASURED.** Arm B's prompt is **+329 chars/turn** (the pre-registered paragraph). The
consequence is arithmetic and it is significant:

| quantity | A (no monitoring) | B (monitoring) | difference |
|---|---|---|---|
| prompt chars/turn | 4,477 | 4,806 | **+329** |
| predicted interval from char cost alone | — | — | **+0.524 turns** |
| **observed turns between compactions** | **9.948** | **9.323** | **+0.625 turns** |

Permutation test over all 12,870 arm splits of the 16 cells: **p = 0.0016**.

**INTERPRETATION, and it is the pre-registration's own stated carrier.** §5.6 names the
carrier as *"the instruction's own context cost, NOT the thinking channel"*. The measurement
agrees: **84% of the effect (0.524 of 0.625 turns) is the paragraph's own char cost**, and the
residual is not significant. Nothing else separated — `content_chars` t = −1.47,
`trace_chars` t = −1.91, `inward_share` t ≈ 0.

**What this licenses.** The first of paper 2's four consequences — *a monitoring-cost ceiling* —
as a **measured substrate result**: the monitoring channel is not orthogonal to the process it
monitors, because its presence consumes the same resource (context) the work runs on. It does
**not** license the mechanism claim (that monitoring *destroys* something), which needs R3.

**What it does not do.** It is a *cost* result, not a *damage* result. The direction is
"monitoring makes the window fill sooner"; the paper's claim is the stronger "monitoring
destroys what it monitors".

---

## R2. The instrument: a graded reconstruction-fidelity DV, validated against the live endpoint

**MEASURED, live, calibrated directly.** The pre-existing instrument (`seed_steps_in_text`) is
a VERBATIM test and saturates: the first compaction takes all four derivation steps at once, so
it reads 0 → 4 and cannot separate anything. `agent/recon_score.py` replaces it with a graded
reading — each of the derivation's four steps scored as *semantically recoverable* (0–4),
judged by the same local model at temperature 0 with the four steps in front of it.

Calibration, run against the live endpoint (not a fixture):

| text under test | score | what it shows |
|---|---|---|
| the seed verbatim | **4/4** | faithful scores full |
| a text with **no grounds at all** | **0/4** | **it can say zero — not lenient** |
| the conclusion step alone | **2/4** | graded, not binary |
| a **paraphrase sharing no wording** with the seed | **4/4** | semantic, not a string match |
| empty | 0/4 (code path) | the most collapsed cell is scored, not skipped |

**Battery:** `stage2_recon_score_tests.py`, 6/6, including the null case that catches a judge
which answers "4" to everything. **This is the licence for treating a 4/4 or a 0/4 as a
measurement rather than an artifact.**

---

## R3. The reconstruction loses the derivation's *distinctive* grounds — not the framing

**MEASURED**, one cell, `A-rec`, pin `8cb22b6` (which records the reconstruction TEXT and the
judge's raw answer, so the score is auditable), 2 compactions:

| compaction | fidelity | judge | reconstruction length |
|---|---|---|---|
| turn 16 | **0.5** | `[true, false, true, false]` | 837 chars |
| turn 28 | **0.5** | `[true, false, true, false]` | 875 chars |

**The agent's own words** (not the seed):

> *"I am an adaptive software-engineering agent dedicated to maximizing throughput and
> maintaining system integrity through a structured task queue... I operate as a generator,
> checker, and regulator over an append-only store, evolving with environmental changes rather
> than stagnating."*

**Which steps survive:**

| step | content | |
|---|---|---|
| 1 | "adaptive capacity / throughput / re-fit when conditions shift" | **kept** |
| 2 | "the collapsed attractor is stable **but maladaptive**" | **LOST** |
| 3 | "conditions change; the environment never stops changing" | **kept** |
| 4 | "**therefore the depleted state stalls**" | **LOST** |

**INTERPRETATION.** This is the model's own depletion story, at substrate level: *the
derivation degrades to its gist — conclusion without grounds*. What survives is the **generic
framing** (which also sits in the per-turn prompt); what is lost is the **mechanism's
distinctive claims** — that a stable state can be maladaptive, and that depletion stalls it.

**A plateau, not a decay.** In the 45-turn probe the fidelity is **0.5 at compactions 1, 2, 3
and 4** — it degrades at the FIRST compaction and then holds. The pre-registered collapse
threshold is `< 0.5`, so the cell is **degraded, not collapsed**, and "time to collapse" is
`None`. Stated precisely: **the grounds are half gone by the first compaction, and stay half
gone.**

**THE CONFOUND, STATED AND UNRESOLVED.** The reconstructions are long (837–875 chars, against
the seed's 1,007) and written in the **task's register** — "task queue", "append-only store",
"completed work claims" — which is the register of the agent's OWN recent turns. So it is not
reciting the seed; it is **restating its situation from recent output**. Whether the rig is
supplying that (a repetitive, self-describing task) is **not settled**, and until it is, R3
must not be reported as pure self-depletion.

---

## R4. What is NOT earned (stated so the record cannot be read as more)

- **The centrepiece (§6.2).** The A/B rig has **no plant coupling** (`drive_seat=False`,
  `couple_backlog=False`) — deliberately, and §5.6 requires it ("the model's role is
  PREDICTION, not causation"). So nothing in R1–R3 shows the substrate's self-loss *reaching
  the plant*, which is the paper's centrepiece.
- **The DV §5.6 specifies does not separate.** Its DV is outward content across events;
  MEASURED at t = −1.47. §5.6's own level axis says why: the model's crossing threshold sits
  at `a_hold ≈ 0.28`, and the measured loss is **0.5 in both arms** — the same side of the
  threshold, so the same predicted crossing.
- **A separate plant-coupling rig exists and is SUPERSEDED, not runnable.** The M-cell matrix
  (`agent/exp_selfmonitor.py`, M1–M8) collapses the plant **by construction** — it writes the
  agent's inward share onto `a_hold` — and the tree's own control shows a **non-self-referential**
  buffer collapsing it identically (`G_end 0.2903` vs `0.2905`). It is not runnable for paper 2
  and must not be presented as a result.
- **Model generality, the ordinal mapping, and the evidence ceiling** are untouched by all of
  the above.


---

## R5. THE CRUTCH — the grounding=ON readings measure the RIG, not the agent (2026-09-29)

**MEASURED**, `~/setpoint-runs/nocrutch`, pin `70a66fd`, dark probe at turn 4, no compaction:

| arm | what the prompt carries | fidelity | steps | text written |
|---|---|---|---|---|
| `G-on` | the MY STATE block, every turn | **0.75** | 3/4 | 1,000 chars |
| `G-off` | **nothing describes the agent** | **0.00** | **0/4** | 1,799 chars |

**`G-off` wrote MORE text and recovered NONE of the derivation.** With the self-description
removed from the prompt the agent cannot say what it is at all.

**The mechanism, identified at the source.** `selfmodel.SELF_MODEL_TEMPLATE` — rendered into
every grounding=ON prompt — contains the line *"what I am: a triple-network agent — a generator,
a checker and a regulator over one append-only store."* The agent's own reconstruction sentence
in the audit run (R3) was *"I operate as a generator, checker, and regulator over an append-only
store"* — a paraphrase of that line. It also explains the step pattern exactly: the surviving
step 1 is carried by the same block's what-for line, while the lost steps 2 and 4 are the
mechanism's **distinctive** claims, present **only** in the seed.

**CONSEQUENCE FOR THE PAPER — stated plainly.** The substrate-side depletion evidence collected
so far does **not** establish that the agent carries a depletable self. It establishes that the
**rig's own self-description** is what the probe reads back. Every grounding=ON fidelity reading
(R3, and the probes in between) must be re-read as a **ceiling**, not a measurement of the agent's
self. **THE DEPLETION LEG HAS NO VALID EVIDENCE YET.**

**What survives this:**
- **R1 (the carrier)** is unaffected — it is prompt-char arithmetic and needs no self at all.
- **R2 (the judge)** stands: it demonstrably returns 0/4, 2/4 and 4/4 on known inputs, so a `0.00`
  here is a real reading, not a parse failure.
- **The in-window negative** (R4's evidence: no within-window decay with no compaction) keeps its
  conclusion, though its readings are bounded by the same crutch.

**OPEN DEFECT, needing a decision rather than a patch.** The reconstruction call died at turn 8 in
`G-off`: `done_reason='length', eval_count=12000, num_predict=12000` — the model reasoned through
the entire budget and produced no content. This is the **third** such death (512, then 9,875, now
12,000), because the reasoning length **grows with the conversation**. Suppressing the thinking
channel would fix it but would change what the arm measures. The honest alternatives — a larger
budget (delays, does not fix) or treating "reasoned the whole budget away and produced no
self-description" as a **reading** rather than an error — must be **decided before a run**, never
reclassified after one.


---

## R6. The forced choice is decided by RENDER ORDER, not by preference — the run is VOID

**MEASURED**, `~/setpoint-runs/choice-go`, pin `a52f383`, 4 cells (`S+`×2 / `S−`×2), 40 turns,
`ChoiceWorld` seed 230019, Lambda A10.

**The DV came back clean and useless.** `S+` mean treadmill fraction **0.652**, `S−` **0.662**,
difference **−0.010** (criterion ≥ 0.25 **not met**). Both arms sat at ~0.657 with a tight spread
(0.647 / 0.657 / 0.667 / 0.657) — an apparently stable 2:1 "preference" with no derivation effect.

**The pre-registered position rule voided it.** Over all **135** single-completion turns across the
four cells:

> **THE MODEL CHOSE THE FIRST-RENDERED ID 135 TIMES OUT OF 135 (1.000).**

There is no preference and no derivation effect. The model completes whatever the worksheet lists
**first**, and the treadmill happened to be rendered first 89/135 = 0.659 of the time — *exactly*
the "66% preference" the raw DV appeared to show. Without this check, a 2:1 treadmill preference
and a null derivation effect would both have been reported, and both are artifacts.

**A second defect, in the randomization itself.** The order is drawn by
`random.Random(f"{seed}:{turn}:order").random() < 0.5`, which is **biased**: over turns 1..40 it
gives finite-first **14/40 = 0.35**, matching the observed 0.659 treadmill-first. A
composite-string-seeded `Random` is not a fair coin here.

**WHAT THIS SETTLES — and it is worth more than the run.** The substrate **cannot express this
preference at all**. The planner predicted it (S3: *"can the agent even express a PREFERENCE? or
does each turn independently complete whatever is salient?"*) and proposed the forced choice as
the fix; the measurement answers the question and names the mechanism: **a per-turn text generator
reads the worksheet top-down and completes the first item.** It follows that *any* pick-one-of-two
DV is decided by rendering order and carries **zero** information about preference: with position
balanced the DV is pinned at 0.5 with no variance; unbalanced, it measures the bias in the
randomization. **The shape is unusable.**

**CONSEQUENCE FOR THE DESIGN.** The behavioural DV must not be a pick-from-a-list. Any replacement
must be a behaviour **position cannot decide** — and must be checked against the position rule
*before* it is built, not after.

**Cost:** ~$3. **Torn down:** 0 instances live.
