> **Raw source.** Verbatim external material - forum transcriptions or research
> agent output. Never edited to fix a claim; corrections go in the wiki pages.

# What other teams and the host have established

Sourced from the competition discussion forum, read 2026-09-10. These are
**reported** results, not reproduced here, except where marked as our own
measurement. They are kept separate from `FINDINGS.md` because that file is
specifically defects in the public notebook, reproduced by executing it.

The forum cannot be reached programmatically: the Kaggle CLI has no discussions
command, the internal forums API returns `403 Permission 'forums.get' was denied`
to an API token, and the pages render client-side so WebFetch sees only a title.
Everything below was transcribed by hand. Future sessions should not waste turns
re-attempting this.

Host is **Po-Hao "Howard" Chen**, RSNA. His threads carry a COMPETITION HOST tag.

---

## Host ruling: commercially hosted LLMs are permitted

Thread "Use of Commercially Hosted LLMs", pinned, host-authored.

> Use of commercially hosted LLMs and other external inference services is
> permitted, provided that the service and method of use otherwise comply with
> the Competition Rules, including requirements that external data, models,
> software, and associated tools be reasonably accessible to all participants and
> of minimal cost.
>
> In other words, for purposes of this competition, submitting Competition Data,
> including report text, to an external LLM or API for inference or other
> computational processing (for example, extracting labels from reports) will not,
> by itself, be considered prohibited PRIVATE SHARING of Competition Data outside
> the Team.

Section 2.6.b, EXTERNAL DATA AND TOOLS. The PRIVATE SHARING clause targets
sharing with other *participants*, not with an inference service. The host
reserves the right to rule a particular service prohibitively costly.

[Certain] This settles the largest open question in `extras.md`. Both routes -
a hosted API and local open weights - are available. The earlier conclusion in
this repo that only Qwen-class open weights were safe was wrong.

Also relevant, quoted from the rules in the same thread:

> In the event that input data or pretrained models with an incompatible license
> are used to generate your winning solution, you do not need to grant an open
> source license... for that data and/or model(s).

So an incompatible upstream licence does not block the CC-BY-NC winner grant.

[Unresolved] Whether click-through research-use datasets (MRNet, fastMRI+, OAI,
SKM-TEA) count as "equally accessible at no cost". Asked in the thread "Rules
clarification: external knee-MRI datasets...". No host answer as of reading.

---

## Host: report-image disagreement is by design

Thread "Possible inconsistencies between MRI reports and provided labels",
23 votes. An auditor hand-checked 20 of the 58 gold studies against their
reports, 240 decisions:

```
overall agreement  82.5%     TP 68  FP 25  FN 17  TN 130
positive predictive agreement  73.1%
positive recall                80.0%
```

Examples raised: a report stating "Synovitis of left knee and massive joint
effusion" labelled Effusion 1 / Synovitis 0; a German report saying
"Baker-Zyste" labelled Baker's 0; a Turkish report saying "lateral meniscus is
normal" labelled Lateral Meniscus tear 1.

The host replied, and did not call any of it an error:

> You have encountered a major design choice in this challenge, and what we
> believe makes the challenge instructive, real-world, and difficult.

[Likely] So the gold labels are image-derived and deliberately allowed to
contradict the report. **Any report-derived labeler has a hard ceiling near 82%
agreement**, and no amount of labeler improvement passes it.

Related, from Tom Aindow (rank 47 at the time): the image labels sometimes flout
the competition's own stated heuristics - a report reading "small effusion" with
Effusion set to 1, though the stated rule is "moderate or large". Near the
decision boundary the annotators simply disagree. His inference is worth keeping:
asking an LLM for confidence in a *diagnosis* may return its confidence in
*applying a heuristic to a report*, which is a different and better-behaved
quantity than the one being scored.

---

## The diagnostic that beats our gate notebook

Tucker Arrants, rank 12 at the time:

> Check how your label extractor performs relative to the 58 provided labels.
> Then check how your image model performs on them. If your image model is not
> beating the label extractor "teacher", there is likely modeling headroom. If
> your image model is beating the label extractor by a large margin, the quality
> of the labels might be holding the image model back.

We already have half of it: our patched lexicon scores **0.8625** on the gold 58.
The `ckpt` arm of `notebooks/RUN_THIS_encode_and_gate.ipynb` supplies the other
half at no extra cost.

**This reverses a reading recorded earlier in this repo.** An earlier session
argued that because the lexicon scores 0.862 while the checkpoints score 0.939,
the lexicon must be a soft ceiling. Tucker's reading of the same fact is the
opposite: a large excess means the labels are what is binding. Both are
consistent with the numbers; his is the more useful one, because it is
falsifiable by a comparison already in the notebook.

---

## LLM labels beat regex labels, but by less than it looks

Thread "'Not addressed' is a label too - what we learned reading 4,407 knee
reports with an LLM", 38 votes.

```
their regex / lexicon extraction   0.8136   macro AUC vs the gold 58
their LLM reading the same reports 0.8780
OUR patched lexicon                0.8625   <- measured in this repo
```

[Certain] So the gap **we** would close is +0.0155, not their +0.064. Their regex
baseline is materially worse than the one in `src/`.

[Certain] The same authors state that on a 58-study ruler, differences below
roughly **0.02 macro are not measurable**. Their own headline result therefore
does not clear their own stated resolution, and neither does our +0.0155.

