# Schema - how this wiki works

Follows Andrej Karpathy's LLM-wiki pattern: raw sources are immutable, the wiki is
the maintained layer, and this file says how to maintain it.

## Layers

| layer | where | rule |
|---|---|---|
| raw sources | `docs/`, `logs/`, `*.ipynb`, `data/` | immutable record; never edited to fix a claim |
| wiki | `wiki/` | the source of truth; atomic pages; maintained |
| schema | this file and `/CLAUDE.md` | co-evolves with use |

When `docs/` and `wiki/` disagree, **the wiki wins**.

## Page types and folders

| type | folder | one page is |
|---|---|---|
| entity | `entities/` | a thing: the competition, a notebook, a dataset |
| concept | `concepts/` | an idea that explains results |
| decision | `decisions/` | what we chose, why, and what would reverse it |
| experiment | `experiments/` | hypothesis, result, verdict |
| howto | `howto/` | a procedure |

Every page has frontmatter: `type`, `updated`, `status`
(`current | done | open | in-progress | superseded`), `sources`.

Every page starts with an H1, then **one paragraph that answers the question on its
own**. The index is generated from that paragraph, so write it to stand alone.

Link with `[[page-name]]`. Keep pages short. Split rather than grow.

## Operations

**Ingest** a new source (forum paste, run log, notebook, result):
1. Read it. Note what it confirms, contradicts, or adds.
2. Update every affected page. Mark superseded claims `**Corrected:**`, never
   silently delete them - the history of being wrong is useful.
3. Append one line to [[log]].
4. Regenerate the index: `python3 wiki/build_index.py`.

**Query:** read [[overview]], then [[index]], then only the pages needed. A good
answer that is not in the wiki becomes a new page.

**Lint** before trusting the wiki after a gap:
- Does any page contradict another? Does [[overview]] match [[E004-submissions]]?
- Are `open` decisions still open?
- Has the leaderboard moved since `updated`?

## Confidence markers

[Certain] measured or read from source. [Likely] strong inference. [Guessing]
speculation. A number with no marker and no source is a bug.
