---
type: concept
updated: 2026-09-22
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
| 4 | What did the pending 2026-09-22 submission score? | our baseline | `kaggle competitions submissions` |
| 5 | Does a competition rerun spend the 30 h/week GPU quota? | how freely we can submit | watch the quota meter across one submission |
| 6 | What is the layout of `extra_vols.npy`? | whether 3,030 or 2,200 studies skip decoding | load one row on Kaggle |
| 7 | Which of the 86 DICOM tags survived? Can TE recover the fluid axis? | a slot every public solution misfiles | `scripts/audit_headers.py` on real DICOMs |
| 8 | Are click-through research datasets allowed? | MRNet, OAI, fastMRI+ pretraining | host answer on the forum |
| 9 | How much of the leaders' margin is public-LB overfit? | how we pick finals | only the private LB, after 2026-10-22 |
