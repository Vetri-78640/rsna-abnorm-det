"""Anatomy-aware slice sampling, slot selection, and per-label plane routing.

Two defects in the public notebook are addressed.

SLICE BAND. It samples uniformly from the middle 12-88% (or 20-80%) of every
stack, identically for all twelve labels. At 30 slices that discards three to six
slices at each end -- which is where several targets actually live:

  coronal  anterior end -> patella and trochlea      (PF OA)
           posterior end -> popliteal fossa          (Baker's cyst)
  axial    superior end -> suprapatellar pouch       (Effusion)
  sagittal both ends    -> meniscal bodies, MCL, Segond

STRIDE. The intact meniscal body spans only 2-3 consecutive sagittal slices --
that is the whole basis of the absent bow-tie sign. Family A takes 8 slices from
the 0.2-0.8 band of a ~30-slice series, a stride of ~2.6, so it can see one or
zero body slices even in a normal knee, making the feature unlearnable.

INDEX CONVENTION. All fractions below assume slices already ordered and mirrored
by src/geometry.py, which yields, for BOTH knees:

  sagittal  0.0 = medial    -> 1.0 = lateral
  coronal   0.0 = anterior  -> 1.0 = posterior
  axial     0.0 = inferior  -> 1.0 = superior

The per-label bands are anatomical priors, not measurements from this dataset.
Treat them as initialisation for an empirically fitted scheme.
"""

from __future__ import annotations

import numpy as np

SAGITTAL, CORONAL, AXIAL = "Sagittal", "Coronal", "Axial"

TARGETS = ["ACL", "MCL", "Medial Meniscus", "Lateral Meniscus", "Medial OA",
           "Lateral OA", "PF OA", "Effusion", "Synovitis", "Baker's",
           "Contusion", "Fracture"]

FULL = (0.0, 1.0)

# Per-label plane weights. Sources: ESSR knee protocol recommendations, and the
# MRNet finding that the most informative plane differs per condition.
PLANE_WEIGHT = {
    "ACL":             {SAGITTAL: 1.00, CORONAL: 0.55, AXIAL: 0.45},
    "MCL":             {SAGITTAL: 0.20, CORONAL: 1.00, AXIAL: 0.40},  # coronal diagnosis
    "Medial Meniscus": {SAGITTAL: 1.00, CORONAL: 0.85, AXIAL: 0.35},
    "Lateral Meniscus": {SAGITTAL: 0.90, CORONAL: 1.00, AXIAL: 0.45},
    "Medial OA":       {SAGITTAL: 0.75, CORONAL: 1.00, AXIAL: 0.10},
    "Lateral OA":      {SAGITTAL: 0.75, CORONAL: 1.00, AXIAL: 0.10},
    "PF OA":           {SAGITTAL: 0.55, CORONAL: 0.10, AXIAL: 1.00},  # axial mandatory
    "Effusion":        {SAGITTAL: 0.70, CORONAL: 0.40, AXIAL: 1.00},
    "Synovitis":       {SAGITTAL: 0.90, CORONAL: 0.40, AXIAL: 0.80},
    "Baker's":         {SAGITTAL: 0.60, CORONAL: 0.70, AXIAL: 1.00},
    "Contusion":       {SAGITTAL: 0.90, CORONAL: 1.00, AXIAL: 0.60},
    "Fracture":        {SAGITTAL: 0.90, CORONAL: 1.00, AXIAL: 0.60},
}

# Contrast preference per label, as (fat_suppressed, fluid_sensitive) -> weight.
# Marrow oedema is water replacing fat inside a fat-dominated compartment, so
# Contusion needs fat suppression. The FRACTURE LINE, by contrast, is a dark line
# best seen against bright fatty marrow on non-fat-suppressed T1 -- which is why
# Fracture keeps real weight on the (False, False) slot.
CONTRAST_WEIGHT = {
    "ACL":             {(1, 1): 1.00, (1, 0): 0.70, (0, 1): 0.80, (0, 0): 0.60},
    "MCL":             {(1, 1): 1.00, (1, 0): 0.70, (0, 1): 0.55, (0, 0): 0.35},
    "Medial Meniscus": {(1, 1): 0.95, (1, 0): 0.85, (0, 1): 0.95, (0, 0): 1.00},
    "Lateral Meniscus": {(1, 1): 1.00, (1, 0): 0.85, (0, 1): 0.90, (0, 0): 0.85},
    "Medial OA":       {(1, 1): 1.00, (1, 0): 0.80, (0, 1): 0.70, (0, 0): 0.65},
    "Lateral OA":      {(1, 1): 1.00, (1, 0): 0.80, (0, 1): 0.70, (0, 0): 0.65},
    "PF OA":           {(1, 1): 1.00, (1, 0): 0.80, (0, 1): 0.70, (0, 0): 0.65},
    "Effusion":        {(1, 1): 1.00, (1, 0): 0.60, (0, 1): 0.90, (0, 0): 0.40},
    "Synovitis":       {(1, 1): 1.00, (1, 0): 0.55, (0, 1): 0.60, (0, 0): 0.25},
    "Baker's":         {(1, 1): 1.00, (1, 0): 0.60, (0, 1): 0.95, (0, 0): 0.50},
    "Contusion":       {(1, 1): 1.00, (1, 0): 0.50, (0, 1): 0.45, (0, 0): 0.20},
    "Fracture":        {(1, 1): 0.90, (1, 0): 0.60, (0, 1): 0.60, (0, 0): 0.85},
}

