---
type: overview
updated: 2026-09-22
status: current
---

# Overview - read this first

## The task in one paragraph

RSNA Knee Abnormality Detection on Kaggle: 12 binary findings per knee MRI, scored
by macro AUC. **Only 58 of 4,407 training studies have labels**; the rest have a
radiology report, so everyone manufactures training targets from text. The hidden
test set is 1,322 studies, labelled by radiologists **from the images**, and the
host confirms those labels deliberately disagree with the reports. Inference must
finish in 9 hours on Kaggle with internet off. Final submission **2026-10-22**.

## Where we are (2026-09-22)

- **Rank 812 of 4,143 at 0.941.** A 0.943 submission is pending.
- Top is 0.958. Prize money (top 10) needs roughly **0.955+** now; 0.950 is rank 47.
- Our best is an **inference-only blend of public checkpoints** - the same pack
  hundreds of teams use. Every public improvement lifts all of them at once.
- **30 days left. 30 GPU-hours/week on 2x T4.**

## What we believe, and how sure

| claim | confidence |
|---|---|
| Blending public checkpoints cannot reach the top ten | [Likely] |
| Slice selection / crop geometry is the biggest lever | [Likely] - measured +0.0059 by one team |
| A bigger encoder does not help | [Certain] - two teams, null |
| Better labels help, but little is closable | [Likely] - +0.0155, below the noise floor |
| The public LB top is partly overfit | [Likely] - top-5 spread was inside one SE |

## The plan

**Train one model with our slice selection on the best public LLM label key, and
blend it into the public pack as a decorrelated member.** Select finals by CV.
See [[D001-train-not-just-blend]] and [[D002-select-finals-by-cv]].

Honest expectation: +0.004 to +0.007 over the base notebook. [Guessing]

## Next action

1. **Decide repo visibility** - [[D005-repo-visibility]].
2. **Get the result of [[E003-encode-and-gate]]** - the Tucker diagnostic.
3. **Build the 224 px pixel cache with our sampling and train a control.**

## Style for anyone working here

[Certain] / [Likely] / [Guessing] on every claim. Verify by executing, not reading -
every real bug in this repo was found that way, several in its own code. Say plainly
when something is unverified.
