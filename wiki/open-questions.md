---
type: concept
updated: 2026-10-02
status: open
sources: [this project]
---

# Open questions

Everything we do not yet know that changes a decision, with what would settle it.
Close a question by moving its answer onto the right page and deleting the row.

| # | question | changes | settled by |
|---|---|---|---|
| 1 | Does our slice selection beat the public one on our CV? | whether [[D001-train-not-just-blend]] survives | issue #6 |
| 2 | Does the image model far exceed the label extractor on the gold 58? | how much week 3 is worth; see [[label-premise]] | issue #1 |
| 3 | Is `AMP_PREF='auto'` score-neutral on the 0.943 notebook? | a 4.72x speedup on Family A | issue #5 |
| ~~4~~ | ~~Pending 2026-09-22 submission?~~ **Closed.** 0.943, now our standing score; rank 533 of 4,783. | our baseline | done, see [[E004-submissions]] |
| 5 | Does a competition rerun spend the 30 h/week GPU quota? | how freely we can submit | watch the quota meter across one submission |
| 6 | What is the layout of `extra_vols.npy`? | whether 3,030 or 2,200 studies skip decoding | load one row on Kaggle |
| 7 | How many series does the fluid flag misfile? (one T2 confirmed so far) **A forum EDA agrees: "non-FS" mixes T1, PD and T2.** | a slot every public solution misfiles | `notebooks/header_census.ipynb`, CPU only |
| 10 | Is `Laterality` present in every series? **[Likely] no - a forum EDA says missing in about half of studies.** | whether laterality is simply solved | same census, to confirm |
| 11 | Does `PatientID` repeat across studies? | whether CV folds must group by patient | same census |
| ~~12~~ | ~~Slices per series?~~ **Closed.** All 24,386 series: median 30, p99 160, max 320. | stride design | done, see [[dataset]] |
| 8 | Are click-through research datasets allowed? | MRNet, OAI, fastMRI+ pretraining | host answer on the forum |
| 9 | How much of the leaders' margin is public-LB overfit? | how we pick finals | only the private LB, after 2026-10-22 |
| 13 | Does a simple CNN at 224 px really reach 0.94+, as two top-100 competitors claim? | whether our DINOv3 plan is the wrong shape entirely | issue #23 |
