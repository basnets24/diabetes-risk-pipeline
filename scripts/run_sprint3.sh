#!/usr/bin/env bash

# Sprint 3 pipeline entry script
#
# Example usage:
#   ./scripts/run_sprint3.sh ../diabetes_prediction_dataset.csv
#   absolute data path: /mnt/scratch/CS131_jelenag/projects/team10_sec3/diabetes_dataset.csv
# This script:
# - accepts the dataset path as an argument
# - writes all evidence artifacts into out/evidence/
# - writes a run log to out/run_sprint3.log
# - writes stderr output to out/errors.log


DATASET_PATH="${1:-}"
RUN_LOG="out/run_sprint3.log"
DELIM="${2:-,}"
ERROR_LOG="out/errors.log"
EVIDENCE_DIR="out/evidence"


if [ -z "$DATASET_PATH" ]; then
    echo "Usage: ./scripts/run_sprint3.sh <dataset_path>"
    echo "Example: ./scripts/run_sprint3.sh /mnt/scratch/CS131_jelenag/projects/team10_sec3/diabetes_dataset.csv"
    exit 1
fi

if [ ! -f "$DATASET_PATH" ]; then
    echo "Error: dataset not found at '$DATASET_PATH'"
    exit 1
fi

mkdir -p "$EVIDENCE_DIR"

# Start fresh logs for this run
: > "$RUN_LOG"
: > "$ERROR_LOG"

echo "Starting Sprint 3 pipeline..." | tee -a "$RUN_LOG"
echo "Dataset: $DATASET_PATH" | tee -a "$RUN_LOG"
echo "Evidence output directory: $EVIDENCE_DIR" | tee -a "$RUN_LOG"
echo "" | tee -a "$RUN_LOG"


echo "[1/7] Running data quality checks..." | tee -a "$RUN_LOG"
python3 scripts/data_quality.py "$DATASET_PATH" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[2/7] Running feature engineering..." | tee -a "$RUN_LOG"
python3 scripts/feature_engineering.py "$DATASET_PATH" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[3/7] Building cohort prevalence summary..." | tee -a "$RUN_LOG"
python3 scripts/cohort_analysis.py "$DATASET_PATH" "$DELIM" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[4/7] Ranking high-risk profiles..." | tee -a "$RUN_LOG"
python3 scripts/rank_high_risk_profiles.py "$DATASET_PATH" "$DELIM" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[5/7] Building location prevalence summary..." | tee -a "$RUN_LOG"
python3 scripts/location_prevalence.py "$DATASET_PATH" "$DELIM" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[6/7] Building rule-based risk flags..." | tee -a "$RUN_LOG"
python3 scripts/risk_rule_flags.py "$DATASET_PATH" "$DELIM" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[7/7] Running assumption test..." | tee -a "$RUN_LOG"
python3 scripts/assumption_test.py "$DATASET_PATH" "$DELIM" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "" | tee -a "$RUN_LOG"
echo "Sprint 3 pipeline completed." | tee -a "$RUN_LOG"
echo "Run log: $RUN_LOG" | tee -a "$RUN_LOG"
echo "Error log: $ERROR_LOG" | tee -a "$RUN_LOG"
