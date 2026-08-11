"""
trainer.py

Production-grade model training pipeline for MediGenie.

Responsibilities
----------------
✓ Load scaled datasets
✓ Train multiple ML models
✓ Support XGBoost
✓ Support Random Forest
✓ Support LightGBM
✓ Support CatBoost
✓ Track training time
✓ Store trained models
✓ Generic for every disease
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import time

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
)
from sklearn.utils.class_weight import compute_class_weight


def _load_optional_classifier(module_name: str, class_name: str) -> Any | None:

    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None

    return getattr(module, class_name)


XGBClassifier = _load_optional_classifier("xgboost", "XGBClassifier")
LGBMClassifier = _load_optional_classifier("lightgbm", "LGBMClassifier")
CatBoostClassifier = _load_optional_classifier("catboost", "CatBoostClassifier")


def _compute_class_weights(y: pd.Series) -> dict[int, float]:
    """Compute class weights for imbalanced classification."""
    y_non_missing = y.dropna().astype(int)
    if y_non_missing.empty:
        return {}
    classes = np.asarray(np.sort(np.unique(y_non_missing.to_numpy())), dtype=int)
    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=y_non_missing.to_numpy(),
    )
    return dict(zip(classes.tolist(), weights))


def _binary_scale_pos_weight(y: pd.Series) -> float:
    """Compute XGBoost scale_pos_weight for binary classification."""
    counts = y.value_counts()
    if len(counts) != 2:
        return 1.0
    negative = counts.iloc[0]
    positive = counts.iloc[1]
    if positive == 0:
        return 1.0
    return float(negative / positive)

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


class TrainingError(Exception):
    """Base training exception."""


class DatasetLoadError(TrainingError):
    """Unable to load dataset."""


class ModelTrainingError(TrainingError):
    """Training failed."""


# ==============================================================================
# Configuration
# ==============================================================================


@dataclass(slots=True)
class TrainerConfig:

    train_path: Path

    validation_path: Path

    target_column: str

    output_directory: Path

    random_state: int = 42

    n_jobs: int = -1


# ==============================================================================
# Training Result
# ==============================================================================


@dataclass(slots=True)
class TrainingResult:

    model_name: str

    model: Any

    training_time: float

    train_samples: int

    validation_samples: int

    accuracy: float = 0.0

    precision: float = 0.0

    recall: float = 0.0

    f1_score: float = 0.0
    # ==============================================================================
# Model Trainer
# ==============================================================================


class ModelTrainer:
    """
    Production-grade multi-model trainer.
    """

    def __init__(
        self,
        config: TrainerConfig,
    ) -> None:

        self.config = config

        self.train_df: pd.DataFrame | None = None

        self.validation_df: pd.DataFrame | None = None

        self.feature_columns: list[str] = []

        self.X_train: pd.DataFrame | None = None

        self.y_train: pd.Series | None = None

        self.X_validation: pd.DataFrame | None = None

        self.y_validation: pd.Series | None = None

        self.models: dict[str, Any] = {}

        self.results: dict[str, TrainingResult] = {}

    # ==========================================================================
    # Dataset Loading
    # ==========================================================================

    def load_datasets(self) -> None:
        """
        Load scaled datasets.
        """

        logger.info("Loading datasets...")

        if not self.config.train_path.exists():

            raise DatasetLoadError(
                f"Train dataset not found:\n"
                f"{self.config.train_path}"
            )

        if not self.config.validation_path.exists():

            raise DatasetLoadError(
                f"Validation dataset not found:\n"
                f"{self.config.validation_path}"
            )

        self.train_df = pd.read_csv(
            self.config.train_path
        )

        self.validation_df = pd.read_csv(
            self.config.validation_path
        )

        logger.info(
            "Datasets loaded successfully."
        )

        logger.info(
            "Training samples: %d",
            len(self.train_df),
        )

        logger.info(
            "Validation samples: %d",
            len(self.validation_df),
        )

    # ==========================================================================
    # Validate Target
    # ==========================================================================

    def validate_target(self) -> None:
        """
        Ensure target exists.
        """

        target = self.config.target_column

        for dataframe_name, dataframe in {

            "train": self.train_df,

            "validation": self.validation_df,

        }.items():

            if target not in dataframe.columns:

                raise TrainingError(

                    f"Target column '{target}' "

                    f"missing in "

                    f"{dataframe_name} dataset."

                )

        logger.info(
            "Target validation successful."
        )

    # ==========================================================================
    # Feature Detection
    # ==========================================================================

    def detect_features(self) -> None:
        """
        Detect feature columns automatically.
        """

        target = self.config.target_column

        self.feature_columns = [

            column

            for column

            in self.train_df.columns

            if column != target

        ]

        logger.info(

            "%d feature columns detected.",

            len(self.feature_columns),

        )

    # ==========================================================================
    # Feature / Target Split
    # ==========================================================================

    def prepare_data(self) -> None:
        """
        Separate features and target.
        """

        target = self.config.target_column

        self.X_train = self.train_df[
            self.feature_columns
        ]

        self.y_train = self.train_df[
            target
        ]

        self.X_validation = self.validation_df[
            self.feature_columns
        ]

        self.y_validation = self.validation_df[
            target
        ]

        logger.info(
            "Feature matrices prepared."
        )

    # ==========================================================================
    # Initialization
    # ==========================================================================

    def initialize(self) -> None:
        """
        Initialize training pipeline.
        """

        self.load_datasets()

        self.validate_target()

        self.detect_features()

        self.prepare_data()

        logger.info(
            "Initialization completed."
        )
            # ==========================================================================
    # Model Factory
    # ==========================================================================

    def build_models(self) -> None:
        """
        Build all machine learning models.
        """

        logger.info(
            "Building machine learning models..."
        )

        class_weights = (
            _compute_class_weights(self.y_train)
            if self.y_train is not None
            else {}
        )
        binary_target = (
            len(class_weights) == 2
            if class_weights is not None
            else False
        )

        self.models = {
            "random_forest": RandomForestClassifier(
                n_estimators=300,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=self.config.random_state,
                n_jobs=self.config.n_jobs,
                class_weight="balanced",
            ),
        }

        if XGBClassifier is not None:
            objective = "multi:softprob"
            eval_metric = "mlogloss"
            scale_pos_weight = 1.0

            if binary_target:
                objective = "binary:logistic"
                eval_metric = "logloss"
                scale_pos_weight = _binary_scale_pos_weight(
                    self.y_train
                )

            self.models["xgboost"] = XGBClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                objective=objective,
                eval_metric=eval_metric,
                random_state=self.config.random_state,
                n_jobs=self.config.n_jobs,
                verbosity=0,
                use_label_encoder=False,
                scale_pos_weight=scale_pos_weight,
            )

        if LGBMClassifier is not None:
            self.models["lightgbm"] = LGBMClassifier(
                n_estimators=300,
                learning_rate=0.05,
                max_depth=6,
                num_leaves=31,
                random_state=self.config.random_state,
                n_jobs=self.config.n_jobs,
                verbose=-1,
                class_weight="balanced",
            )

        if CatBoostClassifier is not None:
            class_weight_list = [
                class_weights[c]
                for c in sorted(class_weights)
            ] if class_weights else None

            self.models["catboost"] = CatBoostClassifier(
                iterations=300,
                learning_rate=0.05,
                depth=6,
                loss_function="MultiClass",
                random_seed=self.config.random_state,
                verbose=False,
                class_weights=class_weight_list,
            )

        logger.info(

            "%d models created.",

            len(self.models),

        )

        for name in self.models:

            logger.info(
                "  ✓ %s",
                name,
            )

    # ==========================================================================
    # Model Summary
    # ==========================================================================

    def print_model_summary(self) -> None:
        """
        Print available models.
        """

        logger.info("=" * 60)

        logger.info(
            "Models Ready For Training"
        )

        logger.info("=" * 60)

        for index, name in enumerate(

            self.models.keys(),

            start=1,

        ):

            logger.info(

                "%d. %s",

                index,

                name,

            )

        logger.info("=" * 60)

    # ==========================================================================
    # Initialize Models
    # ==========================================================================

    def initialize_models(self) -> None:
        """
        Build all configured models.
        """

        self.build_models()

        self.print_model_summary()
            # ==========================================================================
    # Train Single Model
    # ==========================================================================

    def train_model(
        self,
        model_name: str,
        model: Any,
    ) -> TrainingResult:
        """
        Train a single machine learning model.
        """

        logger.info("=" * 60)
        logger.info("Training %s...", model_name)

        start_time = time.perf_counter()

        try:

            model.fit(
                self.X_train,
                self.y_train,
            )

        except Exception as exc:

            raise ModelTrainingError(
                f"Training failed for '{model_name}'.\n{exc}"
            ) from exc

        elapsed = time.perf_counter() - start_time

        logger.info(
            "%s trained successfully in %.2f seconds.",
            model_name,
            elapsed,
        )

        result = TrainingResult(
            model_name=model_name,
            model=model,
            training_time=elapsed,
            train_samples=len(self.X_train),
            validation_samples=len(self.X_validation),
        )

        return result

    # ==========================================================================
    # Train All Models
    # ==========================================================================

    def train_models(self) -> None:
        """
        Train every configured model.
        """

        logger.info("=" * 70)
        logger.info("Starting model training...")

        self.initialize_models()

        for model_name, model in self.models.items():

            result = self.train_model(
                model_name,
                model,
            )

            self.results[model_name] = result

            self.models[model_name] = result.model

        logger.info("=" * 70)
        logger.info(
            "All models trained successfully."
        )

    # ==========================================================================
    # Training Summary
    # ==========================================================================

    def print_training_summary(self) -> None:
        """
        Display training summary.
        """

        logger.info("=" * 70)
        logger.info("Training Summary")
        logger.info("=" * 70)

        for result in self.results.values():

            logger.info(
                "%-18s : %.2f sec",
                result.model_name,
                result.training_time,
            )

        logger.info("=" * 70)

    # ==========================================================================
    # Execute Training Pipeline
    # ==========================================================================

    def run_training(self) -> None:
        """
        Execute the complete training pipeline.
        """

        logger.info("=" * 70)
        logger.info("Initializing trainer...")

        self.initialize()
        self.train_models()
        self.print_training_summary()
        self.evaluate_models()
        self.print_evaluation_summary()
        self.select_best_model()
        self.save_models()
        self.save_best_model()
        self.save_metadata()

        logger.info("=" * 70)
        logger.info("Training pipeline completed successfully.")

    def evaluate_model(
        self,
        result: TrainingResult,
    ) -> None:
        """
        Evaluate one trained model on the validation dataset.
        """

        logger.info("Evaluating %s...", result.model_name)

        predictions = result.model.predict(self.X_validation)

        result.accuracy = accuracy_score(self.y_validation, predictions)
        result.precision = precision_score(
            self.y_validation,
            predictions,
            average="weighted",
            zero_division=0,
        )
        result.recall = recall_score(
            self.y_validation,
            predictions,
            average="weighted",
            zero_division=0,
        )
        result.f1_score = f1_score(
            self.y_validation,
            predictions,
            average="weighted",
            zero_division=0,
        )

        logger.info("%s Accuracy : %.4f", result.model_name, result.accuracy)

    def evaluate_models(self) -> None:
        """
        Evaluate every trained model.
        """

        logger.info("=" * 70)
        logger.info("Evaluating trained models...")

        for result in self.results.values():
            self.evaluate_model(result)

        logger.info("Evaluation completed.")

    def print_evaluation_summary(self) -> None:
        """
        Print evaluation table.
        """

        logger.info("=" * 90)
        logger.info("%-18s %-10s %-10s %-10s %-10s", "MODEL", "ACC", "PREC", "RECALL", "F1")
        logger.info("=" * 90)

        for result in self.results.values():
            logger.info(
                "%-18s %-10.4f %-10.4f %-10.4f %-10.4f",
                result.model_name,
                result.accuracy,
                result.precision,
                result.recall,
                result.f1_score,
            )

        logger.info("=" * 90)

    def select_best_model(self) -> None:
        """
        Select the best model using weighted F1-score.
        """

        logger.info("=" * 70)
        logger.info("Selecting best model...")

        self.best_result = max(self.results.values(), key=lambda r: r.f1_score)
        self.best_model_name = self.best_result.model_name
        self.best_model = self.best_result.model

        logger.info("Best model: %s", self.best_model_name)
        logger.info("Best F1 Score: %.4f", self.best_result.f1_score)

    def save_models(self) -> None:
        """
        Save every trained model.
        """

        models_directory = self.config.output_directory / "models"
        models_directory.mkdir(parents=True, exist_ok=True)

        for result in self.results.values():
            model_path = models_directory / f"{result.model_name}.joblib"
            joblib.dump(result.model, model_path)
            logger.info("Saved model: %s", model_path)

    def save_best_model(self) -> None:
        """
        Save best performing model.
        """

        best_directory = self.config.output_directory / "best_model"
        best_directory.mkdir(parents=True, exist_ok=True)

        model_path = best_directory / "model.joblib"
        joblib.dump(self.best_model, model_path)

        logger.info("Best model saved.")

    def save_metadata(self) -> None:
        """
        Save training metadata.
        """

        self.config.output_directory.mkdir(parents=True, exist_ok=True)

        metadata = {
            "best_model": self.best_model_name,
            "training_samples": len(self.X_train),
            "validation_samples": len(self.X_validation),
            "models": {
                result.model_name: {
                    "accuracy": result.accuracy,
                    "precision": result.precision,
                    "recall": result.recall,
                    "f1_score": result.f1_score,
                    "training_time": result.training_time,
                }
                for result in self.results.values()
            },
        }

        metadata_path = self.config.output_directory / "training_metadata.json"

        with open(metadata_path, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)

        logger.info("Training metadata saved.")


def build_argument_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""

    parser = argparse.ArgumentParser(description="MediGenie Trainer")

    parser.add_argument(
        "--train",
        required=True,
        help="Path to train CSV",
    )

    parser.add_argument(
        "--validation",
        required=True,
        help="Path to validation CSV",
    )

    parser.add_argument(
        "--target",
        required=True,
        help="Target column name",
    )

    parser.add_argument(
        "--output",
        default="backend/ml/training/output",
        help="Output directory",
    )

    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed",
    )

    parser.add_argument(
        "--n-jobs",
        type=int,
        default=-1,
        help="Parallel jobs",
    )

    return parser


def main() -> None:

    args = build_argument_parser().parse_args()

    config = TrainerConfig(
        train_path=Path(args.train),
        validation_path=Path(args.validation),
        target_column=args.target,
        output_directory=Path(args.output),
        random_state=args.random_state,
        n_jobs=args.n_jobs,
    )

    trainer = ModelTrainer(config)
    trainer.run_training()


if __name__ == "__main__":
    main()