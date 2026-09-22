---
type: entity
updated: 2026-09-22
status: superseded
sources: [docs/FINDINGS.md 1-20]
---

# Notebook: Bend the Knee to the Dinosaurs (0.939) - previous baseline

The previous baseline, superseded by [[notebook-0943]], and the notebook where 20
defects were found by executing it. File:
`bend-the-knee-to-the-dinosaurs-all-public.ipynb`. Full list: `docs/FINDINGS.md`.

## The defects that still matter

| # | defect | status |
|---|---|---|
| 13 | every study decoded 4x, arms-outermost | fixed here, see [[E002-study-major-loop]]; also fixed upstream in 0.943 |
| 18 | forces bf16 on T4, which has no bf16 tensor cores | 4.72x slower encode, measured; see [[preprocessing-contract]] |
| 20 | a missing dataset silently drops to a 0.937 parent | fixed upstream by fail-closed gates in 0.943 |
| 10 | arm 2 is arm 0's checkpoint with the slice triplet reversed | ensemble is correlated with itself; see [[ensemble-correlation]] |
| 1-3, 17 | lexicon bugs | patched in `src/lexicon_patch.py`; see [[E001-lexicon-patch]] |

## Corrected claims

- **Item 4 overstated.** It said the vendor sign flip "swaps Medial and Lateral".
  The pooling heads are permutation-invariant over slices, so it cannot. See
  [[permutation-invariance]].

Related: [[notebook-0943]], [[model-families]]
