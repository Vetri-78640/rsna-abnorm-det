---
type: decision
updated: 2026-09-22
status: current
sources: [forum]
---

# D003 - Do not spend GPU hours on a larger encoder

**Decision:** stay at ViT-S and the current backbones - two teams measured ViT-B
as a null.

**Why:** two independent teams measured ViT-S to ViT-B at **+0.0011 against a
0.0020 noise floor**, with only 5 of 12 labels moving and the gain resting on the
least reliable label. 4x the parameters for nothing measurable.

**Would reverse if:** someone posts a ViT-B result that moves 10+ of 12 labels.
