"""Verified fixes to the public notebook's report lexicon (cells 1-3).

Every defect below was reproduced by executing the original lexicon; the before
and after numbers are in wiki/archive/FINDINGS.md and are asserted in
tests/test_lexicon_patch.py.

Why this matters more than any model change: all three model families in the
0.939 ensemble were trained on labels this lexicon produced. Its precision is
the ceiling for all of them, so a fix here lifts every family at once.

Usage:
    import lexicon_base as lex
    import lexicon_patch            # monkeypatches lex in place
    lex.extract(report_text)

Three defects:

1. GRADE DISCARDED FOR OA. `_grade_of()` is wired into `_score_paired()` but not
   `_score_oa()`. With wording held constant, Outerbridge/ICRS grades 1 to 4 all
   scored 0.85 -- softening with an intact surface scored the same as
   full-thickness loss with exposed bone. The meniscus path uses the grade
   correctly, jumping at the grade-2/3 boundary, so the omission looks accidental.

2. GLOBAL OA EVIDENCE DROPPED. In `_score_oa()`, `g_pos` incremented only inside
   the `if not hits:` branch. So "tricompartmental osteoarthritis" scored 0.83 on
   all three compartments, but "tricompartmental osteoarthritis, most severe in
   the patellofemoral joint" scored PF OA 0.96 and Medial/Lateral OA 0.28 --
   adding clinically informative detail destroyed two of twelve targets.

3. POST-POSED NEGATION MISSED. `without` and its Romance/Germanic equivalents
   live only in `PRE_NEG`, which is searched backwards from the match. Negation
   trailing the anatomy was invisible: "medial meniscus without tear" scored 0.96.
"""

from __future__ import annotations

import re

import lexicon_base as lex
from lexicon_base import (_rx, _grade_of, _polarity, _severity, _grade, _near,
                          _negated, OA_EVIDENCE, TF_SITE, PF_SITE, SIDE_MEDIAL,
                          SIDE_LATERAL, OA_TARGETS, TEAR, FEATURES)

# ---------------------------------------------------------------- fix 1a
# lexicon_base.GLOBAL_OA is not a globality detector. Its English entries all
# carry a qualifier (tricompartmental, gonarthrosis, osteoarthritis of the knee)
# but four do not: the two bare Greek words for osteoarthritis, and bare
# "compartments"/"compartmens". Those were harmless in the original _score_oa,
# which consulted GLOBAL_OA only when NO compartment was named. Fix 1 below makes
# a global match propagate to all three compartments, which promotes the regex
# from decorative to load-bearing -- and then
#
#   "arcomenis ekfylistikis osteoarthritidas kata to eso diamerisma"
#   ( = incipient degenerative osteoarthritis IN THE MEDIAL COMPARTMENT )
#
# propagates medial disease onto Lateral OA and PF OA. Verified on the gold 58:
# it costs Lateral OA 0.0097 and PF OA 0.0116 AUC, and fires on 98 of the 4,407
# training studies. Every alternative here carries a globality qualifier.
GLOBAL_OA = _rx(
    "tri ?compartment", "all three compartment", "three compartments",
    "global(ised)? (oa|osteoarthrit)",
    r"\bgonarthros", r"\bgonartros", r"\bgonarthrose", r"\bgonartrose",
    "gonartro", "goanrtrot", "gonartrot", r"\bgonartroz",
    "osteoarthritis of the knee", "knee osteoarthrit",
    "artrosis (de |)(la )?rodilla", r"\bdiz osteoartrit", "artroza koljena",
    "\u03b1\u03c1\u03b8\u03c1\u03b9\u03c4\u03b9\u03b4\u03b1 \u03c4\u03bf\u03c5 \u03b3\u03bf\u03bd\u03b1\u03c4\u03bf\u03c2",
    "\u03b1\u03c1\u03b8\u03c1\u03b9\u03c4\u03b9\u03b4\u03b1 \u03c4\u03c9\u03bd \u03b3\u03bf\u03bd\u03b1\u03c4\u03c9\u03bd",
    "\u0430\u0440\u0442\u0440\u043e\u0437\u0430 \u043d\u0430 \u043a\u043e\u043b\u044f\u043d\u043d\u0430\u0442\u0430", "\u0433\u043e\u043d\u0430\u0440\u0442\u0440\u043e\u0437",
    "degenerative joint disease", r"\bdjd\b",
)


# ---------------------------------------------------------------- fix 3a
# Scoped post-posed negation. The scoping is essential: a bare forward search for
# "without" would wrongly negate "complete tear of the medial meniscus without
# displacement". Firing only when a PATHOLOGY token follows keeps that case intact.
POST_NEG_SCOPED = _rx(
    r"\bwithout\b", r"\bsin\b", r"\bohne\b", r"\bzonder\b", r"\bsans\b",
    r"\bbez\b", r"\bsenza\b", r"\bsem\b", r"\bχωρις\b", r"\bбез\b",
    r"\bolmaksizin\b", r"\beslik etmeyen\b", r"\bicermeyen\b", r"\bnegative for\b",
)
PATHOLOGY_ANY = _rx(TEAR.pattern, OA_EVIDENCE.pattern,
                    r"\btear", r"\brotur", r"\briss", r"\byirtik", r"\bruptur")
