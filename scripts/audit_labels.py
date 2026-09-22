#!/usr/bin/env python3
"""Tier-0 audit. Answers, from the metadata CSVs alone, the questions that every
downstream decision branches on.

  1. How many studies carry gold labels?  A research agent reported 58 of 4,407
     from secondary sources. If that is right, NO per-label parameter can be
     fitted on gold -- a 3%-prevalence label would have about two positives --
     and several recommendations in wiki/raw/research.md are void.
  2. Per-label prevalence, which sets macro-AUC leverage. Moving Effusion from
     0.95 to 0.96 gains 0.0008 macro; moving Fracture from 0.80 to 0.88 gains
     0.0067. Effort should follow this table, not intuition.
  3. Language mix, which decides how much multilingual lexicon work is worth doing.
  4. Whether the lexicon patches actually improve agreement with gold.

Usage:  python3 scripts/audit_labels.py [data_dir]
"""
from __future__ import annotations

import sys
import pathlib
import re
import unicodedata
from collections import Counter

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

TARGETS = ["ACL", "MCL", "Medial Meniscus", "Lateral Meniscus", "Medial OA",
           "Lateral OA", "PF OA", "Effusion", "Synovitis", "Baker's",
           "Contusion", "Fracture"]

# Function words that are distinctive enough to fingerprint a report's language
# without pulling in a dependency. Scripts (Greek, Cyrillic) are checked first.
_HINTS = {
    "es": r"\b(del|los|las|con|sin|articular|rodilla|se observa)\b",
    "pt": r"\b(dos|das|com|sem|joelho|não|apresenta)\b",
    "it": r"\b(del|della|con|senza|ginocchio|non si|nella norma)\b",
    "fr": r"\b(du|des|avec|sans|genou|pas de|aspect)\b",
    "de": r"\b(des|der|mit|ohne|kein|nachweis|kniegelenk|unauff)\b",
    "nl": r"\b(van|het|met|zonder|geen|knie|afwijking)\b",
    "tr": r"\b(ile|var|yok|izlenmekte|eklem|diz|mevcut)\b",
    "hr": r"\b(bez|nema|zglob|koljena|uredan|prikaz)\b",
    "en": r"\b(the|of|with|without|no evidence|joint|knee|there is)\b",
}


