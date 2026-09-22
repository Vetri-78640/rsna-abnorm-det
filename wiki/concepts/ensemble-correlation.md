---
type: concept
updated: 2026-09-22
status: current
sources: [notebook source, docs/FINDINGS.md 10]
---

# Why one decorrelated member beats a 31st correlated one

Everyone on the public LB blends the same highly correlated pack, so one genuinely
different member is worth far more than another correlated one.

The pack is correlated with itself:

- Family B arm 2 is arm 0's checkpoint with the triplet reversed.
- Family C is Family B's representation with a different head.
- Everyone on the public LB blends the same pack.

At that correlation, 24 Family-A members are worth perhaps 2-4 effective members,
and adding more of the same buys under 0.001.

**A genuinely different member** - different labels, different slice selection,
trained by us - is worth several times that. [Guessing] +0.002 to +0.006 for a
~0.92 single model blended at 0.2-0.3 weight.

## How to add one

1. Measure rank correlation of the new model against every existing member.
2. Weight by decorrelation, not by individual AUC.
3. Fit weights at the group level (side-specific, OA, effusion family, traumatic)
   and shrink toward the global weight - four parameters, not twelve.

Related: [[D001-train-not-just-blend]], [[model-families]]
