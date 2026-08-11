"""
split.py

Production-grade dataset splitting module for MediGenie.

Responsibilities
----------------
✓ Load processed dataset
✓ Validate target column
✓ Stratified train/validation/test split
✓ Save split datasets
✓ Save metadata
✓ Generic for all disease datasets
"""

from __future__ import annotations

import argparse
import json
import logging

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from sklearn.model_selection import train_test_split

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


class DatasetSplitError(Exception):
    """Base split exception."""


class DatasetLoadError(DatasetSplitError):
    """Unable to load dataset."""


class TargetColumnError(DatasetSplitError):
    """Target column missing."""


# ==============================================================================
# Configuration
# ==============================================================================


@dataclass(slots=True)
class SplitConfig:

    dataset_path: Path

    output_directory: Path

    target_column: str

    train_size: float = 0.70

    validation_size: float = 0.15

    test_size: float = 0.15

    random_state: int = 42

    shuffle: bool = True


# ==============================================================================
# Split Metadata
# ==============================================================================


@dataclass(slots=True)
class SplitMetadata:

    dataset: str

    created_at: str

    total_samples: int

    train_samples: int

    validation_samples: int

    test_samples: int

    target_column: str

    random_state: int
    # ==============================================================================
# Dataset Splitter
# ==============================================================================


