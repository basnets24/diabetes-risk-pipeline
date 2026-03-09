#!/usr/bin/env python3

from pathlib import Path
import pandas as pd

# Input artifact produced by cohort_analysis.py
INPUT_PATH = Path("out/evidence/cohort_prevalence_summary.csv")

# Output artifact for location analysis
OUTPUT_PATH = Path("out/evidence/location_prevalence_profile.csv")

# Remove very small cohorts
MIN_COHORT_SIZE = 500


def validate_input():
    # Ensure the cohort summary exists
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Cohort summary not found at {INPUT_PATH}. Run cohort_analysis.py first."
        )


def build_location_table(df: pd.DataFrame) -> pd.DataFrame:

    # Keep only location rows
    locations = df[df["cohort_dimension"] == "location"].copy()

    # Remove small cohorts
    locations = locations[locations["cohort_size"] >= MIN_COHORT_SIZE]

    # Sort by prevalence descending
    locations = locations.sort_values(
        by="prevalence_rate",
        ascending=False
    )

    # Add rank column
    locations = locations.reset_index(drop=True)
    locations.insert(0, "rank", locations.index + 1)

    # Rename column for clarity
    locations = locations.rename(columns={"cohort_value": "location"})

    # Clean output columns
    return locations[
        [
            "rank",
            "location",
            "cohort_size",
            "diabetes_count",
            "prevalence_rate",
        ]
    ]


def main():

    validate_input()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(INPUT_PATH)

    location_summary = build_location_table(df)

    location_summary["prevalence_rate"] = location_summary["prevalence_rate"].round(4)

    location_summary.to_csv(OUTPUT_PATH, index=False)

    print(f"Location prevalence summary written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()