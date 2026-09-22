# Research archive

Everything gathered for this competition, in full. Four literature-review agents
(MRI physics, MSK radiology, radiology report NLP, deep learning methods) plus my
own verification against the notebook's source and by executing its code.

Confidence markers throughout: **[Certain]** reproduced, executed, or read
directly from a primary source. **[Likely]** strong inference. **[Guessing]**
speculation.

For the short version, read "Decision summary" below and stop. For what to do
about it, see `PLAN.md`. For the defects themselves, `FINDINGS.md`.

---

## Decision summary

The ten things that actually change what we build.

1. **[Guessing, must verify] Only 58 of 4,407 training studies may carry gold
   labels**, with report-derived labels agreeing with image-derived only ~82%. If
   true, no per-label parameter can be fitted on gold, and fixing the *target*
   beats every model change. `scripts/audit_labels.py` settles it.
2. **[Certain] The test labels are image-derived**, annotated by radiologists
   reading the MRIs. So the objective is not "reproduce the report" but "predict
   what an image-reading annotator would say" - a measurably different target.
3. **[Certain] Macro-AUC leverage is equal per label but achievability is not.**
   Each label is 1/12 of the metric. Effusion at ~55% prevalence is saturated;
   Fracture at ~3% (~39 positives, AUC SE ≈ 0.033) is not. Spend effort where
   +0.01 is reachable.
4. **[Likely] Some labels have an irreducible ceiling.** Inter-reader kappa for
   Synovitis is 0.42-0.62 and this dataset is non-contrast, so synovitis is being
   inferred rather than seen. Do not chase it.
5. **[Certain] The slice normal is not sign-canonicalised**, so medial/lateral
   ordering flips by vendor, silently swapping four of twelve targets.
6. **[Certain] Fat suppression and fluid sensitivity are independent axes.** The
   fracture *line* needs non-fat-suppressed T1; the marrow oedema needs fat
   suppression. Same label, opposite requirements.
7. **[Certain] Every prior RSNA winner used localise → crop → 2.5D → sequence.**
   The current solution has only the last two stages.
8. **[Certain] DINOv2 per slice + transformer across slices beat a 3D ResNet
   0.85 to 0.69 on knee MRI meniscus tears.** Do not build a 3D CNN.
9. **[Likely] The ensemble is saturated.** Arm 2 is arm 0's checkpoint reversed;
   Family C is Family B with a different head. More correlated members buy
   under 0.001.
10. **[Certain] The submission must finish in 9 hours** and the notebook already
    budgets 8. Every study is decoded four times, three of which are redundant.

---

# Part 1 - MRI physics

## 1.1 Sequence physics and contrast formation

**[Certain]** Contrast is set by TR (T1 weighting), TE (T2 weighting), and
whether fat signal is removed. Standard boundaries in the MSK literature:

| weighting | TR | TE | what it shows |
|---|---|---|---|
| T1 TSE | 300-1000 ms | 10-25 ms | fatty marrow bright, fracture line dark |
| PD FSE | 1500-5000 ms | 10-30 ms | highest SNR, meniscus dark on bright fat |
| **Intermediate-weighted** | 1600-5000 ms | **30-40 ms** | the clinical workhorse |
| T2 FSE | 2500-5000 ms | 80-120 at 1.5T, **70-80 at 3T** | fluid only, high specificity |
| STIR | 4000-5000, TI 130-180 (1.5T) / 190-230 (3T) | 30-110 ms | uniform fat null, low SNR |
| GRE / MEDIC / DESS | 800-1200 (2D) | 5-25 ms | cartilage morphology, susceptibility blooming |

**[Certain]** Intermediate-weighted FS FSE at **TE 30-40 ms** is described as "the
cornerstone of MRI protocols for clinical practice and trials" because it
combines PD anatomy with T2 fluid sensitivity *and materially reduces magic-angle
artefact* relative to true PD.

Real reference protocols, for calibration:
- Corsmed: sag/cor/ax PD FS at TR 1600-2000 / TE 20-40, 3 mm / 0.3 mm gap,
  FOV **140 x 140 mm**, 30-34 slices; sag T1 TSE TR 300-500 / TE 10-20; cor T2
  TSE TR 2500-4000 / TE 80-120.
- MRImaster: ax PD FS TR 3000-4000 / TE 15-20; cor PD FS TR 4000-5000 / TE 15-20;
  sag T1 TSE TR 400-600; sag STIR TR 4000-5000 / TE 110; sag T2* MEDIC TR
  800-1200 / TE 15-25.

### Per-finding signal basis

| target | physical basis | best sequence | plane |
|---|---|---|---|
| ACL | loss of low-signal collagen fascicle continuity, replaced by oedema | IW/PD FS | sagittal primary |
| MCL | peri-ligamentous fascial oedema, loss of demarcation from adjacent fat | **fat-suppressed** coronal IW/T2 | coronal |
| Menisci | fibrocartilage has very short T2 (dark); a tear is a linear long-T2 cleft reaching a surface | short-TE PD **or** IW FS | sagittal + coronal |
| OA x3 | cartilage substance loss; contrast is cartilage vs fluid vs subchondral plate | **IW FS** | coronal + axial for PF |
| Effusion | bulk free water, long T1, very long T2 | T2 FS or IW FS | axial |
| Synovitis | inferred, not seen: MOAKS scores Hoffa-synovitis and effusion-synovitis | IW/T2 **FS** | sagittal + axial |
| Baker's | fluid in the gastrocnemius-semimembranosus bursa | T2 FS | **axial** |
| Contusion | trabecular microfracture, marrow oedema - fat replaced by water | **FS fluid-sensitive** or STIR | all |
| Fracture | low-signal line **plus** surrounding oedema | **T1 + STIR combined** | coronal + sagittal |

**[Certain]** T1 + STIR combined gives 100% sensitivity for occult fracture
versus 86% for T2 alone.

### Where the notebook's typing goes wrong

1. **[Certain] GRE tested last.** A 2D T2*/MEDIC at TR 800-1200 passes `TR >= 800`
   and is typed PD. `ScanningSequence` containing `GR` must be tested first.
2. **[Certain] `TR < 800` for T1 is too tight.** In 2D multi-slice FSE, TR is
   driven by slice count, and tissue T1 lengthens with field strength, so 3T T1
   routinely runs TR 700-1100.
3. **[Certain] Intermediate-weighted collapsed into PD.** TE 30-40 sequences are
   the majority of modern knee fluid-sensitive series and are physically much
   closer to T2 than to a TE-12 PD.
4. **[Certain] IR is never a class.** STIR at TE 110 becomes T2; STIR at TE 40
   becomes PD. One clinical sequence, two buckets, decided by vendor TE choice.
5. **[Likely] A global `TE > 60` boundary is field-strength dependent.**

Implemented in `src/sequence_typing.py`.

## 1.2 Fat suppression and fluid sensitivity are orthogonal

**[Certain]** They are produced by different physics:

- **Fluid sensitivity** = long TE (or TI recovery) so long-T2 free water is
  brightest. Controlled by TE/TI.
- **Fat suppression** = removal of the lipid methylene resonance, by frequency
  selectivity (CHESS/SPIR/SPAIR, 3.5 ppm = 220 Hz at 1.5T, 440 Hz at 3T), T1
  nulling (STIR), or phase separation (Dixon). A separate preparation module.

Combinations that break the correlation, all present in an international dataset:

| sequence | fluid-sensitive | fat-suppressed | note |
|---|---|---|---|
| T2 FSE, no fat sat | 1 | 0 | common in older/low-field protocols |
| PD FSE, no fat sat | 0 | 0 | meniscus sequence |
| STIR | 1 | 1 | also nulls mucoid, haemorrhagic, enhancing tissue |
| **T1 FS post-contrast** | **0** | **1** | bright fluid-like signal that is enhancement |
| Dixon water-only | depends on TE | 1 | uniform null with no SNR penalty |
| Dixon in-phase | same TE | 0 | **same acquisition, opposite flag** |
| GRE / MEDIC | 0 | 0 | T2*, fluid moderately bright |

**[Certain]** Dixon is the sharpest case: one 2-point acquisition yields
water-only and in-phase with *identical TR/TE*, so no TR/TE rule can separate
them. Detect by pairing - same plane, geometry, TR, TE, opposite fat-sat flag.
Implemented as `sequence_typing.find_dixon_pairs`.

**Findings that require fat suppression:** Contusion and Fracture oedema (marrow
oedema is water replacing fat inside a fat-dominated compartment; STIR alone 99%
sensitive for occult fracture, T2 alone 86%), Synovitis (Hoffa-synovitis is
defined on fat-suppressed images and does not exist without it), MCL (the
sensitive sign is fascial fat-plane oedema), the three OA labels (fat sat gives
increased contrast at the subchondral bone-cartilage interface).

**Findings where non-fat-sat is better:** the **fracture line** specifically -
the dark line is best on T1 without fat sat, against bright fatty marrow.

**[Certain] A correction to an assumption I held earlier.** Fat suppression does
*not* reduce meniscal conspicuity:
- Skeletal Radiology 2010, 48 arthroscopy-correlated patients: PD FS sens/spec
  95/92 and 93/93; PD non-FS 91/93 and 91/93. No significant difference.
- Clinical Radiology 2026 multireader ROC: medial meniscus AUC 0.9302 (PD) vs
  0.9229 (PD FS); lateral 0.8329 vs 0.8088. FS slightly more sensitive, slightly
  less specific.

The real mechanism to worry about is the opposite: non-FS **short-TE** PD carries
more magic-angle signal in the posterior horn of the lateral meniscus, and IW FS
reduces it. Keep both series types.

## 1.3 Intensity normalisation

**[Certain]** MRI voxel values are arbitrary units - "a combination of tissue
properties and hardware-specific settings, and thus do not have a specific
physical meaning" - varying scanner to scanner and even scan to scan.

**Three problems with per-slice percentile windowing:**

1. **It destroys amplitude.** Effusion, Synovitis, Contusion and Fracture are
   amplitude findings. Effusion-synovitis grade is literally a volume/distension
   grade. A per-slice 1-99% stretch maps the brightest fluid on every slice to
   1.0, so a trace and a tense effusion become identical except by area.
2. **It injects slice-to-slice flicker.** Consecutive slices get different
   transfer functions from their content alone, so a 2.5D model sees spurious
   through-plane gradients.
3. **The 99th percentile is set by different tissue in different sequences** -
   fluid on fat-suppressed, marrow fat on non-suppressed, unsuppressed
   subcutaneous fat when fat sat has failed. That is the opposite of standardising.

**Accepted methods:**
- **Nyul-Udupa piecewise-linear landmark matching** - learns histogram landmarks
  on a training cohort and warps each new volume onto them. Must be fit *per
  sequence type*, since histogram shape is sequence-specific.
