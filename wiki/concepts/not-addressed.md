---
type: concept
updated: 2026-09-22
status: current
sources: [forum thread, stevenleehans]
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

## Rule

Ask the labeller for "I don't know" as a first-class answer. Impute only where
silence is uninformative.

Related: [[label-premise]], [[public-datasets]]
