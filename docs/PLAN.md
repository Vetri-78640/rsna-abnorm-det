# Plan

Six weeks became **42 days** on 2026-09-10. The argument behind this schedule is
in `STRATEGY.md`; the evidence behind it is in `community.md`. This file is only
the sequence.

**What changed on 2026-09-10.** An earlier version of this plan said retraining
was infeasible on a T4. That was arithmetic on CoAtNet at 384 px over 64 slices -
57 h for one arm. At 224 px over 6 slots x 9 slices the entire visual input is
11.12 GiB and **one fold is 76 minutes**, so a 5-fold experiment is 6.5 h. At
30 h/week that is 4-5 experiments a week and about 25 before the deadline.

So the plan inverts: **we train.** The blending-only plan is the fallback.

**Hard constraint unchanged:** the submission notebook must finish inside 9 hours.
Measured from a real commit log, the current pipeline extrapolates to 5h33m as a
floor. See `FINDINGS.md` item 19.

**Levers, by measured effect only** (nobody's estimate, everybody's own CV):

| lever | effect | labels moved | verdict |
|---|---|---|---|
| crop geometry / slice selection | +0.0059 | 10 of 12 | **the thesis** |
| "not addressed" handling on labels | +0.0093 on the key | - | cheap, take it |
| LLM key over our lexicon | +0.0155 on the key | - | below its own noise floor |
| encoder ViT-S to ViT-B | +0.0011 vs 0.0020 floor | 5 of 12 | **null, do not spend here** |

`src/sampling.py` and `src/geometry.py` are the top row. That is the edge.

---

## Week 1 - a training pipeline and a control

| task | why |
|---|---|
| Build the 11 GiB pixel cache using **our** slice selection | the +0.0059 lever needs a pipeline to live in |
| Train DINOv3 ViT-S, 5 folds, on the best public LLM key | ~7 h; this is the control everything else is measured against |
| Measure the noise floor: same config, different seed | without it no later delta is interpretable |
| Run `notebooks/RUN_THIS_encode_and_gate.ipynb` | gives the image-model-vs-teacher diagnostic on the gold 58 |

Print which backbone actually loaded, every run. A silent fallback to ResNet-18
trains fine and logs a plausible score; see `community.md`.

Deliverable: a CV number, a measured noise floor, and a per-label table.

---

## Week 2 - the ablation that is the whole thesis

| task | gain |
|---|---|
| Our sampling against the public one, same folds, same seed | the +0.0059 lever |
| Full-range coverage, per-label bands, per-label plane routing | part of the same lever |
| Resolution: 224 against 288 | community reports resolution pays |

**Decision point Friday.** If our sampling lands under +0.002 on our own CV, the
thesis is wrong. Say so, and move to week 6 plus the efficiency prize.

Judge by how many of the twelve labels move, not by the macro alone. A real
effect here lifts 10 of 12; noise lifts about half.

---

## Week 3 - labels, cheaply

Do **not** build a labeler. Several public LLM keys exist already (pilkwang,
barun2104, lixin73, dreaddevelopment, stevenleehans), and the host has ruled
hosted LLM APIs permitted if we ever need our own.

| task | gain |
|---|---|
| Swap the best public LLM key in, compare on CV | +0.0155 on the key, sublinear to the model |
| Synovitis undecided cells filled from the Effusion field | +0.0093 on the key, targeted only |
| Per-label weak-loss reliability weighting | +0.001 to +0.004 |

The blanket version of the imputation is worse than the targeted one. Silence
about Baker's is a negative label; silence about synovitis is not.

Remember the ceiling: the host has confirmed the gold labels deliberately
contradict the reports, at about 82% agreement. No labeler passes that.

---

## Week 4 - localisation, or cut

| task | gain |
|---|---|
| Hand-annotate ~200 studies with 6 anatomical keypoints | - |
| Keypoint model, heatmap, EfficientNet + FPN | - |
| ROI-cropped classifier arm for the focal labels | +0.005 to +0.015 |

Every prior RSNA winner used localise then crop then 2.5D then sequence. None of
the three public families have the first stage. **This is still the designated
cut** if weeks 1-3 overrun. Validate localisation in millimetres, not AUC.

---

## Week 5 - blend as a decorrelated member

| task | gain |
|---|---|
| Rank correlation of our model against every public member | tells us what the member is worth |
| Weight by decorrelation, not by individual AUC | the public pack is correlated with itself |
| Rare-label pipeline: paired FS / non-FS for Fracture and Contusion | +0.003 to +0.010 |

Arm 2 is arm 0's checkpoint with the triplet reversed; Family C is Family B with
a different head. Adding a 31st correlated member is worth under 0.001. One
genuinely different member is worth several times that, and is the point of
weeks 1-3.

---

## Week 6 - submit

| task | gain |
|---|---|
| Group-level shrunk blend weights, bagged selection, power-mean ranks | +0.002 to +0.006 |
| `AMP_PREF='auto'` in cell 23 | 0.000 on score, 4.72x on Family A's encode |
| Submission plumbing, timeout margin, fallback | - |

**Two finals, both chosen by CV.** Never by public LB. At 1,322 test studies the
public-LB macro SE is 0.004 to 0.013, the top-5 spread is 0.003, and the teams
above us have 42 to 119 submissions against our 3. Selecting on public LB is how
we would inherit their overfit instead of beating it.

Grep every candidate run for `[public0033]`. A missing dataset costs 0.002 with
one printed line and no error. See `FINDINGS.md` item 20.

---

## Open questions

1. ~~**Gold set size.**~~ Settled: 58, trauma-enriched. No per-label parameter can
   be fitted on it. It is usable for ranking a handful of candidates, and is
   better at that than a random 58 would be for the rare labels.
2. **Compute.** Weeks 3-5 need real GPU time. Without it, the achievable plan is
   corrected preprocessing plus the public checkpoints - weeks 1-2 and the blend
   work in week 6.
3. **Where the 9 hours actually go.** The budget model's per-unit costs are
   guesses and they undershoot: the notebook budgets 8h, so the real numbers are
   several times higher somewhere. A saved submission log settles it, and until
   it does, every "add an arm" decision in week 5 is unpriced.
4. **External data eligibility.** MRNet pretraining and RadImageNet weights need a
   ruling on the competition's external-data thread.
5. **Anatomical bands.** Those in `sampling.LABEL_BANDS` are literature priors,
   not measurements. Fit them once data is available.
6. ~~**Is an LLM labeler even legal?**~~ Settled. The host ruled commercially
   hosted LLM APIs permitted for extracting labels from reports. See `extras.md`.
7. **How much of the label gap is actually closable?** The public LLM key scores
   0.8780 against gold; our patched lexicon scores 0.8625. That +0.0155 is below
   the 0.02 noise floor a 58-study ruler supports, so the strongest public
   evidence for the label premise does not clear its own resolution. And the host
   has confirmed the gold labels deliberately disagree with the reports, which
   caps any report-derived labeler near 82%.
8. **Does fixing the labels actually lift a trained model?** The premise says the
   lexicon's precision is the ceiling for every family that consumed it. But the
   lexicon scores macro 0.862 against gold while the public checkpoints score
   0.939 on the test set, so the models already exceed their own labeler by a
   wide margin. Different populations and different label sources, so it is not a
   clean comparison - but it is evidence that the lexicon is a soft ceiling, not
   a hard one, and that week 3's gains will be sublinear in labeler improvement.
   Worth resolving before spending six days on the relabelling loop.