- **WhiteStripe** (Shinohara et al., NeuroImage: Clinical 6:9-19, 2014) -
  z-score against a reference tissue that is contiguous and rarely pathological.
  **The knee analogue of normal-appearing white matter is skeletal muscle** -
  large, contiguous, rarely pathological, and already the accepted reference for
  signal-intensity ratios in MSK and cardiac oedema work.
- **N4/N3 bias field correction** - removes coil sensitivity roll-off. Relevant
  because knee coils have strong gradients and marrow near a coil element reads
  brighter than marrow at the centre.
- **ComBat** - **[Certain] the wrong tool here.** It operates on features not
  images, assumes normality, and requires a known site label, which does not
  exist at test time on 1300 unseen studies.

**[Likely]** Evidence that standardisation helps out-of-distribution: multi-centre
FLAIR white-matter-lesion segmentation improved Dice 0.71 → 0.77 (large lesions),
0.61 → 0.66 (medium) with proper standardisation. Brain, not knee.

Implemented in `src/normalize.py`.

## 1.4 Geometry, resolution and sampling

**Typical knee geometry**, converging across ESSR, Corsmed, MRImaster and OAI:
- 2D FSE slice thickness **3 mm**, gap 0.3 mm or 10%, effective spacing 3.0-3.6 mm
- in-plane FOV **140-160 mm**, matrix 256-512, so **0.3-0.6 mm/pixel**
- 30-34 slices sagittal (~100-110 mm), 30-34 coronal
- 3D isotropic (DESS/VISTA/CUBE) 0.4-0.7 mm, reconstructed to 1.5 mm

The competition's 20-45 slices, median 30, matches routine 2D 3 mm protocols.

**Minimum resolution per finding [Likely, extrapolated from lesion sizes]:**
- ACL, MCL, Baker's, Effusion, large Contusion, displaced Fracture - coarse,
  robust at 224 px over 140 mm.
- **Meniscal tear** - the cleft is sub-millimetre. Most damaged by downsampling.
  224 px over 140 mm = 0.63 mm/px against an acquisition at 0.44. **384 px is
  meaningfully better here.**
- **Cartilage / OA** - femoral cartilage is 2-3 mm thick, a full-thickness defect
  ~2 mm, partial ~1 mm. Same argument. Note even native-resolution MRI has poor
  sensitivity for Outerbridge grade 1, so there is a real ceiling regardless.

**Is 130 mm the right crop?**
- **[Certain]** For a 140 mm FOV acquisition it is nearly a no-op (93%).
- **[Certain]** For 180-200 mm FOV (low-field extremity units, large patients) it
  does real work.
