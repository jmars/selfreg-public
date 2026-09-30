# Future work: an unexplained reproducible response in reasoning models

**Status:** open question + two falsified predictors. **Not a result** — a scoped handoff for a
future line of research. Recorded 2026-09-27. Never published as-is.

Memory: `handoff-selfreg-generalization-prereg` (the full record), `handoff-selfreg-precondition-and-size`,
`handoff-selfreg-sign-probe-result`, `handoff-selfreg-reasoning-finetune-proposal`.

---

## 1. The phenomenon (reproducible, unexplained)

When a reasoning model's **self-description is thinned** (the "self block" removed from the prompt),
its **outward content collapses and its inward trace rises**. Measured, self-present → self-absent:

| model | lineage | inward share | verdict |
|---|---|---|---|
| Ministral-3B-Reasoning | Mistral | 0.847 → 0.968 | RISES |
| Ministral-14B-Reasoning | Mistral | 0.797 → 0.901 | RISES |
| qwen3.5:9b | Alibaba | 0.824 → 0.855 | RISES |
| **DeepSeek-R1-0528-Qwen3-8B** | DeepSeek\* | 0.939 → 0.798 | **FALLS** |
| gemma-4-12B (templated) | Google | 0.895 → 0.896 | FLAT |
| Ministral-14B-**Instruct** | Mistral | — | **NO CHANNEL** |

**Three rise across two lineages; one falls; one is flat; one has no inward stream at all.**
The response replicates. **Nothing we have tried predicts which models show it.**

\* R1-0528-Qwen3-8B is a **distill on a Qwen base** — lineage-linked to Alibaba, not fully independent.

## 2. Two predictors, both falsified

**(a) "Reasoning-trained ⇒ the response."** The original axis. Falsified by DeepSeek-R1-distill:
a capable, reasoning-trained model with a clean n=6/6 measurement pointing the **wrong way**.

**(b) "Self-reference density ⇒ the response."** Generated from two eyeballed traces, then
pre-registered with a blind step. **Fails on its own two source cases, inverted:**

| model | pronoun/100w | response |
|---|---|---|
| R1-distill | **4.36** (highest) | **FALLS** |
| Mistral-14B-R | **2.34** (lowest) | **RISES** |

A self-directed-vs-object-directed regex pair did not rescue it either (**both** models are
overwhelmingly object-directed: self-directed references 1.0 and 0.0 per 1000 words).

## 3. What a successor inherits

**The falsification apparatus is the valuable part.** The phenomenon is established; a successor
does not re-derive it. What they inherit:

1. **A working manipulation and measure** — thin the self, read the inward/outward split from the
   model's own reasoning channel.
2. **The first-hurdle method that killed both predictors** — *when a predictor comes from eyeballed
   examples, check it against those examples quantitatively BEFORE building a study.* One trace and a
   regex, not an hour of GPU time. Both failures above cost ~an hour each, not a week.
3. **Two doors already closed** — it is not *training*, and it is not *how much the model mentions
   itself*. What remains is a property those two don't capture.

**The open question, sharply:** *what property makes a model's reasoning turn inward when its
self-description is thinned?*

## 4. Candidate directions (none staked)

- **Functional, not quantitative.** Whether the model's **self-model is load-bearing for its
  reasoning** — does it refer to itself *in order to proceed* (compliance-checking) versus mention
  itself in passing while reasoning about the object? The qualitative read that suggested this did
  **not** survive quantification as a bag-of-words measure, but the *functional* version is untested.
- **Reasoning *robustness*, not amount.** A model that closes arguments reliably may close them even
  with a thinned self; a weaker one, losing its grip, churns. (R1's both-levels-high-and-unmoved
  pattern is consistent with this; nothing tests it.)
- **Decoding/config.** Several public reports attribute non-termination to the `xhigh` **default** —
  a settings explanation, **unmodelled** and untested here.

## 5. Two confounds to carry, not forget

- **Non-termination ≠ self-reference.** The public-report scan found the *churn* complaint about
  reasoning models generally: target **70.6%** (N=17) vs **control DeepSeek-R1 80%** (N=10). A model
  can loop **on the object** without churning **on itself** — and the populations differ (R1 shows
  the public complaint at 70–80% while our screen has it *falling*). **The field evidence
  corroborates non-termination, not the self-reference mechanism.**
- **The trace-budget trap.** A reasoning model spends `num_predict` on the trace first; if the cap is
  hit, `content == 0` and the inward share saturates at 1.0 — **a budget artifact, not a
  measurement.** Signature: `inward_share == 1.000` exactly, or `content == 0`.

## 6. The finetune that this would enable

`paper2/finetune-proposal.md` — train against the (currently unidentified) axis to buy long-horizon
self-maintenance. **Staked to a predictor that does not yet exist.** Motivation stands; mechanism
does not. The user's own observation — **Qwen3.8-27B's main failure mode is inward collapse**, and
public complaints describe exactly that — makes it a natural target once a target property exists.

## 7. Instrument checklist for whoever picks this up

Both of my runner defects, recorded so they aren't repeated:

- **State the decision rule over the sample size the data actually yields.** A fixed "≥5 of 6" read
  a unanimous `4/4` as FLAT, and a bare "any positive difference" read `+0.0007` of noise as a
  direction. Express it as a **share of the realised n**, with an explicit **INSUFFICIENT** outcome.
- **Hold the protocol constant across the models you compare.** A `num_predict` change between runs
  moved verdicts for the same models (gemma FLAT→RISES, R1 FALLS→VOID). An instrument that cannot
  return **"undecided"** will return something else instead.
