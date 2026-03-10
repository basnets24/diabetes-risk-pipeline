#!/usr/bin/env python3
"""
rank_high_risk_profiles.py (pandas-free)

Reads cohort_prevalence_summary.csv and ranks cohorts by prevalence.
Applies minimum cohort size threshold (>= 10 for sample data).

Usage:
  python3 scripts/rank_high_risk_profiles.py <DATASET_PATH> [DELIM]

Output:
  out/evidence/ranked_high_risk_profiles.csv
"""

import sys, os, csv

def main():
    out_dir = "out/evidence"
    os.makedirs(out_dir, exist_ok=True)

    input_path = os.path.join(out_dir, "cohort_prevalence_summary.csv")
    output_path = os.path.join(out_dir, "ranked_high_risk_profiles.csv")

    if not os.path.exists(input_path):
        print("ERROR: cohort_prevalence_summary.csv not found.")
        sys.exit(1)

    rows = []

    with open(input_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            size = int(row["cohort_size"])
            prev = float(row["prevalence"])
            if size >= 10:   # threshold
                rows.append((prev, size, row))

    rows.sort(reverse=True, key=lambda x: x[0])

    with open(output_path, "w", newline="") as out:
        writer = csv.writer(out)
        writer.writerow([
            "age_bucket","bmi_bucket","gender","smoking_history",
            "hypertension","heart_disease","location",
            "cohort_size","diabetes_count","prevalence"
        ])

        for prev, size, row in rows[:50]:  # top 50
            writer.writerow([
                row["age_bucket"],
                row["bmi_bucket"],
                row["gender"],
                row["smoking_history"],
                row["hypertension"],
                row["heart_disease"],
                row["location"],
                row["cohort_size"],
                row["diabetes_count"],
                row["prevalence"]
            ])

    print("Wrote:", output_path)

if __name__ == "__main__":
    main()
