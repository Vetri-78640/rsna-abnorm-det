---
type: decision
updated: 2026-10-02
status: current
sources: [wiki/raw/forum.md Tucker Arrants rank 34, our own Hanley-McNeil measurements]
---

# D006 Validate on 5-fold CV against report labels, not on the gold 58

**Decided: the 58 gold studies are a development panel, not a ruler.** Every
accept/reject decision is made on 5-fold CV against report-derived labels over all
4,407 studies, with a **0.003 macro threshold** for a genuine improvement. The gold
58 and the public LB are both too small to resolve the differences we are chasing.

## Why

Tucker Arrants, rank 34, stated it plainly:

> Validate against the report extracted labels, not the provided 58 labels and not
> against the LB - neither are large enough sample sizes to resolve 0.002-0.003
> differences... Set a CV threshold for what is a genuine improvement and what is
> noise. Mine is around 0.003.

**We had already measured this ourselves without acting on it.** On the gold 58,
Hanley-McNeil gives a standard error of 0.069 on a single label with 27 positives,
so two variants need to differ by **0.191** before the 58 can tell them apart; see
[[E006-synovitis-fill]]. The macro noise floor is about 0.02, see [[noise-floor]].
We are chasing gains of 0.001 to 0.005. The ruler is two orders of magnitude too
coarse. [Certain]

dreaddevelopment, who runs the most carefully documented pipeline on the forum,
reached the same arrangement independently: five-fold CV against report-derived
targets, with the 58 used as a development panel because they had already informed
his development.

stevenleehans, who built the best public LLM label key, says the 58 misled him
repeatedly:

> We have had three separate readings from this ruler overturned by the
> leaderboard - treat small gaps as unknown, not as zero.

## What this changes

- [[E005-control-and-ablation]] and every future ablation report **CV macro on
  report labels** as the headline number. Gold-58 AUC stays as a secondary
  diagnostic, labelled as such.
- The accept threshold is **+0.003 macro CV**. Below that, a change is not adopted
  no matter how good the story is. Tighten it with multiple seeds before trusting
  anything smaller.
- Submit to the LB **only after** a change clears CV, to build a CV-to-LB
  correlation. Not to test the change.
- `src/folds.py` already provides the leak-free split this needs: iterative
  stratification over near-duplicate report clusters, 4,101 clusters from 4,407
  reports. Use it, not a plain `KFold`.

## What does not change

[[D002-select-finals-by-cv]] still stands - finals are chosen by CV rather than
public LB. D006 is narrower: it says what the CV is computed *against*.

## What would reverse this

A second expert-labelled set large enough to resolve 0.003. The host has not
offered one and the competition ends 2026-10-22, so this will not happen.

## The trap it closes

There is **no transferable CV-to-LB mapping**, so asking the forum what CV
corresponds to 0.950 is the wrong question. Tucker again:

> 0.86 CV could score 0.95 on the public leaderboard - everyone has different
> labels so I can't tell you what a CV of 0.86 means. Use the same fold split and
> find the CV between your models to compare them.

A CV number is only comparable to another CV number computed on the same labels
and the same folds. Ours are only comparable to ours.

Related: [[D002-select-finals-by-cv]], [[noise-floor]], [[label-premise]],
[[validation-protocol]]
