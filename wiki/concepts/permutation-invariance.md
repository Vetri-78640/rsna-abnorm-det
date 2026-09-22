---
type: concept
updated: 2026-09-22
status: current
sources: [executed 2026-09-08]
---

# The pooling heads ignore slice order

The public pooling heads ignore slice order, so the slice-ordering bug cannot swap
medial for lateral the way older docs claimed.

[Certain, executed] The Raptor head is `softmax` over the window axis followed by a
sum. Shuffling all 62 windows changes the output by **4.8e-08**.

Family A's pooling (`segment_softmax`, `index_add_`, `scatter_reduce amax`) has the
same shape and no positional encoding. [Likely] also order-invariant, except the
`SlotDepthMixer` path.

## Consequences

- The vendor-dependent slice-normal sign bug cannot swap medial for lateral in these
  models - they never had a positional signal to swap. They tell the compartments
  apart by what each slice looks like.
- What reversal *does* do: the same span, but picked slices shift by half a stride
  (mean Jaccard 0.071). A sampling jitter, not an anatomical swap.
- Arm 2's `reverse` TTA flips the adjacent-slice **triplet channels**, not the slice
  order.
- `src/geometry.py` is still worth having for a model we train ourselves, but its
  value is much smaller than first claimed.

**Real gap this revealed:** Family B does no laterality normalisation at all. Left
and right knees enter as mirror images.

Related: [[slice-selection]], [[model-families]]
