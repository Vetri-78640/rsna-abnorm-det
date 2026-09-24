# Log

Append-only. Newest at the bottom. One entry per session or event, prefixed so it
is greppable: `grep "^## \[" wiki/log.md | tail -5`.

Types: `build` (code), `measure` (a number we produced), `ingest` (a source read),
`decide`, `correct` (a claim found wrong), `submit`.

## [2026-09-08] build | src/ modules and 49 tests
Geometry, sequence typing, sampling, normalisation, lexicon patch. Research agents
reported; archive in wiki/raw/research.md.

## [2026-09-08] measure | label audit
58/4,407 gold, all-or-nothing. Gold is trauma-enriched. Reports 39.3% English.
Fat_Suppression == Fluid_Sensitive in every series. Lexicon over-calls on all 12.

## [2026-09-08] correct | lexicon patch was net negative
-0.0008 on gold. GLOBAL_OA matched bare Greek "osteoarthritis". Fixed to +0.0008.

## [2026-09-08] build | study-major inference loop
Bit-identical, 75% of header reads and 61% of decodes removed.

## [2026-09-08] correct | slice ordering cannot swap medial/lateral
Pooling heads are permutation-invariant, 4.8e-08 on shuffle. FINDINGS item 4 overstated.

## [2026-09-09] measure | submission commit log
5h33m floor for 1,322 studies. Family B is 11.0 of 20.5 marginal s/study.
Notebook logs native bf16=False then runs bf16. Missing dataset silently cost 0.002.

## [2026-09-09] correct | recalibrating targets cannot help AUC
Simulation with the effect planted in its favour: -0.048. See D004.

## [2026-09-09] measure | timing probe on T4
fp16 0.99 s, bf16 4.66 s (4.72x), fp32 3.11 s per study. build_study 1.89 s.

## [2026-09-09] build | encode-and-gate notebook
Crashed at 250 studies on a savez filename bug; fixed. Corpus and LLM-label
auto-discovery added.

## [2026-09-10] ingest | forum threads
Host: commercial LLM APIs permitted; report-image disagreement is by design.
Community: LLM 0.8780 vs regex 0.8136 on gold; encoder S->B null; crop geometry
+0.0059 on 10/12 labels; 11.12 GiB pixel cache, 76 min/fold.

## [2026-09-10] correct | retraining is affordable
Earlier "infeasible" was CoAtNet-at-384 arithmetic. At 224 px, 6.5 h per 5-fold run.

## [2026-09-10] decide | D001-D004
Train and blend; select finals by CV; no bigger encoder; no target calibration.

## [2026-09-10] submit | 0.941
Public model.

## [2026-09-22] ingest | notebook 0.943, Bend the Knee to Speedy Raptors
Two new CoAtNet readers (depth zones, 96-slice), cached decoding, fail-closed
gates. Keeps bf16 deliberately.

## [2026-09-22] correct | AMP_PREF='auto' is not score-neutral
fp16 and bf16 differ numerically. Speed win, unmeasured score effect.

## [2026-09-22] measure | leaderboard moved
4,143 teams, top 0.958, 0.950 is now rank 47. We are 812 @ 0.941, down from 193.

## [2026-09-22] build | this wiki
Karpathy LLM-wiki pattern. 26 atomic pages, generated index, root CLAUDE.md.

## [2026-09-22] decide | D005 repo visibility - OPEN
Repo created public. Recommend private until 2026-10-22.

## [2026-09-22] correct | gitignore inline comment nearly leaked gold labels
`artifacts/weak_labels.csv  # comment` matched nothing. Caught by checking staged
files before commit. Comments moved to their own lines; `git check-ignore` verified.

## [2026-09-22] build | scripts/make_weak_labels.py
weak_labels.csv is now rebuildable, so it never needs to be in git. scipy dropped:
its native library fails to load after the macOS 27 upgrade; Platt is now fitted
by numpy Newton, matching the old file to 5e-06.

## [2026-09-22] decide | D005 repo stays public
Vetri chose public over the private recommendation. Data remains gitignored.

