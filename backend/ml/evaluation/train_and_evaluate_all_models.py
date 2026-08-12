"""
MediGenie v3 — Full ML Lifecycle Engine (Phases 1-8)

Phase 1: Dataset correctness — freeze nine datasets, verify URLs/rows/targets.
Phase 2: Experimental methodology — 70/15/15 stratified split, 5-fold CV on train only.
Phase 3: Feature engineering — full clinical feature sets (not arbitrary 5-feature subsets).
Phase 4: Model optimization — RF, XGBoost, Logistic Regression, SVM per disease.
Phase 5: Imbalance — class_weight, SMOTE on TRAIN only, threshold tuning on VALIDATION.
Phase 6: Final evaluation — full metrics + 95% CI on held-out TEST set.
Phase 7: Reproducibility — save all metadata, hashes, versions, split indices.
Phase 8: API verification — verified separately via verify_ml_lifecycle.py.
"""

from __future__ import annotations

import sys
import os
import json
import csv
import hashlib
import logging
import platform
from pathlib import Path

# Add backend root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import joblib
import numpy as np
import pandas as pd
import sklearn
from evaluation.evaluator import DISEASE_MODEL_MAP, load_disease_dataset

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    logger.warning("xgboost not installed; XGBoost will not be available.")

try:
    from imblearn.over_sampling import SMOTE
    HAS_SMOTE = True
except ImportError:
    HAS_SMOTE = False
    logger.warning("imbalanced-learn not installed; SMOTE will not be available.")

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
    roc_curve,
    precision_recall_curve,
)
from sklearn.calibration import calibration_curve

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

from ml.inference.predictor import Predictor, PredictorConfig

# ─── Constants ──────────────────────────────────────────────────────────────────
RAW_DATASETS_DIR = Path(__file__).resolve().parents[2] / "datasets" / "raw"

# Phase 3: Full clinical feature sets — all available numeric features per dataset
MODEL_RAW_FEATURES = {
    "heart_disease": [
        "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
        "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target"
    ],
    "diabetes": [
        "age", "time_in_hospital", "num_lab_procedures", "num_procedures",
        "num_medications", "number_outpatient", "number_emergency",
        "number_inpatient", "number_diagnoses", "target"
    ],
    "kidney_disease": [
        "age", "bp", "sg", "al", "su", "rbc_enc", "pc_enc", "pcc_enc",
        "ba_enc", "bgr", "bu", "sc", "sod", "pot", "hemo", "pcv",
        "wc", "rc", "htn_enc", "dm_enc", "cad_enc", "appet_enc",
        "pe_enc", "ane_enc", "target"
    ],
    "liver_disease": [
        "age", "gender_enc", "bilirubin", "db", "alk_phosphatase",
        "sgpt", "sgot", "tp", "alb", "ag_ratio", "target"
    ],
    "breast_cancer": [
        "radius_mean", "texture_mean", "perimeter_mean", "area_mean",
        "smoothness_mean", "compactness_mean", "concavity_mean", "concave_points_mean",
        "symmetry_mean", "fractal_dimension_mean",
        "radius_se", "texture_se", "perimeter_se", "area_se",
        "smoothness_se", "compactness_se", "concavity_se", "concave_points_se",
        "symmetry_se", "fractal_dimension_se",
        "radius_worst", "texture_worst", "perimeter_worst", "area_worst",
        "smoothness_worst", "compactness_worst", "concavity_worst", "concave_points_worst",
        "symmetry_worst", "fractal_dimension_worst",
        "target"
    ],
    "parkinsons": [
        "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)",
        "MDVP:Jitter(%)", "MDVP:Jitter(Abs)", "MDVP:RAP", "MDVP:PPQ",
        "Jitter:DDP", "MDVP:Shimmer", "MDVP:Shimmer(dB)",
        "Shimmer:APQ3", "Shimmer:APQ5", "MDVP:APQ", "Shimmer:DDA",
        "NHR", "HNR", "RPDE", "DFA", "spread1", "spread2", "D2", "PPE",
        "target"
    ],
    "hepatitis": [
        "age", "sex", "steroid", "antivirals", "fatigue", "malaise",
        "anorexia", "liver_big", "liver_firm", "spleen_palpable",
        "spiders", "ascites", "varices", "bilirubin", "alk_phosphatase",
        "sgot", "albumin", "protime", "histology", "target"
    ],
    "heart_failure": [
        "age", "anaemia", "creatinine_phosphokinase", "diabetes",
        "ejection_fraction", "high_blood_pressure", "platelets",
        "serum_creatinine", "serum_sodium", "sex", "smoking", "time",
        "target"
    ],
    "stroke": [
        "gender_enc", "age", "hypertension", "heart_disease",
        "ever_married_enc", "work_type_enc", "Residence_type_enc",
        "avg_glucose_level", "bmi", "smoking_status_enc", "target"
    ],
}

