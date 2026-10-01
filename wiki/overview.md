---
type: overview
updated: 2026-10-02
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

## Where we are (2026-10-01)

- **Rank 533 of 4,783 at 0.943.** Team `a`, 8 submissions.
- **749 teams display 0.943**, filling ranks 291 to 1,039. We are on the public
  plateau with 16% of the field, so **+0.001 is worth about 750 places**.
- Top is 0.961. Prize money (top 10) needs **0.957**; 0.950 is rank 79.
- Our best is an **inference-only blend of public checkpoints** - the same pack
  hundreds of teams use. Every public improvement lifts all of them at once.
- **20 days left. 30 GPU-hours/week on 2x T4.**

See [[E004-submissions]] for the full rank table.

## What we believe, and how sure

| claim | confidence |
|---|---|
| Blending public checkpoints cannot reach the top ten | [Likely] |
| Slice selection / crop geometry is the biggest lever | [Likely] - measured +0.0059 by one team |
| A bigger encoder does not help | [Certain] - two teams, null |
| **Gold-58 target AUC does not predict model gain** | [Certain] - two independent teams, 2026-10-02 |
| **A simple CNN at 224 px reaches 0.94+** | [Likely] - two top-100 competitors, unreproduced |
| The public LB top is partly overfit | [Guessing] - weaker than we thought, see [[E004-submissions]] |

## The plan

**Train one model with our slice selection, validate it on 5-fold CV against report
labels, and blend it into the public pack as a decorrelated member.** See
[[D001-train-not-just-blend]].

Two protocol rules now bind every experiment:

- **[[D006-validate-on-cv-not-gold58]]** - accept a change only at +0.003 macro CV
  on report labels. The gold 58 resolves nothing finer than 0.02 and has misled
  three separate teams. This is new as of 2026-10-02 and changes how every
  remaining experiment is scored.
- **[[D002-select-finals-by-cv]]** - finals are chosen by CV, never public LB.

Honest expectation: **0.944 to 0.947, which is rank 233 to 120.** Not the "rank 30
to 60" earlier pages claimed against the September board. [Likely]

## The open strategic question

Two top-100 competitors say a **ResNet34 or EffNetB0 at 224 px with simple pooling
and no attention** scores 0.94+ on its own. Our plan is shaped around DINOv3 and
CoAtNet because the public pack is. If the simple-CNN claim holds, it is both
cheaper to train and far more decorrelated from the pack than anything we planned,
which is exactly what a blend member needs. Open question 13, issue #23.

## Next action

1. **Get the result of [[E003-encode-and-gate]]** - issue #1, the blocker.
2. **Test the simple-CNN claim** - issue #23.
3. **Run the header census** - issue #14, CPU only, settles three open questions.

## Style for anyone working here

[Certain] / [Likely] / [Guessing] on every claim. Verify by executing, not reading -
every real bug in this repo was found that way, several in its own code. Say plainly
when something is unverified.
