"""
evaluator.py

Production-grade model evaluation module for MediGenie.

Responsibilities
----------------
✓ Load trained models
✓ Load validation/test datasets
✓ Generate predictions
✓ Calculate evaluation metrics
✓ Confusion Matrix
✓ Classification Report
✓ ROC-AUC
✓ Precision-Recall
✓ Save reports
✓ Save plots
"""

from __future__ import annotations

import argparse
import json
import logging
import importlib

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    precision_recall_curve,
)

try:
    plt = importlib.import_module("matplotlib.pyplot")
except ImportError:  # pragma: no cover
    plt = None

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


class EvaluationError(Exception):
    """Base evaluation exception."""


class ModelLoadError(EvaluationError):
    """Unable to load model."""


class DatasetLoadError(EvaluationError):
    """Unable to load dataset."""


# ==============================================================================
# Configuration
# ==============================================================================


@dataclass(slots=True)
class EvaluatorConfig:

    model_path: Path

    dataset_path: Path

    output_directory: Path

    target_column: str


# ==============================================================================
# Evaluation Result
# ==============================================================================


@dataclass(slots=True)
class EvaluationResult:

    accuracy: float

    balanced_accuracy: float

    precision: float

    recall: float

    f1_score: float

    roc_auc: float | None

    confusion_matrix: list

    classification_report: dict
    # ==============================================================================
# Model Evaluator
# ==============================================================================


