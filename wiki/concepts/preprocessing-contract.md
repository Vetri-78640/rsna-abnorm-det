---
type: concept
updated: 2026-09-22
status: current
sources: [forum, timing probe, 0.943 source]
---

# A checkpoint carries its own preprocessing contract

**Feeding a checkpoint inputs prepared differently from its training fails
silently** - no error, a plausible curve, a wrong conclusion.

## Cases

- **Normalisation.** RAD-DINO uses greyscale mean 0.5307 / std 0.2583 at 518 px, not
  ImageNet constants at 224. Hardcoding ImageNet gave an 11-hour losing run that
  looked like "medical pretraining does not transfer". Read
  `preprocessor_config.json`.
- **Numeric precision.** fp16 and bf16 are different number formats. On T4, bf16 is
  **4.72x slower** (measured) but switching to fp16 **changes the predictions**,
  because the arithmetic differs. The 0.943 author kept bf16 deliberately: "no
  unvalidated AMP change".
- **Slice ordering, crop, normalisation mode.** Any of these changed at inference
  on someone else's checkpoint is a train/test mismatch.

## Correction

Older docs said `AMP_PREF='auto'` was "0.000 on score". **Wrong.** It is a speed win
with an unmeasured score effect - probably tiny, but it needs one validation
submission before it goes into a final.

## Rule

Every module in `src/` is **retrain-only**. None of it should be applied at
inference to a public checkpoint.

Related: [[compute]], [[notebook-0943]]
