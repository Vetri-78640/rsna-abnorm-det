"""MRI sequence typing from DICOM headers, and continuous conditioning features.

Fixes three defects in the public notebook's `annotate()`:

1. GRE was tested LAST, so a 2D T2*/MEDIC at TR 800-1200 passed the `TR >= 800`
   rule and was typed PD. ScanningSequence must be checked first.
2. Inversion recovery was never a class. STIR at TE 110 typed as T2, STIR at
   TE 40 typed as PD -- the same clinical sequence split across two buckets.
3. Intermediate-weighted (TE 30-40 ms) was collapsed into PD. IW FSE is the
   workhorse of modern knee protocols and is physically much closer to T2 than
   to a TE-12 PD. It also carries less magic-angle artefact, which is exactly
   why it is preferred for menisci.

The discrete class is kept only for slot selection. For the model, prefer
`conditioning_features()` -- feeding log TR / log TE / TI / flags directly makes
the boundary question moot and lets the network learn the contrast manifold.
"""

from __future__ import annotations

import math
import re

T1, PD, IW, T2, GRE, IR, UNK = "T1", "PD", "IW", "T2", "GRE", "IR", "UNK"

_SEP = re.compile(r"[_\-.]")

_FATSAT = re.compile(
    r"\bfs\b|fatsat|fat sat|\bstir\b|\bspair\b|\bspir\b|\bwe\b|water excit"
    r"|\btirm\b|\bfatsup\b|\bchess\b|\bsping\b|\bfs2d|\bfsat\b"
    # bare "dixon" must NOT imply fat suppression: the in-phase image of a Dixon
    # pair is not fat suppressed, and that contrast is the point of the pairing
    r"|dixon[ _]?w\b|water only|\bwfs\b|dixon[^|]*water")
_IR = re.compile(r"\bstir\b|\btirm\b|\bir\b|\bflair\b|inversion")
_DIXON = re.compile(r"dixon|\bwfs\b|water only|\bw only\b|\bin phase\b|\bopp\b")
_T1 = re.compile(r"\bt1\b|\bt1w\b|\bt1_|t1_tse|t1w_")
_T2 = re.compile(r"\bt2\b|\bt2w\b|\bt2_")
_PD = re.compile(r"\bpd\b|\bpdw\b|proton|\bdp\b|\bdens|\bdp_\b")
_GRE = re.compile(r"\bmedic\b|\bdess\b|\bgre\b|\bflash\b|\bfisp\b|\bfspgr\b"
                  r"|\bspgr\b|\bmerge\b|\bt2star\b|\bt2\*")
_METAL = re.compile(r"\bmars\b|\bwarp\b|\bsemac\b|\bmavric\b|metal")
_POSTOP = re.compile(r"post ?op|postoperat|\bgraft\b|reconstruct|\bplasti\b"
                     r"|meniscectom|arthroplast|\bprotez\b")

FATSAT_OPTS = {"FS", "FATSAT", "FAT_SAT", "FSAT", "SFS", "FSAT_GEMS"}


def _num(v):
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _desc(row):
    parts = [str(row.get(k) or "") for k in
             ("SeriesDescription", "SequenceName", "ProtocolName", "ScanOptions")]
    return _SEP.sub(" ", " ".join(parts).lower())


def is_fat_suppressed(row):
    """Fat suppression from the description plus ScanOptions.

    Note this is orthogonal to fluid sensitivity: they are produced by different
    physics (TE/TI sets fluid weighting; a separate preparation module removes
    fat). A single 2-point Dixon acquisition yields water-only and in-phase
    images with IDENTICAL TR/TE differing only in fat suppression, so no TR/TE
    rule can ever separate them.
    """
    if _FATSAT.search(_desc(row)):
        return True
    opts = str(row.get("ScanOptions") or "").upper()
    return any(t.strip() in FATSAT_OPTS for t in re.split(r"[|\\,]", opts))


