---
type: entity
updated: 2026-09-22
status: current
sources: [kaggle datasets list/files]
---

# Public datasets worth knowing

Other competitors have published pre-decoded volumes that skip the DICOM I/O, and
several LLM label keys that beat a regex; all are permitted inputs.

## Pre-decoded volumes - skip the DICOM I/O

| dataset | contents | verified |
|---|---|---|
| `dreaddevelopment/knee-raptor-corpus` | `all_vols.npy` 15.9 GB | **exactly 2,200 x 64 x 336 x 336 uint8** = arm 0's `build_study` output |
| `dreaddevelopment/knee-raptor-corpus-ext` | `extra_vols.npy` 6.0 GB, ~830 studies | layout not yet confirmed |
| stevenleehans pixel cache notebook | 4,407 x 6 x 9 x 224 x 224 = 11.12 GiB | reported, not reproduced |

The encode notebook verifies the corpus against our own `build_study` before
using it. See [[E003-encode-and-gate]].

## LLM label keys

| dataset | notes |
|---|---|
| `pilkwang/rsna-knee-llm-labels` | first published (2026-08-06); `report_labels_v2.csv`, 12/12 labels |
| `dreaddevelopment/rsna-knee-labels` | "LLM Report-Distilled Soft Labels" |
| barun2104, lixin73, stevenleehans | also published |

## Other

- `xxxx0314/rsna-knee-omnirad-train-features` - 6.4 MB, too small to be per-window
- `dariushafshar/rsna-knee-2026-grouped-cv-folds` - grouped CV folds

Related: [[not-addressed]], [[label-premise]], [[compute]]
