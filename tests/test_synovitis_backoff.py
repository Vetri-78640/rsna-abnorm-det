"""The Synovitis-from-Effusion fill already exists in lexicon_base as
FEATURES['synovitis_backoff']. It fires on 87.2% of studies and is worth +0.038
Synovitis AUC on the gold 58, so these tests pin its contract against accidental
removal. See wiki/concepts/not-addressed.md and wiki/experiments/E006.
"""
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import lexicon_base as lex

SILENT = "MRI of the right knee. Large joint effusion. Menisci intact."
SPOKEN = "MRI of the right knee. Synovial thickening and enhancement. No effusion."
DRY = "MRI of the right knee. No joint effusion. Menisci intact."


def _extract(report, backoff=True):
    old = lex.FEATURES['synovitis_backoff']
    lex.FEATURES['synovitis_backoff'] = backoff
    try:
        return lex.extract(report)
    finally:
        lex.FEATURES['synovitis_backoff'] = old


def test_backoff_is_on_by_default():
    assert lex.FEATURES['synovitis_backoff'] is True


def test_fires_only_when_the_report_is_silent_on_synovitis():
    """A report that mentions synovium is scored, not imputed -- the whole point
    of the targeted fill is that it touches undecided cells only."""
    spoken = _extract(SPOKEN)
    assert spoken['Synovitis__npos'] + spoken['Synovitis__nneg'] > 0
    assert _extract(SPOKEN, backoff=False)['Synovitis'] == spoken['Synovitis']


def test_effusion_raises_an_undecided_cell():
    silent = _extract(SILENT)
    assert silent['Synovitis__npos'] == 0 and silent['Synovitis__nneg'] == 0
    assert silent['Synovitis'] > _extract(SILENT, backoff=False)['Synovitis']


def test_an_undecided_cell_stays_ordered_by_effusion():
    """P(gold synovitis) given silence is 0.34 against 0.76 when the report
    speaks, so the fill must never push a silent study above a spoken one."""
    silent = _extract(SILENT)
    assert silent['Synovitis'] > _extract(SILENT, backoff=False)['Synovitis']
    assert silent['Synovitis'] < _extract(SPOKEN)['Synovitis']


def test_no_effusion_no_proxy_leaves_the_floor():
    dry = _extract(DRY)
    assert dry['Synovitis__npos'] == 0 and dry['Synovitis__nneg'] == 0
    assert abs(dry['Synovitis'] - 0.3) < 1e-9


def test_the_fill_is_capped():
    """0.72 keeps every imputed cell below a directly observed positive."""
    hot = "Massive tense joint effusion with marked suprapatellar bursitis, plica and capsular distension."
    out = _extract(hot)
    assert out['Synovitis__npos'] == 0 and out['Synovitis__nneg'] == 0
    assert out['Synovitis'] > _extract(hot, backoff=False)['Synovitis']
    assert out['Synovitis'] <= 0.72


def test_confidence_is_marked_low_when_imputed():
    assert _extract(SILENT)['Synovitis__conf'] == 0.18
    assert _extract(SPOKEN)['Synovitis__conf'] > 0.18


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