# Where each finding sits through the stack, in the index convention above.
LABEL_BANDS = {
    SAGITTAL: {
        "MCL": (0.00, 0.22), "Medial Meniscus": (0.02, 0.38),
        "Medial OA": (0.02, 0.38), "ACL": (0.48, 0.80),
        "Lateral Meniscus": (0.62, 0.98), "Lateral OA": (0.62, 0.98),
        "PF OA": (0.28, 0.72), "Effusion": (0.20, 0.80),
        "Synovitis": (0.28, 0.72), "Baker's": (0.02, 0.40),
        "Contusion": FULL, "Fracture": FULL,
    },
    CORONAL: {
        "PF OA": (0.00, 0.32), "Synovitis": (0.00, 0.35),
        "Baker's": (0.72, 1.00), "Medial Meniscus": (0.28, 0.92),
        "Lateral Meniscus": (0.28, 0.92), "ACL": (0.45, 0.88),
        "MCL": (0.20, 0.68), "Medial OA": (0.22, 0.82),
        "Lateral OA": (0.22, 0.82), "Effusion": FULL,
        "Contusion": FULL, "Fracture": FULL,
    },
    AXIAL: {
        "Effusion": (0.62, 1.00),   # suprapatellar pouch, superior end
        "PF OA": (0.52, 0.92),      # patella level
        "Synovitis": (0.50, 1.00),
        "Baker's": (0.05, 0.58),
        "MCL": (0.20, 0.70), "ACL": (0.35, 0.70),
        "Medial Meniscus": (0.30, 0.60), "Lateral Meniscus": (0.30, 0.60),
        "Medial OA": (0.25, 0.65), "Lateral OA": (0.25, 0.65),
        "Contusion": FULL, "Fracture": FULL,
    },
}


