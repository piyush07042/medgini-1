"""
scaler.py

Production-grade feature scaling module for MediGenie.

Responsibilities
----------------
✓ Load train/validation/test datasets
✓ Fit scaler only on training data
✓ Transform validation and test data
✓ Preserve target column
✓ Save scaled datasets
✓ Save fitted scaler
✓ Generic for all disease datasets
"""

from __future__ import annotations

import argparse
import logging

from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd

from sklearn.preprocessing import (
    StandardScaler,
    MinMaxScaler,
    RobustScaler,
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


class ScalingError(Exception):
    """Base scaling exception."""


class DatasetNotFoundError(ScalingError):
    """Dataset file not found."""


class InvalidScalerError(ScalingError):
    """Unsupported scaler."""


# ==============================================================================
# Configuration
# ==============================================================================


@dataclass(slots=True)
class ScalerConfig:

    train_path: Path

    validation_path: Path

    test_path: Path

    output_directory: Path

    target_column: str

    scaler_type: str = "standard"

    save_scaler: bool = True
    # ==============================================================================
# Feature Scaler
# ==============================================================================


class FeatureScaler:
    """
    Production-grade feature scaler.
    """

    def __init__(
        self,
        config: ScalerConfig,
    ) -> None:

        self.config = config

        self.train_df: pd.DataFrame | None = None

        self.validation_df: pd.DataFrame | None = None

        self.test_df: pd.DataFrame | None = None

        self.scaler = None

        self.feature_columns: list[str] = []

    # ==========================================================================
    # Dataset Loading
    # ==========================================================================

    def load_datasets(self) -> None:
        """
        Load train, validation and test datasets.
        """

        logger.info("Loading datasets...")

        paths = [
            self.config.train_path,
            self.config.validation_path,
            self.config.test_path,
        ]

        for path in paths:

            if not path.exists():

                raise DatasetNotFoundError(
                    f"Dataset not found:\n{path}"
                )

        self.train_df = pd.read_csv(
            self.config.train_path
        )

        self.validation_df = pd.read_csv(
            self.config.validation_path
        )

        self.test_df = pd.read_csv(
            self.config.test_path
        )

        logger.info("Datasets loaded successfully.")

        logger.info(
            "Train      : %d rows",
            len(self.train_df),
        )

        logger.info(
            "Validation : %d rows",
            len(self.validation_df),
        )

        logger.info(
            "Test       : %d rows",
            len(self.test_df),
        )

    # ==========================================================================
    # Validate Target Column
    # ==========================================================================

    def validate_target(self) -> None:
        """
        Ensure target column exists in all datasets.
        """

        logger.info(
            "Validating target column..."
        )

        target = self.config.target_column

        datasets = {

            "train": self.train_df,

            "validation": self.validation_df,

            "test": self.test_df,

        }

        for name, dataframe in datasets.items():

            if target not in dataframe.columns:

                raise ScalingError(

                    f"Target column '{target}' "

                    f"missing from "

                    f"{name} dataset."

                )

        logger.info(
            "Target validation successful."
        )

    # ==========================================================================
    # Feature Columns
    # ==========================================================================

    def detect_feature_columns(self) -> None:
        """
        Detect feature columns.
        """

        target = self.config.target_column

        self.feature_columns = [

            column

            for column

            in self.train_df.columns

            if column != target

        ]

        logger.info(

            "Detected %d feature columns.",

            len(self.feature_columns),

        )

    # ==========================================================================
    # Select Scaler
    # ==========================================================================

    def create_scaler(self) -> None:
        """
        Create scaler instance.
        """

        scaler_name = (

            self.config.scaler_type

            .lower()

            .strip()

        )

        if scaler_name == "standard":

            self.scaler = StandardScaler()

        elif scaler_name == "minmax":

            self.scaler = MinMaxScaler()

        elif scaler_name == "robust":

            self.scaler = RobustScaler()

        else:

            raise InvalidScalerError(

                f"Unsupported scaler: "

                f"{self.config.scaler_type}"

            )

        logger.info(
            "Scaler selected: %s",
            scaler_name,
        )

    # ==========================================================================
    # Initialization
    # ==========================================================================

    def initialize(self) -> None:
        """
        Initialize scaling pipeline.
        """

        self.load_datasets()

        self.validate_target()

        self.detect_feature_columns()

        self.create_scaler()

        logger.info(
            "Initialization completed."
        )
            # ==========================================================================
    # Fit Scaler
    # ==========================================================================

    def fit_scaler(self) -> None:
        """
        Fit scaler using only the training dataset.
        """

        logger.info(
            "Fitting scaler on training dataset..."
        )

        X_train = self.train_df[
            self.feature_columns
        ]

        self.scaler.fit(X_train)

        logger.info(
            "Scaler fitted successfully."
        )

    # ==========================================================================
    # Transform Datasets
    # ==========================================================================

    def transform_datasets(self) -> None:
        """
        Transform train, validation and test datasets.
        """

        logger.info(
            "Transforming datasets..."
        )

        target = self.config.target_column

        # ---------------------------------------------------------
        # Training
        # ---------------------------------------------------------

        train_scaled = self.scaler.transform(
            self.train_df[self.feature_columns]
        )

        self.train_df = pd.DataFrame(
            train_scaled,
            columns=self.feature_columns,
            index=self.train_df.index,
        )

        self.train_df[target] = (
            self.train_df_original[target].values
        )

        # ---------------------------------------------------------
        # Validation
        # ---------------------------------------------------------

        validation_scaled = self.scaler.transform(
            self.validation_df[self.feature_columns]
        )

        self.validation_df = pd.DataFrame(
            validation_scaled,
            columns=self.feature_columns,
            index=self.validation_df.index,
        )

        self.validation_df[target] = (
            self.validation_df_original[target].values
        )

        # ---------------------------------------------------------
        # Test
        # ---------------------------------------------------------

        test_scaled = self.scaler.transform(
            self.test_df[self.feature_columns]
        )

        self.test_df = pd.DataFrame(
            test_scaled,
            columns=self.feature_columns,
            index=self.test_df.index,
        )

        self.test_df[target] = (
            self.test_df_original[target].values
        )

        logger.info(
            "All datasets transformed successfully."
        )

    # ==========================================================================
    # Preserve Original Target
    # ==========================================================================

    def preserve_original_data(self) -> None:
        """
        Preserve original datasets before scaling.
        """

        self.train_df_original = self.train_df.copy()

        self.validation_df_original = (
            self.validation_df.copy()
        )

        self.test_df_original = (
            self.test_df.copy()
        )

    # ==========================================================================
    # Execute Scaling
    # ==========================================================================

    def scale(self) -> None:
        """
        Execute scaling pipeline.
        """

        self.preserve_original_data()

        self.fit_scaler()

        self.transform_datasets()

        logger.info(
            "Scaling pipeline completed."
        )
            # ==========================================================================
    # Create Output Directory
    # ==========================================================================

    def create_output_directory(self) -> None:
        """
        Create output directory.
        """

        self.config.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        logger.info(
            "Output directory ready: %s",
            self.config.output_directory,
        )

    # ==========================================================================
    # Save Scaled Datasets
    # ==========================================================================

    def save_scaled_datasets(self) -> None:
        """
        Save scaled datasets.
        """

        logger.info(
            "Saving scaled datasets..."
        )

        self.create_output_directory()

        train_path = (
            self.config.output_directory /
            "train_scaled.csv"
        )

        validation_path = (
            self.config.output_directory /
            "validation_scaled.csv"
        )

        test_path = (
            self.config.output_directory /
            "test_scaled.csv"
        )

        self.train_df.to_csv(
            train_path,
            index=False,
        )

        self.validation_df.to_csv(
            validation_path,
            index=False,
        )

        self.test_df.to_csv(
            test_path,
            index=False,
        )

        logger.info("Saved: %s", train_path)
        logger.info("Saved: %s", validation_path)
        logger.info("Saved: %s", test_path)

    # ==========================================================================
    # Save Scaler
    # ==========================================================================

    def save_scaler(self) -> None:
        """
        Save fitted scaler.
        """

        if not self.config.save_scaler:

            logger.info(
                "Scaler saving disabled."
            )

            return

        scaler_path = (
            self.config.output_directory /
            "scaler.joblib"
        )

        joblib.dump(
            self.scaler,
            scaler_path,
        )

        logger.info(
            "Scaler saved: %s",
            scaler_path,
        )

    # ==========================================================================
    # Execute Complete Pipeline
    # ==========================================================================

    def run(self) -> None:
        """
        Execute complete scaling pipeline.
        """

        logger.info("=" * 70)
        logger.info(
            "Starting feature scaling..."
        )

        self.initialize()

        self.scale()

        self.save_scaled_datasets()

        self.save_scaler()

        logger.info("=" * 70)
        logger.info(
            "Feature scaling completed successfully."
        )
        # ==============================================================================
# CLI
# ==============================================================================

def build_argument_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description="MediGenie Feature Scaler"
    )

    parser.add_argument(
        "--train",
        required=True,
    )

    parser.add_argument(
        "--validation",
        required=True,
    )

    parser.add_argument(
        "--test",
        required=True,
    )

    parser.add_argument(
        "--target",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    parser.add_argument(
        "--scaler",
        default="standard",
        choices=[
            "standard",
            "minmax",
            "robust",
        ],
    )

    return parser


# ==============================================================================
# Main
# ==============================================================================

def main():

    args = build_argument_parser().parse_args()

    config = ScalerConfig(

        train_path=Path(args.train),

        validation_path=Path(args.validation),

        test_path=Path(args.test),

        output_directory=Path(args.output),

        target_column=args.target,

        scaler_type=args.scaler,

    )

    FeatureScaler(config).run()


# ==============================================================================
# Entry
# ==============================================================================

if __name__ == "__main__":

    main()