---
type: decision
updated: 2026-09-22
status: current
sources: [wiki/archive/STRATEGY.md]
---

# D002 - Select the two finals by CV, never by public LB

**Decision:** choose final submissions on our own cross-validation.

**Why:** the public LB is a sample of 1,322 studies with macro SE 0.004-0.013. The
top-5 spread on 2026-09-10 was 0.003. Leaders have 40-120 submissions; ours are few.
Selecting on public LB inherits their overfit instead of beating it. See
[[noise-floor]].

**Consequence:** the realistic route to the top ten is arriving near the top with
no public-LB overfit while part of the leading group regresses on private.
