import os
import json
import pandas as pd

raw_dir = r"d:\medigenie\backend\datasets\raw"
model_dir = r"d:\medigenie\backend\ml\models"

mappings = {
    "breast_cancer": "breast_cancer_model",
    "diabetes": "diabetes_model",
    "heart_disease": "disease_risk_model",
    "heart_failure": "heart_failure_model",
    "hepatitis": "hepatitis_model",
    "kidney": "kidney_disease_model",
    "liver": "liver_disease_model",
    "parkinsons": "parkinsons_model",
    "stroke": "stroke_model"
}

for folder_name, model_folder in mappings.items():
    print(f"\n==================== {folder_name} ====================")
    csv_path = os.path.join(raw_dir, folder_name, "data.csv")
    meta_path = os.path.join(raw_dir, folder_name, "metadata.json")
    model_path = os.path.join(model_dir, model_folder)
    
    # Read metadata
    target_col = None
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as fh:
            meta = json.load(fh)
            target_col = meta.get("target_column")
            print(f"Metadata Target: {target_col}")
            
    # Read model schema
    model_features = []
    schema_target = None
    schema_path = os.path.join(model_path, "schema.json")
    if os.path.exists(schema_path):
        with open(schema_path, 'r', encoding='utf-8') as fh:
            schema = json.load(fh)
            model_features = schema.get("required_columns", [])
            schema_target = schema.get("target_column")
            print(f"Model Schema Features: {model_features}")
            print(f"Model Schema Target: {schema_target}")
            
    if os.path.exists(csv_path):
        # We read a few rows to see columns
        try:
            df = pd.read_csv(csv_path)
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            if target_col in df.columns:
                print(f"Target value counts:\n{df[target_col].value_counts().head(5)}")
            else:
                print(f"Target {target_col} NOT found in CSV columns!")
            
            # Check overlap/mapping
            overlap = [f for f in model_features if f in df.columns]
            missing = [f for f in model_features if f not in df.columns]
            print(f"Overlap with model features: {overlap}")
            print(f"Missing model features: {missing}")
        except Exception as e:
            print(f"Error reading CSV: {e}")
