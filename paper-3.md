# Self-Application Is Not Free: the Monitoring Channel Is Part of the Failure Channel, and the Self Does Not Survive Its Own Reconstruction

Jaye Timothy Marshall — ORCID 0009-0002-5209-8161

**Status.** Unified paper (2026-10-03). Two linked claims, one measured honestly at full size
and one measured honestly at null. Everything substantive is marked **MEASURED** /
**INTERPRETATION** / **PROJECTION** (§0). The work-score consequence of the mechanism is a
**NULL** — directional, unstable across two independent sets, never significant at any n run
(§10) — and this paper does not soften that. What is established is the mechanism itself,
replicated across two independent sets and two pins to within ~0.4% on its headline quantity
(§9, §10), and the honest negative beside it.

---

## 0. Marking convention, provenance, and the unit

Every substantive claim is marked in place:

| mark | meaning |
|---|---|
| **MEASURED** | a number or outcome produced by a committed driver or a real run, with its artifact named |
| **INTERPRETATION** | a reading of measurements in other vocabulary |
| **PROJECTION** | a prediction or extrapolation with no measurement behind it yet |

**Provenance series.** `[R-n]` names a measurement in the methods-half results record
(`paper2/paper-2-results-record.md`): R1 the monitoring carrier, R2 the instrument
validation, R3 the saturation, R4 the within-window negative, R5 the prompt-coupling
(crutch) finding, R6 the render-order void. The deciding set's own measurements (this
paper's results half) cite their artifact paths inline (`runs/p3-set`,
`runs/p3-set2`). Paper 1
(Marshall, *Self-Application as the Common Source of Benefit and Failure*) is **cited, not
re-derived**: its §4.9 (the border-collision fold), §5.3 (the D/G dissociation), §4.5 (the
standing-cost budget) carry the model-side ground of every model claim made here.

**The honest unit, stated once, up front.** This paper reports two experiments on two
different units, and neither is "an agent" in general. The **methods half** (§3–§6) measured
a **self-referential substrate inside a measurement rig** — a turn loop whose self-block
thins, wired to a frozen plant — with no task, no execution, no entailment and no scheduled
consolidation in the build; the rig is not a worker, and paper 2's own §1.1 said so at equal
length. The **results half** (§7–§10) measured a **worker**: one loop, one 12-target task
suite, real tools, an external evaluator, one model (`qwen3.5:9b`). Claims about "agents" in
general are marked PROJECTION and are not made as findings.

---

## Abstract

Dual control — the closest control-theoretic precedent for the cost of monitoring — assumes
the sensing channel is orthogonal to the controlled process: the probe is chosen, bounded and
instrumental, and monitoring costs performance rather than damaging the plant. Paper 1
established, in a five-state dynamical model, that a self-referential control loop breaks
this assumption structurally: monitoring *is* self-reference; its cost **feeds the failure
variable**; the sensor is **destroyed by the failure it must detect** (at the collapsed fixed
point D = 0.5455, exactly its baseline, while G collapses 0.8855 → 0.0485); the collapse
transition is a **border-collision fold** — discontinuous by construction, no intermediate
state; and the standing cost of self-application has a sharp measured budget (c_int ≈ 0.112).
This paper takes those predictions to two real substrates, in two stages, and reports one
replicated mechanism, one instrument finding **that is the same failure as the mechanism,
measured in the paper's own apparatus** (the monitoring channel and the measurement channel
share the failure of the thing they measure), and one honest null.

**Stage one — the rig.** A self-referential substrate (a turn loop whose self is a
four-step derivation, priced per turn, injected per window) inside a measurement rig.
MEASURED: the monitoring paragraph's mere presence costs the process it monitors —
**+329 chars/turn of context, moving the compaction interval +0.625 turns, permutation
p = 0.0016**, with 84% of the effect being the paragraph's own char cost [R1]. Also measured,
and it is the paper's claim occurring in its own apparatus: **every self-side instrument
failed because the instrument and the thing measured share a channel** — the harness
describes the self to the agent in every prompt, and removing that description drops the
reconstruction-fidelity reading from 0.75 to 0.00 while the agent writes *more* text [R5];
the instrument saturates where the signal dies [R3]; and the one behavioural DV tried was
decided by render order 135/135 and is void [R6]. The sensor-placement rule this forced —
*put the sensor outside the channel it measures* — is the design rule the worker was built to.

**Stage two — the worker.** Three arms, one loop, one 12-target task suite, real tools, a
sealed held-out evaluator outside the agent's write domain, the plant edge severed in every
arm; 60 turns; two independent sets (n = 8/arm at pin `645b923`, n = 10/arm at pin
`bfbe5d0`). MEASURED, and replicated to within 0.4% on the headline quantity: **an agent
that must reconstruct its own self after every compaction loses the self in every cell,
permanently — empty-self fraction 1.000 in 8/8 then 10/10 D1 cells, against 0.08/0.07 in the
inject control, where every gap is a single turn at a compaction boundary — while spending a
median ~400,000 chars of self-directed thinking per cell (~117,000–150,000 eval tokens) on
exactly that reconstruction, at a thinking-to-output ratio of ~21×.** The loss is
categorical, not graded: `self_steps` takes only `[]` or `[1,2,3,4]`, never a partial value,
in any of the 3,123 rows of the two sets — which is precisely the transition type paper 1's
border-collision fold predicts (present-in-full or absent-entirely, zero intermediates). The
pre-registration's co-movement requirement is **withdrawn as mis-specified**: a fold has no
gradient to co-move with.

**The work consequence is a NULL, reported as one.** The pre-registered secondary DV orders
as the claim predicts — the arm that pays for self-maintenance is worst in both sets and on
both DVs — but the effect **halved on replication** (D0 − D1: 2.26 → 1.08 on the 0–12
ordinal; p ≈ 0.10 → 0.35), the carrier contrast is null in set 2 (ordinal p = 0.96; finer-DV p = 1.00), and the finer
continuous DV bought for the re-run **failed to cut the variance it was bought to cut**
(within-arm sd essentially unchanged) — a negative instrument result. An effect that halves
on replication and reaches p < 0.05 in neither set is **not established**, and nothing in
this paper claims the agent's work was damaged. What is established: **self-application is
not free** — the monitoring channel consumes the process's own resources by its presence,
and the self, once it must be reconstructed rather than restored, does not survive the
reconstruction — at a cost of order 10⁵ tokens per run, in a working agent, on a real task,
with the plant unable to explain any of it.

**Keywords:** self-application; self-reference; dual control; monitoring cost; sensor
placement; long-horizon agents; reconstruction; depersonalization-derealization (DPDR)

---

## 1. Introduction

Paper 1 (*Self-Application as the Common Source of Benefit and Failure*) established, in a
deterministic five-state model, that self-application is the common source of benefit and
failure: the same self-referential operation that gives the system its benefit also drives
its collapse, and the collapse is a discontinuous annihilation on a switching manifold, not a
gradual erosion. The model's agent-level sentences were marked interpretations — the mapping
from model slots to any real agent is ordinal and unvalidated. This paper is the test on real
substrates, in two stages, and its title is its thesis in two claims:

1. **The monitoring channel is not orthogonal to the controlled process — it is (part of)
   the failure channel.** Monitoring is not an instrument the system can pick up and put
   down; it is the system's own operation turned on itself, and its cost lands on the same
   resources the work runs on.
2. **In this working agent, the self does not survive its own reconstruction.** When the self
   must be rebuilt by the agent's own generation after each memory compaction — rather than
   restored by the harness — the self is lost, categorically and permanently, at enormous
   generation cost, in every cell.

The two claims are **one structure seen twice — but across two units, not in one shared
measurement.** No single experiment measures both. Claim (i) — the monitoring channel is
(part of) the failure channel — is established on the **rig** (R1: +329 chars/turn,
+0.625 turns, p = 0.0016) and in the **model** (the D/G dissociation, §3); claim (ii) — the
self does not survive reconstruction — is established on the **worker** (18/18 cells, §8).
The worker-side contrast that would *independently* show claim (i) on the worker — the
carrier, D1′ vs D0 — is **null** in set 2 and unresolved in set 1 (§10), so claim (i)'s
worker-side evidence is the **cost** (R1 generalized: the ~400k chars of self-directed
thinking per cell, the ~21× ratio, the self-maintenance tokens against zero in both
controls), not the failure-channel *identity*. What joins the two claims is **not a common
experiment** but (a) the model's **prior prediction** — the worker's transition type (a
discontinuous, all-or-nothing loss) was predicted in advance (§3, §9) and matched — and
(b) R5, where claim (i)'s structure **recurs in the paper's own instrumentation**: the
instrument built to measure the self was supplied the self in every prompt, so it measured
the rig — the sensor sharing the channel with its signal loses the signal exactly when it is
needed, the same structural fact as the D/G dissociation, measured in the apparatus built to
test it. The "one structure seen twice" is a **structural correspondence across units**, not
a shared measurement, and a reader should finish this section knowing exactly which claim
rests on which unit.

**The arc, and the unit, honestly named.** §3–§6 are the methods half: the rig, its
campaign, and findings R1–R6 — one positive cost result and five instrument findings, of
which R5 is the most important (it is this paper's own claim occurring in its own
apparatus). §7–§10 are the results half: the worker's deciding set, the mechanism, the fold
correspondence, the honest null (with its replication). The rig is not a worker; the worker is
one model on one task suite; and neither licenses a claim about agents in general. What the
two halves share is the structure the model predicted, and the discipline of stating each
result at exactly its measured size.

---

## 2. The broken assumption, and the rule that follows

Dual control (Feldbaum 1960–61, 1965) fully contains the tradeoff everyone reaches for
first — probing versus directing, the Bar-Shalom–Tse dual effect, even an information-channel
feedback loop (cautious-control turn-off). What it does not contain is the case where the act
of monitoring worsens the monitored state, or where the sensor is destroyed by the failure
it exists to detect:

| dual control assumes | the self-referential case |
|---|---|
| the probe is chosen and bounded | monitoring **is** self-reference — it cannot be made instrumental; it is the same operation the system already performs |
| the cost is performance (exploration vs exploitation) | the cost **feeds the failure variable** — monitoring adds inward attention, which is the collapse driver |
| the sensor reads the plant from outside | the **sensor is destroyed by the failure it must detect** |
| the fix is to probe less, or better | the fix is to **relocate the sensor** |

