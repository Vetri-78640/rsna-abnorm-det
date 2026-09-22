---
type: experiment
updated: 2026-09-22
status: in-progress
sources: [notebooks/RUN_THIS_encode_and_gate.ipynb]
---

# E003 - Encode features and run the label gate

Measures whether label quality is worth anything on this data, by caching encoder
features once and training the head under several label sets. Result pending.

**Notebook:** `notebooks/RUN_THIS_encode_and_gate.ipynb`. Encodes the training set
with the Raptor v5 encoder, caches features, then trains the head under several
label sets and scores on the gold 58.

**Arms:** `ckpt` (the shipped head), `fix`, `noise10`, `noise25`, `raw`, `cal`,
and any LLM label table found attached (auto-detected).

**Status:**
- Run 1 crashed at study 250: `np.savez_compressed` appends `.npz`, so a
  `.npz.tmp` name broke `os.replace`. **Fixed.** The 250 studies survived as
  `shard_0000.npz.tmp.npz` and are picked up on resume.
- Timing probe from run 1: build 1.89 s, fp16 0.99 s, bf16 4.66 s per study.
- `pilkwang/rsna-knee-llm-labels` found with 12/12 labels.
- Pre-decoded corpus support added, with verification against our own
  `build_study` before use.
- **Result not yet received.**

**Read it with:** [[label-premise]] - the Tucker diagnostic compares `ckpt` gold
AUC with the extractor's 0.8625.
