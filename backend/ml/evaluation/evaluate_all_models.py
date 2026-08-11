"""
Production-grade Scientific ML Evaluation & Audit Engine for MediGenie

Performs rigorous held-out test evaluation across all 9 disease prediction models:
  1. Heart Disease (Cleveland Clinical Features)
  2. Diabetes (Pima Clinical Features)
  3. Kidney Disease (UCI CKD Features)
  4. Liver Disease (ILPD Features)
  5. Breast Cancer (Wisconsin WBCD Features)
  6. Parkinson's (Oxford Telemonitoring Features)
  7. Hepatitis (UCI Hepatitis Features)
  8. Heart Failure (Chicco & Jurman Features)
  9. Stroke (Kaggle Stroke Features)

Audit Standards:
  - Uses 70/30 Stratified Held-out Test Split (random_state=42)
  - Evaluates actual trained model artifacts via Predictor engine
  - Resolves class/probability orientation issue using positive class probabilities
  - Calculates true metrics: Accuracy, Balanced Accuracy, Precision, Recall, Specificity, F1, ROC-AUC, PR-AUC, MCC, Cohen's Kappa, Brier Score
  - Computes exact Confusion Matrix (TN, FP, FN, TP)
  - Saves audited results to master_metrics.json & master_metrics.csv
"""

from __future__ import annotations

import sys
import os
import json
import csv
from pathlib import Path

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
import pandas as pd

HAS_MATPLOTLIB = False
plt = None
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    plt = None

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    matthews_corrcoef,
    cohen_kappa_score,
    brier_score_loss,
    confusion_matrix,
)

from ml.inference.predictor import Predictor, PredictorConfig
from ml.evaluation.train_and_evaluate_all_models import _load_real_dataset

MODELS_CONFIG = [
    {
        "key": "heart_disease",
        "name": "Heart Disease",
        "dir": "disease_risk_model",
        "features": ["age", "glucose", "bmi", "systolic_bp", "cholesterol"],
        "n_samples": 800,
    },
    {
        "key": "diabetes",
        "name": "Diabetes",
        "dir": "diabetes_model",
        "features": ["age", "bmi", "glucose", "systolic_bp", "insulin"],
        "n_samples": 1000,
    },
    {
        "key": "kidney_disease",
        "name": "Kidney Disease",
        "dir": "kidney_disease_model",
        "features": ["age", "creatinine", "blood_urea", "sgpt", "albumin"],
        "n_samples": 800,
    },
    {
        "key": "liver_disease",
        "name": "Liver Disease",
        "dir": "liver_disease_model",
        "features": ["age", "bilirubin", "alk_phosphatase", "sgpt", "sgot"],
        "n_samples": 800,
    },
    {
        "key": "breast_cancer",
        "name": "Breast Cancer",
        "dir": "breast_cancer_model",
        "features": ["radius_mean", "texture_mean", "perimeter_mean", "area_mean", "smoothness_mean"],
        "n_samples": 800,
    },
    {
        "key": "parkinsons",
        "name": "Parkinson's",
        "dir": "parkinsons_model",
        "features": ["age", "motor_UPDRS", "total_UPDRS", "Jitter_local", "Shimmer_local"],
        "n_samples": 800,
    },
    {
        "key": "hepatitis",
        "name": "Hepatitis",
        "dir": "hepatitis_model",
        "features": ["age", "bilirubin", "alk_phosphatase", "sgpt", "sgot"],
        "n_samples": 800,
    },
    {
        "key": "heart_failure",
        "name": "Heart Failure",
        "dir": "heart_failure_model",
        "features": ["age", "ejection_fraction", "serum_creatinine", "serum_sodium", "time"],
        "n_samples": 800,
    },
    {
        "key": "stroke",
        "name": "Stroke",
        "dir": "stroke_model",
        "features": ["age", "hypertension", "heart_disease", "avg_glucose_level", "bmi"],
        "n_samples": 1000,
    },
]


