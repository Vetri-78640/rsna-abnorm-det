---
type: decision
updated: 2026-09-22
status: current
sources: [gh repo view]
---

# D005 - GitHub repo visibility: public

`Vetri-78640/rsna-abnorm-det` was created **PUBLIC** on 2026-09-22.

**Recommendation: make it private until 2026-10-22, then public.**

**Why:**
1. **Competition data must never be pushed publicly.** `data/*.csv` holds the
   reports; `artifacts/weak_labels.csv` holds the 58 gold labels. Redistributing
   them is a rules violation. These are `.gitignore`d regardless.
2. **A public repo hands the thesis to 4,000+ competitors.** `src/sampling.py` is
   the one thing we have that others do not.
3. **The rules' public-sharing carve-out points at the Kaggle forum.** A public
   GitHub repo is commonly accepted but is a grey area mid-competition.
4. **It costs nothing to wait.** Winners must open-source everything under
   CC-BY-NC afterwards anyway.

**Decided 2026-09-22 by Vetri: keep public.** The recommendation above was
considered and declined. Consequences to keep in mind:

- Everything pushed, including issue text, is visible to every competitor.
- Competition data stays gitignored; verify with `git check-ignore -v` before any
  push.
