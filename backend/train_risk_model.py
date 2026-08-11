import os
import pickle
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import shap

def generate_sample_clinical_data(n_samples=1000):
    """
    Generates synthetic clinical dataset structured like UCI/Kaggle Diabetes/Cardiovascular datasets.
    Features: Glucose, BMI, Age, Systolic BP, Cholesterol, Risk Flag (0 or 1)
    """
    np.random.seed(42)
    glucose = np.random.normal(120, 30, n_samples).clip(70, 250)
    bmi = np.random.normal(26, 5, n_samples).clip(15, 45)
    age = np.random.randint(20, 80, n_samples)
    systolic_bp = np.random.normal(125, 18, n_samples).clip(90, 200)
    cholesterol = np.random.normal(200, 35, n_samples).clip(120, 320)
    
    # Calculate probability score based on risk features
    risk_score = (
        (glucose > 140) * 0.35 + 
        (bmi > 30) * 0.25 + 
        (systolic_bp > 135) * 0.25 + 
        (age > 50) * 0.15
    )
    
    target = (risk_score + np.random.normal(0, 0.1, n_samples) > 0.4).astype(int)
    
    df = pd.DataFrame({
        'glucose': glucose,
        'bmi': bmi,
        'age': age,
        'systolic_bp': systolic_bp,
        'cholesterol': cholesterol,
        'target': target
    })
    return df

def train_and_save_model():
    print("🚀 [Phase 9] Starting XGBoost Disease Risk Model Training...")
    
    # 1. Load / Prepare Dataset
    df = generate_sample_clinical_data(n_samples=2000)
    
    X = df[['glucose', 'bmi', 'age', 'systolic_bp', 'cholesterol']]
    y = df['target']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 2. Train XGBoost Classifier
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        random_state=42,
        eval_metric='logloss'
    )
    model.fit(X_train, y_train)
    
    # 3. Model Evaluation
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]
    
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    
    print(f"✅ Model Trained Successfully!")
    print(f"📊 Test Accuracy: {acc * 100:.2f}%")
    print(f"📈 ROC-AUC Score: {auc:.4f}")
    
    # 4. Prepare SHAP Explainer
    explainer = shap.TreeExplainer(model)
    
    # 5. Save Artifacts (.pkl)
    output_dir = os.path.join("app", "ml", "models")
    os.makedirs(output_dir, exist_ok=True)
    
    model_path = os.path.join(output_dir, "disease_risk_model.pkl")
    
    artifacts = {
    "model": model,
    "explainer": explainer,
    "feature_names": list(X.columns),
    "metrics": {
        "accuracy": float(acc),
        "roc_auc": float(auc),
    },
    "version": "1.0.0",
}
    
    with open(model_path, "wb") as f:
        pickle.dump(artifacts, f)
        
    print(f"💾 Model artifact saved to: {model_path}")

if __name__ == "__main__":
    train_and_save_model()