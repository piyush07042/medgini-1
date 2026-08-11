"""
Hyperparameter tuning + training harness.

Generates synthetic train/validation datasets for a model based on
its `feature_names.json`, runs GridSearchCV for a couple of candidate
estimators (RandomForest, LogisticRegression), evaluates on validation
set, and saves the best model and an evaluation report.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class HyperTrainConfig:
    model_name: str
    model_dir: Path
    output_dir: Path
    n_samples: int = 2000
    random_state: int = 42


def load_feature_names(model_dir: Path) -> list[str]:
    p = model_dir / "feature_names.json"
    if not p.exists():
        raise FileNotFoundError(p)
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def generate_synthetic_dataset(feature_names: list[str], n: int, seed: int = 0) -> pd.DataFrame:
    rng = np.random.RandomState(seed)
    cols = []
    for i, name in enumerate(feature_names):
        # create different scales by index
        scale = 1.0 + (i % 5) * 2.0
        base = 10 * (1 + (i % 3))
        vals = rng.normal(loc=base, scale=scale, size=n)
        cols.append(vals)
    X = np.vstack(cols).T
    # Simple synthetic label: combination of first two features
    y = ((X[:, 0] + 0.5 * X[:, 1]) > np.median(X[:, 0] + 0.5 * X[:, 1])).astype(int)
    df = pd.DataFrame(X, columns=feature_names)
    df["target"] = y
    return df


def build_candidate_estimators(random_state: int = 42) -> Dict[str, Any]:
    return {
        "rf": RandomForestClassifier(n_estimators=200, random_state=random_state, n_jobs=-1),
        "lr": LogisticRegression(solver="liblinear", max_iter=500),
    }


def tune_and_train(cfg: HyperTrainConfig) -> None:
    logger.info("Hyper-train for model: %s", cfg.model_name)
    feature_names = load_feature_names(cfg.model_dir)
    df = generate_synthetic_dataset(feature_names, cfg.n_samples, seed=cfg.random_state)

    train, val = train_test_split(df, test_size=0.2, stratify=df["target"], random_state=cfg.random_state)

    X_train = train[feature_names]
    y_train = train["target"]
    X_val = val[feature_names]
    y_val = val["target"]

    estimators = build_candidate_estimators(cfg.random_state)

    results = {}

    for name, est in estimators.items():
        logger.info("Tuning %s...", name)

        pipe = Pipeline([("scaler", StandardScaler()), ("est", est)])

        if name == "rf":
            param_grid = {"est__n_estimators": [100, 200], "est__max_depth": [5, 10, None]}
        else:
            param_grid = {"est__C": [0.1, 1.0, 10.0]}

        cv = StratifiedKFold(n_splits=4, shuffle=True, random_state=cfg.random_state)

        gs = GridSearchCV(pipe, param_grid, cv=cv, scoring="f1", n_jobs=-1)
        gs.fit(X_train, y_train)

        best = gs.best_estimator_
        preds = best.predict(X_val)
        probs = None
        if hasattr(best, "predict_proba"):
            probs = best.predict_proba(X_val)[:, 1]

        res = {
            "best_params": gs.best_params_,
            "accuracy": float(accuracy_score(y_val, preds)),
            "precision": float(precision_score(y_val, preds, zero_division=0)),
            "recall": float(recall_score(y_val, preds, zero_division=0)),
            "f1_score": float(f1_score(y_val, preds, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_val, probs)) if probs is not None else None,
        }

        results[name] = res

        # save model
        out_dir = cfg.output_dir / cfg.model_name / name
        out_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(best, out_dir / "model.joblib")
        # save validation CSV
        X_val.assign(target=y_val.reset_index(drop=True)).to_csv(out_dir / "validation.csv", index=False)
        with open(out_dir / "metrics.json", "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2)

        logger.info("Completed %s: f1=%.4f", name, res["f1_score"])

    # choose best by f1
    best_name = max(results.keys(), key=lambda k: results[k]["f1_score"]) if results else None
    if best_name:
        logger.info("Best estimator: %s", best_name)
        # copy best model to output/<model_name>/best_model
        best_src = cfg.output_dir / cfg.model_name / best_name / "model.joblib"
        best_dst = cfg.output_dir / cfg.model_name / "best_model"
        best_dst.mkdir(parents=True, exist_ok=True)
        joblib.dump(joblib.load(best_src), best_dst / "model.joblib")
        # save summary
        summary = {
            "model": cfg.model_name,
            "best_estimator": best_name,
            "results": results,
        }
        with open(cfg.output_dir / cfg.model_name / "summary.json", "w", encoding="utf-8") as fh:
            json.dump(summary, fh, indent=2)

    logger.info("Hyper-train complete for %s", cfg.model_name)


if __name__ == "__main__":
    # Run for diabetes and disease_risk
    base = Path(__file__).resolve().parents[1] / "models"
    out = Path(__file__).resolve().parents[1] / "training_output"

    for model in ["diabetes_model", "disease_risk_model"]:
        cfg = HyperTrainConfig(model_name=model, model_dir=base / model, output_dir=out)
        tune_and_train(cfg)

    print("Done hyper-training")
