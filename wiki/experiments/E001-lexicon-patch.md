---
type: experiment
updated: 2026-09-22
status: done
sources: [scripts/audit_labels.py]
---

# E001 - Lexicon patch, measured against gold

**Hypothesis:** fixing three lexicon bugs raises gold AUC on the OA labels.

**Result:** first version scored macro **-0.0008** - all three OA labels fell.
Cause found by executing it: `GLOBAL_OA` matched the bare Greek word for
osteoarthritis and bare "compartments", so medial-only OA propagated to Lateral and
PF on 98 studies. Narrowing the regex took it to **+0.0008**.

**Verdict:** inside noise. Keep it for the mechanism, not the number. Lexicon work
is worth approximately zero as a standalone lift.

**Lesson:** a correct fix can be wrong in combination with the code it lands in.
