#!/usr/bin/env python3

from pathlib import Path
import pandas as pd

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


def validate_input():
    # Make sure the cleaned dataset exists before running aggregation
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found at {INPUT_PATH}. Run feature_engineering.py first."
        )


def compute_cohort_summary(df: pd.DataFrame, column: str) -> pd.DataFrame:
    # Group by one cohort column and compute:
    # - count = total rows in that cohort
    # - sum = total diabetes cases in that cohort
    grouped = df.groupby(column)["diabetes"].agg(["count", "sum"]).reset_index()

    # Prevalence rate = diabetes cases / total cohort size
    grouped["prevalence_rate"] = grouped["sum"] / grouped["count"]

    # Rename columns so the final output is consistent across all cohort dimensions
    grouped = grouped.rename(
        columns={
            column: "cohort_value",
            "count": "cohort_size",
            "sum": "diabetes_count",
        }
    )

    # Add a column to identify which cohort dimension this block came from
    grouped["cohort_dimension"] = column

    # Keep the final output columns in a clean, predictable order
    return grouped[
        [
            "cohort_dimension",
            "cohort_value",
            "cohort_size",
            "diabetes_count",
            "prevalence_rate",
        ]
    ]


def build_cohort_table(df: pd.DataFrame) -> pd.DataFrame:
    tables = []

    # Build one summary table per cohort dimension
    for column in COHORT_COLUMNS:
        if column not in df.columns:
            continue

        cohort_table = compute_cohort_summary(df, column)
        tables.append(cohort_table)

    # Combine all cohort summaries into one consolidated evidence table
    return pd.concat(tables, ignore_index=True)


def main():
    validate_input()

    # Ensure the evidence output folder exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Read the cleaned intermediate dataset
    df = pd.read_csv(INPUT_PATH)

    # Generate the full cohort prevalence summary
    cohort_summary = build_cohort_table(df)

    # Round prevalence for cleaner output
    cohort_summary["prevalence_rate"] = cohort_summary["prevalence_rate"].round(4)

    # Write the evidence artifact
    cohort_summary.to_csv(OUTPUT_PATH, index=False)

    print(f"Cohort prevalence summary written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()