"""
predictor.py

Production inference engine.

Responsibilities
----------------
✓ Load packaged model
✓ Load preprocessing pipeline
✓ Validate patient input
✓ Preprocess features
✓ Predict disease
✓ Return probabilities
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


class PredictionError(Exception):
    """Base prediction exception."""


class ModelNotLoadedError(PredictionError):
    """Model has not been loaded."""


class InvalidInputError(PredictionError):
    """Invalid patient data."""


@dataclass(slots=True)
class PredictorConfig:
    model_directory: Path


@dataclass(slots=True)
class PredictionResult:
    prediction: int
    probability: float
    confidence: float
    class_probabilities: dict[str, float]


class Predictor:
    """Production inference engine."""

    def __init__(self, config: PredictorConfig) -> None:
        self.config = config
        self.model = None
        self.pipeline = None
        self.schema = None
        self.feature_names = None

    def load_model(self) -> None:
        model_path = self.config.model_directory / "model.joblib"
        if not model_path.exists():
            raise ModelNotLoadedError(model_path)

        self._inject_unpickle_helpers()
        self.model = joblib.load(model_path)
        logger.info("Model loaded.")

    def load_pipeline(self) -> None:
        pipeline_path = self.config.model_directory / "preprocessor.joblib"
        if not pipeline_path.exists():
            self.pipeline = None
            logger.warning(
                "Preprocessing pipeline not found at %s; using raw feature matrix.",
                pipeline_path,
            )
            return

        self._inject_unpickle_helpers()
        self.pipeline = joblib.load(pipeline_path)
        logger.info("Pipeline loaded.")

    def load_schema(self) -> None:
        schema_path = self.config.model_directory / "schema.json"
        with open(schema_path, "r", encoding="utf-8") as file:
            self.schema = json.load(file)
        logger.info("Schema loaded.")

    def load_feature_names(self) -> None:
        feature_path = self.config.model_directory / "feature_names.json"
        if not feature_path.exists():
            self.feature_names = None
            logger.warning(
                "Feature names file not found at %s; using schema-derived columns.",
                feature_path,
            )
            return

        with open(feature_path, "r", encoding="utf-8") as file:
            self.feature_names = json.load(file)

    def initialize(self) -> None:
        self.load_model()
        self.load_pipeline()
        self.load_schema()
        self.load_feature_names()
        logger.info("Inference engine initialized.")

    def _inject_unpickle_helpers(self) -> None:
        """Inject helper functions used during training into __main__."""
        import __main__
        import numpy as np
        
        if not hasattr(__main__, "_to_array"):
            def _to_array(x):
                return np.array(x)
            setattr(__main__, "_to_array", _to_array)

    def validate_input(self, patient_data: dict[str, Any]) -> None:
        """Validate patient input against schema."""
        if self.schema is None:
            raise ModelNotLoadedError("Schema not loaded.")

        required = self.schema.get("required_columns", [])
        missing = [
            column
            for column in required
            if column != self.schema.get("target_column") and column not in patient_data
        ]
        if missing:
            raise InvalidInputError("Missing required fields:\n" + "\n".join(missing))

        logger.info("Patient input validated.")

    def create_dataframe(self, patient_data: dict[str, Any]) -> pd.DataFrame:
        """Convert dictionary to dataframe and select only model schema fields."""
        dataframe = pd.DataFrame([patient_data])

        if self.schema is not None:
            required = [
                column
                for column in self.schema.get("required_columns", [])
                if column != self.schema.get("target_column")
            ]
            if required:
                dataframe = dataframe.reindex(columns=required, fill_value=0.0)

        logger.info("Input dataframe created.")
        return dataframe

    def preprocess(self, dataframe: pd.DataFrame):
        """Apply fitted preprocessing pipeline."""
        if self.pipeline is None:
            logger.warning("No preprocessing pipeline available; using raw dataframe directly.")
            return dataframe

        try:
            transformed = self.pipeline.transform(dataframe)
            logger.info("Input transformed.")
            return transformed
        except Exception as exc:
            logger.warning("Pipeline transform failed; attempting manual preprocessing fallback: %s", exc)
            if self.model is not None and hasattr(self.model, "feature_names_in_"):
                expected = list(self.model.feature_names_in_)
                try:
                    row = dataframe.iloc[0].to_dict()
                    feature_values: list[float] = []

                    def _safe_float(value: Any) -> float:
                        try:
                            return float(value)
                        except Exception:
                            return 0.0

                    for key in expected:
                        value = row.get(key, 0.0)
                        feature_values.append(_safe_float(value))

                    if len(feature_values) == len(expected):
                        logger.info(
                            "Manual preprocessing fallback succeeded with %d features.",
                            len(feature_values),
                        )
                        return np.array([feature_values], dtype=float)
                except Exception:
                    logger.exception("Manual preprocessing fallback failed.")

            raise

    def predict(self, patient_data: dict[str, Any]) -> PredictionResult:
        """Predict disease."""
        if self.model is None:
            raise ModelNotLoadedError("Model not loaded.")

        self.validate_input(patient_data)
        dataframe = self.create_dataframe(patient_data)
        transformed = self.preprocess(dataframe)

        prediction = int(self.model.predict(transformed)[0])
        probabilities = self.model.predict_proba(transformed)[0]
        confidence = float(np.max(probabilities))
        probability = float(probabilities[prediction])
        class_probabilities = {
            str(index): float(value)
            for index, value in enumerate(probabilities)
        }

        logger.info("Prediction completed.")
        return PredictionResult(
            prediction=prediction,
            probability=probability,
            confidence=confidence,
            class_probabilities=class_probabilities,
        )

    def predict_json(self, patient_data: dict[str, Any]) -> dict[str, Any]:
        """JSON-ready prediction."""
        result = self.predict(patient_data)
        return {
            "prediction": result.prediction,
            "probability": result.probability,
            "confidence": result.confidence,
            "class_probabilities": result.class_probabilities,
        }


def load_predictor(model_directory: str | Path) -> Predictor:
    """Load predictor and initialize all artifacts."""
    predictor = Predictor(PredictorConfig(model_directory=Path(model_directory)))
    predictor.initialize()
    return predictor
