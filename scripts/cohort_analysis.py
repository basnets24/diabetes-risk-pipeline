#!/usr/bin/env python3
"""
cohort_analysis.py (pandas-free)

Builds a cohort prevalence summary by (age_bucket, bmi_bucket, gender, smoking_history,
hypertension, heart_disease, location). Outputs CSV with cohort_size, diabetes_count, prevalence.

Usage:
  python3 scripts/cohort_analysis.py <DATASET_PATH> [DELIM]

Example:
  python3 scripts/cohort_analysis.py data/samples/sample_1k.csv ","

Output:
  out/evidence/cohort_prevalence_summary.csv
"""
import sys, os, csv
from collections import defaultdict

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

def norm(v):
    v = (v or "").strip()
    return v if v != "" else "unknown"

def main():
    if len(sys.argv) < 2:
        print("Usage: cohort_analysis.py <DATASET_PATH> [DELIM]", file=sys.stderr)
        sys.exit(1)

    dataset_path = sys.argv[1]
    delim = sys.argv[2] if len(sys.argv) >= 3 else ","
    if len(delim) != 1:
        print("ERROR: DELIM must be 1 character", file=sys.stderr)
        sys.exit(2)

    out_dir = "out/evidence"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "cohort_prevalence_summary.csv")

    # key -> [total, diabetes_yes]
    agg = defaultdict(lambda: [0, 0])

    with open(dataset_path, newline="") as f:
        r = csv.DictReader(f, delimiter=delim)
        for row in r:
            k = (
                age_bucket(row.get("age","")),
                bmi_bucket(row.get("bmi","")),
                norm(row.get("gender","")),
                norm(row.get("smoking_history","")),
                norm(row.get("hypertension","")),
                norm(row.get("heart_disease","")),
                norm(row.get("location","")),
            )
            agg[k][0] += 1
            d = norm(row.get("diabetes",""))
            if d in {"1", "true", "yes", "y"}:
                agg[k][1] += 1

    with open(out_path, "w", newline="") as out:
        w = csv.writer(out)
        w.writerow([
            "age_bucket","bmi_bucket","gender","smoking_history",
            "hypertension","heart_disease","location",
            "cohort_size","diabetes_count","prevalence"
        ])
        for k, (n, dy) in agg.items():
            prev = (dy / n) if n else 0.0
            w.writerow(list(k) + [n, dy, f"{prev:.6f}"])

    print("Wrote:", out_path)

if __name__ == "__main__":
    main()
