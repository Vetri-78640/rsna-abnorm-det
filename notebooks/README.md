# Run this one notebook

`RUN_THIS_encode_and_gate.ipynb`. That is the whole answer to "which one".

**It produces no submission and no leaderboard score.** It produces one number
that decides where the next three weeks go. What does move the score is at the
bottom of this file.

---

## Setup

**Upload first:** `artifacts/weak_labels.csv` from this repo (1.6 MB) as a Kaggle
dataset. Call it anything - the notebook finds files by content, not by dataset
name.

**Attach these, and nothing else is required:**

| dataset | why |
|---|---|
| **RSNA Knee Abnormality Detection** | the competition data |
| **Knee MRI - Max-Span ...** | holds `raptor_ft_coatnet_v5_full_swa.pt`, the arm-0 encoder |
| **your `weak_labels.csv` upload** | the label variants |
| **OpenCV Python Headless** | only if `import cv2` fails; harmless to keep |
| **RSNA Knee LLM-read reports** | optional but do attach it - see below |

Everything else in the submission notebook's input list belongs to arms this
notebook does not run:

| dataset | used by | needed here |
|---|---|---|
| Knee MRI - Native 384 Co... | `raptor_ft_coatnet_v8_full_swa.pt`, arm 3 | no |
| Knee MRI - Native 384 De... | `raptor_ft_coatnet_v10_full.pt`, arm 1 | no |
| knee mri fold weights | Family A DINOv3 folds | no |
| RSNA Knee weights | Family A's 20 members | no |
| resnet-50-RadImageNet | Family C encoder | no |
| RSNA Knee V52 / E9 / E11 / E13 | Family C heads | no |
| RSNA Knee CoAt Residual | the coat-arm overlay | no |

Leaving them attached is now harmless - discovery prunes the DICOM trees and
bounds its depth, so it scans in seconds rather than walking 819,640 files.

**RSNA Knee LLM-read reports.** If that holds LLM-derived labels for the training
studies, it is exactly what week 3 was going to build. The notebook inspects every
small table in the attached datasets, prints the schema of anything with a study
id and label columns, and adds it to the gate as an extra arm. That turns the gate
from a simulated perturbation into a direct measurement: does a genuinely
different labeler beat the regex lexicon, through the same head, on the same
features? Trust that over the extrapolated slope if it appears.

It never fails the run. If the columns are named something the matcher does not
recognise, it prints them and continues, and we map them by hand next round.

**Settings:** GPU T4 x2, internet off. Run with **Save & Run All (Commit)**.

The first cell prints exactly what it discovered before doing any work. If
something is missing it lists every attached dataset and stops, so you find out
in thirty seconds rather than five hours in.

---

## What it does

1. **Timing probe.** fp16 against bf16 against fp32 on this GPU. The submission
   log already proves the mismatch exists - it prints `native bf16=False` for
   both T4s and then `amp bfloat16 (on=True)` - but not what it costs. If the
   probe reports bf16 slower than about 1.08x, set `AMP_PREF = 'auto'` in cell 23
   of the submission notebook. Family A only; B and C already use fp16.

2. **Encode.** Runs the Raptor v5 encoder over the training set and caches the
   per-window features. ~95 KB per study, ~420 MB for all 4,407. This is the part
   that changes the economics: after it, training a head is minutes, so the
   relabelling loop stops being a six-day item.

3. **The gate.** Trains the classifier head under five label sets and measures how
   much macro AUC is lost per unit of label corruption.

---

## Resuming

Built in, because an 8-hour encode will not always finish.

- Shards are written every 250 studies, `os.replace`'d into place, so a kill
  never leaves a half-written shard.
- `manifest.json` records progress after each shard.
- The loop exits cleanly at `TIME_BUDGET_H = 8.0`, well under the session limit,
  rather than being killed with output unsaved.
- **Gold studies are encoded first**, so even a run that stops at 20% leaves a
  usable validation set.

To continue: save the version, then add **this notebook's own output** as an input
dataset to the next run. Discovery finds the shards, already-encoded studies are
skipped, and it picks up where it stopped.

To re-run only the gate on an existing cache, set `MAX_STUDIES = 0`.

---

## Reading the result

| arm | labels |
|---|---|
| `ckpt` | the shipped head, not retrained - the reference to beat |
| `fix` | corrected lexicon, the baseline for the others |
| `noise10` | `fix` with 10% of cells resampled from the column marginal |
| `noise25` | `fix` with 25% resampled |
| `raw` | the original lexicon, before the four fixes |
| `cal` | `fix` through a global Platt map |

**Why perturbation instead of just comparing `raw` to `fix`.** The fixes change
the ranking of about 100 studies out of 4,407. Nothing measured on 58 gold
studies can resolve that; `raw` and `fix` will come out level and that tells you
nothing about whether *better labels in general* pay. Planting a large known
perturbation and measuring the slope is a question this sample size can answer.

- `ckpt` is the sanity gate. If no refit arm comes near it, the refit is broken
  and nothing else on the page is interpretable.
- `slope_per_unit_label_accuracy` x 0.11 is the ceiling on what a better labeler
  can buy, since the corrected lexicon disagrees with gold on 23% of cells and
  recovering half of that is ~11%.
- Under about 0.003, week 3 cannot pay for itself. The six days go to
  inference-time work and the efficiency prize, which is a separate $18,000 and
  far less contested.

### About `cal`

An earlier version of this plan recommended recalibrating the training targets,
off a real finding: the lexicon over-calls on all twelve labels, 77% cell
agreement with gold, 136 false positives against 24 false negatives.

**That recommendation was wrong.** It is kept as a control. Calibration is a
monotone map, so it leaves the ranking of the targets untouched and AUC cannot
see it; all it does is shrink the BCE gradient. In a simulation with the effect
planted in its favour it lost 0.048 macro. Expect `cal` to lose here too. If it
wins, something in the notebook is wrong.

The over-calling still matters where two differently-scaled sources get mixed,
such as blending model predictions with lexicon scores in the relabelling loop.
The fix there is to rank-normalise both, not to Platt-calibrate.

---

## What actually moves the leaderboard

Nothing in this notebook does. Being explicit, because it is easy to conflate
"run the notebook" with "get a score":

| change | score effect | status |
|---|---|---|
| study-major loop | **0.000**, bit-identical by construction | done |
| `AMP_PREF='auto'` | **0.000**, speed only | one word, after the probe |
| attach the missing `public0033` bag | **+0.002** if the real submission lacked it | check the log |
| a refit head on corrected labels as a new arm | [Guessing] +0.000 to +0.004 | needs this notebook first |

The first two buy roughly 40-60 minutes of the 9-hour budget. That headroom is
not a score, it is what makes it possible to add anything later.

The third is free and worth checking now: the log in `logs/` ends with
`[public0033] bag absent; exact 0.937 parent retained`. That run did not produce
the 0.939 configuration. A missing dataset costs 0.002 with one printed line and
no error. Near 0.939 that is about 180 leaderboard places. **Grep every run for
`[public0033]` before selecting it as a final.**

## What to send back

`/kaggle/working/premise_test.json` and `timing_probe.json`, plus the printed
output of the last two cells.
