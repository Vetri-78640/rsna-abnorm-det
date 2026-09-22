#!/usr/bin/env bash
# Pull only the metadata CSVs. Deliberately NOT the 570 GB of DICOMs -- every
# tier-0 question (gold count, prevalence, language mix, protocol distribution)
# is answerable from these four files alone, and they are a few MB.
#
# Requires the competition rules to have been accepted on the Kaggle site;
# the API returns 403 until then.
set -euo pipefail

COMP=rsna-knee-abnormality-detection
OUT=${1:-data}

mkdir -p "$OUT"
cd "$OUT"

for f in train.csv train_series.csv test.csv test_series.csv sample_submission.csv; do
  if [ -f "$f" ]; then
    echo "skip   $f (already present)"
    continue
  fi
  echo "fetch  $f"
  kaggle competitions download -c "$COMP" -f "$f" -q || {
    echo "FAILED on $f -- have you accepted the competition rules?" >&2
    exit 1
  }
  [ -f "$f.zip" ] && unzip -oq "$f.zip" && rm -f "$f.zip"
done

echo
ls -lh ./*.csv
echo
echo "next: python3 scripts/audit_labels.py $OUT"
