---
type: concept
updated: 2026-10-02
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

## Independently confirmed, 2026-10-02: a better key did not move a model

Two teams who built the best public label keys both report that improving the key
did not improve the image model.

**dreaddevelopment**, running 20 checkpoints with a documented ablation history:

> I tried Steven's public LLM labels. Better target AUC on gold58 did not translate
> into a convincing image-model improvement in my tested recipe. I do not regard
> target-quality differences as predicted model gains.

**stevenleehans**, who built that key:

> A better key is not automatically a better model. We swapped these labels in and
> got no gain on the first attempt; it only paid off after unrelated pipeline bugs
> were fixed.

This is the strongest available evidence on the week-3 question and it arrives from
two independent sources, neither of them us. It does not prove better labels never
pay - stevenleehans's eventually did, after unrelated fixes - but it does mean
**gold-58 target AUC is not a predictor of model gain**. [Certain, two sources]

Consequence: do not spend GPU time on a better labeller on the strength of its
gold-58 score. The gate in [[E003-encode-and-gate]] is still the right measurement
because it prices label quality *through the head*, which is exactly the step both
teams found broken.

## The image model already beats its teacher on 9 of 12

dreaddevelopment's OOF numbers on the 58, image-model AUC against the AUC of the
report-derived target that trained it:

- **Image model wins on 9 of 12**, sometimes hugely: Effusion 0.901 vs 0.696,
  Contusion 0.915 vs 0.821, Medial OA 0.950 vs 0.891.
- **It loses on Lateral OA** (0.782 vs 0.829) and **Lateral Meniscus** (0.858 vs
  0.894), and ties on PF OA.

By the Tucker diagnostic above, that reads as: labels are **not** the binding
constraint on most findings, and the lateral compartment is a *modelling* problem,
not a labelling one. For Lateral OA, 10 of 11 expert-positive studies do mention
the finding in their reports - the teacher knows, and the model is not learning it.

That is a direct argument for [[slice-selection]] and crop geometry as the lever,
which is where our own +0.0059 measurement already pointed. [Likely]

Related: [[not-addressed]], [[noise-floor]], [[host]], [[slice-selection]],
[[D006-validate-on-cv-not-gold58]]
