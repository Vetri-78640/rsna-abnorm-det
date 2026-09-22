---
type: concept
updated: 2026-09-22
status: current
sources: [forum, src/sampling.py]
---

# Slice selection and crop geometry - the thesis lever

**The largest measured single lever in the competition.** One team's crop-geometry
fix paid **+0.0059 and moved 10 of 12 labels**. Compare encoder scaling: +0.0011,
5 of 12 - noise.

## Why it should matter

- The intact meniscal body spans only 2-3 sagittal slices. A coarse stride can miss
  it entirely, making the absent bow-tie sign unlearnable.
- Narrow bands (0.2-0.8) discard the stack ends, where PF OA (patella), Baker's
  (popliteal fossa) and Effusion (suprapatellar pouch) live.

## What we have

`src/sampling.py`: per-label anatomical bands, stack ends never discarded,
meniscal-body stride, per-label plane and contrast routing, defaulting to the six
slots the metadata can actually fill.

[Likely] Ours is more principled than what is public - built from the radiology
rather than a grid search. **Untested on real data.**

## Supporting evidence

[[notebook-0943]]'s two new members are both depth/slice geometry changes (depth
zones, 96-slice stacks), and they moved the public ceiling from 0.940 to 0.943.

## The test

Ablate ours against the public sampling, same folds, same seed. Under +0.002, the
thesis is wrong. See [[D001-train-not-just-blend]].

Related: [[permutation-invariance]], [[compute]]
