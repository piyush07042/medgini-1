import json
import os
from pathlib import Path
from ml.inference.predictor import load_predictor

# List of model directories relative to the repository root
BASE_MODELS_PATH = Path(__file__).resolve().parents[0] / "models"

MODELS = [
    "heart_disease",
    "diabetes_model",
    "kidney_disease_model",
    "liver_disease_model",
    "breast_cancer_model",
    "parkinsons_model",
    "hepatitis_model",
    "heart_failure_model",
    "stroke_model",
]

for model_key in MODELS:
    model_path = BASE_MODELS_PATH / model_key
    try:
        predictor = load_predictor(model_path)
        feat_path = model_path / "feature_names.json"
        with open(feat_path, "r", encoding="utf-8") as f:
            feats = json.load(f)
        dummy = {f: 1.0 for f in feats}
        result = predictor.predict_json(dummy)
        print(f"{model_key}: SUCCESS -> {result}")
    except Exception as e:
        print(f"{model_key}: FAILURE -> {e}")
