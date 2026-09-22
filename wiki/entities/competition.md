---
type: entity
updated: 2026-09-22
status: current
sources: [wiki/archive/extras.md, kaggle CLI, rsna.org]
---

# The competition

**RSNA Knee Abnormality Detection** on Kaggle: 12 binary findings per knee MRI,
macro AUC, 9-hour inference limit, final submission 2026-10-22.

Predict 12 binary findings per knee
MRI study. Scored by **macro-averaged AUC ROC** - every label is exactly 1/12 of
the score.

Labels: ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA,
Effusion, Synovitis, Baker's, Contusion, Fracture.

## Dates (23:59 UTC)

| date | event |
|---|---|
| 2026-07-30 | start |
| **2026-10-15** | entry and team-merger deadline |
| **2026-10-22** | **final submission** |
| 2026-11-05 | winners' code, video, write-up due |

## Hard limits

- **Submission notebook must finish in 9 hours.** Internet off. Weights come from
  attached Kaggle datasets only.
- **5 submissions per day.** 2 final submissions selected for private scoring.
- Hidden test set is **1,322 studies**. [Certain] the notebook prints it while
  sizing its cache.
- Public LB is a sample of the test set; the private LB decides placing.

## Prizes

**$77,000 total** [Certain, rsna.org]. Main LB $54,000 across top 10; efficiency
track $18,000 across top 3. The efficiency track is separate and far less
contested - a real second shot.

## Rules that bite

- Competition data may not be redistributed to anyone who has not accepted the
  rules. **Never commit `data/` to a public repo.**
- No private code sharing outside the team. Public sharing licenses it openly.
- External data and models allowed if reasonably accessible and minimal cost.
- Commercial LLM APIs are allowed for label extraction - see [[host]].
- Winners must publish training code, inference code and weights, CC-BY-NC 4.0.

Related: [[dataset]], [[host]], [[compute]], [[noise-floor]]
