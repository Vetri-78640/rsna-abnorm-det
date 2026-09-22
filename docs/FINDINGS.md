# Verified defects in the public 0.939 notebook

Every item here was reproduced by executing the notebook's own code, not inferred
by reading it. Line references are to `bend-the-knee-to-the-dinosaurs-all-public.ipynb`
flattened cell-by-cell.

Confidence markers: [Certain] reproduced or read directly from source.
[Likely] strong inference. [Guessing] speculation.

---

## 1. Report lexicon: cartilage grade discarded for the OA targets

[Certain] `_grade_of()` is called at two places inside `_score_paired()` but never
inside `_score_oa()`. With wording held constant:

```
0.85  Outerbridge grade 1 chondromalacia of the medial compartment.
0.85  Outerbridge grade 2 chondromalacia of the medial compartment.
0.85  Outerbridge grade 3 chondromalacia of the medial compartment.
0.85  Outerbridge grade 4 chondromalacia of the medial compartment.
```

Grade 1 is cartilage softening with an intact surface, below the clinical
threshold for cartilage loss. Grade 4 is full-thickness loss with exposed bone.
They score identically.

The machinery exists and works - the meniscus path uses the grade correctly,
jumping at exactly the grade-2 to grade-3 boundary where the radiology defines a
tear:

```
0.65  Grade 1 signal in the medial meniscus.
0.65  Grade 2 signal in the medial meniscus.
0.94  Grade 3 signal in the medial meniscus.
```

so the omission looks accidental rather than deliberate.

**After the patch:** 0.65 / 0.79 / 0.90 / 0.96.

**Deliberately not fixed:** a bare "grade 2" with no named scale. Outerbridge
grade 2 means under 50% cartilage loss, below the OA threshold; Kellgren-Lawrence
grade 2 means definite OA. The regex cannot tell them apart, so an unnamed scale
stays on the old severity path.

---

## 2. Report lexicon: global OA evidence dropped when a compartment is named

[Certain] In `_score_oa()`, `g_pos` incremented only inside the `if not hits:`
branch, so a `GLOBAL_OA` match was discarded the moment any compartment matched.

```
Tricompartmental osteoarthritis.
    Medial OA 0.83   Lateral OA 0.83   PF OA 0.83
Tricompartmental osteoarthritis, most severe in the patellofemoral joint.
    Medial OA 0.28   Lateral OA 0.28   PF OA 0.96
```

Adding clinically informative detail flips two targets from 0.83 to 0.28.

Medial OA, Lateral OA and PF OA are three of twelve macro-AUC components, so this
touches 25% of the metric.

**After the patch:** 0.93 / 0.93 / 0.96.

The fix accumulates `g_pos` whenever `GLOBAL_OA` matches, independent of `hits`.
It is deliberately *not* unconditional - making every unattributed OA clause set
`g_pos` would let "medial compartment OA" imply lateral OA.

---

## 3. Report lexicon: post-posed negation missed

[Certain] `_negated()` is bidirectional in mechanism, but `POST_NEG` holds only
Turkish and Croatian markers. `without`, `sin`, `ohne`, `sans` all live in
`PRE_NEG`, which is searched backwards from the match span, so negation trailing
the anatomy is invisible.

```
0.96  Degenerative changes of the medial meniscus without tear.
0.83  Mucoid degeneration of the ACL without discrete tear.
0.85  Medial compartment osteoarthritis with sparing of the lateral compartment.
0.28  A meniscal tear is not excluded.
```

**After the patch:** 0.16 / 0.16 / 0.28 for the first three. "not excluded" is
left alone pending a decision on whether hedges should map to uncertain.

The fix fires only when a pathology token follows the negation marker within 40
characters. This scoping is essential - a naive forward search for `without`
would wrongly negate "complete tear of the medial meniscus without displacement",
which the regression suite asserts stays at 0.96.

