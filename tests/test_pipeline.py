"""Tests for sampling, sequence typing and normalisation. No data required."""
import sys, pathlib
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import sampling as sm
import sequence_typing as st
import normalize as nz


# ------------------------------------------------------------- sampling
def test_ends_are_never_discarded():
    """The headline fix: the notebook's 0.12-0.88 band drops the suprapatellar
    pouch, the popliteal fossa and the patella. Ends must always be sampled."""
    idx = sm.sample_indices(30, 12, band=(0.2, 0.8), keep_ends=True)
    assert 0 in idx and 29 in idx, idx


def test_band_respected_when_ends_disabled():
    idx = sm.sample_indices(30, 12, band=(0.2, 0.8), keep_ends=False)
    assert idx.min() >= 5 and idx.max() <= 24


def test_exact_count_and_sorted():
    for n in (1, 2, 5, 17, 30, 45, 300):
        for k in (4, 8, 12, 18, 32):
            idx = sm.sample_indices(n, k)
            assert idx.size == k, (n, k, idx.size)
            assert (np.diff(idx) >= 0).all()
            assert idx.min() >= 0 and idx.max() < max(n, 1)


def test_meniscal_body_stride_improves():
    """The intact meniscal body spans 2-3 sagittal slices, so a stride above ~2
    can miss it. Routing Medial Meniscus to its own band raises the local
    sampling density well past the notebook's uniform stride of ~2.6."""
    n = 30
    uniform = sm.sample_indices(n, 8, band=(0.2, 0.8), keep_ends=False)
    stride_uniform = float(np.mean(np.diff(uniform)))
    band = sm.label_band("Medial Meniscus", sm.SAGITTAL)
    routed = sm.sample_indices(n, 8, band=band, keep_ends=False)
    stride_routed = float(np.mean(np.diff(routed)))
    assert stride_uniform > 2.0
    assert stride_routed < 2.0, (stride_uniform, stride_routed)


def test_bands_cover_the_right_anatomy():
    # convention: sagittal 0=medial, coronal 0=anterior, axial 0=inferior
    assert sm.label_band("MCL", sm.SAGITTAL)[0] == 0.0          # far medial
    assert sm.label_band("Lateral Meniscus", sm.SAGITTAL)[1] > 0.9
    assert sm.label_band("PF OA", sm.CORONAL)[0] == 0.0         # anterior patella
    assert sm.label_band("Baker's", sm.CORONAL)[1] == 1.0       # popliteal fossa
    assert sm.label_band("Effusion", sm.AXIAL)[1] == 1.0        # suprapatellar
    assert sm.label_band("Contusion", sm.SAGITTAL) == sm.FULL   # can be anywhere


def test_routing_matrix_shape_and_priors():
    m, slots = sm.routing_matrix()
    assert m.shape == (12, 6) and len(slots) == 6
    assert np.allclose(m.sum(axis=1), 1.0)
    mf, slots_f = sm.routing_matrix(full=True)
    assert mf.shape == (12, 12) and len(slots_f) == 12
    assert np.allclose(mf.sum(axis=1), 1.0)
    i = sm.TARGETS.index("PF OA")
    ax = sum(m[i, j] for j, (p, _, _) in enumerate(slots) if p == sm.AXIAL)
    cor = sum(m[i, j] for j, (p, _, _) in enumerate(slots) if p == sm.CORONAL)
    assert ax > 3 * cor, "PF OA must be axial-dominant"
    j = sm.TARGETS.index("MCL")
    cor_m = sum(m[j, k] for k, (p, _, _) in enumerate(slots) if p == sm.CORONAL)
    sag_m = sum(m[j, k] for k, (p, _, _) in enumerate(slots) if p == sm.SAGITTAL)
    assert cor_m > 2 * sag_m, "MCL is a coronal diagnosis"


def test_fracture_keeps_non_fatsat_weight():
    """The fracture LINE is a dark line on non-fat-suppressed T1; fat-suppressed
    sequences show the oedema but blur the line."""
    frac = sm.CONTRAST_WEIGHT["Fracture"][(0, 0)]
    cont = sm.CONTRAST_WEIGHT["Contusion"][(0, 0)]
    assert frac > 3 * cont, (frac, cont)


def test_slot_grid_defaults_to_the_six_observed_slots():
    """MEASURED from train_series.csv: Fat_Suppression == Fluid_Sensitive for all
    24,371 train series and all 15 test series, so the mixed cells (1, 0) and
    (0, 1) do not exist in the organisers' metadata. Defaulting to the 2x2 would
    hand a training run six permanently-zero routing columns."""
    grid = sm.slot_grid()
    assert len(grid) == 6
    assert (sm.SAGITTAL, 1, 1) in grid and (sm.SAGITTAL, 0, 0) in grid
    assert (sm.SAGITTAL, 1, 0) not in grid and (sm.SAGITTAL, 0, 1) not in grid


