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

Every PR updates its docs in the same change - the affected wiki pages, a line in
`wiki/log.md`, and the regenerated index. **CI enforces it:** on every PR it runs the
tests, `wiki/lint.py`, and `scripts/check_docs_updated.sh`, which fails if `src/`,
`scripts/`, `tests/`, `notebooks/` or any notebook changed without `wiki/log.md`.

Run the same checks locally before pushing:

```bash
./run_tests.sh && python3 wiki/lint.py && scripts/check_docs_updated.sh main
```

**No attribution.** Commit messages and PR bodies carry no `Co-Authored-By`,
`Claude-Session:` or other Claude credit.

## Never

- Push `data/`, `logs/`, or `artifacts/weak_labels.csv`. Check with
  `git check-ignore -v <file>` - `.gitignore` has no inline comments.
- Put strategy in issue bodies on a public repo.

Setup, run once: `bash scripts/gh_setup.sh`.
