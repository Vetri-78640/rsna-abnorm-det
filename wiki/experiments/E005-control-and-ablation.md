---
type: experiment
updated: 2026-09-24
status: in-progress
sources: [notebooks/cache_and_train_control.ipynb, src/folds.py]
---

# E005 - Control model and the sampling ablation

The training pipeline that did not exist before. Builds a 224 px pixel cache using
**either our slice selection or the public fixed budgets**, then trains a 5-fold
control and reports out-of-fold AUC per label plus the gold-58 score.

Covers issues #2 (cache), #3 (control), #4 (noise floor), #6 (ablation), #7
(resolution). Notebook: `notebooks/cache_and_train_control.ipynb`.

## Runs

| run | change | answers |
|---|---|---|
| 1 | `SAMPLING="public"` | the control |
| 2 | `SAMPLING="ours"` | **#6, the thesis** |
| 3 | `SAMPLING="public"`, `SEED=1` | **#4, the noise floor** |
| 4 | `SIZE=288` | **#7** |

## How to judge it

**Count how many of the twelve per-label AUCs move, not the macro.** A real effect
lifts about 10 of 12; noise lifts about half. One team's crop-geometry fix moved 10
of 12 for +0.0059; their encoder scaling moved 5 of 12 for +0.0011 and was a null.

Then compare the gap against the seed-to-seed noise floor from run 3. A difference
smaller than that is not a result. See [[noise-floor]].

## Folds

`src/folds.py` clusters near-duplicate reports and distributes clusters by
iterative stratification. Measured on the real reports: **4,407 reports form 4,101
clusters**, while the public notebook's MD5-of-report grouping makes 4,276 - so it
splits 175 near-duplicate studies across folds. See `wiki/archive/FINDINGS.md` 12.

[Likely] the clustering is conservative in the other direction: the largest cluster
is 37 identical Turkish "normal knee" template reports, which are probably different
patients. `PatientID` from the census (#14) would group better.

## Status

Written and dry-run end to end against a synthetic competition tree built from real
DICOM slices, on both sampling paths. **Not yet run on Kaggle.** Two bugs the dry
run caught, both of which would have failed silently:

- `geometry.order_slices` returns `(records, method)` and `geometry.laterality_flips`
  returns a tuple, not a dict. The original code wrapped the second in a bare
  `except`, so laterality would have been skipped on every study while still
  producing a plausible cache.
- Only fold 0's encoder was frozen; later folds trained every block, so the folds
  were not comparable.

The notebook prints the slice-ordering method and the laterality tags seen, so a
silent regression of either shows up in the log.

Related: [[slice-selection]], [[E003-encode-and-gate]], [[compute]]
