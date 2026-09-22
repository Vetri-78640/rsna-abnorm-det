#!/usr/bin/env python3
"""List every file in the competition via the Kaggle API, 200 per page, into
data/file_inventory.csv (gitignored: paths carry competition UIDs).

Gives slices per series and bytes per slice for all 24,371 series without
downloading the 570 GB. Resumable: the next page token is saved after every page.

Usage: python3 scripts/crawl_file_inventory.py [out_csv]
"""
import csv, json, pathlib, subprocess, sys, time

COMP = "rsna-knee-abnormality-detection"
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "data/file_inventory.csv")
state = out.with_suffix(".state.json")
tok = json.loads(state.read_text())["token"] if state.exists() else None
mode = "a" if (state.exists() and out.exists()) else "w"

with out.open(mode, newline="") as fh:
    w = csv.writer(fh)
    if mode == "w":
        w.writerow(["name", "size"])
    pages = 0
    while True:
        cmd = ["kaggle", "competitions", "files", "-c", COMP, "--page-size", "200", "--csv"]
        if tok:
            cmd += ["--page-token", tok]
        for attempt in range(6):
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0 and "name,size" in r.stdout:
                break
            time.sleep(5 * (attempt + 1))
        else:
            sys.exit(f"gave up after retries at page {pages}: {r.stderr[:200]}")
        lines = r.stdout.splitlines()
        nxt = None
        rows = []
        for ln in lines:
            if ln.startswith("Next Page Token = "):
                nxt = ln.split(" = ", 1)[1].strip()
            elif ln and not ln.startswith("name,size"):
                parts = ln.split(",")
                rows.append([parts[0], parts[1]])
        w.writerows(rows)
        fh.flush()
        pages += 1
        tok = nxt
        state.write_text(json.dumps({"token": tok, "pages": pages}))
        if pages % 100 == 0:
            print(f"{pages} pages", flush=True)
        if not tok:
            break
        time.sleep(0.2)
state.unlink(missing_ok=True)
print(f"done: {pages} pages -> {out}")