def detect_language(text):
    if not isinstance(text, str) or not text.strip():
        return "empty"
    if re.search(r"[Ͱ-Ͽ]", text):
        return "el"
    if re.search(r"[Ѐ-ӿ]", text):
        return "bg/ru"
    if re.search(r"[一-鿿぀-ヿ]", text):
        return "cjk"
    if re.search(r"[֐-׿]", text):
        return "he"
    if re.search(r"[؀-ۿ]", text):
        return "ar"
    low = unicodedata.normalize("NFKD", text.lower())
    low = "".join(c for c in low if not unicodedata.combining(c))
    scores = {k: len(re.findall(v, low)) for k, v in _HINTS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else "unknown"


def _auc(y, p):
    """Rank AUC, ties averaged. Returns nan when a class is absent."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    ok = np.isfinite(y) & np.isfinite(p)
    y, p = y[ok], p[ok]
    n1, n0 = int((y == 1).sum()), int((y == 0).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    r = pd.Series(p).rank().to_numpy()
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def _auc_se(auc, n_pos, n_neg):
    """Hanley-McNeil standard error. The point of printing it: at ~39 positives
    an AUC of 0.90 carries an SE around 0.033, which is larger than the gap
    between many leaderboard positions."""
    if not np.isfinite(auc) or n_pos < 1 or n_neg < 1:
        return float("nan")
    q1 = auc / (2 - auc)
    q2 = 2 * auc ** 2 / (1 + auc)
    v = (auc * (1 - auc) + (n_pos - 1) * (q1 - auc ** 2)
         + (n_neg - 1) * (q2 - auc ** 2)) / (n_pos * n_neg)
    return float(np.sqrt(max(v, 0)))


def main(data_dir="data"):
    d = pathlib.Path(data_dir)
    train_path = d / "train.csv"
    if not train_path.exists():
        print(f"no {train_path}. Run scripts/fetch_metadata.sh first.")
        return 1

    train = pd.read_csv(train_path)
    n = len(train)
    print(f"=== studies ===\n{n} rows in train.csv\n")

    present = [t for t in TARGETS if t in train.columns]
    missing = [t for t in TARGETS if t not in train.columns]
    if missing:
        print(f"WARNING: label columns absent from train.csv: {missing}\n")

    # ---- 1. gold coverage --------------------------------------------------
    gold_mask = train[present].notna().all(axis=1) if present else pd.Series(False, index=train.index)
    n_gold = int(gold_mask.sum())
    print("=== gold label coverage ===")
    print(f"studies with all {len(present)} labels present: {n_gold} "
          f"({100 * n_gold / max(n, 1):.2f}%)")
    if present:
        partial = int((train[present].notna().any(axis=1) & ~gold_mask).sum())
        print(f"studies with SOME labels present: {partial}")
    if n_gold and n_gold < 300:
        print("\n  ** n_gold is small. Do NOT fit per-label parameters on it.")
        print("     Use gold only to choose among a handful of candidates.")
    print()

    # ---- 2. prevalence and macro-AUC leverage ------------------------------
    if n_gold:
        g = train.loc[gold_mask, present]
        n_test = 1300
        print("=== prevalence and macro-AUC leverage (gold subset) ===")
        print("  ** gold prevalence is NOT population prevalence -- see the")
        print("     enrichment test below before using exp@1300 for anything.")
        print(f"{'label':<18}{'n_pos':>7}{'prev':>8}{'exp@1300':>10}"
              f"{'AUC SE@.90':>12}{'leverage':>10}")
        rows = []
        for t in present:
            pos = int(g[t].sum())
            prev = pos / len(g)
            exp = prev * n_test
            se = _auc_se(0.90, max(int(round(exp)), 1), max(int(round(n_test - exp)), 1))
            rows.append((t, pos, prev, exp, se))
            print(f"{t:<18}{pos:>7}{prev:>8.3f}{exp:>10.0f}{se:>12.4f}"
                  f"{1 / 12:>10.4f}")
        print("\n  leverage is 1/12 for every label: a +0.01 AUC move on ANY label")
        print("  is worth 0.00083 macro. So spend effort where +0.01 is ACHIEVABLE,")
        print("  which is the rare, small-feature labels, not the saturated ones.")
        rare = sorted(rows, key=lambda r: r[3])[:4]
        print(f"  rarest four IN GOLD: {', '.join(r[0] for r in rare)}")
        print()

    # ---- 2b. is the gold subset a random sample? ---------------------------
    # It is not. Measured on this data: Fracture fires 5.2x more often on gold
    # than on the rest (p=4e-11), Contusion 2.3x, ACL 2.2x, while the three OA
    # labels and Baker's are flat. The gold 58 is trauma-enriched, so every
    # absolute number derived from it is biased and exp@1300 above is fiction.
    # Ranking a handful of candidates on it is still fine, and is in fact better
    # than a random 58 would be for the rare labels.
    if n_gold and "Report" in train.columns:
        try:
            import lexicon_base as lex0
            sc = pd.DataFrame([lex0.extract(r) for r in train["Report"].fillna("")])
            print("=== is the gold subset random? (lexicon fire rate) ===")
            print(f"{'label':<18}{'gold':>8}{'rest':>8}{'ratio':>8}{'p(>=k)':>10}")
            from math import comb
            skew = 0
            for t in present:
                if t not in sc:
                    continue
                gm = gold_mask.to_numpy()
                p0 = float((sc.loc[~gm, t] > 0.5).mean())
                k = int((sc.loc[gm, t] > 0.5).sum())
                pv = sum(comb(n_gold, j) * p0 ** j * (1 - p0) ** (n_gold - j)
                         for j in range(k, n_gold + 1))
                ratio = (k / n_gold) / max(p0, 1e-9)
                skew += pv < 0.01
                print(f"{t:<18}{k / n_gold:>8.3f}{p0:>8.3f}{ratio:>8.2f}{pv:>10.1e}")
            if skew:
                print(f"\n  ** {skew} labels enriched at p<0.01. The gold set is NOT a")
                print("     random sample. Do not read test prevalence off it, and do")
                print("     not use it to allocate effort by rarity.")
            print()
        except Exception as exc:
            print(f"  enrichment test skipped: {type(exc).__name__}: {exc}\n")

    # ---- 3. language mix ---------------------------------------------------
    if "Report" in train.columns:
        langs = Counter(detect_language(r) for r in train["Report"].fillna(""))
        print("=== report language mix (heuristic) ===")
        for k, v in langs.most_common():
            print(f"  {k:<10}{v:>6}  {100 * v / n:>5.1f}%")
        exotic = sum(v for k, v in langs.items() if k in ("cjk", "he", "ar"))
        if exotic:
            print(f"\n  ** {exotic} reports in scripts the lexicon's normalize()")
            print("     cannot handle. Route these to an LLM labeler, conf 0.")
        print()

        med = int(train["Report"].fillna("").str.len().median())
        print(f"median report length: {med} characters\n")

    # ---- 4. does the lexicon patch help? -----------------------------------
    if "Report" in train.columns and n_gold >= 20:
        print("=== lexicon scorecard vs gold ===")
        try:
            import lexicon_base as lex
            reports = train.loc[gold_mask, "Report"].fillna("").tolist()
            truth = train.loc[gold_mask, present]

            before = pd.DataFrame([lex.extract(r) for r in reports])
            import lexicon_patch  # noqa: F401 -- monkeypatches lex
            after = pd.DataFrame([lex.extract(r) for r in reports])

            print(f"{'label':<18}{'n_pos':>7}{'AUC before':>12}{'AUC after':>11}{'delta':>9}")
            deltas = []
            for t in present:
                y = truth[t].to_numpy()
                a, b = _auc(y, before[t].to_numpy()), _auc(y, after[t].to_numpy())
                if np.isfinite(a) and np.isfinite(b):
                    deltas.append(b - a)
                dl = f"{b - a:+.4f}" if np.isfinite(a) and np.isfinite(b) else "  n/a"
                print(f"{t:<18}{int(y.sum()):>7}{a:>12.4f}{b:>11.4f}{dl:>9}")
            if deltas:
                print(f"\nmacro AUC before {np.nanmean([_auc(truth[t], before[t]) for t in present]):.4f}"
                      f"  after {np.nanmean([_auc(truth[t], after[t]) for t in present]):.4f}")
                print("  NOTE: with a small gold set these deltas are noisy. Treat a")
                print("  change under one SE as unmeasured, not as zero.")

            # Threshold sweep. AUC cannot see this, but a training run using
            # these scores as soft targets can: every optimal threshold sits far
            # above 0.5, so the lexicon over-calls on every label at once.
            print("\n=== lexicon calibration ===")
            print(f"{'label':<18}{'agree@.5':>10}{'best th':>9}{'agree@best':>12}")
            ths = np.arange(0.05, 1.0, 0.01)
            a5s, abs_, tbs = [], [], []
            for t in present:
                y = truth[t].to_numpy().astype(int)
                v = after[t].to_numpy()
                a5 = float(((v > 0.5).astype(int) == y).mean())
                ab, tb = max((float(((v > th).astype(int) == y).mean()), float(th))
                             for th in ths)
                a5s.append(a5); abs_.append(ab); tbs.append(tb)
                print(f"{t:<18}{a5:>10.3f}{tb:>9.2f}{ab:>12.3f}")
            high = sum(t > 0.5 for t in tbs)
            print(f"\nmean agreement {np.mean(a5s):.3f} -> {np.mean(abs_):.3f} "
                  f"by threshold alone (fitted on gold, so optimistic)")
            print(f"  {high}/{len(tbs)} optimal thresholds above 0.5. The magnitude is")
            print("  overfitted at this n; the DIRECTION is a sign test at "
                  f"p={2.0 ** -len(tbs):.0e}.")
            print("  AUC cannot see this. A BCE run against these soft targets can.")
        except Exception as exc:
            print(f"  skipped: {type(exc).__name__}: {exc}")
        print()

    # ---- 5. protocol distribution -----------------------------------------
    sp = d / "train_series.csv"
    if sp.exists():
        s = pd.read_csv(sp)
        print("=== series / protocol ===")
        print(f"{len(s)} series over {s['StudyInstanceUID'].nunique()} studies "
              f"(median {s.groupby('StudyInstanceUID').size().median():.0f} per study)")
        if "Anatomical_Plane" in s.columns:
            print("\nplane x fat-sat x fluid-sensitive availability:")
            grp = s.groupby(["Anatomical_Plane", "Fat_Suppression", "Fluid_Sensitive"]).size()
            for (pl, fs, fl), c in grp.items():
                print(f"  {pl:<10} fs={fs} fluid={fl}  {c:>7}  "
                      f"{100 * c / len(s):>5.1f}%")
            # the organisers warn these two flags are correlated but not equal
            if {"Fat_Suppression", "Fluid_Sensitive"} <= set(s.columns):
                x = pd.crosstab(s["Fat_Suppression"], s["Fluid_Sensitive"])
                off = int(x.to_numpy().sum() - np.trace(x.to_numpy()))
                print(f"\n  series where fat-sat != fluid-sensitive: {off} "
                      f"({100 * off / len(s):.1f}%)")
                print("  -> these are exactly the series a 1-D slot key mishandles")
        print("\nstudies missing each plane:")
        have = s.groupby("StudyInstanceUID")["Anatomical_Plane"].apply(set)
        for pl in ("Sagittal", "Coronal", "Axial"):
            miss = int((~have.apply(lambda v: pl in v)).sum())
            print(f"  {pl:<10}{miss:>6} ({100 * miss / len(have):.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