def sequence_class(row):
    """Weighting class. Order matters: GRE and IR are checked before TR/TE."""
    desc = _desc(row)
    scanseq = str(row.get("ScanningSequence") or "").upper()
    tr, te, ti = _num(row.get("RepetitionTime")), _num(row.get("EchoTime")), \
        _num(row.get("InversionTime"))

    # 1. gradient echo, before any TR/TE rule can misclaim it
    if "GR" in scanseq or _GRE.search(desc):
        return GRE
    # 2. inversion recovery, its own class -- STIR nulls by T1, not by frequency,
    #    so it also darkens mucoid, haemorrhagic and enhancing tissue
    if "IR" in scanseq or _IR.search(desc) or (ti is not None and ti > 0):
        return IR
    # 3. explicit description
    if _T1.search(desc) and not _T2.search(desc) and not _PD.search(desc):
        return T1
    if _PD.search(desc):
        return IW if (te is not None and te >= 30) else PD
    if _T2.search(desc):
        return T2
    # 4. TR/TE fallback. T1 TR is driven by slice count in 2D multi-slice and
    #    tissue T1 lengthens with field strength, so 800 was far too tight.
    if te is not None:
        if te >= 60:
            return T2
        if te >= 30:
            return IW
        if tr is not None and tr <= 1100:
            return T1
        return PD
    if tr is not None:
        return T1 if tr <= 1100 else PD
    return UNK


def is_fluid_sensitive(row, cls=None):
    """Long TE or an inversion-recovery null makes free water the brightest thing."""
    cls = cls or sequence_class(row)
    if cls in (T2, IW, IR):
        return True
    if cls == PD:
        te = _num(row.get("EchoTime"))
        return te is not None and te >= 25
    return False


def conditioning_features(row):
    """Continuous vector for the model, instead of a hard class.

    Removes the intermediate-weighted collapse and the GRE ordering bug in one
    move: the network sees the actual acquisition parameters and can learn where
    the boundaries are.
    """
    tr, te = _num(row.get("RepetitionTime")), _num(row.get("EchoTime"))
    ti, fa = _num(row.get("InversionTime")), _num(row.get("FlipAngle"))
    cls = sequence_class(row)
    desc = _desc(row)
    return {
        "log_tr": math.log1p(tr) if tr else 0.0,
        "log_te": math.log1p(te) if te else 0.0,
        "log_ti": math.log1p(ti) if ti else 0.0,
        "flip_angle": (fa or 0.0) / 90.0,
        "has_tr": float(tr is not None),
        "has_te": float(te is not None),
        "fat_sat": float(is_fat_suppressed(row)),
        "fluid_sensitive": float(is_fluid_sensitive(row, cls)),
        "is_ir": float(cls == IR),
        "is_gre": float(cls == GRE),
        "is_dixon": float(bool(_DIXON.search(desc))),
        # short TE drives the magic-angle false positive in the normal posterior
        # horn of the lateral meniscus; it disappears above roughly TE 37 ms
        "magic_angle_risk": float(te is not None and te < 37 and cls != IR),
        "metal_suppression": float(bool(_METAL.search(desc))),
        "post_op": float(bool(_POSTOP.search(desc))),
    }


def find_dixon_pairs(series_rows, tr_tol=0.05, te_tol=2.0):
    """Two series from one Dixon acquisition: same plane and geometry, same
    TR/TE, opposite fat suppression. Free 'with and without fat' registration.
    """
    pairs, rows = [], list(series_rows)
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            if a.get("Anatomical_Plane") != b.get("Anatomical_Plane"):
                continue
            if is_fat_suppressed(a) == is_fat_suppressed(b):
                continue
            tra, trb = _num(a.get("RepetitionTime")), _num(b.get("RepetitionTime"))
            tea, teb = _num(a.get("EchoTime")), _num(b.get("EchoTime"))
            if None in (tra, trb, tea, teb) or tra <= 0:
                continue
            if abs(tra - trb) / tra <= tr_tol and abs(tea - teb) <= te_tol:
                pairs.append((a.get("SeriesInstanceUID"), b.get("SeriesInstanceUID")))
    return pairs


def annotate(df):
    """Vectorised wrapper for a pandas series-level table."""
    rows = df.to_dict("records")
    df = df.copy()
    df["seq_class"] = [sequence_class(r) for r in rows]
    df["fatsat"] = [is_fat_suppressed(r) for r in rows]
    df["fluid"] = [is_fluid_sensitive(r, c) for r, c in zip(rows, df["seq_class"])]
    feats = [conditioning_features(r) for r in rows]
    for k in feats[0]:
        df[f"f_{k}"] = [f[k] for f in feats]
    return df
