"""DICOM geometry for knee MRI: canonical slice ordering, laterality, physical spacing.

Fixes the defect in the public 0.939 notebook where the slice normal
`cross(IOP[:3], IOP[3:])` is used unsigned. That cross product's sign is chosen by
the vendor, so an ascending sort runs medial->lateral on some studies and
lateral->medial on others, silently swapping Medial/Lateral Meniscus and
Medial/Lateral OA -- four of the twelve targets.

DICOM patient coordinates are LPS: +x patient left, +y posterior, +z superior.
LPS is patient-relative and already absorbs PatientPosition, so head-first vs
feet-first and prone vs supine need no special handling.

  IOP[0:3]  unit vector along increasing COLUMN index (image left -> right)
  IOP[3:6]  unit vector along increasing ROW index    (image top  -> bottom)
  IPP       LPS coords of the centre of the top-left pixel of the slice
  PixelSpacing = [row_spacing, col_spacing] = [vertical, horizontal]
"""

from __future__ import annotations

import numpy as np

SAGITTAL, CORONAL, AXIAL = "Sagittal", "Coronal", "Axial"

# canonical positive normal per plane, in LPS
_AXIS = {SAGITTAL: np.array([1.0, 0, 0]),
         CORONAL: np.array([0, 1.0, 0]),
         AXIAL: np.array([0, 0, 1.0])}

# after canonicalisation, ascending sort by (IPP . n) runs:
#   sagittal  patient right -> patient left
#   coronal   anterior      -> posterior
#   axial     inferior      -> superior
_ORDER = {SAGITTAL: "right_to_left", CORONAL: "ant_to_post", AXIAL: "inf_to_sup"}

# in-plane targets: which LPS axis we want pointing image-right / image-down
_H_TARGET = {SAGITTAL: np.array([0, 1.0, 0]),   # posterior to the image right
             CORONAL: np.array([1.0, 0, 0]),    # patient left to the image right
             AXIAL: np.array([1.0, 0, 0])}
_V_TARGET = {SAGITTAL: np.array([0, 0, -1.0]),  # superior at the image top
             CORONAL: np.array([0, 0, -1.0]),
             AXIAL: np.array([0, 1.0, 0])}      # anterior at the image top


