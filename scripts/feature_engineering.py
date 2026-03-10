#!/usr/bin/env python3

import sys
import csv
from pathlib import Path
from collections import Counter

RACE_COLUMNS = {
    "race:AfricanAmerican": "AfricanAmerican",
    "race:Asian": "Asian",
    "race:Caucasian": "Caucasian",
    "race:Hispanic": "Hispanic",
    "race:Other": "Other",
}

ANALYSIS_COLUMNS = [
    "year",
    "gender",
    "location",
    "race",
    "hypertension",
    "heart_disease",
    "smoking_history",
    "diabetes",
    "age_bucket",
    "bmi_bucket",
]


def get_dataset_path() -> Path:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/feature_engineering.py <dataset_path>")
        sys.exit(1)

    dataset_path = Path(sys.argv[1])
    if not dataset_path.exists():
        print(f"Error: dataset not found at '{dataset_path}'")
        sys.exit(1)

    return dataset_path


def is_missing(value: str) -> bool:
    if value is None:
        return True
    cleaned = str(value).strip()
    return cleaned == "" or cleaned.lower() in {"nan", "none", "null", "n/a", "na"}


def clean_text_value(value: str) -> str:
    if is_missing(value):
        return "Unknown"
    return str(value).strip()


def normalize_smoking_history(value: str) -> str:
    cleaned = "" if value is None else str(value).strip().lower()

    mapping = {
        "never": "Never",
        "former": "Former",
        "ever": "Former",
        "not current": "Former",
        "current": "Current",
        "no info": "Unknown",
        "unknown": "Unknown",
        "nan": "Unknown",
        "none": "Unknown",
        "": "Unknown",
    }

    return mapping.get(cleaned, "Unknown")


def parse_float(value: str):
    if is_missing(value):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def parse_int_like(value: str):
    if is_missing(value):
        return None
    raw = str(value).strip()
    try:
        return int(raw)
    except ValueError:
        try:
            f = float(raw)
            if f.is_integer():
                return int(f)
        except ValueError:
            pass
    return None


def age_to_bucket(age) -> str:
    if age is None:
        return "Unknown"
    if age < 25:
        return "0-24"
    if age < 40:
        return "25-39"
    if age < 55:
        return "40-54"
    if age < 70:
        return "55-69"
    return "70+"


def bmi_to_bucket(bmi) -> str:
    if bmi is None:
        return "Unknown"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def parse_binary_flag(value: str):
    if is_missing(value):
        return None

    cleaned = str(value).strip()
    if cleaned in {"1", "1.0"}:
        return 1
    if cleaned in {"0", "0.0"}:
        return 0

    return None


def derive_race(row: dict) -> str:
    matches = []

    for column, label in RACE_COLUMNS.items():
        if parse_binary_flag(row.get(column, "")) == 1:
            matches.append(label)

    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:
        return "Unknown"
    return "Multiple"


def clean_categorical_fields(row: dict) -> dict:
    cleaned = dict(row)

    if "gender" in cleaned:
        cleaned["gender"] = clean_text_value(cleaned["gender"])

    if "location" in cleaned:
        cleaned["location"] = clean_text_value(cleaned["location"])

    if "smoking_history" in cleaned:
        cleaned["smoking_history"] = normalize_smoking_history(cleaned["smoking_history"])

    return cleaned


def add_derived_fields(row: dict) -> dict:
    enriched = dict(row)

    age = parse_float(enriched.get("age", ""))
    bmi = parse_float(enriched.get("bmi", ""))

    enriched["race"] = derive_race(enriched)
    enriched["age_bucket"] = age_to_bucket(age)
    enriched["bmi_bucket"] = bmi_to_bucket(bmi)

    return enriched


def normalize_output_value(column: str, value: str) -> str:
    if column in {"gender", "location"}:
        return clean_text_value(value)

    if column == "smoking_history":
        return normalize_smoking_history(value)

    if column in {"year", "hypertension", "heart_disease", "diabetes"}:
        if is_missing(value):
            return ""
        return str(value).strip()

    return "" if value is None else str(value).strip()


def build_clean_row(row: dict) -> dict:
    row = clean_categorical_fields(row)
    row = add_derived_fields(row)

    clean_row = {}
    for column in ANALYSIS_COLUMNS:
        clean_row[column] = normalize_output_value(column, row.get(column, ""))
    return clean_row


def append_distribution_section(lines: list[str], rows: list[dict], column: str) -> None:
    if not rows or column not in rows[0]:
        return

    lines.append(column.upper())
    lines.append("-" * 60)

    counts = Counter(row.get(column, "") for row in rows)
    for value in sorted(counts, key=lambda x: str(x)):
        lines.append(f"{value}: {counts[value]}")
    lines.append("")


def write_feature_summary(rows: list[dict], output_path: Path) -> None:
    lines: list[str] = []

    lines.append("FEATURE ENGINEERING SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Rows in cleaned dataset: {len(rows)}")
    lines.append(f"Columns in cleaned dataset: {len(ANALYSIS_COLUMNS)}")
    lines.append("")

    for column in ["race", "age_bucket", "bmi_bucket", "gender", "smoking_history", "location"]:
        append_distribution_section(lines, rows, column)

    lines.append("DERIVED FIELD CHECKS")
    lines.append("-" * 60)
    lines.append(f"Unknown race rows: {sum(1 for row in rows if row['race'] == 'Unknown')}")
    lines.append(f"Multiple race rows: {sum(1 for row in rows if row['race'] == 'Multiple')}")
    lines.append(f"Unknown age bucket rows: {sum(1 for row in rows if row['age_bucket'] == 'Unknown')}")
    lines.append(f"Unknown bmi bucket rows: {sum(1 for row in rows if row['bmi_bucket'] == 'Unknown')}")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    dataset_path = get_dataset_path()

    out_dir = Path("out")
    evidence_dir = Path("out/evidence")
    out_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    cleaned_output_path = out_dir / "cleaned_diabetes_data.csv"
    summary_output_path = evidence_dir / "feature_engineering_summary.txt"

    cleaned_rows = []

    with dataset_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            print("Error: input file is empty or missing a header row")
            sys.exit(1)

        for row in reader:
            cleaned_rows.append(build_clean_row(row))

    with cleaned_output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=ANALYSIS_COLUMNS)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    write_feature_summary(cleaned_rows, summary_output_path)

    print(f"Cleaned dataset written to {cleaned_output_path}")
    print(f"Feature engineering summary written to {summary_output_path}")


if __name__ == "__main__":
    main()