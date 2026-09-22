---
type: entity
updated: 2026-09-22
status: current
sources: [run log, notebook source]
---

# The three model families in the public pack

The public pack is three families - a DINOv3 slot model, a CoAtNet Raptor model,
and a RadImageNet ResNet - all fine-tuned by other competitors and shipped as
public datasets.

| family | backbone | input | share of per-study time |
|---|---|---|---|
| **A** slot model | `vit_small_patch16_dinov3.lvd1689m`, 20 members | 336 px, 6 slots | 6.8 s |
| **B** Raptor | CoAtNet `coatnet_rmlp_2_rw_384`, 4 arms | 384 px triplets | **11.0 s** |
| **C** Rad-dual5 | ResNet-50 RadImageNet + heads | 224 px | 2.7 s |

Per-study times are marginal, from a 3-study commit log - floors, not estimates.
See [[compute]].

## Facts

- Family A is **DINOv3**, not DINOv2 as older docs said. [Certain, run log]
- Family B's head is `softmax` over windows then a sum - **permutation-invariant**.
  [Certain, executed] See [[permutation-invariance]].
- Family B arms 0 and 2 load the same checkpoint over a byte-identical volume.
- [[notebook-0943]] adds two more CoAtNet readers on top.

## The field uses DINOv3 too, and bigger does not help

Two teams measured ViT-S to ViT-B at +0.0011 against a 0.0020 noise floor. See
[[D003-no-bigger-encoder]].

Related: [[notebook-0943]], [[ensemble-correlation]]
