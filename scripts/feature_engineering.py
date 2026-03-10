#!/usr/bin/env python3

import sys
from pathlib import Path
import pandas as pd

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


def clean_text_column(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .replace({"": "Unknown", "nan": "Unknown", "None": "Unknown"})
    )


def normalize_smoking_history(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.strip().str.lower()

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

    return cleaned.map(mapping).fillna("Unknown")


def age_to_bucket(age: float) -> str:
    if pd.isna(age):
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


def bmi_to_bucket(bmi: float) -> str:
    if pd.isna(bmi):
        return "Unknown"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def derive_race(row: pd.Series) -> str:
    matches = [label for column, label in RACE_COLUMNS.items() if row[column] == 1]

    if len(matches) == 1:
        return matches[0]
    if len(matches) == 0:
        return "Unknown"
    return "Multiple"


def clean_categorical_columns(df: pd.DataFrame) -> pd.DataFrame:
    for column in ["gender", "location"]:
        if column in df.columns:
            df[column] = clean_text_column(df[column])

    if "smoking_history" in df.columns:
        df["smoking_history"] = normalize_smoking_history(df["smoking_history"])

    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["race"] = df.apply(derive_race, axis=1)
    df["age_bucket"] = df["age"].apply(age_to_bucket)
    df["bmi_bucket"] = df["bmi"].apply(bmi_to_bucket)
    return df


def build_clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = clean_categorical_columns(df)
    df = add_derived_columns(df)
    return df[ANALYSIS_COLUMNS].copy()


def append_distribution_section(lines: list[str], df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        return

    lines.append(column.upper())
    lines.append("-" * 60)

    counts = df[column].value_counts(dropna=False).sort_index()
    for value, count in counts.items():
        lines.append(f"{value}: {count}")
    lines.append("")


def write_feature_summary(df: pd.DataFrame, output_path: Path) -> None:
    lines: list[str] = []

    lines.append("FEATURE ENGINEERING SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Rows in cleaned dataset: {len(df)}")
    lines.append(f"Columns in cleaned dataset: {len(df.columns)}")
    lines.append("")

    for column in ["race", "age_bucket", "bmi_bucket", "gender", "smoking_history", "location"]:
        append_distribution_section(lines, df, column)

    lines.append("DERIVED FIELD CHECKS")
    lines.append("-" * 60)
    lines.append(f"Unknown race rows: {(df['race'] == 'Unknown').sum()}")
    lines.append(f"Multiple race rows: {(df['race'] == 'Multiple').sum()}")
    lines.append(f"Unknown age bucket rows: {(df['age_bucket'] == 'Unknown').sum()}")
    lines.append(f"Unknown bmi bucket rows: {(df['bmi_bucket'] == 'Unknown').sum()}")
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

    df = pd.read_csv(dataset_path)
    cleaned_df = build_clean_dataset(df)

    cleaned_df.to_csv(cleaned_output_path, index=False)
    write_feature_summary(cleaned_df, summary_output_path)

    print(f"Cleaned dataset written to {cleaned_output_path}")
    print(f"Feature engineering summary written to {summary_output_path}")


if __name__ == "__main__":
    main()