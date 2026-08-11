"""
Build a minimal sample Diabetes model and save artifacts expected by
`ml.inference.predictor.Predictor`.

Creates:
- model.joblib
- preprocessor.joblib
- schema.json
- feature_names.json

This mirrors the disease_risk sample builder but with Diabetes-like features.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler


def _to_array(df):
    return df.astype(float).to_numpy()


MODEL_DIR = Path(__file__).resolve().parent


def build():
    feature_names = [
        "age",
        "bmi",
        "glucose",
        "systolic_bp",
        "insulin",
    ]

    # Simple synthetic training data (random but reproducible)
    rng = np.random.RandomState(1)
    X = rng.normal(size=(300, len(feature_names))) * [15, 6, 30, 20, 50] + [45, 28, 110, 120, 80]
    # Label by glucose and BMI noisy threshold to simulate diabetes signal
    y = ((X[:, 2] > 125) | (X[:, 1] > 30)).astype(int)

    preprocessor = Pipeline([
        ("to_array", FunctionTransformer(_to_array, validate=False)),
        ("scaler", StandardScaler()),
    ])

    # Fit preprocessor
    import pandas as _pd

    df = _pd.DataFrame(X, columns=feature_names)
    preprocessor.fit(df)

    model = LogisticRegression(solver="liblinear")
    model.fit(preprocessor.transform(df), y)

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

    print("diabetes sample model built at", MODEL_DIR)


if __name__ == "__main__":
    build()
