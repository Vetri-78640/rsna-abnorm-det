---
type: howto
updated: 2026-09-22
status: current
sources: [scripts/gh_setup.sh]
---

# GitHub workflow

Work is tracked as one issue per task, grouped into four dated milestones, with one
branch and one PR per issue that closes it.

Repo: `Vetri-78640/rsna-abnorm-det`. Visibility is an open decision, see
[[D005-repo-visibility]].

## Milestones

| milestone | due | done when |
|---|---|---|
| M1 control model | 2026-09-29 | a 5-fold control CV number and a measured noise floor exist |
| M2 sampling ablation | 2026-10-06 | our sampling is proven or disproven against the public one |
| M3 labels and blend | 2026-10-13 | our model is blended into the 0.943 notebook |
| M4 final submissions | 2026-10-22 | two finals chosen by CV, under 9 h |

2026-10-15 is the entry and team-merger deadline. We are already entered.

## Per task

```bash
git switch -c <issue-number>-<short-name>
# work, run ./run_tests.sh, update the wiki page and wiki/log.md
git push -u origin HEAD
gh pr create --fill --body "Closes #<n>"
```

Every PR that produces a number updates the matching `wiki/experiments/` page.

## Never

- Push `data/`, `logs/`, or `artifacts/weak_labels.csv`. Check with
  `git check-ignore -v <file>` - `.gitignore` has no inline comments.
- Put strategy in issue bodies on a public repo.

Setup, run once: `bash scripts/gh_setup.sh`.
