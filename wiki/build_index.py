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
       "- [SCHEMA](SCHEMA.md) - how this wiki is maintained", ""]
for head, d in SECTIONS:
    out += [f"## {head}", ""]
    for p in sorted((W / d).glob("*.md")):
        title, status, first = summary(p)
        tag = "" if status in ("current", "done") else f" **[{status}]**"
        out.append(f"- [{p.stem}]({d}/{p.name}){tag} - {first}")
    out.append("")
out += ["## Long-form archive (not maintained)", "",
        "`docs/` holds the original long-form record. Where it disagrees with the wiki,",
        "**the wiki wins** - several `docs/` claims have since been corrected here.", "",
        "- `docs/researched.md` - the 1,400-line research archive, four literature reviews",
        "- `docs/FINDINGS.md` - 20 reproduced defects in the 0.939 notebook, full detail",
        "- `docs/community.md` - forum threads transcribed verbatim",
        "- `docs/STRATEGY.md`, `docs/PLAN.md` - the reasoning and schedule as of 2026-09-10", ""]
(W / "index.md").write_text("\n".join(out))
print("wrote", W / "index.md")
