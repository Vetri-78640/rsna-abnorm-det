> **Archive, frozen 2026-09-10.** Dated long-form reasoning, kept as the record of
> what was believed and when. Some claims here have since been corrected - the
> maintained pages in `wiki/` win. Start at `wiki/overview.md`.

# Extras - competition mechanics, rules, and things that bite

Everything that is not research or code but changes what you can do. Sourced from
the competition Overview, Dataset Description and Official Rules.

---

## Timeline

| date | event |
|---|---|
| 2026-07-30 | start |
| **2026-10-15** | **entry deadline** - rules must be accepted before this to compete |
| **2026-10-15** | **team merger deadline** |
| **2026-10-22** | **final submission deadline** |
| 2026-11-05 | winners' deadline for training code, video, method description |

All at 23:59 UTC. As of 2026-09-08 that is about six weeks to final submission.

**The entry deadline matters even if you are not ready.** Accepting the rules is
free and reversible in effect; missing 15 October means you cannot compete at all
regardless of what you have built. Do it now if it is not done.

---

## Submission mechanics

- **5 submissions per day.** At ~1300 test studies a macro-AUC delta under about
  0.003 is noise, so most submissions cannot resolve what you are choosing
  between. Budget them for verification, not for search.
- **2 final submissions** selected for private-leaderboard judging.
- **9-hour notebook runtime limit.** The public notebook already sets
  `TIME_BUDGET = 8.0 * 3600`, leaving roughly an hour of margin. See
  `scripts/budget_model.py`.
- Public leaderboard is a sample of the test set; private determines placing.
- Ties broken by earliest submission.

## Submission format

```
StudyInstanceUID,ACL,MCL,Medial Meniscus,Lateral Meniscus,Medial OA,Lateral OA,PF OA,Effusion,Synovitis,Baker's,Contusion,Fracture
<uid>,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5
```

Column order is fixed and the notebook validates it. Note the apostrophe in
`Baker's` and the spaces in the multi-word names - both are easy to break when
round-tripping through a DataFrame.

The notebook writes a 0.5-everywhere fallback submission *first*, then overwrites
it on success. Keep that pattern. A failed run that leaves a valid file scores
0.5 macro; a failed run that leaves nothing scores zero.

---

## Prizes

**Main leaderboard, $54,000:** 1st $9,000, 2nd $7,000, 3rd $6,500, 4th $6,000,
5th $5,500, 6th-10th $5,000 each.

**Efficiency track, $18,000:** 1st $7,000, 2nd $6,000, 3rd $5,000.

[Unresolved] These sum to $72,000. `kaggle competitions list` reports $77,000 for
this competition. The $5,000 difference is unaccounted for - check the Overview
page rather than trusting either number.

The efficiency track is a genuinely separate shot. A distilled single-student
model at a fraction of the ensemble's compute is a plausible entry, and it shares
machinery with the relabelling loop.

---

## Team rules

- Maximum team size **5**.
- Mergers allowed until 15 October, and the combined team's total submission count
  must not exceed `5 × days_running` at merge time. Burning submissions early
  restricts who you can merge with later.
- One Kaggle account per person. Submitting from multiple accounts is
  disqualification.
- **No private code sharing outside a team.** Sharing publicly on the competition
  forum or in a notebook is fine and is deemed to license it openly.

---

## Data rules

- **Competition and commercial use permitted**, subject to the RSNA MIRA licence
  at http://rsna.org/mira-license.
- Do not redistribute the competition data to anyone who has not accepted the rules.
- **External data is allowed** if publicly available and "equally accessible to
  all Participants at no cost", or meeting a "Reasonableness Standard" on cost
  and accessibility.

**[Certain] Commercially hosted LLMs ARE permitted.** Host ruling, Po-Hao
"Howard" Chen, pinned thread "Use of Commercially Hosted LLMs":

> Use of commercially hosted LLMs and other external inference services is
> permitted, provided that the service and method of use otherwise comply with
> the Competition Rules... submitting Competition Data, including report text, to
> an external LLM or API for inference or other computational processing (for
> example, extracting labels from reports) will not, by itself, be considered
> prohibited PRIVATE SHARING of Competition Data outside the Team.

Section 2.6.b, EXTERNAL DATA AND TOOLS. The PRIVATE SHARING restriction targets
sharing with other *participants*, not with an inference service. Conditions
still bind: "reasonably accessible to all participants and of minimal cost", and
the host reserves the right to rule a particular service prohibitively costly.

This kills the earlier reading in this file that only Qwen-class open weights
were safe. Both routes are open. Note also, from the rules:

> In the event that input data or pretrained models with an incompatible license
> are used to generate your winning solution, you do not need to grant an open
> source license... for that data and/or model(s).

So an incompatible upstream licence does not block the CC-BY-NC winner grant.

**[Likely, still unresolved by a host] The external-data trap.** MRNet, OAI, SKM-TEA and fastMRI are all
non-commercial research-only behind registration-gated DUAs. "Freely and equally
available to all participants" arguably excludes a gated DUA. The winner licence
is CC-BY-NC 4.0, so the non-commercial part aligns, but Gemma and Llama community
licences impose use restrictions CC-BY-NC does not - **Qwen (Apache 2.0) is the
only fully safe LLM choice**. Post on the external-data thread before depending
on any of these. This is a question for the organisers, not for inference.

---

## Winner obligations

If you place, you must deliver training code, inference code, **model weights as a
public Kaggle dataset**, and an environment spec (a `requirements.txt` plus either
a Kaggle image reference or a Dockerfile). The method description must be
reproducible from reading it. Everything is licensed CC-BY-NC 4.0.

**Plan for this from the start.** Keep training code runnable and seeds fixed. A
solution you cannot reproduce is a solution you cannot claim.