- **[Likely] Too tight for sagittal.** Sagittal in-plane axes are A-P and S-I, and
  adult patella-to-popliteal-skin depth routinely exceeds 130 mm. A centre crop
  can clip the patella (PF OA) or the popliteal fossa (Baker's).
- **[Certain] `PixelSpacing[0]` is the wrong index for width.** DICOM PixelSpacing
  is `[row spacing (vertical), column spacing (horizontal)]`. Harmless for square
  pixels, a silent error for anisotropic or phase-oversampled series.
- **[Certain] Centre-of-FOV is not centre-of-knee.** Rectangular FOV, phase
  oversampling and off-centre coil placement all shift it. A content-based centre
  costs almost nothing.

**Where each finding sits, and what uniform sampling discards:**

| plane | stack direction | discarded first 12% | discarded last 12% |
|---|---|---|---|
| sagittal | medial → lateral | MCL, peripheral medial meniscus body, medial osteophytes | peripheral lateral meniscus, lateral osteophytes, fibular head |
| coronal | anterior → posterior | **patella and trochlea = PF OA**, Hoffa fat pad = Synovitis | **popliteal fossa = Baker's**, posterior horns, posterior recess |
| axial | superior → inferior | **suprapatellar pouch = Effusion** (76% of effusions; ≥4 mm depth is the standard threshold) | tibial tuberosity, distal MCL insertion |

At 30 slices, 0.12-0.88 discards ~3.6 slices at each end - roughly the whole
suprapatellar recess on axial, roughly the whole patella on coronal.

Conversely the ACL sits in the intercondylar notch, the *middle* of a sagittal
stack, which is presumably why a central band tuned well overall. The fix is not
to widen the band uniformly but to make sampling **anisotropic**.

**Recovering spacing without SliceThickness:**

```
n = cross(IOP[0:3], IOP[3:6])
n = n * sign(n · a_canonical)      # canonicalise
z_i = IPP_i · n                     # signed slice coordinate, mm
spacing = median(diff(sort(z_i)))   # = SliceThickness + gap
coverage = ptp(z)                   # total extent, a strong QC feature
```

Implemented as `geometry.slice_metrics`.

## 1.5 Artefacts and confounders

**Magic angle. [Certain]** Ordered collagen has dipolar coupling that averages to
zero at **54.7 degrees to B0**, lengthening apparent T2 and producing spurious
high signal. Appears on **short-TE images** and vanishes on long-TE. Classically
hits the **upsloping medial segment of the posterior horn of the normal lateral
meniscus**. Increasing TE beyond ~37 ms abolishes it while real pathology stays
bright. **Header-detectable via TE**, so it is a direct false-positive predictor
for the Lateral Meniscus target specifically.

**Truncation / Gibbs. [Certain]** Finite k-space sampling produces ringing
parallel to a high-contrast edge, creating linear intrameniscal signal that mimics
a tear. Detectable in principle from `AcquisitionMatrix` and
`InPlanePhaseEncodingDirection` if those survived the allowlist.

**Partial volume. [Certain]** At 3-3.6 mm spacing the concave meniscal margin and
sloping tibial plateau average with adjacent fluid. Fully quantifiable from
IPP-derived spacing.

**Chemical shift. [Certain]** Fat and water resonate 3.5 ppm apart, displacing
fat along the frequency-encode axis. In MSK "these artifacts appear similar to
bone fractures". Doubles at 3T.

**Failed fat suppression. [Certain]** CHESS/SPIR/SPAIR fail with B0
inhomogeneity, "particularly exacerbated in off-isocenter imaging" - which is
exactly the knee in a large-bore magnet. STIR is immune because it nulls by T1.
**This is the most consequential artefact here**: a series whose header says
`Fat_Suppression = 1` but where fat sat failed presents bright marrow fat that
hides oedema. Not header-detectable but **trivially image-detectable** via the
subcutaneous-fat-to-muscle ratio. Implemented as `normalize.fatsat_failure_ratio`.

**Susceptibility / metal. [Certain]** ACL interference screws cause extensive
signal loss, sometimes rendering a study uninterpretable. A MARS/WARP/SEMAC series
in the description is itself a strong indicator of prior surgery, and prior ACL
reconstruction is highly informative for the ACL label.

## 1.6 Laterality and orientation

**[Certain]** DICOM patient coordinates are **LPS**: +x patient left, +y
posterior, +z superior. `IOP[0:3]` is the unit vector along increasing column
index; `IOP[3:6]` along increasing row index; `IPP` is the LPS position of the
centre of the top-left pixel.

**[Certain] LPS is patient-relative and already absorbs PatientPosition**, so
head-first/feet-first and prone/supine need no special handling.

**[Certain] Two independent failure modes in the notebook:**

1. `median(IPP.x)` is the image **corner**, not the knee. For coronal and axial
   every slice shares the same corner x ≈ `-FOV/2`, so the median is a
   near-constant negative number. (This applies to the *legacy* path
   `side_from_corner_x`; the default `side_from_geometry` correctly reconstructs
   the centre.)
2. Even for sagittal, the knee is isocentred - "the patella aligned to the centre
   of the coil", "the knee centred at isocentre" - so knee_centre_x ≈ 0 and the
   sign is close to noise.

**[Certain] The slice-normal sign is separately fragile.** For sagittal knee, one
vendor writes `IOP = [0,1,0, 0,0,-1]` giving normal `(-1,0,0)`, another writes
`[0,-1,0, 0,0,-1]` giving `(+1,0,0)`. Sorting ascending therefore runs
medial→lateral in one case and lateral→medial in the other.

**Damage model [Likely, with stated assumptions]** - symmetric label noise at
rate p on the four side-specific targets:

| p | AUC on those 4, from a clean 0.90 | macro cost |
|---|---|---|
| 0.05 | 0.86 | -0.013 |
| 0.10 | 0.82 | -0.027 |
| 0.20 | 0.74 | -0.053 |
| 0.50 | 0.50 | -0.133 |

Two softeners: Medial and Lateral OA co-occur in generalised OA, so a swap partly
preserves signal; and prevalence is asymmetric (medial commoner), so a swap
biases toward the medial pattern rather than randomising - but that also means
the *lateral* targets take the damage.

**The rigorous algorithm** is implemented in `src/geometry.py`. For the
missing-laterality case, the reliable signals are anatomical rather than header:
the **fibula is always lateral**, the medial femoral condyle is larger and extends
further distally. Train a small CNN on the subset where `Laterality` *is* present
- free supervision, likely tens of thousands of series - and propagate at **study**
level, since all series in a knee study image the same knee.

## 1.7 Field strength and vendor effects

**[Certain]** SNR at 3T is roughly 2x that at 1.5T. T1 lengthens with B0, T2
shortens slightly. STIR TI must rise from ~130-180 ms at 1.5T to ~190-230 at 3T.
Chemical shift doubles, but frequency-selective fat sat gets *easier* because the
peaks separate further.

**[Certain] Field strength barely changes diagnostic accuracy, with one exception:**
- Meniscus: 1.5T sens/spec 92.7/82.2 vs 3T 92.6/76.1. One study found 1.5T
  *higher* sensitivity for lateral meniscal tears. "3T MRI of the knee does not
  improve diagnosis accuracy compared to 1.5T for meniscal and cruciate lesions."
- ACL: 1.5T 100/100 vs 3T 95.5/100 - equal.
- **Cartilage is the exception**: 3T improves sensitivity 70.6 → 75.7%, accuracy
  86.4 → 88.2%, correct grading 42.9 → 51.3%.
- Low field: dedicated extremity 0.2-0.31T reports 95.8/97.4 medial meniscus,
  100/100 ACL. 0.55T with DL reconstruction matched 1.5T.

So **the three OA labels are the only ones with a real field-strength
dependence**, and low-field studies should not be excluded.

**Inferring field strength if `MagneticFieldStrength` is absent [Likely]:** T2
series TE (~80-120 at 1.5T, ~70-80 at 3T); T1 TR; PixelSpacing and matrix (3T
routinely 0.3-0.4 mm/px, 1.5T 0.45-0.6, low-field 0.6-0.9); vendor strings;
`InversionTime` if present is the cleanest single discriminator (TI ~150-180 →
1.5T, ~200-230 → 3T). Best practice is to feed the proxies as conditioning
features rather than hard-classify.

---

# Part 2 - MSK radiology

## 2.1 Per-finding imaging protocol

ESSR requires all three orthogonal planes, slice thickness ≤3 mm preferred, and
explicitly both T2/fluid-sensitive and T1-weighted images - the latter
specifically "to differentiate between causes of bone marrow pathology and to
detect microfracture lines".

| finding | reference plane + sequence | secondary | low value |
|---|---|---|---|
| ACL | **sagittal** (oblique ideal) PD/FS-IW; primary signs sens 96% spec 94% | coronal FS (empty notch; 92/83); axial FS (oblique axial raised sens 74%→95%) | none |
| MCL | **coronal** FS-IW/T2 - essentially a coronal diagnosis | axial FS for distal extent | sagittal alone |
| Medial meniscus | **sagittal** FS/PD (horns, ramp, bucket-handle) **plus coronal** (body, root, extrusion) | axial for radial/root tears | neither is dispensable |
| Lateral meniscus | as medial, **coronal + axial weight higher**; posterior horn has the lowest sensitivity of any meniscal location | sagittal FS | popliteus hiatus is the classic pitfall |
| Medial OA | **coronal** FS-IW + sagittal FS | sagittal T1/PD for osteophytes | axial |
| Lateral OA | as medial, coronal-dominant | sagittal FS | axial |
| PF OA | **axial** FS-IW is mandatory - cartilage seen en face, "crater sign" is axial; axial ICC consistently higher than sagittal | sagittal FS | coronal is near-useless |
| Effusion | **axial** FS-IW at the suprapatellar pouch (single axial slice validated against multi-slice volume) | sagittal FS | coronal T1 |
| Synovitis | **contrast-enhanced T1 FS is the true reference**; non-contrast: sagittal FS-IW for Hoffa-synovitis | any fluid-sensitive plane | non-FS |
| Baker's | **axial** T2/FS - "especially in the axial plane"; fluid between semimembranosus and medial gastrocnemius communicating with a posterior cyst is ~100% accurate | sagittal FS | coronal T1 |
| Contusion | any fluid-sensitive FS plane | axial for patellar dislocation patterns | non-FS is near-blind |
| Fracture | **T1 non-FS is the discriminating sequence** - lines are low-signal linear on T1; FS shows oedema but blurs the line | coronal + sagittal T1 | FS-only reading confuses contusion with fracture |

**Key asymmetries the notebook ignores:** Fracture is the only label where non-FS
T1 is primary evidence, and there is no axial or sagittal T1 slot. PF OA is the
only label that fundamentally requires axial. MCL is close to a single-plane
diagnosis. Baker's and Effusion are labels where axial is cheap and near-diagnostic.

Encoded in `sampling.PLANE_WEIGHT` and `sampling.CONTRAST_WEIGHT`.

## 2.2 Per-finding diagnostic signs

### ACL

Primary: fibre discontinuity, non-visualisation, wavy contour, diffuse
intrasubstance high signal. **ACL angle** - normal fibres parallel to or under
10-15 degrees from the intercondylar roof. **Empty notch sign** on axial/coronal.

Secondary, with published operating points:

| sign | plane | sens | spec |
|---|---|---|---|
| anterior tibial translation ≥5 mm | sagittal | 58% (one series 86%) | 93% (one 99%) |
| translation ≥7 mm | sagittal | low | ~100% |
| PCL angle <107° | sagittal | 52% | 94% |
| PCL bowing ratio >0.39 | sagittal | 34% | 100% |
| deep lateral femoral notch >1.5 mm | sagittal lateral | in 20-60% of ACL tears | high |
| Segond fracture | coronal/axial far lateral | 3-7% of ruptures | 75-100% have ACL tear |

**Pivot-shift contusion pattern - the most informative secondary sign for a
model. [Certain]** In acute ACL tears bone bruises are present in **92.3%**:
lateral tibial plateau 83.9%, lateral femoral condyle 78.6%, medial tibial plateau
56.5%, medial femoral condyle 29.8%. A systematic review over ~3,900 knees gives
LTP 82.8%, LFC 71.4%. Only 7.7% had no bruise.

### Menisci

**[Certain] Grading:** grade 1 globular/punctate signal not reaching a surface;
grade 2 linear signal not reaching a surface; grade 3 signal unequivocally
contacting an articular surface = tear. Only grade 3 counts. Histological
correlation confirms grade 1/2 is mucoid degeneration, not tear.

Threshold choice moves operating characteristics enormously. For medial tears:
grade 5 (definite) as cut-off gives sens 0.91 / spec 0.94; grades 4-5 gives
0.96 / 0.76; grades 3-5 gives 0.99 / **0.47**. Since AUC is threshold-free, the
model should reproduce the *continuous* confidence - the ranking information lives
in the equivocal band.

| morphology | sign | plane | performance |
|---|---|---|---|
| bucket-handle | absent bow-tie (body on <2 consecutive sagittal slices) | sagittal | sens 88-97% |
| bucket-handle | double PCL sign | sagittal | spec 100% |
| bucket-handle | flipped meniscus | sagittal | spec 89.7% |
| root tear | vertical linear defect, "giraffe neck" on coronal FS; ghost meniscus on sagittal | coronal | commonly missed per ESSR |
| root tear | extrusion ≥3 mm (Costa), ≥4 mm (Svensson), ≥2.5 mm (OAI) | coronal mid | all MMPRT had ≥2 mm |
| ramp lesion | fluid cleft at posteromedial meniscocapsular junction | sagittal FS posteromedial | pooled sens 71% spec 94%; individual studies 0-77% |

**[Certain] The two meniscus labels are not equally hard**: pooled sensitivity
91.0% medial vs **78.5% lateral**; in ACL-injured knees lateral posterior horn
sensitivity falls to **58.5%**.

### OA compartments

**[Certain]** MRI-defined OA is not radiographic OA. The MOST definition requires
**both** WORMS cartilage damage ≥2 and WORMS osteophyte ≥2.

Grading systems: **Outerbridge** 0 normal, 1 softening with intact surface, 2
<50% depth, 3 >50%, 4 full-thickness to bone. **ICRS** identical with grade 3
subdivided. **WORMS** cartilage 0-6, BML 0-3, osteophytes 0-7 at 16 locations.
**MOAKS** dual-graded cartilage, adds Hoffa-synovitis 0-3 and effusion-synovitis
0-3. **Kellgren-Lawrence** 0-4, with **KL≥2 the conventional definition of
definite OA**.

**[Certain] Compartment distribution:** single-compartment 50% (31.5-58.3%),
bicompartmental 33%, tricompartmental only 17%. So a model that learns one latent
"OA-ness" and copies it to all three heads loses ranking on the discriminating
half of cases.

### Effusion vs Synovitis

**[Certain]** The hardest distinction of the twelve on non-contrast MRI:
- True synovitis requires contrast-enhanced T1 FS. On non-contrast,
  effusion-synovitis and Hoffa-synovitis are accepted *surrogates*, not equivalents.
- "Fluid-sensitive MRI sequences are not able to properly distinguish joint
  effusion from synovial thickening and therefore commonly over-report effusion."
- Hoffa signal is "only a non-specific marker" against CE-MRI.
- Grading by capsular distension: grade 1 <33%, grade 2 33-66%, grade 3 >66%.

Proxy signs a model can learn: suprapatellar pouch fluid volume (→ Effusion);
**complexity** of the fluid - septations, debris, intermediate signal, loss of a
sharp fluid-fat-pad interface (→ Synovitis); thickness and irregularity of the
fluid-synovium border; Hoffa hyperintensity.

The discriminating signal is texture and border morphology at the fluid-soft-tissue
interface - exactly what a 130 mm crop aggressively downsampled destroys.

### Contusion vs Fracture

**[Certain]** Bone contusion is ill-defined, geographic, reticulated marrow signal,
"distinguished from a fracture because of the absence of a contour deformity or
fracture line". Occult fracture is a discrete curvilinear **hypointensity on T1
within** the oedema.

**The overlap is large and unavoidable:** occult fractures were found in 72% of
knees with acute post-traumatic haemarthrosis, and 56% of acute ACL-injured knees
- many of which other readers would call contusions.

**The operational fact:** the discriminator is a thin low-signal line best seen on
**T1**, not on the fat-suppressed sequences the pipeline weights most heavily, and
it is a high-spatial-frequency feature surviving neither aggressive downsampling
nor stride-3 slice sampling.

## 2.3 Co-occurrence, quantified

| association | rate |
|---|---|
| acute ACL tear → any bone bruise | **92.3%** (7.7% none) |
| ... lateral tibial plateau | 83.9% (review 82.8%) |
| ... lateral femoral condyle | 78.6% (review 71.4%) |
| ... both compartments | 65.5%; isolated lateral 24.4%; isolated medial 2.4% |
| acute ACL → lateral meniscus tear | 38.2-56.1% |
| acute ACL → medial meniscus tear | 14.7-45.3% |
| **chronic** ACL deficiency → medial meniscus tear | 68.75% vs lateral 12.5%; overall up to 96% |
| ACL → ramp lesion | 9-34% |
| Segond → ACL tear | **75-100%** (Segond in only 3-7% of ACL tears) |
| Segond → meniscal tear | 67% |
| deep lateral femoral notch → ACL tear | notch in 20-60% of ACL tears; highly specific |
| clinical grade III MCL → ACL tear | 75% |
| O'Donoghue triad (ACL+MCL+**medial** meniscus) | ~25% of acute athletic knee injuries |
| Shelbourne revision: ACL+MCL+**lateral** meniscus | lateral 71% vs medial 32% |
| MM posterior root tear → extrusion | 100% had ≥2 mm |
| Baker's given 1 of {effusion, meniscal tear, degenerative arthropathy} | P = 0.08-0.10 |
| Baker's given 2 | P = 0.19-0.21 |
| Baker's given all 3 | **P = 0.38** |
| lateral patellar dislocation → MPFL abnormality | **82-100%** |
| patellar dislocation → osteochondral injury inferomedial patella | up to 70% |

**How to exploit, in increasing order of risk:**
1. **Multi-task structure (safest).** Shared trunk, per-label heads reading
   anatomically-routed features, plus auxiliary heads for the *mediating* signs
   (lateral compartment bruise, extrusion, MPFL, Segond, PCL buckling) - the
   causal variables that explain the correlation.
2. **Second-stage stacker (best value per hour).** Fit a small model on
   out-of-fold 12-logit vectors plus auxiliary-sign logits.
3. **Post-hoc rules (riskiest).** Brittle to prevalence shift. And **any
   adjustment that changes ranking uniformly is a no-op for AUC**.

**[Likely] Caveat:** labels here are image-derived by adjudicating radiologists,
so co-occurrence in the label file may be weaker than in the clinical literature.

## 2.4 Prevalence and epidemiology

Literature anchors for a general clinical knee MRI population. **Not measured on
this dataset** - `scripts/audit_labels.py` replaces these.

| finding | expected base rate | basis |
|---|---|---|
| ACL | **20-25%** | MRNet 319/1370 = 23.3%; KneeMRI Rijeka 227/917 = 24.8% |
| MCL | 10-20% [Likely] | ligament lesions 36.2% in a symptomatic series |
| Medial Meniscus | **25-40%** | MRNet meniscal 37.1%; symptomatic 37.9%; asymptomatic 3T 30% |
| Lateral Meniscus | 10-20% [Likely] | consistently less common outside acute ACL |
| Medial OA | 15-30% [Likely] | medial is the commonest single compartment |
| Lateral OA | 5-12% [Likely] | isolated lateral is the least common pattern |
| PF OA | 20-40% [Likely] | PF cartilage abnormality 57% in *asymptomatic* 3T knees |
| Effusion | **40-65%** | 63.8% symptomatic; 74.4% in a Saudi cohort |
| Synovitis | 10-25% [Guessing] | depends entirely on the organisers' threshold |
| Baker's | **10-33%** | 10.4-10.6% clinical; 33% asymptomatic 3T; range 10-41% |
| Contusion | 5-25% [Guessing] | 5.2% BME in one series, 48% "marrow abnormalities" at 3T |
| Fracture | 2-8% [Guessing] | 56-72% in acute haemarthrosis, but that is highly selected |

**Which labels dominate the macro average.** At ~1300 test studies:
- Fracture at 3% = ~39 positives. AUC SE around 0.90 ≈ **±0.033**. That single
  label's noise is comparable to the entire spread between leaderboard positions.
- Lateral OA at 8% = ~104 positives, SE ≈ ±0.02.
- Effusion at 55% = ~715 positives, SE ≈ ±0.01, essentially saturated.

**The consequence:** improving Effusion 0.95 → 0.96 moves macro by 0.0008.
Improving Fracture 0.80 → 0.88 moves it by 0.0067 - eight times more.

## 2.5 Inter-reader reliability - the ceiling

| finding | agreement | source |
|---|---|---|
| ACL tear | **kappa 0.73**; oblique planes raise reader kappa 0.606 → 0.759 | 1.5T vs arthroscopy |
| MCL | grading "inaccurate for grade 3, questionably accurate for 1 and 2"; MRI underestimated instability in up to 21% | Radiology 1995 |
| Medial meniscus | **kappa 0.70**; BLOKS tear 0.79 | |
| Lateral meniscus | lower - PHLM sensitivity 58.5% in ACL-injured knees | AJR |
| Meniscal extrusion | **kappa 0.51** - worst meniscal item | BLOKS |
| OA cartilage morphology | **kappa 0.57-0.72**; chondral lesion kappa ranged **0.06-0.78** | |
| OA bone marrow lesions | **kappa 0.88** - most reliable OA feature | |
| Effusion grading | percent agreement 0.70; MOAKS ICC ~0.72 | |
| **Synovitis** | BLOKS **kappa 0.62**; Hoffa-synovitis intra-rater **0.42** | |
| Baker's | not formally reported; [Likely] >0.85 | |
| Contusion / BML | **kappa 0.88** | |
| Fracture | not reported; [Likely] moderate | |
| Ramp lesion | poor; MRI sensitivity 0-77% across studies | |

**Reading this for the competition:**
- **High ceiling (kappa ≥0.79):** ACL, Medial Meniscus, Contusion, Baker's,
  Effusion. Should already be near-saturated. MRNet reached ACL AUC 0.965 in 2018.
- **Middle (0.6-0.75):** Lateral Meniscus, MCL, the three OA compartments.
- **Low ceiling (≤0.62):** **Synovitis** and the contusion/fracture boundary.
  Cartilage grading is bimodal - readers agree on grade 0 vs 4 and disagree
  everywhere in between, which is exactly where the OA threshold sits.

**[Likely] Do not rank effort by lowest current AUC** - that reliably
over-invests in Synovitis, whose low AUC is partly irreducible. Rank by
(kappa ceiling − current AUC) × achievability.

## 2.6 Anatomical localisation

Fractions of the traversed stack. **[Likely] anatomical estimates, not
measurements** - initialisation for an empirically fitted scheme. Note the
convention here is the agent's (sagittal 0 = most medial, coronal 0 = anterior,
axial 0 = **superior**); `src/sampling.py` uses axial 0 = inferior to match
`geometry.py`'s canonical ordering, so those bands are inverted.

