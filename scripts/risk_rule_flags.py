#!/usr/bin/env python3

import csv
from pathlib import Path

# Input produced by feature_engineering.py
INPUT_PATH = Path("out/cleaned_diabetes_data.csv")

# Output evidence artifact for rule-based screening logic
OUTPUT_PATH = Path("out/evidence/risk_rule_flags.csv")


def validate_input() -> None:
    # Make sure the cleaned dataset exists before evaluating rules
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found at {INPUT_PATH}. Run feature_engineering.py first."
        )


def parse_diabetes_value(value: str):
    """
    Convert the diabetes field into an integer 0 or 1 when possible.

    Returns:
        0 or 1 if valid
        None if missing or invalid
    """
    if value is None:
        return None

    cleaned = str(value).strip()

    if cleaned in {"0", "0.0"}:
        return 0
    if cleaned in {"1", "1.0"}:
        return 1

    return None


def parse_binary_flag(value: str):
    """
    Convert a binary indicator field into 0 or 1 when possible.

    Returns:
        0 or 1 if valid
        None if missing or invalid
    """
    if value is None:
        return None

    cleaned = str(value).strip()

    if cleaned in {"0", "0.0"}:
        return 0
    if cleaned in {"1", "1.0"}:
        return 1

    return None


def evaluate_rule(rows: list[dict], rule_name: str, predicate) -> dict:
    """
    Evaluate one rule across all rows in the cleaned dataset.

    For the rows that match the rule:
    - count total matched rows
    - count diabetes-positive rows
    - compute prevalence rate
    """
    matched_rows = 0
    diabetes_count = 0

    for row in rows:
        # Keep only rows that satisfy the rule predicate
        if not predicate(row):
            continue

        matched_rows += 1

        # Count diabetes cases only when the diabetes value is valid and equal to 1
        diabetes_value = parse_diabetes_value(row.get("diabetes", ""))
        if diabetes_value == 1:
            diabetes_count += 1

    # Prevalence rate = diabetes cases / matched rows
    prevalence_rate = 0.0
    if matched_rows > 0:
        prevalence_rate = diabetes_count / matched_rows

    # Return one summary row for this rule
    return {
        "rule_name": rule_name,
        "matched_rows": matched_rows,
        "diabetes_count": diabetes_count,
        "prevalence_rate": round(prevalence_rate, 4),
    }


def is_age_55_plus(row: dict) -> bool:
    """
    Older adults are treated as a higher-risk population segment.
    """
    return row.get("age_bucket", "") in {"55-69", "70+"}


def is_obese(row: dict) -> bool:
    """
    Obesity is treated as a strong diabetes risk factor.
    """
    return row.get("bmi_bucket", "") == "Obese"


def has_hypertension(row: dict) -> bool:
    """
    Hypertension is treated as a strong comorbidity associated with diabetes.
    """
    return parse_binary_flag(row.get("hypertension", "")) == 1


def has_heart_disease(row: dict) -> bool:
    """
    Heart disease indicates a very high-risk subgroup.
    """
    return parse_binary_flag(row.get("heart_disease", "")) == 1


def build_rule_table(rows: list[dict]) -> list[dict]:
    """
    Build the full rule-based screening table.

    Each row in the output summarizes:
    - how many rows matched the rule
    - how many diabetes-positive cases were inside that group
    - the resulting prevalence rate
    """
    rules = []

    # Rule 1: Older adults are a higher-risk population segment
    rules.append(
        evaluate_rule(
            rows,
            "Age 55+",
            lambda row: is_age_55_plus(row),
        )
    )

    # Rule 2: Obesity is a strong diabetes risk factor
    rules.append(
        evaluate_rule(
            rows,
            "BMI Obese",
            lambda row: is_obese(row),
        )
    )

    # Rule 3: Hypertension is a strong comorbidity associated with diabetes
    rules.append(
        evaluate_rule(
            rows,
            "Hypertension",
            lambda row: has_hypertension(row),
        )
    )

    # Rule 4: Heart disease indicates a very high-risk subgroup
    rules.append(
        evaluate_rule(
            rows,
            "Heart Disease",
            lambda row: has_heart_disease(row),
        )
    )

    # Rule 5: Combined older age and obesity create a more targeted high-risk segment
    rules.append(
        evaluate_rule(
            rows,
            "Age 55+ AND Obese",
            lambda row: is_age_55_plus(row) and is_obese(row),
        )
    )

    # Rule 6: Combined hypertension and obesity create another targeted risk segment
    rules.append(
        evaluate_rule(
            rows,
            "Hypertension AND Obese",
            lambda row: has_hypertension(row) and is_obese(row),
        )
    )

    # Rank rules by prevalence so the highest-risk flags appear first
    rules.sort(key=lambda row: row["prevalence_rate"], reverse=True)

    return rules


def main() -> None:
    validate_input()

    # Ensure the evidence output folder exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    cleaned_rows = []

    # Read the cleaned analysis dataset produced by feature_engineering.py
    with INPUT_PATH.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError("Cleaned dataset is empty or missing a header row.")

        for row in reader:
            cleaned_rows.append(row)

    # Build the rule-based risk summary
    rule_table = build_rule_table(cleaned_rows)

    # Write the final evidence artifact
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "rule_name",
            "matched_rows",
            "diabetes_count",
            "prevalence_rate",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rule_table)

    print(f"Risk rule flags written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()