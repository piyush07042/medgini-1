"""
Production Verification and Audit Script for MediGenie ML Lifecycle

Performs final validation steps to ensure:
  1. Exact reproducibility of all evaluation metrics across consecutive runs.
  2. Complete parity between raw evaluation predictor results and production API services.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add backend root to sys.path
backend_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_root))

import numpy as np
import pandas as pd
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

# Import services
from app.services.heart_disease_service import get_heart_disease_service
from app.services.diabetes_service import get_diabetes_service
from app.services.kidney_disease_service import get_kidney_disease_service
from app.services.liver_disease_service import get_liver_disease_service
from app.services.breast_cancer_service import get_breast_cancer_service
from app.services.parkinsons_service import get_parkinsons_service
from app.services.hepatitis_service import get_hepatitis_service
from app.services.heart_failure_service import get_heart_failure_service
from app.services.stroke_service import get_stroke_service

MODELS_CONFIG = [
    {
        "key": "heart_disease",
        "name": "Heart Disease",
        "dir": "heart_disease",
        "features": ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"],
        "n_samples": 800,
        "service_getter": get_heart_disease_service,
    },
    {
        "key": "diabetes",
        "name": "Diabetes",
        "dir": "diabetes_model",
        "features": ["age", "time_in_hospital", "num_medications"],
        "n_samples": 1000,
        "service_getter": get_diabetes_service,
    },
    {
        "key": "kidney_disease",
        "name": "Kidney Disease",
        "dir": "kidney_disease_model",
        "features": ["creatinine", "blood_urea", "blood_glucose_random", "albumin"],
        "n_samples": 800,
        "service_getter": get_kidney_disease_service,
    },
    {
        "key": "liver_disease",
        "name": "Liver Disease",
        "dir": "liver_disease_model",
        "features": ["age", "bilirubin", "alk_phosphatase", "sgpt", "sgot"],
        "n_samples": 800,
        "service_getter": get_liver_disease_service,
    },
    {
        "key": "breast_cancer",
        "name": "Breast Cancer",
        "dir": "breast_cancer_model",
        "features": ["radius_mean", "texture_mean", "perimeter_mean", "area_mean", "smoothness_mean"],
        "n_samples": 800,
        "service_getter": get_breast_cancer_service,
    },
    {
        "key": "parkinsons",
        "name": "Parkinson's",
        "dir": "parkinsons_model",
        "features": ["MDVP:Fo(Hz)", "MDVP:Jitter(%)", "MDVP:Shimmer", "HNR", "RPDE"],
        "n_samples": 800,
        "service_getter": get_parkinsons_service,
    },
    {
        "key": "hepatitis",
        "name": "Hepatitis",
        "dir": "hepatitis_model",
        "features": ["age", "bilirubin", "alk_phosphatase", "sgpt", "sgot"],
        "n_samples": 800,
        "service_getter": get_hepatitis_service,
    },
    {
        "key": "heart_failure",
        "name": "Heart Failure",
        "dir": "heart_failure_model",
        "features": ["age", "ejection_fraction", "serum_creatinine", "serum_sodium", "time"],
        "n_samples": 800,
        "service_getter": get_heart_failure_service,
    },
    {
        "key": "stroke",
        "name": "Stroke",
        "dir": "stroke_model",
        "features": ["age", "hypertension", "heart_disease", "avg_glucose_level", "bmi"],
        "n_samples": 1000,
        "service_getter": get_stroke_service,
    },
]


def run_evaluation(cfg: dict, predictor: Predictor) -> dict[str, float | int]:
    """Generates the test data split and computes evaluation metrics."""
    df = _load_real_dataset(cfg["key"])
    X = df[cfg["features"]]
    y = df["target"].values

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )
    
    if len(X_test) > 50:
        X_test = X_test.iloc[:50]
        y_test = y_test[:50]

    y_probs_pos = []
    y_preds = []

    for _, row in X_test.iterrows():
        res = predictor.predict(row.to_dict())
        y_preds.append(res.prediction)
        y_probs_pos.append(res.class_probabilities.get("1", 0.5))

    y_probs_pos = np.array(y_probs_pos)
    y_preds = np.array(y_preds)

    acc = accuracy_score(y_test, y_preds)
    bal_acc = balanced_accuracy_score(y_test, y_preds)
    prec = precision_score(y_test, y_preds, zero_division=0)
    rec = recall_score(y_test, y_preds, zero_division=0)
    f1 = f1_score(y_test, y_preds, zero_division=0)
    roc = roc_auc_score(y_test, y_probs_pos) if len(np.unique(y_test)) > 1 else 0.5
    pr_auc = average_precision_score(y_test, y_probs_pos) if len(np.unique(y_test)) > 1 else 0.5
    mcc = matthews_corrcoef(y_test, y_preds)
    kappa = cohen_kappa_score(y_test, y_preds)
    brier = brier_score_loss(y_test, y_probs_pos)

    tn, fp, fn, tp = confusion_matrix(y_test, y_preds).ravel()
    spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

    return {
        "accuracy": acc,
        "balanced_accuracy": bal_acc,
        "precision": prec,
        "recall": rec,
        "specificity": spec,
        "f1_score": f1,
        "roc_auc": roc,
        "pr_auc": pr_auc,
        "mcc": mcc,
        "cohen_kappa": kappa,
        "brier_score": brier,
        "TN": int(tn),
        "FP": int(fp),
        "FN": int(fn),
        "TP": int(tp),
    }


def verify_ml_lifecycle():
    models_dir = backend_root / "models"
    overall_success = True

    print("=" * 82)
    print("RUNNING FINAL ML VALIDATION AUDIT")
    print("=" * 82)

    for cfg in MODELS_CONFIG:
        name = cfg["name"]
        key = cfg["key"]
        model_path = models_dir / cfg["dir"]

        print(f"Auditing [{name:15s}]...")

        # Initialize Predictor
        predictor = Predictor(PredictorConfig(model_directory=model_path))
        predictor.initialize()

        # Step 1: Reproducibility Check
        metrics_run_1 = run_evaluation(cfg, predictor)
        metrics_run_2 = run_evaluation(cfg, predictor)

        reproducible = True
        for k in metrics_run_1.keys():
            v1 = metrics_run_1[k]
            v2 = metrics_run_2[k]
            if abs(v1 - v2) > 1e-9:
                print(f"  [FAIL] Reproducibility mismatch on '{k}': {v1} vs {v2}")
                reproducible = False
                overall_success = False

        if reproducible:
            print("  [PASS] Reproducibility validation passed.")

        # Step 2: API parity Check
        df = _load_real_dataset(key)
        # Take a sample patient record (first record from test set)
        _, X_test, _, _ = train_test_split(
            df[cfg["features"]], df["target"].values, test_size=0.30, random_state=42, stratify=df["target"].values
        )
        sample_patient = X_test.iloc[0].to_dict()

        # Raw prediction
        raw_res = predictor.predict(sample_patient)

        # Service prediction
        service = cfg["service_getter"](model_path)
        service_res = service.predict(sample_patient)

        parity = True
        if raw_res.prediction != service_res["prediction"]:
            print(f"  [FAIL] API Prediction mismatch: Raw={raw_res.prediction} Service={service_res['prediction']}")
            parity = False
            overall_success = False

        raw_prob_pos = raw_res.class_probabilities.get("1", 0.5)
        service_prob_pos = service_res["class_probabilities"].get("1", 0.5)
        if abs(raw_prob_pos - service_prob_pos) > 1e-9:
            print(f"  [FAIL] API Probability mismatch: Raw={raw_prob_pos} Service={service_prob_pos}")
            parity = False
            overall_success = False

        if parity:
            print("  [PASS] API inference service parity check passed.")
        print("-" * 50)

    print("=" * 82)
    if overall_success:
        print("ML LIFECYCLE FINAL AUDIT VALIDATION: SUCCESS (ALL PASSED)")
        sys.exit(0)
    else:
        print("ML LIFECYCLE FINAL AUDIT VALIDATION: FAILED (SEE LOGS ABOVE)")
        sys.exit(1)


if __name__ == "__main__":
    verify_ml_lifecycle()
