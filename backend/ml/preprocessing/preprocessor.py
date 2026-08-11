"""
preprocessor.py

Production-grade preprocessing pipeline.

Responsibilities
----------------
✓ Missing value imputation
✓ Feature encoding
✓ Feature scaling
✓ Feature ordering
✓ Save preprocessing pipeline
✓ Load preprocessing pipeline
✓ Transform new inference data
"""

from __future__ import annotations

import argparse
import json
import logging

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
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

class PreprocessingError(Exception):
    """Base preprocessing exception."""


class PipelineNotFittedError(PreprocessingError):
    """Pipeline has not been fitted."""


class DatasetError(PreprocessingError):
    """Dataset loading failed."""
    # ==============================================================================
# Configuration
# ==============================================================================

@dataclass(slots=True)
class PreprocessorConfig:

    dataset_path: Path

    target_column: str

    output_directory: Path

    numeric_features: list[str]

    categorical_features: list[str]
    # ==============================================================================
# Pipeline Artifacts
# ==============================================================================

@dataclass(slots=True)
class PipelineArtifacts:

    pipeline: Any

    feature_names: list[str]
    # ==============================================================================
# Preprocessor
# ==============================================================================


class Preprocessor:
    """
    Production-grade preprocessing pipeline.
    """

    def __init__(
        self,
        config: PreprocessorConfig,
    ) -> None:

        self.config = config

        self.dataset: pd.DataFrame | None = None

        self.X: pd.DataFrame | None = None

        self.y: pd.Series | None = None

        self.pipeline: ColumnTransformer | None = None

        self.feature_names: list[str] = []

    # ==========================================================================
    # Load Dataset
    # ==========================================================================

    def load_dataset(self) -> None:
        """
        Load dataset from disk.
        """

        logger.info(
            "Loading dataset..."
        )

        if not self.config.dataset_path.exists():

            raise DatasetError(
                f"Dataset not found:\n"
                f"{self.config.dataset_path}"
            )

        try:

            self.dataset = pd.read_csv(
                self.config.dataset_path
            )

        except Exception as exc:

            raise DatasetError(
                f"Unable to load dataset.\n{exc}"
            ) from exc

        if self.dataset.empty:

            raise DatasetError(
                "Dataset is empty."
            )

        logger.info(
            "Dataset loaded successfully "
            "(%d rows × %d columns).",
            len(self.dataset),
            len(self.dataset.columns),
        )

    # ==========================================================================
    # Validate Target Column
    # ==========================================================================

    def validate_target(self) -> None:
        """
        Validate target column.
        """

        if self.config.target_column not in self.dataset.columns:

            raise PreprocessingError(
                f"Target column "
                f"'{self.config.target_column}' "
                f"not found."
            )

        logger.info(
            "Target column validated."
        )

    # ==========================================================================
    # Validate Features
    # ==========================================================================

    def validate_features(self) -> None:
        """
        Ensure all configured features exist.
        """

        missing = []

        expected = (
            self.config.numeric_features
            + self.config.categorical_features
        )

        for column in expected:

            if column not in self.dataset.columns:

                missing.append(column)

        if missing:

            raise PreprocessingError(

                "Missing feature columns:\n"

                + "\n".join(missing)

            )

        logger.info(
            "Feature validation passed."
        )

    # ==========================================================================
    # Prepare Features
    # ==========================================================================

    def prepare_features(self) -> None:
        """
        Separate features and target.
        """

        self.X = self.dataset.drop(
            columns=[self.config.target_column]
        )

        self.y = self.dataset[
            self.config.target_column
        ]

        self.feature_names = list(
            self.X.columns
        )

        logger.info(
            "%d feature columns prepared.",
            len(self.feature_names),
        )

    # ==========================================================================
    # Detect Numeric Features
    # ==========================================================================

    def detect_numeric_features(
        self,
    ) -> list[str]:
        """
        Detect numeric columns.
        """

        numeric = self.X.select_dtypes(
            include=["number"]
        ).columns.tolist()

        logger.info(
            "Detected %d numeric features.",
            len(numeric),
        )

        return numeric

    # ==========================================================================
    # Detect Categorical Features
    # ==========================================================================

    def detect_categorical_features(
        self,
    ) -> list[str]:
        """
        Detect categorical columns.
        """

        categorical = self.X.select_dtypes(
            exclude=["number"]
        ).columns.tolist()

        logger.info(
            "Detected %d categorical features.",
            len(categorical),
        )

        return categorical

    # ==========================================================================
    # Initialize
    # ==========================================================================

    def initialize(self) -> None:
        """
        Initialize preprocessing.
        """

        self.load_dataset()

        self.validate_target()

        self.validate_features()

        self.prepare_features()

        logger.info(
            "Preprocessor initialized successfully."
        )
            # ==========================================================================
    # Build Pipeline
    # ==========================================================================

    def build_pipeline(self) -> None:
        """
        Build sklearn preprocessing pipeline.
        """

        logger.info(
            "Building preprocessing pipeline..."
        )

        numeric_features = (
            self.config.numeric_features
            if self.config.numeric_features
            else self.detect_numeric_features()
        )

        categorical_features = (
            self.config.categorical_features
            if self.config.categorical_features
            else self.detect_categorical_features()
        )

        numeric_pipeline = Pipeline(

            steps=[

                (
                    "imputer",

                    SimpleImputer(
                        strategy="median",
                    ),

                ),

                (
                    "scaler",

                    StandardScaler(),
                ),

            ]

        )

        categorical_pipeline = Pipeline(

            steps=[

                (
                    "imputer",

                    SimpleImputer(
                        strategy="most_frequent",
                    ),

                ),

                (
                    "encoder",

                    OneHotEncoder(
                        handle_unknown="ignore",
                        sparse_output=False,
                    ),

                ),

            ]

        )

        self.pipeline = ColumnTransformer(

            transformers=[

                (
                    "numeric",

                    numeric_pipeline,

                    numeric_features,

                ),

                (
                    "categorical",

                    categorical_pipeline,

                    categorical_features,

                ),

            ],

            remainder="drop",

        )

        logger.info(
            "Pipeline created successfully."
        )

    # ==========================================================================
    # Fit Pipeline
    # ==========================================================================

    def fit(self) -> None:
        """
        Fit preprocessing pipeline.
        """

        if self.pipeline is None:

            raise PipelineNotFittedError(
                "Pipeline has not been created."
            )

        logger.info(
            "Fitting preprocessing pipeline..."
        )

        self.pipeline.fit(
            self.X
        )

        logger.info(
            "Pipeline fitted successfully."
        )

    # ==========================================================================
    # Transform Dataset
    # ==========================================================================

    def transform(self) -> pd.DataFrame:
        """
        Transform dataset.
        """

        if self.pipeline is None:

            raise PipelineNotFittedError(
                "Pipeline has not been fitted."
            )

        logger.info(
            "Transforming dataset..."
        )

        transformed = self.pipeline.transform(
            self.X
        )

        try:

            feature_names = self.pipeline.get_feature_names_out()

        except Exception:

            feature_names = [

                f"feature_{i}"

                for i in range(
                    transformed.shape[1]
                )

            ]

        transformed_df = pd.DataFrame(

            transformed,

            columns=feature_names,

            index=self.X.index,

        )

        logger.info(

            "Transformation complete "

            "(%d rows × %d columns).",

            len(transformed_df),

            len(transformed_df.columns),

        )

        return transformed_df

    # ==========================================================================
    # Fit & Transform
    # ==========================================================================

    def fit_transform(self) -> tuple[pd.DataFrame, pd.Series]:
        """
        Fit pipeline and transform dataset.
        """

        self.build_pipeline()

        self.fit()

        transformed = self.transform()

        return transformed, self.y

    # ==========================================================================
    # Save Pipeline
    # ==========================================================================

    def save_pipeline(self) -> None:
        """
        Save fitted preprocessing pipeline.
        """

        if self.pipeline is None:

            raise PipelineNotFittedError(
                "Nothing to save."
            )

        self.config.output_directory.mkdir(

            parents=True,

            exist_ok=True,

        )

        pipeline_path = (

            self.config.output_directory
            / "preprocessor.joblib"

        )

        feature_path = (

            self.config.output_directory
            / "feature_names.json"

        )

        logger.info(
            "Saving preprocessing pipeline..."
        )

        joblib.dump(
            self.pipeline,
            pipeline_path,
        )

        try:

            names = list(
                self.pipeline.get_feature_names_out()
            )

        except Exception:

            names = self.feature_names

        with open(
            feature_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                names,
                file,
                indent=4,
            )

        logger.info(
            "Pipeline saved successfully."
        )

        logger.info(
            "Saved: %s",
            pipeline_path,
        )

        logger.info(
            "Saved: %s",
            feature_path,
        )
            # ==========================================================================
    # Load Pipeline
    # ==========================================================================

    def load_pipeline(self) -> None:
        """
        Load a previously saved preprocessing pipeline.
        """

        pipeline_path = (
            self.config.output_directory /
            "preprocessor.joblib"
        )

        if not pipeline_path.exists():

            raise PipelineNotFittedError(
                f"Pipeline not found:\n{pipeline_path}"
            )

        logger.info(
            "Loading preprocessing pipeline..."
        )

        self.pipeline = joblib.load(
            pipeline_path
        )

        logger.info(
            "Pipeline loaded successfully."
        )

    # ==========================================================================
    # Transform New Data
    # ==========================================================================

    def transform_new_data(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Transform new inference data.
        """

        if self.pipeline is None:

            raise PipelineNotFittedError(
                "Pipeline has not been loaded."
            )

        transformed = self.pipeline.transform(
            dataframe
        )

        try:

            columns = (
                self.pipeline.get_feature_names_out()
            )

        except Exception:

            columns = [

                f"feature_{i}"

                for i in range(
                    transformed.shape[1]
                )

            ]

        return pd.DataFrame(

            transformed,

            columns=columns,

            index=dataframe.index,

        )

    # ==========================================================================
    # Save Processed Dataset
    # ==========================================================================

    def save_processed_dataset(
        self,
        X: pd.DataFrame,
        y: pd.Series,
    ) -> None:
        """
        Save transformed dataset.
        """

        output = self.config.output_directory

        output.mkdir(
            parents=True,
            exist_ok=True,
        )

        dataset = X.copy()

        dataset[self.config.target_column] = y.values

        path = (
            output /
            "processed_dataset.csv"
        )

        dataset.to_csv(
            path,
            index=False,
        )

        logger.info(
            "Processed dataset saved."
        )

        logger.info(
            "Saved: %s",
            path,
        )

    # ==========================================================================
    # Execute Pipeline
    # ==========================================================================

    def run(self) -> None:
        """
        Execute preprocessing pipeline.
        """

        logger.info("=" * 70)

        logger.info(
            "Starting preprocessing..."
        )

        self.initialize()

        X_processed, y = (
            self.fit_transform()
        )

        self.save_pipeline()

        self.save_processed_dataset(
            X_processed,
            y,
        )

        logger.info("=" * 70)

        logger.info(
            "Preprocessing completed successfully."
        )
        # ==============================================================================
# CLI
# ==============================================================================

def build_argument_parser():

    parser = argparse.ArgumentParser(
        description="MediGenie Preprocessor"
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
        "--numeric",
        nargs="*",
        default=[],
    )

    parser.add_argument(
        "--categorical",
        nargs="*",
        default=[],
    )

    return parser


# ==============================================================================
# Main
# ==============================================================================

def main():

    args = (
        build_argument_parser()
        .parse_args()
    )

    config = PreprocessorConfig(

        dataset_path=Path(
            args.dataset
        ),

        target_column=args.target,

        output_directory=Path(
            args.output
        ),

        numeric_features=args.numeric,

        categorical_features=args.categorical,

    )

    processor = Preprocessor(
        config
    )

    processor.run()


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":

    main()