#!/usr/bin/env python3

from pathlib import Path
import pandas as pd

# Input produced by feature_engineering.py
INPUT_PATH = Path("out/cleaned_diabetes_data.csv")

# Output evidence artifact for rule-based screening logic
OUTPUT_PATH = Path("out/evidence/risk_rule_flags.csv")


def validate_input():
    # Make sure the cleaned dataset exists before evaluating rules
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found at {INPUT_PATH}. Run feature_engineering.py first."
        )


def evaluate_rule(df, rule_name, mask):
    # Filter the dataset down to only rows that match the rule
    matched = df[mask]

    # Count how many rows matched the rule
    matched_rows = len(matched)

    # Count how many diabetes cases appear inside the matched group
    diabetes_count = matched["diabetes"].sum()

    # Prevalence rate = diabetes cases / matched rows
    prevalence_rate = 0
    if matched_rows > 0:
        prevalence_rate = diabetes_count / matched_rows

    # Return one summary row for this rule
    return {
        "rule_name": rule_name,
        "matched_rows": matched_rows,
        "diabetes_count": diabetes_count,
        "prevalence_rate": prevalence_rate,
    }


def build_rule_table(df):
    rules = []

    # Rule 1: Older adults are a higher-risk population segment
    rules.append(
        evaluate_rule(
            df,
            "Age 55+",
            df["age_bucket"].isin(["55-69", "70+"]),
        )
    )

    # Rule 2: Obesity is a strong diabetes risk factor
    rules.append(
        evaluate_rule(
            df,
            "BMI Obese",
            df["bmi_bucket"] == "Obese",
        )
    )

    # Rule 3: Hypertension is a strong comorbidity associated with diabetes
    rules.append(
        evaluate_rule(
            df,
            "Hypertension",
            df["hypertension"] == 1,
        )
    )

    # Rule 4: Heart disease indicates a very high-risk subgroup
    rules.append(
        evaluate_rule(
            df,
            "Heart Disease",
            df["heart_disease"] == 1,
        )
    )

    # Rule 5: Combined older age and obesity create a more targeted high-risk segment
    rules.append(
        evaluate_rule(
            df,
            "Age 55+ AND Obese",
            df["age_bucket"].isin(["55-69", "70+"]) &
            (df["bmi_bucket"] == "Obese"),
        )
    )

    # Rule 6: Combined hypertension and obesity create another targeted risk segment
    rules.append(
        evaluate_rule(
            df,
            "Hypertension AND Obese",
            (df["hypertension"] == 1) &
            (df["bmi_bucket"] == "Obese"),
        )
    )

    # Convert the list of rule summaries into a table
    table = pd.DataFrame(rules)

    # Rank rules by prevalence so the highest-risk flags appear first
    table = table.sort_values(
        by="prevalence_rate",
        ascending=False,
    )

    # Round prevalence for cleaner stakeholder-facing output
    table["prevalence_rate"] = table["prevalence_rate"].round(4)

    return table


def main():
    validate_input()

    # Ensure the evidence output folder exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Read the cleaned analysis dataset
    df = pd.read_csv(INPUT_PATH)

    # Build the rule-based risk summary
    rule_table = build_rule_table(df)

    # Write the final evidence artifact
    rule_table.to_csv(OUTPUT_PATH, index=False)

    print(f"Risk rule flags written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

