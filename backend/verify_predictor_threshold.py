"""Quick verification script for predictor threshold logic and imbalanced-learn."""
import sys
import json

sys.path.insert(0, "d:/MedGini-main/backend")

# 1. Verify imbalanced-learn
print("=" * 60)
print("CHECK 1: imbalanced-learn")
try:
    from imblearn.over_sampling import SMOTE
    print("  PASS - SMOTE imported successfully")
except ImportError as e:
    print(f"  FAIL - {e}")

# 2. Load a real model and verify metadata + threshold
print("=" * 60)
print("CHECK 2: Predictor metadata/threshold loading")
from ml.inference.predictor import load_predictor

model_dirs = {
    "heart_disease": "d:/MedGini-main/backend/models/heart_disease",
    "diabetes": "d:/MedGini-main/backend/models/diabetes_model",
    "breast_cancer": "d:/MedGini-main/backend/models/breast_cancer_model",
    "stroke": "d:/MedGini-main/backend/models/stroke_model",
    "kidney_disease": "d:/MedGini-main/backend/models/kidney_disease_model",
    "liver_disease": "d:/MedGini-main/backend/models/liver_disease_model",
    "hepatitis": "d:/MedGini-main/backend/models/hepatitis_model",
    "parkinsons": "d:/MedGini-main/backend/models/parkinsons_model",
    "heart_failure": "d:/MedGini-main/backend/models/heart_failure_model",
}

for name, path in model_dirs.items():
    print(f"\n--- {name} ---")
    try:
        p = load_predictor(path)
        md = getattr(p, "metadata", None)
        if md is None:
            print(f"  WARN - metadata is None")
        else:
            thr = md.get("threshold", "NOT SET")
            print(f"  metadata.threshold = {thr}")
            print(f"  metadata keys: {list(md.keys())}")
    except Exception as e:
        print(f"  FAIL - {e}")

# 3. Test threshold-based prediction on one model
print("\n" + "=" * 60)
print("CHECK 3: Threshold-based prediction (heart_disease)")
try:
    p = load_predictor("d:/MedGini-main/backend/models/heart_disease")
    # Read schema to know what columns are expected
    with open("d:/MedGini-main/backend/models/heart_disease/schema.json") as f:
        schema = json.load(f)
    cols = [c for c in schema.get("required_columns", []) if c != schema.get("target_column")]
    # Create a dummy patient with all zeros
    dummy = {c: 0 for c in cols}
    result = p.predict(dummy)
    print(f"  prediction = {result.prediction}")
    print(f"  probability = {result.probability}")
    print(f"  confidence = {result.confidence}")
    print(f"  class_probabilities = {result.class_probabilities}")
    thr = p.metadata.get("threshold", 0.5)
    expected_pred = int(result.probability >= thr)
    match = result.prediction == expected_pred
    print(f"  threshold = {thr}")
    print(f"  prob >= threshold? {result.probability} >= {thr} => {expected_pred}")
    print(f"  prediction matches threshold logic: {'PASS' if match else 'FAIL'}")
except Exception as e:
    print(f"  FAIL - {e}")

print("\n" + "=" * 60)
print("All checks complete.")
