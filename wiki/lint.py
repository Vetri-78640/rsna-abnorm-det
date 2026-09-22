#!/usr/bin/env python3
"""Lint the wiki: every [[link]] and relative link resolves, every page has
frontmatter and a standalone opening, and index.md is current. Exit 1 on failure.
This is the "lint" operation of the LLM-wiki pattern, automated for CI."""
import pathlib, re, subprocess, sys

W = pathlib.Path(__file__).resolve().parent
REPO = W.parent
pages = {p.stem: p for p in W.rglob("*.md")}
errors = []

for p in W.rglob("*.md"):
    t = p.read_text()
    rel = p.relative_to(W)
    prose = re.sub(r"```.*?```", "", t, flags=re.S)
    prose = re.sub(r"`[^`\n]*`", "", prose)          # links inside code are examples
    for name in re.findall(r"\[\[([^\]|#]+)", prose):
        if name.strip() not in pages:
            errors.append(f"{rel}: broken [[{name}]]")
    for href in re.findall(r"\]\(([^)#:\s]+\.md)\)", prose):
        if not (p.parent / href).exists():
            errors.append(f"{rel}: broken link ({href})")
    top = rel.parts[0]
    if top in ("entities", "concepts", "decisions", "experiments", "howto") or rel.name in (
            "overview.md", "glossary.md", "open-questions.md"):
        if not t.startswith("---\n") or "\nupdated:" not in t or "\nstatus:" not in t:
            errors.append(f"{rel}: missing frontmatter (type / updated / status)")

before = (W / "index.md").read_text()
subprocess.run([sys.executable, str(W / "build_index.py")], check=True, capture_output=True)
if (W / "index.md").read_text() != before:
    errors.append("index.md was stale - run python3 wiki/build_index.py and commit it")

for e in errors:
    print("  x", e)
print(f"wiki lint: {len(pages)} pages, {len(errors)} problem(s)")
sys.exit(1 if errors else 0)