def as_vec(value, n):
    """Parse a DICOM multi-value into a float array, or None if unusable."""
    if value is None:
        return None
    if isinstance(value, str):
        parts = value.replace("\\", "|").split("|")
    else:
        try:
            parts = list(value)
        except TypeError:
            return None
    try:
        v = np.asarray([float(x) for x in parts], dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if v.size < n or not np.isfinite(v[:n]).all():
        return None
    return v[:n]


def plane_of(iop):
    """Imaging plane from the direction cosines. Handles oblique prescriptions:
    knee obliques are always well under 45 degrees, so argmax is safe."""
    iop = as_vec(iop, 6)
    if iop is None:
        return None
    n = np.cross(iop[0:3], iop[3:6])
    if not np.isfinite(n).all() or np.allclose(n, 0):
        return None
    return (SAGITTAL, CORONAL, AXIAL)[int(np.argmax(np.abs(n)))]


def canonical_normal(iop, plane=None):
    """Unit slice normal with a deterministic sign.

    This is the fix. `cross(row, col)` alone flips with the vendor's choice of
    row/column direction; forcing a positive projection onto the plane's
    canonical LPS axis makes the ordering reproducible across vendors.
    """
    iop = as_vec(iop, 6)
    if iop is None:
        return None, None
    n = np.cross(iop[0:3], iop[3:6])
    norm = np.linalg.norm(n)
    if norm < 1e-6:
        return None, None
    n = n / norm
    plane = plane or (SAGITTAL, CORONAL, AXIAL)[int(np.argmax(np.abs(n)))]
    s = float(np.dot(n, _AXIS[plane]))
    if s < 0:
        n = -n
    return n, plane


def slice_key(iop, ipp, plane=None):
    """Signed position of a slice along the canonical normal, in mm."""
    n, plane = canonical_normal(iop, plane)
    ipp = as_vec(ipp, 3)
    if n is None or ipp is None:
        return None
    return float(np.dot(ipp, n))


def order_slices(records, plane=None):
    """Sort slice records into canonical anatomical order.

    `records` is a sequence of dicts with keys 'iop', 'ipp' and optionally
    'instance' and 'name'. Returns (ordered_records, method) where method is
    'geometry' | 'instance' | 'name' so callers can log how far they fell back.
    """
    keyed, n_geom = [], 0
    for pos, r in enumerate(records):
        k = slice_key(r.get("iop"), r.get("ipp"), plane)
        if k is not None:
            n_geom += 1
        keyed.append((k, r.get("instance"), pos, r))

    if n_geom >= max(2, int(0.8 * len(keyed))):
        spare = float(np.median([k for k, *_ in keyed if k is not None]))
        keyed.sort(key=lambda t: (t[0] if t[0] is not None else spare,
                                  t[1] if t[1] is not None else np.inf, t[2]))
        return [t[3] for t in keyed], "geometry"

    if sum(t[1] is not None for t in keyed) >= max(2, int(0.8 * len(keyed))):
        keyed.sort(key=lambda t: (t[1] if t[1] is not None else np.inf, t[2]))
        return [t[3] for t in keyed], "instance"

    keyed.sort(key=lambda t: _natural_key(str(t[3].get("name", t[2]))))
    return [t[3] for t in keyed], "name"


def _natural_key(name):
    import re
    return tuple(int(p) if p.isdigit() else p.lower()
                 for p in re.split(r"(\d+)", name))


def slice_metrics(records, plane=None):
    """Through-plane geometry recovered from IPP, since SliceThickness and
    SpacingBetweenSlices are not in the competition's 86-tag allowlist.

    Returns spacing_mm (thickness + gap, which is what matters for resampling
    and partial-volume reasoning) and coverage_mm (total extent). A sagittal
    series covering only 60 mm did not cover the whole knee.
    """
    ks = sorted(k for k in (slice_key(r.get("iop"), r.get("ipp"), plane)
                            for r in records) if k is not None)
    if len(ks) < 2:
        return {"spacing_mm": None, "coverage_mm": None, "n_positioned": len(ks)}
    d = np.diff(ks)
    d = d[d > 1e-6]
    return {"spacing_mm": float(np.median(d)) if d.size else None,
            "coverage_mm": float(ks[-1] - ks[0]),
            "n_positioned": len(ks)}


def image_centre(iop, ipp, rows, cols, pixel_spacing):
    """LPS coordinates of the centre of the image plane.

    IPP is the top-left PIXEL CENTRE, so the half-extent uses (n-1)/2, not n/2.
    PixelSpacing is [row, col] = [vertical, horizontal], so the column direction
    IOP[0:3] pairs with PixelSpacing[1].
    """
    iop, ipp = as_vec(iop, 6), as_vec(ipp, 3)
    ps = as_vec(pixel_spacing, 2)
    if iop is None or ipp is None or ps is None or not rows or not cols:
        return None
    return (ipp
            + iop[0:3] * ps[1] * (float(cols) - 1) / 2.0
            + iop[3:6] * ps[0] * (float(rows) - 1) / 2.0)


def in_plane_flips(iop, plane=None):
    """Flips needed to bring a slice into canonical display orientation.

    Derived from the direction cosines rather than assumed, so vendor and
    prescription differences are handled. Returns (flip_h, flip_v).
    """
    iop = as_vec(iop, 6)
    if iop is None:
        return False, False
    plane = plane or plane_of(iop)
    if plane is None:
        return False, False
    return (float(np.dot(iop[0:3], _H_TARGET[plane])) < 0,
            float(np.dot(iop[3:6], _V_TARGET[plane])) < 0)


def laterality_flips(plane, side):
    """Mirror a right knee onto the left knee's convention so that medial always
    lands on the same image side and sagittal stacks always run medial->lateral.

    Left knee sits at +x; its medial aspect faces the midline (-x), so a canonical
    ascending sort already runs medial->lateral. A right knee sits at -x with
    medial facing +x, so its slice order must be reversed.
    """
    if side not in ("L", "R"):
        return False, False
    right = side == "R"
    if plane == SAGITTAL:
        return False, right          # (flip_h, reverse_slice_order)
    return right, False               # coronal / axial: mirror horizontally


def study_laterality(series_rows):
    """Resolve L/R for a study.

    Prefers the Laterality / ImageLaterality tags and propagates by study-level
    consensus, because every series in a knee study images the same knee.

    Deliberately does NOT fall back to sign(IPP.x). For coronal and axial series
    IPP.x is the image CORNER, roughly -FOV/2 for every study, so its sign is
    near-constant and carries no laterality information. Even on sagittal the
    knee is positioned at isocentre, so centre-x hovers around zero and its sign
    is close to noise. Unresolved returns None; the caller should leave the study
    unmirrored rather than guess, and ideally resolve it with a learned
    fibula-based classifier trained on the studies where the tag is present.
    """
    votes = []
    for r in series_rows:
        for key in ("Laterality", "ImageLaterality"):
            v = r.get(key)
            if v is None:
                continue
            v = str(v).strip().upper()
            if v[:1] in ("L", "R"):
                votes.append(v[0])
    if not votes:
        return None, "unresolved"
    left, right = votes.count("L"), votes.count("R")
    if left and right:
        return ("L" if left > right else "R" if right > left else None), "conflict"
    return ("L" if left else "R"), "tag"


def plane_agreement(iop, declared_plane):
    """Compare the IOP-derived plane with the organiser's Anatomical_Plane.

    A disagreement usually marks an oblique prescription, which in knee MRI most
    often means a dedicated high-resolution ACL series -- a strong slot to keep.
    """
    derived = plane_of(iop)
    if derived is None or declared_plane is None:
        return derived, None
    return derived, derived == str(declared_plane).strip().title()


ORDER_MEANING = _ORDER
