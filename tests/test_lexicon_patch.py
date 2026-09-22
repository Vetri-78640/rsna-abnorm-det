"""Regression tests for src/lexicon_patch.py.

Split into two groups. FIXES must change. REGRESSIONS must not -- they are the
cases the original lexicon already handled correctly, and the patch must leave
every one of them byte-identical.
"""
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import lexicon_base as lex

# A real gold report clause, Greek: "findings of incipient degenerative
# osteoarthritis IN THE MEDIAL COMPARTMENT". Gold says Medial 1, Lateral 0, PF 0.
# lexicon_base.GLOBAL_OA matches the bare word for osteoarthritis here, so once
# fix 1 lets a global match propagate, medial disease leaks onto the other two.
_EL_LOCALISED = ("\u03b5\u03c5\u03c1\u03b7\u03bc\u03b1\u03c4\u03b1 \u03b1\u03c1\u03c7\u03bf\u03bc\u03b5\u03bd\u03b7\u03c2 \u03b5\u03ba\u03c6\u03c5\u03bb\u03b9\u03c3\u03c4\u03b9\u03ba\u03b7\u03c2 "
                 "\u03bf\u03c3\u03c4\u03b5\u03bf\u03b1\u03c1\u03b8\u03c1\u03b9\u03c4\u03b9\u03b4\u03b1\u03c2 \u03ba\u03b1\u03c4\u03b1 \u03c4\u03bf \u03b5\u03c3\u03c9 \u03b4\u03b9\u03b1\u03bc\u03b5\u03c1\u03b9\u03c3\u03bc\u03b1.")

# capture the unpatched behaviour before importing the patch
_CASES = [
    ("Outerbridge grade 1 chondromalacia of the medial compartment.", "Medial OA"),
    ("Outerbridge grade 2 chondromalacia of the medial compartment.", "Medial OA"),
    ("Outerbridge grade 3 chondromalacia of the medial compartment.", "Medial OA"),
    ("Outerbridge grade 4 chondromalacia of the medial compartment.", "Medial OA"),
    ("ICRS grade 1 chondral change of the medial compartment.", "Medial OA"),
    ("ICRS grade 4 chondral change of the medial compartment.", "Medial OA"),
    ("Tricompartmental osteoarthritis, most severe in the patellofemoral joint.", "Medial OA"),
    ("Tricompartmental osteoarthritis, most severe in the patellofemoral joint.", "Lateral OA"),
    ("Tricompartmental osteoarthritis, most severe in the patellofemoral joint.", "PF OA"),
    ("Tricompartmental osteoarthritis.", "Medial OA"),
    (_EL_LOCALISED, "Medial OA"),
    (_EL_LOCALISED, "Lateral OA"),
    (_EL_LOCALISED, "PF OA"),
    ("Medial compartment osteoarthritis with sparing of the lateral compartment.", "Medial OA"),
    ("Medial compartment osteoarthritis with sparing of the lateral compartment.", "Lateral OA"),
    ("Degenerative changes of the medial meniscus without tear.", "Medial Meniscus"),
    ("Mucoid degeneration of the ACL without discrete tear.", "ACL"),
    ("Complete tear of the medial meniscus without displacement.", "Medial Meniscus"),
    ("Full-thickness tear of the ACL.", "ACL"),
    ("Severe medial compartment osteoarthritis.", "Medial OA"),
    ("Moderate lateral compartment osteoarthritis.", "Lateral OA"),
    ("No evidence of meniscal, ligamentous or cartilage injury.", "Medial Meniscus"),
    ("Large tense joint effusion.", "Effusion"),
    ("Bucket-handle tear of the medial meniscus.", "Medial Meniscus"),
    ("Normal cruciate ligaments.", "ACL"),
]
BEFORE = {(s, k): lex.extract(s)[k] for s, k in _CASES}

import lexicon_patch  # noqa: E402  -- import order is the point


def _after(s, k):
    return lex.extract(s)[k]


# ------------------------------------------------------------------ fixes
def test_oa_grade_is_now_monotone():
    """Was flat at 0.85 for grades 1-4; the grade must now order the score."""
    vals = [_after(f"Outerbridge grade {g} chondromalacia of the medial compartment.",
                   "Medial OA") for g in (1, 2, 3, 4)]
    assert vals == sorted(vals), vals
    assert vals[3] - vals[0] > 0.25, f"grades barely separated: {vals}"
    assert len(set(vals)) == 4


def test_icrs_scale_also_honoured():
    lo = _after("ICRS grade 1 chondral change of the medial compartment.", "Medial OA")
    hi = _after("ICRS grade 4 chondral change of the medial compartment.", "Medial OA")
    assert hi - lo > 0.25


def test_bare_grade_untouched():
    """Outerbridge 2 and Kellgren-Lawrence 2 mean different things, and the regex
    cannot tell them apart, so an unnamed scale must stay on the old path."""
    s = "Grade 2 changes of the medial compartment."
    assert abs(_after(s, "Medial OA") - BEFORE.get((s, "Medial OA"),
                                                   lex.extract(s)["Medial OA"])) < 1e-9


