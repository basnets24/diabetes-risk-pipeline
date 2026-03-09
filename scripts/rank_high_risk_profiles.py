#!/usr/bin/env python3

from pathlib import Path
import pandas as pd

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


def build_cohort_label(row: pd.Series) -> str:
    # Convert raw cohort dimension/value pairs into stakeholder-friendly labels
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


def build_ranked_table(df: pd.DataFrame) -> pd.DataFrame:
    # Remove dimensions that do not belong in this artifact
    filtered = df[~df["cohort_dimension"].isin(EXCLUDED_DIMENSIONS)].copy()

    # Remove small cohorts so rankings are not driven by tiny groups
    filtered = filtered[filtered["cohort_size"] >= MIN_COHORT_SIZE].copy()

    # Sort by prevalence first, then cohort size to make near-ties more stable
    ranked = filtered.sort_values(
        by=["prevalence_rate", "cohort_size"],
        ascending=[False, False]
    ).head(TOP_N)

    # Add a readable label for stakeholder-facing output
    ranked["cohort_label"] = ranked.apply(build_cohort_label, axis=1)

    # Add a 1-based rank column
    ranked = ranked.reset_index(drop=True)
    ranked.insert(0, "rank", ranked.index + 1)

    # Keep output columns in a clean order
    return ranked[
        [
            "rank",
            "cohort_label",
            "cohort_size",
            "diabetes_count",
            "prevalence_rate",
        ]
    ]


def main() -> None:
    validate_input()

    # Ensure the output folder exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Read the cohort-level prevalence summary
    df = pd.read_csv(INPUT_PATH)

    # Build the ranked high-risk cohort table
    ranked_profiles = build_ranked_table(df)

    # Round prevalence for cleaner output
    ranked_profiles["prevalence_rate"] = ranked_profiles["prevalence_rate"].round(4)

    # Write the final ranked artifact
    ranked_profiles.to_csv(OUTPUT_PATH, index=False)

    print(f"Ranked high-risk profiles written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()