Sparing is handled separately and forward-only. A symmetric window suppressed
*both* compartments in a short clause, since the diseased side is named before
the sparing term and the spared side after it.

---

## 4. Slice normal is not sign-canonicalised

[Certain] `order_slices` sorts by `dot(IPP, cross(IOP[:3], IOP[3:]))`. The cross
product's sign follows the vendor's choice of row and column direction. Two
equally valid sagittal conventions:

```
IOP [0,1,0, 0,0,-1]  ->  normal (-1, 0, 0)
IOP [0,-1,0, 0,0,-1] ->  normal (+1, 0, 0)
```

Ascending sort therefore runs medial to lateral on one and lateral to medial on
the other. `normalise_laterality` then flips sagittal along the slice axis for
right knees, compounding rather than correcting it.

This silently swaps Medial and Lateral Meniscus, and Medial and Lateral OA - four
of twelve targets.

`src/geometry.py` forces a positive projection onto the plane's canonical LPS
axis before sorting. `tests/test_geometry.py::test_vendor_sign_invariance`
asserts both conventions now produce identical anatomical order.

[Likely] worth noting: the *legacy* path `_order_dominant_axis` sorts by the
dominant world-axis coordinate directly, which is already sign-canonical. So the
legacy ordering is correct here and the native one is not - the opposite of what
you would assume.

---

## 5. Laterality fallback is weak, and one variant is geometrically wrong

[Certain] `side_from_corner_x` takes the median of `ImagePositionPatient[0]`
across a study. For coronal and axial series every slice shares the same corner
x, roughly `-FOV/2`, so the median is a near-constant negative number carrying no
laterality information. This path is used by the legacy rules in cell 25.

[Certain] The default path `side_from_geometry` correctly reconstructs the image
centre from the corner plus half the physical extent along both direction
cosines, so it is geometrically sound.

[Likely] The residual concern is still real but smaller: knees are positioned at
isocentre, so centre-x hovers near zero and its sign is weak evidence. The code
guards this with `LAT_MIN_OFFSET_MM = 20.0` and returns `None` below that, which
means no flip rather than a wrong flip - a safe failure mode.

`lat_of` already logs the tag-versus-geometry disagreement rate. Running it once
on training headers is the cheapest possible diagnostic. `scripts/audit_headers.py`
reports the same statistic.

---

## 6. Slice band discards the anatomy several targets live in

[Certain] Family A samples 0.2-0.8, Family B 0.12-0.88, Family C 0.02-0.98. At 30
slices the 0.2-0.8 band drops six slices at each end.