# ─── Dataset Info ───────────────────────────────────────────────────────────────
DATASET_INFO = {
    "heart_disease": {
        "name": "Cleveland Heart Disease Dataset",
        "source": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/ml/datasets/heart+disease",
        "expected_rows": 303,
        "target_definition": "disease > 0 → 1, else 0",
    },
    "diabetes": {
        "name": "Diabetes 130-US Hospitals Dataset",
        "source": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/dataset/296/diabetes+130-us+hospitals+for+years+1999-2008",
        "expected_rows": 101766,
        "target_definition": "readmitted != NO → 1 (predicting hospital readmission)",
    },
    "kidney_disease": {
        "name": "Chronic Kidney Disease Dataset",
        "source": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/ml/datasets/chronic_kidney_disease",
        "expected_rows": 400,
        "target_definition": "class = ckd → 1, else 0",
    },
    "liver_disease": {
        "name": "Indian Liver Patient Dataset (ILPD)",
        "source": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/ml/datasets/ILPD+(Indian+Liver+Patient+Dataset)",
        "expected_rows": 583,
        "target_definition": "selector = 1 → has liver disease",
    },
    "breast_cancer": {
        "name": "Breast Cancer Wisconsin (Diagnostic) Dataset",
        "source": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/ml/datasets/Breast+Cancer+Wisconsin+(Diagnostic)",
        "expected_rows": 569,
        "target_definition": "diagnosis M → 1 (malignant), B → 0 (benign)",
    },
    "parkinsons": {
        "name": "Parkinsons Dataset",
        "source": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/dataset/174/parkinsons",
        "expected_rows": 195,
        "target_definition": "status = 1 (Parkinson's), 0 (healthy)",
    },
    "hepatitis": {
        "name": "Hepatitis Dataset",
        "source": "UCI Machine Learning Repository",
        "url": "https://archive.ics.uci.edu/ml/datasets/hepatitis",
        "expected_rows": 155,
        "target_definition": "class = 1 → die, 2 → live (mapped: die → 1)",
    },
    "heart_failure": {
        "name": "Heart Failure Clinical Records Dataset",
        "source": "UCI Machine Learning Repository / Chicco & Jurman",
        "url": "https://archive.ics.uci.edu/ml/datasets/Heart+failure+clinical+records",
        "expected_rows": 299,
        "target_definition": "DEATH_EVENT = 1 (died), 0 (survived)",
    },
    "stroke": {
        "name": "Stroke Prediction Dataset",
        "source": "Kaggle",
        "url": "https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset",
        "expected_rows": 5110,
        "target_definition": "stroke = 1 (had stroke), 0 (no stroke)",
    },
}

# Phase 1: Model configurations with full clinical features
MODELS_CONFIG = [
    {
        "key": "heart_disease",
        "name": "Heart Disease",
        "dir": "heart_disease",
        "features": [c for c in MODEL_RAW_FEATURES["heart_disease"] if c != "target"],
        "target": "target",
        "imbalance_strategy": "balanced",
    },
    {
        "key": "diabetes",
        "name": "Diabetes",
        "dir": "diabetes_model",
        "features": [c for c in MODEL_RAW_FEATURES["diabetes"] if c != "target"],
        "target": "target",
        "imbalance_strategy": "balanced",
    },
    {
        "key": "kidney_disease",
        "name": "Kidney Disease",
        "dir": "kidney_disease_model",
        "features": [c for c in MODEL_RAW_FEATURES["kidney_disease"] if c != "target"],
        "target": "target",
        "imbalance_strategy": None,
    },
    {
        "key": "liver_disease",
        "name": "Liver Disease",
        "dir": "liver_disease_model",
        "features": [c for c in MODEL_RAW_FEATURES["liver_disease"] if c != "target"],
        "target": "target",
        "imbalance_strategy": "balanced",
    },
    {
        "key": "breast_cancer",
        "name": "Breast Cancer",
        "dir": "breast_cancer_model",
        "features": [c for c in MODEL_RAW_FEATURES["breast_cancer"] if c != "target"],
        "target": "target",
        "imbalance_strategy": None,
    },
    {
        "key": "parkinsons",
        "name": "Parkinson's",
        "dir": "parkinsons_model",
        "features": [c for c in MODEL_RAW_FEATURES["parkinsons"] if c != "target"],
        "target": "target",
        "imbalance_strategy": "balanced",
    },
    {
        "key": "hepatitis",
        "name": "Hepatitis",
        "dir": "hepatitis_model",
        "features": [c for c in MODEL_RAW_FEATURES["hepatitis"] if c != "target"],
        "target": "target",
        "imbalance_strategy": "balanced",
    },
    {
        "key": "heart_failure",
        "name": "Heart Failure",
        "dir": "heart_failure_model",
        "features": [c for c in MODEL_RAW_FEATURES["heart_failure"] if c != "target"],
        "target": "target",
        "imbalance_strategy": "balanced",
    },
    {
        "key": "stroke",
        "name": "Stroke",
        "dir": "stroke_model",
        "features": [c for c in MODEL_RAW_FEATURES["stroke"] if c != "target"],
        "target": "target",
        "imbalance_strategy": "smote",
    },
]


