---
type: entity
updated: 2026-09-22
status: current
sources: [data/*.csv measured 2026-09-08 and 2026-09-22, scripts/audit_labels.py]
---

# The dataset

Only 58 of 4,407 training studies carry labels; the rest have a radiology report,
five-ish MRI series, and nothing else. Every number on this page was measured on the
competition files unless marked otherwise.

## The five files

| file | shape | columns |
|---|---|---|
| `train.csv` | 4,407 x 14 | `StudyInstanceUID`, `Report`, 12 label columns |
| `train_series.csv` | 24,371 x 5 | `StudyInstanceUID`, `SeriesInstanceUID`, `Fluid_Sensitive`, `Fat_Suppression`, `Anatomical_Plane` |
| `test.csv` | 3 x 1 | `StudyInstanceUID` - a **placeholder**; the hidden set is 1,322 studies |
| `test_series.csv` | 15 x 5 | same columns as `train_series.csv` |
| `sample_submission.csv` | 3 x 13 | `StudyInstanceUID` + 12 labels, all 0.5 |

DICOMs live at `{train,test}_series/<StudyInstanceUID>/<SeriesInstanceUID>/*.dcm`:
819,640 files, ~570 GB. Columns are exactly as spelled above - note the apostrophe
in `Baker's` and the spaces in the multi-word labels.

## Labels

- Label columns are `float64`: **NaN** for the 4,349 unlabelled studies, **0 or 1**
  for the 58 gold. No other values. [Certain]
- **Every gold study has at least one positive.** Mean 4.14 positives, min 1, max 9.
  There is no all-negative study in gold. [Certain]
- **Gold is trauma-enriched, not random.** Fracture fires 5.2x more often on gold
  than on the rest (p=4e-11), Contusion 2.3x, ACL 2.2x; OA and Baker's are flat.
  Gold prevalence is not test prevalence. [Certain]
- Gold labels are image-derived and deliberately disagree with the reports - see
  [[host]] and [[label-premise]].

## Identifiers

- Every UID sits under `1.2.826.0.1.3680043.8.498` - **pydicom's anonymisation
  root**. UIDs were regenerated and carry no site, date or ordering information.
  [Certain]
- Study and series UIDs are unique. Every train study has series and vice versa.
  **Zero overlap between train and test studies.** [Certain]
- `PatientID` survives in the DICOM headers. Whether it repeats across studies is
  unknown - see [[open-questions]].

## Series and slots

| | Sagittal | Coronal | Axial |
|---|---|---|---|
| series | 9,864 | 8,609 | 5,898 |

- Series per study: **min 3, median 5, mean 5.53, max 14.** [Certain]
- `Fat_Suppression == Fluid_Sensitive` in **every** series (14,010 ones, 10,361
  zeros). It is one flag, and it tracks **fat suppression, not fluid sensitivity** -
  a real T2 TSE without fat-sat is labelled 0/0. See [[dicom-headers]].

**Slot availability** - share of studies missing each (plane, fat-sat) slot:

| slot | missing in |
|---|---|
| Axial fat-sat | **0.0%** |
| Sagittal non-FS | 3.2% |
| Coronal fat-sat | 3.6% |
| Sagittal fat-sat | 5.8% |
| Coronal non-FS | **22.7%** |
| Axial non-FS | **80.6%** |

So **axial non-fat-sat is effectively not a slot**. Only **566 studies (12.8%) have
all six**; 2,516 are missing only axial non-FS; 745 miss axial non-FS and coronal
non-FS. **Any model must handle missing slots** - the Raptor family's
`("Axial", -1)` "any axial" slot is the right design for this.

**Selection choices:** 13.6% of filled slots (2,898 of 21,334) have more than one
candidate series. How a pipeline picks among them matters for those.

## Slices per series

Measured on **all 24,386 series** from the complete file listing. The implied total
is **570 GB against the stated 569.76 GB**, and 819,635 slices plus the 5 CSVs is
exactly the stated 819,640 files - so this is the whole dataset, not a sample.

| | slices |
|---|---|
| min | 11 |
| p5 / p25 | 18 / 25 |
| **median** | **30** |
| p75 / p95 | 34 / 45 |
| p99 / max | 160 / 320 |

8.4% of series have under 20 slices and **2.9% have over 100** - the tail is axial
and sagittal 3D acquisitions (axial fat-sat p95 is 144 slices). Slices per study:
median 162, p95 369, max 632. Total 819,635 slices.

The older claim "20-45 slices, median 30" was a research estimate. The median is
right; the tails are wider than stated in both directions.

## Reports

- **Length:** min 52 chars, p10 288, median 977, p90 2,118, max 4,743. 41 reports
  are under 100 chars. None empty. [Certain]
- **Language:** 39.3% English; tr 12.0, es 11.9, el 7.3, hr 6.8, de 5.8, bg/ru 5.0,
  nl 3.4, fr 1.8, unknown 6.6. [Certain, heuristic detector]
- **Structure:** 54% have a findings section, 52% an impression/conclusion.
- **Effectively non-contrast.** 403 reports mention contrast, but almost all say
  "non-contrast protocol", "wo contrast" or "no contrast was administered". About 4
  studies actually used gadolinium. This is why Synovitis is the hardest label - it
  is normally judged on contrast images. [Certain]
- **Dates are scrubbed** to `[date...]`-style placeholders.
- **Side** is stated in ~30% of reports; both sides in 0.2%.
- **Strong per-site templates.** One phrase ("using a standard non-contrast
  protocol") appears 331 times, another header template 351 times. [Likely] reports
  fingerprint the site, which is useful for grouped CV folds.
- 12% mention a prior or comparison exam.

## What we still do not know

Slices per series across the whole set (crawling), how common the fluid misfiling
is, whether `Laterality` is present everywhere, and whether patients repeat. See
[[open-questions]] and `notebooks/header_census.ipynb`.

Related: [[dicom-headers]], [[label-premise]], [[not-addressed]], [[competition]]