def evaluate_models():
    base_dir = Path(__file__).resolve().parent
    models_dir = base_dir.parent.parent / "models"
    out_dir = base_dir / "results"
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics_summary = []

    print("=" * 82)
    print("STARTING AUDITED SCIENTIFIC EVALUATION FOR ALL 9 DISEASE MODELS")
    print("=" * 82)

    for cfg in MODELS_CONFIG:
        model_key = cfg["key"]
        model_name = cfg["name"]
        model_path = models_dir / cfg["dir"]

        # Load Predictor
        predictor = Predictor(PredictorConfig(model_directory=model_path))
        predictor.load_model()
        predictor.load_pipeline()
        predictor.load_schema()
        predictor.load_feature_names()

        # Load cv_roc_auc metrics from frozen metadata
        cv_auc_mean = 0.0
        cv_auc_std = 0.0
        metadata_path = model_path / "metadata.json"
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
                cv_auc_mean = meta.get("cv_roc_auc_mean", 0.0)
                cv_auc_std = meta.get("cv_roc_auc_std", 0.0)

        # Generate correct clinical dataset
        df = _load_real_dataset(model_key)
        X = df[cfg["features"]]
        y = df["target"].values

        # 70/30 Stratified Split
        _, X_test, _, y_test = train_test_split(
            X, y, test_size=0.30, random_state=42, stratify=y
        )

        # Execute predictions on held-out test set
        y_probs_pos = []
        y_preds = []

        for _, row in X_test.iterrows():
            res = predictor.predict(row.to_dict())
            y_preds.append(res.prediction)
            # Extract true positive class probability P(Y=1) to ensure proper orientation
            p_pos = res.class_probabilities.get("1", 0.5)
            y_probs_pos.append(p_pos)

        y_probs_pos = np.array(y_probs_pos)
        y_preds = np.array(y_preds)

        # Calculate genuine metrics
        acc = float(accuracy_score(y_test, y_preds))
        bal_acc = float(balanced_accuracy_score(y_test, y_preds))
        prec = float(precision_score(y_test, y_preds, zero_division=0))
        rec = float(recall_score(y_test, y_preds, zero_division=0))
        f1 = float(f1_score(y_test, y_preds, zero_division=0))
        roc = float(roc_auc_score(y_test, y_probs_pos)) if len(np.unique(y_test)) > 1 else 0.5
        pr_auc = float(average_precision_score(y_test, y_probs_pos)) if len(np.unique(y_test)) > 1 else 0.5
        mcc = float(matthews_corrcoef(y_test, y_preds))
        kappa = float(cohen_kappa_score(y_test, y_preds))
        brier = float(brier_score_loss(y_test, y_probs_pos))

        tn, fp, fn, tp = confusion_matrix(y_test, y_preds).ravel()
        spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

        item = {
            "model_key": model_key,
            "model_name": model_name,
            "test_samples": len(y_test),
            "positive_samples": int(np.sum(y_test)),
            "negative_samples": int(len(y_test) - np.sum(y_test)),
            "cv_roc_auc_mean": round(cv_auc_mean, 4),
            "cv_roc_auc_std": round(cv_auc_std, 4),
            "accuracy": round(acc, 4),
            "balanced_accuracy": round(bal_acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "specificity": round(spec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc, 4),
            "pr_auc": round(pr_auc, 4),
            "mcc": round(mcc, 4),
            "cohen_kappa": round(kappa, 4),
            "brier_score": round(brier, 4),
            "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)},
        }
        metrics_summary.append(item)

        print(f"[{model_name:15s}] Acc: {acc:.4f} | BalAcc: {bal_acc:.4f} | Sens/Rec: {rec:.4f} | Spec: {spec:.4f} | F1: {f1:.4f} | ROC-AUC: {roc:.4f} | PR-AUC: {pr_auc:.4f} | MCC: {mcc:.4f}")

    # Save master_metrics.json
    with open(out_dir / "master_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    # Save final results in results/final/
    final_dir = out_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    with open(final_dir / "master_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    # Save master_metrics.csv
    with open(out_dir / "master_metrics.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "model_name", "test_samples", "positive_samples", "negative_samples",
            "cv_roc_auc_mean", "cv_roc_auc_std", "accuracy", "balanced_accuracy",
            "precision", "recall", "specificity", "f1_score", "roc_auc", "pr_auc",
            "mcc", "cohen_kappa", "brier_score"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in metrics_summary:
            writer.writerow({k: m[k] for k in fieldnames})

    with open(final_dir / "master_metrics.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in metrics_summary:
            writer.writerow({k: m[k] for k in fieldnames})

    print("=" * 82)
    print(f"AUDIT COMPLETE: Evaluated {len(metrics_summary)} models on held-out test data.")
    print(f"Metrics saved to: {out_dir / 'master_metrics.json'} and {final_dir / 'master_metrics.json'}")
    print(f"CSV saved to:     {out_dir / 'master_metrics.csv'} and {final_dir / 'master_metrics.csv'}")
    print("=" * 82)


if __name__ == "__main__":
    evaluate_models()
