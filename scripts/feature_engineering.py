#!/usr/bin/env python3
"""
feature_engineering.py (pandas-free)

Creates simple derived "bucket" summaries needed for cohort analysis.

Usage:
  python3 scripts/feature_engineering.py <DATASET_PATH> [DELIM]

Example:
  python3 scripts/feature_engineering.py data/samples/sample_1k.csv ","

Outputs:
  out/evidence/feature_engineering_summary.txt
"""
import sys, os, csv
from collections import Counter

def age_bucket(age):
    try:
        a = float(age)
    except:
        return "unknown"
    if a < 18: return "<18"
    if a < 30: return "18-29"
    if a < 45: return "30-44"
    if a < 60: return "45-59"
    return "60+"

def bmi_bucket(bmi):
    try:
        b = float(bmi)
    except:
        return "unknown"
    if b < 18.5: return "underweight"
    if b < 25: return "normal"
    if b < 30: return "overweight"
    return "obese"

def main():
    if len(sys.argv) < 2:
        print("Usage: feature_engineering.py <DATASET_PATH> [DELIM]", file=sys.stderr)
        sys.exit(1)
    dataset_path = sys.argv[1]
    delim = sys.argv[2] if len(sys.argv) >= 3 else ","
    if len(delim) != 1:
        print("ERROR: DELIM must be 1 character", file=sys.stderr)
        sys.exit(2)

    out_dir = "out/evidence"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "feature_engineering_summary.txt")

    with open(dataset_path, newline="") as f:
        r = csv.DictReader(f, delimiter=delim)
        # Expecting these fields from diabetes dataset
        # age, bmi, gender, smoking_history, hypertension, heart_disease, diabetes, location, year
        age_b = Counter()
        bmi_b = Counter()
        gender_c = Counter()
        smoke_c = Counter()

        rows = 0
        for row in r:
            rows += 1
            age_b[age_bucket(row.get("age",""))] += 1
            bmi_b[bmi_bucket(row.get("bmi",""))] += 1
            gender_c[(row.get("gender","") or "unknown").strip()] += 1
            smoke_c[(row.get("smoking_history","") or "unknown").strip()] += 1

    with open(out_path, "w") as out:
        out.write("Sprint 3 Feature Engineering Summary (pandas-free)\n")
        out.write(f"Dataset: {dataset_path}\n")
        out.write(f"Rows processed: {rows}\n\n")

        out.write("Age bucket counts:\n")
        for k,v in age_b.most_common():
            out.write(f"- {k}: {v}\n")
        out.write("\nBMI bucket counts:\n")
        for k,v in bmi_b.most_common():
            out.write(f"- {k}: {v}\n")
        out.write("\nGender counts:\n")
        for k,v in gender_c.most_common():
            out.write(f"- {k}: {v}\n")
        out.write("\nSmoking history counts:\n")
        for k,v in smoke_c.most_common():
            out.write(f"- {k}: {v}\n")

    print("Wrote:", out_path)

if __name__ == "__main__":
    main()