## [2026-09-22] build | docs/ folded into the wiki
community.md and researched.md are external material, so they became
wiki/raw/forum.md and wiki/raw/research.md. FINDINGS, STRATEGY, PLAN and extras are
our own dated reasoning, so they became wiki/archive/ with a frozen banner. HANDOFF
is replaced by CLAUDE.md, which every session loads automatically. 20 files had
their paths rewritten, including a stale reference to a docs/RESEARCH.md that never
existed.

## [2026-09-22] build | glossary, open questions, wiki lint, CI
glossary.md defines arm, slot, key, gold, commit run and the rest. open-questions.md
lists nine unknowns with what settles each. wiki/lint.py checks links, frontmatter
and index freshness. CI runs tests, lint, and a check that code changes carry a log
entry.

## [2026-09-22] decide | no attribution; docs updated every iteration
Vetri: never co-author Claude in commits or PRs. Every change updates its docs in the
same commit, now enforced by CI.

## [2026-09-22] build | stripped attribution trailers from history
The first four commits carried a Claude-Session trailer. Rewrote main with a
message-only filter and force-pushed with lease. Trees verified byte-identical before
and after. Local backup tag: backup-before-trailer-strip.

## [2026-09-22] measure | full CSV audit
Every gold study has >=1 positive (mean 4.14). UIDs regenerated under pydicom's
root, no train/test overlap. Axial non-FS missing in 80.6% of studies; only 12.8%
have all six slots; 13.6% of slots offer several series. Reports effectively
non-contrast (~4 of 4,407 used gadolinium); strong per-site templates.

## [2026-09-22] measure | DICOM headers, one test study
62 tags survive, including Laterality, EchoTime, ScanOptions, SeriesDescription,
PatientID. Confirmed: a T2 TSE (TE 91, no fat-sat) is labelled fluid=0 by the
organisers - the flag tracks fat suppression, not fluid sensitivity.

## [2026-09-22] build | header census notebook, file inventory crawler
notebooks/header_census.ipynb reads one header per series for all 24,371 series,
CPU only; dry-run on the real sample. scripts/crawl_file_inventory.py lists all
819,640 files for slices per series; running.

## [2026-09-24] measure | slices per series, from 41% of the file listing
Median 30, p5 18, p95 45, p99 160, max 320; 2.8% of series exceed 100 slices.
Extrapolated total 0.56 TB against the stated 570 GB, so the sample is sound.
The public fixed slice budgets give a median stride of 3.60 on coronal non-FS
(84.7% over 2.5) and a p95 stride of 11.5 on axial. 80% of studies have at least
one slot sampled at stride over 2.5. Sagittal, the slot that matters most for the
meniscal body, is the one that is already fine.

## [2026-09-24] correct | crawler retry was too impatient
It gave up after 6 attempts over 105 s at page 1,677 and reported an empty stderr.
The API rate-limits after a few thousand rapid pages and recovers. Now 12 attempts
with backoff to 5 minutes, the failing stdout and stderr printed, a 20 s pause every
500 pages, and exit code 2 with resume instructions. Resumed from the saved token.

## [2026-09-24] correct | crawler page counter reset on resume
The counter was per run, so the saved state under-reported progress after a resume.
Now cumulative, and it prints the page it resumes from.

## [2026-09-24] build | training pipeline: cache builder, folds, control model
src/folds.py clusters near-duplicate reports and stratifies folds over clusters;
8 tests. Measured: 4,407 reports -> 4,101 clusters, against 4,276 MD5 groups in the
public notebook, so it splits 175 near-duplicates across folds.
notebooks/cache_and_train_control.ipynb builds a 224 px cache under either sampling
rule and trains a 5-fold control. Dry-run on both paths. Two silent bugs caught:
order_slices/laterality_flips return tuples (a bare except would have skipped
laterality entirely), and only fold 0 had its encoder frozen.

## [2026-09-24] measure | complete file inventory, all 819,640 files
The crawl finished. 24,386 series, 819,635 slices plus 5 CSVs = the stated 819,640
files, and 570 GB against the stated 569.76 GB - so the numbers are the dataset, not
a sample. The 41% sample had predicted every figure to within 1%: median 30 slices,
p99 160, max 320; coronal non-FS stride 83.6% over 2.5 (sample said 84.7%); 79.6% of
studies have a slot over stride 2.5 (sample said 80.0%).
