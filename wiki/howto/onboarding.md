---
type: howto
updated: 2026-10-02
status: current
sources: [.gitignore, scripts/fetch_metadata.sh, scripts/make_weak_labels.py]
---

# Onboarding a second person

A fresh clone has all the code and none of the labels, by design. Accept the
competition rules on your own Kaggle account, pull the five CSVs, rebuild
`artifacts/weak_labels.csv` locally, and you are at parity in about ten minutes
without anyone sending you data.

**Nobody may send you the data.** `data/`, `logs/` and `artifacts/weak_labels.csv`
are gitignored because redistributing competition data to a person who has not
accepted the rules is a rules violation, and `weak_labels.csv` carries the 58 gold
labels. Everything below rebuilds from your own download. See [[dataset]].

## 1. Access

- Accept the GitHub invite to `Vetri-78640/rsna-abnorm-det` (check
  `github.com/settings/organizations` or your email; invites expire after 7 days
  and have to be reissued).
- Accept the competition rules at
  `kaggle.com/competitions/rsna-knee-abnormality-detection/rules`. The Kaggle API
  returns 403 on every file until you do.
- `pip install kaggle`, then put your API token at `~/.kaggle/kaggle.json` from
  Kaggle > Settings > API > Create New Token, and `chmod 600` it.

## 2. Clone and prove it works

```bash
git clone https://github.com/Vetri-78640/rsna-abnorm-det.git
cd rsna-abnorm-det
./run_tests.sh          # 60 tests, ~2 s, needs no data, no GPU, no network
```

If that passes you have a working checkout. Nothing below is required to read the
wiki or review a PR.

## 3. Metadata, 8.7 MB

```bash
./scripts/fetch_metadata.sh data
python3 scripts/audit_labels.py data
```

Five CSVs, not the 570 GB. Every label question - gold count, prevalence, language
mix, lexicon scorecard - is answerable from these alone.

## 4. Rebuild the labels

```bash
python3 scripts/make_weak_labels.py data
```

Writes `artifacts/weak_labels.csv` (1.5 MB) and `artifacts/platt.json`. Expect
`platt a=0.925 b=-1.397`; a different pair means your `train.csv` differs from
ours. Needs numpy and pandas only - scipy is deliberately not a dependency, see
[[log]] 2026-09-23.

## 5. Pixels, only if you are training

You do not need these to work on labels, the wiki, the budget model or any test.

```bash
kaggle competitions download -c rsna-knee-abnormality-detection   # 570 GB
```

In practice nobody downloads that. Work on Kaggle instead, where the data is
already mounted at `/kaggle/input` - see [[run-a-kaggle-notebook]].

## What to pick up first

| you have | take |
|---|---|
| Kaggle GPU quota | the `blocker` issue, then anything in M1 |
| a CPU and an hour | `#14` header census, CPU-only |
| neither | review an open PR, or an `experiment` issue that only needs the CSVs |

One branch and one PR per issue, `Closes #N` in the body. See
[[github-workflow]].

## Traps

- **Do not `git add -f` anything under `data/`.** An inline `#` comment in
  `.gitignore` silently matches nothing; that bug once staged the gold labels. If
  you edit `.gitignore`, verify with `git check-ignore -v <path>`.
- **CI fails any PR that changes code without touching `wiki/log.md`.** That is
  deliberate, not a flake. See [[github-workflow]].
- **Kaggle quota is per account, 30 h/week of T4 x2.** Two accounts is two quotas,
  but only if the team is merged before the 2026-10-15 merger deadline.