| finding | sagittal (medial→lateral) | coronal (ant→post) | axial (sup→inf) |
|---|---|---|---|
| ACL | **0.55-0.72** | 0.55-0.80 | 0.30-0.60 |
| MCL | 0.02-0.15 (often clipped) | **0.30-0.60** | 0.35-0.75 |
| MM horns | **0.10-0.32** | 0.30-0.50 ant / **0.60-0.85** post | 0.45-0.60 |
| MM body | **0.05-0.18** (only 2-3 slices) | 0.35-0.60 | 0.45-0.60 |
| LM horns | **0.70-0.92** | as MM | 0.45-0.60 |
| LM body | **0.82-0.95** | 0.35-0.60 | 0.45-0.60 |
| Medial OA | 0.05-0.35 | **0.30-0.75** | 0.40-0.65 |
| Lateral OA | 0.68-0.95 | **0.30-0.75** | 0.40-0.65 |
| PF OA | 0.30-0.70 | 0.00-0.25 | **0.10-0.40** |
| Effusion | 0.25-0.75 | 0.00-0.30 + 0.80-1.0 | **0.00-0.30** |
| Synovitis | 0.30-0.70 | 0.00-0.25 | **0.05-0.45** |
| Baker's | **0.08-0.30** | **0.85-1.00** | **0.55-0.95** |
| Contusion | anywhere; ACL pattern **0.70-0.95** | 0.30-0.85 | 0.35-0.80 |
| Fracture | anywhere, subchondral | 0.30-0.85 | 0.40-0.85 |
| Segond | **0.85-0.97** | 0.45-0.70 | 0.55-0.70 |
| deep lateral notch | **0.70-0.88** | 0.20-0.45 | 0.30-0.50 |

**What uniform sampling does wrong, concretely:**
1. Peripheral truncation removes exactly where meniscal bodies, MCL and Segond live.
2. **[Certain]** The intact meniscal body appears on only **2-3 consecutive
   sagittal slices** - the whole basis of the absent bow-tie sign. Sampling 12
   from 32 is stride ~2.7, so there is a meaningful probability of seeing one or
   zero body slices even in a normal knee, making the feature unlearnable. The
   ACL is diagnostic on ~3-5 sagittal slices; roots and Segond on 1-2.
3. PF OA is starved: patellar cartilage occupies the superior 10-40% of an axial
   stack, so uniform 12-88% sampling spends two thirds on levels with no patellar
   cartilage.
4. Baker's neck sits at the posteromedial edge of a 130 mm centre crop.

**Reusable segmentation resources**, all trained on DESS/qDESS gradient-echo from
OAI-type protocols, so **[Likely] a large domain gap to clinical 2D FSE**:
**OAI-ZIB** (507 manual bone/cartilage segmentations), **IWOAI 2019** challenge
(pretrained weights public), **DOSMA** (two pretrained models plus automatic
cartilage subregion division - exactly the compartment assignment needed),
**SKM-TEA** (segmentations plus 16 pathology bounding-box categories).

**[Likely] A landmark regressor trained on the competition data itself is a
better investment than adapting an OAI segmentation model.**

## 2.7 Public datasets and prior art

| dataset | size | labels | licence | usable? |
|---|---|---|---|---|
| **MRNet** (Stanford) | 1,370 exams (23.3% ACL, 37.1% meniscal) | study-level abnormal / ACL / meniscal | Stanford RUA, non-commercial, **no redistribution** | [Likely] pretraining ok; do not ship the data |
| **KneeMRI** (Rijeka) | 917 volumes | ACL 3-class | publicly downloadable, licence unconfirmed | [Guessing] |
| **OAI** | ~4,796 participants, longitudinal | KL grades, MOAKS/WORMS subsets | NDA + DUA | OA/cartilage pretraining only; slow access |
| **MOST** | large longitudinal | OA structural readings | biobank request, **reviewed only Jan/May/Sep** | **effectively unusable on this timeline** |
| **SKM-TEA** | 155 patients, 1.6 TB | 6-class segmentations + 16 pathology bboxes | Stanford AIMI clickthrough | good for localisation supervision; large domain gap |
| **fastMRI knee** | ~1,500 volumes | reconstruction; fastMRI+ adds bboxes | NYU, internal research only | marginal |
| **OAI-ZIB / IWOAI** | 507 / 9,040 segmentations | bone + cartilage | public code and models | good for cartilage weights |

**[Certain] Every one is non-commercial research-only.** The competition requires
winning solutions under CC-BY-NC 4.0, so the *spirit* aligns, but Kaggle's
external-data rule requires data be freely and equally available to all
participants, and a registration-gated DUA arguably fails that. **Post on the
competition's external-data thread before building on any of them.**

**Published performance on this task:**

| model | abnormality | ACL | meniscus | method |
|---|---|---|---|---|
| **MRNet** (2018) | 0.937 | **0.965** | 0.847 | AlexNet per slice, max-pool, logistic-regression fusion of 3 series |
| **ELNet** (2020) | 0.941 | 0.960 | **0.904** | lightweight blurpool CNN, single series |
| **MRPyrNet** (2021) | - | ~88.6% acc | ~77.8% acc | Feature Pyramid Network bolted onto MRNet/ELNet |

**Three transferable lessons:** ACL is essentially solved at ~0.96 on
single-institution data, so a large gap means domain shift or slice sampling, not
architecture. Meniscus trails ACL by 0.06-0.12 consistently across seven years.
**MRPyrNet's contribution is specifically a feature pyramid to capture small
lesions**, and it improved exactly the small-lesion tasks - direct evidence that
the binding constraint is spatial resolution on small structures, not
representation quality.

Also relevant: **MRNet trains one model per plane and fuses with logistic
regression, and reports that the most informative plane differs per condition** -
axial PD for abnormality and meniscal tear, coronal T1 for ACL. Empirical
confirmation of per-label routing.

---

# Part 3 - Radiology report NLP

## 3.1 The framing correction

**[Certain]** RSNA states the training set is >5,000 knee MRI exams with reports
in "a dozen different languages" from **16 sites across five continents**, and
the *evaluation* set was "annotated by expert radiologists".

**So the test target is image-derived, not report-derived.** The objective is to
build a function from report text to *the distribution over what an image-reading
annotator would say*. VisualCheXbert measured exactly this gap and gained **+0.14
F1 on average, +0.12 to +0.21 per condition** by mapping reports to *image*
labels rather than report labels. Separately, "Caveats in Generating Medical
Imaging Labels from Radiology Reports" showed "a surprisingly large discrepancy
between what radiologists visually perceive and what they clinically report".

**[Guessing] The reported 58 gold studies of 4,407, and 82% report-image
agreement**, come from the RSNA challenge page and a secondary summary, not from
the data. Must be verified.

## 3.2 Negation and uncertainty

