#!/usr/bin/env bash

DATASET=$1

if [ -z "$DATASET" ]; then
    echo "Usage: ./scripts/run_sprint3.sh <dataset_path>"
    echo "Example: ./scripts/run_sprint3.sh data/diabetes.csv"
    exit 1
fi

mkdir -p out/evidence

echo "Starting Sprint 3 pipeline..." | tee out/run_sprint3.log
echo "Dataset: $DATASET" | tee -a out/run_sprint3.log



echo "Sprint 3 pipeline finished." | tee -a out/run_sprint3.log

