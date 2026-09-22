# RSNA Knee Abnormality Detection - project instructions

Kaggle competition. 12 binary findings per knee MRI, macro AUC, 9-hour inference
limit, final submission **2026-10-22**. Owner: Vetri (Kaggle `imvetri0`, GitHub
`Vetri-78640`).

## Read before doing anything

1. `wiki/overview.md` - current state, thesis, next action. Two minutes.
2. `wiki/index.md` - one line per page. Open only the pages the task needs.
3. `wiki/log.md` - what changed recently. Check it before trusting any page.

**The wiki is the source of truth.** `docs/` is the long-form archive; where they
disagree, the wiki wins. Maintenance rules are in `wiki/SCHEMA.md`.

## Hard rules

- **Never commit or push competition data.** `data/`, `logs/` and
  `artifacts/weak_labels.csv` (holds the 58 gold labels) are gitignored.
  Redistributing competition data breaks the rules.
- **Every module in `src/` is retrain-only.** Never apply its preprocessing at
  inference to a public checkpoint - that is a train/test mismatch.
- **Select final submissions by CV, never by public LB.**
- **Do not spend GPU time on a larger encoder.** Measured null by two teams.
- **The Kaggle forum cannot be read by tools.** Ask Vetri to paste the thread.

## How to work here

- Mark claims [Certain] / [Likely] / [Guessing]. A number with no source is a bug.
- **Verify by executing, not by reading.** Every real bug in this repo was found by
  running code, several of them in its own code.
- Concise answers. Vetri has repeatedly asked for shorter output - lead with the
  answer, keep it to what matters.
- When you learn something durable, update the wiki page, append to `wiki/log.md`,
  and run `python3 wiki/build_index.py`.

## Commands

```bash
./run_tests.sh                                   # 52 tests, ~2 s, no data needed
python3 scripts/audit_labels.py data             # gold coverage, lexicon scorecard
python3 scripts/make_weak_labels.py data         # regenerate artifacts/weak_labels.csv
python3 scripts/budget_model.py --from-log FILE  # 9-hour budget from a Kaggle log
python3 wiki/build_index.py                      # regenerate the wiki index
kaggle competitions leaderboard -c rsna-knee-abnormality-detection --download
```

## Layout

```
wiki/        the maintained knowledge base - start here
src/         geometry, sequence typing, sampling, normalisation, lexicon patch
scripts/     audits, label generation, budget model
tests/       52 tests
notebooks/   Kaggle notebooks we wrote
docs/        long-form archive
*.ipynb      public Kaggle notebooks we run (0.939 baseline, 0.943 current best)
```
