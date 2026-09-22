"""Tests for src/geometry.py, run without pydicom or competition data.

The headline test is test_vendor_sign_invariance: two vendors writing opposite
but equally valid IOP conventions for the same sagittal acquisition must produce
the same anatomical slice order. The public notebook fails this.
"""
import sys, pathlib
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import geometry as g

# two real-world sagittal conventions whose raw cross products point opposite ways
SAG_A = [0, 1, 0, 0, 0, -1]      # cross -> (-1, 0, 0)
SAG_B = [0, -1, 0, 0, 0, -1]     # cross -> (+1, 0, 0)
COR = [1, 0, 0, 0, 0, -1]        # cross -> (0, 1, 0)
AX = [1, 0, 0, 0, 1, 0]          # cross -> (0, 0, 1)


def _stack(iop, axis, lo, hi, n=12):
    """A stack whose slices advance along `axis` from lo to hi mm."""
    out = []
    for i, t in enumerate(np.linspace(lo, hi, n)):
        ipp = [0.0, 0.0, 0.0]
        ipp[axis] = float(t)
        out.append({"iop": iop, "ipp": ipp, "instance": i + 1, "name": f"{i:03d}.dcm"})
    return out


def test_raw_cross_product_signs_disagree():
    """Confirms the premise: the two conventions really do differ in raw sign."""
    a = np.cross(SAG_A[0:3], SAG_A[3:6])
    b = np.cross(SAG_B[0:3], SAG_B[3:6])
    assert a[0] < 0 < b[0]


def test_canonical_normal_agrees():
    na, pa = g.canonical_normal(SAG_A)
    nb, pb = g.canonical_normal(SAG_B)
    assert pa == pb == g.SAGITTAL
    assert np.allclose(na, nb) and na[0] > 0


def test_vendor_sign_invariance():
    """The fix: identical anatomy, opposite IOP conventions, same ordering."""
    a, ma = g.order_slices(_stack(SAG_A, 0, -50, 50))
    b, mb = g.order_slices(_stack(SAG_B, 0, -50, 50))
    assert ma == mb == "geometry"
    xa = [r["ipp"][0] for r in a]
    xb = [r["ipp"][0] for r in b]
    assert xa == sorted(xa), "canonical sagittal order must run patient right to left"
    assert xa == xb, "vendor convention must not change anatomical order"


def test_plane_detection():
    assert g.plane_of(SAG_A) == g.SAGITTAL
    assert g.plane_of(COR) == g.CORONAL
    assert g.plane_of(AX) == g.AXIAL


def test_oblique_still_resolves():
    """A 15-degree oblique sagittal ACL series must still type as sagittal."""
    th = np.radians(15)
    iop = [0, np.cos(th), -np.sin(th), 0, 0, -1]
    assert g.plane_of(iop) == g.SAGITTAL


def test_slice_metrics_recovers_spacing():
    m = g.slice_metrics(_stack(SAG_A, 0, 0, 33, n=12))   # 12 slices over 33 mm
    assert abs(m["spacing_mm"] - 3.0) < 1e-6
    assert abs(m["coverage_mm"] - 33.0) < 1e-6


def test_image_centre_uses_pixel_centres_and_correct_spacing_index():
    """PixelSpacing is [row, col]; the column direction pairs with index 1."""
    c = g.image_centre(COR, [-70.0, 0.0, 20.0], rows=256, cols=320,
                       pixel_spacing=[0.5, 0.4])
    # column dir (1,0,0) advances by 0.4 * (320-1)/2 = 63.8 mm
    assert abs(c[0] - (-70.0 + 63.8)) < 1e-9
    # row dir (0,0,-1) advances by 0.5 * (256-1)/2 = 63.75 mm downward in z
    assert abs(c[2] - (20.0 - 63.75)) < 1e-9


def test_in_plane_flips():
    # coronal with column dir +x already puts patient-left on the image right
    assert g.in_plane_flips(COR) == (False, False)
    # mirrored coronal needs a horizontal flip
    assert g.in_plane_flips([-1, 0, 0, 0, 0, -1])[0] is True
    # coronal with column dir +z puts superior at the bottom -> vertical flip
    assert g.in_plane_flips([1, 0, 0, 0, 0, 1])[1] is True


def test_laterality_flips_reverse_right_sagittal():
    assert g.laterality_flips(g.SAGITTAL, "R") == (False, True)
    assert g.laterality_flips(g.SAGITTAL, "L") == (False, False)
    assert g.laterality_flips(g.CORONAL, "R") == (True, False)
    assert g.laterality_flips(g.AXIAL, "L") == (False, False)
    assert g.laterality_flips(g.CORONAL, None) == (False, False)


def test_study_laterality_prefers_tag_and_never_guesses_from_x():
    assert g.study_laterality([{"Laterality": "R"}, {"Laterality": "R"}]) == ("R", "tag")
    assert g.study_laterality([{"ImageLaterality": "l"}]) == ("L", "tag")
    # a lone series with no tag must stay unresolved rather than fall back to IPP.x
    assert g.study_laterality([{"ipp": [-80.0, 0, 0]}]) == (None, "unresolved")
    side, how = g.study_laterality([{"Laterality": "L"}, {"Laterality": "R"}])
    assert how == "conflict" and side is None


def test_plane_agreement_flags_oblique():
    assert g.plane_agreement(SAG_A, "Sagittal") == (g.SAGITTAL, True)
    assert g.plane_agreement(SAG_A, "Coronal") == (g.SAGITTAL, False)


def test_degenerate_headers_do_not_crash():
    assert g.plane_of(None) is None
    assert g.canonical_normal("garbage") == (None, None)
    assert g.slice_key([0, 0, 0, 0, 0, 0], [1, 2, 3]) is None
    assert g.image_centre(COR, [0, 0, 0], 0, 0, [1, 1]) is None
    recs = [{"iop": None, "ipp": None, "name": "s2.dcm"},
            {"iop": None, "ipp": None, "name": "s10.dcm"},
            {"iop": None, "ipp": None, "name": "s1.dcm"}]
    ordered, method = g.order_slices(recs)
    assert method == "name"
    assert [r["name"] for r in ordered] == ["s1.dcm", "s2.dcm", "s10.dcm"]


def test_backslash_and_pipe_multivalue_parsing():
    assert np.allclose(g.as_vec("0\\1\\0\\0\\0\\-1", 6), SAG_A)
    assert np.allclose(g.as_vec("0|1|0|0|0|-1", 6), SAG_A)


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  pass  {name}")
            except Exception as exc:
                fails += 1
                print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{fails} failure(s)")
    sys.exit(1 if fails else 0)
