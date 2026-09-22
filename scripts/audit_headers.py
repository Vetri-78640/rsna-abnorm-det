#!/usr/bin/env python3
"""DICOM header audit. Answers the geometry questions the metadata CSVs cannot.

  1. WHICH OF THE 86 ALLOWLISTED TAGS SURVIVED. Several recommendations branch on
     this. InversionTime, MagneticFieldStrength, SpacingBetweenSlices,
     AcquisitionMatrix, PixelBandwidth, ImageLaterality and PatientPosition are
     each a free physics feature if present.
  2. HOW OFTEN LATERALITY IS UNRESOLVED. The public notebook falls back to the
     sign of a geometric x coordinate when the Laterality tag is missing. Since
     knees are positioned at isocentre that sign is close to noise, and for
     coronal and axial series the legacy variant reads the image CORNER, which is
     roughly -FOV/2 for every study. This audit measures how often that fallback
     actually fires.
  3. HOW OFTEN THE RAW SLICE NORMAL POINTS THE WRONG WAY. This is the defect that
     silently swaps Medial/Lateral Meniscus and Medial/Lateral OA. If the sign of
     cross(IOP) varies across the dataset, canonicalisation is mandatory.
  4. Slice spacing and coverage, recovered from ImagePositionPatient because
     SliceThickness may not be in the allowlist.

Reads one slice per series, so it is I/O-light -- but it does need the DICOMs.

Usage:  python3 scripts/audit_headers.py <series_root> [--limit N]
"""
from __future__ import annotations

import argparse
import os
import pathlib
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import geometry as g  # noqa: E402

WANTED = [
    "SeriesDescription", "SequenceName", "ProtocolName", "ScanOptions",
    "ScanningSequence", "SequenceVariant", "MRAcquisitionType",
    "RepetitionTime", "EchoTime", "InversionTime", "FlipAngle",
    "MagneticFieldStrength", "PixelBandwidth", "NumberOfAverages",
    "SliceThickness", "SpacingBetweenSlices", "PixelSpacing", "Rows", "Columns",
    "AcquisitionMatrix", "InPlanePhaseEncodingDirection", "PercentPhaseFieldOfView",
    "Laterality", "ImageLaterality", "BodyPartExamined", "PatientPosition",
    "Manufacturer", "ManufacturerModelName", "PhotometricInterpretation",
    "RescaleSlope", "RescaleIntercept", "ImagePositionPatient",
    "ImageOrientationPatient", "InstanceNumber", "SliceLocation",
    "PatientID", "PatientSex", "PatientAge", "StudyDate", "InstitutionName",
]


