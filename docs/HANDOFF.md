# Handoff prompt for a new session

Copy everything between the rulers into the first message of a fresh session.

---

I'm working on the RSNA Knee Abnormalities Detection Kaggle competition in
`/Users/vetri/Downloads/Personal_Project/Kaggle/rsna_knee`. Earlier sessions did
the research, built `src/`, and ran the label audit. Start by reading, in this
order:

1. `README.md` - where this stands and what held up
2. `docs/STRATEGY.md` - the plan, the leaderboard arithmetic, the lever ranking
3. `docs/community.md` - what other teams measured and what the host has ruled
4. `docs/PLAN.md` - the schedule
5. `docs/FINDINGS.md` - 20 defects in the public notebook, each reproduced
6. `docs/extras.md` - competition mechanics and what is still unverified
7. `docs/researched.md` - the research archive (long; skim the decision summary)

Then run `./run_tests.sh` to confirm the 52 tests still pass.

**The premise, in one paragraph.** The public 0.939 notebook trains nothing - it
blends other competitors' fine-tuned checkpoints on top of Meta's DINOv3 and
Google's CoAtNet, so everyone converges there and blending better buys almost
nothing. Those checkpoints were all trained on weak labels from one regex lexicon
that has verified bugs. The plan is to compete on data quality rather than
architecture: fix the labels and the DICOM geometry, then retrain, which also
yields models genuinely decorrelated from the public pack. Keep the pretrained
backbones - the Medical Slice Transformer result says DINOv2 per slice plus a
transformer across slices is already the right shape for knee MRI.

**Read the premise sceptically, but note the reading was corrected.** An earlier
session argued that because the lexicon scores 0.862 on gold while the
checkpoints score 0.939 on test, the lexicon is a soft ceiling. A top-15
competitor argues the opposite from the same fact: an image model far exceeding
its teacher means the labels are what is binding. His is the more useful reading
because it is falsifiable - compare the image model's AUC on the 58 gold studies
against the extractor's 0.8625 on the same 58. See `FINDINGS.md` item 22.

What is measured, by other teams: an LLM key scores 0.8780 on gold against a
regex at 0.8136, but our patched lexicon is already at 0.8625, so the real gap is
+0.0155 - below the 0.02 noise floor a 58-study ruler supports. The host has also
confirmed the gold labels deliberately contradict the reports, capping any
report-derived labeler near 82% agreement. `FINDINGS.md` item 21.

**What is built and tested** (`src/`): canonical slice ordering that fixes the
vendor-dependent normal sign, rigorous laterality, sequence typing with GRE and IR
checked before TR/TE, anatomy-aware slice sampling with per-label routing,
per-series and muscle-referenced normalisation with a fat-suppression failure
detector, and four lexicon fixes with a regression suite. `scripts/` has metadata
fetch, the label audit, a header audit, and the 9-hour budget model.

**What the label audit settled** (it has been run; the CSVs are in `data/`):

- 58 of 4,407 studies carry gold labels, all twelve or none.
- Those 58 are trauma-enriched, not a random sample. Fracture fires 5.2x more
  often on them than on the rest, p=4e-11. Gold prevalence is not test prevalence,
  and effort cannot be allocated by rarity measured on it.
- Reports are 39.3% English. The labeler must be multilingual-first.
- `Fat_Suppression` and `Fluid_Sensitive` are the same column in all 24,371 train
  and 15 test series. Six plane-by-contrast slots exist, not twelve.
- The lexicon over-calls on all twelve labels: 77.0% cell agreement with gold,
  136 false positives against 24 false negatives, and every agreement-maximising
  threshold between 0.66 and 0.96.

**What is done in the notebook.** `_KE_SRC` in cell 26 now runs studies-outermost
with a per-study header and pixel cache, verified bit-identical to the arm-major
loop on synthetic studies (75% of header reads and 61% of pixel decodes removed,
`max abs diff 0.0`). It falls back to arm-major automatically on exception.

**What is not done:** nothing is wired into a training loop. No LLM labeler, no
relabelling loop, no retraining. `audit_headers.py` has never run.

