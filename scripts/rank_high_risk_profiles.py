#!/usr/bin/env python3

import csv
from pathlib import Path

# Input artifact produced by cohort_analysis.py
INPUT_PATH = Path("out/evidence/cohort_prevalence_summary.csv")

# Final ranked decision-driving artifact
OUTPUT_PATH = Path("out/evidence/ranked_high_risk_profiles.csv")

# Only keep cohorts large enough to be meaningful
MIN_COHORT_SIZE = 500

# Number of top high-risk cohorts to return
TOP_N = 20

# Exclude location from this artifact so it stays focused on demographic/clinical risk groups
EXCLUDED_DIMENSIONS = {"location"}


def validate_input() -> None:
    # Make sure the cohort summary exists before ranking
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


def build_cohort_label(row: dict) -> str:
    """
    Convert raw cohort dimension/value pairs into stakeholder-friendly labels.
    """
    dimension = row["cohort_dimension"]
    value = row["cohort_value"]

    if dimension == "age_bucket":
        return f"Age group: {value}"

    if dimension == "bmi_bucket":
        return f"BMI category: {value}"

    if dimension == "smoking_history":
        return f"Smoking status: {value}"

    if dimension == "hypertension":
        return f"Hypertension: {'Yes' if value == '1' else 'No'}"

    if dimension == "heart_disease":
        return f"Heart disease: {'Yes' if value == '1' else 'No'}"

    if dimension == "race":
        return f"Race: {value}"

    if dimension == "gender":
        return f"Gender: {value}"

    return f"{dimension}: {value}"


def build_ranked_table(rows: list[dict]) -> list[dict]:
    """
    Build the final ranked table of high-risk cohorts.

    Steps:
    1. Exclude dimensions we do not want in this artifact
    2. Exclude small cohorts below the minimum size threshold
    3. Sort by prevalence rate descending, then cohort size descending
    4. Keep only the top N rows
    5. Add a stakeholder-friendly label and 1-based rank
    """
    filtered_rows = []

    for row in rows:
        dimension = row.get("cohort_dimension", "")
        if dimension in EXCLUDED_DIMENSIONS:
            continue

        cohort_size = parse_int_value(row.get("cohort_size", ""))
        diabetes_count = parse_int_value(row.get("diabetes_count", ""))
        prevalence_rate = parse_float_value(row.get("prevalence_rate", ""))

        # Skip rows that are missing required numeric values
        if cohort_size is None or diabetes_count is None or prevalence_rate is None:
            continue

        # Remove small cohorts so rankings are not driven by tiny groups
        if cohort_size < MIN_COHORT_SIZE:
            continue

        filtered_rows.append(
            {
                "cohort_dimension": dimension,
                "cohort_value": row.get("cohort_value", ""),
                "cohort_size": cohort_size,
                "diabetes_count": diabetes_count,
                "prevalence_rate": prevalence_rate,
            }
        )

    # Sort by prevalence first, then cohort size for more stable tie-breaking
    filtered_rows.sort(
        key=lambda row: (row["prevalence_rate"], row["cohort_size"]),
        reverse=True,
    )

    # Keep only the top N high-risk cohorts
    top_rows = filtered_rows[:TOP_N]

    ranked_rows = []

    # Add a 1-based rank and stakeholder-friendly label
    for index, row in enumerate(top_rows, start=1):
        ranked_rows.append(
            {
                "rank": index,
                "cohort_label": build_cohort_label(row),
                "cohort_size": row["cohort_size"],
                "diabetes_count": row["diabetes_count"],
                "prevalence_rate": round(row["prevalence_rate"], 4),
            }
        )

    return ranked_rows


def main() -> None:
    validate_input()

    # Ensure the output folder exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    input_rows = []

    # Read the cohort-level prevalence summary produced by cohort_analysis.py
    with INPUT_PATH.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError("Cohort prevalence summary is empty or missing a header row.")

        for row in reader:
            input_rows.append(row)

    # Build the ranked high-risk cohort table
    ranked_profiles = build_ranked_table(input_rows)

    # Write the final ranked artifact
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "rank",
            "cohort_label",
            "cohort_size",
            "diabetes_count",
            "prevalence_rate",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ranked_profiles)

    print(f"Ranked high-risk profiles written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()