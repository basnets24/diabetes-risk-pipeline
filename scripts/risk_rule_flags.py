#!/usr/bin/env python3
"""
risk_rule_flags.py (pandas-free)

Applies simple rule-based flags:
- bmi >= 30
- hypertension == 1
- heart_disease == 1
- age >= 60

Outputs:
  out/evidence/risk_rule_flags.csv
"""

import sys, os, csv

def to_float(x):
    try:
        return float(x)
    except:
        return None

def norm(x):
    return (x or "").strip().lower()

def main():
    if len(sys.argv) < 2:
        print("Usage: risk_rule_flags.py <DATASET_PATH> [DELIM]")
        sys.exit(1)

    dataset_path = sys.argv[1]
    delim = sys.argv[2] if len(sys.argv) >= 3 else ","

    out_dir = "out/evidence"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "risk_rule_flags.csv")

    total = 0
    flagged = 0

    with open(dataset_path, newline="") as f:
        r = csv.DictReader(f, delimiter=delim)

        with open(out_path, "w", newline="") as out:
            w = csv.writer(out)
            w.writerow(["row_index", "high_risk_flag"])

            for i, row in enumerate(r):
                total += 1

                age = to_float(row.get("age"))
                bmi = to_float(row.get("bmi"))
                hypertension = norm(row.get("hypertension"))
                heart = norm(row.get("heart_disease"))

                high_risk = False

                if bmi and bmi >= 30:
                    high_risk = True
                if age and age >= 60:
                    high_risk = True
                if hypertension in {"1", "yes", "true"}:
                    high_risk = True
                if heart in {"1", "yes", "true"}:
                    high_risk = True

                if high_risk:
                    flagged += 1

                w.writerow([i, int(high_risk)])

    print("Wrote:", out_path)
    print("Total rows:", total)
    print("Flagged rows:", flagged)

if __name__ == "__main__":
    main()
