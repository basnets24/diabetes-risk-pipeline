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

{
  echo -e "year\tcount\tdiabetes_rate\tavg_bmi\tavg_blood_glucose"
  awk -f scripts/yearly_summary.awk "$INPUT" | sort -t$'\t' -k1,1
} > out/yearly_summary.tsv

awk -f scripts/numeric_signals.awk "$INPUT" > out/numeric_signals_unsorted.tsv

{
  head -1 out/numeric_signals_unsorted.tsv
  tail -n +2 out/numeric_signals_unsorted.tsv | sort -t$'\t' -k1,1n -k2,2n
} > out/numeric_signals.tsv

rm -f out/numeric_signals_unsorted.tsv

echo "[INFO] Finished successfully" | tee -a logs/run_pa4.log
