"""
model_selector.py

Production-grade model selection module.

Responsibilities
----------------
✓ Load evaluation reports
✓ Compare multiple models
✓ Rank models
✓ Select best model
✓ Generate comparison report
✓ Save best model metadata
"""

from __future__ import annotations

import argparse
import json
import logging

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

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


class ModelSelectionError(Exception):
    """Base model selection exception."""


class ReportLoadError(ModelSelectionError):
    """Evaluation report loading failed."""


# ==============================================================================
# Configuration
# ==============================================================================


@dataclass(slots=True)
class SelectorConfig:

    evaluation_directory: Path

    output_directory: Path

    ranking_metric: str = "f1_score"


# ==============================================================================
# Model Result
# ==============================================================================


@dataclass(slots=True)
class ModelResult:

    model_name: str

    accuracy: float

    precision: float

    recall: float

    f1_score: float

    roc_auc: float | None

    report_path: Path
    # ==============================================================================
# Model Selector
# ==============================================================================


class ModelSelector:
    """
    Production-grade model selector.
    """

    def __init__(
        self,
        config: SelectorConfig,
    ) -> None:

        self.config = config

        self.results: list[ModelResult] = []

        self.best_model: ModelResult | None = None

    # ==========================================================================
    # Load Evaluation Reports
    # ==========================================================================

    def load_reports(self) -> None:
        """
        Load every evaluation.json file.
        """

        logger.info(
            "Loading evaluation reports..."
        )

        if not self.config.evaluation_directory.exists():

            raise ReportLoadError(
                f"Directory not found:\n"
                f"{self.config.evaluation_directory}"
            )

        report_files = sorted(
            self.config.evaluation_directory.glob(
                "**/evaluation.json"
            )
        )

        if not report_files:

            raise ReportLoadError(
                "No evaluation reports found."
            )

        for report_path in report_files:

            try:

                with open(
                    report_path,
                    "r",
                    encoding="utf-8",
                ) as file:

                    report = json.load(file)

            except Exception as exc:

                raise ReportLoadError(
                    f"Unable to read:\n{report_path}"
                ) from exc

            model_name = report_path.parent.name

            self.results.append(

                ModelResult(

                    model_name=model_name,

                    accuracy=float(
                        report.get("accuracy", 0.0)
                    ),

                    precision=float(
                        report.get("precision", 0.0)
                    ),

                    recall=float(
                        report.get("recall", 0.0)
                    ),

                    f1_score=float(
                        report.get("f1_score", 0.0)
                    ),

                    roc_auc=report.get("roc_auc"),

                    report_path=report_path,

                )

            )

        logger.info(
            "%d evaluation reports loaded.",
            len(self.results),
        )

    # ==========================================================================
    # Validate Results
    # ==========================================================================

    def validate_results(self) -> None:
        """
        Ensure at least one model exists.
        """

        if not self.results:

            raise ModelSelectionError(
                "No models available."
            )

        logger.info(
            "Validation successful."
        )

    # ==========================================================================
    # Print Loaded Models
    # ==========================================================================

    def print_loaded_models(self) -> None:

        logger.info("=" * 60)

        logger.info(
            "Loaded Evaluation Reports"
        )

        logger.info("=" * 60)

        for result in self.results:

            logger.info(
                "%-20s %.4f",
                result.model_name,
                result.f1_score,
            )

        logger.info("=" * 60)

    # ==========================================================================
    # Initialization
    # ==========================================================================

    def initialize(self) -> None:

        self.load_reports()

        self.validate_results()

        self.print_loaded_models()

        logger.info(
            "Initialization completed."
        )
            # ==========================================================================
    # Rank Models
    # ==========================================================================

    def rank_models(self) -> None:
        """
        Rank models using the configured metric.
        """

        logger.info("Ranking models...")

        metric = self.config.ranking_metric

        valid_metrics = {
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "roc_auc",
        }

        if metric not in valid_metrics:

            raise ModelSelectionError(
                f"Unsupported ranking metric: {metric}"
            )

        self.results.sort(
            key=lambda result: (
                getattr(result, metric)
                if getattr(result, metric) is not None
                else -1.0
            ),
            reverse=True,
        )

        self.best_model = self.results[0]

        logger.info(
            "Best model: %s",
            self.best_model.model_name,
        )

    # ==========================================================================
    # Print Ranking
    # ==========================================================================

    def print_ranking(self) -> None:
        """
        Print ranked model table.
        """

        metric = self.config.ranking_metric

        logger.info("=" * 80)

        logger.info(
            "%-5s %-20s %-15s",
            "Rank",
            "Model",
            metric.upper(),
        )

        logger.info("=" * 80)

        for index, result in enumerate(
            self.results,
            start=1,
        ):

            logger.info(
                "%-5d %-20s %-15.4f",
                index,
                result.model_name,
                getattr(result, metric)
                if getattr(result, metric) is not None
                else 0.0,
            )

        logger.info("=" * 80)

    # ==========================================================================
    # Save Comparison CSV
    # ==========================================================================

    def save_comparison_csv(self) -> None:
        """
        Save model comparison table.
        """

        self.config.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        dataframe = pd.DataFrame(
            [
                {
                    "model": result.model_name,
                    "accuracy": result.accuracy,
                    "precision": result.precision,
                    "recall": result.recall,
                    "f1_score": result.f1_score,
                    "roc_auc": result.roc_auc,
                }
                for result in self.results
            ]
        )

        path = (
            self.config.output_directory
            / "model_comparison.csv"
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
    # Save Best Model Metadata
    # ==========================================================================

    def save_best_model_metadata(self) -> None:
        """
        Save metadata for the selected model.
        """

        metadata = {
            "model_name": self.best_model.model_name,
            "accuracy": self.best_model.accuracy,
            "precision": self.best_model.precision,
            "recall": self.best_model.recall,
            "f1_score": self.best_model.f1_score,
            "roc_auc": self.best_model.roc_auc,
            "report_path": str(
                self.best_model.report_path
            ),
        }

        path = (
            self.config.output_directory
            / "best_model.json"
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
        """
        Execute complete model selection pipeline.
        """

        logger.info("=" * 70)
        logger.info(
            "Starting model selection..."
        )

        self.initialize()

        self.rank_models()

        self.print_ranking()

        self.save_comparison_csv()

        self.save_best_model_metadata()

        logger.info("=" * 70)
        logger.info(
            "Model selection completed successfully."
        )
        # ==============================================================================
# CLI
# ==============================================================================

def build_argument_parser():

    parser = argparse.ArgumentParser(
        description="MediGenie Model Selector"
    )

    parser.add_argument(
        "--evaluation-dir",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    parser.add_argument(
        "--metric",
        default="f1_score",
        choices=[
            "accuracy",
            "precision",
            "recall",
            "f1_score",
            "roc_auc",
        ],
    )

    return parser


# ==============================================================================
# Main
# ==============================================================================

def main():

    args = build_argument_parser().parse_args()

    config = SelectorConfig(
        evaluation_directory=Path(
            args.evaluation_dir
        ),
        output_directory=Path(
            args.output
        ),
        ranking_metric=args.metric,
    )

    selector = ModelSelector(config)

    selector.run()


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":

    main()
    