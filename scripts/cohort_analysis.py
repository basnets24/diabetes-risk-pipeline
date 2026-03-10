#!/usr/bin/env python3

import csv
from pathlib import Path
from collections import defaultdict

# Input produced by feature_engineering.py
INPUT_PATH = Path("out/cleaned_diabetes_data.csv")

# Final evidence artifact for cohort comparison
OUTPUT_PATH = Path("out/evidence/cohort_prevalence_summary.csv")

# Cohort dimensions we want to analyze
COHORT_COLUMNS = [
    "age_bucket",
    "race",
    "gender",
    "bmi_bucket",
    "hypertension",
    "heart_disease",
    "smoking_history",
    "location",
]


def validate_input() -> None:
    # Make sure the cleaned dataset exists before running aggregation
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found at {INPUT_PATH}. Run feature_engineering.py first."
        )


def parse_diabetes_value(value: str):
    """
    Convert the diabetes field into an integer 0 or 1 when possible.

    Returns:
        0 or 1 if valid
        None if the value is missing or invalid
    """
    if value is None:
        return None

    cleaned = str(value).strip()

    if cleaned in {"0", "0.0"}:
        return 0
    if cleaned in {"1", "1.0"}:
        return 1

    return None


def compute_cohort_summary(rows: list[dict], column: str) -> list[dict]:
    """
    Build one cohort summary table for a single cohort dimension.

    For example, if column = "race", this function will produce rows like:
    - race, Asian, total rows, diabetes cases, prevalence
    - race, Hispanic, total rows, diabetes cases, prevalence
    """
    # Track:
    # - cohort_size: how many rows belong to each cohort value
    # - diabetes_count: how many of those rows have diabetes = 1
    cohort_size = defaultdict(int)
    diabetes_count = defaultdict(int)

    for row in rows:
        # Skip the column if it does not exist in the current row
        if column not in row:
            continue

        cohort_value = row[column]

        # Count every row in that cohort bucket
        cohort_size[cohort_value] += 1

        # Count diabetes cases only when diabetes is a valid binary value
        diabetes_value = parse_diabetes_value(row.get("diabetes", ""))
        if diabetes_value == 1:
            diabetes_count[cohort_value] += 1

    summary_rows = []

    # Sort cohort values for stable, predictable output
    for cohort_value in sorted(cohort_size, key=lambda x: str(x)):
        size = cohort_size[cohort_value]
        d_count = diabetes_count[cohort_value]

        # Prevalence rate = diabetes cases / total cohort size
        prevalence_rate = (d_count / size) if size else 0.0

        summary_rows.append(
            {
                "cohort_dimension": column,
                "cohort_value": cohort_value,
                "cohort_size": size,
                "diabetes_count": d_count,
                "prevalence_rate": round(prevalence_rate, 4),
            }
        )

    return summary_rows


def build_cohort_table(rows: list[dict]) -> list[dict]:
    """
    Build one combined cohort prevalence table across all cohort dimensions.
    """
    tables = []

    # Build one summary block per cohort column
    for column in COHORT_COLUMNS:
        if not rows:
            continue

        # If the column is missing entirely from the cleaned dataset, skip it
        if column not in rows[0]:
            continue

        cohort_table = compute_cohort_summary(rows, column)
        tables.extend(cohort_table)

    return tables


def main() -> None:
    validate_input()

    # Ensure the evidence output folder exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    cleaned_rows = []

    # Read the cleaned intermediate dataset produced by feature_engineering.py
    with INPUT_PATH.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError("Cleaned dataset is empty or missing a header row.")

        for row in reader:
            cleaned_rows.append(row)

    # Generate the full cohort prevalence summary
    cohort_summary = build_cohort_table(cleaned_rows)

    # Write the evidence artifact as CSV
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "cohort_dimension",
            "cohort_value",
            "cohort_size",
            "diabetes_count",
            "prevalence_rate",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cohort_summary)

    print(f"Cohort prevalence summary written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()