class ModelEvaluator:
    """
    Production-grade model evaluator.
    """

    def __init__(
        self,
        config: EvaluatorConfig,
    ) -> None:

        self.config = config

        self.model: Any | None = None

        self.dataset: pd.DataFrame | None = None

        self.X: pd.DataFrame | None = None

        self.y: pd.Series | None = None

        self.predictions = None

        self.probabilities = None

        self.result: EvaluationResult | None = None

        self.feature_columns: list[str] = []

    # ==========================================================================
    # Load Model
    # ==========================================================================

    def load_model(self) -> None:
        """
        Load trained model.
        """

        logger.info("Loading trained model...")

        if not self.config.model_path.exists():

            raise ModelLoadError(
                f"Model not found:\n"
                f"{self.config.model_path}"
            )

        try:

            self.model = joblib.load(
                self.config.model_path
            )

        except Exception as exc:

            raise ModelLoadError(
                f"Unable to load model.\n{exc}"
            ) from exc

        logger.info("Model loaded successfully.")

    # ==========================================================================
    # Load Dataset
    # ==========================================================================

    def load_dataset(self) -> None:
        """
        Load evaluation dataset.
        """

        logger.info("Loading evaluation dataset...")

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
                f"Unable to load dataset.\n{exc}"
            ) from exc

        logger.info(

            "Dataset loaded successfully "

            "(%d rows × %d columns).",

            len(self.dataset),

            len(self.dataset.columns),

        )

    # ==========================================================================
    # Validate Target
    # ==========================================================================

    def validate_target(self) -> None:
        """
        Validate target column.
        """

        target = self.config.target_column

        if target not in self.dataset.columns:

            raise EvaluationError(

                f"Target column "

                f"'{target}' "

                f"not found."

            )

        logger.info(
            "Target validation successful."
        )

    # ==========================================================================
    # Prepare Features
    # ==========================================================================

    def prepare_features(self) -> None:
        """
        Separate features and target.
        """

        target = self.config.target_column

        self.feature_columns = [

            column

            for column

            in self.dataset.columns

            if column != target

        ]

        self.X = self.dataset[
            self.feature_columns
        ]

        self.y = self.dataset[
            target
        ]

        logger.info(

            "%d feature columns detected.",

            len(self.feature_columns),

        )

    # ==========================================================================
    # Initialization
    # ==========================================================================

    def initialize(self) -> None:
        """
        Initialize evaluator.
        """

        self.load_model()

        self.load_dataset()

        self.validate_target()

        self.prepare_features()

        logger.info(
            "Initialization completed."
        )
            # ==========================================================================
    # Generate Predictions
    # ==========================================================================

    def predict(self) -> None:
        """
        Generate predictions and prediction probabilities.
        """

        logger.info(
            "Generating predictions..."
        )

        self.predictions = self.model.predict(
            self.X
        )

        if hasattr(self.model, "predict_proba"):

            self.probabilities = (
                self.model.predict_proba(
                    self.X
                )
            )

        else:

            self.probabilities = None

        logger.info(
            "Predictions generated successfully."
        )

    # ==========================================================================
    # Calculate ROC-AUC
    # ==========================================================================

    def calculate_roc_auc(self) -> float | None:
        """
        Calculate ROC-AUC score.

        Supports both binary and multiclass problems.
        """

        if self.probabilities is None:

            return None

        try:

            unique_classes = np.unique(
                self.y
            )

            if len(unique_classes) == 2:

                return roc_auc_score(

                    self.y,

                    self.probabilities[:, 1],

                )

            return roc_auc_score(

                self.y,

                self.probabilities,

                multi_class="ovr",

                average="weighted",

            )

        except Exception:

            return None

    # ==========================================================================
    # Evaluate
    # ==========================================================================

    def evaluate(self) -> None:
        """
        Compute evaluation metrics.
        """

        logger.info(
            "Evaluating model..."
        )

        accuracy = accuracy_score(
            self.y,
            self.predictions,
        )

        balanced_accuracy = balanced_accuracy_score(
            self.y,
            self.predictions,
        )

        precision = precision_score(

            self.y,

            self.predictions,

            average="weighted",

            zero_division=0,

        )

        recall = recall_score(

            self.y,

            self.predictions,

            average="weighted",

            zero_division=0,

        )

        f1 = f1_score(

            self.y,

            self.predictions,

            average="weighted",

            zero_division=0,

        )

        roc_auc = self.calculate_roc_auc()

        cm = confusion_matrix(

            self.y,

            self.predictions,

        )

        report = classification_report(

            self.y,

            self.predictions,

            output_dict=True,

            zero_division=0,

        )

        self.result = EvaluationResult(

            accuracy=accuracy,

            balanced_accuracy=balanced_accuracy,

            precision=precision,

            recall=recall,

            f1_score=f1,

            roc_auc=roc_auc,

            confusion_matrix=cm.tolist(),

            classification_report=report,

        )

        logger.info("Evaluation completed.")

    # ==========================================================================
    # Print Metrics
    # ==========================================================================

    def print_metrics(self) -> None:
        """
        Print evaluation summary.
        """

        logger.info("=" * 70)
        logger.info("Evaluation Summary")
        logger.info("=" * 70)

        logger.info(
            "Accuracy : %.4f",
            self.result.accuracy,
        )

        logger.info(
            "Balanced Accuracy : %.4f",
            self.result.balanced_accuracy,
        )

        logger.info(
            "Precision: %.4f",
            self.result.precision,
        )

        logger.info(
            "Recall   : %.4f",
            self.result.recall,
        )

        logger.info(
            "F1 Score : %.4f",
            self.result.f1_score,
        )

        if self.result.roc_auc is not None:

            logger.info(
                "ROC AUC  : %.4f",
                self.result.roc_auc,
            )

        logger.info("=" * 70)
            # ==========================================================================
    # Save Evaluation Report
    # ==========================================================================

    def save_report(self) -> None:
        """
        Save evaluation report as JSON.
        """

        logger.info("Saving evaluation report...")

        self.config.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        report_path = (
            self.config.output_directory
            / "evaluation.json"
        )

        report = {
            "accuracy": self.result.accuracy,
            "balanced_accuracy": self.result.balanced_accuracy,
            "precision": self.result.precision,
            "recall": self.result.recall,
            "f1_score": self.result.f1_score,
            "roc_auc": self.result.roc_auc,
            "confusion_matrix": self.result.confusion_matrix,
            "classification_report": self.result.classification_report,
        }

        with open(
            report_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                report,
                file,
                indent=4,
            )

        logger.info(
            "Saved: %s",
            report_path,
        )

    # ==========================================================================
    # Confusion Matrix Plot
    # ==========================================================================

    def save_confusion_matrix(self) -> None:
        """
        Save confusion matrix figure.
        """

        if plt is None:
            logger.info("matplotlib is not installed; skipping confusion matrix plot.")
            return

        logger.info(
            "Saving confusion matrix..."
        )

        cm = np.array(
            self.result.confusion_matrix
        )

        plt.figure(figsize=(6, 6))

        plt.imshow(
            cm,
            interpolation="nearest",
        )

        plt.colorbar()

        plt.title("Confusion Matrix")

        plt.xlabel("Predicted")

        plt.ylabel("Actual")

        for i in range(cm.shape[0]):

            for j in range(cm.shape[1]):

                plt.text(
                    j,
                    i,
                    str(cm[i, j]),
                    ha="center",
                    va="center",
                )

        plt.tight_layout()

        path = (
            self.config.output_directory
            / "confusion_matrix.png"
        )

        plt.savefig(
            path,
            dpi=300,
            bbox_inches="tight",
        )

        plt.close()

        logger.info(
            "Saved: %s",
            path,
        )

    # ==========================================================================
    # ROC Curve
    # ==========================================================================

    def save_roc_curve(self) -> None:
        """
        Save ROC curve for binary classification.
        """

        if plt is None:
            logger.info("matplotlib is not installed; skipping ROC curve plot.")
            return

        if self.probabilities is None:

            return

        if len(np.unique(self.y)) != 2:

            return

        fpr, tpr, _ = roc_curve(
            self.y,
            self.probabilities[:, 1],
        )

        plt.figure(figsize=(6, 6))

        plt.plot(fpr, tpr)

        plt.plot(
            [0, 1],
            [0, 1],
            linestyle="--",
        )

        plt.xlabel("False Positive Rate")

        plt.ylabel("True Positive Rate")

        plt.title("ROC Curve")

        plt.tight_layout()

        path = (
            self.config.output_directory
            / "roc_curve.png"
        )

        plt.savefig(
            path,
            dpi=300,
            bbox_inches="tight",
        )

        plt.close()

        logger.info(
            "Saved: %s",
            path,
        )

    # ==========================================================================
    # Precision Recall Curve
    # ==========================================================================

    def save_precision_recall_curve(self) -> None:
        """
        Save precision-recall curve.
        """

        if plt is None:
            logger.info("matplotlib is not installed; skipping precision-recall plot.")
            return

        if self.probabilities is None:

            return

        if len(np.unique(self.y)) != 2:

            return

        precision, recall, _ = precision_recall_curve(
            self.y,
            self.probabilities[:, 1],
        )

        plt.figure(figsize=(6, 6))

        plt.plot(
            recall,
            precision,
        )

        plt.xlabel("Recall")

        plt.ylabel("Precision")

        plt.title("Precision Recall Curve")

        plt.tight_layout()

        path = (
            self.config.output_directory
            / "precision_recall_curve.png"
        )

        plt.savefig(
            path,
            dpi=300,
            bbox_inches="tight",
        )

        plt.close()

        logger.info(
            "Saved: %s",
            path,
        )

    # ==========================================================================
    # Execute Pipeline
    # ==========================================================================

    def run(self) -> None:
        """
        Execute evaluation pipeline.
        """

        logger.info("=" * 70)

        logger.info(
            "Starting model evaluation..."
        )

        self.initialize()

        self.predict()

        self.evaluate()

        self.print_metrics()

        self.save_report()

        self.save_confusion_matrix()

        self.save_roc_curve()

        self.save_precision_recall_curve()

        logger.info("=" * 70)

        logger.info(
            "Evaluation completed successfully."
        )
        # ==============================================================================
# CLI
# ==============================================================================

def build_argument_parser():

    parser = argparse.ArgumentParser(
        description="MediGenie Evaluator"
    )

    parser.add_argument(
        "--model",
        required=True,
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

    return parser


# ==============================================================================
# Main
# ==============================================================================

def main():

    args = build_argument_parser().parse_args()

    config = EvaluatorConfig(

        model_path=Path(args.model),

        dataset_path=Path(args.dataset),

        target_column=args.target,

        output_directory=Path(args.output),

    )

    evaluator = ModelEvaluator(config)

    evaluator.run()


# ==============================================================================
# Entry
# ==============================================================================

if __name__ == "__main__":

    main()