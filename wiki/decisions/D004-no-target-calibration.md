---
type: decision
updated: 2026-09-22
status: current
sources: [simulation 2026-09-09]
---

# D004 - Do not recalibrate training targets

**Decision:** do not Platt-calibrate lexicon scores before training.

**Why:** calibration is monotone, so it leaves the ranking untouched and AUC cannot
see it. All it does is shrink the BCE gradient. In a simulation with the effect
planted **in its favour** it lost 0.048 macro.

An earlier session recommended it off a real finding (the lexicon over-calls on
all twelve labels) and was wrong. **Before recommending a transform, ask what the
metric can see.**

**Where calibration still matters:** mixing two differently-scaled sources, such as
model predictions blended with lexicon scores. Fix there by rank-normalising both.
