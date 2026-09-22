---
type: concept
updated: 2026-09-22
status: current
sources: [docs/STRATEGY.md, computed 2026-09-10]
---

# Noise floor: what differences are real

**Most differences people chase in this competition are inside the noise.** Knowing
the floor is what stops us chasing them.

## On the test set

Macro-AUC SE, Hanley-McNeil at AUC 0.94, prevalence from the non-gold studies:

| set | n | SE (independent labels) | SE (correlated) |
|---|---|---|---|
| full test | 1,322 | 0.0026 | 0.0090 |
| public LB at 50% | 661 | 0.0037 | 0.0128 |

## On the gold 58

A 58-study ruler cannot resolve differences **below about 0.02 macro**. Per-label
SE is 0.04-0.09. Use gold to sanity-check and to rank a few candidates, never to
fit parameters.

## On your own CV

Measure it: same config, different seed. One team measured **0.0020** at 3 folds.

## Consequences

- The top of the public LB is not resolved. On 2026-09-10 the top-5 spread was
  0.003, inside one SE.
- **Leaders with 40-120 submissions are partly fitting the public sample.** That
  overfit does not survive to private. See [[D002-select-finals-by-cv]].
- **"Moved 10 of 12 labels" beats a macro delta.** A real effect lifts most labels;
  noise lifts about half.

Related: [[D002-select-finals-by-cv]], [[label-premise]]
