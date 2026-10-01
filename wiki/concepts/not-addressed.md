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

## Synovitis is the only label where the report really under-calls

**Corrected 2026-10-02.** An earlier version of this page claimed Fracture was a
second silence problem, on the grounds that reports call fracture in 7.1% of studies
while 31% of gold studies are fracture-positive - a 4.4x gap. **That comparison is
invalid and the conclusion from it was wrong.**

The 7.1% is the rate over all 4,407 studies. The 31% is the rate over the 58 gold
studies, which are trauma-enriched: our extractor calls fracture on 6.7% of non-gold
studies and **36.2%** of gold ones, a **5.4x enrichment**. The gap was almost
entirely the sampling of the gold set. gchauhan's forum post makes the same
comparison and our numbers reproduced it exactly, which is why it survived a check -
**reproducing a number is not validating the inference drawn from it.**

Compared like with like, on the same 58 studies:

| finding | report says POSITIVE (on the 58) | gold positive | direction |
|---|---|---|---|
| **Synovitis** | **29.3%** | **46.6%** | **under-calls, 1.6x** |
| Lateral Meniscus | 43.1% | 39.7% | slight over-call |
| Medial OA | 27.6% | 25.9% | slight over-call |
| Fracture | 36.2% | 31.0% | **over-calls** |
| Contusion | 56.9% | 32.8% | over-calls 1.7x |
| Effusion | 84.5% | 60.3% | over-calls 1.4x |

**Synovitis is the only one of the twelve that under-calls.** Everything else
over-calls, consistent with the lexicon's known bias - 77% cell agreement, 136 false
positives against 24 false negatives. That is why the targeted Synovitis fill pays
and a blanket one does not.

Fracture's silence is also informative rather than uninformative:
P(gold+ | report silent) = **0.16** against P(gold+ | report speaks) = **0.50**, with
a base rate of 0.31. By the rule below, that makes Fracture a *worse* imputation
candidate than Synovitis, not a better one. Its gold AUC is already 0.8326. [Certain]

dreaddevelopment's audit gives the mechanism for the one real case: **12 of 27
expert-positive Synovitis studies had no explicit Synovitis statement at all.** That
label is not recoverable from those reports by any extractor.

## Rule

Ask the labeller for "I don't know" as a first-class answer. Impute only where
silence is uninformative.

The regex route is finished. Doing better needs a labeller that emits "not
addressed" as a category rather than an absence of matches. [Likely]

Related: [[label-premise]], [[public-datasets]], [[E006-synovitis-fill]]
