"""
feature_engineering.py

Production-ready feature engineering pipeline for MediGenie.

Responsibilities
----------------
- Load cleaned dataset
- Load dataset schema
- Encode categorical features
- Generate engineered features
- Remove low-information features
- Compute correlations
- Export engineered dataset
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

from backend.ml.preprocessing.schema_loader import (
    DatasetSchema,
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


class FeatureEngineeringError(Exception):
    """Base exception."""


class DatasetLoadError(FeatureEngineeringError):
    """Raised when dataset cannot be loaded."""


class OutputSaveError(FeatureEngineeringError):
    """Raised when output cannot be saved."""


# ==============================================================================
# Configuration
# ==============================================================================


@dataclass(slots=True)
class FeatureEngineeringConfig:

    dataset_path: Path

    dataset_name: str

    output_directory: Path

    save_metadata: bool = True

    save_correlation: bool = True

    random_state: int = 42


# ==============================================================================
# Metadata
# ==============================================================================


@dataclass(slots=True)
class FeatureMetadata:

    original_feature_count: int = 0

    final_feature_count: int = 0

    removed_features: list[str] = field(
        default_factory=list
    )

    encoded_features: list[str] = field(
        default_factory=list
    )

    created_features: list[str] = field(
        default_factory=list
    )

    target_column: str = ""

    feature_names: list[str] = field(
        default_factory=list
    )


# ==============================================================================
# Feature Engineer
# ==============================================================================


class FeatureEngineer:

    """
    Generic feature engineering pipeline.
    """

    def __init__(
        self,
        config: FeatureEngineeringConfig,
    ):

        self.config = config

        self.schema: DatasetSchema = load_schema(
            config.dataset_name
        )

        self.df: pd.DataFrame | None = None

        self.metadata = FeatureMetadata()

        self.label_encoders: dict[
            str,
            LabelEncoder,
        ] = {}

        logger.info(
            "Initialized feature engineering for %s",
            self.schema.name,
        )
            # -------------------------------------------------------------------------
    # Dataset Loading
    # -------------------------------------------------------------------------

    def load_dataset(self) -> None:
        """
        Load the cleaned dataset.
        """

        logger.info("Loading cleaned dataset...")

        try:

            self.df = pd.read_csv(
                self.config.dataset_path
            )

        except Exception as exc:

            raise DatasetLoadError(
                f"Unable to load dataset.\n{exc}"
            ) from exc

        if self.df.empty:

            raise DatasetLoadError(
                "Dataset is empty."
            )

        logger.info(
            "Dataset loaded successfully (%d rows, %d columns).",
            len(self.df),
            len(self.df.columns),
        )

    # -------------------------------------------------------------------------
    # Validate Dataset
    # -------------------------------------------------------------------------

    def validate_dataset(self) -> None:
        """
        Validate dataset against schema.
        """

        if self.df is None:

            raise DatasetLoadError(
                "Dataset has not been loaded."
            )

        missing_columns = [

            column

            for column in self.schema.required_columns

            if column not in self.df.columns

        ]

        if missing_columns:

            raise DatasetLoadError(

                "Missing required columns: "

                + ", ".join(missing_columns)

            )

        if self.schema.target_column not in self.df.columns:

            raise DatasetLoadError(

                f"Target column "

                f"'{self.schema.target_column}' "

                f"not found."

            )

        logger.info(
            "Schema validation successful."
        )

    # -------------------------------------------------------------------------
    # Dataset Summary
    # -------------------------------------------------------------------------

    def summarize_dataset(self) -> None:
        """
        Store dataset metadata.
        """

        if self.df is None:

            raise DatasetLoadError(
                "Dataset not loaded."
            )

        self.metadata.original_feature_count = (

            len(self.df.columns) - 1

        )

        self.metadata.target_column = (

            self.schema.target_column

        )

        self.metadata.feature_names = [

            column

            for column in self.df.columns

            if column != self.schema.target_column

        ]

        logger.info(

            "Original Features : %d",

            self.metadata.original_feature_count,

        )

    # -------------------------------------------------------------------------
    # Prepare Output Directory
    # -------------------------------------------------------------------------

    def prepare_output_directory(self) -> None:
        """
        Create output directory if it does not exist.
        """

        self.config.output_directory.mkdir(

            parents=True,

            exist_ok=True,

        )

        logger.info(

            "Output directory: %s",

            self.config.output_directory,

        )

    # -------------------------------------------------------------------------
    # Initial Pipeline
    # -------------------------------------------------------------------------

    def initialize(self) -> None:
        """
        Initialize feature engineering.
        """

        self.load_dataset()

        self.validate_dataset()

        self.summarize_dataset()

        self.prepare_output_directory()

        logger.info(
            "Initialization complete."
        )
            # -------------------------------------------------------------------------
    # Detect Categorical Features
    # -------------------------------------------------------------------------

    def get_categorical_columns(self) -> list[str]:
        """
        Return categorical columns excluding target.
        """

        categorical = []

        for column in self.schema.categorical_columns:

            if (
                column in self.df.columns
                and column != self.schema.target_column
            ):
                categorical.append(column)

        return categorical

    # -------------------------------------------------------------------------
    # Detect Numeric Features
    # -------------------------------------------------------------------------

    def get_numeric_columns(self) -> list[str]:
        """
        Return numeric columns excluding target.
        """

        numeric = []

        for column in self.schema.numeric_columns:

            if (
                column in self.df.columns
                and column != self.schema.target_column
            ):
                numeric.append(column)

        return numeric

    # -------------------------------------------------------------------------
    # Label Encoding
    # -------------------------------------------------------------------------

    def label_encode_features(self) -> None:
        """
        Encode categorical features using LabelEncoder.

        Numeric categorical values (0/1, 1/2/3, etc.)
        are left unchanged.
        """

        categorical_columns = self.get_categorical_columns()

        if not categorical_columns:

            logger.info(
                "No categorical columns found."
            )

            return

        for column in categorical_columns:

            # Skip if already numeric
            if pd.api.types.is_numeric_dtype(
                self.df[column]
            ):

                logger.info(
                    "Skipping numeric categorical column: %s",
                    column,
                )

                continue

            encoder = LabelEncoder()

            self.df[column] = encoder.fit_transform(
                self.df[column].astype(str)
            )

            self.label_encoders[column] = encoder

            self.metadata.encoded_features.append(
                column
            )

            logger.info(
                "Encoded column: %s",
                column,
            )

    # -------------------------------------------------------------------------
    # Binary Feature Validation
    # -------------------------------------------------------------------------

    def validate_binary_features(self) -> None:
        """
        Ensure binary columns contain only 0/1.
        """

        for column in self.get_categorical_columns():

            if column == self.schema.target_column:
                continue

            values = set(
                self.df[column]
                .dropna()
                .unique()
                .tolist()
            )

            if values.issubset({0, 1}):

                logger.info(
                    "Binary feature validated: %s",
                    column,
                )

    # -------------------------------------------------------------------------
    # Encode Pipeline
    # -------------------------------------------------------------------------

    def encode_features(self) -> None:
        """
        Complete encoding pipeline.
        """

        logger.info(
            "Encoding categorical features..."
        )

        self.validate_binary_features()

        self.label_encode_features()

        logger.info(
            "Feature encoding completed."
        )
            # -------------------------------------------------------------------------
    # Create Age Groups
    # -------------------------------------------------------------------------

    def create_age_groups(self) -> None:
        """
        Create age group categories.
        """

        if "age" not in self.df.columns:
            return

        self.df["age_group"] = pd.cut(
            self.df["age"],
            bins=[0, 40, 50, 60, 70, 120],
            labels=[
                "Young",
                "Middle",
                "Senior",
                "Elderly",
                "Very_Elderly",
            ],
            include_lowest=True,
        )

        encoder = LabelEncoder()

        self.df["age_group"] = encoder.fit_transform(
            self.df["age_group"].astype(str)
        )

        self.label_encoders["age_group"] = encoder

        self.metadata.created_features.append(
            "age_group"
        )

        logger.info(
            "Created feature: age_group"
        )

    # -------------------------------------------------------------------------
    # Cholesterol Risk Category
    # -------------------------------------------------------------------------

    def create_cholesterol_category(self) -> None:
        """
        Categorize cholesterol levels.
        """

        if "chol" not in self.df.columns:
            return

        self.df["chol_category"] = pd.cut(
            self.df["chol"],
            bins=[
                0,
                200,
                239,
                float("inf"),
            ],
            labels=[
                "Normal",
                "Borderline",
                "High",
            ],
            include_lowest=True,
        )

        encoder = LabelEncoder()

        self.df["chol_category"] = encoder.fit_transform(
            self.df["chol_category"].astype(str)
        )

        self.label_encoders["chol_category"] = encoder

        self.metadata.created_features.append(
            "chol_category"
        )

        logger.info(
            "Created feature: chol_category"
        )

    # -------------------------------------------------------------------------
    # Blood Pressure Category
    # -------------------------------------------------------------------------

    def create_bp_category(self) -> None:
        """
        Categorize resting blood pressure.
        """

        if "trestbps" not in self.df.columns:
            return

        self.df["bp_category"] = pd.cut(
            self.df["trestbps"],
            bins=[
                0,
                120,
                129,
                139,
                float("inf"),
            ],
            labels=[
                "Normal",
                "Elevated",
                "Stage1",
                "Stage2",
            ],
            include_lowest=True,
        )

        encoder = LabelEncoder()

        self.df["bp_category"] = encoder.fit_transform(
            self.df["bp_category"].astype(str)
        )

        self.label_encoders["bp_category"] = encoder

        self.metadata.created_features.append(
            "bp_category"
        )

        logger.info(
            "Created feature: bp_category"
        )

    # -------------------------------------------------------------------------
    # Heart Disease Derived Features
    # -------------------------------------------------------------------------

    def create_heart_disease_features(self) -> None:
        """
        Heart Disease specific feature engineering.
        """

        self.create_age_groups()

        self.create_cholesterol_category()

        self.create_bp_category()

    # -------------------------------------------------------------------------
    # Generic Feature Creation
    # -------------------------------------------------------------------------

    def create_features(self) -> None:
        """
        Create dataset-specific engineered features.
        """

        logger.info(
            "Creating engineered features..."
        )

        dataset = (
            self.schema.name.lower()
            .replace("-", " ")
        )

        if "heart" in dataset:

            self.create_heart_disease_features()

        # Future disease datasets:
        #
        # elif "diabetes" in dataset:
        #     self.create_diabetes_features()
        #
        # elif "kidney" in dataset:
        #     self.create_ckd_features()
        #
        # elif "liver" in dataset:
        #     self.create_liver_features()

        logger.info(
            "Feature engineering completed."
        )
            # -------------------------------------------------------------------------
    # Remove Duplicate Columns
    # -------------------------------------------------------------------------

    def remove_duplicate_features(self) -> None:
        """
        Remove duplicate feature columns.
        """

        logger.info("Removing duplicate features...")

        duplicate_columns = []

        columns = self.df.columns.tolist()

        for i in range(len(columns)):

            for j in range(i + 1, len(columns)):

                col1 = columns[i]
                col2 = columns[j]

                if col1 == self.schema.target_column:
                    continue

                if col2 == self.schema.target_column:
                    continue

                if self.df[col1].equals(self.df[col2]):

                    duplicate_columns.append(col2)

        if duplicate_columns:

            self.df.drop(
                columns=duplicate_columns,
                inplace=True,
            )

            self.metadata.removed_features.extend(
                duplicate_columns
            )

        logger.info(
            "Removed %d duplicate features.",
            len(duplicate_columns),
        )

    # -------------------------------------------------------------------------
    # Remove Constant Features
    # -------------------------------------------------------------------------

    def remove_constant_features(self) -> None:
        """
        Remove features having only one unique value.
        """

        logger.info("Removing constant features...")

        remove_columns = []

        for column in self.df.columns:

            if column == self.schema.target_column:
                continue

            if self.df[column].nunique(dropna=False) <= 1:

                remove_columns.append(column)

        if remove_columns:

            self.df.drop(
                columns=remove_columns,
                inplace=True,
            )

            self.metadata.removed_features.extend(
                remove_columns
            )

        logger.info(
            "Removed %d constant features.",
            len(remove_columns),
        )

    # -------------------------------------------------------------------------
    # Remove Near-Zero Variance Features
    # -------------------------------------------------------------------------

    def remove_low_variance_features(
        self,
        threshold: float = 0.01,
    ) -> None:
        """
        Remove features with extremely low variance.
        """

        logger.info("Removing low variance features...")

        remove_columns = []

        numeric_columns = self.get_numeric_columns()

        for column in numeric_columns:

            if column == self.schema.target_column:
                continue

            if column not in self.df.columns:
                continue

            series = pd.to_numeric(
                self.df[column],
                errors="coerce",
            )

            variance = series.var()

            if pd.isna(variance):
                continue

            if variance < threshold:

                remove_columns.append(column)

        if remove_columns:

            self.df.drop(
                columns=remove_columns,
                inplace=True,
            )

            self.metadata.removed_features.extend(
                remove_columns
            )

        logger.info(
            "Removed %d low variance features.",
            len(remove_columns),
        )

    # -------------------------------------------------------------------------
    # Remove Highly Correlated Features
    # -------------------------------------------------------------------------

    def remove_correlated_features(
        self,
        threshold: float = 0.95,
    ) -> None:
        """
        Remove highly correlated numeric features.
        """

        logger.info("Removing correlated features...")

        numeric_df = self.df.select_dtypes(
            include=["number"]
        )

        if self.schema.target_column in numeric_df.columns:

            numeric_df = numeric_df.drop(
                columns=[self.schema.target_column]
            )

        if numeric_df.empty:
            return

        corr_matrix = numeric_df.corr().abs()

        upper = corr_matrix.where(
            np.triu(
                np.ones(corr_matrix.shape),
                k=1,
            ).astype(bool)
        )

        remove_columns = [

            column

            for column in upper.columns

            if any(upper[column] > threshold)

        ]

        if remove_columns:

            self.df.drop(
                columns=remove_columns,
                inplace=True,
            )

            self.metadata.removed_features.extend(
                remove_columns
            )

        logger.info(
            "Removed %d correlated features.",
            len(remove_columns),
        )

    # -------------------------------------------------------------------------
    # Feature Selection Pipeline
    # -------------------------------------------------------------------------

    def select_features(self) -> None:
        """
        Execute feature selection pipeline.
        """

        logger.info(
            "Running feature selection..."
        )

        self.remove_duplicate_features()

        self.remove_constant_features()

        self.remove_low_variance_features()

        self.remove_correlated_features()

        self.metadata.final_feature_count = (

            len(self.df.columns) - 1

        )

        logger.info(
            "Final feature count: %d",
            self.metadata.final_feature_count,
        )