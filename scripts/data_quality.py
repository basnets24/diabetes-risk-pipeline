#!/usr/bin/env python3
"""
data_quality.py 

Usage:
  python3 scripts/data_quality.py <DATASET_PATH> [DELIM]

Output:
  out/evidence/data_quality_report.txt
"""

import sys
import os
import csv
from pathlib import Path
from collections import Counter, defaultdict

RACE_COLUMNS = [
    "race:AfricanAmerican",
    "race:Asian",
    "race:Caucasian",
    "race:Hispanic",
    "race:Other",
]

BINARY_COLUMNS = [
    "hypertension",
    "heart_disease",
    "diabetes",
    *RACE_COLUMNS,
]

NUMERIC_COLUMNS = [
    "year",
    "age",
    "bmi",
    "hbA1c_level",
    "blood_glucose_level",
]


def is_missing(val: str) -> bool:
    if val is None:
        return True
    v = str(val).strip()
    return v == "" or v.lower() in {"na", "n/a", "null", "none", "nan", "unknown"}


def parse_float(val: str):
    if is_missing(val):
        return None
    try:
        return float(val)
    except ValueError:
        return None


def parse_binary(val: str):
    if is_missing(val):
        return None
    v = str(val).strip()
    if v in {"0", "0.0"}:
        return 0
    if v in {"1", "1.0"}:
        return 1
    return "INVALID"


def get_dataset_path():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/data_quality.py <dataset_path> [DELIM]", file=sys.stderr)
        sys.exit(1)

    dataset_path = Path(sys.argv[1])
    if not dataset_path.exists():
        print(f"Error: dataset not found at '{dataset_path}'", file=sys.stderr)
        sys.exit(1)

    delim = sys.argv[2] if len(sys.argv) >= 3 else ","
    if len(delim) != 1:
        print("Error: delimiter must be a single character", file=sys.stderr)
        sys.exit(1)

    return dataset_path, delim


def add_section(lines, title):
    lines.append(title)
    lines.append("-" * 60)