| system | approach | performance |
|---|---|---|
| NegEx | regex trigger + fixed window | F1 0.84-0.89 on narrative clinical text |
| pyConTextNLP | NegEx + experiencer + temporality | comparable |
| **medspaCy ConText** | spaCy, sentence-scoped | on 984 radiology reports: **F1 0.492, precision 0.356, recall 0.795** |
| **CAN-BERT** | transformer assertion classifier | same corpus: **F1 0.777, precision 0.768** |
| **NegBio** | universal-dependency subgraph matching | **+9.5% precision, +5.1% F1 over NegEx** |
| fine-tuned LLM | 6 assertion classes | accuracy 0.962 vs GPT-4o 0.901 |

**[Certain] The medspaCy number is the important one:** off-the-shelf window
negation applied to arbitrary spans in radiology text has **precision around
0.36** - it over-negates massively.

**Measured failure modes of the notebook's 55/90-character window.** An agent ran
`extract()` over 40 assertions in 24 constructed sentences: **8/40 wrong (20%)**.
A sidedness-focused probe: **5/29 wrong (17%)**. [Certain] for those sentences;
[Guessing] the corpus-wide rate, probably 5-12%. Treat 17-20% as the rate *on the
hard constructions that matter*.

I independently reproduced and fixed three of these - see `FINDINGS.md` 1-3.

**Hedged language under AUC. [Certain]** AUC only cares about ranking, so never
threshold. The correct treatment of a hedge is a target between the confident
poles, positioned at the empirical P(present | hedge used) estimated on gold.
Evidence: soft-label ensembles significantly outperform hard-label methods **as
measured by AUC**. CheXpert uncertainty policies are **pathology-dependent** -
U-Ones+LSR best for some, U-MultiClass for others, and **U-Ignore generally
sub-optimal**.

## 3.3 State of the art labelers

| system | key number | borrowable |
|---|---|---|
| CheXpert labeler | macro F1 0.743 | design pattern |
| **CheXbert** | **F1 0.798 vs radiologist 0.805** | **yes - the recipe transfers directly** |
| **VisualCheXbert** | **+0.14 F1** over report-labeler when the target is what a radiologist sees | **yes - most relevant paper to this competition** |
| RadGraph / RadGraph-XL | 2,300 reports, 410k entities; beats GPT-4 in-domain | schema yes; weights are CXR/CT, **no MSK**, English only |
| CheX-GPT | macro F1 **92.79** vs CheXbert 79.8 | recipe |
| **MOSAIC** (MedGemma-4B) | mean macro F1 **88** across 5 CXR datasets; **weighted F1 82 on Danish from 80 annotated samples**; runs in 24 GB | **closest published analogue** |

**[Certain] No MSK- or knee-specific published report labeler exists.** The field
is overwhelmingly chest. Every performance number cited is a chest analogue.

**LLM vs rules:** GPT-4 micro F1 0.98, Llama-2-70B 0.97 on CXR labeling; few-shot
closed the gap for open models. **[Certain] The strongest single result for this
case:** in-context learning with **annotation instructions in the prompt** (the
label *definitions*, not examples) gave F1 gains of +0.17 to +0.31 on hard
categories, including **MSK +0.306**. Temperature 0 removed format errors.

**Open-weight candidates.** Labelling happens offline at training time, so the
labeler never runs in the submission kernel - only the external-tools rule applies.

| model | params | licence | multilingual | fit |
|---|---|---|---|---|
| **MedGemma-4B-it** | 4B | HAI-DEF (open weight, not OSI) | Gemma base | proven via MOSAIC; 24 GB |
| **Qwen3 / Qwen2.5 Instruct** | 7-32B | **Apache 2.0** | strong ES/FR/DE/IT/PT/TR/RU | **cleanest licence, best default** |
| Gemma 3 | 4-27B | Gemma terms | 140+ claimed | licence caveat |
| Llama 3.3-70B | 8-70B | Llama Community | 8 official | proven at 0.97 F1 |
| Apollo | ≤7B | open | 6, medical-tuned | small |
| MMedLM2 / MMed-Llama-3 | 8B | open | 6, 25.5B-token medical corpus | |
| BioMistral-7B | 7B | Apache 2.0 | PubMed | English-centric in practice |

**[Guessing] Licence risk:** whether Gemma/Llama community licences satisfy a
CC-BY-NC 4.0 open-sourcing requirement is a real question - they impose use
restrictions CC-BY-NC does not. **Qwen (Apache 2.0) avoids it entirely.**

## 3.4 Multilingual reports

**[Certain]** 12 languages, 16 sites, 5 continents. From the lexicon's own
coverage the author empirically found English, Spanish, French, Dutch, German,
Turkish, Croatian/Serbian/Bosnian, Greek, Bulgarian, plus scattered Portuguese -
about 9-10 of 12.

**[Likely] gaps, by probability:** Italian, Portuguese (Brazil accounts for the
South America site), Polish, Romanian, Czech/Slovak, Hebrew, Arabic, Japanese,
Korean, Chinese, Hindi. **CJK/Arabic/Hebrew would break `normalize()` entirely**
(NFKD + diacritic stripping + `[a-z]` assumptions).

### Vocabulary - Romance and Germanic

