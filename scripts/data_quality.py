#!/usr/bin/env python3
"""
data_quality.py (pandas-free)

Usage:
  python3 scripts/data_quality.py <DATASET_PATH> [DELIM]

Example:
  python3 scripts/data_quality.py data/samples/sample_1k.csv ","

Outputs:
  out/evidence/data_quality_report.txt
"""
import sys
import os
import csv
from collections import Counter

def is_missing(val: str) -> bool:
    if val is None:
        return True
    v = val.strip()
    if v == "":
        return True
    return v.lower() in {"na", "n/a", "null", "none", "nan", "unknown"}

def main():
    if len(sys.argv) < 2:
        print("Usage: data_quality.py <DATASET_PATH> [DELIM]", file=sys.stderr)
        sys.exit(1)

    dataset_path = sys.argv[1]
    delim = sys.argv[2] if len(sys.argv) >= 3 else ","

    if len(delim) != 1:
        print("ERROR: DELIM must be a 1-character string (e.g. ',' or '\\t')", file=sys.stderr)
        sys.exit(2)

    if not os.path.isfile(dataset_path):
        print(f"ERROR: dataset not found: {dataset_path}", file=sys.stderr)
        sys.exit(3)

    out_dir = "out/evidence"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "data_quality_report.txt")

    total_rows = 0
    header = None
    col_missing = Counter()
    col_total = Counter()
    bad_rows = 0

    with open(dataset_path, newline="") as f:
        reader = csv.reader(f, delimiter=delim)
        header = next(reader, None)
        if header is None:
            raise SystemExit("ERROR: empty file")

        num_cols = len(header)
        for row in reader:
            if len(row) == 0:
                continue
            total_rows += 1
            if len(row) != num_cols:
                bad_rows += 1

            # pad/trim to header length for counting
            row2 = (row + [""] * num_cols)[:num_cols]
            for i, val in enumerate(row2):
                col_total[i] += 1
                if is_missing(val):
                    col_missing[i] += 1

    with open(out_path, "w") as out:
        out.write("Sprint 3 Trust Check: Data Quality Report (pandas-free)\n")
        out.write(f"Dataset: {dataset_path}\n")
        out.write(f"Delimiter: {repr(delim)}\n\n")
        out.write(f"Total data rows (excluding header): {total_rows}\n")
        out.write(f"Header columns: {len(header)}\n")
        out.write(f"Rows with wrong column count: {bad_rows}\n\n")

        out.write("Missingness by column (missing/total, percent):\n")
        for i, name in enumerate(header):
            miss = col_missing[i]
            tot = col_total[i] if col_total[i] else 0
            pct = (miss / tot * 100.0) if tot else 0.0
            out.write(f"- {name}: {miss}/{tot} ({pct:.2f}%)\n")

    print("Wrote:", out_path)

if __name__ == "__main__":
    main()
