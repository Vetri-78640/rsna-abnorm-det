---
type: entity
updated: 2026-09-22
status: current
sources: [scripts/audit_labels.py run 2026-09-08]
---

# The dataset

**Only 58 of 4,407 training studies carry labels**, all twelve or none. The other
4,349 have a free-text radiology report and nothing else. [Certain, measured]

So almost everyone trains on labels they manufactured from the reports, and this
is the defining constraint of the competition.

## Facts, all measured here

- **The 58 gold studies are trauma-enriched, not random.** Fracture fires 5.2x
  more often on them than on the rest (p=4e-11), Contusion 2.3x, ACL 2.2x. OA and
  Baker's are flat. Gold prevalence is **not** test prevalence.
- **Reports are 39.3% English.** tr 12.0, es 11.9, el 7.3, hr 6.8, de 5.8, bg/ru 5.0.
- **`Fat_Suppression == Fluid_Sensitive` in all 24,371 train and 15 test series.**
  Six plane x contrast slots exist, not twelve.
- `Report` exists in train only. Text can make targets, never an inference input.
- 819,640 DICOM files, ~570 GB. After slice selection and a 224 px resize the whole
  visual input is **11.12 GiB** - see [[compute]].
- 86 DICOM tags survive the organisers' allowlist. Which 86 is unverified.

## The gold labels are image-derived and deliberately disagree with reports

[Certain, host] Annotated from the images by radiologists. An audit found 82.5%
report-label agreement; the host called the gap "a major design choice". So any
report-derived labeler is capped near 82%. See [[label-premise]].

Related: [[label-premise]], [[not-addressed]], [[competition]]
