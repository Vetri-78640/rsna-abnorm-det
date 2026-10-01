---
type: experiment
updated: 2026-10-02
status: done
sources: [src/lexicon_base.py:329-334, data/train.csv, tests/test_synovitis_backoff.py]
---

# E006 Synovitis fill from Effusion: already implemented, and already paying

The targeted fill that the forum reported as worth +0.0093 is already in our
lexicon as `FEATURES['synovitis_backoff']`, on by default. Measured against the
gold 58 it is worth **+0.0377 Synovitis AUC and +0.0031 macro**. No variant of its
formula is distinguishable from any other at this sample size, so there is nothing
left to tune here with a regex. [Certain]

## Hypothesis

Synovitis is the finding reports are most often silent about, and silence is
uninformative for it: P(gold positive | silent) = 0.34 against 0.76 when the report
speaks. Filling those undecided cells from the Effusion field should help, since
effusion and synovitis co-occur. See [[not-addressed]].

## What was already there

`lexicon_base.extract` ends with a block that fires only when Synovitis has
neither a positive nor a negative match:

```python
prior = 0.3 + 0.3 * max(0.0, (eff - 0.5) / 0.45) + 0.06 * min(proxy, 3)
out['Synovitis'] = min(0.72, prior)
out['Synovitis__conf'] = 0.18
```

`proxy` counts positive clauses matching `SYNOVIAL_PROXY` - bursitis, Hoffa, plica,
capsule, pannus, the synovial stems in nine languages.

## Result

Over all 4,407 training studies, toggling the flag with the lexicon patch applied:

| | Synovitis AUC | macro AUC |
|---|---|---|
| backoff off | 0.6714 | 0.8594 |
| **backoff on** | **0.7091** | **0.8625** |

It fires on **3,841 of 4,407 studies (87.2%)**, which is our own undecided rate and
matches the 83.7% the forum reported for an LLM labeller. 41 of the 58 gold studies
are undecided, and on those P(gold Synovitis) = 0.34 against 0.76 on the 17 decided
ones - reproducing the forum's table from our own data. [Certain]

## Can the formula be tuned?

No, not on this ruler. Seven variants, gold AUC over all 58:

| variant | gold Synovitis AUC | undecided-only |
|---|---|---|
| no backoff | 0.6714 | 0.5000 |
| effusion only | 0.6935 | 0.5489 |
| proxy only | 0.6941 | 0.5503 |
| **current formula** | **0.7091** | **0.5833** |
| unclipped effusion slope | 0.7103 | 0.5860 |
| no cap | 0.7115 | 0.5833 |
| heavier proxy weight | 0.7174 | 0.6124 |
| raw effusion score | 0.6219 | 0.5556 |

Hanley-McNeil standard error at AUC 0.71 on 27 positives and 31 negatives is
**0.069**, so two variants are only distinguishable if they differ by **0.191**.
The entire spread is 0.055. "Heavier proxy weight" looks best and that ranking is
noise; adopting it would be fitting 41 gold cells. [Certain]

## Verdict

**Issue closed as already done, not as worth doing.** The feature exists, it is
measurably positive, and it is now pinned by `tests/test_synovitis_backoff.py` -
deleting the block fails five of its seven tests.

The real version of this question needs a labeller that can answer "not addressed"
as a first-class output, where undecided is a category rather than an absence of
regex matches. That is the LLM label key, not more regex. [Likely]

Related: [[not-addressed]], [[E001-lexicon-patch]], [[label-premise]]
