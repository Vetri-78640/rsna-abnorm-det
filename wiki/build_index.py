#!/usr/bin/env python3
"""Regenerate wiki/index.md from each page's H1 and first paragraph."""
import pathlib, re
W = pathlib.Path(__file__).resolve().parent

def summary(p):
    t = p.read_text()
    body = re.sub(r"^---.*?---\s*", "", t, flags=re.S)
    title = re.search(r"^# (.+)$", body, re.M).group(1).strip()
    m = re.search(r"^status: (\S+)", t, re.M)
    status = m.group(1) if m else "current"
    paras = [x.strip() for x in re.split(r"\n\s*\n", body.split("\n", 1)[1]) if x.strip()]
    first = re.sub(r"\s+", " ", re.sub(r"\*\*|`|\[\[|\]\]", "", paras[0]))
    return title, status, (first.split(". ")[0].rstrip(".") + ".")[:150]

SECTIONS = [("Entities - the things", "entities"), ("Concepts - the ideas", "concepts"),
            ("Decisions - what we chose and why", "decisions"),
            ("Experiments - what we ran", "experiments"), ("How-to", "howto")]
out = ["# Wiki index", "",
       "Every page, one line each. Read [[overview]] first. Pages are atomic: open only",
       "what the question needs. `[[name]]` links refer to the page file of that name.", "",
       "## Start here", "",
       "- [overview](overview.md) - current state, the thesis, and the next action",
       "- [log](log.md) - append-only history; check it before trusting any page",
       "- [SCHEMA](SCHEMA.md) - how this wiki is maintained",
       "- [glossary](glossary.md) - what arm, slot, key, gold, commit run and the rest mean here",
       "- [open-questions](open-questions.md) - what we do not know yet, and what would settle it", ""]
for head, d in SECTIONS:
    out += [f"## {head}", ""]
    for p in sorted((W / d).glob("*.md")):
        title, status, first = summary(p)
        tag = "" if status in ("current", "done") else f" **[{status}]**"
        out.append(f"- [{p.stem}]({d}/{p.name}){tag} - {first}")
    out.append("")
out += ["## Raw sources - verbatim, external", "",
        "- [forum](raw/forum.md) - Kaggle forum threads and host rulings, transcribed",
        "- [research](raw/research.md) - four literature reviews from research agents, 1,400 lines", "",
        "## Archive - our dated reasoning, frozen", "",
        "Where these disagree with a page above, the page wins.", "",
        "- [FINDINGS](archive/FINDINGS.md) - 20 reproduced defects in the 0.939 notebook, full detail",
        "- [STRATEGY](archive/STRATEGY.md) - leaderboard arithmetic and lever ranking, 2026-09-10",
        "- [PLAN](archive/PLAN.md) - the six-week schedule as of 2026-09-10",
        "- [extras](archive/extras.md) - competition mechanics and rules, long form", ""]
(W / "index.md").write_text("\n".join(out))
print("wrote", W / "index.md")
