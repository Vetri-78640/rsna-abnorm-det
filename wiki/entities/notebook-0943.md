---
type: entity
updated: 2026-09-22
status: current
sources: [bend-the-knee-to-speedy-raptors-the-original.ipynb]
---

# Notebook: Bend the Knee to Speedy Raptors (0.943) - current best

Our current best (0.943): an inference-only blend of public checkpoints that adds
two CoAtNet depth-geometry readers, cached decoding and fail-closed gates. Local file:
`bend-the-knee-to-speedy-raptors-the-original.ipynb`. Kaggle:
`imvetri0/bend-the-knee-to-speedy-raptors-the-original`, derived from Mattia
Angeli's public notebook.

**Inference-only. Trains nothing.** 24 cells, ~223k chars of code.

## What it adds over [[notebook-0939]]

- **Two new CoAtNet readers:** a D4 depth-zone SWA3 model (three depth zones inside
  each anatomical slot) and a CoAtNet Global96 model (96-slice stack, full-width
  gated head). Note both are *depth and slice geometry* changes - more evidence
  for [[slice-selection]].
- **Speed:** shared DINO prefixes (first 6 layers), persistent T4x2 replicas,
  overlapping preparation, **cached source decoding**, completion-driven workers.
  Runs under 9 h. The cached decoding is the same idea as our study-major loop in
  [[E002-study-major-loop]], arrived at independently.
- **Fail-closed gates.** Raises instead of writing `submission.csv` if the DINO
  member count is not 20 or the calibrator did not apply. This fixes the silent
  0.002 loss in [[notebook-0939]].

## Watch out

- **It keeps `AMP_PREF = 'bf16'` on purpose**, commented "no unvalidated AMP
  change". fp16 and bf16 give different numerics, so switching changes the
  predictions. See [[preprocessing-contract]].
- Fail-closed means a failed run produces **no file**, which costs a submission
  slot rather than scoring 0.5.

## Datasets it needs (all public, all permitted)

pilkwang/rsna-knee-weights, pilkwang/rsna-knee-llm-labels,
mattiaangeli/{knee-mri-fold-weights, rsna-knee-coat-resgated-ep10-top3,
rsna-knee-coatnet-d4-depthzone-swa3-b2, rsna-knee-coatnet-global96-top3,
opencv-python-headless-4120088-x86}, dreaddevelopment/{raptor-knee-maxspan,
raptor-knee-native384, raptor-knee-native384dense},
antoinegg1/{rsna-knee-e11-diverse-heads-v20, rsna-knee-e9-radimagenet-heads-v15},
prvsiyan/rsna-knee-v52-radimagenet-heads-20260812,
marwanmath/resnet-50-radimagenet-marwan, sofiaanjenje/{rsna-knee-e11-train,
rsna-knee-e13-train} (notebook outputs), metaresearch/dinov2 small.

Related: [[model-families]], [[notebook-0939]], [[E004-submissions]]