def main():
    dataset_path, delim = get_dataset_path()

    output_path = Path("out/evidence/data_quality_report.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    bad_rows = 0

    null_counts = Counter()
    numeric_min = {}
    numeric_max = {}
    numeric_non_numeric = Counter()

    binary_unique = defaultdict(set)
    binary_invalid_count = Counter()

    diabetes_counts = Counter()

    race_exactly_one = 0
    race_all_zero = 0
    race_multiple = 0
    race_non_binary_rows = 0
    race_check_possible = True

    invalid_age = 0
    invalid_bmi = 0
    invalid_year = 0
    invalid_hba1c = 0
    invalid_glucose = 0

    all_columns = []

    with open(dataset_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delim)

        if reader.fieldnames is None:
            print("Error: empty file or missing header", file=sys.stderr)
            sys.exit(1)

        all_columns = reader.fieldnames

        for row in reader:
            total_rows += 1

            # Null counts for every column
            for col in all_columns:
                value = row.get(col, "")
                if is_missing(value):
                    null_counts[col] += 1

            # Numeric ranges + invalid parsing count
            for col in NUMERIC_COLUMNS:
                if col not in row:
                    continue
                value = row.get(col, "")
                if is_missing(value):
                    continue

                num = parse_float(value)
                if num is None:
                    numeric_non_numeric[col] += 1
                    continue

                if col not in numeric_min or num < numeric_min[col]:
                    numeric_min[col] = num
                if col not in numeric_max or num > numeric_max[col]:
                    numeric_max[col] = num

            # Binary validation
            for col in BINARY_COLUMNS:
                if col not in row:
                    continue
                parsed = parse_binary(row.get(col, ""))
                if parsed is None:
                    continue
                if parsed == "INVALID":
                    binary_invalid_count[col] += 1
                    binary_unique[col].add(str(row.get(col, "")).strip())
                else:
                    binary_unique[col].add(parsed)

            # Diabetes distribution
            if "diabetes" in row:
                raw = row.get("diabetes", "")
                if is_missing(raw):
                    diabetes_counts["MISSING"] += 1
                else:
                    parsed = parse_binary(raw)
                    if parsed == "INVALID":
                        diabetes_counts["INVALID"] += 1
                    else:
                        diabetes_counts[str(parsed)] += 1

            # Race one-hot consistency
            if all(col in row for col in RACE_COLUMNS):
                race_values = []
                row_has_non_binary_race = False

                for col in RACE_COLUMNS:
                    parsed = parse_binary(row.get(col, ""))
                    if parsed in (0, 1):
                        race_values.append(parsed)
                    else:
                        row_has_non_binary_race = True

                if row_has_non_binary_race:
                    race_non_binary_rows += 1
                else:
                    s = sum(race_values)
                    if s == 1:
                        race_exactly_one += 1
                    elif s == 0:
                        race_all_zero += 1
                    elif s > 1:
                        race_multiple += 1
            else:
                race_check_possible = False

            # Invalid value checks
            age = parse_float(row.get("age", ""))
            if age is not None and (age < 0 or age > 120):
                invalid_age += 1

            bmi = parse_float(row.get("bmi", ""))
            if bmi is not None and bmi < 0:
                invalid_bmi += 1

            year = parse_float(row.get("year", ""))
            if year is not None and (year < 1900 or year > 2100):
                invalid_year += 1

            hba1c = parse_float(row.get("hbA1c_level", ""))
            if hba1c is not None and hba1c < 0:
                invalid_hba1c += 1

            glucose = parse_float(row.get("blood_glucose_level", ""))
            if glucose is not None and glucose < 0:
                invalid_glucose += 1

    lines = []
    lines.append("DATA QUALITY REPORT")
    lines.append("=" * 60)
    lines.append(f"Dataset path: {dataset_path}")
    lines.append(f"Rows: {total_rows}")
    lines.append(f"Columns: {len(all_columns)}")
    lines.append("")

    add_section(lines, "NULL COUNTS BY COLUMN")
    for col in all_columns:
        lines.append(f"{col}: {null_counts[col]}")
    lines.append("")

    add_section(lines, "NUMERIC RANGES")
    for col in NUMERIC_COLUMNS:
        if col not in all_columns:
            continue
        if col not in numeric_min:
            lines.append(f"{col}: no valid numeric values")
        else:
            lines.append(
                f"{col}: min={numeric_min[col]}, max={numeric_max[col]}, non_numeric_count={numeric_non_numeric[col]}"
            )
    lines.append("")

    add_section(lines, "BINARY FIELD VALIDATION")
    for col in BINARY_COLUMNS:
        if col not in all_columns:
            continue
        unique_vals = sorted(binary_unique[col], key=str)
        lines.append(f"{col}: unique_values={unique_vals}, invalid_count={binary_invalid_count[col]}")
    lines.append("")

    add_section(lines, "DIABETES CLASS DISTRIBUTION")
    if "diabetes" not in all_columns:
        lines.append("Skipped: diabetes column missing")
    else:
        for value, count in sorted(diabetes_counts.items(), key=lambda x: str(x[0])):
            pct = (count / total_rows * 100.0) if total_rows else 0.0
            lines.append(f"{value}: {count} ({pct:.2f}%)")
    lines.append("")

    add_section(lines, "RACE ONE-HOT CONSISTENCY CHECK")
    if not race_check_possible:
        lines.append("Skipped: one or more race one-hot columns are missing.")
    else:
        lines.append(f"Rows with exactly one race flag = 1: {race_exactly_one}")
        lines.append(f"Rows with all race flags = 0: {race_all_zero}")
        lines.append(f"Rows with multiple race flags = 1: {race_multiple}")
        lines.append(f"Rows with non-binary values in race columns: {race_non_binary_rows}")
    lines.append("")

    add_section(lines, "INVALID VALUE CHECKS")
    lines.append(f"age outside [0, 120]: {invalid_age}")
    lines.append(f"negative bmi values: {invalid_bmi}")
    lines.append(f"year outside [1900, 2100]: {invalid_year}")
    lines.append(f"negative hbA1c_level values: {invalid_hba1c}")
    lines.append(f"negative blood_glucose_level values: {invalid_glucose}")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Data quality report written to {output_path}")


if __name__ == "__main__":
    main()