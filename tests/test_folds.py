"""Tests for src/folds.py. No data, no GPU."""
import sys, pathlib
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import folds as F


def test_normalise_ignores_formatting_and_accents():
    a = F.normalise("  Rotura del MENISCO interno.\n\n(grade 3)  ")
    b = F.normalise("rotura del menisco interno grade 3")
    assert a == b == "rotura del menisco interno grade 3"


def test_exact_duplicates_share_a_cluster():
    r = ["ACL tear noted.", "acl  tear   noted!!", "Normal study.", "ACL tear noted."]
    c = F.report_clusters(r)
    assert c[0] == c[1] == c[3], "formatting-only differences must cluster"
    assert c[2] != c[0]


def test_one_character_difference_still_clusters():
    """The defect this module exists for: the public notebook hashes the report, so
    a single changed character puts a near-duplicate in a different fold."""
    base = "Findings show a horizontal tear of the posterior horn of the medial meniscus with mild joint effusion and no ligament injury"
    c = F.report_clusters([base, base + "."])
    assert c[0] == c[1]


def test_distinct_reports_do_not_cluster():
    a = "Complete tear of the anterior cruciate ligament with bone contusion"
    b = "Normal knee study with no meniscal or ligamentous abnormality seen"
    assert len(set(F.report_clusters([a, b]).tolist())) == 2


def test_groups_never_split_across_folds():
    rng = np.random.default_rng(0)
    groups = np.repeat(np.arange(60), 3)
    y = (rng.random((180, 12)) < 0.3).astype(float)
    f = F.stratified_group_folds(groups, y, n_folds=5, seed=0)
    for g in np.unique(groups):
        assert len(set(f[groups == g].tolist())) == 1, "a group leaked across folds"


def test_every_fold_gets_some_of_each_label():
    rng = np.random.default_rng(1)
    groups = np.arange(400)
    y = (rng.random((400, 12)) < 0.15).astype(float)
    f = F.stratified_group_folds(groups, y, n_folds=5, seed=0)
    for k in range(5):
        assert y[f == k].sum(0).min() > 0, "a fold has zero positives for some label"


def test_stratification_beats_random_on_a_rare_label():
    """A 3%-prevalence label is where naive splitting fails."""
    rng = np.random.default_rng(2)
    groups = np.arange(600)
    y = np.zeros((600, 12))
    y[:, 0] = (rng.random(600) < 0.03).astype(float)
    y[:, 1:] = (rng.random((600, 11)) < 0.3).astype(float)
    f = F.stratified_group_folds(groups, y, n_folds=5, seed=0)
    ours = np.array([y[f == k, 0].sum() for k in range(5)])
    rnd = np.array([y[rng.integers(0, 5, 600) == k, 0].sum() for k in range(5)])
    assert ours.std() <= rnd.std(), f"stratified spread {ours.std()} worse than random {rnd.std()}"
    assert ours.min() > 0


def test_deterministic_for_a_seed():
    groups = np.arange(100)
    y = (np.random.default_rng(3).random((100, 12)) < 0.2).astype(float)
    a = F.stratified_group_folds(groups, y, 5, seed=7)
    b = F.stratified_group_folds(groups, y, 5, seed=7)
    assert (a == b).all()


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"  pass  {name}")
            except Exception as exc:
                fails += 1; print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{fails} failure(s)")
    sys.exit(1 if fails else 0)
