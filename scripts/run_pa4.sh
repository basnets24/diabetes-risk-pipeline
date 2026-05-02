#!/usr/bin/env bash
set -euo pipefail

INPUT="${1:-}"

if [ -z "$INPUT" ]; then
  echo "Usage: bash run_pa4.sh <INPUT_CSV>" >&2
  exit 1
fi

if [ ! -f "$INPUT" ]; then
  echo "ERROR: input file not found: $INPUT" >&2
  exit 1
fi

mkdir -p out logs
chmod -R g+rX "$(dirname "$INPUT")" 2>/dev/null || true

echo "[INFO] Running PA4 pipeline on: $INPUT" | tee logs/run_pa4.log

echo "[INFO] Step 1: normalization" | tee -a logs/run_pa4.log
head -n 20 "$INPUT" > out/before_sample.csv
sed -E -f scripts/normalize.sed "$INPUT" > out/normalized.tsv
head -n 20 out/normalized.tsv > out/after_sample.tsv

echo "[INFO] Step 2: quality filtering" | tee -a logs/run_pa4.log
awk -f scripts/quality_filter.awk out/normalized.tsv > out/filtered.tsv

echo "[INFO] Step 3: BMI bucket summary" | tee -a logs/run_pa4.log
awk -f scripts/bmi_buckets.awk out/filtered.tsv > out/bmi_bucket_summary_unsorted.tsv
{
  head -n 1 out/bmi_bucket_summary_unsorted.tsv
  tail -n +2 out/bmi_bucket_summary_unsorted.tsv | sort -t$'\t' -k4,4nr
} > out/bmi_bucket_summary.tsv
rm -f out/bmi_bucket_summary_unsorted.tsv

{
  echo -e "year\tcount\tdiabetes_rate\tavg_bmi\tavg_blood_glucose"
  awk -f scripts/yearly_summary.awk out/filtered.tsv | sort -t$'\t' -k1,1
} > out/yearly_summary.tsv

awk -f scripts/numeric_signals.awk out/filtered.tsv > out/numeric_signals_unsorted.tsv

{
  head -1 out/numeric_signals_unsorted.tsv
  tail -n +2 out/numeric_signals_unsorted.tsv | sort -t$'\t' -k1,1n -k2,2n
} > out/numeric_signals.tsv

rm -f out/numeric_signals_unsorted.tsv

echo "[INFO] Finished successfully" | tee -a logs/run_pa4.log
