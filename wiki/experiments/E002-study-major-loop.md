---
type: experiment
updated: 2026-09-22
status: done
sources: [docs/FINDINGS.md 13, harness]
---

# E002 - Study-major inference loop

**Hypothesis:** the 0.939 notebook decodes each study 4x; reordering removes the
waste with no accuracy change.

**Result:** verified bit-identical on synthetic studies with the real arm table,
`max abs diff 0.0`. **75% of header reads and 61% of pixel decodes removed.**
Estimated 40 min saved on headers alone.

**Verdict:** done in `bend-the-knee-to-the-dinosaurs-all-public.ipynb`. The same
idea ("cached source decoding") was independently added upstream in
[[notebook-0943]], which supersedes this.
