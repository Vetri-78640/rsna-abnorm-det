---
type: decision
updated: 2026-09-22
status: current
sources: [wiki/archive/STRATEGY.md]
---

# D001 - Train our own model, then blend it in

**Decision:** train one model with our slice selection on the best public LLM label
key, and add it to the public ensemble as a decorrelated member.

**Why:**
1. The public pack is correlated with itself - see [[ensemble-correlation]].
2. Training is now affordable: 6.5 h per 5-fold experiment - see [[compute]].
3. Slice selection is the largest measured lever, and ours is untested but
   principled - see [[slice-selection]].

**Rejected:** blending only. It caps at the public ceiling, which is where we are.

**Kill switch:** if our sampling ablation lands under +0.002 on our own CV, the
thesis is wrong. Redirect to the efficiency prize.

**Expectation:** [Guessing] +0.004 to +0.007 over the base notebook.
