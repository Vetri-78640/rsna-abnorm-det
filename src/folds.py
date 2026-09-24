"""Cross-validation folds that do not leak.

The public notebook forms folds from the MD5 of the report text, so two reports
differing by one character land in different folds while describing the same
patient's knee. That inflates CV. See wiki/archive/FINDINGS.md item 12.

Here a fold is assigned to a *cluster* of near-duplicate reports, and clusters are
distributed by iterative stratification so every fold sees a similar number of
positives for each of the twelve labels.

Numpy only, no scipy: scipy's native libraries do not load on every machine here.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import defaultdict

import numpy as np

_WS = re.compile(r"\s+")
_NONWORD = re.compile(r"[^a-z0-9 ]+")


def normalise(text):
    """Fold case, strip accents and punctuation, collapse whitespace. Two reports
    that differ only in formatting normalise to the same string."""
    if not isinstance(text, str):
        return ""
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return _WS.sub(" ", _NONWORD.sub(" ", t)).strip()


def _shingles(tokens, k=5):
    if len(tokens) < k:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i:i + k]) for i in range(len(tokens) - k + 1)}


def report_clusters(reports, threshold=0.8, block_tokens=6):
    """Group near-duplicate reports. Returns an array of cluster ids.

    Exact matches after normalisation always share a cluster. Near-duplicates are
    found within a block keyed on the first `block_tokens` tokens, which keeps this
    O(n * block) rather than O(n^2) - 4,407 reports would otherwise be 9.7M pairs.
    """
    norm = [normalise(r) for r in reports]
    toks = [n.split() for n in norm]
    shin = [_shingles(t) for t in toks]

    parent = list(range(len(reports)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j):
        a, b = find(i), find(j)
        if a != b:
            parent[max(a, b)] = min(a, b)

    exact = defaultdict(list)
    for i, n in enumerate(norm):
        exact[hashlib.md5(n.encode()).hexdigest()].append(i)
    for group in exact.values():
        for j in group[1:]:
            union(group[0], j)

    blocks = defaultdict(list)
    for i, t in enumerate(toks):
        blocks[" ".join(t[:block_tokens])].append(i)
    for group in blocks.values():
        for a in range(len(group)):
            for b in range(a + 1, len(group)):
                i, j = group[a], group[b]
                if find(i) == find(j):
                    continue
                si, sj = shin[i], shin[j]
                if not si or not sj:
                    continue
                inter = len(si & sj)
                if inter / (len(si) + len(sj) - inter) >= threshold:
                    union(i, j)

    roots = {}
    out = np.empty(len(reports), dtype=np.int64)
    for i in range(len(reports)):
        r = find(i)
        out[i] = roots.setdefault(r, len(roots))
    return out


def stratified_group_folds(groups, labels, n_folds=5, seed=0):
    """Iterative stratification over groups (Sechidis et al. 2011, simplified).

    `labels` is (n, n_labels) with NaN allowed. Every row of a group goes to the
    same fold. Groups are placed largest first, each into the fold currently most
    short of the label it is richest in.
    """
    groups = np.asarray(groups)
    Y = np.nan_to_num(np.asarray(labels, dtype=float))
    uniq, inv = np.unique(groups, return_inverse=True)
    n_lab = Y.shape[1]

    counts = np.zeros((len(uniq), n_lab))
    sizes = np.zeros(len(uniq), dtype=np.int64)
    for g in range(len(uniq)):
        m = inv == g
        counts[g] = Y[m].sum(0)
        sizes[g] = int(m.sum())

    rng = np.random.default_rng(seed)
    order = np.lexsort((rng.random(len(uniq)), -counts.sum(1), -sizes))

    want = counts.sum(0) / n_folds
    have = np.zeros((n_folds, n_lab))
    fold_size = np.zeros(n_folds, dtype=np.int64)
    gfold = np.empty(len(uniq), dtype=np.int64)

    for g in order:
        deficit = want - have
        if counts[g].sum() > 0:
            score = (deficit * counts[g]).sum(1) if deficit.ndim > 1 else deficit @ counts[g]
        else:
            score = -fold_size.astype(float)
        best = np.flatnonzero(score == score.max())
        f = best[np.argmin(fold_size[best])]
        gfold[g] = f
        have[f] += counts[g]
        fold_size[f] += sizes[g]
    return gfold[inv]
