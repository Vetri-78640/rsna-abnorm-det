---
type: concept
updated: 2026-09-22
status: current
sources: [wiki/raw/forum.md, audit]
---

# The label premise: do better labels help?

Better labels help a little, but our lexicon is already close to the best public
LLM key and the gold labels deliberately disagree with reports - so little is
closable. **The original "bad labels cap everyone" thesis was half right.**

## What held

- LLM keys beat regex keys. One team: LLM 0.8780 vs regex 0.8136 on the gold 58.
- The public ensemble is saturated and correlated.

## What did not

- **Our patched lexicon already scores 0.8625 on gold**, so the closable gap to the
  best public LLM key is **+0.0155** - below the 0.02 noise floor. [Certain]
- **The gold labels deliberately contradict the reports** at ~82% agreement, host
  confirmed. No report-derived labeler passes that. [Certain]

## The diagnostic to run (Tucker Arrants, rank 12)

> If your image model is not beating the label extractor "teacher", there is
> likely modeling headroom. If your image model is beating the label extractor by
> a large margin, the quality of the labels might be holding the image model back.

Compare the image model's gold AUC to the extractor's **0.8625** on the same 58.
The `ckpt` arm of [[E003-encode-and-gate]] gives the first number.

**An earlier reading here was backwards.** It argued a model exceeding its teacher
means labels are a *soft* ceiling. Tucker's reading - that it means labels are
*binding* - is the more useful one because it is falsifiable.

Related: [[not-addressed]], [[noise-floor]], [[host]]
