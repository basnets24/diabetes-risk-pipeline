#!/usr/bin/env bash

#
# Sprint 3 pipeline entry script
#
# Usage:
#   ./scripts/run_sprint3.sh <team10_sec3_path>
#
# Example:
#   ./scripts/run_sprint3.sh /mnt/scratch/CS131_jelenag/projects/team10_sec3
#
# Expected layout:
#   <team10_sec3_path>/Team10-ComprehensiveDiabetesClinicalDataset-health
#   <team10_sec3_path>/diabetes_dataset.csv
#

BASE_DIR="${1:-}"
if [ -z "$BASE_DIR" ]; then
    echo "Usage: $0 <team10_sec3_path>"
    exit 1
fi

PROJECT_ROOT="$BASE_DIR/Team10-ComprehensiveDiabetesClinicalDataset-health"
DATASET_PATH="$BASE_DIR/diabetes_dataset.csv"
DELIM="${2:-,}"

RUN_LOG="$PROJECT_ROOT/out/run_sprint3.log"
ERROR_LOG="$PROJECT_ROOT/out/errors.log"
EVIDENCE_DIR="$PROJECT_ROOT/out/evidence"

if [ ! -d "$PROJECT_ROOT" ]; then
    echo "Error: project root not found at '$PROJECT_ROOT'"
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
echo "Base directory: $BASE_DIR" | tee -a "$RUN_LOG"
echo "Project root: $PROJECT_ROOT" | tee -a "$RUN_LOG"
echo "Dataset: $DATASET_PATH" | tee -a "$RUN_LOG"
echo "" | tee -a "$RUN_LOG"

echo "[1/7] Running data quality checks..." | tee -a "$RUN_LOG"
python3 "$PROJECT_ROOT/scripts/data_quality.py" "$DATASET_PATH" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[2/7] Running feature engineering..." | tee -a "$RUN_LOG"
python3 "$PROJECT_ROOT/scripts/feature_engineering.py" "$DATASET_PATH" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[3/7] Building cohort prevalence summary..." | tee -a "$RUN_LOG"
python3 "$PROJECT_ROOT/scripts/cohort_analysis.py" "$DATASET_PATH" "$DELIM" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[4/7] Ranking high-risk profiles..." | tee -a "$RUN_LOG"
python3 "$PROJECT_ROOT/scripts/rank_high_risk_profiles.py" "$DATASET_PATH" "$DELIM" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[5/7] Building location prevalence summary..." | tee -a "$RUN_LOG"
python3 "$PROJECT_ROOT/scripts/location_prevalence.py" "$DATASET_PATH" "$DELIM" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[6/7] Building rule-based risk flags..." | tee -a "$RUN_LOG"
python3 "$PROJECT_ROOT/scripts/risk_rule_flags.py" "$DATASET_PATH" "$DELIM" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "[7/7] Running assumption test..." | tee -a "$RUN_LOG"
python3 "$PROJECT_ROOT/scripts/assumption_test.py" "$DATASET_PATH" "$DELIM" >> "$RUN_LOG" 2>> "$ERROR_LOG"

echo "" | tee -a "$RUN_LOG"
echo "Sprint 3 pipeline completed." | tee -a "$RUN_LOG"
echo "Run log: $RUN_LOG" | tee -a "$RUN_LOG"
echo "Error log: $ERROR_LOG" | tee -a "$RUN_LOG"