POST_NEG_GAP = 60      # how far after the span the marker may sit
POST_NEG_REACH = 40    # how far after the marker the pathology token may sit


def _post_negated(clause: str, end: int) -> bool:
    for m in POST_NEG_SCOPED.finditer(clause):
        if m.start() >= end and m.start() - end <= POST_NEG_GAP:
            if PATHOLOGY_ANY.search(clause[m.end():m.end() + POST_NEG_REACH]):
                return True
    return False


def _negated_v2(clause: str, start: int, end: int) -> bool:
    return _negated(clause, start, end) or _post_negated(clause, end)


# ---------------------------------------------------------------- fix 3b
# Contrastive sparing: "medial OA with sparing of the lateral compartment" was
# scoring Lateral OA at 0.85. Forward-only from the sparing term, because a
# symmetric window in a short clause suppresses BOTH compartments -- the diseased
# side is named before the sparing term, the spared side after it.
SPARING = _rx(r"\bspar(ing|ed)\b", r"\bpreserv", r"\bconservad", r"\berhalten\b",
              r"\bgespaard\b", r"\bkorunmus\b", r"\bocuvan", r"\bδιατηρ",
              r"\bзапазен", r"\bintegro\b", r"\brisparmi")
SPARING_REACH = 30


def _spared_side(clause: str, side_rx) -> bool:
    for m in SPARING.finditer(clause):
        if side_rx.search(clause[m.end():m.end() + SPARING_REACH]):
            return True
    return False


# ---------------------------------------------------------------- fix 2
# Cartilage grade -> severity. Applied ONLY when the scale is named, because the
# capture group cannot tell Outerbridge grade 2 (<50% cartilage loss, below the
# usual OA threshold) from Kellgren-Lawrence grade 2 (definite OA). A bare
# "grade 2" therefore stays on the old severity path.
_SCALE_RX = re.compile(r"\b(outerbridge|icrs)\b")
_GRADE_SEV = {1: 0.30, 2: 0.60, 3: 0.85, 4: 1.00}


def _oa_severity(clause: str) -> float:
    if _SCALE_RX.search(clause):
        g = _grade_of(clause)
        if g is not None:
            return _GRADE_SEV[g]
    return _severity(clause)


# ---------------------------------------------------------------- fix 1 (+2, 3b)
def _score_oa_v2(cls):
    acc = {t: {"pos": 0, "neg": 0, "unc": 0, "best": 0.0} for t in OA_TARGETS}
    g_pos, g_neg, g_best = 0, 0, 0.0

    for c in cls:
        m = OA_EVIDENCE.search(c)
        if not m:
            continue
        pol = _polarity(c, (m.start(), m.end()))
        sev = _oa_severity(c)                                   # fix 2
        is_global = GLOBAL_OA.search(c) is not None

        tf_med = _near(c, TF_SITE, SIDE_MEDIAL, 45) and not _spared_side(c, SIDE_MEDIAL)
        tf_lat = _near(c, TF_SITE, SIDE_LATERAL, 45) and not _spared_side(c, SIDE_LATERAL)
        pf = PF_SITE.search(c) is not None
        hits = [t for t, h in (("Medial OA", tf_med), ("Lateral OA", tf_lat),
                               ("PF OA", pf)) if h]

        # fix 1: a global-OA statement registers even when a compartment is also
        # named. Deliberately NOT unconditional -- making every unattributed OA
        # clause set g_pos would let "medial compartment OA" imply lateral OA.
        if is_global:
            if pol == "positive":
                g_pos += 1
                g_best = max(g_best, sev)
            elif pol == "negative":
                g_neg += 1
        elif not hits:
            if pol == "positive":
                g_pos += 1
                g_best = max(g_best, sev * 0.7)
            elif pol == "negative":
                g_neg += 1

        if not hits:
            continue
        for t in hits:
            if pol == "positive":
                acc[t]["pos"] += 1
                acc[t]["best"] = max(acc[t]["best"], sev)
            elif pol == "negative":
                acc[t]["neg"] += 1
            else:
                acc[t]["unc"] += 1
                acc[t]["best"] = max(acc[t]["best"], 0.3)

    out = {}
    for t in OA_TARGETS:
        a = acc[t]
        pos, neg, unc, best = a["pos"], a["neg"], a["unc"], a["best"]
        if not (pos or unc) and g_pos and FEATURES["oa_inherit"]:
            if neg:
                score, conf = _grade(0, neg, 0, 0.0)
                score, conf = max(score, 0.35), conf * 0.7
            else:
                score, conf = _grade(g_pos, 0, 0, g_best * 0.92)
                conf *= 0.75
        else:
            score, conf = _grade(pos, neg + g_neg, unc, best)
        out[t] = (score, conf, pos, neg)
    return out


def apply():
    """Install the patches. Idempotent."""
    lex._negated = _negated_v2
    lex._score_oa = _score_oa_v2
    return lex


apply()
