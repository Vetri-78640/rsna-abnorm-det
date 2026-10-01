---
type: experiment
updated: 2026-10-02
status: current
sources: [kaggle competitions submissions, kaggle competitions leaderboard 2026-10-01]
---

# E004 - Every leaderboard submission

Our best public score is 0.943 and it places us **533 of 4,783**, because **749
teams are tied at exactly 0.943**. The field did not just inflate, it piled up on
one number, and that number is ours.

| date (UTC) | public LB | notebook |
|---|---|---|
| 2026-09-08 | 0.939 | bend-the-knee-to-the-dinosaurs |
| 2026-09-09 | 0.939 | same |
| 2026-09-09 | 0.940 | a newer public model |
| 2026-09-10 | 0.941 | public model |
| 2026-09-22 | 0.942 | [[notebook-0943]] |
| 2026-09-22 | **0.943** | [[notebook-0943]] |
| 2026-09-28 | 0.943 | same |
| 2026-09-29 | **0.943** | same, our standing score |

Eight submissions, not the three earlier pages claimed. Team `a`, members
`cosmicmap, imvetri0, kaori02`. **Corrected:** [[E005-control-and-ablation]] and
the README both said "our 3". [Certain, `kaggle competitions submissions`]

## Where that places us

| date | teams | top | 0.950 is rank | us |
|---|---|---|---|---|
| 2026-09-10 | 3,434 | 0.954 | 16 | 193 @ 0.940 |
| 2026-09-22 | 4,143 | 0.958 | 47 | 812 @ 0.941 |
| **2026-10-01** | **4,783** | **0.961** | **79** | **533 @ 0.943** |

## The 0.943 plateau is the whole story

**749 teams display 0.943**, filling ranks 291 through 1,039. That is the current
public-notebook ceiling and we are sitting in the middle of it at 533.

They are not actually tied. The CSV export rounds to three decimals while Kaggle
ranks on full precision - checked by testing whether rank order inside the band
follows submission date, the usual tie-break, and it does not. So those 749 teams
are really spread across roughly one thousandth of AUC, ordered by their unrounded
scores. [Certain]

That is the leverage: **one thousandth of AUC is worth about 750 places here**,
because 16% of the entire field is packed into that single thousandth. Nothing
else on this project has that ratio. It also means our 533 is a real position
rather than an artefact, and that small genuine gains are not lost in noise the
way they would be further up the board.

## What each score is now worth

| score | best achievable rank |
|---|---|
| 0.944 | 233 |
| 0.945 | 170 |
| 0.947 | 120 |
| 0.948 | 104 |
| **0.950** (prize line) | **79** |
| 0.952 | 59 |
| 0.955 | 27 |

**Corrected:** the README's "0.944 to 0.947 lands rank 30 to 60" was written
against the 2026-09-10 board and is now wrong by a factor of three. 0.947 lands
about 120. Reaching the top 10 needs **0.957**. [Certain]

## The leaders are not obviously overfitting any more

Top-10 spread is 0.004, still inside one standard error on this test set. But
top-20 submission counts now run 16 to 287 with a median of **117**, and the
minimum of 16 matters: at least one team reached the top 20 on 16 submissions,
which is not a public-LB grind. [[D002-select-finals-by-cv]] still holds, but the
argument "their margin is mostly overfit" is weaker than it was.

Re-pull: `kaggle competitions leaderboard -c rsna-knee-abnormality-detection --download`.
