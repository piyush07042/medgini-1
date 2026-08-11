"""
split.py

Production-grade dataset splitting module.

Responsibilities
----------------
✓ Load processed dataset
✓ Validate target column
✓ Stratified train/validation/test split
✓ Save split datasets
✓ Generate split metadata
"""

from __future__ import annotations

import argparse
import json
import logging

from dataclasses import dataclass
from pathlib import Path

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


class SplitError(Exception):
    """Base split exception."""


class DatasetLoadError(SplitError):
    """Dataset loading failed."""


class TargetColumnError(SplitError):
    """Target column missing."""


# ==============================================================================
# Configuration
# ==============================================================================


@dataclass(slots=True)
class SplitConfig:

    dataset_path: Path

    output_directory: Path

    target_column: str

    test_size: float = 0.20

    validation_size: float = 0.20

    random_state: int = 42

    stratify: bool = True
    # ==============================================================================
# Dataset Splitter
# ==============================================================================


class DatasetSplitter:
    """
    Production dataset splitting pipeline.
    """

    def __init__(
        self,
        config: SplitConfig,
    ) -> None:

        self.config = config

        self.dataset: pd.DataFrame | None = None

        self.X: pd.DataFrame | None = None

        self.y: pd.Series | None = None

        self.X_train: pd.DataFrame | None = None
        self.X_validation: pd.DataFrame | None = None
        self.X_test: pd.DataFrame | None = None

        self.y_train: pd.Series | None = None
        self.y_validation: pd.Series | None = None
        self.y_test: pd.Series | None = None
            # ==========================================================================
    # Load Dataset
    # ==========================================================================

    def load_dataset(self) -> None:

        logger.info(
            "Loading processed dataset..."
        )

        if not self.config.dataset_path.exists():

            raise DatasetLoadError(
                f"Dataset not found:\n"
                f"{self.config.dataset_path}"
            )

        try:

            self.dataset = pd.read_csv(
                self.config.dataset_path
            )

        except Exception as exc:

            raise DatasetLoadError(
                str(exc)
            ) from exc

        if self.dataset.empty:

            raise DatasetLoadError(
                "Dataset is empty."
            )

        logger.info(
            "Dataset loaded (%d rows × %d columns).",
            len(self.dataset),
            len(self.dataset.columns),
        )
            # ==========================================================================
    # Validate Target
    # ==========================================================================

    def validate_target(self) -> None:

        if self.config.target_column not in self.dataset.columns:

            raise TargetColumnError(
                f"'{self.config.target_column}' not found."
            )

        logger.info(
            "Target column validated."
        )

    # ==========================================================================
    # Prepare Features
    # ==========================================================================

    def prepare_features(self) -> None:

        self.X = self.dataset.drop(
            columns=[self.config.target_column]
        )

        self.y = self.dataset[
            self.config.target_column
        ]

        logger.info(
            "%d feature columns prepared.",
            len(self.X.columns),
        )

    # ==========================================================================
    # Initialize
    # ==========================================================================

    def initialize(self) -> None:

        self.load_dataset()

        self.validate_target()

        self.prepare_features()

        logger.info(
            "Initialization completed."
        )
            # ==========================================================================
    # Split Dataset
    # ==========================================================================

    def split_dataset(self) -> None:
        """
        Perform stratified train/validation/test split.
        """

        logger.info(
            "Splitting dataset..."
        )

        stratify_target = (
            self.y
            if self.config.stratify
            else None
        )

        (
            X_train,
            X_test,
            y_train,
            y_test,
        ) = train_test_split(

            self.X,

            self.y,

            test_size=self.config.test_size,

            random_state=self.config.random_state,

            shuffle=True,

            stratify=stratify_target,

        )

        validation_ratio = (
            self.config.validation_size /
            (1.0 - self.config.test_size)
        )

        stratify_target = (
            y_train
            if self.config.stratify
            else None
        )

        (
            self.X_train,
            self.X_validation,
            self.y_train,
            self.y_validation,
        ) = train_test_split(

            X_train,

            y_train,

            test_size=validation_ratio,

            random_state=self.config.random_state,

            shuffle=True,

            stratify=stratify_target,

        )

        self.X_test = X_test
        self.y_test = y_test

        logger.info(
            "Train      : %d samples",
            len(self.X_train),
        )

        logger.info(
            "Validation : %d samples",
            len(self.X_validation),
        )

        logger.info(
            "Test        : %d samples",
            len(self.X_test),
        )

    # ========================================================================== 
    # Save Dataset
    # ==========================================================================

    def save_dataset(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        filename: str,
    ) -> None:
        """
        Save dataset split.
        """

        dataframe = X.copy()

        dataframe[self.config.target_column] = y.values

        path = (
            self.config.output_directory /
            filename
        )

        dataframe.to_csv(
            path,
            index=False,
        )

        logger.info(
            "Saved: %s",
            path,
        )

    # ==========================================================================
    # Save All Splits
    # ==========================================================================

    def save_splits(self) -> None:

        logger.info(
            "Saving dataset splits..."
        )

        self.config.output_directory.mkdir(

            parents=True,

            exist_ok=True,

        )

        self.save_dataset(

            self.X_train,

            self.y_train,

            "train.csv",

        )

        self.save_dataset(

            self.X_validation,

            self.y_validation,

            "validation.csv",

        )

        self.save_dataset(

            self.X_test,

            self.y_test,

            "test.csv",

        )
            # ==========================================================================
    # Save Metadata
    # ==========================================================================

    def save_metadata(self) -> None:
        """
        Save split metadata.
        """

        metadata = {

            "train_samples": len(self.X_train),

            "validation_samples": len(
                self.X_validation
            ),

            "test_samples": len(
                self.X_test
            ),

            "total_samples": len(
                self.dataset
            ),

            "target_column": self.config.target_column,

            "random_state": self.config.random_state,

            "test_size": self.config.test_size,

            "validation_size": self.config.validation_size,

            "stratified": self.config.stratify,

        }

        path = (
            self.config.output_directory /
            "split_metadata.json"
        )

        with open(

            path,

            "w",

            encoding="utf-8",

        ) as file:

            json.dump(
                metadata,
                file,
                indent=4,
            )

        logger.info(
            "Saved: %s",
            path,
        )
            # ==========================================================================
    # Execute Pipeline
    # ==========================================================================

    def run(self) -> None:

        logger.info("=" * 70)

        logger.info(
            "Starting dataset split..."
        )

        self.initialize()

        self.split_dataset()

        self.save_splits()

        self.save_metadata()

        logger.info("=" * 70)

        logger.info(
            "Dataset splitting completed successfully."
        )
        # ==============================================================================
# CLI
# ==============================================================================

def build_argument_parser():

    parser = argparse.ArgumentParser(
        description="MediGenie Dataset Splitter"
    )

    parser.add_argument(
        "--dataset",
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
        "--test-size",
        type=float,
        default=0.20,
    )

    parser.add_argument(
        "--validation-size",
        type=float,
        default=0.20,
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--no-stratify",
        action="store_true",
    )

    return parser


def main():

    args = build_argument_parser().parse_args()

    config = SplitConfig(

        dataset_path=Path(args.dataset),

        output_directory=Path(args.output),

        target_column=args.target,

        test_size=args.test_size,

        validation_size=args.validation_size,

        random_state=args.random_state,

        stratify=not args.no_stratify,

    )

    splitter = DatasetSplitter(
        config
    )

    splitter.run()


if __name__ == "__main__":

    main()
    