class DatasetSplitter:
    """
    Production-grade dataset splitter.
    """

    def __init__(
        self,
        config: SplitConfig,
    ) -> None:

        self.config = config

        self.df: pd.DataFrame | None = None

        self.train_df: pd.DataFrame | None = None

        self.validation_df: pd.DataFrame | None = None

        self.test_df: pd.DataFrame | None = None

    # ==========================================================================
    # DataFrame Property
    # ==========================================================================

    @property
    def dataframe(self) -> pd.DataFrame:

        if self.df is None:
            raise DatasetLoadError(
                "Dataset has not been loaded."
            )

        return self.df

    # ==========================================================================
    # Load Dataset
    # ==========================================================================

    def load_dataset(self) -> None:

        logger.info("Loading dataset...")

        if not self.config.dataset_path.exists():

            raise DatasetLoadError(
                f"Dataset not found:\n"
                f"{self.config.dataset_path}"
            )

        try:

            self.df = pd.read_csv(
                self.config.dataset_path
            )

        except Exception as exc:

            raise DatasetLoadError(
                f"Unable to load dataset.\n{exc}"
            ) from exc

        logger.info(

            "Dataset loaded successfully "

            "(%d rows × %d columns).",

            self.df.shape[0],

            self.df.shape[1],

        )

    # ==========================================================================
    # Validate Target
    # ==========================================================================

    def validate_target(self) -> None:

        logger.info(
            "Validating target column..."
        )

        if self.config.target_column not in self.df.columns:

            raise TargetColumnError(

                f"Target column "

                f"'{self.config.target_column}' "

                f"not found."

            )

        logger.info(
            "Target validation successful."
        )

    # ==========================================================================
    # Validate Split Ratios
    # ==========================================================================

    def validate_split_ratios(self) -> None:

        total = (

            self.config.train_size +

            self.config.validation_size +

            self.config.test_size

        )

        if abs(total - 1.0) > 0.0001:

            raise DatasetSplitError(

                "Train + Validation + Test "

                "must equal 1.0"

            )

        logger.info(
            "Split ratios validated."
        )

    # ==========================================================================
    # Class Distribution
    # ==========================================================================

    def class_distribution(self) -> dict[Any, int]:

        target = self.config.target_column

        distribution = (

            self.df[target]

            .value_counts()

            .sort_index()

            .to_dict()

        )

        logger.info(
            "Class distribution:"
        )

        for cls, count in distribution.items():

            logger.info(
                "  %s : %d",
                cls,
                count,
            )

        return distribution

    # ==========================================================================
    # Initialization
    # ==========================================================================

    def initialize(self) -> None:

        self.load_dataset()

        self.validate_target()

        self.validate_split_ratios()

        self.class_distribution()

        logger.info(
            "Initialization completed."
        )
            # ==========================================================================
    # Split Dataset
    # ==========================================================================

    def split_dataset(self) -> None:
        """
        Split dataset into train, validation and test sets
        using stratified sampling.
        """

        logger.info("Splitting dataset...")

        df = self.dataframe

        target = self.config.target_column

        X = df.drop(columns=[target])

        y = df[target]

        # ---------------------------------------------------------
        # First split:
        # Train (70%)
        # Temp (30%)
        # ---------------------------------------------------------

        X_train, X_temp, y_train, y_temp = train_test_split(
            X,
            y,
            train_size=self.config.train_size,
            shuffle=self.config.shuffle,
            random_state=self.config.random_state,
            stratify=y,
        )

        # ---------------------------------------------------------
        # Second split:
        # Validation (15%)
        # Test (15%)
        # ---------------------------------------------------------

        validation_ratio = (
            self.config.validation_size
            / (
                self.config.validation_size
                + self.config.test_size
            )
        )

        X_validation, X_test, y_validation, y_test = train_test_split(
            X_temp,
            y_temp,
            train_size=validation_ratio,
            shuffle=self.config.shuffle,
            random_state=self.config.random_state,
            stratify=y_temp,
        )

        # ---------------------------------------------------------
        # Combine Features + Target
        # ---------------------------------------------------------

        self.train_df = pd.concat(
            [
                X_train.reset_index(drop=True),
                y_train.reset_index(drop=True),
            ],
            axis=1,
        )

        self.validation_df = pd.concat(
            [
                X_validation.reset_index(drop=True),
                y_validation.reset_index(drop=True),
            ],
            axis=1,
        )

        self.test_df = pd.concat(
            [
                X_test.reset_index(drop=True),
                y_test.reset_index(drop=True),
            ],
            axis=1,
        )

        logger.info("Dataset splitting completed.")

    # ==========================================================================
    # Verify Split
    # ==========================================================================

    def verify_split(self) -> None:
        """
        Verify split integrity.
        """

        logger.info("Verifying split...")

        total = (
            len(self.train_df)
            + len(self.validation_df)
            + len(self.test_df)
        )

        if total != len(self.df):

            raise DatasetSplitError(
                "Split verification failed."
            )

        logger.info(
            "Train      : %d",
            len(self.train_df),
        )

        logger.info(
            "Validation : %d",
            len(self.validation_df),
        )

        logger.info(
            "Test       : %d",
            len(self.test_df),
        )

        logger.info("Split verification successful.")

    # ==========================================================================
    # Split Statistics
    # ==========================================================================

    def split_statistics(self) -> dict[str, Any]:
        """
        Return split statistics.
        """

        return {
            "train_samples": len(self.train_df),
            "validation_samples": len(self.validation_df),
            "test_samples": len(self.test_df),
            "total_samples": len(self.df),
        }
        # ==========================================================================
    # Create Output Directory
    # ==========================================================================

    def create_output_directory(self) -> None:
        """
        Create output directory if it doesn't exist.
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
    # Save Split Datasets
    # ==========================================================================

    def save_datasets(self) -> None:
        """
        Save train, validation and test datasets.
        """

        logger.info("Saving split datasets...")

        self.create_output_directory()

        train_path = (
            self.config.output_directory
            / "train.csv"
        )

        validation_path = (
            self.config.output_directory
            / "validation.csv"
        )

        test_path = (
            self.config.output_directory
            / "test.csv"
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
    # Save Metadata
    # ==========================================================================

    def save_metadata(self) -> None:
        """
        Save dataset split metadata.
        """

        logger.info(
            "Saving split metadata..."
        )

        metadata = SplitMetadata(

            dataset=self.config.dataset_path.stem,

            created_at=datetime.now().isoformat(),

            total_samples=len(self.df),

            train_samples=len(self.train_df),

            validation_samples=len(self.validation_df),

            test_samples=len(self.test_df),

            target_column=self.config.target_column,

            random_state=self.config.random_state,

        )

        metadata_path = (
            self.config.output_directory
            / "split_metadata.json"
        )

        with open(
            metadata_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                asdict(metadata),
                file,
                indent=4,
            )

        logger.info(
            "Saved: %s",
            metadata_path,
        )

    # ==========================================================================
    # Execute Complete Split Pipeline
    # ==========================================================================

    def run(self) -> None:
        """
        Execute complete dataset splitting pipeline.
        """

        logger.info("=" * 70)
        logger.info("Starting dataset split pipeline...")

        self.initialize()

        self.split_dataset()

        self.verify_split()

        self.save_datasets()

        self.save_metadata()

        logger.info("=" * 70)
        logger.info(
            "Dataset splitting completed successfully."
        )
        # ==============================================================================
# Command Line Interface
# ==============================================================================

def build_argument_parser() -> argparse.ArgumentParser:
    """
    Build CLI argument parser.
    """

    parser = argparse.ArgumentParser(
        description="MediGenie Dataset Splitter"
    )

    parser.add_argument(
        "--dataset",
        required=True,
        help="Path to processed dataset CSV",
    )

    parser.add_argument(
        "--target",
        required=True,
        help="Target column name",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output directory",
    )

    parser.add_argument(
        "--train-size",
        type=float,
        default=0.70,
        help="Training split ratio",
    )

    parser.add_argument(
        "--validation-size",
        type=float,
        default=0.15,
        help="Validation split ratio",
    )

    parser.add_argument(
        "--test-size",
        type=float,
        default=0.15,
        help="Test split ratio",
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed",
    )

    return parser


# ==============================================================================
# Main
# ==============================================================================

def main() -> None:

    args = build_argument_parser().parse_args()

    config = SplitConfig(
        dataset_path=Path(args.dataset),
        output_directory=Path(args.output),
        target_column=args.target,
        train_size=args.train_size,
        validation_size=args.validation_size,
        test_size=args.test_size,
        random_state=args.random_state,
    )

    splitter = DatasetSplitter(config)

    splitter.run()


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    main()