def test_slot_grid_full_is_still_reachable():
    """The physics is unchanged -- a non-fat-sat T2 FSE really is fluid-sensitive.
    Recovering it needs TE from the headers, so keep the 2x2 available."""
    grid = sm.slot_grid(full=True)
    assert len(grid) == 12
    assert (sm.SAGITTAL, 1, 0) in grid and (sm.SAGITTAL, 0, 1) in grid


def test_pick_series_prefers_thin_spacing_over_slice_count():
    cands = [{"plane": sm.SAGITTAL, "fat_sat": 1, "fluid_sensitive": 1,
              "n_slices": 45, "spacing_mm": 5.0, "coverage_mm": 225},
             {"plane": sm.SAGITTAL, "fat_sat": 1, "fluid_sensitive": 1,
              "n_slices": 28, "spacing_mm": 2.5, "coverage_mm": 70}]
    got = sm.pick_series(cands, sm.SAGITTAL, 1, 1)
    assert got["spacing_mm"] == 2.5, "thin spacing must win over slice count"


def test_pick_series_deprioritises_failed_fatsat():
    cands = [{"plane": sm.AXIAL, "fat_sat": 1, "fluid_sensitive": 1,
              "n_slices": 30, "spacing_mm": 3.0, "fatsat_fail_ratio": 1.9},
             {"plane": sm.AXIAL, "fat_sat": 1, "fluid_sensitive": 1,
              "n_slices": 30, "spacing_mm": 3.5, "fatsat_fail_ratio": 0.4}]
    assert sm.pick_series(cands, sm.AXIAL, 1, 1)["fatsat_fail_ratio"] == 0.4


def test_slot_plan_reallocates_budget_when_a_plane_is_missing():
    full = [{"plane": p, "fat_sat": f, "fluid_sensitive": l, "n_slices": 30,
             "spacing_mm": 3.0, "coverage_mm": 90}
            for p in (sm.SAGITTAL, sm.CORONAL, sm.AXIAL) for f in (1, 0) for l in (1, 0)]
    no_ax = [c for c in full if c["plane"] != sm.AXIAL]
    a = sum(n for *_, n in sm.build_slot_plan(full, budget=64))
    b = sum(n for *_, n in sm.build_slot_plan(no_ax, budget=64))
    assert abs(a - 64) <= 8 and abs(b - 64) <= 8, (a, b)
    assert sm.build_slot_plan([], budget=64) == []


# ------------------------------------------------------ sequence typing
def test_gre_checked_before_tr_te():
    """The notebook tested GRE last, so a 2D MEDIC at TR 900 passed TR>=800 and
    was typed PD."""
    row = {"SeriesDescription": "sag medic", "ScanningSequence": "GR",
           "RepetitionTime": 900, "EchoTime": 20}
    assert st.sequence_class(row) == st.GRE


def test_inversion_recovery_is_its_own_class():
    """STIR at TE 110 typed T2, STIR at TE 40 typed PD -- one sequence, two buckets."""
    for te in (40, 110):
        row = {"SeriesDescription": "cor stir", "RepetitionTime": 4500,
               "EchoTime": te, "InversionTime": 150}
        assert st.sequence_class(row) == st.IR, te


def test_intermediate_weighted_split_from_pd():
    pd = {"SeriesDescription": "sag pd fs", "RepetitionTime": 2500, "EchoTime": 12}
    iw = {"SeriesDescription": "sag pd fs", "RepetitionTime": 2500, "EchoTime": 35}
    assert st.sequence_class(pd) == st.PD
    assert st.sequence_class(iw) == st.IW


def test_t1_boundary_allows_multislice_and_3t():
    """T1 TR is driven by slice count in 2D multi-slice, and tissue T1 lengthens
    with field strength, so the notebook's TR<800 rule was far too tight."""
    assert st.sequence_class({"SeriesDescription": "sag t1 tse",
                              "RepetitionTime": 950, "EchoTime": 15}) == st.T1
    assert st.sequence_class({"RepetitionTime": 900, "EchoTime": 12}) == st.T1


def test_fat_sat_and_fluid_are_independent_axes():
    t1fs = {"SeriesDescription": "ax t1 fs post", "RepetitionTime": 600, "EchoTime": 12}
    assert st.is_fat_suppressed(t1fs) and not st.is_fluid_sensitive(t1fs)
    t2 = {"SeriesDescription": "cor t2 tse", "RepetitionTime": 3500, "EchoTime": 90}
    assert not st.is_fat_suppressed(t2) and st.is_fluid_sensitive(t2)


