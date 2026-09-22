#!/usr/bin/env bash
# Full suite. No data, no GPU, no network.
set -uo pipefail
fail=0
for t in tests/test_*.py; do
  echo "=== $t"
  python3 "$t" || fail=1
done
echo
[ $fail -eq 0 ] && echo "ALL SUITES PASS" || echo "FAILURES PRESENT"
exit $fail
