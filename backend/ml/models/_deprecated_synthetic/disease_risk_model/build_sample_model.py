"""
Build a minimal sample disease risk model and save artifacts expected by
`ml.inference.predictor.Predictor`.

Creates:
- model.joblib
- preprocessor.joblib
- schema.json
- feature_names.json

This is a convenience helper for local testing and CI.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler


MODEL_DIR = Path(__file__).resolve().parent


def build():
    # feature names used by risk_assessment
    feature_names = [
        "age",
        "glucose",
        "bmi",
        "systolic_bp",
        "cholesterol",
    ]

    # Simple training data (random but reproducible)
    rng = np.random.RandomState(0)
    X = rng.normal(size=(200, len(feature_names))) * [15, 30, 5, 20, 40] + [50, 100, 25, 130, 200]
    y = (X[:, 1] > 125).astype(int)  # label by glucose threshold

    # Preprocessor: fillna->values and scale
    preprocessor = Pipeline([
        ("to_array", FunctionTransformer(lambda df: df.astype(float).to_numpy(), validate=False)),
        ("scaler", StandardScaler()),
    ])

    # Fit scaler on X
    preprocessor.fit(
        __import__("pandas").DataFrame(X, columns=feature_names)
    )

    model = LogisticRegression(solver="liblinear")
    model.fit(preprocessor.transform(__import__("pandas").DataFrame(X, columns=feature_names)), y)

    # Save artifacts
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, MODEL_DIR / "model.joblib")
    joblib.dump(preprocessor, MODEL_DIR / "preprocessor.joblib")

    schema = {
        "required_columns": feature_names,
        "target_column": "target",
    }

    with open(MODEL_DIR / "schema.json", "w", encoding="utf-8") as fh:
        json.dump(schema, fh)

    with open(MODEL_DIR / "feature_names.json", "w", encoding="utf-8") as fh:
        json.dump(feature_names, fh)

    print("sample model built at", MODEL_DIR)


if __name__ == "__main__":
    build()
