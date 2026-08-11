"""
clean.py

Production-ready dataset cleaning pipeline for MediGenie.

This module cleans validated datasets before feature engineering
and machine learning training.

Features
--------
- Load validated datasets
- Normalize column names
- Remove duplicate rows
- Handle missing values
- Fix data types
- Detect invalid values
- Generate cleaning reports
- Save cleaned datasets
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.ml.preprocessing.schema_loader import load_schema

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


class CleaningError(Exception):
    """Base cleaning exception."""


class DatasetLoadError(CleaningError):
    """Raised when dataset cannot be loaded."""


# ==============================================================================
# Configuration
# ==============================================================================


@dataclass(slots=True)
class CleaningConfig:
    """
    Configuration for dataset cleaning.
    """

    dataset_path: Path

    output_directory: Path

    metadata_directory: Path

    dataset_name: str

    save_report: bool = True

    verbose: bool = True


# ==============================================================================
# Cleaning Report
# ==============================================================================


@dataclass(slots=True)
class CleaningReport:

    dataset_name: str

    cleaning_time: str

    original_rows: int

    cleaned_rows: int

    removed_duplicates: int

    missing_values_before: dict[str, int]

    missing_values_after: dict[str, int]

    invalid_rows_removed: int

    saved_dataset: str


# ==============================================================================
# Cleaner
# ==============================================================================


class DatasetCleaner:

    """
    Generic dataset cleaner.

    Works for every disease dataset.
    """

    def __init__(self, config: CleaningConfig):

        self.config = config

        self.df: pd.DataFrame | None = None

        self.original_rows = 0

        self.invalid_rows_removed = 0

    # -------------------------------------------------------------------------

    @property
    def dataframe(self) -> pd.DataFrame:

        if self.df is None:
            raise CleaningError(
                "Dataset not loaded."
            )

        return self.df

    # -------------------------------------------------------------------------

    def load_dataset(self):

        logger.info("Loading dataset...")

        try:

            schema = load_schema(
                self.config.dataset_name
            )

            self.df = pd.read_csv(
                self.config.dataset_path
                ,
                header=schema.header,
                names=schema.columns,
            )

        except Exception as exc:

            raise DatasetLoadError(
                str(exc)
            ) from exc

        self.original_rows = len(self.df)

        logger.info(
            "Dataset loaded successfully."
        )

    # -------------------------------------------------------------------------

    def normalize_column_names(self):

        logger.info(
            "Normalizing column names..."
        )

        df = self.dataframe

        df.columns = [

            column.strip()

            .lower()

            .replace(" ", "_")

            .replace("-", "_")

            for column in df.columns

        ]

    # -------------------------------------------------------------------------

    def remove_duplicate_rows(self):

        logger.info(
            "Removing duplicate rows..."
        )

        df = self.dataframe

        before = len(df)

        df.drop_duplicates(
            inplace=True
        )

        after = len(df)

        removed = before - after

        logger.info(
            "%d duplicate rows removed.",
            removed,
        )

        return removed

    # -------------------------------------------------------------------------

    def missing_values_before(self):

        return (
            self.dataframe
            .isna()
            .sum()
            .astype(int)
            .to_dict()
        )

    # -------------------------------------------------------------------------

    def missing_values_after(self):

        return (
            self.dataframe
            .isna()
            .sum()
            .astype(int)
            .to_dict()
        )
    # -------------------------------------------------------------------------
    # Handle Missing Values
    # -------------------------------------------------------------------------

    def handle_missing_values(self):
        """
        Fill missing values.

        Numerical columns -> Median
        Categorical columns -> Mode
        """

        logger.info("Handling missing values...")

        df = self.dataframe

        numerical_columns = df.select_dtypes(
            include=[np.number]
        ).columns

        categorical_columns = df.select_dtypes(
            exclude=[np.number]
        ).columns

        for column in numerical_columns:

            if df[column].isna().sum() > 0:

                median = df[column].median()

                df[column] = df[column].fillna(median)

        for column in categorical_columns:

            if df[column].isna().sum() > 0:

                mode = df[column].mode(dropna=True)

                if not mode.empty:

                    df[column] = df[column].fillna(mode.iloc[0])

        logger.info("Missing values processed.")

    # -------------------------------------------------------------------------
    # Strip Whitespace
    # -------------------------------------------------------------------------

    def strip_whitespace(self):
        """
        Remove leading and trailing whitespace.
        """

        logger.info("Removing extra whitespace...")

        df = self.dataframe

        object_columns = df.select_dtypes(
            include=["object"]
        ).columns

        for column in object_columns:

            df[column] = (
                df[column]
                .astype(str)
                .str.strip()
            )

    # -------------------------------------------------------------------------
    # Fix Data Types
    # -------------------------------------------------------------------------

    def fix_data_types(self):
        """
        Convert object columns to numeric when possible.
        """

        logger.info("Fixing data types...")

        df = self.dataframe

        for column in df.columns:

            if df[column].dtype == object:

                converted = pd.to_numeric(
                    df[column],
                    errors="ignore",
                )

                df[column] = converted

        logger.info("Data types updated.")

    # -------------------------------------------------------------------------
    # Remove Invalid Numerical Values
    # -------------------------------------------------------------------------

    def remove_invalid_values(self):
        """
        Remove impossible values.

        Generic checks only.
        """

        logger.info("Checking invalid values...")

        df = self.dataframe

        before = len(df)

        for column in df.select_dtypes(
            include=[np.number]
        ).columns:

            df.dropna(
                subset=[column],
                inplace=True,
            )

        if "age" in df.columns:

            df = df[
                (df["age"] >= 0)
                &
                (df["age"] <= 120)
            ]

        if "chol" in df.columns:

            df = df[
                df["chol"] >= 0
            ]

        if "trestbps" in df.columns:

            df = df[
                df["trestbps"] >= 0
            ]

        if "thalach" in df.columns:

            df = df[
                df["thalach"] >= 0
            ]

        if "oldpeak" in df.columns:

            df = df[
                df["oldpeak"] >= 0
            ]

        self.invalid_rows_removed = (
            before - len(df)
        )

        self.df = df.reset_index(drop=True)

        logger.info(
            "%d invalid rows removed.",
            self.invalid_rows_removed,
        )

    # -------------------------------------------------------------------------
    # Remove Constant Columns
    # -------------------------------------------------------------------------

    def remove_constant_columns(self):
        """
        Remove columns with only one unique value.
        """

        logger.info("Removing constant columns...")

        df = self.dataframe

        constant_columns = [

            column

            for column in df.columns

            if df[column].nunique(dropna=False) <= 1

        ]

        if constant_columns:

            df.drop(
                columns=constant_columns,
                inplace=True,
            )

            logger.info(
                "Removed %d constant columns.",
                len(constant_columns),
            )

    # -------------------------------------------------------------------------
    # Remove Empty Rows
    # -------------------------------------------------------------------------

    def remove_empty_rows(self):
        """
        Remove rows that are completely empty.
        """

        logger.info("Removing empty rows...")

        before = len(self.dataframe)

        self.df.dropna(
            how="all",
            inplace=True,
        )

        after = len(self.dataframe)

        logger.info(
            "%d empty rows removed.",
            before - after,
        )

    # -------------------------------------------------------------------------
    # Dataset Shape
    # -------------------------------------------------------------------------

    def dataset_shape(self):

        return self.dataframe.shape

    # -------------------------------------------------------------------------
    # Cleaning Summary
    # -------------------------------------------------------------------------

    def summary(self):

        rows, columns = self.dataset_shape()

        return {

            "rows": rows,

            "columns": columns,

            "memory_usage_kb": round(

                self.dataframe.memory_usage(
                    deep=True
                ).sum() / 1024,

                2,

            ),

            "missing_values": self.missing_values_after(),

        }

    # -------------------------------------------------------------------------
    # Save Cleaned Dataset
    # -------------------------------------------------------------------------

    def save_dataset(self) -> Path:
        """
        Save cleaned dataset.
        """

        self.config.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            self.config.output_directory
            / "cleaned.csv"
        )

        self.dataframe.to_csv(
            output_path,
            index=False,
        )

        logger.info(
            "Cleaned dataset saved -> %s",
            output_path,
        )

        return output_path

    # -------------------------------------------------------------------------
    # Save Cleaning Report
    # -------------------------------------------------------------------------

    def save_report(
        self,
        report: CleaningReport,
    ) -> Path:

        self.config.metadata_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        report_path = (
            self.config.metadata_directory
            / "cleaning_report.json"
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
            "Cleaning report saved -> %s",
            report_path,
        )

        return report_path

    # -------------------------------------------------------------------------
    # Console Report
    # -------------------------------------------------------------------------

    def print_report(
        self,
        report: CleaningReport,
    ) -> None:

        print()

        print("=" * 70)
        print("DATASET CLEANING REPORT")
        print("=" * 70)

        print(f"Dataset             : {report.dataset_name}")
        print(f"Cleaning Time       : {report.cleaning_time}")

        print()

        print(f"Original Rows       : {report.original_rows}")
        print(f"Cleaned Rows        : {report.cleaned_rows}")

        print()

        print(
            f"Duplicate Removed   : {report.removed_duplicates}"
        )

        print(
            f"Invalid Rows Removed: {report.invalid_rows_removed}"
        )

        print()

        print("Missing Values Before")

        for column, value in report.missing_values_before.items():

            print(f"{column:<30} {value}")

        print()

        print("Missing Values After")

        for column, value in report.missing_values_after.items():

            print(f"{column:<30} {value}")

        print()

        print(f"Saved Dataset       : {report.saved_dataset}")

        print("=" * 70)

    # -------------------------------------------------------------------------
    # Cleaning Pipeline
    # -------------------------------------------------------------------------

    def clean(self) -> CleaningReport:

        logger.info(
            "Starting cleaning pipeline..."
        )

        self.load_dataset()

        before_missing = self.missing_values_before()

        self.normalize_column_names()

        duplicate_rows = self.remove_duplicate_rows()

        self.strip_whitespace()

        self.fix_data_types()

        self.handle_missing_values()

        self.remove_invalid_values()

        self.remove_constant_columns()

        self.remove_empty_rows()

        output_path = self.save_dataset()

        report = CleaningReport(

            dataset_name=self.config.dataset_name,

            cleaning_time=datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            original_rows=self.original_rows,

            cleaned_rows=len(self.dataframe),

            removed_duplicates=duplicate_rows,

            missing_values_before=before_missing,

            missing_values_after=self.missing_values_after(),

            invalid_rows_removed=self.invalid_rows_removed,

            saved_dataset=str(output_path),

        )

        if self.config.save_report:

            self.save_report(report)

        if self.config.verbose:

            self.print_report(report)

        logger.info(
            "Cleaning completed successfully."
        )

        return report

# ==============================================================================
# Command Line Interface
# ==============================================================================

import argparse


def parse_arguments():

    parser = argparse.ArgumentParser(
        description="Dataset Cleaner"
    )

    parser.add_argument(
        "--dataset",
        required=True,
        help="Input CSV dataset",
    )

    parser.add_argument(
        "--name",
        required=True,
        help="Dataset name",
    )

    parser.add_argument(
        "--output",
        default="backend/datasets/processed/heart_disease",
        help="Processed dataset directory",
    )

    parser.add_argument(
        "--metadata",
        default="backend/datasets/metadata",
        help="Metadata directory",
    )

    return parser.parse_args()


def main():

    args = parse_arguments()

    config = CleaningConfig(

        dataset_path=Path(args.dataset),

        output_directory=Path(args.output),

        metadata_directory=Path(args.metadata),

        dataset_name=args.name,

    )

    cleaner = DatasetCleaner(config)

    cleaner.clean()


if __name__ == "__main__":
    main()