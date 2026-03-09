#!/usr/bin/env python3

import sys
from pathlib import Path
import pandas as pd

RACE_COLUMNS = [
    "race:AfricanAmerican",
    "race:Asian",
    "race:Caucasian",
    "race:Hispanic",
    "race:Other",
]

BINARY_COLUMNS = [
    "hypertension",
    "heart_disease",
    "diabetes",
    *RACE_COLUMNS,
]

NUMERIC_COLUMNS = [
    "year",
    "age",
    "bmi",
    "hbA1c_level",
    "blood_glucose_level",
]


def get_dataset_path() -> Path:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/data_quality.py <dataset_path>")
        sys.exit(1)

    dataset_path = Path(sys.argv[1])
    if not dataset_path.exists():
        print(f"Error: dataset not found at '{dataset_path}'")
        sys.exit(1)

    return dataset_path


def add_section(lines: list[str], title: str) -> None:
    lines.append(title)
    lines.append("-" * 60)


def get_null_count_lines(df: pd.DataFrame) -> list[str]:
    null_counts = df.isna().sum().sort_values(ascending=False)
    return [f"{column}: {count}" for column, count in null_counts.items()]


def get_numeric_range_lines(df: pd.DataFrame) -> list[str]:
    lines = []
    for column in NUMERIC_COLUMNS:
        if column not in df.columns:
            continue

        values = df[column].dropna()
        if values.empty:
            lines.append(f"{column}: all values are null")
        else:
            lines.append(f"{column}: min={values.min()}, max={values.max()}")
    return lines


def get_binary_validation_lines(df: pd.DataFrame) -> list[str]:
    lines = []
    for column in BINARY_COLUMNS:
        if column not in df.columns:
            continue

        unique_values = sorted(df[column].dropna().unique().tolist())
        invalid_count = int((~df[column].isin([0, 1]) & df[column].notna()).sum())
        lines.append(
            f"{column}: unique_values={unique_values}, invalid_count={invalid_count}"
        )
    return lines


def get_diabetes_distribution_lines(df: pd.DataFrame) -> list[str]:
    if "diabetes" not in df.columns:
        return ["Skipped: diabetes column missing"]

    total_rows = len(df)
    counts = df["diabetes"].value_counts(dropna=False).sort_index()

    lines = []
    for value, count in counts.items():
        percentage = (count / total_rows * 100) if total_rows else 0
        lines.append(f"{value}: {count} ({percentage:.2f}%)")
    return lines


def get_race_consistency_lines(df: pd.DataFrame) -> list[str]:
    if not all(column in df.columns for column in RACE_COLUMNS):
        return ["Skipped: one or more race one-hot columns are missing."]

    race_sum = df[RACE_COLUMNS].sum(axis=1)

    return [
        f"Rows with exactly one race flag = 1: {(race_sum == 1).sum()}",
        f"Rows with all race flags = 0: {(race_sum == 0).sum()}",
        f"Rows with multiple race flags = 1: {(race_sum > 1).sum()}",
        f"Rows with non-binary values in race columns: {(~df[RACE_COLUMNS].isin([0, 1])).any(axis=1).sum()}",
    ]


def get_invalid_value_lines(df: pd.DataFrame) -> list[str]:
    lines = []

    if "age" in df.columns:
        lines.append(f"age outside [0, 120]: {((df['age'] < 0) | (df['age'] > 120)).sum()}")

    if "bmi" in df.columns:
        lines.append(f"negative bmi values: {(df['bmi'] < 0).sum()}")

    if "year" in df.columns:
        lines.append(f"year outside [1900, 2100]: {((df['year'] < 1900) | (df['year'] > 2100)).sum()}")

    if "hbA1c_level" in df.columns:
        lines.append(f"negative hbA1c_level values: {(df['hbA1c_level'] < 0).sum()}")

    if "blood_glucose_level" in df.columns:
        lines.append(f"negative blood_glucose_level values: {(df['blood_glucose_level'] < 0).sum()}")

    return lines if lines else ["No invalid value checks were run."]


def build_report(df: pd.DataFrame, dataset_path: Path) -> str:
    lines: list[str] = []

    lines.append("DATA QUALITY REPORT")
    lines.append("=" * 60)
    lines.append(f"Dataset path: {dataset_path}")
    lines.append(f"Rows: {len(df)}")
    lines.append(f"Columns: {len(df.columns)}")
    lines.append("")

    add_section(lines, "NULL COUNTS BY COLUMN")
    lines.extend(get_null_count_lines(df))
    lines.append("")

    add_section(lines, "NUMERIC RANGES")
    lines.extend(get_numeric_range_lines(df))
    lines.append("")

    add_section(lines, "BINARY FIELD VALIDATION")
    lines.extend(get_binary_validation_lines(df))
    lines.append("")

    add_section(lines, "DIABETES CLASS DISTRIBUTION")
    lines.extend(get_diabetes_distribution_lines(df))
    lines.append("")

    add_section(lines, "RACE ONE-HOT CONSISTENCY CHECK")
    lines.extend(get_race_consistency_lines(df))
    lines.append("")

    add_section(lines, "INVALID VALUE CHECKS")
    lines.extend(get_invalid_value_lines(df))
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    dataset_path = get_dataset_path()
    output_path = Path("out/evidence/data_quality_report.txt")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(dataset_path)
    report = build_report(df, dataset_path)

    output_path.write_text(report, encoding="utf-8")
    print(f"Data quality report written to {output_path}")


if __name__ == "__main__":
    main()