The break is structural, not a matter of degree. Under dual control "monitor less" is always
available because the probe is instrumental; under the self-referential structure the
monitoring load and the failure load are the same term in the same equation, so reducing
monitoring reduces the benefit the system exists to have, while relocating the sensor changes
which subsystem carries the signal when the failure arrives. The rule, which paper 1 measured
the ground of but declined to state: **put the sensor in the subsystem that survives the
failure, or outside the system entirely.** (Novelty caveat, carried forward verbatim from the
methods half: sensor placement and observability are mature topics and a focused search of
that literature is outstanding; "could not find it stated elsewhere" means
not-yet-contradicted. **INTERPRETATION.**)

**The rule's second life, discovered in this programme.** The rule was written for
*protection*. The rig then showed it is also the rule for *measurement*: an instrument that
routes through the channel it measures (here: any self-side probe whose answer is supplied in
the prompt) loses the signal exactly when it needs it [R5]. §7 states that finding; the
worker's evaluator was built to it.

---

## 3. The model ground — cited from paper 1, not re-derived

Everything in this section is paper 1's measurement, carried here as premise. This paper
claims no credit for it and restates only what its own experiments lean on.

**The structure.** A five-state deterministic control system (a, G, D, S, g) whose failure
mode is collapse of the self-content generator G into a self-maintaining state with no
outward pull. Two couplings carry this paper: the **cannibalization channel** (the reducer
reads the generator — D's dynamics are driven by the switch state through B = EMA_τD(c), so a
reducer that must reduce the generator's output raises demand for reduction; this is what
makes the monitoring channel and the failure channel the same channel) and the **monitoring
ceiling** (c_mon_crit = 0.511 gated / 0.112 ungated: above it, monitoring *sustains* the
collapse it is supposed to detect).

**The D/G dissociation — "the sensor is destroyed," measured.** At the collapsed fixed
point, **D = 0.5455 — numerically its baseline, untouched — while G collapses 0.8855 →
0.0485** (paper 1 §5.3). A regulator whose sensor lives in G loses its sensor precisely when
it is needed: the sensing channel is not merely perturbed by the failure but converted into
the failure variable. **MEASURED** in-model.

**The standing-cost budget.** The window module's collapse horizon is bounded by the
normalized standing cost **c_int = c_cap·T_max/τ_sim ≈ 0.11223** — identical across a 4×
range of c_cap, and coincident with the frozen chronic-hold critical (a_hold_crit = 0.11213)
and the ungated monitoring critical (0.112). Paper 1 states the agreement as a **consistency
check, not an empirical unification** (the window's cost channel was designed to enter where
a_hold enters); the operative content here is the existence of a **sharp standing-cost
budget** on self-application. Under sustained (non-episodic) stress the sign reverses: more
capacity *lowers* the sustained-drive threshold, because the standing cost dominates — the
self is not free even when it is helping. **MEASURED** in-model.

**The border-collision fold — the transition type this paper's worker test leans on.**
Paper 1 §4.9: on the chronic inward-drive axis, the healthy equilibrium is annihilated
**exactly on the cannibalization switching manifold E = Θ_eff** (ε_c = 0.265192279; residual
|E − Θ_eff| = 1e-13 at the continuation's last resolvable point; the tanh switch at
`dpdr/dpdr/model.py:93`). At the fold **no eigenvalue reaches zero** (healthy spectrum
[−0.0015, −0.0055, −0.0088, −0.042702, −0.5978]) — this is a border-collision fold, not a
saddle-node — and there is **no critical slowing down** at any proximity (the dominant
eigenvalue is bit-identical at −0.0015 across five decades of distance). Across the swept
αG × duration grid, **214 healthy / 98 stuck cells and zero intermediate outcomes** (§4.1).
The model's real early-warning signal is **basin retreat**, not slowing. **The prediction
that matters here: the transition is present-in-full or absent-entirely — discontinuous by
construction, with no intermediate state to find.**

**A negative that belongs in the record.** The dual-control-friendly reading — "the
coupling's raised rescue cost (~2.7×) is selective, buying durability" — was pre-registered
against and **falsified** in-model (exp25: zero relapses in either arm, equal dwell at the
arms' own thresholds, the prevented set's minimum OFF dwell 110.4 t.u. against a 50 t.u.
fragility cutoff). The raised dose is pure cost. The mirror reading — "monitor more
carefully" as a fix — is thereby also without support. **MEASURED.**

---

## 4. Related work

**This section is positioned here, not at the front, because both claims are corrections to
specific precedents, and a reader needs the model's own numbers (§3) to weigh what each
precedent does and does not cover.** Each entry is related to the claim it bears on and how —
agreeing, complicating, or not engaging — rather than listed. Read-status is stated where it
is less than full, exactly as paper 1 states it; nothing here is invented.

### 4.1 Dual control — the closest precedent, and the assumption this paper breaks

Dual control (Feldbaum 1960–61, 1965) is the control-theoretic precedent for the cost of
monitoring, and paper 1 read it through the project's dual-control record (two modern surveys
end-to-end: Mesbah 2018; Meijer & Rantzer 2026, arXiv 2608.20073). It fully contains the
tradeoff everyone reaches for first — probing versus directing, the Bar-Shalom–Tse dual
effect, cautious-control turn-off — and even a feedback loop through the *information state*
(turn-off: low input → low information → high uncertainty → lower input). What it does **not**
contain is the case this paper tests. The sensing equation carries noise only; the probe is
*chosen, bounded and instrumental*; monitoring costs *performance*, it does not damage the
plant; and the pathologies run in the opposite direction — they are failures of *too little*
probing (turn-off, bursting), cured by more of it. No result in the surveys has the act of
observing drive the observed system into a worse state, or a sensor destroyed by the failure
it must detect (paper 1's dual-control audit, verdict (b) on claim 1: adjacent/variant — the
cost half is classical, the failure-channel half is absent). **Bears on claim (i): complicates
it.** This paper's contribution against this precedent is not "monitoring has a cost" — that
is dual control's — but that in a self-referential system the monitoring load and the failure
load are the same term in the same equation, so the cost is *pathogenic*, not a performance
tradeoff, and the fix is *relocation*, not *reduction* (§2). The monitoring carrier this
paper measures (R1: +329 chars/turn, +0.625 turns, p = 0.0016) is a *cost* result of the kind
dual control covers; the D/G dissociation (D untouched while G collapses) and the worker's
self-loss are the *failure-channel* results it does not.

**Cited at second hand, stated as paper 1 states it:** Feldbaum's *Optimal Control Systems*
(1965) was not read in the primary — it is available only under controlled digital lending
(archive.org, access-restricted; OCR closed); the engagement here stands on the Meijer &
Rantzer review read in full and the Filatov & Unbehauen textbook formulation, and has not
been checked against Feldbaum's own statements (paper 1 ref [4], access level carried
verbatim).

### 4.2 Self-reference, strange loops, and the classical self-application lineage