---

## Dataset facts that bite

- **1,322 studies in the hidden test set.** [Certain] the notebook prints it
  while sizing its cache, even on a 3-study commit run.
- **The GPU is 2x Tesla T4, sm_75, 15 GiB, no native bf16.** [Certain] from the
  run log.
- **819,640 DICOM files, 569.76 GB.** Do not download the pixel data unless you
  are training. Every tier-0 question is answerable from four small CSVs -
  `scripts/fetch_metadata.sh` pulls only those.
- **86 metadata tags survive** the organisers' allowlist. Which 86 is not
  published; `scripts/audit_headers.py` finds out. Several recommendations branch
  on whether `InversionTime`, `MagneticFieldStrength`, `SpacingBetweenSlices`,
  `AcquisitionMatrix`, `PixelBandwidth` and `ImageLaterality` survived.
- **Mixed transfer syntaxes** - uncompressed Explicit VR Little Endian, JPEG
  Lossless, JPEG 2000, Implicit VR Little Endian. Decode speed varies by an order
  of magnitude between them, and this is probably the runtime bottleneck.
- **Series are 20-45 slices, median 30, with a long tail to a few hundred.** Code
  that assumes a bounded slice count will blow its memory budget on the tail.
- **`Report` exists in train only.** Any pipeline that feeds report text at
  inference is a dead end.
- **Prevalence differs between train, public LB and private LB**, stated
  explicitly by the organisers. Do not tune anything prevalence-dependent. AUC is
  prevalence-insensitive per label, which is a mercy.
- **Only 58 of 4,407 training studies carry labels**, all twelve or none.
  [Certain, measured] The other 4,349 carry a report and nothing else.
- **Those 58 are trauma-enriched, not a random sample.** [Certain] Fracture fires
  5.2x more often on them than on the rest (p=4e-11). Gold prevalence is not test
  prevalence. See `FINDINGS.md` item 15.
- **`Fat_Suppression` and `Fluid_Sensitive` are identical columns** in every one
  of the 24,371 train and 15 test series. [Certain] Six plane-by-contrast slots
  exist, not twelve. See `FINDINGS.md` item 14.
- **Reports are 39% English.** [Certain] tr 12.0, es 11.9, el 7.3, hr 6.8, de 5.8,
  bg/ru 5.0, nl 3.4, fr 1.8, unknown 6.6. Any report labeler has to be
  multilingual-first, not English-first with fallbacks.
- **Intensities, orientations and resolutions vary across series and studies.**

---

## Failure modes to guard against

1. **Notebook times out.** Write the fallback submission first. Check elapsed time
   against a budget and degrade gracefully (fewer arms, fewer slices) rather than
   dying.
2. **A study has no series metadata, or a series fails to decode.** The public
   notebook catches per-study exceptions and leaves 0.5. Keep that.
3. **Column drift.** `Baker's` with an apostrophe, spaces in names. Validate
   against `sample_submission.csv` columns, not a hard-coded list.
4. **Study identity drift.** Reindex against `test.csv` order and assert the UID
   set matches, as the notebook does in `_v37_validate_submission`.
5. **Weights dataset not attached.** The notebook searches `/kaggle/input` broadly
   and raises a clear error. Hash-verify anything load-bearing.
6. **Internet is off in submission kernels.** Everything - weights, tokenisers,
   packages - must be a mounted dataset. `HF_HUB_OFFLINE=1` and
   `TRANSFORMERS_OFFLINE=1` are set in the public notebook for this reason.

---

## Things I could not verify

Recorded so a future session does not assume they were checked.

**Now settled, from the data:**

1. ~~Gold label count.~~ 58 of 4,407, confirmed from `train.csv`. And the 58 are
   trauma-enriched, which the research did not anticipate.
2. ~~Whether the competition rules are accepted.~~ They are.
   `kaggle competitions list` reports `userHasEntered True`, and all five CSVs
   downloaded without a 403.
3. ~~Language mix.~~ Measured. English is a minority at 39.3%.

**Still open:**

4. **Kaggle discussion threads.** WebFetch cannot read them; they render
   client-side. All forum-derived claims in `wiki/raw/research.md` came from secondary
   sources and should be treated as weaker.
5. **The 86-tag allowlist contents.** Needs actual DICOMs; the competition
   publishes no header CSV, only the five files `fetch_metadata.sh` pulls.
6. **Laterality resolution rate.** Same blocker - `audit_headers.py` needs
   DICOMs and pydicom.
7. **Population per-label prevalence.** Gold is enriched, so the honest estimate
   is the lexicon's fire rate on the 4,349 non-gold studies, discounted for
   over-calling. [Guessing] Fracture 5-8%, not the 3% in the earlier draft.
8. ~~**Where the 9 hours actually go.**~~ Bounded from a commit log: marginal
   20.5 s/study, ~5h33m extrapolated to 1,322 studies, against an 8h budget and a
   9h limit. Family B is 11.0 of those seconds. Still a floor - a commit log runs
   3 studies entirely from page cache. See `FINDINGS.md` item 19.
9. **What the hidden set's cold I/O costs.** The gap between the 5h33m floor and
   the author's 8h budget is unexplained and is probably this. Only a real
   submission log settles it.
10. **Whether three resident checkpoints fit the submission GPU.** The
   study-major loop holds three CoAtNet-rmlp-2 at once instead of one, on a 15 GiB
   T4. It falls back to arm-major automatically on exception, so the downside is
   time, not a failed submission - but that fallback has never fired on real
   hardware.
11. **Whether a competition rerun spends the 30 h/week GPU quota.** At ~6 h a run
   this decides whether the practical submission rate is 5/day or about 4/week.
