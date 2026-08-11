"""
train_pipeline.py

Complete training pipeline for MediGenie.

Runs the end-to-end ML workflow from raw dataset to
packaged deployment artifacts.
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from backend.app.schemas.heart_disease import REQUEST_EXAMPLE
from backend.ml.deployment.model_packager import ModelPackager
from backend.ml.deployment.model_packager import PackageConfig
from backend.ml.preprocessing.clean import CleaningConfig
from backend.ml.preprocessing.clean import DatasetCleaner
from backend.ml.preprocessing.feature_engineering import FeatureEngineer
from backend.ml.preprocessing.feature_engineering import FeatureEngineeringConfig
from backend.ml.preprocessing.preprocessor import Preprocessor
from backend.ml.preprocessing.preprocessor import PreprocessorConfig
from backend.ml.preprocessing.schemas.heart_disease import SCHEMA
from backend.ml.preprocessing.split import DatasetSplitter
from backend.ml.preprocessing.split import SplitConfig
from backend.ml.preprocessing.validation import DatasetValidator
from backend.ml.preprocessing.validation import ValidationConfig
from backend.ml.training.evaluator import EvaluatorConfig
from backend.ml.training.evaluator import ModelEvaluator
from backend.ml.training.model_selector import ModelSelector
from backend.ml.training.model_selector import SelectorConfig
from backend.ml.training.trainer import ModelTrainer
from backend.ml.training.trainer import TrainerConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineConfig:
    dataset: Path
    dataset_name: str
    target_column: str
    workspace: Path
    model_output: Path
    random_state: int = 42


class TrainingPipeline:
    """End-to-end ML training pipeline."""

    def __init__(self, config: PipelineConfig) -> None:
        self.config = config

    @property
    def validation_dir(self) -> Path:
        return self.config.workspace / "validation"

    @property
    def clean_dir(self) -> Path:
        return self.config.workspace / "clean"

    @property
    def features_dir(self) -> Path:
        return self.config.workspace / "features"

    @property
    def preprocessor_dir(self) -> Path:
        return self.config.workspace / "preprocessor"

    @property
    def split_dir(self) -> Path:
        return self.config.workspace / "split"

    @property
    def training_dir(self) -> Path:
        return self.config.workspace / "training"

    @property
    def evaluation_dir(self) -> Path:
        return self.config.workspace / "evaluation"

    @property
    def selected_model_dir(self) -> Path:
        return self.config.workspace / "selected_model"

    @property
    def package_assets_dir(self) -> Path:
        return self.config.workspace / "package_assets"

    @property
    def cleaned_dataset_path(self) -> Path:
        return self.clean_dir / "cleaned.csv"

    @property
    def engineered_dataset_path(self) -> Path:
        return self.features_dir / "engineered_dataset.csv"

    @property
    def processed_dataset_path(self) -> Path:
        return self.preprocessor_dir / "processed_dataset.csv"

    @property
    def preprocessor_path(self) -> Path:
        return self.preprocessor_dir / "preprocessor.joblib"

    @property
    def feature_names_path(self) -> Path:
        return self.preprocessor_dir / "feature_names.json"

    @property
    def train_path(self) -> Path:
        return self.split_dir / "train.csv"

    @property
    def validation_path(self) -> Path:
        return self.split_dir / "validation.csv"

    @property
    def test_path(self) -> Path:
        return self.split_dir / "test.csv"

    @property
    def best_model_path(self) -> Path:
        return self.training_dir / "best_model" / "model.joblib"

    @property
    def schema_json_path(self) -> Path:
        return self.package_assets_dir / "schema.json"

    @property
    def packaged_metadata_path(self) -> Path:
        return self.selected_model_dir / "best_model.json"

    def run(self) -> None:
        logger.info("=" * 80)
        logger.info("Starting complete ML pipeline...")

        self.validate()
        self.clean()
        self.feature_engineering()
        self.preprocess()
        self.split()
        self.train()
        self.evaluate()
        self.select_model()
        self.package()

        logger.info("=" * 80)
        logger.info("Pipeline completed successfully.")

    def validate(self) -> None:
        logger.info("=" * 70)
        logger.info("STEP 1 : Dataset Validation")

        validator = DatasetValidator(
            ValidationConfig(
                dataset_path=self.config.dataset,
                dataset_name=self.config.dataset_name,
                output_directory=self.validation_dir,
            )
        )
        validator.validate()

    def clean(self) -> None:
        logger.info("=" * 70)
        logger.info("STEP 2 : Data Cleaning")

        cleaner = DatasetCleaner(
            CleaningConfig(
                dataset_path=self.config.dataset,
                output_directory=self.clean_dir,
                metadata_directory=self.clean_dir / "metadata",
                dataset_name=self.config.dataset_name,
            )
        )
        cleaner.clean()

    def feature_engineering(self) -> None:
        logger.info("=" * 70)
        logger.info("STEP 3 : Feature Engineering")

        engineer = FeatureEngineer(
            FeatureEngineeringConfig(
                dataset_path=self.cleaned_dataset_path,
                dataset_name=self.config.dataset_name,
                output_directory=self.features_dir,
                random_state=self.config.random_state,
            )
        )
        engineer.initialize()
        engineer.create_features()
        engineer.select_features()

        self.features_dir.mkdir(parents=True, exist_ok=True)
        engineer.df.to_csv(self.engineered_dataset_path, index=False)

        with open(self.features_dir / "feature_metadata.json", "w", encoding="utf-8") as file:
            json.dump(asdict(engineer.metadata), file, indent=4)

        logger.info("Saved: %s", self.engineered_dataset_path)

    def preprocess(self) -> None:
        logger.info("=" * 70)
        logger.info("STEP 4 : Preprocessing")

        processor = Preprocessor(
            PreprocessorConfig(
                dataset_path=self.engineered_dataset_path,
                target_column=self.config.target_column,
                output_directory=self.preprocessor_dir,
                numeric_features=[],
                categorical_features=[],
            )
        )
        processor.run()

    def split(self) -> None:
        logger.info("=" * 70)
        logger.info("STEP 5 : Dataset Split")

        splitter = DatasetSplitter(
            SplitConfig(
                dataset_path=self.processed_dataset_path,
                output_directory=self.split_dir,
                target_column=self.config.target_column,
                test_size=0.20,
                validation_size=0.20,
                random_state=self.config.random_state,
                stratify=True,
            )
        )
        splitter.run()

    def train(self) -> None:
        logger.info("=" * 70)
        logger.info("STEP 6 : Model Training")

        trainer = ModelTrainer(
            TrainerConfig(
                train_path=self.train_path,
                validation_path=self.validation_path,
                target_column=self.config.target_column,
                output_directory=self.training_dir,
                random_state=self.config.random_state,
            )
        )
        trainer.run_training()

    def evaluate(self) -> None:
        logger.info("=" * 70)
        logger.info("STEP 7 : Model Evaluation")

        evaluator = ModelEvaluator(
            EvaluatorConfig(
                model_path=self.best_model_path,
                dataset_path=self.test_path,
                target_column=self.config.target_column,
                output_directory=self.evaluation_dir,
            )
        )
        evaluator.run()

    def select_model(self) -> None:
        logger.info("=" * 70)
        logger.info("STEP 8 : Model Selection")

        selector = ModelSelector(
            SelectorConfig(
                evaluation_directory=self.evaluation_dir,
                output_directory=self.selected_model_dir,
            )
        )
        selector.run()

    def package(self) -> None:
        logger.info("=" * 70)
        logger.info("STEP 9 : Model Packaging")

        self.package_assets_dir.mkdir(parents=True, exist_ok=True)

        with open(self.schema_json_path, "w", encoding="utf-8") as file:
            json.dump(SCHEMA, file, indent=4)

        packager = ModelPackager(
            PackageConfig(
                model_path=self.best_model_path,
                preprocessor_path=self.preprocessor_path,
                feature_names_path=self.feature_names_path,
                scaler_path=None,
                encoder_path=None,
                schema_path=self.schema_json_path,
                metadata_path=self.packaged_metadata_path,
                output_directory=self.config.model_output,
                version="1.0.0",
            )
        )
        packager.run()


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MediGenie Training Pipeline")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--workspace", default="backend/ml/pipeline/workspace")
    parser.add_argument("--model-output", default="backend/ml/deployment/output")
    parser.add_argument("--random-state", type=int, default=42)
    return parser


def main() -> None:
    args = build_argument_parser().parse_args()

    pipeline = TrainingPipeline(
        PipelineConfig(
            dataset=Path(args.dataset),
            dataset_name=args.name,
            target_column=args.target,
            workspace=Path(args.workspace),
            model_output=Path(args.model_output),
            random_state=args.random_state,
        )
    )
    pipeline.run()


if __name__ == "__main__":
    main()

    main()