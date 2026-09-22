# Schema - how this wiki works

Follows Andrej Karpathy's LLM-wiki pattern: raw sources are immutable, the wiki is
the maintained layer, and this file says how to maintain it.

## Layers

| layer | where | rule |
|---|---|---|
| raw sources | `wiki/raw/`, `logs/`, `*.ipynb`, `data/` | verbatim external material; never edited to fix a claim |
| archive | `wiki/archive/` | our own dated long-form reasoning; frozen, may be wrong |
| wiki | `wiki/` | the source of truth; atomic pages; maintained |
| schema | this file and `/CLAUDE.md` | co-evolves with use |

When `raw/` or `archive/` disagrees with a wiki page, **the page wins**. Fix the
page, never the archive - the archive is the record of what we thought and when.

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
5. Run `python3 wiki/lint.py`. All of this lands in the **same commit** as the work -
   CI rejects a PR that changes code without touching `wiki/log.md`.

**Query:** read [[overview]], then [[index]], then only the pages needed. A good
answer that is not in the wiki becomes a new page.

**Lint** is automated: `python3 wiki/lint.py` checks every `[[link]]` and relative
link resolves, every page has frontmatter, and the index is current. CI runs it.
By hand, before trusting the wiki after a gap:
- Does any page contradict another? Does [[overview]] match [[E004-submissions]]?
- Are `open` decisions still open?
- Has the leaderboard moved since `updated`?

## Confidence markers

[Certain] measured or read from source. [Likely] strong inference. [Guessing]
speculation. A number with no marker and no source is a bug.