| plane | discarded start | discarded end |
|---|---|---|
| coronal | patella, trochlea (PF OA) | popliteal fossa (Baker's) |
| axial | tibial end | suprapatellar pouch (Effusion) |
| sagittal | far medial: MCL, meniscal body | far lateral: meniscal body, Segond |

Family C is already near-full-range, so this criticism lands on A and B.

---

## 7. Slice stride can miss the meniscal body entirely

[Certain] The intact meniscal body spans only 2-3 consecutive sagittal slices -
that is the entire basis of the absent bow-tie sign. Family A takes 8 slices from
the 0.2-0.8 band of a ~30-slice series, a stride of about 2.6, so it can see one
or zero body slices even in a normal knee, making that feature unlearnable.
Family B's raptor arm is better at 18 sagittal slices over 0.02-0.98, stride
about 1.6.

---

## 8. Per-slice intensity windowing, in one place

[Certain] Cell 21 sets `INTENSITY = 'slice'` and stretches each slice to its own
1st-99th percentile. Family A's `read_slot` and the raptor arm both already
normalise per series, so this affects one path only.

Effusion, Synovitis, Contusion and Fracture are amplitude findings. A per-slice
stretch maps the brightest fluid on every slice to 1.0, so a trace effusion and a
tense effusion become indistinguishable except by area.

The file already contains an untaken `INTENSITY == 'series'` branch, so flipping
one constant is a free experiment.

---

## 9. Sequence typing tests GRE last

[Certain] `annotate()` applies the TR/TE rules before checking `ScanningSequence`
for `GR`, so a 2D T2*/MEDIC at TR 800-1200 passes `TR >= 800` and is typed PD.

[Certain] Inversion recovery is never a class, so STIR at TE 110 types as T2 and
STIR at TE 40 types as PD - one clinical sequence split across two buckets by an
arbitrary vendor TE choice.

[Likely] `TR < 800` for T1 is too tight. T1 TR is driven by slice count in 2D
multi-slice, and tissue T1 lengthens with field strength, so 3T T1 routinely runs
TR 700-1100.

[Certain] Intermediate-weighted (TE 30-40 ms), the workhorse of modern knee
protocols, is collapsed into PD despite being physically closer to T2.

---

## 10. The ensemble is more redundant than it appears

[Certain] Family B arm 0 and arm 2 load the *same checkpoint file*,
`raptor_ft_coatnet_v5_full_swa.pt`, differing only by `reverse: True`. That is
test-time augmentation counted as an ensemble member at weight 0.15.

[Certain] Family C is the same backbone at the same resolution on the same
adjacent-slice triplets as Family B, differing only in the head.

[Likely] All three families consume nearly the same representation, so their
errors are correlated. At that correlation the 24-member Family A is worth
perhaps 2 to 4 effective members, and adding more of the same kind will move
macro-AUC by under 0.001.

---

## 11. The "calibrator" is a stacker

[Certain] AUC is invariant to any monotone transform, so per-label recalibration
cannot change it. The logistic model in cell 25 does real work only because it
*mixes branches*. Worth knowing before trying to tune it as a calibrator.

---

## 12. Cross-validation grouping by report hash

[Certain] Folds are formed by MD5 of the report text. Near-duplicate reports
differing by one character land in different folds, and repeat patients are not
grouped at all.

[Likely] Documented leakage inflation in comparable medical imaging settings runs
30-55%. Correct grouping is near-duplicate clustering plus patient identifier,
stratified by site and multi-label.

---

## 13. Every study's pixels are decoded four times

[Certain] Cell 26's `main()` nests the loops arms-outermost:

```python
for arm in ARMS:                 # 4 arms
    for study in test_ids:       # ~1300 studies
        volume, mask = build_study(...)   # decodes DICOMs
        infer(...)
```

so `build_study` runs four times per study. `order_and_meta` inside it also
re-reads every header in every series, four times.

[Certain] The four arms do not need four distinct volumes:

| arm | img | slots | span | weight |
|---|---|---|---|---|
| 0 maxspan-v5 | 336 | SLOTS64 | 0.02-0.98 | 0.55 |
| 1 native384dense-v10 | 384 | SLOTS64 | 0.02-0.98 | 0.10 |
| 2 maxspan-v5-reverse | 336 | SLOTS64 | 0.02-0.98 | 0.15 |
| 3 native384-v8 | 384 | SLOTS44 | 0.06-0.94 | 0.20 |

Arm 2 loads the same checkpoint file as arm 0 and builds a byte-identical volume.
[Certain] verified with `symtable`: `build_study` reads exactly `IMG`, `SLOTS`,
`MAXS`, `SPAN_LO`, `SPAN_HI`, and all five match between arms 0 and 2.

**Two corrections to what this note originally claimed.**

[Certain] `reverse` is not slice-order reversal. `windows.flip(1)` acts on a
`(K, 3, res, res)` tensor, so dim 1 is the three-channel adjacent-slice triplet.
It turns `[c-1, c, c+1]` into `[c+1, c, c-1]`. That is channel-order TTA inside
each window, not reversal of the volume.

[Certain] "one decode at 384 serves all four" is false. Arms 0 and 2 build at
`IMG=336` with `cv2.INTER_AREA`, and `eval_windows` then bilinearly upsamples to
384. Serving them from a 384 decode inserts an extra resample and changes their
model inputs, so it is not free.

**What is actually free, and now done.** `_KE_SRC` runs studies-outermost
(`STUDY_MAJOR = True`), with the arm-major loop kept as an automatic fallback on
exception - most plausibly CUDA OOM, since three checkpoints are now resident
instead of one. The reader memoises headers and pixels per study. Measured by
running both orders over synthetic studies with the real arm table:

```
                 arm-major   study-major   removed
header reads      593/study    148/study      75%
pixel decodes     217/study     85/study      61%
arm_probs         bit-identical (max abs diff 0.0)
```

Three sources of saving: `order_and_meta` collapses 4x to 1x because both slot
schemes select the same series (`SLOTS64` and `SLOTS44` have identical
`(plane, fluid)` keys); arm 2's `build_study` and `eval_windows` disappear
entirely; and arms 0, 1 and 2 pick the same file indices, so one `read_px` per
file serves all three and only the post-decode resize differs.

GPU work is unchanged at 62+62+62+42 windows per study. The saving is pure I/O
and its share of the 9 hours is still unknown - `budget_model.py --from-log` now
parses the study-major line, which reports the build/windows/infer split
directly, the one number the arm-major log could never give.

This matters because the submission must finish inside 9 hours and the notebook
already sets `TIME_BUDGET = 8.0 * 3600` in two places, leaving about an hour of
margin. `scripts/budget_model.py` models the saving, and `--from-log` calibrates
it against a real run using the notebook's own progress output.


---

## 14. Fat suppression and fluid sensitivity are one column, not two

[Certain] In `train_series.csv`, `Fat_Suppression == Fluid_Sensitive` for all
24,371 series. In `test_series.csv`, for all 15. The off-diagonal count is zero.

```
plane x fs x fluid, all six cells that exist:
  Axial      fs=0 fluid=0   1179    Axial      fs=1 fluid=1   4719
  Coronal    fs=0 fluid=0   3985    Coronal    fs=1 fluid=1   4624
  Sagittal   fs=0 fluid=0   5197    Sagittal   fs=1 fluid=1   4667
```

So the notebook's six-slot key, which item 6 and `src/sampling.py` criticise for
collapsing two axes into one, loses nothing at all against this metadata. The
2x2 grid could never fill more than half its cells, and `routing_matrix()` would
have handed a training run six permanently-zero columns.

`slot_grid()` now defaults to the six observed slots; `full=True` keeps the 2x2.

[Certain] the physics is unchanged - a coronal T2 FSE without fat suppression is
fluid-sensitive, and 8,361 series are marked `fs=0 fluid=0`. [Likely] the
organisers derived one flag from the other, or defined "fluid sensitive" to mean
"fat-suppressed fluid-sensitive"; a knee protocol with zero non-fat-sat
fluid-sensitive series across 4,407 studies is not clinically plausible.

That is the opening. Recovering true fluid sensitivity from TE would surface a
slot every public solution is currently filing as "structural". It needs DICOM
headers, and `src/sequence_typing.py` already implements the typing.

---

## 15. The gold set is trauma-enriched, so its prevalence is not the test's

[Certain] 58 of 4,407 studies carry labels, all twelve or none. Confirmed from
`train.csv`, not from a secondary source.

[Certain] it is not a random sample. Lexicon fire rate, gold versus the rest:

| label | gold | rest | ratio | p |
|---|---|---|---|---|
| Fracture | 0.379 | 0.073 | 5.2x | 4e-11 |
| Contusion | 0.586 | 0.252 | 2.3x | 7e-08 |
| ACL | 0.569 | 0.261 | 2.2x | 7e-07 |
| Medial OA | 0.431 | 0.391 | 1.1x | 0.31 |
| Baker's | 0.293 | 0.279 | 1.1x | 0.45 |

The traumatic labels are enriched, the degenerative ones are not. Mean
lexicon-positive labels per study: 6.07 in gold, 4.01 outside. Median report
length 1,206 versus 974 characters. Language mix is unchanged, so it is not a
site or language selection.

Consequences: `audit_labels.py`'s `exp@1300` column is fiction and is now
labelled as such. `extras.md`'s "Fracture at ~3%, ~39 positives" came from
external epidemiology and is wrong for this dataset - the lexicon fires on 7.3%
of non-gold studies, and [Guessing] true prevalence is 5 to 8% after correcting
for over-firing.

The upside: a stratified 58 is a better ranking set for the rare labels than a
random 58, which would have carried about four Fracture positives instead of 18.

---

## 16. The lexicon over-calls on every label, and AUC cannot see it

[Certain] Against the gold 58 at the 0.5 threshold the lexicon agrees on 77.0% of
cells, with 136 false positives against 24 false negatives. Specificity runs
0.30 (Effusion) to 0.87 (Baker's); sensitivity runs 0.78 to 1.00.

[Certain] Sweeping the threshold, the agreement-maximising cut is above 0.5 for
all twelve labels, ranging 0.66 to 0.96 with a median of 0.86. Mean agreement
0.770 to 0.841.

The magnitude is overfitted at n=58. The direction is not: twelve of twelve in
the same direction is a sign test at p=0.0002.

This is not a regex bug, it is one global miscalibration, and it is invisible to
every AUC number in this repo because AUC is invariant to monotone transforms.
It matters to anything that consumes the scores as values rather than ranks -
a BCE run against them as soft targets, or the relabelling loop in week 3, which
blends model predictions with lexicon scores on a shared scale.

[Guessing] the effect on a trained model's AUC is small, because per-label target
inflation mostly moves the bias term. The place it plausibly costs something is
the shared backbone, where twelve inflated targets reweight the gradient.

---

## 17. The lexicon patch's own regression, found by running it

[Certain] Measured against gold, `lexicon_patch` as originally written scored
macro -0.0008: Lateral Meniscus +0.0211, but Medial OA -0.0093, Lateral OA
-0.0097, PF OA -0.0116. All three OA labels, which are exactly what items 1 and 2
target.

Cause, reproduced clause by clause: `lexicon_base.GLOBAL_OA` is not a globality
detector. Every English alternative carries a qualifier - `tricompartment`,
`gonarthros`, `osteoarthritis of the knee`, `degenerative joint disease`. Four do
not: the two bare Greek words for osteoarthritis, and bare `compartments` /
`compartmens`. On a real gold report:

```
"ευρηματα αρχομενης εκφυλιστικης οστεοαρθριτιδας κατα το εσω διαμερισμα"
  = incipient degenerative osteoarthritis IN THE MEDIAL COMPARTMENT
  gold Medial/Lateral/PF = 1/0/0
  patch raised Lateral OA 0.16 -> 0.70 and PF OA 0.16 -> 0.70
```

These entries were harmless in the original `_score_oa`, which consulted
`GLOBAL_OA` only when no compartment was named. Item 2's fix is what promotes the
regex from decorative to load-bearing, and the regex is not good enough to bear
the load. That is the general lesson: a correct fix can be wrong in combination
with the code it lands in.

Blast radius: 98 of 4,407 studies (2.2%) - `compartments` 53 clauses, the two
Greek entries 135.

**After narrowing `GLOBAL_OA` so every alternative carries a globality
qualifier:** PF OA returns to baseline, Lateral OA to within 0.001 of it, macro
goes from -0.0008 to **+0.0008**. Guarded by
`test_globality_regex_requires_a_qualifier` and
`test_localised_greek_oa_does_not_propagate`.

The residual Medial OA -0.0101 is one study whose report says "tricompartmental"
while the image annotator recorded no medial OA. That is the report-versus-image
ceiling, not a bug, and no lexicon work will fix it.

Honest caveat on all of the above: at n=58 with 9 to 35 positives, every delta
here is inside one standard error. The reason to make the change is the
mechanism, not the AUC.


---

## 18. The submission runs bf16 on a GPU that has no bf16

[Certain] Not inferred - the notebook prints both halves itself, five lines
apart, in `logs/bend-the-knee-to-the-dinosaurs-all-public.log`:

```
105.0s  gpu0 : Tesla T4 sm_75, 15 GiB, native bf16=False
105.0s  gpu1 : Tesla T4 sm_75, 15 GiB, native bf16=False
111.8s  device cuda | amp bfloat16 (on=True) | workers 4 | chunk 48 | micro 8
```

Cell 23:

```python
AMP_PREF = 'bf16'
def amp_for(dev):
    cc = torch.cuda.get_device_capability(dev)
    if AMP_PREF == 'bf16': return (torch.bfloat16, True)   # cc computed, ignored
    ...
    return (torch.bfloat16 if cc >= (8, 0) else torch.float16, True)   # unreachable
```

The author's own fallback says fp16 below cc 8.0 and can never run. Turing has
fp16 tensor cores and no bf16 ones. Setting `AMP_PREF = 'auto'` reaches the
correct branch.

This affects Family A only. Family B's `infer_probs` hardcodes fp16, and
Family C never enters that path.

[Guessing] the size of the win. The log cannot price it; `notebooks/01` times
fp16 against bf16 against fp32 on the real hardware.

---

## 19. Where the 9 hours go, measured

[Certain] From the same log, which is a **commit** run: 3 studies from the public
placeholder, not the 1,322-study hidden set the notebook itself names while
sizing its cache. Fixed costs are 31% of that run, so the naive division is
useless and `budget_model.py --from-log` now detects the case and strips them.

```
fixed, counted from the log
  25 checkpoint loads             43.4s
  4 raptor arm loads              15.9s
  cuDNN autotune, new shapes      17.9s     <- arms 0 and 3 introduce new
                                               window shapes; 1 and 2 reuse
marginal, per study
  Family A  slot/DINOv3            6.8s
  Family C  Rad-dual5              2.7s
  Family B  raptor, four arms     11.0s     (2.8s per arm warm)

extrapolated to 1,322 studies    5h33m       floor
notebook's own TIME_BUDGET       8h00m
competition limit                9h00m
```

The floor is a floor: three studies sit entirely in page cache and this pipeline
is I/O bound. That the author set 8h is the best evidence for the real number.

[Certain] **Family B is 11.0 of the 20.5 marginal seconds per study** - more than
Family A and C combined, for 0.60 of the blend. It is the right place to have
spent the restructuring effort.

[Certain] a header read costs **4.1 ms** (469 headers ordered in 1.9s).
Arm-major reads ~600 headers per study in Family B; study-major reads ~150.
595,000 reads saved at 4.1 ms is **40 minutes**, plus ~151 pixel decodes per
study that this log cannot price.

---

## 20. A missing dataset silently costs 0.002

[Certain] The log ends with:

```
[coat-arm] blended OUR resgated e4/e6/e8 into the public Raptor arm (private alpha 0.400)
[public0033] bag absent; exact 0.937 parent retained
```

So this run did **not** produce the 0.939 configuration. An expected input was
not attached and the notebook fell back to a 0.937 parent, printing one line and
continuing. There is no assertion and no non-zero exit.

`extras.md` already lists "weights dataset not attached" as a failure mode, and
notes the notebook "raises a clear error". For the *primary* weight search that
is true. For this overlay it is not - it degrades quietly.

Check that line on every submission before selecting it as a final.

---

## Community results and host rulings

Not defects, so not here. What other teams measured, what the host has ruled, and
the transcribed discussion threads live in **`community.md`**. The reasoning that
turns all of it into a plan lives in **`STRATEGY.md`**.