# ─── Dataset Loaders (Phase 1) ─────────────────────────────────────────────────

def _to_array(x):
    if hasattr(x, "to_numpy"):
        return x.to_numpy(dtype=float)
    return np.array(x, dtype=float)


def _load_real_dataset(key: str) -> pd.DataFrame:
    """Load and clean the raw dataset for the given disease key.
    Returns a DataFrame with all MODEL_RAW_FEATURES columns including 'target'."""
    raw_folder = DISEASE_MODEL_MAP[key]["raw_folder"]
    raw_path = RAW_DATASETS_DIR / raw_folder / "data.csv"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw dataset not found for '{key}': {raw_path}")

    if key == "heart_disease":
        df = pd.read_csv(raw_path, header=None, na_values="?")
        df.columns = [
            "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
            "thalach", "exang", "oldpeak", "slope", "ca", "thal", "target"
        ]
        df["target"] = (df["target"] > 0).astype(int)
        for col in [c for c in df.columns if c != "target"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    elif key == "diabetes":
        df = pd.read_csv(raw_path)
        df = df.replace("?", np.nan)

        def parse_age(v):
            if isinstance(v, str) and "-" in v:
                clean = v.strip("[]() ")
                parts = clean.split("-")
                try:
                    return (float(parts[0]) + float(parts[1])) / 2.0
                except Exception:
                    return 50.0
            return float(v) if pd.notnull(v) else 50.0

        df["age"] = df["age"].apply(parse_age)
        for col in ["time_in_hospital", "num_lab_procedures", "num_procedures",
                     "num_medications", "number_outpatient", "number_emergency",
                     "number_inpatient", "number_diagnoses"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["target"] = (df["readmitted"].astype(str) != "NO").astype(int)

    elif key == "kidney_disease":
        rows = []
        attrs = []
        data_started = False
        with open(raw_path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                text = line.strip()
                if text.startswith("@attribute"):
                    parts = text.split()
                    attrs.append(parts[1].strip("'\"") if len(parts) > 1 else f"col_{len(attrs)}")
                elif text.startswith("@data"):
                    data_started = True
                elif data_started and text and not text.startswith("%"):
                    vals = [v.strip() for v in text.split(",")]
                    if len(vals) > 0 and vals != [""]:
                        rows.append(vals)

        df = pd.DataFrame([r[: len(attrs)] for r in rows], columns=attrs)
        df = df.replace("?", np.nan)
        df["target"] = df["class"].astype(str).apply(lambda x: 1 if "ckd" in x.lower() and "notckd" not in x.lower() else 0)
        # Map ARFF attribute names to our feature names
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
        df["bp"] = pd.to_numeric(df["bp"], errors="coerce")
        df["sg"] = pd.to_numeric(df["sg"], errors="coerce")
        df["al"] = pd.to_numeric(df["al"], errors="coerce")
        df["su"] = pd.to_numeric(df["su"], errors="coerce")
        # Encode categorical columns as binary
        df["rbc_enc"] = (df["rbc"].astype(str).str.strip().str.lower() == "abnormal").astype(float)
        df["pc_enc"] = (df["pc"].astype(str).str.strip().str.lower() == "abnormal").astype(float)
        df["pcc_enc"] = (df["pcc"].astype(str).str.strip().str.lower() == "present").astype(float)
        df["ba_enc"] = (df["ba"].astype(str).str.strip().str.lower() == "present").astype(float)
        df["bgr"] = pd.to_numeric(df["bgr"], errors="coerce")
        df["bu"] = pd.to_numeric(df["bu"], errors="coerce")
        df["sc"] = pd.to_numeric(df["sc"], errors="coerce")
        df["sod"] = pd.to_numeric(df["sod"], errors="coerce")
        df["pot"] = pd.to_numeric(df["pot"], errors="coerce")
        df["hemo"] = pd.to_numeric(df["hemo"], errors="coerce")
        df["pcv"] = pd.to_numeric(df["pcv"], errors="coerce")
        df["wc"] = pd.to_numeric(df.get("wbcc", df.get("wc")), errors="coerce")
        df["rc"] = pd.to_numeric(df.get("rbcc", df.get("rc")), errors="coerce")
        df["htn_enc"] = (df["htn"].astype(str).str.strip().str.lower() == "yes").astype(float)
        df["dm_enc"] = (df["dm"].astype(str).str.strip().str.lower() == "yes").astype(float)
        df["cad_enc"] = (df["cad"].astype(str).str.strip().str.lower() == "yes").astype(float)
        df["appet_enc"] = (df["appet"].astype(str).str.strip().str.lower() == "good").astype(float)
        df["pe_enc"] = (df["pe"].astype(str).str.strip().str.lower() == "yes").astype(float)
        df["ane_enc"] = (df["ane"].astype(str).str.strip().str.lower() == "yes").astype(float)

    elif key == "liver_disease":
        df = pd.read_csv(raw_path, header=None)
        df.columns = [
            "age", "gender", "bilirubin", "db", "alk_phosphatase",
            "sgpt", "sgot", "tp", "alb", "ag_ratio", "target",
        ]
        df = df.replace("?", np.nan)
        df["target"] = (df["target"] == 1).astype(int)
        df["gender_enc"] = (df["gender"].astype(str).str.strip().str.lower() == "male").astype(float)
        for col in ["age", "bilirubin", "db", "alk_phosphatase", "sgpt", "sgot", "tp", "alb", "ag_ratio"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    elif key == "breast_cancer":
        df = pd.read_csv(raw_path, header=None)
        df = df.replace("?", np.nan)
        df["target"] = (df[1].astype(str) == "M").astype(int)
        feature_names = [
            "radius_mean", "texture_mean", "perimeter_mean", "area_mean",
            "smoothness_mean", "compactness_mean", "concavity_mean", "concave_points_mean",
            "symmetry_mean", "fractal_dimension_mean",
            "radius_se", "texture_se", "perimeter_se", "area_se",
            "smoothness_se", "compactness_se", "concavity_se", "concave_points_se",
            "symmetry_se", "fractal_dimension_se",
            "radius_worst", "texture_worst", "perimeter_worst", "area_worst",
            "smoothness_worst", "compactness_worst", "concavity_worst", "concave_points_worst",
            "symmetry_worst", "fractal_dimension_worst"
        ]
        for i, fname in enumerate(feature_names):
            df[fname] = pd.to_numeric(df[2 + i], errors="coerce")

    elif key == "parkinsons":
        df = pd.read_csv(raw_path)
        df = df.replace("?", np.nan)
        df["target"] = df["status"].astype(int)
        feats = [c for c in MODEL_RAW_FEATURES[key] if c != "target"]
        for f in feats:
            df[f] = pd.to_numeric(df[f], errors="coerce")

    elif key == "hepatitis":
        df = pd.read_csv(raw_path, header=None)
        df = df.replace("?", np.nan)
        # Column 0 = class (1=die, 2=live); we map die→1
        df["target"] = (pd.to_numeric(df[0], errors="coerce") == 1).astype(int)
        # Map columns by index to named features
        hep_cols = {
            1: "age", 2: "sex", 3: "steroid", 4: "antivirals", 5: "fatigue",
            6: "malaise", 7: "anorexia", 8: "liver_big", 9: "liver_firm",
            10: "spleen_palpable", 11: "spiders", 12: "ascites", 13: "varices",
            14: "bilirubin", 15: "alk_phosphatase", 16: "sgot", 17: "albumin",
            18: "protime", 19: "histology"
        }
        for idx, name in hep_cols.items():
            df[name] = pd.to_numeric(df[idx], errors="coerce")

    elif key == "heart_failure":
        df = pd.read_csv(raw_path)
        df = df.replace("?", np.nan)
        df["target"] = df["DEATH_EVENT"].astype(int)
        feats = [c for c in MODEL_RAW_FEATURES[key] if c != "target"]
        for col in feats:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    elif key == "stroke":
        df = pd.read_csv(raw_path)
        df = df.replace(["?", "N/A", "n/a"], np.nan)
        df["target"] = df["stroke"].astype(int)
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
        df["bmi"] = pd.to_numeric(df["bmi"], errors="coerce")
        df["hypertension"] = pd.to_numeric(df["hypertension"], errors="coerce")
        df["heart_disease"] = pd.to_numeric(df["heart_disease"], errors="coerce")
        df["avg_glucose_level"] = pd.to_numeric(df["avg_glucose_level"], errors="coerce")
        # Encode categorical features
        df["gender_enc"] = (df["gender"].astype(str).str.strip().str.lower() == "male").astype(float)
        df["ever_married_enc"] = (df["ever_married"].astype(str).str.strip().str.lower() == "yes").astype(float)
        work_map = {"private": 0, "self-employed": 1, "govt_job": 2, "children": 3, "never_worked": 4}
        df["work_type_enc"] = df["work_type"].astype(str).str.strip().str.lower().map(work_map).fillna(0).astype(float)
        df["Residence_type_enc"] = (df["Residence_type"].astype(str).str.strip().str.lower() == "urban").astype(float)
        smoke_map = {"formerly smoked": 1, "never smoked": 0, "smokes": 2, "unknown": 0}
        df["smoking_status_enc"] = df["smoking_status"].astype(str).str.strip().str.lower().map(smoke_map).fillna(0).astype(float)

    else:
        raise ValueError(f"Real dataset loader not implemented for key '{key}'")

    # Validate required columns
    missing_cols = [col for col in MODEL_RAW_FEATURES[key] if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Raw dataset for '{key}' is missing expected columns: {missing_cols}. "
            f"Loaded columns: {list(df.columns)}"
        )

    return df[MODEL_RAW_FEATURES[key]]


def _sha256_file(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _bootstrap_ci(y_true, y_pred, metric_fn, n_boot=1000, ci=0.95):
    """Bootstrap 95% confidence interval for a given metric."""
    rng = np.random.RandomState(42)
    scores = []
    n = len(y_true)
    for _ in range(n_boot):
        idx = rng.randint(0, n, size=n)
        try:
            scores.append(metric_fn(y_true[idx], y_pred[idx]))
        except Exception:
            continue
    if not scores:
        return (0.0, 0.0)
    alpha = (1 - ci) / 2
    lower = float(np.percentile(scores, 100 * alpha))
    upper = float(np.percentile(scores, 100 * (1 - alpha)))
    return (round(lower, 4), round(upper, 4))


# ─── Main Lifecycle ─────────────────────────────────────────────────────────────

def run_full_ml_lifecycle(data_dir: str | Path | None = None):
    base_dir = Path(__file__).resolve().parent
    models_dir = base_dir.parent.parent / "models"
    out_dir = base_dir / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    split_dir = base_dir / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)

    metrics_summary = []

    print("=" * 90)
    print("MEDIGENIE v3 — FULL ML LIFECYCLE ENGINE (PHASES 1-8)")
    print("=" * 90)

    for cfg in MODELS_CONFIG:
        model_key = cfg["key"]
        model_name = cfg["name"]
        model_dir = models_dir / cfg["dir"]
        model_dir.mkdir(parents=True, exist_ok=True)

        model_res_dir = out_dir / model_key
        model_res_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'-' * 90}")
        print(f"  Processing: {model_name} ({model_key})")
        print(f"{'-' * 90}")

        # ── Phase 1: Load & validate dataset ────────────────────────────────
        raw_path = RAW_DATASETS_DIR / DISEASE_MODEL_MAP[model_key]["raw_folder"] / "data.csv"
        csv_candidate = None
        if data_dir:
            candidate = Path(data_dir) / f"{model_key}.csv"
            if candidate.exists():
                csv_candidate = candidate
        if csv_candidate is None:
            candidate2 = Path(__file__).resolve().parent.parent.parent.parent / "datasets" / f"{model_key}.csv"
            if candidate2.exists():
                csv_candidate = candidate2

        if csv_candidate is not None:
            df = pd.read_csv(csv_candidate)
            source_label = "csv override"
        elif raw_path.exists():
            df = _load_real_dataset(model_key)
            source_label = "real raw dataset"
        else:
            raise ValueError(f"Raw dataset not found for '{model_key}' at {raw_path}.")

        dataset_hash = _sha256_file(raw_path) if raw_path.exists() else "csv_override"
        info = DATASET_INFO.get(model_key, {})
        print(f"  Loaded {len(df)} rows (expected ~{info.get('expected_rows', '?')})")

        features = cfg["features"]
        X = df[features]
        y = df["target"].values

        # ── Phase 2: 70/15/15 stratified split ──────────────────────────────
        stratify = y if len(np.unique(y)) > 1 and int(np.bincount(y).min()) >= 2 else None
        if stratify is None:
            logger.warning("Model '%s': insufficient class balance for stratified split.", model_key)

        X_trainval, X_test, y_trainval, y_test = train_test_split(
            X, y, test_size=0.15, random_state=42, stratify=stratify
        )
        strat_tv = y_trainval if stratify is not None else None
        # Split the remaining 85% into 70% train / 15% validation
        # val_fraction = 15/85 ≈ 0.1765
        X_train, X_valid, y_train, y_valid = train_test_split(
            X_trainval, y_trainval, test_size=0.1765, random_state=42, stratify=strat_tv
        )

        # Save split indices for reproducibility (Phase 7)
        np.save(split_dir / f"{model_key}_train.npy", X_train.index.values)
        np.save(split_dir / f"{model_key}_valid.npy", X_valid.index.values)
        np.save(split_dir / f"{model_key}_test.npy", X_test.index.values)
        print(f"  Split: Train={len(y_train)}, Valid={len(y_valid)}, Test={len(y_test)}")

        # ── Phase 3: Preprocessing (fit on train only) ──────────────────────
        preprocessor = Pipeline([
            ("to_array", FunctionTransformer(_to_array, validate=False)),
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        X_train_scaled = preprocessor.fit_transform(X_train)
        X_valid_scaled = preprocessor.transform(X_valid)
        X_test_scaled = preprocessor.transform(X_test)

        # ── Phase 5: Imbalance handling (train split only) ──────────────────
        strategy = cfg.get("imbalance_strategy", None)
        X_train_balanced = X_train_scaled
        y_train_balanced = y_train

        if strategy == "smote" and HAS_SMOTE:
            min_class_count = int(np.bincount(y_train).min())
            k_neighbors = min(5, min_class_count - 1)
            if k_neighbors >= 1:
                smote = SMOTE(random_state=42, k_neighbors=k_neighbors)
                X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train)
                logger.info("SMOTE applied for '%s': %d -> %d training samples.",
                            model_key, len(y_train), len(y_train_balanced))
            else:
                logger.warning("SMOTE skipped for '%s': minority class too small.", model_key)
                strategy = "balanced"

        class_weight = "balanced" if strategy == "balanced" else None

        # ── Phase 4: Model optimization (RF, XGB, LR, SVM) ─────────────────
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

        candidate_classifiers = {
            "RandomForest": RandomForestClassifier(
                n_estimators=200, max_depth=None, random_state=42, class_weight=class_weight
            ),
            "LogisticRegression": LogisticRegression(
                max_iter=2000, class_weight=class_weight, solver="liblinear", random_state=42
            ),
            "SVM": SVC(
                probability=True, class_weight=class_weight, random_state=42
            ),
        }
        if HAS_XGB:
            pos_count = int(np.sum(y_train_balanced))
            neg_count = len(y_train_balanced) - pos_count
            spw = neg_count / pos_count if pos_count > 0 else 1.0
            candidate_classifiers["XGBoost"] = xgb.XGBClassifier(
                use_label_encoder=False, eval_metric="logloss",
                random_state=42, scale_pos_weight=spw if class_weight else 1.0,
                n_estimators=200, max_depth=6,
            )

        if len(y_train_balanced) > 10000:
            if "SVM" in candidate_classifiers:
                logger.info(f"Skipping SVM for {model_key} due to dataset size ({len(y_train_balanced)} rows).")
                del candidate_classifiers["SVM"]

        best_clf_name = None
        best_clf = None
        best_val_score = -1.0
        all_cv_results = {}

        for clf_name, clf in candidate_classifiers.items():
            # 5-fold CV on training data
            try:
                cv_scores = cross_val_score(clf, X_train_balanced, y_train_balanced,
                                            cv=cv, scoring="roc_auc")
            except Exception as e:
                logger.warning("CV failed for %s/%s: %s", model_key, clf_name, e)
                continue

            cv_mean = float(np.mean(cv_scores))
            cv_std = float(np.std(cv_scores))
            all_cv_results[clf_name] = {"cv_roc_auc_mean": round(cv_mean, 4),
                                        "cv_roc_auc_std": round(cv_std, 4)}

            # Fit and evaluate on validation set
            clf.fit(X_train_balanced, y_train_balanced)
            if hasattr(clf, "predict_proba"):
                val_probs = clf.predict_proba(X_valid_scaled)[:, 1]
            else:
                val_probs = clf.predict(X_valid_scaled).astype(float)

            val_score = float(average_precision_score(y_valid, val_probs))  # PR-AUC
            all_cv_results[clf_name]["val_pr_auc"] = round(val_score, 4)

            print(f"    {clf_name:20s} | CV ROC-AUC: {cv_mean:.4f}±{cv_std:.4f} | Val PR-AUC: {val_score:.4f}")

            if val_score > best_val_score:
                best_val_score = val_score
                best_clf_name = clf_name
                best_clf = clf

        print(f"  * Best model: {best_clf_name} (Val PR-AUC={best_val_score:.4f})")

        # Re-fit best classifier on full training data (already fitted but being explicit)
        best_clf.fit(X_train_balanced, y_train_balanced)
        clf = best_clf
        cv_auc_mean = all_cv_results[best_clf_name]["cv_roc_auc_mean"]
        cv_auc_std = all_cv_results[best_clf_name]["cv_roc_auc_std"]

        # ── Phase 5b: Threshold tuning on validation set ────────────────────
        if hasattr(clf, "predict_proba"):
            val_probs = clf.predict_proba(X_valid_scaled)[:, 1]
        else:
            val_probs = clf.predict(X_valid_scaled).astype(float)

        best_threshold = 0.5
        best_bal_acc = 0.0
        for t in np.arange(0.01, 1.0, 0.01):
            preds_t = (val_probs >= t).astype(int)
            ba = float(balanced_accuracy_score(y_valid, preds_t))
            if ba > best_bal_acc:
                best_bal_acc = ba
                best_threshold = round(float(t), 2)
        print(f"  Optimal threshold: {best_threshold} (Val Bal-Acc={best_bal_acc:.4f})")

        # ── Save artifacts (Phase 7) ────────────────────────────────────────
        joblib.dump(clf, model_dir / "model.joblib")
        joblib.dump(preprocessor, model_dir / "preprocessor.joblib")

        schema = {"required_columns": features, "target_column": "target"}
        with open(model_dir / "schema.json", "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)

        with open(model_dir / "feature_names.json", "w", encoding="utf-8") as f:
            json.dump(features, f, indent=2)

        # ── Phase 6: Final evaluation on held-out TEST set ──────────────────
        if hasattr(clf, "predict_proba"):
            y_probs_pos = clf.predict_proba(X_test_scaled)[:, 1]
        else:
            y_probs_pos = clf.predict(X_test_scaled).astype(float)

        y_preds = (y_probs_pos >= best_threshold).astype(int)

        acc = float(accuracy_score(y_test, y_preds))
        bal_acc = float(balanced_accuracy_score(y_test, y_preds))
        prec = float(precision_score(y_test, y_preds, zero_division=0))
        rec = float(recall_score(y_test, y_preds, zero_division=0))
        f1 = float(f1_score(y_test, y_preds, zero_division=0))
        roc = float(roc_auc_score(y_test, y_probs_pos))
        pr_auc_val = float(average_precision_score(y_test, y_probs_pos))
        mcc = float(matthews_corrcoef(y_test, y_preds))
        kappa = float(cohen_kappa_score(y_test, y_preds))
        brier = float(brier_score_loss(y_test, y_probs_pos))
        tn, fp, fn, tp = confusion_matrix(y_test, y_preds).ravel()
        spec = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0

        # 95% Confidence Intervals via bootstrapping
        ci_acc = _bootstrap_ci(y_test, y_preds, accuracy_score)
        ci_f1 = _bootstrap_ci(y_test, y_preds, lambda yt, yp: f1_score(yt, yp, zero_division=0))
        ci_roc = _bootstrap_ci(y_test, y_probs_pos, roc_auc_score)

        item = {
            "model_key": model_key,
            "model_name": model_name,
            "classifier": best_clf_name,
            "threshold": best_threshold,
            "imbalance_strategy": cfg.get("imbalance_strategy") or "none",
            "test_samples": len(y_test),
            "positive_samples": int(np.sum(y_test)),
            "negative_samples": int(len(y_test) - np.sum(y_test)),
            "cv_roc_auc_mean": round(cv_auc_mean, 4),
            "cv_roc_auc_std": round(cv_auc_std, 4),
            "accuracy": round(acc, 4),
            "accuracy_95ci": ci_acc,
            "balanced_accuracy": round(bal_acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "specificity": round(spec, 4),
            "f1_score": round(f1, 4),
            "f1_95ci": ci_f1,
            "roc_auc": round(roc, 4),
            "roc_auc_95ci": ci_roc,
            "pr_auc": round(pr_auc_val, 4),
            "mcc": round(mcc, 4),
            "cohen_kappa": round(kappa, 4),
            "brier_score": round(brier, 4),
            "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)},
            "all_classifiers_cv": all_cv_results,
        }
        metrics_summary.append(item)

        # ── Phase 7: Extended metadata ──────────────────────────────────────
        model_hash = _sha256_file(model_dir / "model.joblib")
        metadata = {
            "model_name": model_name,
            "model_key": model_key,
            "algorithm": best_clf_name,
            "threshold": best_threshold,
            "imbalance_strategy": cfg.get("imbalance_strategy") or "none",
            "dataset_name": info.get("name", "Unknown"),
            "dataset_source": info.get("source", "Unknown"),
            "dataset_url": info.get("url", "Unknown"),
            "target_definition": info.get("target_definition", "Unknown"),
            "real_or_synthetic": source_label,
            "total_samples": len(df),
            "train_samples": len(y_train),
            "validation_samples": len(y_valid),
            "test_samples": len(y_test),
            "feature_count": len(features),
            "target_column": "target",
            "random_state": 42,
            "features": features,
            "train_valid_test_split": "70/15/15 stratified",
            "cross_validation": "5-fold stratified on train only",
            "version": "3.0.0",
            "cv_roc_auc_mean": round(cv_auc_mean, 4),
            "cv_roc_auc_std": round(cv_auc_std, 4),
            "dataset_sha256": dataset_hash,
            "model_sha256": model_hash,
            "software_versions": {
                "python": platform.python_version(),
                "scikit-learn": sklearn.__version__,
                "xgboost": xgb.__version__ if HAS_XGB else "not installed",
                "imbalanced-learn": "installed" if HAS_SMOTE else "not installed",
            },
            "split_indices_dir": str(split_dir),
        }
        with open(model_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        # Save per-model metrics
        with open(model_res_dir / "metrics.json", "w", encoding="utf-8") as f:
            json.dump(item, f, indent=2)

        # ── Generate Evaluation Plots ───────────────────────────────────────
        if plt is not None:
            # 1. Confusion Matrix
            fig, ax = plt.subplots(figsize=(4, 4))
            cm = np.array([[tn, fp], [fn, tp]])
            ax.matshow(cm, cmap=plt.cm.Blues, alpha=0.7)
            for i in range(2):
                for j in range(2):
                    ax.text(x=j, y=i, s=cm[i, j], va='center', ha='center', size='large', weight='bold')
            ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
            ax.set_xticklabels(["Neg (0)", "Pos (1)"]); ax.set_yticklabels(["Neg (0)", "Pos (1)"])
            ax.set_xlabel("Predicted Label"); ax.set_ylabel("True Label")
            ax.set_title(f"{model_name} Confusion Matrix")
            fig.tight_layout(); fig.savefig(model_res_dir / "confusion_matrix.png", dpi=150); plt.close(fig)

            # 2. ROC Curve
            fpr, tpr, _ = roc_curve(y_test, y_probs_pos)
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.plot(fpr, tpr, color="darkorange", lw=2, label=f"ROC Curve (AUC = {roc:.4f})")
            ax.plot([0, 1], [0, 1], color="navy", lw=1, linestyle="--")
            ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
            ax.set_title(f"{model_name} ROC Curve"); ax.legend(loc="lower right")
            fig.tight_layout(); fig.savefig(model_res_dir / "roc_curve.png", dpi=150); plt.close(fig)

            # 3. Precision-Recall Curve
            prec_arr, rec_arr, _ = precision_recall_curve(y_test, y_probs_pos)
            fig, ax = plt.subplots(figsize=(5, 4))
            ax.plot(rec_arr, prec_arr, color="green", lw=2, label=f"PR Curve (AUC = {pr_auc_val:.4f})")
            ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
            ax.set_title(f"{model_name} Precision-Recall Curve"); ax.legend(loc="lower left")
            fig.tight_layout(); fig.savefig(model_res_dir / "pr_curve.png", dpi=150); plt.close(fig)

            # 4. Calibration Curve
            try:
                prob_true, prob_pred = calibration_curve(y_test, y_probs_pos, n_bins=5)
                fig, ax = plt.subplots(figsize=(5, 4))
                ax.plot(prob_pred, prob_true, marker="o", lw=2, color="purple", label=f"Brier = {brier:.4f}")
                ax.plot([0, 1], [0, 1], linestyle="--", color="gray")
                ax.set_xlabel("Mean Predicted Probability"); ax.set_ylabel("Fraction of Positives")
                ax.set_title(f"{model_name} Calibration Curve"); ax.legend(loc="upper left")
                fig.tight_layout(); fig.savefig(model_res_dir / "calibration_curve.png", dpi=150); plt.close(fig)
            except Exception:
                pass

        print(f"  [{model_name:15s}] Acc: {acc:.4f} | BalAcc: {bal_acc:.4f} | Rec: {rec:.4f} | Spec: {spec:.4f} | F1: {f1:.4f} | ROC-AUC: {roc:.4f} | PR-AUC: {pr_auc_val:.4f} | MCC: {mcc:.4f}")

    # ── Export master metrics ───────────────────────────────────────────────────
    with open(out_dir / "master_metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_summary, f, indent=2)

    with open(out_dir / "master_metrics.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "model_name", "classifier", "threshold", "test_samples",
            "positive_samples", "negative_samples",
            "cv_roc_auc_mean", "cv_roc_auc_std", "accuracy", "balanced_accuracy",
            "precision", "recall", "specificity", "f1_score", "roc_auc", "pr_auc",
            "mcc", "cohen_kappa", "brier_score"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in metrics_summary:
            writer.writerow({k: m.get(k, "") for k in fieldnames})

    print("\n" + "=" * 90)
    print(f"ML LIFECYCLE COMPLETE for all {len(metrics_summary)} models.")
    print(f"Master JSON: {out_dir / 'master_metrics.json'}")
    print(f"Master CSV:  {out_dir / 'master_metrics.csv'}")
    print(f"Split indices: {split_dir}")
    print("=" * 90)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run full ML lifecycle for all disease models")
    parser.add_argument("--data-dir", help="Directory containing per-model CSVs named <model_key>.csv", default=None)
    args = parser.parse_args()

    run_full_ml_lifecycle(data_dir=args.data_dir)
