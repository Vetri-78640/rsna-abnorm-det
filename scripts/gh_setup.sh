#!/usr/bin/env bash
# Create labels, milestones and issues for the rest of the competition.
# Run ONCE, after deciding repo visibility (wiki/decisions/D005-repo-visibility.md):
# on a public repo every issue body below is public too.
set -euo pipefail
R=Vetri-78640/rsna-abnorm-det

lab() { gh label create "$1" --repo "$R" --color "$2" --description "$3" --force >/dev/null; }
lab blocker    B60205 "blocks other work"
lab experiment 1D76DB "produces a number on CV or the LB"
lab decision   5319E7 "a choice with a wiki/decisions page"
lab infra      0E8A16 "pipeline, cache, notebook plumbing"
lab submission FBCA04 "touches what gets submitted"

ms() { gh api "repos/$R/milestones" -f title="$1" -f due_on="$2T23:59:00Z" -f description="$3" --jq .number; }
M1=$(ms "M1 control model"      2026-09-29 "Pixel cache with our sampling, 5-fold control, noise floor, gate result.")
M2=$(ms "M2 sampling ablation"  2026-10-06 "The thesis test. Under +0.002 on our CV means the thesis is wrong.")
M3=$(ms "M3 labels and blend"   2026-10-13 "Best LLM key, synovitis fill, blend as a decorrelated member.")
M4=$(ms "M4 final submissions"  2026-10-22 "Two finals chosen by CV, runtime verified under 9 h.")

iss() { gh issue create --repo "$R" --milestone "$1" --label "$2" --title "$3" --body "$4" >/dev/null; echo "  + $3"; }

iss "M1 control model" "decision,blocker" "Decide repo visibility" \
"Repo was created public. Recommendation: private until 2026-10-22. Competition data is gitignored either way, but a public repo hands src/sampling.py to every competitor. See wiki/decisions/D005-repo-visibility.md."

iss "M1 control model" "experiment,blocker" "Get the encode-and-gate result" \
"Run notebooks/RUN_THIS_encode_and_gate.ipynb to completion. Report ckpt gold AUC against the extractor's 0.8625 on the same 58 (the Tucker diagnostic), and the LLM-key arm. See wiki/experiments/E003-encode-and-gate.md."

iss "M1 control model" "infra" "Build the 224 px pixel cache with our slice selection" \
"4,407 x 6 slots x 9 slices x 224 x 224 uint8 = 11.12 GiB. Use src/sampling.py, not the public sampling, so the M2 ablation has something to compare. Verify against a DICOM decode on a few studies before trusting it."

iss "M1 control model" "experiment" "Train a 5-fold DINOv3 ViT-S control" \
"On the best public LLM key. ~6.5 h. Print which backbone actually loaded every run - a silent fallback logs a plausible score. Record per-label OOF AUC."

iss "M1 control model" "experiment" "Measure the CV noise floor" \
"Same config, different seed. Without this no later delta is interpretable. One team measured 0.0020 at 3 folds."

iss "M1 control model" "experiment,submission" "Validate AMP_PREF='auto' on the 0.943 notebook" \
"bf16 is 4.72x slower than fp16 on T4 (measured) but switching changes the numerics, so it is not score-neutral. The 0.943 author kept bf16 deliberately. Needs one validation submission. See wiki/concepts/preprocessing-contract.md."

iss "M2 sampling ablation" "experiment,blocker" "Ablate our sampling against the public sampling" \
"The thesis. Same folds, same seed. Judge by how many of 12 labels move, not the macro alone - a real effect lifts ~10 of 12. Under +0.002 the thesis is wrong; redirect to the efficiency prize. See wiki/decisions/D001-train-not-just-blend.md."

iss "M2 sampling ablation" "experiment" "Resolution: 224 against 288" \
"Community reports resolution pays. Price it against the 9 h limit before adopting."

iss "M3 labels and blend" "experiment" "Fill Synovitis undecided cells from Effusion" \
"Targeted only. Reported +0.0093 on the label key; the blanket 12-label version was worse. See wiki/concepts/not-addressed.md."

iss "M3 labels and blend" "experiment" "Rank correlation of our model against every public member" \
"Decides what our member is worth to the blend. The public pack is correlated with itself. See wiki/concepts/ensemble-correlation.md."

iss "M3 labels and blend" "experiment,submission" "Blend our model into the 0.943 notebook" \
"Weight by decorrelation, group-level weights shrunk toward global. Must fit under 9 h."

iss "M4 final submissions" "submission" "Runtime check: 0.943 plus our member under 9 h" \
"Commit on real hardware, save the log, run scripts/budget_model.py --from-log."

iss "M4 final submissions" "decision,submission" "Select the two finals by CV" \
"Never by public LB. Leaders have 40-120 submissions and the top spread sits inside one SE. See wiki/decisions/D002-select-finals-by-cv.md."

echo "done: 5 labels, 4 milestones, 13 issues"
