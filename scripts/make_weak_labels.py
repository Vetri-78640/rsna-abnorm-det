#!/usr/bin/env python3
"""Regenerate artifacts/weak_labels.csv from train.csv.

The file is gitignored because its gold:: columns are competition data, so it must
be rebuildable. Columns per label:

    raw::   the public notebook's lexicon, unmodified
    fix::   plus the fixes in src/lexicon_patch.py
    cal::   fix through one global Platt map fitted on the pooled gold cells
    gold::  the real label, non-null on the 58 gold studies only

cal is kept only as a control. Calibration is monotone, so AUC cannot see it; see
wiki/decisions/D004-no-target-calibration.md.

Usage:  python3 scripts/make_weak_labels.py [data_dir] [out_csv]
"""
import sys
import json
import pathlib

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

T = ["ACL", "MCL", "Medial Meniscus", "Lateral Meniscus", "Medial OA", "Lateral OA",
     "PF OA", "Effusion", "Synovitis", "Baker's", "Contusion", "Fracture"]


def logit(p, e=1e-4):
    p = np.clip(p, e, 1 - e)
    return np.log(p / (1 - p))


def fit_platt(x, y, iters=50):
    """One-feature logistic regression by Newton's method. The problem is convex,
    so this reaches the same optimum as any general optimiser, with no scipy."""
    X = np.column_stack([logit(x), np.ones_like(x)])
    w = np.array([1.0, 0.0])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ w))
        g = X.T @ (p - y)
        H = (X * (p * (1 - p))[:, None]).T @ X + 1e-9 * np.eye(2)
        step = np.linalg.solve(H, g)
        w -= step
        if np.abs(step).max() < 1e-10:
            break
    return w


def main(data_dir="data", out="artifacts/weak_labels.csv"):
    tr = pd.read_csv(pathlib.Path(data_dir) / "train.csv")
    gold = tr[T].notna().all(axis=1).to_numpy()
    reports = tr["Report"].fillna("").tolist()

    import lexicon_base as lex
    raw = pd.DataFrame([lex.extract(r) for r in reports])[T]
    import lexicon_patch  # noqa: F401 -- monkeypatches lex in place
    fix = pd.DataFrame([lex.extract(r) for r in reports])[T]

    a, b = fit_platt(fix[gold].to_numpy().ravel(), tr.loc[gold, T].to_numpy().ravel())
    cal = pd.DataFrame(1 / (1 + np.exp(-(a * logit(fix.to_numpy()) + b))), columns=T)

    df = pd.DataFrame({"StudyInstanceUID": tr["StudyInstanceUID"], "is_gold": gold.astype(int)})
    for t in T:
        df[f"raw::{t}"] = raw[t].to_numpy().astype(np.float32)
        df[f"fix::{t}"] = fix[t].to_numpy().astype(np.float32)
        df[f"cal::{t}"] = cal[t].to_numpy().astype(np.float32)
        df[f"gold::{t}"] = tr[t].to_numpy()

    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    (out.parent / "platt.json").write_text(json.dumps({"platt_a": a, "platt_b": b}))
    print(f"wrote {out} {df.shape}, platt a={a:.3f} b={b:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