**Timing, from a real commit log** (`logs/`, 3-study placeholder, so fixed costs
are 31% of it and `budget_model.py --from-log` strips them):

- Marginal 20.5 s/study, extrapolating to **5h33m** for the 1,322-study hidden
  set. Floor, not estimate: 3 studies sit in page cache and this is I/O bound.
- **Family B is 11.0 of those 20.5 seconds** for 0.60 of the blend weight, so the
  study-major restructure went to the right place. A header read costs 4.1 ms;
  595,000 saved reads is 40 minutes.
- [Certain] the notebook logs `native bf16=False` on T4 and then runs
  `amp bfloat16 (on=True)`. See `FINDINGS.md` item 18. One-word fix in cell 23.
- [Certain] that run printed `[public0033] bag absent; exact 0.937 parent
  retained`. A missing dataset silently costs 0.002. See item 20.

**Compute:** Kaggle only, T4 x2, 30 h/week. Full retraining is infeasible - one
CoAtNet arm is ~57 h. The whole plan therefore runs through cached encoder
features (`notebooks/01`), which turns head training into minutes.

**The three things blocking progress, in order:**

1. **Build the pixel cache with our slice selection and train a control.** At
   224 px the whole visual input is 11.12 GiB and one fold is 76 min, so a 5-fold
   run is 6.5 h. Measure the noise floor with a second seed before interpreting
   any delta. Print which backbone loaded - a silent fallback logs a plausible
   score.
2. **Ablate our sampling against the public one.** This is the thesis: crop
   geometry and slice selection is the largest measured lever in the competition
   (+0.0059, 10 of 12 labels). If ours lands under +0.002 on our own CV, the
   thesis is wrong and the weeks go to the efficiency prize instead.
3. **Run `notebooks/RUN_THIS_encode_and_gate.ipynb`** for the image-model-versus-
   teacher diagnostic on the gold 58. Our extractor scores 0.8625 there; the
   `ckpt` arm gives the other half. See `community.md`.

**Do not spend GPU hours on a larger encoder.** Two independent teams measured
ViT-S to ViT-B at +0.0011 against a 0.0020 noise floor.

**Working style:** I want [Certain] / [Likely] / [Guessing] markers on claims,
concise and direct answers, no emojis, no em dashes, sentence case headers. Verify
things by executing them rather than by reading - every real bug found in this
repo so far was found that way, including four in its own code. Challenge
assumptions, tell me when a recommendation from the research is wrong, and say
plainly when something is unverified rather than smoothing over it.

Do not re-run the research agents. Four already reported and everything they found
is in `docs/researched.md`.

---

## Notes for whoever writes the next handoff

Keep the three blockers at the top and current. The docs are the memory: if a
session learns something durable it belongs in a `.md` file before the session
ends, not in the conversation.

Two things this repo has now learned the hard way, worth preserving:

1. **A correct fix can be wrong in combination with the code it lands in.** The
   `GLOBAL_OA` propagation fix was right on its own terms and net-negative in
   practice, because it promoted a sloppy regex from decorative to load-bearing.
   Measure every fix against gold before believing it.
2. **Synthetic tests can assert a world the dataset does not contain.**
   `test_fat_sat_and_fluid_are_independent_axes` passed for weeks against data in
   which the two flags are perfectly collinear. Tests written from the literature
   need one check against the real distribution.
3. **The forum is unreachable programmatically.** No CLI command, the internal
   API returns 403 on `forums.get`, and the pages render client-side. Ask for a
   paste; do not spend turns re-attempting. Everything read so far is transcribed
   in `community.md`.
4. **Recalibrating training targets cannot help an AUC metric.** A session
   recommended it off a real finding - the lexicon over-calls on all twelve
   labels - and it was wrong: calibration is monotone, so it leaves the target
   ranking untouched while shrinking the BCE gradient. A simulation with the
   effect planted in its favour showed it losing 0.048 macro. Before recommending
   a transform, ask what the metric can see.