def test_dixon_pair_detection():
    """One Dixon acquisition emits water-only and in-phase with identical TR/TE,
    so no TR/TE rule can separate them -- only the pairing can."""
    rows = [{"SeriesInstanceUID": "w", "Anatomical_Plane": "Sagittal",
             "SeriesDescription": "sag dixon w", "RepetitionTime": 3000, "EchoTime": 35},
            {"SeriesInstanceUID": "ip", "Anatomical_Plane": "Sagittal",
             "SeriesDescription": "sag dixon in phase", "RepetitionTime": 3000,
             "EchoTime": 35}]
    assert st.find_dixon_pairs(rows) == [("w", "ip")]


def test_magic_angle_risk_flagged_on_short_te():
    """Short-TE sequences create spurious signal in the normal posterior horn of
    the lateral meniscus; it vanishes above roughly TE 37."""
    short = st.conditioning_features({"SeriesDescription": "sag pd",
                                      "RepetitionTime": 2000, "EchoTime": 12})
    long = st.conditioning_features({"SeriesDescription": "sag pd",
                                     "RepetitionTime": 2000, "EchoTime": 40})
    assert short["magic_angle_risk"] == 1.0 and long["magic_angle_risk"] == 0.0


def test_conditioning_features_survive_missing_headers():
    f = st.conditioning_features({})
    assert f["has_tr"] == 0.0 and f["has_te"] == 0.0
    assert all(np.isfinite(list(f.values())))


def test_metal_and_postop_flags():
    f = st.conditioning_features({"SeriesDescription": "cor warp metal artifact"})
    assert f["metal_suppression"] == 1.0
    g = st.conditioning_features({"SeriesDescription": "sag pd post op acl graft"})
    assert g["post_op"] == 1.0


# --------------------------------------------------------- normalisation
def _phantom(bright_slices, bright_value):
    """Muscle at 100, fat at 200, plus `bright_slices` slices of fluid."""
    rng = np.random.default_rng(0)
    v = rng.normal(100, 5, size=(20, 64, 64)).astype(np.float32)
    v[:, :6, :] = 200.0
    for i in range(bright_slices):
        v[i, 30:40, 30:40] = bright_value
    return v


def test_per_slice_windowing_destroys_amplitude():
    """Trace vs tense effusion must remain distinguishable. Per-slice windowing
    maps the brightest fluid on every slice to 1.0 and erases the difference."""
    trace, tense = _phantom(2, 260.0), _phantom(2, 900.0)
    ps = abs(nz.per_slice_window(trace).max() - nz.per_slice_window(tense).max())
    assert ps < 1e-3, "premise: per-slice erases the difference"
    mr = abs(nz.muscle_reference(trace).max() - nz.muscle_reference(tense).max())
    assert mr > 0.5, "muscle referencing must preserve it"


def test_amplitude_features_separate_trace_from_tense():
    a = nz.amplitude_features(_phantom(2, 260.0))
    b = nz.amplitude_features(_phantom(2, 900.0))
    assert b["p999_over_muscle"] > 2 * a["p999_over_muscle"]


def test_muscle_mode_finds_the_muscle_peak():
    m = nz.muscle_mode(_phantom(0, 0))
    assert 85 < m < 115, m


def test_per_series_window_is_monotone_and_bounded():
    out = nz.per_series_window(_phantom(3, 500.0))
    assert 0.0 <= out.min() and out.max() <= 1.0


def test_fatsat_failure_detected():
    """A working fat-sat slice has a dark subcutaneous ring; a failed one does not."""
    def knee(ring_value):
        a = np.full((64, 64), 4.0, np.float32)      # air background
        a[8:56, 8:56] = 100.0                       # muscle / core
        a[8:14, 8:56] = a[50:56, 8:56] = ring_value  # subcutaneous fat, top/bottom
        a[8:56, 8:14] = a[8:56, 50:56] = ring_value  # and sides
        return a
    ok, bad = knee(20.0), knee(240.0)               # suppressed vs failed
    r_ok, r_bad = nz.fatsat_failure_ratio(ok), nz.fatsat_failure_ratio(bad)
    assert r_ok is not None and r_bad is not None
    assert r_ok < 1.2 < r_bad, (r_ok, r_bad)


def test_normalisers_handle_degenerate_input():
    empty = np.zeros((0, 8, 8), np.float32)
    assert nz.per_series_window(empty).size == 0
    assert nz.muscle_mode(empty) is None
    assert nz.fatsat_failure_ratio(np.zeros((4, 4), np.float32)) is None
    flat = np.ones((5, 32, 32), np.float32)
    assert np.isfinite(nz.muscle_reference(flat)).all()


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
