---
type: entity
updated: 2026-09-22
status: current
sources: [run logs, timing probe, forum]
---

# Compute and timing

**2x Kaggle T4 (15 GiB each, no native bf16) at 30 GPU-hours a week is enough to
train: a 5-fold 224 px experiment is ~6.5 h.** There is no local GPU.

**Memory is per card and does not pool.** Two T4s are not 32 GB.

## Measured timings

| thing | cost | source |
|---|---|---|
| header read | **4.1 ms** | run log |
| arm-0 `build_study` | 1.89 s/study | timing probe |
| arm-0 encode, **fp16** | **0.99 s/study** | timing probe |
| arm-0 encode, **bf16** | **4.66 s/study** | timing probe - **4.72x slower** |
| arm-0 encode, fp32 | 3.11 s/study | timing probe |
| submission pipeline, 1,322 studies | **5h33m floor** | commit log, fixed costs stripped |
| one training fold, 224 px ViT-S | 76 min | forum, stevenleehans |

## What this buys

- A **5-fold training experiment is ~6.5 h**, so 30 h/week is 4-5 experiments.
  Retraining is affordable. An early session called it infeasible from
  CoAtNet-at-384 arithmetic and was wrong.
- Encoding all 4,407 studies for the gate is ~4 h cold, ~2 h using the pre-decoded
  corpus.

Related: [[notebook-0943]], [[public-datasets]], [[preprocessing-contract]]
