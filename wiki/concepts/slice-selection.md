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

## What the data allows

[Certain] Axial non-fat-sat is missing in 80.6% of studies and coronal non-FS in
22.7%; only 12.8% of studies have all six slots. And 13.6% of filled slots offer more
than one series to choose from. So slice selection is also *series* selection, and
it must degrade gracefully when a slot is empty. See [[dataset]].

## Measured: the public sampling is coarse outside sagittal

The Raptor family takes a fixed number of slices per slot. Against the real slice
counts, that fixed budget produces very different strides
(stride = slices spanned / slices taken, over the 0.02-0.98 span):

| slot | budget | median stride | p95 | share over 2.5 |
|---|---|---|---|---|
| Sagittal fat-sat | 18 | 1.55 | 2.51 | 5.0% |
| Sagittal non-FS | 14 | 2.06 | 4.11 | 10.3% |
| Coronal fat-sat | 12 | 2.40 | 3.04 | 32.2% |
| **Coronal non-FS** | 8 | **3.60** | 4.44 | **83.6%** |
| **Axial fat-sat** | 12 | 2.56 | **11.52** | 51.6% |
| Axial non-FS | 12 | 2.56 | 6.43 | 55.8% |

[Certain, measured on **all 24,386 series**] **79.6% of studies have at least one
slot sampled at a stride over 2.5.**

Read this carefully rather than as a slam dunk. The sampling is densest exactly where
fine detail is classically needed - sagittal, where the meniscal body spans 2-3
slices - and that slot is fine (5.3% over stride 2.5). The coarse slots are coronal
non-FS and axial, which carry **MCL, Baker's, Effusion and PF OA**: four of twelve
labels. Whether those findings need dense sampling is exactly what the week-2
ablation tests.

The unambiguous defect is the axial tail: a 3D axial series of 144 slices sampled at
12 gets a stride of 11.5, which discards almost everything. 1.4% of sagittal fat-sat
series are the opposite problem - the budget exceeds the slices available, so slices
are sampled twice.

An adaptive per-series stride is the obvious fix, and it is what `src/sampling.py`
is for.

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
