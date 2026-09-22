---
type: concept
updated: 2026-09-22
status: current
sources: [this project]
---

# Glossary

Terms that mean something specific in this project. Read this before any other page
if the vocabulary is unfamiliar.

## Data

| term | meaning |
|---|---|
| **study** | one knee MRI exam; the unit being predicted. Keyed by `StudyInstanceUID` |
| **series** | one acquisition within a study: one plane, one contrast. A study has ~5 |
| **plane** | sagittal, coronal or axial |
| **fat-sat / fluid-sensitive** | two contrast flags; in this dataset they are always equal, see [[dataset]] |
| **gold** | the 58 training studies with real radiologist labels |
| **report** | free-text radiology report; train only, never at inference |
| **weak label** | a training target manufactured from a report |
| **lexicon** | the regex report labeller from the public notebook, patched in `src/lexicon_patch.py` |
| **label key** | a full set of weak labels for all studies; "LLM key" = one made by an LLM |
| **not addressed** | a report that says nothing about a finding; see [[not-addressed]] |

## Models and notebooks

| term | meaning |
|---|---|
| **family** | one of the three model groups in the public pack, A/B/C; see [[model-families]] |
| **arm** | one member configuration inside a family, e.g. Family B arm 0 |
| **member** | one checkpoint in the ensemble |
| **slot** | a plane x contrast position in the input, e.g. sagittal fat-sat |
| **window / triplet** | three adjacent slices stacked as RGB channels for a 2D backbone |
| **head** | the pooling + classifier on top of the encoder; "head refit" = retraining only this |
| **pixel cache / corpus** | pre-decoded volumes saved to disk, skipping DICOM I/O |
| **TTA** | test-time augmentation; arm 2 is TTA on arm 0 |
| **decorrelated member** | a model whose errors differ from the pack's; see [[ensemble-correlation]] |

## Evaluation

| term | meaning |
|---|---|
| **macro AUC** | mean of the 12 per-label ROC AUCs; the metric |
| **CV / OOF** | cross-validation; out-of-fold predictions scored against weak labels |
| **public / private LB** | leaderboard on a sample of the test set / on the rest, which decides placing |
| **noise floor** | the smallest difference that is real; see [[noise-floor]] |
| **SE** | standard error; Hanley-McNeil for AUC |

## Kaggle

| term | meaning |
|---|---|
| **commit run** | "Save & Run All"; runs on the 3-study placeholder test set, not the real one |
| **submission run** | Kaggle's rerun on the hidden 1,322-study test set |
| **fail-closed** | raise instead of writing a degraded `submission.csv`; see [[notebook-0943]] |
| **attach** | add a dataset or notebook output as a read-only input |
