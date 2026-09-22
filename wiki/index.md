# Wiki index

Every page, one line each. Read [[overview]] first. Pages are atomic: open only
what the question needs. `[[name]]` links refer to the page file of that name.

## Start here

- [overview](overview.md) - current state, the thesis, and the next action
- [log](log.md) - append-only history; check it before trusting any page
- [SCHEMA](SCHEMA.md) - how this wiki is maintained
- [glossary](glossary.md) - what arm, slot, key, gold, commit run and the rest mean here
- [open-questions](open-questions.md) - what we do not know yet, and what would settle it

## Entities - the things

- [competition](entities/competition.md) - RSNA Knee Abnormality Detection on Kaggle: 12 binary findings per knee MRI, macro AUC, 9-hour inference limit, final submission 2026-10-22.
- [compute](entities/compute.md) - 2x Kaggle T4 (15 GiB each, no native bf16) at 30 GPU-hours a week is enough to train: a 5-fold 224 px experiment is ~6.5 h.
- [dataset](entities/dataset.md) - Only 58 of 4,407 training studies carry labels, all twelve or none.
- [host](entities/host.md) - The host (Po-Hao "Howard" Chen, RSNA) has ruled commercial LLM APIs permitted for label extraction and confirmed report-image disagreement is delibera
- [model-families](entities/model-families.md) - The public pack is three families - a DINOv3 slot model, a CoAtNet Raptor model, and a RadImageNet ResNet - all fine-tuned by other competitors and sh
- [notebook-0939](entities/notebook-0939.md) **[superseded]** - The previous baseline, superseded by notebook-0943, and the notebook where 20 defects were found by executing it.
- [notebook-0943](entities/notebook-0943.md) - Our current best (0.943): an inference-only blend of public checkpoints that adds two CoAtNet depth-geometry readers, cached decoding and fail-closed 
- [public-datasets](entities/public-datasets.md) - Other competitors have published pre-decoded volumes that skip the DICOM I/O, and several LLM label keys that beat a regex; all are permitted inputs.

## Concepts - the ideas

- [ensemble-correlation](concepts/ensemble-correlation.md) - Everyone on the public LB blends the same highly correlated pack, so one genuinely different member is worth far more than another correlated one.
- [label-premise](concepts/label-premise.md) - Better labels help a little, but our lexicon is already close to the best public LLM key and the gold labels deliberately disagree with reports - so l
- [noise-floor](concepts/noise-floor.md) - Most differences people chase in this competition are inside the noise.
- [not-addressed](concepts/not-addressed.md) - A quarter of report-derived label cells are "not addressed", and silence is a negative for some findings but uninformative for others.
- [permutation-invariance](concepts/permutation-invariance.md) - The public pooling heads ignore slice order, so the slice-ordering bug cannot swap medial for lateral the way older docs claimed.
- [preprocessing-contract](concepts/preprocessing-contract.md) - Feeding a checkpoint inputs prepared differently from its training fails silently - no error, a plausible curve, a wrong conclusion.
- [slice-selection](concepts/slice-selection.md) - The largest measured single lever in the competition.

## Decisions - what we chose and why

- [D001-train-not-just-blend](decisions/D001-train-not-just-blend.md) - Decision: train one model with our slice selection on the best public LLM label key, and add it to the public ensemble as a decorrelated member.
- [D002-select-finals-by-cv](decisions/D002-select-finals-by-cv.md) - Decision: choose final submissions on our own cross-validation.
- [D003-no-bigger-encoder](decisions/D003-no-bigger-encoder.md) - Decision: stay at ViT-S and the current backbones - two teams measured ViT-B as a null.
- [D004-no-target-calibration](decisions/D004-no-target-calibration.md) - Decision: do not Platt-calibrate lexicon scores before training.
- [D005-repo-visibility](decisions/D005-repo-visibility.md) - Vetri-78640/rsna-abnorm-det was created PUBLIC on 2026-09-22.

## Experiments - what we ran

- [E001-lexicon-patch](experiments/E001-lexicon-patch.md) - Hypothesis: fixing three lexicon bugs raises gold AUC on the OA labels.
- [E002-study-major-loop](experiments/E002-study-major-loop.md) - Hypothesis: the 0.939 notebook decodes each study 4x; reordering removes the waste with no accuracy change.
- [E003-encode-and-gate](experiments/E003-encode-and-gate.md) **[in-progress]** - Measures whether label quality is worth anything on this data, by caching encoder features once and training the head under several label sets.
- [E004-submissions](experiments/E004-submissions.md) - Our best public score is 0.941, but the field inflated so fast that it fell from rank 193 to 812 in twelve days without regressing.

## How-to

- [github-workflow](howto/github-workflow.md) - Work is tracked as one issue per task, grouped into four dated milestones, with one branch and one PR per issue that closes it.
- [read-the-forum](howto/read-the-forum.md) - The Kaggle forum cannot be read by any tool here - ask for a paste.
- [run-a-kaggle-notebook](howto/run-a-kaggle-notebook.md) - Commit with GPU T4 x2 and internet off, attach datasets by content, resume from the notebook's own output, and grep the log before trusting a run.

## Raw sources - verbatim, external

- [forum](raw/forum.md) - Kaggle forum threads and host rulings, transcribed
- [research](raw/research.md) - four literature reviews from research agents, 1,400 lines

## Archive - our dated reasoning, frozen

Where these disagree with a page above, the page wins.

- [FINDINGS](archive/FINDINGS.md) - 20 reproduced defects in the 0.939 notebook, full detail
- [STRATEGY](archive/STRATEGY.md) - leaderboard arithmetic and lever ranking, 2026-09-10
- [PLAN](archive/PLAN.md) - the six-week schedule as of 2026-09-10
- [extras](archive/extras.md) - competition mechanics and rules, long form