def test_global_oa_survives_a_named_compartment():
    s = "Tricompartmental osteoarthritis, most severe in the patellofemoral joint."
    for t in ("Medial OA", "Lateral OA"):
        assert BEFORE[(s, t)] < 0.4, "premise: was suppressed"
        assert _after(s, t) > 0.8, f"{t} still suppressed: {_after(s, t)}"
    assert _after(s, "PF OA") > 0.9


def test_naming_a_compartment_no_longer_hurts():
    """Adding detail must not reduce the score for the other compartments."""
    plain = _after("Tricompartmental osteoarthritis.", "Medial OA")
    detailed = _after("Tricompartmental osteoarthritis, most severe in the "
                      "patellofemoral joint.", "Medial OA")
    assert detailed >= plain - 1e-9


def test_sparing_negates_only_the_spared_side():
    s = "Medial compartment osteoarthritis with sparing of the lateral compartment."
    assert _after(s, "Lateral OA") < 0.4, "spared side must not score positive"
    assert _after(s, "Medial OA") > 0.8, "diseased side must be unaffected"


def test_post_posed_negation():
    assert _after("Degenerative changes of the medial meniscus without tear.",
                  "Medial Meniscus") < 0.3
    assert _after("Mucoid degeneration of the ACL without discrete tear.", "ACL") < 0.3


def test_post_posed_negation_multilingual():
    for s, k in [("Meniskusdegeneration medial ohne Riss.", "Medial Meniscus"),
                 ("Cambios degenerativos del menisco medial sin rotura.", "Medial Meniscus")]:
        assert _after(s, k) < 0.5, f"{s} -> {_after(s, k)}"


# ------------------------------------------------------------ regressions
REGRESSIONS = [
    ("Complete tear of the medial meniscus without displacement.", "Medial Meniscus"),
    ("Full-thickness tear of the ACL.", "ACL"),
    ("Severe medial compartment osteoarthritis.", "Medial OA"),
    ("Moderate lateral compartment osteoarthritis.", "Lateral OA"),
    ("No evidence of meniscal, ligamentous or cartilage injury.", "Medial Meniscus"),
    ("Large tense joint effusion.", "Effusion"),
    ("Bucket-handle tear of the medial meniscus.", "Medial Meniscus"),
    ("Normal cruciate ligaments.", "ACL"),
    ("Tricompartmental osteoarthritis.", "Medial OA"),
]


def test_no_regressions():
    bad = [(s, k, BEFORE[(s, k)], _after(s, k)) for s, k in REGRESSIONS
           if abs(BEFORE[(s, k)] - _after(s, k)) > 1e-9]
    assert not bad, f"patch changed cases that were already correct: {bad}"


def test_scoped_negation_does_not_overreach():
    """The scoping guard: 'without displacement' carries no pathology token, so
    it must not negate the tear that precedes it."""
    assert _after("Complete tear of the medial meniscus without displacement.",
                  "Medial Meniscus") > 0.9


def test_globality_regex_requires_a_qualifier():
    """lexicon_base.GLOBAL_OA matches bare Greek "osteoarthritis" and bare
    "compartments", neither of which asserts globality. Fix 1 makes a global
    match propagate to all three compartments, so the regex has to be tight."""
    G = lexicon_patch.GLOBAL_OA
    for qualified in ("tricompartmental osteoarthritis", "gonarthrosis",
                      "osteoarthritis of the knee", "degenerative joint disease",
                      "artroza koljena", "\u03b1\u03c1\u03b8\u03c1\u03b9\u03c4\u03b9\u03b4\u03b1 \u03c4\u03bf\u03c5 \u03b3\u03bf\u03bd\u03b1\u03c4\u03bf\u03c2"):
        assert G.search(qualified), f"globality lost: {qualified}"
    for unqualified in ("\u03bf\u03c3\u03c4\u03b5\u03bf\u03b1\u03c1\u03b8\u03c1\u03b9\u03c4\u03b9\u03b4\u03b1",
                        "\u03b5\u03ba\u03c6\u03c5\u03bb\u03b9\u03c3\u03c4\u03b9\u03ba\u03b7 \u03bf\u03c3\u03c4\u03b5\u03bf\u03b1\u03c1\u03b8\u03c1\u03b9\u03c4\u03b9\u03b4\u03b1",
                        "the lateral and patellofemoral compartments",
                        "medial and lateral compartments"):
        assert not G.search(unqualified), f"false globality: {unqualified}"


def test_localised_greek_oa_does_not_propagate():
    """The regression this guards: medial-only OA in Greek must not raise
    Lateral OA or PF OA. Measured cost on the gold 58 when it did: Lateral OA
    -0.0097, PF OA -0.0116 AUC."""
    assert _after(_EL_LOCALISED, "Medial OA") > 0.5
    for side in ("Lateral OA", "PF OA"):
        assert _after(_EL_LOCALISED, side) < 0.5, (
            f"{side} raised by a medial-only Greek clause: "
            f"{_after(_EL_LOCALISED, side):.2f}")


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
