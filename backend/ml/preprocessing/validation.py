"""
validation.py

Production-ready dataset validation module for MediGenie.

Features
--------
✓ Schema-driven validation
✓ Automatic header detection
✓ Automatic target detection
✓ Required column validation
✓ Numeric range validation
✓ Category validation
✓ Missing value analysis
✓ Duplicate detection
✓ Statistical summaries
✓ JSON validation reports
✓ Generic support for all disease datasets
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from dataclasses import asdict
from dataclasses import dataclass

from datetime import datetime

from pathlib import Path

from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.ml.preprocessing.schema_loader import (
    load_schema,
)

# ==============================================================================
# Logging
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)

# ==============================================================================
# Exceptions
# ==============================================================================


class DatasetValidationError(Exception):
    """Base validation exception."""


class DatasetNotFoundError(
    DatasetValidationError
):
    """Dataset file not found."""


class InvalidDatasetError(
    DatasetValidationError
):
    """Dataset cannot be loaded."""


class TargetColumnError(
    DatasetValidationError
):
    """Target column missing."""


class SchemaValidationError(
    DatasetValidationError
):
    """Dataset violates schema."""


# ==============================================================================
# Configuration
# ==============================================================================


@dataclass(slots=True)
class ValidationConfig:

    dataset_path: Path

    dataset_name: str

    output_directory: Path

    save_report: bool = True

    verbose: bool = True

    check_duplicates: bool = True

    check_missing: bool = True


# ==============================================================================
# Validation Report
# ==============================================================================


@dataclass(slots=True)
class ValidationReport:

    dataset_name: str

    validation_time: str

    validation_status: str

    rows: int

    columns: int

    duplicate_rows: int

    missing_values: dict[str, int]

    column_types: dict[str, str]

    target_distribution: dict[str, int]

    memory_usage_kb: float


# ==============================================================================
# Dataset Validator
# ==============================================================================


class DatasetValidator:
    """
    Generic dataset validator.

    Every disease dataset uses the same validator.

    Validation rules come from the schema.
    """

    def __init__(
        self,
        config: ValidationConfig,
    ):

        self.config = config

        self.schema = load_schema(
            config.dataset_name
        )

        self.df: pd.DataFrame | None = None

        logger.info(
            "Loaded schema: %s",
            self.schema.name,
        )

    @property
    def dataframe(self) -> pd.DataFrame:

        if self.df is None:

            raise DatasetValidationError(
                "Dataset has not been loaded."
            )

        return self.df
        # ==========================================================================
    # File Validation
    # ==========================================================================

    def validate_file(self) -> None:
        """
        Validate dataset file before loading.
        """

        logger.info("Checking dataset file...")

        path = self.config.dataset_path

        if not path.exists():
            raise DatasetNotFoundError(
                f"Dataset not found:\n{path}"
            )

        if not path.is_file():
            raise DatasetValidationError(
                f"{path} is not a file."
            )

        if path.suffix.lower() != ".csv":
            raise DatasetValidationError(
                "Only CSV datasets are supported."
            )

        logger.info("Dataset file validation passed.")

    # ==========================================================================
    # Dataset Loading
    # ==========================================================================

def load_dataset(self) -> None:
    """
    Load dataset using schema configuration.
    """

    logger.info("Loading dataset...")

    try:
        self.df = pd.read_csv(
            self.config.dataset_path,
            header=self.schema.header,
            names=self.schema.columns,
            na_values=["?", "NA", "N/A", ""],
        )

    except Exception as exc:
        raise InvalidDatasetError(
            f"Unable to load dataset.\n{exc}"
        ) from exc

    if self.df.empty:
        raise InvalidDatasetError(
            "Dataset is empty."
        )

    logger.info(
        "Dataset loaded successfully (%d rows × %d columns).",
        len(self.df),
        len(self.df.columns),
    )

    # ==========================================================================
    # Required Column Validation
    # ==========================================================================

    def validate_required_columns(self) -> None:
        """
        Ensure every required column exists.
        """

        logger.info(
            "Validating required columns..."
        )

        missing_columns = [

            column

            for column in self.schema.required_columns

            if column not in self.df.columns

        ]

        if missing_columns:

            raise SchemaValidationError(

                "Missing required columns:\n"

                + "\n".join(missing_columns)

            )

        logger.info(
            "Required columns validated."
        )

    # ==========================================================================
    # Target Validation
    # ==========================================================================

    def validate_target(self) -> None:
        """
        Validate target column.
        """

        logger.info(
            "Validating target column..."
        )

        if self.schema.target_column not in self.df.columns:

            raise TargetColumnError(

                f"Target column "

                f"'{self.schema.target_column}' "

                f"not found."

            )

        logger.info(
            "Target column validated."
        )

    # ==========================================================================
    # Dataset Summary
    # ==========================================================================

    def dataset_summary(self) -> dict[str, Any]:
        """
        Return dataset summary.
        """

        df = self.dataframe

        return {

            "rows": int(df.shape[0]),

            "columns": int(df.shape[1]),

            "memory_usage_kb": round(

                df.memory_usage(
                    deep=True
                ).sum() / 1024,

                2,

            ),

            "column_names": list(df.columns),

        }

    # ==========================================================================
    # Initialization Pipeline
    # ==========================================================================

    def initialize(self) -> None:
        """
        Execute initialization.
        """

        self.validate_file()

        self.load_dataset()

        self.validate_required_columns()

        self.validate_target()

        logger.info(
            "Initialization completed."
        )
            # ==========================================================================
    # Numeric Range Validation
    # ==========================================================================

    def validate_numeric_ranges(self) -> None:
        """
        Validate numeric columns using schema ranges.
        """

        logger.info("Validating numeric ranges...")

        for column, limits in self.schema.numeric_ranges.items():

            if column not in self.df.columns:
                continue

            minimum, maximum = limits

            series = pd.to_numeric(
                self.df[column],
                errors="coerce",
            )

            invalid = series[
                (series < minimum) |
                (series > maximum)
            ]

            if not invalid.empty:

                raise SchemaValidationError(

                    f"Column '{column}' contains "

                    f"{len(invalid)} value(s) outside "

                    f"allowed range "

                    f"[{minimum}, {maximum}]."

                )

        logger.info(
            "Numeric range validation passed."
        )

    # ==========================================================================
    # Allowed Category Validation
    # ==========================================================================

    def validate_allowed_categories(self) -> None:
        """
        Validate categorical values.
        """

        logger.info(
            "Validating categorical values..."
        )

        for column, allowed_values in (
            self.schema.allowed_categories.items()
        ):

            if column not in self.df.columns:
                continue

            values = set(

                self.df[column]
                .dropna()
                .unique()
                .tolist()

            )

            invalid_values = values.difference(
                set(allowed_values)
            )

            if invalid_values:

                raise SchemaValidationError(

                    f"Column '{column}' contains "

                    f"invalid values: "

                    f"{sorted(invalid_values)}"

                )

        logger.info(
            "Categorical validation passed."
        )

    # ==========================================================================
    # Missing Value Analysis
    # ==========================================================================

    def validate_missing_values(self) -> dict[str, int]:
        """
        Analyze missing values.
        """

        logger.info(
            "Checking missing values..."
        )

        missing = (

            self.df.isna()
            .sum()
            .astype(int)
            .to_dict()

        )

        total_missing = sum(
            missing.values()
        )

        logger.info(
            "Total missing values: %d",
            total_missing,
        )

        return missing

    # ==========================================================================
    # Duplicate Row Validation
    # ==========================================================================

    def validate_duplicate_rows(self) -> int:
        """
        Count duplicate rows.
        """

        duplicates = int(

            self.df.duplicated().sum()

        )

        logger.info(
            "Duplicate rows: %d",
            duplicates,
        )

        return duplicates

    # ==========================================================================
    # Duplicate Column Validation
    # ==========================================================================

    def validate_duplicate_columns(self) -> list[str]:
        """
        Detect duplicate columns.
        """

        duplicate_columns = []

        columns = list(self.df.columns)

        for i in range(len(columns)):

            for j in range(i + 1, len(columns)):

                col1 = columns[i]
                col2 = columns[j]

                if self.df[col1].equals(
                    self.df[col2]
                ):

                    duplicate_columns.append(
                        col2
                    )

        if duplicate_columns:

            logger.warning(

                "Duplicate columns detected: %s",

                ", ".join(duplicate_columns),

            )

        else:

            logger.info(
                "No duplicate columns detected."
            )

        return duplicate_columns

    # ==========================================================================
    # Complete Validation Pipeline
    # ==========================================================================

    def validate_schema(self) -> None:
        """
        Execute schema validation.
        """

        self.validate_numeric_ranges()

        self.validate_allowed_categories()

        logger.info(
            "Schema validation completed."
        )
            # ==========================================================================
    # Dataset Statistics
    # ==========================================================================

    def dataset_statistics(self) -> dict[str, Any]:
        """
        Generate dataset statistics.
        """

        df = self.dataframe

        statistics = {}

        numeric_columns = df.select_dtypes(
            include=[np.number]
        ).columns

        for column in numeric_columns:

            statistics[column] = {

                "mean": round(
                    float(df[column].mean()),
                    4,
                ),

                "median": round(
                    float(df[column].median()),
                    4,
                ),

                "std": round(
                    float(df[column].std()),
                    4,
                ),

                "min": round(
                    float(df[column].min()),
                    4,
                ),

                "max": round(
                    float(df[column].max()),
                    4,
                ),

            }

        return statistics

    # ==========================================================================
    # Target Distribution
    # ==========================================================================

    def target_distribution(self) -> dict[str, int]:
        """
        Return target class distribution.
        """

        target = self.schema.target_column

        distribution = (

            self.df[target]
            .value_counts()
            .sort_index()
            .to_dict()

        )

        return {

            str(key): int(value)

            for key, value

            in distribution.items()

        }

    # ==========================================================================
    # Column Types
    # ==========================================================================

    def column_types(self) -> dict[str, str]:
        """
        Return dataframe column types.
        """

        return {

            column: str(dtype)

            for column, dtype

            in self.df.dtypes.items()

        }

    # ==========================================================================
    # Memory Usage
    # ==========================================================================

    def memory_usage(self) -> float:
        """
        Dataset memory usage in KB.
        """

        return round(

            self.df.memory_usage(
                deep=True
            ).sum() / 1024,

            2,

        )

    # ==========================================================================
    # Validation Report
    # ==========================================================================

    def generate_report(self) -> ValidationReport:
        """
        Generate validation report.
        """

        logger.info(
            "Generating validation report..."
        )

        report = ValidationReport(

            dataset_name=self.schema.name,

            validation_time=datetime.now().isoformat(),

            validation_status="SUCCESS",

            rows=int(self.df.shape[0]),

            columns=int(self.df.shape[1]),

            duplicate_rows=self.validate_duplicate_rows(),

            missing_values=self.validate_missing_values(),

            column_types=self.column_types(),

            target_distribution=self.target_distribution(),

            memory_usage_kb=self.memory_usage(),

        )

        logger.info(
            "Validation report generated."
        )

        return report

    # ==========================================================================
    # Console Summary
    # ==========================================================================

    def print_summary(
        self,
        report: ValidationReport,
    ) -> None:
        """
        Print validation summary.
        """

        print()

        print("=" * 70)

        print("VALIDATION SUMMARY")

        print("=" * 70)

        print(
            f"Dataset      : {report.dataset_name}"
        )

        print(
            f"Rows         : {report.rows}"
        )

        print(
            f"Columns      : {report.columns}"
        )

        print(
            f"Memory (KB)  : {report.memory_usage_kb}"
        )

        print(
            f"Duplicates   : {report.duplicate_rows}"
        )

        print()

        print("Missing Values")

        for column, count in report.missing_values.items():

            print(
                f"  {column:<20}{count}"
            )

        print()

        print("Target Distribution")

        for label, count in (

            report.target_distribution.items()

        ):

            print(

                f"  Class {label:<6}{count}"

            )

        print()

        print("=" * 70)
            # ==========================================================================
    # Save Validation Report
    # ==========================================================================

    def save_report(
        self,
        report: ValidationReport,
    ) -> Path:
        """
        Save validation report as JSON.
        """

        if not self.config.save_report:

            logger.info(
                "Report saving disabled."
            )

            return Path()

        self.config.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        report_path = (
            self.config.output_directory
            / "validation_report.json"
        )

        with open(
            report_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                asdict(report),
                file,
                indent=4,
            )

        logger.info(
            "Validation report saved: %s",
            report_path,
        )

        return report_path

    # ==========================================================================
    # Complete Validation Pipeline
    # ==========================================================================

    def validate(self) -> ValidationReport:
        """
        Execute complete validation pipeline.
        """

        logger.info(
            "=" * 70
        )

        logger.info(
            "Starting dataset validation..."
        )

        self.initialize()

        self.validate_schema()

        report = self.generate_report()

        self.save_report(report)

        if self.config.verbose:

            self.print_summary(report)

        logger.info(
            "Validation completed successfully."
        )

        return report


class DatasetValidator:
    """
    Working dataset validator used by the CLI.

    This replaces the partially mis-indented class body above.
    """

    def __init__(self, config: ValidationConfig):

        self.config = config

        self.schema = load_schema(config.dataset_name)

        self.df: pd.DataFrame | None = None

        logger.info("Loaded schema: %s", self.schema.name)

    @property
    def dataframe(self) -> pd.DataFrame:

        if self.df is None:
            raise DatasetValidationError("Dataset has not been loaded.")

        return self.df

    def validate_file(self) -> None:

        logger.info("Checking dataset file...")

        path = self.config.dataset_path

        if not path.exists():
            raise DatasetNotFoundError(f"Dataset not found:\n{path}")

        if not path.is_file():
            raise DatasetValidationError(f"{path} is not a file.")

        if path.suffix.lower() != ".csv":
            raise DatasetValidationError("Only CSV datasets are supported.")

        logger.info("Dataset file validation passed.")

    def load_dataset(self) -> None:

        logger.info("Loading dataset...")

        try:
            self.df = pd.read_csv(
                self.config.dataset_path,
                header=self.schema.header,
                names=self.schema.columns,
                na_values=["?", "NA", "N/A", ""],
            )
        except Exception as exc:
            raise InvalidDatasetError(f"Unable to load dataset.\n{exc}") from exc

        if self.df.empty:
            raise InvalidDatasetError("Dataset is empty.")

        logger.info(
            "Dataset loaded successfully (%d rows × %d columns).",
            len(self.df),
            len(self.df.columns),
        )

    def validate_required_columns(self) -> None:

        logger.info("Validating required columns...")

        missing_columns = [
            column
            for column in self.schema.required_columns
            if column not in self.df.columns
        ]

        if missing_columns:
            raise SchemaValidationError(
                "Missing required columns:\n" + "\n".join(missing_columns)
            )

        logger.info("Required columns validated.")

    def validate_target(self) -> None:

        logger.info("Validating target column...")

        if self.schema.target_column not in self.df.columns:
            raise TargetColumnError(
                f"Target column '{self.schema.target_column}' not found."
            )

        logger.info("Target column validated.")

    def validate_numeric_ranges(self) -> None:

        logger.info("Validating numeric ranges...")

        for column, limits in self.schema.numeric_ranges.items():

            if column not in self.df.columns:
                continue

            minimum, maximum = limits

            series = pd.to_numeric(self.df[column], errors="coerce")
            invalid = series[(series < minimum) | (series > maximum)]

            if not invalid.empty:
                raise SchemaValidationError(
                    f"Column '{column}' contains {len(invalid)} value(s) outside allowed range [{minimum}, {maximum}]."
                )

        logger.info("Numeric range validation passed.")

    def validate_allowed_categories(self) -> None:

        logger.info("Validating allowed categories...")

        for column, allowed_values in self.schema.allowed_categories.items():

            if column not in self.df.columns:
                continue

            values = set(self.df[column].dropna().unique())
            invalid = values - set(allowed_values)

            if invalid:
                raise SchemaValidationError(
                    f"Column '{column}' contains invalid categories: {sorted(invalid)}"
                )

        logger.info("Category validation passed.")

    def validate_missing_values(self) -> dict[str, int]:

        missing = self.df.isna().sum()

        return {
            column: int(count)
            for column, count in missing.items()
            if count > 0
        }

    def validate_duplicate_rows(self) -> int:

        return int(self.df.duplicated().sum())

    def target_distribution(self) -> dict[str, int]:

        target = self.schema.target_column

        return {
            str(key): int(value)
            for key, value in self.df[target].value_counts(dropna=False).sort_index().items()
        }

    def dataset_summary(self) -> dict[str, Any]:

        df = self.dataframe

        return {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "memory_usage_kb": round(df.memory_usage(deep=True).sum() / 1024, 2),
            "column_names": list(df.columns),
        }

    def initialize(self) -> None:

        self.validate_file()
        self.load_dataset()
        self.validate_required_columns()
        self.validate_target()

        logger.info("Initialization completed.")

    def generate_report(self) -> ValidationReport:

        return ValidationReport(
            dataset_name=self.schema.name,
            validation_time=datetime.now().isoformat(),
            validation_status="PASS",
            rows=int(self.df.shape[0]),
            columns=int(self.df.shape[1]),
            duplicate_rows=self.validate_duplicate_rows(),
            missing_values=self.validate_missing_values(),
            column_types={column: str(dtype) for column, dtype in self.df.dtypes.items()},
            target_distribution=self.target_distribution(),
            memory_usage_kb=round(self.df.memory_usage(deep=True).sum() / 1024, 2),
        )

    def save_report(self, report: ValidationReport) -> Path:

        if not self.config.save_report:
            logger.info("Report saving disabled.")
            return Path()

        self.config.output_directory.mkdir(parents=True, exist_ok=True)

        report_path = self.config.output_directory / "validation_report.json"

        with open(report_path, "w", encoding="utf-8") as file:
            json.dump(asdict(report), file, indent=4)

        logger.info("Validation report saved: %s", report_path)

        return report_path

    def print_summary(self, report: ValidationReport) -> None:

        print("\nVALIDATION SUMMARY")
        print(f"Dataset      : {report.dataset_name}")
        print(f"Status       : {report.validation_status}")
        print(f"Rows         : {report.rows}")
        print(f"Columns      : {report.columns}")
        print(f"Duplicates   : {report.duplicate_rows}")
        print(f"Memory (KB)  : {report.memory_usage_kb}")

    def validate(self) -> ValidationReport:

        logger.info("=" * 70)
        logger.info("Starting dataset validation...")

        self.initialize()
        self.validate_numeric_ranges()
        self.validate_allowed_categories()

        report = self.generate_report()
        self.save_report(report)

        if self.config.verbose:
            self.print_summary(report)

        logger.info("Validation completed successfully.")

        return report


# ============================================================================== # Command Line Interface
# ==============================================================================


def build_argument_parser() -> argparse.ArgumentParser:
    """
    Create CLI parser.
    """

    parser = argparse.ArgumentParser(
        description="MediGenie Dataset Validator"
    )

    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to dataset CSV",
    )

    parser.add_argument(
        "--name",
        required=True,
        help="Dataset schema name "
             "(heart_disease, diabetes, kidney...)",
    )

    parser.add_argument(
        "--output",
        default="backend/datasets/validation",
        help="Output directory",
    )

    return parser


# ==============================================================================
# Main
# ==============================================================================


def main() -> None:

    args = build_argument_parser().parse_args()

    config = ValidationConfig(

        dataset_path=Path(args.dataset),

        dataset_name=args.name,

        output_directory=Path(args.output),

    )

    validator = DatasetValidator(config)

    validator.validate()


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":

    main()