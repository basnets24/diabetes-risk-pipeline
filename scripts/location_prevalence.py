#!/usr/bin/env python3
"""
location_prevalence.py (pandas-free)

Computes diabetes prevalence by location.

Usage:
  python3 scripts/location_prevalence.py <DATASET_PATH> [DELIM]

Output:
  out/evidence/location_prevalence_profile.csv
"""

import sys, os, csv
from collections import defaultdict

def norm(v):
    v = (v or "").strip()
    return v if v != "" else "unknown"

def main():
    if len(sys.argv) < 2:
        print("Usage: location_prevalence.py <DATASET_PATH> [DELIM]")
        sys.exit(1)

    dataset_path = sys.argv[1]
    delim = sys.argv[2] if len(sys.argv) >= 3 else ","

    out_dir = "out/evidence"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "location_prevalence_profile.csv")

    agg = defaultdict(lambda: [0,0])

    with open(dataset_path, newline="") as f:
        r = csv.DictReader(f, delimiter=delim)
        for row in r:
            loc = norm(row.get("location",""))
            agg[loc][0] += 1
            d = norm(row.get("diabetes",""))
            if d in {"1","true","yes","y"}:
                agg[loc][1] += 1

    with open(out_path, "w", newline="") as out:
        w = csv.writer(out)
        w.writerow(["location","total","diabetes_count","prevalence"])
        for loc, (n, dy) in agg.items():
            prev = dy/n if n else 0.0
            w.writerow([loc,n,dy,f"{prev:.6f}"])

    print("Wrote:", out_path)

if __name__ == "__main__":
    main()
