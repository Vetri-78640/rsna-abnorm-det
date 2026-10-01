---
type: concept
updated: 2026-10-02
status: current
sources: [wiki/raw/forum.md, src/folds.py, our own measurements]
---

# The validation protocol, end to end

Train on report-derived labels, measure on 5-fold CV over all 4,407 studies using
leak-free report-cluster folds, accept a change only at **+0.003 macro**, and
submit to the leaderboard only to calibrate CV against LB - never to test an idea.
The gold 58 is a diagnostic panel, not a ruler. Decided in
[[D006-validate-on-cv-not-gold58]].

## The loop

1. **Change one thing.** Tucker Arrants: "Change one thing at a time so you can
   isolate what helped and what did not." A run with two changes in it produces no
   information.
2. **Score 5-fold CV on report labels.** Use `src/folds.py`
   `stratified_group_folds` over `report_clusters`, not `KFold` - 4,407 reports
   collapse to 4,101 near-duplicate clusters, and splitting a cluster across folds
   leaks.
3. **Compare against the 0.003 threshold.** Below it, the result is noise. Run
   multiple seeds to tighten the threshold before trusting anything smaller.
4. **Only then submit**, to build the CV-to-LB correlation.
5. **Record it** in a `wiki/experiments/` page whether it worked or not. The
   failures are the expensive part to rediscover.

## Three rulers, and what each can actually resolve

| ruler | n | resolves | use for |
|---|---|---|---|
| 5-fold CV, report labels | 4,407 | ~0.003 macro | **every accept/reject decision** |
| gold 58 | 58 | ~0.02 macro, 0.19 on one label | sanity, and label-quality diagnosis only |
| public LB | 1,322 (sampled) | ~0.003, but 5/day and overfits | final calibration only |

The gold-58 figure is ours: Hanley-McNeil on 27 positives and 31 negatives gives
SE 0.069 per label. See [[E006-synovitis-fill]] for the worked case where seven
genuinely different formulas all landed inside the noise. [Certain]

## What the gold 58 is still good for

Not nothing. It is the only place where **report-derived labels can be scored
against what a radiologist actually saw**, which is how we know the lexicon
over-calls and where the silence problem lives. See [[not-addressed]]. It just
cannot rank two models that differ by 0.003.

Treat it the way dreaddevelopment does: a development panel that has already seen
the development, therefore not an independent test set.

## Known failure mode: comparing numbers that are not comparable

A CV number is comparable only to another CV number on the **same labels and the
same folds**. Everyone's report labels differ, so a forum CV figure tells you
nothing about yours. Nor can a CV number be compared to an LB number. This is the
single most common error in the discussion threads.

Related: [[D006-validate-on-cv-not-gold58]], [[noise-floor]], [[E005-control-and-ablation]]
