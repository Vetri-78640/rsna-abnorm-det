---
type: howto
updated: 2026-09-22
status: current
sources: [session experience]
---

# How to run a notebook on Kaggle

Commit with GPU T4 x2 and internet off, attach datasets by content, resume from the
notebook's own output, and grep the log before trusting a run.

1. **Settings:** GPU T4 x2, internet **off**. Run with **Save & Run All (Commit)** so
   output survives.
2. **Attach datasets** listed on the notebook's page. Discovery in our notebooks
   finds files by content, so dataset names do not matter.
3. **Resume** by attaching the notebook's own previous output as an input.
4. **Grep the log** before selecting a run as final: look for fallbacks, gate
   failures, and member counts.

## Traps already hit

- `np.savez_compressed` appends `.npz` unless the name already ends in it.
- A recursive `glob("**")` over `/kaggle/input` walks 819,640 DICOMs. Prune
  `train_series` and `test_series`.
- A missing dataset can degrade silently. Print which backbone and how many members
  loaded, every run.
- A narrow timing probe underestimates the full loop. Treat it as go/no-go.
- **`.gitignore` has no inline comments.** `file.csv  # note` is one literal pattern
  and matches nothing. This nearly committed the 58 gold labels. Verify with
  `git check-ignore -v <file>` before any push.
