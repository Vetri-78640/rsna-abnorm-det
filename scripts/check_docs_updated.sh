#!/usr/bin/env bash
# Fail if code changed since BASE without wiki/log.md changing too.
# The project rule: every iteration updates its docs in the same change.
# Usage: scripts/check_docs_updated.sh [BASE]   (default: origin/main)
set -euo pipefail
BASE=${1:-origin/main}
changed=$(git diff --name-only "$BASE"...HEAD)
code=$(echo "$changed" | grep -E '^(src|scripts|tests|notebooks)/|\.ipynb$|^run_tests\.sh$' || true)
if [ -z "$code" ]; then
  echo "docs check: no code changed"
  exit 0
fi
if echo "$changed" | grep -qx 'wiki/log.md'; then
  echo "docs check: code changed and wiki/log.md updated - ok"
  exit 0
fi
echo "docs check FAILED: code changed but wiki/log.md did not."
echo "Update the affected wiki page(s), append to wiki/log.md, run python3 wiki/build_index.py."
echo "$code" | sed 's/^/  changed: /'
exit 1
