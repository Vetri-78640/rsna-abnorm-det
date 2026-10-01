---
type: concept
updated: 2026-10-02
status: current
sources: [forum thread, stevenleehans, src/lexicon_base.py, data/train.csv]
---

# "Not addressed": silence means different things per finding

A quarter of report-derived label cells are "not addressed", and silence is a
negative for some findings but uninformative for others.

When a labeller may answer "the report does not address this", **25.4% of cells**
come back that way - and unevenly: Synovitis 83.7%, Baker's 48.2%, Fracture 42.9%,
ACL 8.3%.

## Silence is a label for some findings and noise for others

| finding | P(gold+) when report is SILENT | when it SPEAKS |
|---|---|---|
| Baker's | **0.03** | 0.44 |
| Medial OA | **0.00** | 0.36 |
| PF OA | 0.21 | 0.41 |
| Synovitis | **0.34** | 0.76 |

Silent Baker's is a negative. Silent synovitis is uninformative.

## What paid, and what did not

- **Targeted:** fill only Synovitis's undecided cells from the Effusion field
  (P(syn|eff) = 0.63 vs 0.22). Key 0.8780 to **0.8873**.
- **Blanket:** learned imputation for all twelve. Key 0.8805 - **worse**.

## Our lexicon already does the targeted version

`lexicon_base.FEATURES['synovitis_backoff']`, on by default, fills Synovitis from
the Effusion field plus a synovial-proxy count whenever the report is silent. It
fires on **87.2%** of studies and is worth **+0.0377 Synovitis AUC, +0.0031 macro**
on the gold 58. Our own undecided rate and conditional probabilities reproduce the
table above from our data: 0.34 silent against 0.76 spoken. [Certain]

No variant of its formula is distinguishable from another at 58 studies - the
Hanley-McNeil resolution is 0.191 and the whole spread across seven variants is
0.055. Tuning it further is overfitting. See [[E006-synovitis-fill]].

## Rule

Ask the labeller for "I don't know" as a first-class answer. Impute only where
silence is uninformative.

The regex route is finished. Doing better needs a labeller that emits "not
addressed" as a category rather than an absence of matches. [Likely]

Related: [[label-premise]], [[public-datasets]], [[E006-synovitis-fill]]
