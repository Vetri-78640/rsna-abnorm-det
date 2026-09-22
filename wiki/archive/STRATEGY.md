> **Archive, frozen 2026-09-10.** Dated long-form reasoning, kept as the record of
> what was believed and when. Some claims here have since been corrected - the
> maintained pages in `wiki/` win. Start at `wiki/overview.md`.

# Strategy - what to build, and why

Written 2026-09-10, 42 days to the final submission. This file holds the
reasoning behind the plan. `PLAN.md` holds the schedule; this holds the argument.
If a number here is wrong, the plan is wrong, so every claim carries its source.

---

## Where we stand

[Certain, `kaggle competitions leaderboard`, 2026-09-10 03:06 UTC]

```
3,434 teams | top 0.954 (5 teams) | median 0.906
us: rank 193, score 0.940, 3 submissions

>= 0.954  rank   5
>= 0.950  rank  16      <- prize money is top 10
>= 0.945  rank  58
>= 0.940  rank 320      (we hold 193 on the earlier-submission tiebreak)
```

[Certain] Public notebooks cap around **0.942**
(`prvsiyan/the-bee-s-knees-final-rsna-push`). We are at the public ceiling. The
0.012 to the top is private work, not a notebook to copy.

---

## Is the gap real? Partly.

Macro-AUC standard error on this test set, Hanley-McNeil at AUC 0.94, using our
lexicon's fire rate on the 4,349 non-gold studies as the prevalence estimate
(gold is trauma-enriched, so gold prevalence would be the wrong input):

| set | n | macro-AUC SE, independent | fully correlated |
|---|---|---|---|
| full test | 1,322 | 0.0026 | 0.0090 |
| public LB at 50% | 661 | 0.0037 | 0.0128 |
| public LB at 30% | 396 | 0.0048 | 0.0165 |

Label errors are correlated across the twelve targets, so the truth sits between
the columns, nearer the right for the OA and effusion families.

Two conclusions that change what we do:

1. **The top-5 spread is 0.954 to 0.951 - 0.003, inside one SE.** The ordering at
   the top is not resolved by the public leaderboard.
2. **Submission counts at the top are 42 to 119. Ours is 3.** At 5/day over 40
   days, 119 submissions is enough to fit the public sample. [Likely] some of the
   0.012 gap is public-LB overfit that will not survive to private.

That is a real and free edge, and it dictates one rule: **select the two final
submissions by CV, never by public LB.** It is also why no number in this file is
promised - the instrument cannot resolve what would be promised.

---

## The number that inverted the plan

An earlier session concluded retraining was infeasible. That was arithmetic on
CoAtNet-rmlp-2 at 384 px over 64 slices: ~57 h for one arm on a T4, against
30 h/week. Correct for that configuration, and wrong as a general claim.

The competition discussion supplied the right figure. After slice selection,
windowing, the physical crop and a resize to 224 px, the entire visual input is:

```
4,407 studies x 6 slots x 9 slices x 224 x 224 uint8 = 11.12 GiB
one fold on a Kaggle T4                              = 76 min
```

So a **5-fold experiment is about 6.5 hours**. 30 h/week is 4-5 experiments a
week, roughly 25 before the deadline. That is a research budget, not a single
shot, and it means we should be training rather than only blending.

The decode is what costs, not the training, and it is paid once: persisting the
array removes 55 min per run, which was 72% of a fold.

---

## Levers, ranked by measured effect only

Nothing here is an estimate from a research agent. Each row was measured by
somebody, on their own cross-validation, and reported with a noise floor.

| lever | effect | labels moved | source |
|---|---|---|---|
| crop geometry / slice selection | **+0.0059** | 10 of 12 | stevenleehans, own CV |
| "not addressed" handling on the label key | +0.0093 | - | same team, vs gold 58 |
| LLM key over regex key | +0.0155 vs **our** lexicon | - | computed in this repo |
| encoder ViT-S to ViT-B | +0.0011 vs a 0.0020 floor | 5 of 12 | two teams, **null** |

"Moved 10 of 12" is the tell. A real effect lifts most labels; noise lifts about
half. That single column separates the first row from the last.

### On DINOv3

The field does use it - Family A of the public notebook is
`vit_small_patch16_dinov3.lvd1689m`, confirmed in our own run log. But **making
it bigger is a measured null by two independent teams.** The backbone is the
default, not the lever. Do not spend GPU hours there.

### Why our modules line up with the top lever

`src/sampling.py` and `src/geometry.py` are exactly "crop geometry and slice
selection", and ours is more principled than anything public: per-label
anatomical bands, stack ends never discarded, a meniscal-body stride chosen so
the bow-tie sign stays learnable. That is not luck - the earlier research pointed
at this before the community measured it.

This is the thesis of the whole plan.

---

## The plan, in one sentence

**Train one model with our slice selection, on the best public LLM label key, and
blend it into the public pack as a genuinely decorrelated member.**

The supporting argument, in three parts:

1. **The public pack is correlated with itself.** Arm 2 is arm 0's checkpoint
   with the adjacent-slice triplet reversed. Family C is Family B with a
   different head. Adding a 31st correlated member is worth under 0.001; adding
   one genuinely different member is worth several times that.
2. **We can now afford to make that member ourselves**, at 6.5 h per experiment.
3. **The one thing we have that others do not** is a slice-selection module built
   from the radiology rather than from a grid search, and that is the lever with
   the largest measured effect.

---

## What to expect, honestly

**0.944 to 0.947, rank roughly 30 to 60.** [Guessing, but reasoned:] a
decorrelated single model near 0.92 blended at 0.2-0.3 weight into a 0.940
ensemble is typically worth +0.002 to +0.006 in this kind of setting, and the
sampling ablation is +0.006 on our own CV at best. Those overlap, so they do not
add.

Reaching 0.950 needs several such members, or one model well above 0.92. Neither
is ruled out; neither should be planned around.

**The realistic route into the top ten is not out-scoring the leaders on public.**
It is arriving at 0.946 with no public-LB overfit while part of the 0.951-0.954
group regresses on private. That is not a consolation prize - it is the shape of
most private-leaderboard shakeups, and it is the only route our submission budget
and compute actually support.

---

## Things that would change this file

- If the gate notebook shows the image model far exceeding the label extractor on
  the gold 58, the label lever is bigger than assessed here and week 3 should
  grow. See `wiki/raw/forum.md` for the diagnostic.
- If our sampling ablation lands under +0.002 on our own CV, the thesis is wrong
  and the remaining weeks should go to the efficiency prize, which is a separate
  $18,000 and far less contested.
- If a real submission log shows the pipeline near the 9-hour limit, adding a
  member stops being free and the whole plan gets priced against runtime.