### Their actual finding, which is better than the headline

They asked the labeller for an explicit "the report does not address this" option
mapping to 0.5. **25.4% of all label cells came back at exactly 0.5**, wildly
unevenly:

| finding | gold AUC | "not addressed" |
|---|---|---|
| Synovitis | 0.678 | 83.7% |
| Baker's | 0.946 | 48.2% |
| Fracture | 0.793 | 42.9% |
| ACL | 0.993 | 8.3% |
| Medial Meniscus | 0.954 | 5.5% |

And silence means a different thing for each finding:

| finding | P(gold+) when the report is SILENT | when it SPEAKS |
|---|---|---|
| Synovitis | 0.34 | 0.76 |
| PF OA | 0.21 | 0.41 |
| Baker's | 0.03 | 0.44 |
| Medial OA | 0.00 | 0.36 |

Silence about a Baker's cyst is a negative label. Silence about synovitis is
uninformative. Treating them alike is worse than leaving the gaps in.

**One targeted fix paid; the blanket version did not.** Radiologists report
effusion readily and synovitis rarely, and the two co-occur
(P(syn|eff) = 0.63 vs P(syn|no eff) = 0.22). The Effusion field predicts gold
Synovitis (0.7115) better than the Synovitis field does (0.6780). Filling only
Synovitis's undecided cells from Effusion moved the key 0.8780 to **0.8873**.
Learned ridge imputation across all twelve moved it to 0.8805 - worse than the
targeted version.

Public LLM label sets, in order of publication: Pilkwang Kim
(`rsna-knee-llm-labels`, first, 2026-08-06), barun2104, lixin73, dreaddevelopment
(`rsna-knee-labels`), stevenleehans.

---

## Encoder capacity is a dead lever

Thread "Scaling the encoder bought us nothing (+0.0011)", 12 votes.

```
dinov2-small (control)  22M params  0.436 s/step  OOF 0.7931
dinov2-base             87M params  1.710 s/step  OOF 0.7942
                                    delta +0.0011, measured noise floor 0.0020
```

Only 5 of 12 labels moved in Base's favour, and the whole macro gain rests on
MCL, their least reliable label. For contrast, their crop-geometry fix paid
+0.0059 and moved **10 of 12**. That ratio is the tell: a real effect lifts most
labels, noise lifts about half.

### The pixel cache, which is what changed our plan

```
4,407 studies x 6 slots x 9 slices x 224 x 224 uint8 = 11.12 GiB
```

Decode was 55 min per run, 72% of a fold. Persisting it removes that permanently
and fits on a laptop. One fold: 76 min on a Kaggle T4, 67 min on an M4 Pro.
Notebook: `stevenleehans/rsna-knee-500gb-to-11gib-cpu-pixel-cache`.

### A preprocessing trap worth more than the result

**A checkpoint carries its own normalisation contract.** RAD-DINO is greyscale
mean 0.5307 / std 0.2583 at 518 px, not ImageNet constants at 224. Hardcoding the
ImageNet buffers fed it inputs shifted ~0.2 std with a 12% scale error, and it
produced a plausible losing curve - no error, no warning, an 11-hour experiment
supporting a false conclusion about the exact hypothesis being tested. Read
`preprocessor_config.json` before trusting any encoder swap.

Our encode notebook is safe here only because it reuses the raptor checkpoint's
own `NORM='imagenet'`, which is correct for that checkpoint.

Three more of their measurement failures, all cheap to repeat:

- **Silent backbone fallback.** Off Kaggle there is no `/kaggle/input`, the
  weights lookup returned None, and the builder fell back to ResNet-18 - which
  trains fine and logs a plausible score. Any run that does not print which
  backbone it loaded is not evidence about that backbone.
- **The narrow probe.** Timing training steps predicted 0.64 h/fold; the fold
  took 1.11 h, because the probe ignored validation, memory-mapped reads and
  augmentation. Their third consecutive underestimate from a narrow probe. Treat
  a probe as go/no-go, never as a schedule.
- **A tool that answered the wrong question.** Their comparison script printed the
  absolute difference under the heading NOISE FLOOR, because it was written to
  compare two seeds of one config. Fed a control and a treatment, it reported
  "floor = 0.0011" for a result sitting under the real floor of 0.0020.

---

## Where the community thinks the bottleneck is

Thread "What is the real bottleneck now: labels, image pipeline, or model
capacity?", 11 votes, 11 comments. The framing, from the author:

- Single DINO-based models already reach around **0.91-0.92**.
- Increasing encoder size does not necessarily improve CV.
- Several people report meaningful gains from **crop geometry, resolution and
  slice selection**.
- Most training labels are report-derived, and label quality may itself impose a
  ceiling.

> The emerging lesson is that improving what the model *sees* and what we *teach
> it* may be more important than simply using a larger backbone.

---

## Threads not yet read

Worth transcribing if a question comes up that they would settle:

- "Best single-model score" (39 votes, 65 comments) - the single-model ceiling,
  directly relevant to the efficiency prize
- "Metric edge cases: single-class label columns, and corrupted DICOMs in the
  test set" - submission robustness
- "9h runtime question" - our hard constraint
- "0.932 LB within one day. Tested for DICOM metadata shortcut" - leakage check
- "Knee Abnormality Detection AI Challenge Overview" (host, 69 votes)
- "How is ... Effusion graded?" - the severity thresholds behind the labels
