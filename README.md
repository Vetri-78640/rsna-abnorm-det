# RSNA Knee Abnormalities Detection

Predict twelve binary findings per knee MRI study. Metric is macro-averaged AUC ROC.
Final submission 2026-10-22. **The submission notebook must finish inside 9 hours** -
the public one already budgets 8, so efficiency is on the critical path, not a
side quest.

Targets - ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA,
PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture.

## Where this stands

**Rank 193 of 3,434, score 0.940**, on the public 0.939 notebook. Top is 0.954,
prize money starts at 0.950. Public notebooks cap around 0.942, so we are at the
public ceiling and the rest is private work.

The plan and the reasoning behind it are in **`wiki/archive/STRATEGY.md`**. In short:

- The top-5 spread is 0.003, inside one standard error on this test set. The
  leaders have 42-119 submissions against our 3, so part of their margin is
  public-LB overfit. **Select finals by CV, never by public LB.**
- Retraining turned out to be affordable after all: at 224 px the whole visual
  input is 11.12 GiB and one fold is 76 minutes, so a 5-fold experiment is 6.5 h.
- The largest measured lever in the whole competition is **crop geometry and
  slice selection** (+0.0059, moving 10 of 12 labels). Encoder size is a measured
  null. `src/sampling.py` and `src/geometry.py` are that lever, and ours is built
  from the radiology rather than a grid search.

So: train one model with our slice selection, on the best public LLM label key,
and blend it into the public pack as a genuinely decorrelated member. The pack is
highly correlated with itself - one of its four arms is another arm's checkpoint
with the slice triplet reversed.

Honest expectation: **0.944 to 0.947, rank 30 to 60.** The route into the top ten
is arriving there with no public-LB overfit while part of the leading group
regresses on private.

## The original premise, and how it has held up

The public 0.939 notebook trains nothing. It loads other competitors' fine-tuned
checkpoints and blends them, on top of Meta's DINOv3 and Google's CoAtNet. Those
checkpoints were all trained on weak labels from one regex lexicon, and that
lexicon has verified defects.

Partly borne out, partly not:

- **Held:** the ensemble is saturated and correlated, and everyone converges near
  0.939. Confirmed by the leaderboard - 25% of the field sits on two notebooks.
- **Held:** better labels beat a regex. An LLM key scores 0.8780 on the gold 58
  against a regex at 0.8136.
- **Did not hold:** that the lexicon is the binding ceiling. Our patched lexicon
  is already at 0.8625, so the closable gap is +0.0155, which is below the 0.02
  noise floor a 58-study ruler supports. And the host has confirmed the gold
  labels deliberately contradict the reports at about 82% agreement, capping any
  report-derived labeler.
- **Did not hold:** that fixing the slice ordering matters much. The pooling head
  is permutation-invariant over slices, verified by execution, so the ordering
  bug cannot swap medial for lateral the way `FINDINGS.md` item 4 claimed.

## Layout

```
src/
  geometry.py         canonical slice ordering, laterality, physical spacing
  sequence_typing.py  T1/PD/IW/T2/GRE/IR typing, continuous conditioning features
  sampling.py         anatomy-aware slice bands, 6 observed slots, per-label routing
  normalize.py        per-series intensity normalisation, fat-sat failure QC
  lexicon_base.py     the public notebook's report lexicon, extracted verbatim
  lexicon_patch.py    four verified fixes, applied by monkeypatch
notebooks/
  RUN_THIS_...        encode once, then measure what label quality is worth
artifacts/
  weak_labels.csv     raw / fixed / calibrated lexicon labels + the gold 58
scripts/
  fetch_metadata.sh   pull the CSVs only, not the 570 GB
  audit_labels.py     gold coverage, prevalence, language mix, lexicon scorecard
  audit_headers.py    tag survival, slice-normal signs, laterality, geometry
  budget_model.py     9h inference budget; --from-log calibrates on a real run
tests/                52 tests, no data or GPU required
wiki/                 the knowledge base; start at wiki/overview.md
```

## Quick start

```bash
./run_tests.sh                          # 52 tests, ~2 seconds
./scripts/fetch_metadata.sh data        # needs competition rules accepted
python3 scripts/audit_labels.py data
python3 scripts/audit_headers.py data/train_series --limit 400   # needs pydicom
python3 scripts/budget_model.py                          # where the 9 hours go
```

`audit_labels.py` has been run. What it said:

- **58 of 4,407 studies carry gold labels**, all twelve or none.
- **Those 58 are trauma-enriched**, not a random sample - Fracture fires 5.2x
  more often on them than on the rest. Gold prevalence is not test prevalence.
- **Reports are 39.3% English.** The labeler has to be multilingual-first.
- **`Fat_Suppression` and `Fluid_Sensitive` are the same column** in all 24,371
  train and 15 test series. Six contrast-by-plane slots exist, not twelve.
- **The lexicon over-calls on every label**: 77.0% agreement with gold, 136 false
  positives against 24 false negatives, every optimal threshold above 0.5.
- **The lexicon patch was net negative** until its cause was found and fixed.

## Status

Done and tested:

- Canonical slice ordering, so the vendor's choice of IOP sign no longer flips
  medial and lateral.
- Rigorous laterality that prefers the DICOM tag and refuses to guess from a
  geometric x sign.
- Sequence typing with GRE and inversion recovery checked before the TR/TE rules,
  and intermediate-weighted split out of PD.
- Slice sampling that never discards the stack ends, plus per-label anatomical
  bands and a plane-by-contrast slot grid, defaulting to the six slots the
  organisers' metadata can actually fill.
- Per-series and muscle-referenced intensity normalisation, and an image-based
  fat-suppression failure detector.
- Three lexicon fixes plus a fourth found by measuring them, with a regression
  suite proving the cases that already worked are untouched.
- The label audit, run against the real CSVs.
- Studies-outermost inference in the notebook. Arms 0 and 2 share a byte-identical
  volume, both slot schemes select the same series, and arms 0, 1 and 2 pick the
  same file indices - so headers are read once per study instead of four times.
  Verified bit-identical against the arm-major loop on synthetic studies:
  75% of header reads and 61% of pixel decodes removed, `max abs diff 0.0`.
  Falls back to arm-major automatically if the three resident checkpoints do not
  fit.

Ready to run on Kaggle - one notebook, see `notebooks/README.md`:

`RUN_THIS_encode_and_gate.ipynb` caches the encoder's features (resumable, gold
first) and then measures macro AUC lost per unit of label corruption, which is
the only form of the week-3 question that 58 gold studies can answer. It also
prices the bf16-on-T4 mismatch the run log exposed. It produces no submission.

Not started - needs the DICOMs, and for the last two, a GPU:

- `audit_headers.py`: laterality resolution rate, the 86-tag allowlist, and
  whether TE can recover the fluid-sensitivity axis the organisers collapsed.
- LLM report labeler and the image-model relabelling loop.
- Retraining on corrected labels.

## Conventions

After `geometry.py` ordering and laterality mirroring, slice index runs, for both
knees:

| plane | 0.0 | 1.0 |
|---|---|---|
| sagittal | medial | lateral |
| coronal | anterior | posterior |
| axial | inferior | superior |

Every band in `sampling.py` assumes this. The anatomical bands are priors from
the radiology literature, not measurements from this dataset - fit them
empirically once the data is in hand.