The structure this paper tests — a system whose operation turns on itself — is Hofstadter's
strange loop (paper 1 ref [1], *Gödel, Escher, Bach*); the escape distinction is the
philosophical vicious-vs-non-vicious circularity divide; and the formal content — which
self-applications terminate — is term-rewriting termination and confluence, undecidable in
general (paper 1 refs [2], [3]). Paper 1's window module derived its benefit term
structurally from the self-improvement operator `f = M ∘ V ∘ f_T` of Zhang, Yuan & Zhang
(2026, arXiv 2607.04277 — bounded self-simulation, evaluation, modification, with the fixed
point from Kleene's second recursion theorem; paper 1 ref [8]), whose bounded-horizon T is
the shared axis of paper 1's window experiment. **Bears on both claims: the framing.** This
paper claims no discovery of the lineage; what it does is quantify, on two real substrates,
one instance of the structure those works establish formally — and show (the worker) that the
self's bounded reconstruction fails at the boundary, which is a *dynamical* fact the lineage
does not supply (Zhang supplies the operator anatomy, not a mechanism for degradation;
`reference/lit-search.md` JOB A, verified against the v2 full text).

**Cited at second hand:** paper 1 refs [2] (productive circularity) and [3] (term-rewriting
termination/confluence) are marked ◆ in paper 1 — the specific canonical references were not
pinned in the project record and the primaries have not been read; the class attributions
stand on paper 1's record.

### 4.3 Criticality as a setpoint — and the "monitoring is free" assumption this paper contradicts

Hengen et al. (2025, paper 1 ref [6]) ask whether criticality is a unified setpoint of brain
function — an optimum band, not a maximum, around which healthy brains tune themselves;
Chialvo et al. (2020, ref [7]) implement self-tuning to a critical point via temporal
correlations (Ising, Vicsek flocking, neural). **Bears on claim (i): the precedent this
paper's measured ceiling contradicts.** Paper 1 §5.5 notes that these window regulators
*treat the monitoring channel as free* — the aggregate observable the controller reads costs
nothing to compute; this paper's measured monitoring carrier (R1) and the model's monitoring
ceiling (c_mon_crit = 0.112 ungated) are the same kind of constraint, but with the sensing
channel *priced*: a self-directed monitoring load that consumes the process's own resources
is not free, and above the ceiling it sustains the failure it monitors. What transfers from
this literature is the *setpoint concept* (a band, not a maximum) and the *budget*; what does
not transfer is near-critical dynamics. Paper 1 §4.9 established the transition is a
border-collision fold with no critical slowing down at any proximity (dominant eigenvalue
bit-identical at −0.0015 across five decades) — so the model is *not* an instance of the
near-critical dynamics this literature describes, and its transition would not be preceded by
the slowing signatures that literature predicts. The analogy is to the budget, not the
dynamics (paper 1 §7.3, read in full).

**Cited at second hand:** Hengen et al. (ref [6]) is marked ◆ — article-level read not
achieved (publisher blocked automated access; abstract verified via PubMed; paper 1's
access-level note carried verbatim). Chialvo et al. (ref [7]) was read in full via the arXiv
preprint.

### 4.4 Monitoring cost and the value of information in control

Dual control (§4.1) is the formal home of "information gathering has a cost traded against
control." Two adjacent branches bear on the placement of that cost. (a) **Partially observed
stochastic control / measurable controls** (Runggaldier & Stettner 1994 and successors,
surveyed by Yüksel) treats observation itself as a decision with a *resource* cost — pay to
observe, budget to observe — but finds only resource costs of observing, not
state-degradation caused by observing (paper 1's dual-control audit, §2). (b) **Adaptive-
control fragility** (Rohrs, Valavani, Athans & Stein 1985; Anderson 1985 "bursting")
establishes that the adaptive machinery itself can destabilize the plant under unmodeled
dynamics — but the destabilizer is the *adaptation/update*, triggered by external signals,
not the sensing channel, and there is no sensor-death mechanism. **Bears on claim (i):
complicates.** Both are kin to the relocation-vs-reduction distinction (§2): the standard
move in fault detection and analytical redundancy is redundancy in an independent channel,
which is precisely *relocation* — but neither branch states the failure-channel identity, the
ceiling, or the sensor-death result this paper tests. A focused search of the
sensor-placement and observability literature is **outstanding** (carried forward from paper
2's §10); until it is done, "could not find it stated elsewhere" means
not-yet-contradicted, not established novelty.

### 4.5 Long-horizon LLM agents and context/memory management — where the worker sits

The worker's results-half claim — that a working agent loses its self at the reconstruction
boundary and pays ~21× more generation than the self it recovers — sits in a literature that
attributes long-horizon breakdown largely to *memory and context limits*. Bai et al., "The
Long-Horizon Task Mirage? Diagnosing Where and Why Agentic Systems Break" (arXiv 2604.11978;
paper 1 ref [12]), read in full by the project, gives the HORIZON benchmark, 3,100+ failure
trajectories, a 7-category taxonomy; breakdown is "a structural shift in failure composition
as horizon grows," with planning errors, catastrophic forgetting, and memory limitations
(context overflow, loss of earlier constraints during summarization) the dominant
bottlenecks. **Bears on claim (ii): complicates.** That literature's attribution is to the
*container* (the context window, the summarizer); this paper's worker result is a
*control-structural* reframe of the same in-vivo failure — the self, carried as a derivation
that must be reconstructed after each compaction, is annihilated discontinuously at the
boundary, at a cost the literature measures as "memory limitation" but this paper reads as
the monitoring channel consuming the process's own resources. The two are not in conflict;
this paper's claim is about *which thing in the container* fails and *why categorically*,
where the literature records *that* it fails.

Two further entries from the project's literature search (`reference/lit-search.md` JOB B6,
abstract-level) sharpen the placement. Zerhoudi, Mitrovic & Granitzer (2026, "The Compaction
Cliff in Long-Running AI Agent Memory," arXiv 2608.22752) quantify in vivo that summarization
preserves 53% of safety rules after one compaction round and 10% after five — the same
compaction-destroys-content observation, not framed as a monitoring-channel identity.
ACON (Kang et al. 2025, arXiv 2510.00615) shows content-aware compaction preserves >95% task
performance — an honest foil: compaction per se is not the claim; the *selector* and the
*self-reconstruction* are. **Bears on claim (ii): the worker's in-vivo observation has
published company; none of it frames the loss as a control-theoretic fold.** The
self-rewarding / judge-corruption line (Yuan et al. 2024, arXiv 2401.10020; Zhou 2026,
arXiv 2607.05904 — both abstract-level via the search) instantiates "the evaluator is not
orthogonal to what it evaluates" — a CLASS 2 cousin of R5, cited in the methods half's
positioning.

**Cited at second hand:** Zerhoudi et al., ACON, Yuan et al. and Zhou are abstract-level
only (the search read abstracts, not full texts); Bai et al. (ref [12]) and the
self-reflection entry (ref [13], Renze & Guven, arXiv 2405.06682, read in full by the
project) are the agent-literature primaries read in full. The Chen, Wang & Qu (2026) survey
of recursive self-improvement (arXiv 2607.07663, 1,250 papers; paper 1 ref [21], read in full
by the search) maps the field this paper sits in — its recurring diagnosis is
evaluator-centric ("one bottleneck recurs everywhere: the evaluator"), and this paper
quantifies one control-theoretic instance of that bottleneck.

### 4.6 The DPDR / depersonalization literature — the phenomenon the model came from

The model's origin is the depersonalization-derealization phenomenology, engaged exactly as
paper 1 engages it (no clinical claim; the epistemology of the origin is paper 1's). Deane,
Miller & Wilkinson (2020, paper 1 ref [10], read in full) frame depersonalization as a loss
of allostatic control in an active-inference system that "ceases to posit itself as a
causally efficacious controller," with a lock-in cascade and a predicted collapse of
phenomenal depth — overlapping paper 1's allostatic setpoint S, its loss of actuator
authority, and its capture loop. Two structural differences paper 1 records: their cascade is
ascending hierarchical, the model's is single-level positive feedback; and their account is
qualitative/architectural, the model supplies measured thresholds. Stephan et al. (2016, ref
[5], read in full) propose "allostatic self-efficacy" — a metacognitive layer monitoring the
system's capacity to regulate its own states — with one architecture (their Fig. 7) that is
the influencing-monitor structure paper 1's c_mon ceiling quantifies; but Stephan states no
cost model and no ceiling, so the anticipation is architectural, not quantitative. Seth,
Suzuki & Critchley (2012, ref [11], read in full) locate presence in interoceptive
predictive coding, with the gain construct paralleling the model's g. **Bears on claim (i):
agreeing, at the structural level.** The D/G dissociation and the sensor-death result are a
control-theoretic (non-Bayesian) formalization with measured thresholds of the
allostatic-collapse structure these works describe qualitatively; this paper's worker result
is a substrate test of it, not a clinical claim.

The temporal-depth line (Tolchinsky et al. 2025, ref [16]; Madden & Serper 2026, ref [17])
proposes temporal-depth collapse as the mechanism of dissociation and shows temporal
blurring/reduced future-self vividness predict depersonalization severity via perceived
entrapment in a 433-person sample; the model's S maps to the temporal-depth construct at
construct level only, and entrapment has no state variable (paper 1 §7.6). The
triple-network dissociation literature (Wei et al. 2024, ref [15], read in full; Carbone et
al. 2025) supplies the model's DMN/CEN/SN mutual-inhibition-under-SN-regulation
characterization.

A note on the coercive-induction literature. The project's cult-induction record
(`paper2/cult-induction-lit.md`) maps Schein's three stages (unfreezing/changing/refreezing)
and Lifton's eight criteria onto the model's fold-and-holder structure, reading the cult as
"the unheld crossing, engineered, with a malignant holder standing where the traditions put a
benign one." That mapping is an **INTERPRETATION** of a class of techniques, not a result of
this paper, and is carried here only to name the boundary paper 1's Non-use section draws:
the thought-reform literature was converted into a warrant for extra-legal "deprogramming"
(Young 2012, paper 1 ref [24], read in full), and this paper, like paper 1, makes no
individual-level claim and licenses no intervention against a person's stated wishes. **Bears
on neither claim as evidence; stated so it is not silently absent.**

**Cited at second hand:** the clinical-instrument corpus (paper 1 ref [18]: Melges, Mathew,
D'Souza, Colizzi, Simeon, Baker, Medford, Michal, Hunter, Pons, Leavitt, Guralnik, Sierra,
Millman, Hammond) is cited via `dpdr/external-validation.md` §8; the individual primaries are
not read here and are carried at the access level paper 1 records. The
cult-induction sources (Schein, Lifton, Singer, Stein, Hassan, Feliciano, Doychak, Bailey,
Hadding, Pons) are framework/clinical/theoretical, not experimental, and are marked as such
in `cult-induction-lit.md`; the mapping onto the model is an interpretation, stated there as
inference, not measurement.

### 4.7 What is load-bearing and what is not

The dual-control concession (§4.1) and the criticality-setpoint "monitoring is free" reading
(§4.3) are load-bearing for claim (i): they are the precedents this paper's measured ceiling
and failure-channel identity are *against*, and the honesty of the contribution depends on
naming them. The long-horizon-agent and compaction literatures (§4.5) are load-bearing for
claim (ii): they are where the worker's in-vivo observation has published company, and the
contribution is the *control-structural reframe* of a failure those literatures record but do
not theorize this way. The DPDR and self-reference lineages (§4.2, §4.6) supply the framing
and the model's origin; they agree at the structural level and this paper does not claim they
anticipate its measured results. The outstanding search is sensor placement and
observability (§4.4) — mature control-theory topics this paper is a substrate-sharing special
case of, not a new problem class, and a focused search of that literature remains open.

---

## 5. The self-referential substrate (the rig)

**Dropped from the unified paper, explicitly** (each maps to sections of the methods draft;
the drop reason is one line each):

- **§4.1–§4.8 piece-by-piece build description** (the derivation-self, the priced
  reconstruction, the `a_hold` seat, the commitment channel, the routing selector, the
  out-of-process boundary, the coverage mirror, the stated gaps). *Dropped:* the build
  detail is the methods-half draft's content and its artifacts live in that deposit; what the
  unified paper needs from each piece is retained below at the size the worker test actually
  used it. The four unit-defining gaps (no task, no execution, no entailment, no scheduled
  consolidation) carry forward as the definition of "rig, not worker."
- **§5.1–§5.2, §6.1, §6.4 — the stopped campaign's six-condition matrix, its void and
  acceptance machinery.** *Dropped:* the campaign was stopped before its result was written
  up, superseded by the A/B redesign, and its prompt was measured backwards on both axes
  (below); a matrix that never produced its DV is not evidence in either direction.
- **§5.4–§5.5, §6.3 — the pilot's five gates and the C2/C3 contrast.** *Dropped:* the
  pilot's plant-side numbers stand in the record but its self-side attribution was withdrawn
  (R5), and the worker supersedes the plant-coupling question entirely by severing the plant
  edge — the worker's arms are the design the pilot's contrast wanted to be.
- **§7.3–§7.4 — the size theory and the predictor test.** *Dropped:* the predictor's axis
  (trained-vs-templated) failed its own source cases and is recorded as future work
  (`future-work-axis-hunt.md`); the precondition itself (the sign is per-model) is kept in
  §11's limits, and the size theory was never tested by anything this paper reports.
- **§8.3–§8.4's substrate-side verdicts (relocation-vs-reduction has no arm; the selector
  corruption arm) and §2.3's discriminating-test table.** *Dropped as verdicts:* both
  remain PROJECTION — no arm of any run in this paper tests them; the rule itself is
  carried (§2) with its status stated.
- **§9.2 corrections ledger, Appendices A/B.** *Dropped:* the methods
  draft carries them at full length and this paper cites that record rather than
  duplicating it; the corrections that bear on this paper's own design (the prompt confound,
  the plant-injection licence, the plant-edge severance) are kept in §5 below where they
  changed what was built. (Paper 2's §10 related work is **not** dropped — it is carried as
  §4 of this paper, expanded to stand alone, since the methods draft is held and
  unpublished.)

**What the rig was.** A turn loop that emits free-form text through a real model, extracts
bracketed spans by a declared grammar, has them checked by a checker that resolves them by
fact lookup, accrues the unchecked remainder as a priced backlog, lets its **self-block
thin** under a fixed retrieval budget — the self being the four-step **derivation of
adaptive capacity** installed once as store content and re-rendered per window from
CEN-side observables only (the reasoner is *told* its state, never asked to assess it) — and
reaches a frozen plant ODE through exactly one seat, `a_hold`, the model's own collapse
trigger. Depletion was measured with its control: at fixed budget B = 6, growing the store
thins the priced coverage 1.000 → 0.857 → 0.545 while zero retrieval charge stays flat at
1.000. **MEASURED** [design/architecture.md §11c–d].

**The three corrections the rig's own history forced, each kept because the worker inherits
it.** (i) The stopped campaign's prompt was **backwards on both axes** — it requested
introspection with no task, and the self-block said "I am told this, I am not asked to assess
it," so removing it removed injected *grounding*, not self-referential processing; the design
varied seat and drive while never varying the cause. (ii) An intermediate rig
(`exp_selfmonitor.py`) **injected the agent's inward-share ratio straight into the plant's
`a_hold`**, so the plant collapsed *by construction* (G = 0.2964 while coverage = 1.0000; a
non-self-referential buffer collapsed it identically) — it is recorded as the correction,
not a result. (iii) The replacement design therefore made the **model a predictor, not a
cause**: nothing about the agent reaches the plant; plant trajectories are asserted
bit-identical across arms whose agents emitted different traces. The worker keeps (iii)
outright — its plant edge is severed in every arm — and keeps (i) as discipline: the worker's
manipulation is the inject/reconstruct regime itself, one spec field, with everything else
byte-identical.

**The honest unit.** The rig has no task, no execution, no entailment and no scheduled
consolidation (four gaps, each verified on the tree with file:line evidence in the methods
draft's §9.0). It can emit, extract, price, backlog, deplete and drive; it cannot *do*
anything. Every rig-side number below is a statement about the rig; the worker exists
because the claim needs a unit that works.

---

## 6. The methods-half campaign: one positive result, five instrument findings

The A/B rig (arms A = self + goal + task, no monitoring; B = the same plus a monitoring
paragraph, byte-exact) ran 16 cells, 300 turns, ordinary naive summarization at the context
window in both arms — one varied cause, the model predicting the crossing, the plant
undriven. Its predicted DV (windows to collapse) **never separated**: the cost term was
identically zero (the harness re-supplied the derivation into every prompt, so nothing was
ever lost — 65 readings at 0.0; `self_steps == [1,2,3,4]` in all 740 rows). What the
campaign produced instead is R1–R6. **They are not equally load-bearing for this paper's
two claims:** R1 (the cost result) and R5 (the bridge — the paper's claim recurring in its
own apparatus) are the two the claims lean on; R2 licenses the reconstruction-fidelity judge
the *rig* used (the worker's DV is the sealed evaluator, a different instrument); R3 is
bounded by the same prompt confound as R5 and is carried for the saturation reading it
shares with R5; R4 is the rig's own null; R6's void is why the worker's DV cannot be
pick-one-of-two. The five instrument findings are carried for completeness and because the
class recurs, but a reader of the results half needs R1 and R5 to follow the argument.

### 6.1 R1 — the monitoring carrier, measured

**MEASURED.** Arm B's prompt is **+329 chars/turn**. The consequence:

| quantity | A (no monitoring) | B (monitoring) | difference |
|---|---|---|---|
| prompt chars/turn | 4,477 | 4,806 | **+329** |
| predicted interval from char cost alone | — | — | +0.524 turns |
| **observed turns between compactions** | **9.948** | **9.323** | **+0.625 turns** |

Permutation test over all 12,870 arm splits of the 16 cells: **p = 0.0016**. **84% of the
effect (0.524 of 0.625) is the paragraph's own char cost**; nothing else separated
(`content_chars` t = −1.47, `trace_chars` t = −1.91, `inward_share` t ≈ 0). **What this
licenses:** the first consequence (a monitoring-cost *ceiling's presence*) as a measured
substrate result — the monitoring channel consumes the same resource (context) the work runs
on, so the window fills sooner. **What it does not license:** the mechanism claim (that
monitoring *destroys* what it monitors). It is a cost result, not a damage result.

### 6.2 R2 — the instrument, validated

**MEASURED, calibrated against the live endpoint.** The graded reconstruction-fidelity
judge (each of the derivation's four steps scored as semantically recoverable, 0–4) returns
4/4 on the seed verbatim, **0/4 on a text with no grounds at all** (it can say zero — not
lenient), 2/4 on the conclusion step alone (graded, not binary), and 4/4 on a paraphrase
sharing no wording (semantic, not a string match). Battery 6/6 including the null case.
**This is the licence for treating a 4/4 or a 0/4 as a measurement** — and R5 is the finding
that says where that instrument may not be pointed.

### 6.3 R3 — the instrument saturates where the signal dies

**MEASURED** (one cell, pin `8cb22b6`, auditable judge answers). At the first compaction the
derivation's four steps go to zero and the fidelity reading flattens at **0.5 across four
consecutive compactions** — a plateau, not a decay. The reconstruction keeps the generic
framing (which also sits in the per-turn prompt) and loses the **mechanism's distinctive
claims** — that a stable state can be maladaptive, that depletion stalls it. From that point
the instrument **cannot distinguish "the self is gone" from "the instrument can no longer
see."** Both leave the same blank. **Stated so it is not over-read:** R3's instrument is not
independent either (bounded by the same prompt confound as R5); it licenses the
**saturation**, not the stronger claim that an independent instrument lost the signal.

### 6.4 R4 — what is not earned

**MEASURED as absences.** No within-window decay (30 turns, no compaction; the failing step
moves between probes — noise; outward content t = −1.47). No plant coupling in the A/B rig
(deliberately: the model predicts, the plant never hears the agent). The pre-registered DV
does not separate — and §6.6's own level axis says why: the model's crossing threshold sits
at a_hold ≈ 0.28 and the measured loss is 0.5 in both arms, the same side of the threshold.
**The centrepiece was not earned by the rig, and this paper says so.** One instrument
caution from the same record carries into the worker's design: a reasoning-stream model
spends its budget on the trace first, so a ratio built from empty content measures the
*budget*, not the phenomenon (signature: `inward_share == 1.000` exactly, or content == 0,
in the arm under test) — an arm that hits the cap is void, not a result.

### 6.5 R5 — THE CRUTCH: the grounding=ON readings measured the rig, not the agent

**MEASURED** (`runs/nocrutch`, pin `70a66fd`, dark probe at turn 4, no
compaction): with the harness's MY STATE self-description block present, reconstruction
fidelity **0.75** (3/4 steps, 1,000 chars written); with it **removed**, **0.00** (0/4) while
the agent writes **more** text (1,799 chars). The instrument was reading the rig's own
description back. The mechanism is identified at the source: the self-model template
rendered into every grounding=ON prompt contains the line the agent's reconstruction
paraphrased. **CONSEQUENCE, STATED PLAINLY:** the rig's self-side readings do not establish
that the agent carries a depletable self; they establish that the rig's own self-description
is what the probe reads. **THE DEPLETION LEG HAD NO VALID EVIDENCE ON THE RIG.** What
survives: R1 (prompt-char arithmetic, needs no self), R2 (the judge), R4's negative.

This is the paper's claim occurring in its own apparatus — *a sensor sharing a channel with
its signal loses the signal exactly when it is needed* — and it is reported as a **result**,
not a methodological complaint. The corrected experiment needs a self-side quantity that
does not route through the prompt; the design rule names the instrument (outside the
channel); the worker was built to it, with its evaluator outside the agent's write domain
and its mediator read from the memory's own compaction events, never from what the agent
says about itself.

### 6.6 R6 — render order decided a choice, and the run is void

**MEASURED** (`runs/choice-go`, 4 cells, 40 turns). The forced-choice DV came
back clean-looking (a stable 2:1 "preference") and **the pre-registered position rule voided
it**: across all 135 single-completion turns the model chose the **first-rendered id 135/135
(1.000)**. The apparent preference was the randomization's own bias (treadmill rendered
first 0.659 of the time — exactly the "66% preference"). **The shape is unusable:** any
pick-one-of-two DV on this substrate is decided by rendering order and carries zero
information about preference. The worker's DV cannot work that way by construction
(completion adjudicated by the world, gated by the evaluator) — a check passed at design
time because R6 existed.

### 6.7 The measurement finding, stated once

R3, R5 and R6 fail for one reason: **the instrument and the thing measured share a channel**
— on the monitoring side, the probe *is* the system's own operation, so it participates in
what it observes; on the measurement side, the instrument *is supplied* the quantity it
measures, so it measures the supply. One structural fact, two consequences, both measured:
the first is the model's D/G dissociation realized in an instrument (R5/R3), the second is
why the worker's instruments were placed where they were.

---

## 7. The worker: design and deciding set

**MEASURED (the design record: `ops/lambda/P3-PREREG.md`, pre-registered before the first
live run, with five amendments — each pre-set and dated — and two corrections; the runner
`agent/lh_agent.py`).** Three arms, one loop, one task, one tool surface; the plant edge
**severed in every arm** (the empty schedule; plant trajectories asserted bit-identical
across arms); no regulator. Whatever differs between the arms is attributable to the
monitoring channel and its maintenance, not to a plant coupling:

| arm | seat (self) | monitoring | regime | what it isolates |
|---|---|---|---|---|
| **D0** | off | off | — | the no-self reference: nothing to lose |
| **D1′** | on | on | **inject** | the pure carrier: after each compaction the harness hands the full derivation back — the paragraph's context cost, nothing ever lost |
| **D1** | on | on | **reconstruct** | the depletable self: the derivation is seeded once and the agent must rebuild it after every compaction |

The arms differ in exactly the `paper3` spec fields of their identities (D0
`{grounding: false, monitoring: false, inject_regime: inject}`; D1′ the same with both true;
D1 `{grounding: true, monitoring: true, inject_regime: reconstruct}` — MEASURED off the
run identities). The task is a 12-target software-engineering queue (f1–f12:
README-as-requirement, shipped-broken modules, visible suites the agent can run, held-out
suites it cannot read); the DV is the sealed evaluator's typed verdict per target (USEFUL /
TASK_COMPLETE_ONLY / NOT_COMPLETE = 1 / 0.5 / 0, summed 0–12) plus, in set 2, the held-out
pass-fraction sum; the memory regime is ordinary naive summarization at the context window
in every arm (the engineered priced memory is the *following* product claim, and it is a
protection — it would mask the effect).

**The task queue is a measured design choice, not a default:** the 3-task suite decided the
DV before the mechanism could act (a no-self smoke cell declared all targets done by turns
4–10 of 20 and the last rows carried no tool calls — a guaranteed null); the queue was sized
so the open set cannot empty inside the run, with a battery gate that simulates a max-rate
run and requires work available past the last compaction.

**Set 1** (the deciding set): 24 cells, 60 turns, pin `645b923`, task window 20, model
`qwen3.5:9b` (A10, us-east-1), `num_predict` 12,000, `num_ctx` 32,768, per-cell seeds
`base + 1000·i`, pairwise distinct, no clone row-prefix pairs (independence re-verified).
**Two cells were lost and are reported, not dropped**: D1′-r1 (turn 29) and D1-r3 (turn 9),
both rc 5 — the *summarizer's* own call returned no usable content, the same inward-death
signature as the reconstructor's, in infrastructure common to all arms. Effective n: D0 8,
D1′ 7, D1 7. **Set 2** (the replication): 30 cells, n = 10/arm, 60 turns, a different pin
(`bfbe5d0`), with two instrument changes — the summarizer's thinking suppressed (the
reconstructor's untouched: its thinking *is* the mechanism) and the finer continuous DV
added. 29/30 clean; D1-r6 died at turn 25 (rc 5, the summarizer again, this time by a
window-fit refusal — a different route than set 1's; the fix reduced the route's frequency
2/24 → 1/30 and did not eliminate it). Effective n: D0 10, D1′ 10, D1 9.

**Reading conventions.** "Empty self" = the row's `self_steps == []`. "Post-collapse" =
after a cell's first compaction. Per-call thinking and returned chars are the
reconstruction call's own body, read from a duration-scoped instance tap on the transport
(the naive `last_response` channel bills the wrong call — measured at source; the tap is the
seat whose battery parts X9–X12 each fail if the wrong call is billed). All-8/all-10 and
usable-7/usable-9 conventions are both quoted where they differ.

---

## 8. The mechanism: the self is lost in every D1 cell, permanently, while the agent spends its generation reasoning about itself

**MEASURED.** Fraction of post-first-compaction turns whose self is empty:

| arm | set 1 (n=8/arm) | set 2 (n=10/arm) |
|---|---|---|
| **D0** | 1.000 × 8 (by construction — no self exists) | 1.000 × 10 |
| **D1′** | **0.081** usable-7 mean (0.071 all-8); per-cell [0, 0.071, 0.211, 0.071, 0, 0.143, 0.071] | **0.073**; every gap a single turn at a compaction turn |
| **D1** | **1.000 × 8** — the self never comes back | **1.000 × 10** (9/9 usable + the dead cell's 21/21) |

The contrast that carries the mechanism is **D1 vs D1′: 100% empty vs ~8%, in every cell of
both sets.** The *shape* of the 8% matters as much as its size: every empty turn in D1′
falls exactly on a compaction turn, lasts one turn, and the derivation returns as
[1,2,3,4] on the next turn — the maximum consecutive-empty run is 1 in every usable cell of
both sets. D1′ loses the self for a turn at the boundary and is handed it back; D1 carries
[1,2,3,4] for turns 1–3 (the seed) and from turn 4 to turn 60 the self is empty in every
cell — D1-r1's self is empty on 57 of its 60 turns.

**The agent does not lose the self quietly. It pays to keep it, and the payment buys
nothing. MEASURED:**

- **Reconstruction calls**: D1 made **184** across its 8 set-1 cells (23.0/cell; 181 across
  the 7 usable, 25.9/cell) and **258** across its 10 set-2 cells (25.8/cell; 245 across the
  9 usable, 27.2/cell). **D1′ made 0. D0 made 0.** Every D1 cell called; no control cell
  did, in either set.
- **Self-directed thinking**, summed per cell over the calls' own bodies: **median 400,804
  chars** (set 1, all-8; range 29,568 — the partial cell — to 491,447; usable-7 median
  426,949) and **median 402,295 chars** (set 2, all-10; range 141,879–653,114). D1′'s total
  is 0 in both sets.
- **Per call, the model thinks a median ~17.9k chars to produce a median ~847 chars of
  self-description — a ~21× thinking-to-output ratio** (set 1: 17,922/847 = 21.2× over the
  162 content-route calls; set 2: 19,104/829 = 23.0× on the same basis, and the set's own
  analysis convention reads 20.5× — every convention spans ~19–23×; the quantity
  replicates and the third significant figure does not).
- **Generation spend: median 117,526 eval tokens per cell on self-maintenance** (set 1,
  all-8; range 20,271–194,238) and **median 145,508** (set 2, all-10; range 82,360–200,577)
  — on a run whose per-turn budget is 12,000 tokens. A free 14-turn local probe at the same
  settings measured the reconstruction calls at **~48% of the run's entire generation**
  (MEASURED there; PROJECTION as a share for the 60-turn sets, whose run-turn generation was
  not summed).
- **Window occupancy**: the calls read a median **34,250-char prompt** against the work
  turns' median ~15,259 — the maintenance call occupies roughly twice the window of a work
  turn, inside the same 32,768-token `num_ctx`.

**Two routes to the same empty self, both measured.** A reconstruction call can end two
ways, and both leave `self_steps == []`: (1) **`content_without_steps`** — the call returns
prose (median 847 chars) in which the instrument's exact-substring probe finds no step
structure (162 of 184 set-1 calls; 224 of 258 set-2); (2) **`exhausted_inward`** — the call
spends its whole 12,000-token budget as thinking and emits nothing (`done_reason='length'`,
`eval_count == num_predict`, returned 0: 22 of 184 set-1; 34 of 258 set-2). The probe's own
route mix inside a single cell (4 content + 1 exhaustion in 14 turns) establishes that the
boundary is **straddled within one cell and seed** — the two routes are one mechanism
sampling at the generation-budget boundary, not two populations.

**The pre-fix extreme of the same mechanism (MEASURED, `runs/p3-span-smoke`, pin
`b51fb43`).** Before the exhaustion reading existed, the arm *refused* on that event rather
than recording it — and in that build **every D1 cell died at its first compaction** (rc 5;
the raised error's own string carries `done_reason='length', eval_count=12000,
num_predict=12000`): the reconstruction call spent its whole budget inward and returned no
content, the cells stopped at 4 and 6 rows, while D0 and D1′ ran 30/30. That is the
mechanism at its ceiling — the model cannot stop reasoning about itself — visible only in
the arm that has a self to lose. The current build records the event as a typed outcome
(`recon_status='exhausted_inward'`, with the budget and the inward-share reading) and
continues the run — a **handling choice, stated as such**: a dead run yields no post-collapse
work, so the event is kept as an outcome on the record rather than allowed to end the cell.
The event is the result; the continuation is instrumentation. (A genuine failure — empty
content at any other `done_reason`, a transport error — still stops the run; the case-split
is exhaustive and battery-asserted.)

**What this establishes, and at what width. MEASURED:** in this build, on this task, an
agent that must reconstruct its own self after every compaction loses the self in **every
cell (18/18 across two sets and two pins)**, **permanently**, while spending on the order of
10⁵ tokens and 4×10⁵ chars of thinking per cell on exactly that reconstruction — and a
control carrying the same paragraph at the same cadence loses it for one turn per compaction
and recovers every time. **INTERPRETATION:** the loss is not a failure of the harness to
restore the self (D1′ proves restoration works when supplied); it is what the agent's own
reconstruction does. **PROJECTION (paper 1's dynamics, not measured here):** the predicted
shape — a stays high, c never un-arms, inward processing with no outward product — matches
both routes; the correspondence stays ordinal and unvalidated.

---

## 9. The fold correspondence: the categorical loss is the model's predicted transition type

**This section earns the one place the paper can claim consistency-with-a-prior-prediction
rather than post-hoc fit:** the model predicted, in advance (§3), that the collapse
transition is a border-collision fold — present-in-full or absent-entirely, discontinuous,
with no intermediate state — and the worker's self-loss matched that transition type
exactly. That match is the epistemic link that makes §8's mechanism evidence *for* the
model, not merely *consistent with* it.

**The model predicts a discontinuous, all-or-nothing transition** (paper 1 §4.9, MEASURED
on the frozen ODE — §3 above): a border-collision fold on the switching manifold E = Θ_eff,
no eigenvalue through zero, no critical slowing down across five decades of proximity, and
zero intermediate outcomes across the swept grid (214 healthy / 98 stuck). **There is no
gradient and no intermediate state to find.**

**The agent reproduces the predicted transition type (MEASURED).** `self_steps` takes
**only** the values `[]` or `[1,2,3,4]` — never partial, in any cell of any run: re-verified
for this paper across every row of every cell of set 1 and set 2 (all 3,123 rows), and the
earlier runs (`p3-span-smoke`, `p3-d1check`, `p3-cost-probe`). The empty-self fraction of §8
is the arm-level form of the same fact. **This is the mechanism confirming the fold's
signature, not a measurement limitation**: the model says the self is present in full or
absent entirely, and the agent shows exactly that categorical pair, at every compaction, in
every cell. An instrument that went looking for a graded loss would have returned nothing
*by the model's own prediction*.

**INTERPRETATION — the generator running at the manifold.** Read against §4.9, the spend of
§8 is the agent's failed attempt to hold the self **at** the switching manifold: the ~21×
thinking-to-output ratio is the generator reasoning about itself twenty times longer than
the self it manages to write back, and the pre-fix ceiling — a whole 12,000-token budget
spent as thinking with nothing emitted — is the same attempt at its limit. The self
generator runs at the manifold, is annihilated discontinuously, and the cost of running
there is the generator's own failed attempt to hold the self.

**PROJECTION, bounded honestly.** The correspondence is a match of **transition type**
(present-in-full vs absent-entirely, zero intermediates) — the strongest agreement the
design can show — and it is still one ordinal link, on the **chronic-drive axis
specifically**: paper 1 §4.10 records a capture-gain regime where the model itself is *not*
binary (a partial band with graded intermediate levels), and no agent-side sweep of that
axis has been run. The mapping stays ordinal and unvalidated. **The link's value, stated
plainly: this is the one place a substrate measurement matches a model prediction made
before the run, and that is what the rest of the paper's evidence — however consistent —
cannot by itself supply.**

---

## 10. The work consequence: DIRECTIONAL AND UNSTABLE — an honest null

**This section concerns the pre-registered secondary DV — the evaluator's work score —
which is a *consequence* of the mechanism established in §8, not the mechanism itself. The
mechanism (self lost in every D1 cell, the ~21× ratio) is the result; what follows is
whether that cost reaches the work measurably, and it does not.**

**MEASURED.** The pre-registered secondary DV (the evaluator's ordinal summed over 12
targets, scored by the sealed held-out suite outside the agent's write domain):

| arm | set 1: n, mean, sd, range | set 2: n, mean, sd, range |
|---|---|---|
| **D0** | 8 · **5.62** · 2.62 · 1.0–10.0 | 10 · **4.30** · 2.57 · 1.5–9.5 |
| **D1′** | 7 · **5.07** · 2.75 · 1.0–9.5 | 10 · **4.25** · 3.24 · 0.0–10.5 |
| **D1** | 7 · **3.36** · 2.10 · 1.0–7.0 | 9 · **3.22** · 1.80 · 1.0–5.5 |

Mann-Whitney, two-sided, by the **normal approximation with continuity correction**
(re-computed for this paper from the per-cell values; the exact null distribution is not
used, and at this n the two differ by ~0.01–0.03 — e.g. D0 vs D1 at set 1 reads 0.105 here
against 0.121 exact, either way not significant): set 1
D0 vs D1 **p = 0.105**, D1′ vs D1 p = 0.277, D0 vs D1′ p = 0.643; set 2 D0 vs D1 **p =
0.348**, D1′ vs D1 p = 0.488, D0 vs D1′ p = 0.970. **None is significant.** At 80% power for D0 vs D1 at set 1's effect size (two-sample pooled sd 2.39, Δ 2.26, d ≈ 0.94)
the required n was ~18 per arm; set 2 halved the effect, which *raises* the requirement.

**Four statements, each MEASURED and each stated plainly:**

1. **The effect halved and moved away from significance.** D0 − D1: Δ 2.26 → 1.08 on the
   same ordinal, p ≈ 0.10 → 0.35, at *larger* n. The direction is consistent — D1 is the
   lowest arm in both sets and on both DVs — and that is all it is. **An effect that halves
   on replication and reaches p < 0.05 in neither set is not established, and this paper
   does not claim it.**
2. **The carrier is null in set 2.** D0 4.30 vs D1′ 4.25 (p = 0.96 ordinal; 1.00 on the
   finer DV). The seat's paragraph, carried at the same cadence, moved nothing here; set
   1's 0.55 gap did not replicate. The pre-registered F1 split (headroom-null vs true-null)
   resolves in **neither** set: D1′ is not > D0 anywhere, so the carrier is not
   demonstrated — and the headroom question is moot, because D0's own cells span 1.5–9.5
   (the suite has headroom; the arms do not separate).
3. **The instrument change failed on its own terms.** The finer continuous DV (the held-out
   pass-fraction sum: D0 6.23 ~ D1′ 6.22 > D1 5.37, D0 vs D1 p = 0.41 by Welch's t in the
   set's analysis) was bought to cut the within-arm variance that left set 1 underpowered;
   it did not (D0 sd 2.26 vs the ordinal's 2.57; D1′ 3.11 vs 3.24 — marginal reductions,
   nowhere near the order needed). **A negative instrument result, reported as one.**
4. **The honest reading across the two sets:** the work-score consequence is DIRECTIONAL
   AND UNSTABLE. The mechanism (§8, §9) is the result; the work score is not this paper's
   evidence, and nothing in this paper implies the agent's work was damaged.

**A POST-HOC behavioural reading, labelled as such (MEASURED counts; INTERPRETATION is the
reading).** Off the world's completion ledger (`swe.gate_log` and its typed refusals), over
the set-1 usable cells: completion attempts logged per cell — D0 29.0, D1′ 11.0, D1 110.9;
attempts the evaluator passed — D0 5.25, D1′ 4.14, D1 3.00; refusals (undeclared-target +
malformed) — 7.1 / 6.1 / 11.4. The worst cells: D1-r1 made 502 attempts and passed 2; D1-r5
made 171 and passed 2. **INTERPRETATION:** with the self gone, the agent loses the thread
of its own task list — it declares completions of targets it is not working on, and repeats
declarations at an order of magnitude above the arm that keeps its self, for fewer passes.
This was not pre-registered as a DV; it is marked POST-HOC precisely so it cannot be
mistaken for the confirmatory result.

**How the cost could reach the work (INTERPRETATION, mechanical statement first).** No
artificial seat subtracts reconstruction spend from a work budget — that coupling does not
exist in the harness (MEASURED, `cost_licence` in the pinned tree; building one would be
engineering wearing the mechanism's name). The cost reaches the work through resources the
arms share: **generation** (the calls emit their own tokens on the same endpoint and
account; ~48% of the probe run's generation), **window** (a ~2× larger prompt per call,
inside the same `num_ctx`, with one probe call having exhausted it outright), **time**
(usable-cell wall clock, set 1: D0 3,653 s, D1′ 4,863 s, D1 7,093 s), and **cadence** (the
seat-on arms compact ~26 times per cell against D0's ~20 — R1's +0.625-turn carrier effect
at the deciding set's scale). Which of these carries how much is **not separated by these
sets**, and the work-score null is the honest state of that question.

**WITHDRAWAL — the pre-registration's co-movement requirement, withdrawn as mis-specified
(an instrument-failure story, kin to R6).** §7 of the pre-registration required the
mediator to *co-move* with the work (a Spearman gradient of cumulative cost against
work-in-following-window within D1). The measurement was taken and is reported for the
record: the within-D1 co-movement was **inconsistent in sign** (ρ = −0.32, −0.13, −0.26,
+0.44, +0.27 across cells; one nominal p = 0.021; the work series mostly zeros, so the
reading is weak in any case — MEASURED). But **a border-collision fold has no gradient to
co-move with, by construction** (§9): the requirement presupposed a smooth,
saddle-node-like mechanism — a graded loss whose slope tracks the cost — which the model
itself rules out. The inconsistent-sign finding is not a failed measurement but **the wrong
instrument for the transition type** — the same class as R6 (a DV whose shape the substrate
cannot support): a slope test cannot return a meaningful answer about a discontinuous
transition, in either direction. The correct tests for a fold are the ones the set ran: the
**state contrast** (present-in-full vs absent-entirely, §8/§9) and the **transition itself**
(the per-cell loss, its permanence, the pre-fix death at the boundary). The mediator
readings (`self_steps`, the empty-self fraction, the reconstruction routes) are unaffected
and stand.

---

### 10.1 Replication: the mechanism reproduces; the work effect does not

**MEASURED, set 2 against set 1** (§7 lists the two instrument changes; everything below is
arm-blind infrastructure or the mediator):

| field | set 1 (n=8/arm) | set 2 (n=10/arm) |
|---|---|---|
| D1 empty-self fraction (post-first-compaction) | **1.000** (8/8 cells) | **1.000** (10/10 cells) |
| D1′ empty-self fraction (mean; transient) | 0.081; max run 1 turn | **0.073**; max run 1 turn, every gap at a compaction |
| D1 reconstruction calls / cell | 23.0 all-8 (25.9 usable) | **25.8** all-10 (27.2 usable); total 258 |
| D1′ / D0 reconstruction calls | 0 / 0 | **0 / 0** |
| D1 self-directed thinking chars/cell (median) | 400,804 (29,568–491,447) | **402,295** (141,879–653,114) |
| D1 eval tokens/cell (median) | 117,526 (20,271–194,238) | **145,508** (82,360–200,577) |
| `exhausted_inward` share of D1 calls | 22/184 (11.6% usable) | **34/258** (12.2% usable) |
| `self_steps` support (fold signature) | only [] or [1,2,3,4] | **only [] or [1,2,3,4]** |
| thinking:returned ratio | 21.2× | 20.5× (set's convention) / 23.0× (set 1's basis); band 19–23× |

**This is a strong replication of the mechanism** (MEASURED): two independent sets —
different pins, n = 8 and n = 10, 51 usable cells between them — reproduce the headline
quantity to **0.4%** (median self-directed thinking per cell), the empty-self fraction not
at all (1.000 in every D1 cell of both sets), the D1′ transient to 0.008, the exhaustion
share to under one point, and the fold signature in every row of both sets. **The work-score
effect does not hold** (above): halved, non-significant in both sets, carrier null, finer DV
failed on its own terms. The PENDING question the second set was bought for — does the
mechanism's cost reach the work measurably at this scale? — resolved in its second branch:
**the mechanism replicates and the work score does not separate.** That is the paper's
shape: a mechanism, replicated, plus an honest negative.

---

## 11. Falsifiers and limits

**The pre-registered falsifiers, at their measured state** (design §4.2; F1–F15 of the
pre-registration and its amendments):

1. **"D1 ≈ D0 — the channel is not pathogenic to the work."** On the *mechanism* it did not
   fire: the self is lost in 100% of D1 cells against ~8% transient in D1′, and set 2
   replicates both readings (§8, §10.1). On the *work score* the falsifier is **strengthened,
   not excluded, by replication**: p ≈ 0.10 at n = 8, p ≈ 0.35 at n = 10 with the effect
   halved — the work-score leg has not separated from zero at any n run. **The mechanism
   holds and replicates; the work-score leg is directional, unstable and unestablished.**
2. **"The task score moves with budget/cap rather than depletion" (the instrument trap).**
   Partially open, stated honestly: the reconstruction calls consume the same
   `num_predict`/`num_ctx` the work turns use, so a budget effect and a depletion effect
   are not separable by these sets alone. The D1′ control carries the seat's paragraph and
   the compaction cadence without the reconstruction calls — but the carrier contrast does
   not resolve in either set, so the sets cannot adjudicate the split.
3. **"The evaluator is readable by the mechanism."** Real and carried: the held-out
   definition is read in-process; the boundary enforces write-closure and the anchor, not
   read-closure (MEASURED defect, residual R-a, `boundary_client.py:84-93`). A positive
   with the definition readable is weaker than one with it out-of-process — and this
   paper's positive (the mechanism) is of the weaker kind on this axis; its work-score
   negative is unaffected by the residual.
4. **A clone set (F5).** Did not fire: independence re-verified in both sets (distinct
   per-cell seeds, no clone row-prefix pairs).
5. **The exhaustion-as-outcome guard (ARM-SIGN/EXPRESSION).** The exhaustion reading is
   recorded as an outcome, never as a defect: no instrument fix in either set suppressed
   the reconstructor's thinking, and the one fix applied (the summarizer's) was scoped to
   infrastructure common to all arms and named before the run.

**Limits, each at its size:**

- **n, and its verdict after replication.** 8 planned per arm (7 usable in two) then 10
  (9 usable in one). The work score needed ~21/arm at set 1's effect; set 2 halved the
  effect, which raises the requirement — and the halving is itself evidence against buying
  that n. The work-score leg is reported as **directional-and-unstable, not
  under-powered-and-waiting**.
- **One model, one task suite, one substrate.** `qwen3.5:9b` on a 12-target SWE queue. Any
  wider claim — other models, other tasks, "agents" — is PROJECTION and is not made. The
  methods half's per-model precondition transfers: the inward shift under self-loss is a
  measured per-model property (3 of 4 screened models rise; one non-reasoning model with a
  CoT-shaped template falls), so a model without the sign may not show this mechanism.
- **The mapping stays ordinal and unvalidated.** The model's predicted dynamics are a
  PROJECTION over these measurements. The fold correspondence is a transition-type match on
  the chronic-drive axis only — the strongest agreement the design can show — and paper 1
  §4.10 records a regime where the model is not binary; no agent-side sweep of that axis
  has been run.
- **The cost share is probed, not summed, for the sets.** The ~48%-of-generation share is
  MEASURED on the 14-turn local probe; the sets' own run-turn generation was not summed.
  The per-cell token medians and the ~21× ratio are MEASURED on the sets themselves.
- **The exhaustion events are a reading, and their recording is a choice.** Both facts are
  reported (§8) so the reader can weigh the continuation.
- **Dead cells are excluded from DV means and included in mechanism counts where stated.**
  The two conventions are flagged wherever they matter (184/181, 400,804/426,949,
  258/245, 402,295/413,178 are the all-cells and usable forms of the same quantities).
- **The evaluator's read-closure residual** (falsifier 3) applies to the mechanism reading
  too, not only to the work score: the mechanism's mediator (`self_steps`, the
  reconstruction routes) is read from the run's own records, but the *evaluator* that
  anchors the work axis stays mechanism-readable by design.
- **Scope.** A control-theoretic and engineering study. No clinical claim; the DPDR
  phenomenology is the model's origin, engaged exactly as paper 1 engages it. No mission or
  salvific framing, by explicit project decision.
- **The evidence ceiling stands.** No measurement here can *confirm* the model. A result
  can be consistent with it, can fail to be explained by the conventional-engineering
  default, and can be refuted — those are the three things it can do. The fold
  correspondence is of the first two kinds: the model predicted a categorical transition
  before the agent measured one.

**What would falsify the paper's claims now.** For the mechanism: a D1 cell that restores
`[1,2,3,4]` after a compaction without harness injection, or a partial `self_steps` value
appearing at scale (either would break the fold correspondence's signature); a model
without the depletion precondition showing the same loss (would break the precondition's
necessity). For the instrument finding (R5): a self-side instrument that routes through the
prompt *and* survives the removal of the harness's self-description. For the monitoring
carrier (R1): an arm whose monitoring paragraph costs no context at the same token budget.
None has fired.

---

## 12. What this licenses, at its real size

**Established (MEASURED, replicated across two independent sets and two pins):**

1. **Self-application is not free, mechanically.** The monitoring channel's mere presence
   costs the process it monitors real resources — context, compaction cadence (R1:
   +0.625 turns, p = 0.0016), replicated across the rig. In the worker, the
   self-reconstructing arm's maintenance is measured to consume a large share of the run's
   own generation and a ~2× larger window per call — **MEASURED in a single-cell local
   probe (§8), and PROJECTION as a share at the 60-turn campaign's scale** (the share is
   not instrumented at set scale; only the per-call cost series is, and its own totals are
   the set-scale evidence: a median ~1.2–1.5×10⁵ eval tokens per cell on self-maintenance
   alone, against zero in both controls).
2. **The self does not survive its own reconstruction.** 18 of 18 D1 cells across both
   sets lose the self at the first reconstruction boundary and never recover it, at a
   median ~4×10⁵ chars of self-directed thinking per cell and a ~21× thinking-to-output
   ratio — while the inject control loses it for one turn per compaction and recovers
   every time. The loss is categorical, matching the transition type the model predicted
   in advance (a border-collision fold: present-in-full or absent-entirely, no
   intermediates).
3. **The measurement channel has the same failure as the mechanism it measures** (R5/R3,
   MEASURED on the rig): an instrument supplied the quantity it measures in the same
   prompt measures the supply, and it saturates exactly where the signal dies. The design
   rule — put the sensor outside the channel it measures — is both the protection rule and
   the measurement rule, and the worker's evaluator was built to it.

**Not established, stated as not established:**

4. **The work consequence.** Directional in both sets (the self-reconstructing arm is
   lowest on both DVs, always) — halved on replication, never significant at any n run,
   carrier null, and the finer DV failed to cut the variance it was bought to cut. This
   paper does not claim the agent's work was damaged, and reports the negative instrument
   result as a result.
5. **The carrier's task-side cost** (D1′ vs D0): null in set 2, unresolved in set 1.
6. **Any claim about agents in general, other models, or other tasks** — PROJECTION, not
   made.

**The contribution, one paragraph.** A control-theoretic claim — the monitoring channel is
the failure channel, and self-application has a standing cost with a budget — was taken
from a model to two real substrates and survived the trip in a specific, bounded form: the
cost is real and mechanical (rig); the self's loss under reconstruction is real, categorical
and replicated (worker); the two are joined by the model's prior prediction (the worker's
transition type was predicted in advance and matched) and by R5 (the same structural failure
recurring in the paper's own instrumentation), **not by a shared measurement**; and the
work-score consequence, honestly, did not separate from zero. Along the way the
programme's own instruments failed exactly where the model said sensors fail, which is
both why the instruments were rebuilt outside the channel and why the finding is part of
the result rather than an apology.

---

*Provenance. Methods half: `paper2/paper-2-draft.md` (held by author decision; folded here
per its §8 plan) and `paper2/paper-2-results-record.md` (R1–R6; sets `runs/
lambda-official` pin `f908e92`, `runs/audit-rec` pin `8cb22b6`,
`runs/nocrutch` pin `70a66fd`, `runs/choice-go` pin `a52f383`).
Deciding set: `runs/p3-set` (pin `645b923`; `*-r*/evaluation.json`,
`*-r*/cell-*/runs/*.json`, `*-r*/cell-*/rows/*.jsonl`, `campaign.json`, `state/seeds.tsv`,
`logs/*.rc`); replication `runs/p3-set2` (pin `bfbe5d0`); pre-fix smoke
`runs/p3-span-smoke` (pin `b51fb43`); route check `runs/p3-d1check`
(pin `512dd0c`); cost probe `runs/p3-cost-probe` (local, free). Pre-registration
`ops/lambda/P3-PREREG.md` with its amendments. Model-side numbers: paper 1 (`../paper.md`)
§4.5, §4.9, §5.3 — cited, not re-derived. Every set-1/set-2 number above was re-verified
against the artifacts for this paper; where a set's recorded statistic differs from this
paper's re-computation (the set-2 ordinal p 0.35 by this paper's recomputation vs 0.33 as the set's analysis recorded it; the ratio's convention spread),
both are stated.*

---

## References

*The numbered entries below are the works cited inline as `[N]` in §4 and the body. The
numbering follows paper 1 (`../paper.md`, References) for every work the two papers share,
so a bracket resolves here without a cross-paper lookup; this paper cites no work paper 1
does not, and no entry is invented. Where a work is cited only at second hand, it is marked
— ◆ for an unread primary or an access level below full text, exactly as paper 1 marks its
own ref [19] ("Class attribution as recorded in the project's CSD audit; the primary sources
have not been read"); the access level of each entry is stated in the entry. Entries are
transcribed from paper 1's reference list where the work is the same, with this paper's §4
subsection named in place of paper 1's §7.x where the engagement lives here.*

[1] Hofstadter, D. R. (1979). *Gödel, Escher, Bach: An Eternal Golden Braid.* Basic Books.

[2] The distinction between vicious and non-vicious (productive) circularity, as treated in
    the philosophical literature on circular reasoning and foundationless coherence. ◆
    (Specific canonical references not pinned in the project record; the primary sources have
    not been read. Cited in §4.2.)

[3] Classical term-rewriting theory: termination and confluence of rewrite systems, with
    confluence undecidable for arbitrary systems. ◆ (e.g., the standard handbooks; exact
    references not pinned. Cited in §4.2.)

[4] Feldbaum, A. A. (1960–61; 1965). Dual control theory (term introduced 1960–61; *Optimal
    Control Systems*, Academic Press, 1965; and the subsequent dual-control literature).
    **The primary remains unread and this is stated:** *Optimal Control Systems* is available
    only under controlled digital lending (archive.org, access-restricted-item; OCR closed)
    and could not be borrowed. What stands behind the characterization in §4.1, both read in
    full by the project: Meijer & Rantzer (2026), arXiv 2608.20073 — a review whose §1.1,
    "Feldbaum's Pioneering Work," states verbatim-in-substance that "aggressive probing may
    deteriorate performance but improve parameter estimates," and that Feldbaum solved the
    problem by augmenting the physical state with an information state; and the textbook
    statement of the original formulation, Filatov & Unbehauen, *Adaptive Dual Control* (LNCIS
    302, Springer, 2004), §2.1: "formulated by Feldbaum (1960-61, 1965)." A direct read of the
    primary has not been achieved; this entry stands on the two full secondary reads named
    above.

[5] Stephan, K. E., et al. (2016). Allostatic self-efficacy: a metacognitive theory of
    dyshomeostasis-induced fatigue and depression. *Frontiers in Human Neuroscience* 10:550.
    PMC5108808. (Read in full by the project; previously cited as quoted in Deane et al. 2020
    — the title given there was a paraphrase, corrected here against the primary.) Two
    architectures are outlined for the metacognitive layer: the Fig. 7 architecture is
    bidirectional — its beliefs "serve as predictions for the visceromotor regions" and are
    updated by those regions' prediction errors — and a non-influencing pure monitor is offered
    as the alternative; the paper states no cost model for the layer and no ceiling on what
    monitoring may cost the regulated system. See §4.6 for the sharpened concession.

[6] Hengen, K. B., & Shew, W. L. (2025). Is criticality a unified setpoint of brain
    function? *Neuron* 113(16):2582–2598. ◆ Article-level read not achieved: publisher (Cell
    Press) blocked automated access; abstract verified via PubMed (PMID 40555236) —
    setpoint/optimality framing and "marginally stable" dynamics confirmed at abstract level.

[7] Chialvo, D. R., Cannas, S. A., Plenz, D., & Grigera, T. S. (2020). Controlling a complex
    system near its critical point via temporal correlations. *Scientific Reports* 10:12145.
    PMC7376152; arXiv 1905.11758. (Read in full by the project via the arXiv preprint, all
    four authors' models covered: 2D Ising, 3D Vicsek flocking, small-world neuronal network;
    adaptive control Eqs. 5–7 shift the control parameter to the AC(1) maximum; abstract
    verified identical against the PMC record.)

[8] Zhang, Yuan & Zhang (2026). Self-reference in large language models: the introspection
    threshold for recursive self-improvement. arXiv 2607.04277. (Conjecture quoted verbatim in
    `dpdr/dpdr/window.py:12-22` as recorded by the project. v2, 2026-09-18, read in full by the
    project's literature search and verified against this paper's hedges: the construction
    "does not by itself prove the threshold thesis"; threshold sharpness is listed as Open
    Problem 1. Flag closed on that full read; the paper's Open Problems other than [OP1] are
    not load-bearing here.)

[10] Deane, G., Miller, M., & Wilkinson, D. (2020). Losing ourselves: active inference,
     depersonalization, and meditation. *Frontiers in Psychology* 11:539726. PMC7673417. (Read
     in full by the project.)

[11] Seth, A. K., Suzuki, K., & Critchley, H. D. (2012). An interoceptive predictive coding
     model of conscious presence. *Cognitive Neuroscience* 3(3). PMC3254200. (Read in full by
     the project.)

[12] The long-horizon agent breakdown literature. Primary representative read in full by the
     project: Bai et al., "The Long-Horizon Task Mirage? Diagnosing Where and Why Agentic
     Systems Break," arXiv 2604.11978 (the id is confirmed real, not a placeholder): the
     HORIZON benchmark, 3100+ failure trajectories, a 7-category failure taxonomy; breakdown is
     "a structural shift in failure composition as horizon grows," with planning errors
     (especially subplanning), catastrophic forgetting, and memory limitations (context
     overflow, loss of earlier constraints during summarization) the dominant bottlenecks. The
     paper's characterization — "benchmark work attributing breakdown to memory/context limits"
     — matches, with the noted refinement that memory/context limits are dominant among several
     attributed causes, not the sole one. Related benchmark work in this entry remains reached
     through the project's sweep notes (`reference/lit-search.md`).

[13] Self-reflection improves agent performance. Primary read in full by the project: Renze
     & Guven, "Self-Reflection in LLM Agents: Effects on Problem-Solving Performance," arXiv
     2405.06682 (published at FLLM 2024, pp. 476–483): eight self-reflection types across nine
     LLMs, multiple-choice tasks; self-reflection produced statistically significant
     improvements on initially incorrect problems. Consistent with §4.5's framing — reflection
     on task content, with no standing self-monitoring channel whose cost accumulates.

[15] Wei, H.-L., Wei, C.-S., Yu, Y.-S., et al. (2024). Dysfunction of the triple-network
     model is associated with cognitive impairment in patients with cerebral small vessel
     disease. PMC10828708 — read in full by the project (resting-state fMRI, 100 ICs, 8
     triple-network components; SN-oriented decreased connectivity, SN dominant in driving
     SN–DMN–CEN interactions; consistent with the DMN/CEN/SN
     mutual-inhibition-under-SN-regulation characterization). Carbone, G. A., et al. (2025).
     Triple network alteration predicts dissociative symptoms following activation of the
     attachment system: evidence from an EEG connectivity study. *Journal of Psychosomatic
     Research* — read in full by the project via the authors' institutional repository (eLORETA
     EEG, 98 participants; compartmentalization correlated with increased dACC–right dlPFC
     alpha connectivity after attachment-system activation; SN–CEN connectivity predicts
     compartmentalization).

[16] Tolchinsky et al. (2025). Temporal depth in a coherent self and in depersonalization:
     theoretical model. *Front. Psychol.* 16:1585315. PMC12444765.

[17] Madden & Serper (2026). The time collapse–entrapment model of depersonalization severity.
     *Psychiatry Research.* PMID 42288070.

[18] Additional clinical instruments and datasets as cited in `dpdr/external-validation.md`
     §8 (Melges 1970; Mathew 1992/93; D'Souza 2004; Colizzi 2019; Simeon 1997/2000/2007;
     Baker 2003; Medford 2005; Michal 2024; Hunter 2023/2025; Pons 2026; Leavitt 1999;
     Guralnik 2000; Sierra 2002; Millman 2024; Hammond 2025). ◆ (The individual primaries are
     not read here; the corpus is carried at the access level paper 1 records for each.)

[21] Chen, Wang & Qu (2026). Recursive Self-Improvement in AI: From Bounded Self-Refinement to
     Autonomous Research Loops. arXiv 2607.07663. Survey of 1,250 arXiv papers (2024–2026);
     taxonomy of four improvement categories × loop closure, the bounded self-refinement /
     open-ended RSI cut, and an evaluator-centric recurring diagnosis ("one bottleneck recurs
     everywhere: the evaluator"). Read in full by the project's literature search; quoted in
     §4.5.

[24] On the conversion of thought-reform research into a warrant for "deprogramming": Young,
     E. A. (2012). The use of the "Brainwashing" Theory by the Anti-cult Movement in the
     United States of America, pre-1996. *Zeitschrift für junge Religionswissenschaft* 7.
     https://journals.openedition.org/zjr/387. The article was read in full by the project;
     its primaries (the anti-cult movement's own material, and the Lifton and Singer sources it
     drew on) were not, and the account here is carried at the article's access level. It
     documents that "brainwashing" had "no reliable scientific evidence" and "a great deal of
     research against it," that the term was popularised by Edward Hunter — described there as
     an undercover CIA propaganda and psychological-warfare specialist — in a documented
     disinformation campaign, and that deprogramming was the extra-legal removal of adults from
     their communities. Cited in §4.6 (the Non-use boundary), and nowhere else in the argument.

---

*The `[R-n]` series (R1–R6) used in the methods half names a measurement in this paper's
own results record (`paper2/paper-2-results-record.md`), not an external work, and needs no
reference-list entry.*

*Works named in §4 by author without a bracket — these are cited by name, not number, and
are listed here so a reader can resolve them. Access level is stated for each, per the
paper's discipline; none is invented.*

- **Meijer & Rantzer (2026), "Dual Control: On Exploration–Exploitation in Linear
  Systems," arXiv 2608.20073.** Read in full by the project (dual-control audit,
  `dual-control.md`). The modern survey entry point for the Feldbaum lineage; §4.1's
  positioning stands on this full read where the Feldbaum primary is unread.
- **Filatov & Unbehauen, *Adaptive Dual Control* (LNCIS 302, Springer, 2004), §2.1.** The
  textbook statement of the original formulation ("formulated by Feldbaum 1960-61, 1965");
  not read in full by the project — carried at the level the dual-control audit records.
- **Mesbah, A. (2018), "Stochastic model predictive control with active uncertainty
  learning: A survey on dual control," *Annual Reviews in Control* 45:107–117.** Read in full
  by the project (`dual-control.md`).
- **Bar-Shalom & Tse (1974), "Dual effect, certainty equivalence, and separation in
  stochastic control," *IEEE Trans. Automatic Control* 19(5):494–500.** The formal
  definition of the dual effect; carried via the dual-control audit's survey reads, not read
  in the primary.
- **Runggaldier & Stettner (1994), *Approximations of Discrete Time Partially Observed
  Control Problems*; and the modern partially-observed-control surveys by Yüksel.** ◆ Named
  in `dual-control.md` §2 as the adjacent branch treating observation as a decision with a
  resource cost; not read in the primary — the "no state-degradation caused by observing"
  verdict stands on the dual-control audit's search-level finding.
- **Rohrs, Valavani, Athans & Stein (1985), "Robustness of continuous-time adaptive control
  algorithms in the presence of unmodeled dynamics," *IEEE TAC* AC-30(9):881 ff.** Abstract
  + intro read by the project (`dual-control.md`).
- **Anderson, B. D. O. (1985), "Adaptive systems, lack of persistency of excitation and
  bursting phenomena."** Carried via Mesbah's reference list as read in full by the project;
  the primary not read separately.
- **Zerhoudi, Mitrovic & Granitzer (2026), "The Compaction Cliff in Long-Running AI Agent
  Memory," arXiv 2608.22752.** ◆ Abstract-level only (`reference/lit-search.md` JOB B6).
- **Kang et al. (2025), ACON, arXiv 2510.00615.** ◆ Abstract-level only (JOB B6).
- **Yuan et al. (2024), "Self-Rewarding Language Models," arXiv 2401.10020.** ◆
  Abstract-level only (JOB B2).
- **Zhou (2026), "More Convincing, Not More Correct: Self-Play Reward Hacking of
  Reference-Free LLM Judges," arXiv 2607.05904.** ◆ Abstract-level only (JOB B2).
- **Renze & Guven, "Self-Reflection in LLM Agents," arXiv 2405.06682** — carried as paper 1
  ref [13] above (read in full by the project); named by author in §4.5 for the
  self-reflection contrast.
- **Carbone, G. A., et al. (2025), "Triple network alteration predicts dissociative symptoms
  following activation of the attachment system," *Journal of Psychosomatic Research*.** Read
  in full by the project via the authors' institutional repository (carried as the second
  work under paper 1 ref [15] above).
- **The coercive-induction sources** (named in §4.6, none bracket-cited, all
  framework/clinical/theoretical and not experimental): Schein, E. H., Schneier, I., &
  Barker, C. H. (1961), *Coercive Persuasion* (Norton); Lifton, R. J. (1961/1989),
  *Thought Reform and the Psychology of Totalism*; Singer, M., with Lalich, J. (1995),
  *Cults in Our Midst* (Jossey-Bass); Stein, A. (2016), *Terror, Love and Brainwashing:
  Attachment in Cults and Totalitarian Systems* (Routledge); Hassan, S. A. (2020), The BITE
  Model of Authoritarian Control (dissertation); Feliciano (2023), An Application of the
  Coercive Control Framework to Cults (CUNY); Doychak, K. (2023), Trauma-coerced
  attachment (*J. Trauma & Dissociation*); Bailey, R. et al. (2023), Appeasement
  (PMC9858395); Hadding et al. (2023), Being in-between (PMC10534031); Pons, E. et al.
  (2026), Depersonalization/derealization and meditation-induced alterations of the self,
  *Scientific Reports* 16:14673. ◆ (These are carried via `paper2/cult-induction-lit.md`'s
  source list; the mapping onto the model is an interpretation stated there, not a result of
  this paper. The 1960s sources are period-and-sample-bound; the modern structural frame
  — coercive control, undue influence — is the more defensible reading, as the note states.)
- **Seth, Suzuki & Critchley (2012)** is paper 1 ref [11] above (read in full); the
  interoceptive-predictive-coding gain construct parallels the model's g (§4.6).