def probe(series_dir):
    try:
        import pydicom
    except ImportError:
        raise SystemExit("pydicom required: pip install pydicom")
    files = sorted(f for f in os.listdir(series_dir) if f.endswith(".dcm"))
    if not files:
        return None
    out = {"dir": str(series_dir), "n_files": len(files)}
    try:
        ds = pydicom.dcmread(os.path.join(series_dir, files[len(files) // 2]),
                             stop_before_pixels=True, force=True)
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
        return out
    for t in WANTED:
        v = getattr(ds, t, None)
        if v is None:
            continue
        out[t] = ("|".join(str(x) for x in v)
                  if isinstance(v, (list, tuple)) or type(v).__name__ == "MultiValue"
                  else str(v))
    # per-slice positions, capped, for spacing and normal-sign statistics
    recs = []
    for f in files[:64]:
        try:
            s = pydicom.dcmread(os.path.join(series_dir, f), stop_before_pixels=True,
                                force=True, specific_tags=["ImagePositionPatient",
                                                           "ImageOrientationPatient",
                                                           "InstanceNumber"])
            recs.append({"iop": getattr(s, "ImageOrientationPatient", None),
                         "ipp": getattr(s, "ImagePositionPatient", None),
                         "instance": getattr(s, "InstanceNumber", None),
                         "name": f})
        except Exception:
            recs.append({"iop": None, "ipp": None, "instance": None, "name": f})
    out["_recs"] = recs
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("series_root")
    ap.add_argument("--limit", type=int, default=400,
                    help="studies to sample; the audit is statistical, not exhaustive")
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()

    root = pathlib.Path(a.series_root)
    if not root.is_dir():
        print(f"not a directory: {root}")
        return 1

    studies = sorted(p for p in root.iterdir() if p.is_dir())[:a.limit]
    jobs = [s for st in studies for s in sorted(st.iterdir()) if s.is_dir()]
    print(f"probing {len(jobs)} series across {len(studies)} studies\n")

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        rows = [r for r in pool.map(probe, jobs) if r]

    # ---- 1. tag survival ---------------------------------------------------
    print("=== tag availability (of the 86-tag allowlist) ===")
    counts = Counter(k for r in rows for k in r if k in WANTED)
    for t in WANTED:
        c = counts.get(t, 0)
        flag = "" if c else "   <-- ABSENT"
        print(f"  {t:<32}{c:>6}/{len(rows)}  {100 * c / max(len(rows), 1):>5.1f}%{flag}")
    print()

    # ---- 2. slice-normal sign ---------------------------------------------
    print("=== raw slice-normal sign, by plane ===")
    print("(if both signs appear for a plane, the notebook's uncased sort runs")
    print(" medial->lateral on some studies and lateral->medial on others)")
    signs = defaultdict(Counter)
    for r in rows:
        iop = g.as_vec(r.get("ImageOrientationPatient"), 6)
        if iop is None:
            continue
        plane = g.plane_of(iop)
        if plane is None:
            continue
        n = np.cross(iop[0:3], iop[3:6])
        axis = {"Sagittal": 0, "Coronal": 1, "Axial": 2}[plane]
        signs[plane]["+" if n[axis] > 0 else "-"] += 1
    for plane, c in signs.items():
        tot = sum(c.values())
        minority = min(c.values()) if len(c) > 1 else 0
        verdict = (f"BOTH SIGNS PRESENT -- {minority} series ({100*minority/tot:.1f}%) "
                   f"would sort backwards" if len(c) > 1 else "single sign, consistent")
        print(f"  {plane:<10} +:{c['+']:>6}  -:{c['-']:>6}   {verdict}")
    print()

    # ---- 3. laterality -----------------------------------------------------
    print("=== laterality resolution ===")
    by_study = defaultdict(list)
    for r in rows:
        by_study[pathlib.Path(r["dir"]).parent.name].append(r)
    how = Counter()
    for st, rs in by_study.items():
        _, method = g.study_laterality(rs)
        how[method] += 1
    for k, v in how.most_common():
        print(f"  {k:<12}{v:>6}  {100 * v / max(len(by_study), 1):>5.1f}%")
    if how["unresolved"]:
        print(f"\n  ** {how['unresolved']} studies have no laterality tag. The")
        print("     notebook guesses from a geometric x sign here. Since knees sit")
        print("     at isocentre that sign is near noise, and a wrong guess mirrors")
        print("     4 of the 12 targets. Train a fibula-based classifier on the")
        print(f"     {how['tag']} tagged studies and apply it to these instead.")
    print()

    # ---- 4. plane agreement and geometry ----------------------------------
    print("=== through-plane geometry (from ImagePositionPatient) ===")
    sp, cov, order_method = [], [], Counter()
    for r in rows:
        recs = r.get("_recs") or []
        if not recs:
            continue
        m = g.slice_metrics(recs)
        if m["spacing_mm"]:
            sp.append(m["spacing_mm"])
        if m["coverage_mm"]:
            cov.append(m["coverage_mm"])
        order_method[g.order_slices(recs)[1]] += 1
    if sp:
        print(f"  spacing mm   median {np.median(sp):.2f}  "
              f"p10 {np.percentile(sp, 10):.2f}  p90 {np.percentile(sp, 90):.2f}")
    if cov:
        print(f"  coverage mm  median {np.median(cov):.1f}  "
              f"p10 {np.percentile(cov, 10):.1f}  p90 {np.percentile(cov, 90):.1f}")
        thin = int(sum(1 for c in cov if c < 70))
        if thin:
            print(f"  {thin} series cover under 70 mm -- likely truncated, "
                  f"deprioritise in slot selection")
    print(f"  slice ordering resolved by: {dict(order_method)}")
    print()

    print("=== in-plane geometry ===")
    px = [float(g.as_vec(r["PixelSpacing"], 2)[0]) for r in rows
          if r.get("PixelSpacing") and g.as_vec(r["PixelSpacing"], 2) is not None]
    if px:
        print(f"  pixel spacing mm  median {np.median(px):.3f}  "
              f"p10 {np.percentile(px, 10):.3f}  p90 {np.percentile(px, 90):.3f}")
        fov = [p * 320 for p in px]
        print(f"  implied FOV at 320 px  median {np.median(fov):.0f} mm")
        print("  (the notebook centre-crops to 130 mm; if median FOV is near 140")
        print("   that crop is nearly a no-op, and on sagittal it may clip the")
        print("   patella anteriorly or the popliteal fossa posteriorly)")
    aniso = 0
    for r in rows:
        v = g.as_vec(r.get("PixelSpacing"), 2)
        if v is not None and abs(v[0] - v[1]) > 1e-3:
            aniso += 1
    print(f"  anisotropic pixels: {aniso} series "
          f"(these are where PixelSpacing[0] vs [1] actually matters)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
