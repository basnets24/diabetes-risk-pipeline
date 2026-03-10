#!/usr/bin/env python3

import csv
from pathlib import Path

# Input artifact produced by cohort_analysis.py
INPUT_PATH = Path("out/evidence/cohort_prevalence_summary.csv")

# Output artifact for location analysis
OUTPUT_PATH = Path("out/evidence/location_prevalence_profile.csv")

# Remove very small cohorts
MIN_COHORT_SIZE = 500


def validate_input() -> None:
    # Ensure the cohort summary exists before building the location artifact
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Cohort summary not found at {INPUT_PATH}. Run cohort_analysis.py first."
        )


def parse_int_value(value: str):
    """
    Convert a CSV string into an integer when possible.

    Returns:
        int if valid
        None if missing or invalid
    """
    if value is None:
        return None

    cleaned = str(value).strip()
    if cleaned == "":
        return None

    try:
        return int(cleaned)
    except ValueError:
        try:
            numeric_value = float(cleaned)
            if numeric_value.is_integer():
                return int(numeric_value)
        except ValueError:
            pass

    return None


def parse_float_value(value: str):
    """
    Convert a CSV string into a float when possible.

    Returns:
        float if valid
        None if missing or invalid
    """
    if value is None:
        return None

    cleaned = str(value).strip()
    if cleaned == "":
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def build_location_table(rows: list[dict]) -> list[dict]:
    """
    Build a ranked location prevalence table.

    Steps:
    1. Keep only rows where cohort_dimension == "location"
    2. Remove locations smaller than MIN_COHORT_SIZE
    3. Sort by prevalence descending
    4. Add a 1-based rank column
    5. Rename cohort_value to location in the final output
    """
    location_rows = []

    for row in rows:
        # Keep only the rows representing location cohorts
        if row.get("cohort_dimension", "") != "location":
            continue

        cohort_size = parse_int_value(row.get("cohort_size", ""))
        diabetes_count = parse_int_value(row.get("diabetes_count", ""))
        prevalence_rate = parse_float_value(row.get("prevalence_rate", ""))

        # Skip rows that are missing required numeric values
        if cohort_size is None or diabetes_count is None or prevalence_rate is None:
            continue

        # Remove very small location cohorts
        if cohort_size < MIN_COHORT_SIZE:
            continue

        location_rows.append(
            {
                "location": row.get("cohort_value", ""),
                "cohort_size": cohort_size,
                "diabetes_count": diabetes_count,
                "prevalence_rate": prevalence_rate,
            }
        )

    # Sort by prevalence descending
    location_rows.sort(key=lambda row: row["prevalence_rate"], reverse=True)

    ranked_rows = []

    # Add a 1-based rank column for stakeholder-friendly output
    for index, row in enumerate(location_rows, start=1):
        ranked_rows.append(
            {
                "rank": index,
                "location": row["location"],
                "cohort_size": row["cohort_size"],
                "diabetes_count": row["diabetes_count"],
                "prevalence_rate": round(row["prevalence_rate"], 4),
            }
        )

    return ranked_rows


def main() -> None:
    validate_input()

    # Ensure the output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    input_rows = []

    # Read the cohort prevalence summary produced by cohort_analysis.py
    with INPUT_PATH.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError("Cohort prevalence summary is empty or missing a header row.")

        for row in reader:
            input_rows.append(row)

    # Build the ranked location prevalence table
    location_summary = build_location_table(input_rows)

    # Write the final location artifact
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "rank",
            "location",
            "cohort_size",
            "diabetes_count",
            "prevalence_rate",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(location_summary)

    print(f"Location prevalence summary written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()