| concept | Spanish | French | Italian | Portuguese | German | Dutch |
|---|---|---|---|---|---|---|
| meniscal tear | rotura/desgarro meniscal | déchirure/fissuration méniscale | lesione meniscale, **meniscosi** | lesão/rotura meniscal | Meniskusriss, Einriss | meniscusscheur, ruptuur |
| medial meniscus | menisco medial/**interno** | ménisque médial/**interne** | menisco mediale/interno | menisco medial | Innenmeniskus | **binnenmeniscus** |
| lateral meniscus | menisco lateral/**externo** | ménisque latéral/**externe** | menisco laterale/esterno | menisco lateral | Außenmeniskus | **buitenmeniscus** |
| ACL | LCA | LCA | LCA | LCA | **VKB** | **VKB** |
| MCL | colateral medial/interno | collatéral **interne** | collaterale mediale | colateral medial | **Innenband** | **binnenband** |
| effusion | **derrame articular** | **épanchement** | **versamento articolare** | **derrame articular** | **Gelenkerguss** | **gewrichtsvocht** |
| Baker's cyst | quiste poplíteo | kyste poplité | **cisti di Baker** | cisto de Baker | **Bakerzyste** | **bakercyste** |
| marrow oedema | edema óseo | œdème osseux | edema osseo | edema ósseo | **Knochenmarködem** | **botmergoedeem** |
| fracture | fractura, fisura | fracture | frattura | fratura | Fraktur | fractuur |
| synovitis | sinovitis | synovite | sinovite | sinovite | **Synovialitis** | synovitis |
| OA | **artrosis**, gonartrosis, condropatía | **arthrose**, gonarthrose | **gonartrosi**, condropatia | **artrose** | **Gonarthrose**, Knorpelschaden | **artrose** |
| cartilage | cartílago | cartilage | cartilagine | cartilagem | **Knorpel** | **kraakbeen** |

### Vocabulary - Turkish, South Slavic, Greek, Bulgarian

| concept | Turkish | Croatian/Serbian | Greek | Bulgarian |
|---|---|---|---|---|
| meniscal tear | menisküs **yırtığı** | **ruptura**, puknuće | **ρήξη** μηνίσκου | **руптура** |
| medial meniscus | **iç menisküs** | **medijalni meniskus** | **έσω μηνίσκος** | **вътрешен менискус** |
| lateral meniscus | **dış menisküs** | **lateralni meniskus** | **έξω μηνίσκος** | **външен менискус** |
| ACL | **ön çapraz bağ (ÖÇB)** | **prednji križni ligament** | **πρόσθιος χιαστός** | **предна кръстна връзка** |
| MCL | **iç yan bağ (İYB)** | **medijalni kolateralni** | **έσω πλάγιος** | **медиален колатерален** |
| effusion | **eklem içi sıvı** | **izljev** | **αρθρικό υγρό** | **ставен излив** |
| Baker's cyst | **popliteal kist** | **Bakerova cista** | **κύστη Baker** | **киста на Бейкър** |
| marrow oedema | **kemik iliği ödemi** | **edem koštane srži** | **οστεομυελικό οίδημα** | **костномозъчен едем** |
| fracture | **kırık** | **prijelom** | **κάταγμα** | **фрактура** |
| synovitis | **sinovit** | **sinovitis** | **υμενίτιδα** | **синовит** |
| OA | **gonartroz**, kondropati | **gonartroza**, hondromalacija | **οστεοαρθρίτιδα** | **гонартроза** |
| cartilage | **kıkırdak** | **hrskavica** | **χόνδρος** | **хрущял** |

**[Certain] Gaps found in the current lexicon:** Italian essentially absent
(`meniscosi`, `versamento`, `cisti di Baker`, `gonartrosi`, `condropatia`,
`crociato`); `rotura` will not catch Italian `rottura` (two t's). Portuguese
near-absent (`lesão` normalises to `lesao`, and `\blesion` will not match).
`NORMALITY` lacks Italian `nella norma`, `integro`; Portuguese `íntegro`,
`preservado`. `PRE_NEG` lacks Italian `non`, `senza`; Portuguese `sem`, `não`.

**[Likely] Do not machine-translate as the primary path.** Translated versions
consistently yield lower accuracy; the BRIDGE benchmark (95 LLMs, 87 tasks, 9
languages) found consistent degradation in non-English clinical contexts; clinical
negation patterns are not translations of English patterns. The specific risk here
is **site-correlated bias**: translation quality varies by language, so
translation error becomes a site confounder, and since sites differ in case mix a
translation-induced label bias will look like real signal and will not transfer.

**A real language-specific problem:** German/French/Turkish/Croatian reports
frequently write a single global `Gonarthrose`/`gonartroz`/`gonartroza` with **no
compartment attribution**, whereas English/Dutch more often enumerate compartments.
The `oa_inherit` feature addresses this - and it was disabled by the bug I fixed.

## 3.5 Grading scales to binary

**[Likely] These thresholds matter more than architecture**, and the +0.306 MSK
ICL result is direct evidence that writing them into a prompt is the highest
leverage use of them.

| finding | text | binary | soft | rationale |
|---|---|---|---|---|
| Meniscus | grade 1 / punctate | 0 | 0.05 | not a tear [Certain] |
| Meniscus | **grade 2** / linear not reaching surface | 0 | **0.20** | not a tear by definition, but grade-2 vs 3 disagreement is the classic MSK error |
| Meniscus | grade 3 / reaching surface | 1 | 0.95 | [Certain] |
| Meniscus | tear, bucket-handle, macerated | 1 | 0.97 | |
| Meniscus | fraying, blunting, irregular free edge | 1 weak | 0.65 | commonly read as tear |
| Meniscus | degenerative/mucoid **without tear**, meniscosis | 0 | 0.20 | |
| Meniscus | post-meniscectomy | mask | mask | cannot be graded normally |
| ACL | complete tear / non-visualised | 1 | 0.98 | |
| ACL | **partial tear** | 1 | 0.90 | still an ACL abnormality |
| ACL | attenuated, lax, wavy, signal without discrete tear | 1 weak | 0.55 | genuinely borderline |
| ACL | **mucoid degeneration, no tear** | 0 | 0.15 | was a false positive at 0.83 |
| ACL | graft intact post-reconstruction | 0 | 0.10 | |
| MCL | **grade I sprain** (oedema, fibres intact) | 1 | **0.70** | the judgement call - target is "MCL injury" and grade I is an injury with a visible abnormality |
| MCL | grade II / III | 1 | 0.92 / 0.98 | |
| OA | Outerbridge/ICRS **1** | 0 | **0.25** | below the clinical threshold; was 0.85 |
| OA | Outerbridge 2 / 3 / 4 | 1 | 0.55 / 0.85 / 0.97 | |
| OA | **KL 0 / 1** | 0 | 0.05 / 0.20 | KL≥2 = definite OA [Certain] |
| OA | KL 2 / 3 / 4 | 1 | 0.65 / 0.90 / 0.97 | |
| OA | mild / moderate / severe | 1 | 0.50 / 0.85 / 0.97 | |
| OA | osteophytes only | 1 weak | 0.60 | KL 2 is defined by definite osteophytes |
| Effusion | **trace / physiologic** | 0 | **0.30** | MOAKS grade 0 is explicitly physiologic; was 0.72 |
| Effusion | small/mild, moderate, large | 1 | 0.70 / 0.92 / 0.98 | MOAKS grade 1 counts |
| Effusion | haemarthrosis | 1 | 0.98 | |
| Synovitis | explicit synovitis | 1 | 0.95 | |
| Synovitis | synovial thickening / pannus | 1 | 0.92 | |
| Synovitis | **effusion-synovitis** | 1 | 0.85 | |
| Synovitis | **Hoffa-synovitis, fat-pad oedema** | 1 weak | 0.65 | established non-contrast surrogate [Certain] |
| Synovitis | bursitis / plica only | weak | 0.35 | |
| Baker's | any Baker/popliteal cyst regardless of size | 1 | 0.96 | presence is binary |
| Baker's | parameniscal / meniscal cyst | 0 | 0.05 | decoy, keep |
| Contusion | bone bruise, kissing contusion, pivot-shift | 1 | 0.96 | |
| Contusion | marrow oedema **with trauma context** | 1 | 0.90 | |
| Contusion | **subchondral oedema in a degenerative context** | 0 | **0.25** | this is a bone marrow LESION, not a contusion; was 0.67 |
| Fracture | acute, avulsion, stress, insufficiency, osteochondral | 1 | 0.90-0.97 | |
| Fracture | **microfracture** (surgical procedure) | 0 | 0.03 | decoy, keep |
| Fracture | old / healed / consolidated | ambiguous | 0.45 | depends on whether annotators scored morphology or acuity |

## 3.6 Sidedness disambiguation

Four of twelve labels are side-specific, a fifth (MCL) inherently medial. **That
is 33% of the metric.**

| technique | value | evidence |
|---|---|---|
| relation extraction (RadGraph `located_at`) | explicit finding→anatomy link, distance-insensitive | beats GPT-4 in-domain |
| dependency parsing (NegBio) | scope not limited by word distance | +9.5% precision |
| **section segmentation** | compartment headings scope everything beneath | BI-RADS BERT: **95.9% vs 78.9%** field extraction - a **17-point absolute gain** |
| LLM extract + rule ensemble | best reported for laterality specifically | laterality "often crosses sentence boundaries, beyond current NLP pipeline capabilities" |

**Measured errors of the 55-char window** - 5/29 assertions wrong (17%), four
distinct causes, all of which I reproduced:

| construction | result | cause |
|---|---|---|
| "Medial compartment OA with sparing of the lateral compartment" | Lateral OA **0.85** FP | nothing detects that "sparing" scopes the side |
| "...medial meniscus without tear; small radial tear of the lateral meniscus" | Medial Meniscus **0.96** FP | post-posed "without" |
| "MEDIAL COMPARTMENT: Posterior horn tear. LATERAL: Normal." | Medial Meniscus **0.28** FN | heading does not scope the sentence beneath |
| "Tricompartmental OA, most severe in the patellofemoral joint" | Medial + Lateral OA **0.28** FN | the `_score_oa` bug |

The coordination case *passed* by luck: "tears of the posterior horn of the medial
and body of the lateral meniscus" gave both 0.96 because the stem matched once and
both side tokens fell inside ±55 chars. A longer construction breaks it.

## 3.7 Report sectioning

**[Certain] Impression is higher precision, lower recall.** One study found 3,401
reports with pulmonary nodules in Findings vs 2,162 in Impression - a **36.4%
shortfall**. CheXpert labels only the Impression and its authors acknowledge this
increases the report-image label disparity.

**[Likely] Use both, weight Impression higher.** Several targets here are
mentioned only in Findings and rarely reach the Impression - Effusion, Synovitis,
Baker's, mild compartmental OA. Restricting to Impression converts real positives
into negatives on exactly the low-prevalence targets. Suggested: Impression ×1.0,
Findings ×0.85, Findings-only ×0.75; an Impression negative overrides a Findings
positive.

**Multilingual section headers:**

| section | terms |
|---|---|
| Technique | technique, technik, técnica, tecnica, techniek, teknik, tehnika, τεχνική, протокол |
| Comparison | comparison, vergleich, comparación, comparaison, vergelijking, karşılaştırma, usporedba, σύγκριση |
| Findings | findings, befund, hallazgos, résultats, bevindingen, bulgular, nalaz, ευρήματα, находки |
| Impression | impression, conclusion, beurteilung, **beoordeling**, conclusión, conclusie, **sonuç**, **zaključak**, **συμπέρασμα**, заключение, **izlenim** |

**[Likely] A sharp catch:** Turkish `izlenim` is in the notebook's `UNCERTAIN`
regex, but `İzlenim:` is the standard Turkish section header for Impression, not a
hedge. If Turkish is a meaningful share, this could be systematically corrupting
polarity across it. (Ambiguous though - `izlenimi vermektedir` = "gives the
impression of" genuinely is hedging. Needs checking against real reports.)

**Three contaminants, none handled:**
1. **Prior-comparison statements.** "the previously described medial meniscal tear
   is no longer seen following partial meniscectomy" → 0.96 false positive.
   ConText's `historical` axis is exactly this.
2. **Clinical indication sections.** "History: suspected ACL tear" is a referral
   question, not a finding.
3. **Post-operative reports.** ACL graft, meniscectomy, arthroplasty. **[Likely]
   the highest-noise studies in any knee cohort** - the ACL tear was real but is
   now reconstructed. **Mask** the affected targets rather than labelling them.

## 3.8 Using the weak labels

**Measurement protocol [Certain]:** per target, on gold only - labeler AUC, AP,
precision/recall, and a reliability diagram in 10 bins. Report
**confidence-stratified**: if `__conf` is not monotone with accuracy, the
`0.25 + 0.75·conf` sample weight is doing nothing. Break down **by language and by
site** - a labeler at 0.90 on English and 0.60 on Greek gives site-correlated
noise, the worst kind.

**Absence is not negation. [Certain]** Quantified on a report with no synovitis
mention:

```
unmentioned Synovitis: 0.45  conf 0.18  -> sample weight 0.385
unmentioned Fracture:  0.28  conf 0.05  -> sample weight 0.288
unmentioned Medial OA: 0.28  conf 0.05  -> sample weight 0.288
```

Every unmentioned finding is pulled toward 0.28 at ~29% weight. Across ~5,000
studies that is a large aggregate gradient asserting "absent".

How wrong is 0.28? Base rates in **asymptomatic** knees:

| finding | prevalence in asymptomatic knees |
|---|---|
| any abnormality | **97%** |
| Baker's cyst | **33-38%** |
| meniscal tear | **30%** |
| PF cartilage lesion (moderate/severe) | 19% / 31% |

**[Likely] The unmentioned prior should be per-target and estimated from gold.**
For ACL - almost always explicitly commented on - P(present | unmentioned) is near
0.02. For Synovitis, which radiologists mention only when florid, it could be far
higher than 0.45.

Evidence on masking vs negative-imputation: **U-Ignore (masking) is generally
sub-optimal** - masking throws away signal. **PU learning** is the principled
middle: PU-DPO reformulates absent mentions as *unlabeled rather than negative*
and shows consistent detection-rate improvements under omission noise.

**Noise-robust training:**

| method | verdict |
|---|---|
| soft labels + standard BCE | **do this** - the fix is calibration, not the loss |
| GCE / SCE / NCE+RCE | **[Likely] poor fit** - designed for *symmetric* flips; this noise is asymmetric and instance-dependent |
| co-teaching / DISC | strongest in benchmarks, but see below; doubles training cost |
| bootstrapping / refurbishment | medium; a self-training round is cheaper |
| **two-stage weak-pretrain → gold-finetune** | **highest value/effort** - the CheXbert recipe, 0.743 → 0.798 |
| sample weighting by confidence | keep, but validate `__conf` correlates with accuracy first |

**[Likely] The key argument against co-teaching here:** small-loss selection
assumes mislabelled examples are high-loss outliers. Under systematic noise - a
regex that consistently misses one phrasing - they are a coherent sub-population
the network fits with **low** loss, so co-teaching selects them as *clean*.

**Cross-validation. [Certain]** Hashing report text is unsafe. Documented leakage:
**41% inflation** when tiles from one patient span the split; **30-55%** from
slice-level rather than subject-level CV in brain MRI. Correct grouping, in
priority order: patient identifier; near-duplicate report cluster (MinHash or
TF-IDF cosine > 0.9, then connected components); stratify by site and language;
multi-label stratification so rare positives distribute evenly.

## 3.9 Text-supervised pretraining

| method | result |
|---|---|
| ConVIRT | bidirectional image-report contrastive; improved label efficiency |
| GLoRIA | global-local alignment of regions to phrases |
| BioViL | + biomedical LM pretraining; better zero-shot |
| **MedCLIP** | **44.8% zero-shot with 20k pairs**, beating GLoRIA (43.3% with 191k) and ConVIRT (42.2% with 369k) - pairing strategy beats corpus size |
| **CheXzero** | zero-shot **statistically indistinguishable from board-certified radiologists** on 5 CheXpert pathologies |
| EchoCLR | **0.82 vs 0.61 AUROC at 1% of labels** |

**[Likely] Not worth it as the primary strategy; worth it as a cheap auxiliary
loss.** Against: ConVIRT/GLoRIA/CheXzero used 190k-370k pairs and this corpus is
~5,000 studies - 4x below even MedCLIP's careful 20k. All of them are 2D single
chest radiographs; knee MRI is multi-sequence multi-plane 3D. And you already have
a working extractor, so the marginal value is small. Opportunity cost is the real
argument: sections 3.5-3.8 contain a dozen one-line-to-one-day fixes with
measurable effect, while contrastive pretraining is a multi-week bet with no
intermediate checkpoint that tells you it is working.

**The light version, ~half a day:** add a head predicting a frozen multilingual
sentence embedding of the report (multilingual-e5 or LaBSE) alongside the 12 BCE
heads. Uses the full text signal including everything the 12 targets discard, and
ablates cleanly.

**[Certain] The deciding factor is the gold subset size.** If gold >1,500,
supervised fine-tuning alone approaches the weak-label score and pretraining is
redundant. If gold <300 you are in the 1-10% label regime where EchoCLR-type gains
appear - but even then, the auxiliary-head version, not a two-tower CLIP.

---

# Part 4 - Deep learning methods

## 4.1 Prior RSNA solutions

**[Certain] The dominant pattern across every RSNA competition with 3D
multi-series data:**

```
localise (segmentation or keypoint) -> crop -> 2.5D CNN per slice
    -> sequence model (GRU/LSTM) + pooling -> study label
```

**RSNA 2023 Abdominal Trauma, 1st (Nischaydnk)** - stage 1 3D organ segmentation →
study-level crop. Stage 2/3 2D CNN + **GRU** on 96 equidistant slices reshaped to
`(32, 3, 384, 384)` - adjacent-slice triplets as RGB, the same trick as Raptor,
but with a *recurrent* aggregator. **Soft slice labels** = study label ×
normalised organ-visibility curve from the segmentation mask, giving slice-level
supervision free from study-level labels. **Auxiliary segmentation loss**
`BCE + 0.125·Dice`, reported **+0.01 to +0.03**. Per-study aggregation by **max**.

**RSNA 2022 Cervical Spine** - uniformly multi-stage: vertebra localisation →
per-vertebra crop → 2.5D CNN → sequence aggregation. The competition-defining
insight was that a global 3D classifier cannot find a small fracture.

**RSNA 2024 Lumbar Spine, 2nd (brendanartley)** - the closest analogue (MRI,
multi-series, multi-condition, per-level). Stage 1 predicts disc **coordinates**
from 8 middle frames, ~99.1% within 5 px. Stage 2 separate T1 and T2 pipelines:
T1 = encoder → **LSTM** → attention pooling over 24 frames; T2 = variable 5-16
frames at varied sizes *for ensemble diversity*. **Pseudo-labelling + confident
learning**, loss `0.5·loss(labels) + 0.5·loss(pseudolabels)`. Manifold mixup;
left/right swapping augmentation; 9-rotation TTA. **Notable negative result:** an
axial T2 pipeline improved CV 0.01-0.02 standalone **but did not help the team
ensemble** - it was correlated with what was already there.

**RSNA Intracranial Haemorrhage 2019, 1st (SeuTao)** - titled "Sequential model
wins". 2D CNN for intra-slice features + **two sequence models** (bi-GRU/LSTM) for
inter-slice context. AUC 0.988.

**RSNA Pulmonary Embolism 2020** - for **exam-level** labels, a **concatenation of
attention-weighted average pooling and max pooling**. Direct precedent for mixed
pooling.

**RSNA Breast Cancer 2023, 1st (dangnh0611)** - YOLOX-nano 416px ROI detector →
ConvNeXt-small classifier, TensorRT engines.

## 4.2 Macro-AUC and ensembling

**(a) Rank vs logit vs power mean.** Rank averaging is conservative and
approximately right since AUC is rank-only. Nuance: **power/geometric averaging
typically beats plain rank or arithmetic averaging for AUC specifically** (it does
not for RMSE or logloss), because it lets confident members dominate the head of
the ranking. Logit averaging wins for accuracy but needs comparable calibration,
which three architecturally different families do not have. Try `mean(rank^p)`
with p ∈ {0.5, 1, 2, 3}.

**(b) Per-label blend weights.** Strong in principle - a coronal-heavy family
should dominate MCL. The danger is entirely in the fitting set:
- **On 58 gold studies: do not.** With ~2 Fracture positives the weight is noise.
- On weak-label OOF: legitimate, but you optimise against a target agreeing with
  truth only ~82%, systematically. A weight maximising weak-OOF AUC can be
  *anti*-optimal on image truth for the labels where the lexicon is most broken.
- **Mitigation: hierarchical shrinkage.** `w' = α·w_label + (1-α)·w_global` with
  α ≈ 0.3-0.5 by nested CV. And fit at the **group** level (side-specific / OA /
  effusion-family / traumatic) - 4 parameters, not 12.
- Use **bagged ensemble selection** rather than unconstrained optimisation.
  Caruana's finding: hill-climbing **overfits badly with many correlated models
  and a small validation set** - exactly this regime.

**(c) Capacity for rare labels. [Certain]** More ensemble members do *not* reduce
the estimation variance of the true AUC, only model variance. The right moves are
(i) more signal - dedicated crops, correct sequence routing, a T1 non-FS arm for
Fracture; (ii) more positive examples - pseudo-labelling, co-occurrence mining
(acute ACL → bone bruise at 0.92 gives a way to mine contusion positives); (iii)
refusing to tune on LB, since **any delta under ~0.003 macro is noise**.

**(d) AUC-specific losses. [Likely] supported but modest.** Deep AUC Maximization
(Yuan et al., ICCV 2021) reports beating cross-entropy "by a large margin" on
medical image classification. LibAUC prescribes the practical recipe: **pretrain
with BCE, then fine-tune with the AUC margin surrogate** - AUCM from scratch is
unstable. Apply per label. Helps most on rare labels, which is where the leverage is.

## 4.3 Slice and series aggregation

In MIL benchmarks, **gated attention pooling (ABMIL)** is generally best of the
classical operators on medical bags; max outperforms mean at small data and mean
catches up with more. Max/mean are ~1.7-1.8× faster.

**Three specific problems with the current head:**

1. **[Likely] Softmax normalises away evidence magnitude.** For a diffuse finding,
   the *number* of slices showing fluid is the signal, but softmax weights always
   sum to 1. A study with fluid on 30 slices and one with fluid on 2 can produce
   identical pooled features. This is actively hurting Effusion and both OA-extent
   labels.
2. **Attention concentration on rare focal findings.** With 62 windows and a small
   fracture in 2, the softmax must place nearly all mass on 2 windows; gradients
   through a saturated softmax are poor.
3. **No recurrence.** Every RSNA winner used a bi-GRU/LSTM *in addition to*
   pooling. "This bright signal persists across 4 slices, therefore it is a real
   effusion and not partial volume" is exactly what a sequence model captures.

**Per-label pooling is cheap and well-precedented.** Generalise the PE solutions'
`concat(attention-avg, max)` to a **learned per-label mixture over {mean, max,
LSE(τ), attention}** with τ learned per label. Focal (Fracture, Contusion,
menisci, Baker's) should converge toward max/LSE; diffuse (Effusion, Synovitis,
the three OA) toward mean/count. ~40 lines, and strictly more expressive than the
current head if initialised at attention-only.

Also add an **extent feature**: `mean(sigmoid(per-slice logit) > θ)` per label.

## 4.4 Cross-series fusion

1. **Learned series embeddings conditioned on metadata.** Embed
   (plane, fluid, fat-sat) and both add it to slice tokens and FiLM-condition the
   backbone's normalisation. **[Likely] worth more than it sounds** - the current
   design gives the model no explicit signal about *what it is looking at* beyond
   slot position, and a T1 non-FS coronal and a fluid-sensitive sagittal are
   radically different images.
2. **Cross-attention between series.** Fracture is the motivating case: the line
   is a T1 non-FS feature, the oedema is a fluid-sensitive feature, and the
   diagnosis is the *conjunction*. Late fusion can represent "both present
   somewhere" but not "both present at the same location".
3. **Missing slots** - practically the most important. A missing slot currently
   means a zero tensor or a duplicated substitute, both of which the model reads
   as *evidence*. **Modality dropout during training** is the cheapest reliable
   fix. Learned "missing" tokens rather than zeros. mmFormer and SMIL are the
   full-strength versions, probably too expensive here.
   **Important:** protocol availability is *not* missing-at-random - which series
   a site acquires correlates with clinical suspicion, which correlates with the
   labels. The notebook's protocol-count calibrator features exploit this. It
   probably generalises but is fragile.
4. **Registration.** Full inter-series registration is [Guessing] not worth it.
   But resampling every series onto a **common isotropic mm grid in patient
   coordinates** with sign-canonicalised normals fixes laterality in the same
   commit, makes cross-attention meaningful, and makes slice index physically
   interpretable.

## 4.5 Backbones

**[Certain] RadImageNet vs ImageNet on knee MRI** (Mei et al., Radiology:AI): ACL
tear **0.97 ± 0.03 vs 0.91 ± 0.08**; meniscal tear **0.96 ± 0.02 vs 0.92 ± 0.06**;
both p < 0.001. Caveat: the gain is largest on small datasets, and a later
comparative study found ImageNet fine-tuned beat RadImageNet in 6 of 7 datasets.
[Likely] worth one ensemble arm, not a wholesale replacement.

**[Certain] Medical Slice Transformer** (arXiv 2411.15802) - DINOv2 per slice +
transformer across slices, on 1,199 knee MRI studies for **meniscus tear**: MST
**0.85 ± 0.04** vs 3D ResNet **0.69 ± 0.05** (p = 0.001). Two conclusions: Family
A's design is the published state-of-the-art shape, and **do not build a true 3D
CNN** - that knee-MRI gap is the largest in the paper.

**[Likely] DINOv2 domain shift:** generally wins on public medical datasets
*especially frozen*, but underperforms ImageNet models on private clinical data,
with MRI called out as domain-shift-limited. Fine-tune, do not freeze.

**Practical ranking for 6 weeks:** keep CoAtNet/MaxViT at 384 as the accuracy arm;
add **ConvNeXt-small/base** (won RSNA Breast, architecturally distinct from both
DINOv2-ViT and CoAtNet, so real diversity); add **one RadImageNet arm**;
EfficientNetV2-S + GRU as the efficiency candidate. **[Guessing]** BiomedCLIP not
worth it - 2D, image-text, figure-caption tuned, and there is no test-time text.

**[Certain] SSL on the 570 GB from scratch is not realistic in 6 weeks.** What is:
**continued pretraining** - a few epochs of MAE or self-distillation on ~2M slices
to adapt patch statistics. Small, uncertain gain; do it only with slack.

## 4.6 Efficiency

**[Likely] DICOM decode is the bottleneck.** 819,640 files, mixed JPEG2000 and
JPEG Lossless. From RSNA Breast, where this was decisive: a notebook extracting
`.jp2` streams and decoding on GPU with **NVIDIA DALI reported a 17× speedup**,
and the community converged on **dicomsdl for CPU + nvJPEG2000/DALI for GPU**.
NVIDIA now ships nvImageCodec with a documented pydicom integration path.

**Recommended stack:** parse headers with dicomsdl → build the slot plan → **decode
only the slices you will use** (the biggest free win: at 64 slices from a study of
several hundred files you may be decoding 5-10× more than you consume) → GPU
decode selected frames → overlap decode with inference via a producer pool and
pinned memory.

**Model side:** **distil the ensemble into one student** - train a single
EfficientNetV2-S or ConvNeXt-tiny + GRU on the soft rank-blended outputs of the
full ensemble over the whole training set. This dovetails with the relabelling
loop - same machinery. **TensorRT FP16** is essentially free; INT8 needs
calibration and carries [Guessing] 0.001-0.005 macro risk.

## 4.7 What is structurally missing, ranked

1. **No localisation stage. [Certain, on the prior-solutions evidence]** The
   largest gap. A 384 px whole-knee slice devotes maybe 200 pixels to the ACL and
   30 to a Segond fragment.
2. **Correlated ensemble members. [Certain]** Family B and C are the same backbone
   at the same resolution on the same triplets, differing only in head. One
   Family-B arm is the same checkpoint with reversed slices - TTA, not a member.
   Ensemble variance reduction goes as `(1-ρ)/M + ρ`; at ρ ≈ 0.95 the 24-member
   Family A is worth 2-4 effective members. **The blend is already saturated.**
   The fix is representational diversity, not more members.
3. **Uniform blend weights.** Moderate gain, cheap, bounded by the weak-label proxy.
4. **Unused label correlation.** A sparse L1-regularised 12×12 coupling doing one
   message-passing step on the logits is a ~1-day intervention. Caveat: it helps
   only if test couplings match train, and the test labels are image-derived while
   the couplings would be fitted on report-derived ones.
5. **The "calibrator" is the only learned combination step** and it currently sees
   only Family A's branches. Extending it to all three families with shrinkage
   converts the entire hand-tuned blend into a fitted one.

---

# Part 5 - My own verification

Everything in `FINDINGS.md` was reproduced rather than inferred. The method: I
extracted the notebook's 27 cells to a flat file, then extracted cells 1-3 (the
lexicon) into an importable module and executed it against constructed reports.

**What I confirmed:** the `_grade_of` omission in `_score_oa` (grades 1-4 all
scoring 0.85 with wording held constant, while the meniscus path correctly jumps
at the grade-2/3 boundary); the `g_pos` accumulation bug (adding "most severe in
the patellofemoral joint" flipping two targets from 0.83 to 0.28); post-posed
negation; the un-canonicalised slice normal; the four-times decode; that Family B
arms 0 and 2 load the same checkpoint file.

**Where I corrected an agent.** The physics agent claimed `median(IPP.x)` returns
the image corner for *the* laterality path. True for the legacy
`side_from_corner_x`, but the **default** `side_from_geometry` correctly
reconstructs the image centre. Its residual weakness (knees are isocentred, so the
sign is near noise) is real but smaller, and it fails safe by returning `None`.

**Where I corrected myself.** I assumed fat suppression reduces meniscal contrast;
two arthroscopy-correlated studies say otherwise. And my first sparing rule used a
symmetric window that suppressed *both* compartments in a short clause - it has to
be forward-only, because the diseased side is named before the sparing term and
the spared side after it.

**One agent failed.** The DL agent hit a session rate limit mid-run on its first
attempt and returned nothing. Relaunched with a tool-call budget and the other
agents' findings pre-loaded so it would not re-derive them.

---

# Ruled out

Consistent across agents, with reasons:

| do not | why |
|---|---|
| true 3D CNNs | 0.85 vs 0.69 against, on knee MRI specifically |
| more members of the existing families | ρ ≈ 0.95; under 0.001 macro |
| GCE, SCE, co-teaching, small-loss selection | wrong noise model - systematic noise is fitted with *low* loss |
| global per-label recalibration or threshold tuning | AUC is invariant to monotone transforms; a no-op at best |
| chasing Synovitis past kappa 0.42-0.62 | largely irreducible on non-contrast data |
| ComBat harmonisation | needs a site label that does not exist at test time |
| MOST dataset | biobank reviews requests only in January, May, September |
| two-tower CLIP from scratch | ~5,000 studies against a 190k-370k precedent |
| tuning blend constants on the public LB | deltas under 0.003 macro are noise at 1300 studies |
| BiomedCLIP | 2D, figure-caption tuned, no test-time text |

---

# Sources

## MRI physics
Skeletal Radiology 2023 on intermediate-weighted sequences ·
Radiopaedia intermediate-weighted images ·
RadioGraphics, Articular Cartilage in the Knee: Current MR Imaging Techniques ·
MRImaster and Corsmed knee protocols · ESSR MRI Protocols - Knee ·
Skeletal Radiology 2010, PD with vs without fat suppression ·
Clinical Radiology 2026 multireader ROC, PD vs PD FS ·
AJR 1994, magic-angle phenomenon in the normal lateral meniscus ·
Skeletal Radiology 2018, "Some new angles on the magic angle" ·
Radiology 1991, truncation artefact as a meniscal pitfall ·
AJR 2014, Pitfalls and Pearls in MRI of the Knee ·
AJR, limited MRI protocols for radiographically occult hip fractures ·
RadioGraphics, Bone Contusion Patterns of the Knee ·
Radiology 1995, MCL injuries and associated bone bruises ·
Radiology 2024, fat suppression in distal extremity 3T MRI ·
MRIquestions on fat suppression, chemical shift, B0 effects on T1/T2 ·
AJR, nonspecificity of STIR · JMRI 1992, metal and ACL reconstruction ·
NeuroImage: Clinical 2014, WhiteStripe · Nyul-Udupa intensity normalisation ·
arXiv 2307.03827, intensity standardisation for multi-centre FLAIR ·
Scientific Reports 2025, ComBat caveats ·
Scientific Reports 2023, scanner manufacturer effects on DL ·
NiBabel DICOM orientation · AJR, 3T vs 1.5T meniscal tears ·
KSSTA, 1.5T vs 3T cartilage

## MSK radiology
ESSR essentials: MRI of the knee · AJR Global Reading Room: Knee MRI Protocols ·
Radiology 1993 and 1994, ACL indirect signs and anterior translocation ·
AJSM, compartmental bone bruise distribution in acute ACL tears ·
systematic review of bone bruise patterns after acute ACL tears ·
Segond fracture narrative review · deep lateral femoral notch sign ·
Radiology 2025 meta-analysis, MRI diagnosis of meniscus tears ·
AJR, posterior horn of the lateral meniscus in acute ACL injury ·
AJR, MRI accuracy for meniscal tears in older patients ·
Korean J Radiol, histological correlation of meniscal high signal ·
Skeletal Radiology, bucket-handle signs · AJR, absent bow tie sign ·
AJR 2022, meniscal root tears · Insights into Imaging, ramp lesions ·
Osteoarthritis and Cartilage: WORMS, MOAKS, BLOKS reliability,
compartmental distribution meta-analysis, anatomical distribution of synovitis ·
MOST MRI-based definition of knee OA · Outerbridge review ·
AJR, Imaging of Synovial Inflammation in Osteoarthritis ·
single axial slice vs multi-slice effusion-synovitis quantitation ·
Clinical Radiology, The Imaging Spectrum of Baker's Cysts ·
Insights into Imaging, cysts around the knee ·
Radiology 1996, Baker cysts and internal derangement ·
RadioGraphics 2018, Osteochondral Lesions of the Knee ·
Radiology 1991 and 1992, occult osteochondral lesions and fracture patterns ·
RadioGraphics, MR Imaging of Patellar Instability ·
Skeletal Radiology 2020, 230 asymptomatic knees at 3T · NEJM Framingham ·
PLOS Medicine, MRNet · ELNet arXiv 2005.02706 · MRPyrNet ·
Stanford AIMI (MRNet, SKM-TEA) · OAI at NDA · NIA Aging Research Biobank (MOST) ·
IWOAI 2019 challenge repo · DOSMA

## Report NLP
ACL W13-5635, NegEx/pyConTextNLP/SynNeg comparison · pyConTextNLP · medspaCy ·
J Imaging Inform Med 2025, medspaCy vs CAN-BERT on radiology negation ·
NegBio arXiv 1712.05898 · JMIR Med Inform 2023, negation and speculation ·
arXiv 2503.17425, assertion models · CheXbert arXiv 2004.09167 ·
VisualCheXbert arXiv 2102.11467 ·
arXiv 1905.02283, Caveats in Generating Medical Imaging Labels from Reports ·
RadGraph-XL, ACL Findings 2024 ·
Radiology 241139, commercial vs open-source LLMs for CXR report labeling ·
Healthc Inform Res 2025, in-context learning for report labeling ·
MOSAIC arXiv 2509.04471 · Apollo arXiv 2403.03640 ·
Nature Communications 2024, MMedLM · BioMistral arXiv 2402.10373 ·
arXiv 1911.06475, CheXpert uncertainty policies ·
PMC3994863, soft-label learning · Machine Learning 2025, Learning with Confidence ·
arXiv 2608.05341, PU-DPO under omission noise ·
Pattern Recognition, noisy-label benchmark · SCE loss · asymmetric losses ·
Scientific Reports 2021, data leakage in brain MRI CV ·
BI-RADS BERT section segmentation · SecTag ·
critical finding capture in the Impression · JMIR Form Res 2025 and JACR 2024,
laterality errors · Chest ImaGenome · MOAKS · modified Outerbridge MRI grading ·
Kellgren-Lawrence · Radsource, medial supporting structures ·
contrastive learning in medical AI review · EchoCLR ·
RSNA challenge announcement · AuntMinnie coverage

## Deep learning
Nischaydnk, RSNA 2023 Abdominal Trauma 1st place repo ·
pascal-pfeiffer and i-pan, RSNA 2022 Cervical Spine ·
Radiology: AI 230256, cervical spine winning-algorithm analysis ·
brendanartley, RSNA 2024 Lumbar Spine 2nd place repo ·
SeuTao, RSNA 2019 Intracranial Haemorrhage 1st place ·
i-pan and GuanshuoXu, RSNA STR Pulmonary Embolism ·
dangnh0611, RSNA Breast Cancer 1st place ·
Ilse et al., ABMIL arXiv 1802.04712 · QG-MIL arXiv 2606.20027 ·
Yuan et al., Deep AUC Maximization arXiv 2012.03173 · LibAUC docs ·
Caruana et al., ensemble selection from libraries of models ·
power/geometric ensembling for AUC ·
mmFormer arXiv 2206.02425 · SMIL, CVPR 2023 ·
Mei et al., RadImageNet, Radiology: Artificial Intelligence ·
Medical Slice Transformer arXiv 2411.15802 ·
DINOv2 comparative analysis arXiv 2402.07595 ·
Kaggle: DALI JPEG2000 decode, dicomsdl + nvJPEG2000 baselines ·
NVIDIA nvImageCodec DICOM/pydicom docs ·
label-graph refinement arXiv 2511.07801 ·
BKD for noisy CXR labels · DISTL, Nature Communications 2022 ·
ensemble distillation in medical imaging PMC9142841
