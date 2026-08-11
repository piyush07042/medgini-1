"""
Sample Parkinson's model builder.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

MODEL_DIR = Path(__file__).resolve().parent


def _to_array(df):
    return df.astype(float).to_numpy()


def build():
    feature_names = [
        "age",
        "motor_UPDRS",
        "total_UPDRS",
        "Jitter_local",
        "Shimmer_local",
    ]

    rng = np.random.RandomState(6)
    X = rng.normal(size=(300, len(feature_names))) * [15, 10, 12, 0.02, 0.03] + [60, 20, 25, 0.005, 0.02]
    y = (X[:,1] > 25).astype(int)

    preprocessor = Pipeline([
        ("to_array", FunctionTransformer(_to_array, validate=False)),
        ("scaler", StandardScaler()),
    ])

    import pandas as _pd
    df = _pd.DataFrame(X, columns=feature_names)
    preprocessor.fit(df)

    model = RandomForestClassifier(n_estimators=40, random_state=0)
    model.fit(preprocessor.transform(df), y)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_DIR / "model.joblib")
    joblib.dump(preprocessor, MODEL_DIR / "preprocessor.joblib")

    schema = {"required_columns": feature_names, "target_column": "target"}
    with open(MODEL_DIR / "schema.json", "w", encoding="utf-8") as fh:
        json.dump(schema, fh)
    with open(MODEL_DIR / "feature_names.json", "w", encoding="utf-8") as fh:
        json.dump(feature_names, fh)

    print("parkinsons sample model built at", MODEL_DIR)


if __name__ == "__main__":
    build()