def sample_indices(n_slices, k, band=FULL, keep_ends=True, n_end=2):
    """Pick k slice indices from a stack of n_slices.

    `keep_ends` forces the first and last n_end slices into the sample even when
    a narrow band is requested. That is the safety net against the notebook's
    systematic loss of the suprapatellar pouch, popliteal fossa and patella.
    Returns a sorted array of length exactly k (with repeats if n_slices < k).
    """
    if n_slices <= 0 or k <= 0:
        return np.zeros(0, dtype=int)
    if n_slices == 1:
        return np.zeros(k, dtype=int)

    lo = int(round(band[0] * (n_slices - 1)))
    hi = int(round(band[1] * (n_slices - 1)))
    lo, hi = max(0, min(lo, n_slices - 1)), max(0, min(hi, n_slices - 1))
    if hi <= lo:
        lo, hi = 0, n_slices - 1

    forced = []
    if keep_ends and n_slices >= 2 * n_end:
        e = min(n_end, max(1, k // 4))
        forced = list(range(e)) + list(range(n_slices - e, n_slices))
        forced = [i for i in forced if not lo <= i <= hi]

    n_main = max(1, k - len(forced))
    main = np.linspace(lo, hi, n_main)
    idx = np.unique(np.concatenate([np.asarray(forced, dtype=float), main]))
    idx = np.clip(np.round(idx).astype(int), 0, n_slices - 1)
    idx = np.unique(idx)

    # top up toward the densest part of the band if uniqueness lost slices
    while idx.size < k:
        pool = np.setdiff1d(np.arange(lo, hi + 1), idx)
        if pool.size == 0:
            idx = np.concatenate([idx, np.full(k - idx.size, idx[-1])])
            break
        take = pool[np.linspace(0, pool.size - 1,
                                min(k - idx.size, pool.size)).round().astype(int)]
        idx = np.unique(np.concatenate([idx, take]))
    if idx.size > k:
        idx = idx[np.linspace(0, idx.size - 1, k).round().astype(int)]
    return np.sort(idx)[:k]


def label_band(label, plane):
    return LABEL_BANDS.get(plane, {}).get(label, FULL)


# MEASURED: in the organisers' metadata, Fat_Suppression == Fluid_Sensitive for
# all 24,371 train series and all 15 test series. Off-diagonal count is zero. So
# only the (1, 1) and (0, 0) cells of the 2x2 are reachable from the CSVs, and
# the notebook's 6-slot key loses nothing at all.
#
# The physics below is still right -- the two ARE independent axes, and a coronal
# T2 FSE without fat-sat is fluid-sensitive and is being filed as "structural" by
# everyone in this competition. But recovering that needs TE/TI from the DICOM
# headers, which is what sequence_typing.py is for. Until something feeds it,
# `full=True` describes a grid this dataset cannot populate.
OBSERVED_CONTRASTS = ((1, 1), (0, 0))
FULL_CONTRASTS = ((1, 1), (1, 0), (0, 1), (0, 0))


def slot_grid(planes=(SAGITTAL, CORONAL, AXIAL), full=False):
    """Per-plane contrast slots.

    Default is the six cells the organisers' metadata can actually fill. Pass
    full=True for the 2x2 (fat-sat x fluid-sensitive), which needs a fluid
    -sensitivity signal recovered from TE rather than read from the CSV: T1
    fat-sat post-contrast is (1, 0); non-fat-sat T2 FSE is (0, 1); Dixon emits
    (1, x) and (0, x) from one acquisition.
    """
    contrasts = FULL_CONTRASTS if full else OBSERVED_CONTRASTS
    return [(p, fs, fl) for p in planes for fs, fl in contrasts]


def pick_series(candidates, plane, fat_sat, fluid, spacing_key="spacing_mm"):
    """Choose one series for a slot.

    Tie-breaks on through-plane spacing (thinner is better -- less partial-volume
    averaging), not on slice count. The notebook's "most slices wins" rule is a
    proxy for coverage, not quality: a 45-slice series may simply span more
    anatomy at coarser spacing.
    """
    sel = [c for c in candidates
           if c.get("plane") == plane
           and int(bool(c.get("fat_sat"))) == fat_sat
           and int(bool(c.get("fluid_sensitive"))) == fluid]
    if not sel:
        return None

    def rank(c):
        sp = c.get(spacing_key)
        sp = sp if (sp and sp > 0) else 99.0
        cov = c.get("coverage_mm") or 0.0
        fail = c.get("fatsat_fail_ratio") or 0.0
        return (fail > 1.2, sp, -cov, -(c.get("n_slices") or 0))

    return sorted(sel, key=rank)[0]


def build_slot_plan(candidates, budget=64, planes=(SAGITTAL, CORONAL, AXIAL),
                    full=False):
    """Allocate a per-study slice budget across available slots.

    Weights every slot by how much total per-label evidence it can carry, so a
    study missing its axial series spends that budget elsewhere instead of
    padding zeros. Returns [(series, plane, fat_sat, fluid, n_slices)].
    """
    chosen = []
    for plane, fs, fl in slot_grid(planes, full=full):
        s = pick_series(candidates, plane, fs, fl)
        if s is not None and s not in [c[0] for c in chosen]:
            score = sum(PLANE_WEIGHT[t][plane] * CONTRAST_WEIGHT[t][(fs, fl)]
                        for t in TARGETS)
            chosen.append((s, plane, fs, fl, score))
    if not chosen:
        return []
    total = sum(c[4] for c in chosen)
    plan = []
    for s, plane, fs, fl, score in chosen:
        n = max(4, int(round(budget * score / total)))
        plan.append((s, plane, fs, fl, n))
    return plan


def routing_matrix(full=False):
    """12 x (plane, fat_sat, fluid) prior weights, for initialising a learned
    per-label slot-attention head rather than hard-coding the routing.

    Defaults to the six observed slots. With full=True six of the twelve columns
    are permanently zero for this dataset -- see slot_grid."""
    slots = slot_grid(full=full)
    m = np.zeros((len(TARGETS), len(slots)), dtype=np.float32)
    for i, t in enumerate(TARGETS):
        for j, (plane, fs, fl) in enumerate(slots):
            m[i, j] = PLANE_WEIGHT[t][plane] * CONTRAST_WEIGHT[t][(fs, fl)]
    m /= m.sum(axis=1, keepdims=True)
    return m, slots
