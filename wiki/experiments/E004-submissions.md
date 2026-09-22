---
type: experiment
updated: 2026-09-22
status: current
sources: [kaggle competitions submissions]
---

# E004 - Every leaderboard submission

Our best public score is 0.941, but the field inflated so fast that it fell from
rank 193 to 812 in twelve days without regressing.

| date (UTC) | public LB | notebook |
|---|---|---|
| 2026-09-08 | 0.939 | bend-the-knee-to-the-dinosaurs |
| 2026-09-09 | 0.939 | same |
| 2026-09-09 | 0.940 | a newer public model |
| 2026-09-10 | **0.941** | public model |
| 2026-09-22 | pending | presumably [[notebook-0943]] |

## Where that places us

| date | teams | top | 0.950 is rank | us |
|---|---|---|---|---|
| 2026-09-10 | 3,434 | 0.954 | 16 | 193 @ 0.940 |
| **2026-09-22** | **4,143** | **0.958** | **47** | **812 @ 0.941** |

**The field inflated fast.** We fell 600 places in 12 days without regressing. The
public ceiling rose with it. Every public-notebook improvement is shared by
hundreds of teams at once, which is why blending alone cannot win.

Re-pull: `kaggle competitions leaderboard -c rsna-knee-abnormality-detection --download`.
