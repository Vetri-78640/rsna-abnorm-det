---
type: howto
updated: 2026-09-22
status: current
sources: [attempts 2026-09-10]
---

# How to read the competition forum

**The Kaggle forum cannot be read by any tool here - ask for a paste.** Do not spend
turns retrying.

- `kaggle` CLI 1.7.4.5 has no discussions command.
- The internal forums API returns `403 Permission 'forums.get' was denied` to an
  API token.
- The pages render client-side; WebFetch sees only the title.

**Do this instead:** ask Vetri to paste or screenshot the thread. Transcribe it into
`wiki/raw/forum.md` and update the relevant wiki pages, then add a line to
[[log]].

Unread threads worth having: "Best single-model score", "Metric edge cases",
"9h runtime question", "How is Effusion graded?", dreaddevelopment discussion 737696.
