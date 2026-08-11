# ⚠️ DEPRECATED — Synthetic Model Artifacts

These model directories were trained on **programmatically generated (synthetic) data**
using `generate_clinical_dataset()` in `ml/evaluation/train_and_evaluate_all_models.py`.

## Why deprecated?

Phase 2 (August 2026) replaced all synthetic models with models trained on **real clinical
datasets** sourced from UCI and Kaggle. The real models are now saved to:

```
backend/models/<disease_model>/
```

These paths are picked up first by `ml.registry.get_model_registry()`.

## Do NOT use these models

- They were trained on artificially generated distributions, not real patient data.
- Their reported metrics (80–93% accuracy) are inflated and misleading.
- They have been deliberately moved here so the registry ignores them.

## Real model locations

| Disease         | Real model path                              |
|-----------------|----------------------------------------------|
| Heart Disease   | backend/models/disease_risk_model/           |
| Diabetes        | backend/models/diabetes_model/               |
| Kidney Disease  | backend/models/kidney_disease_model/         |
| Liver Disease   | backend/models/liver_disease_model/          |
| Breast Cancer   | backend/models/breast_cancer_model/          |
| Parkinson's     | backend/models/parkinsons_model/             |
| Hepatitis       | backend/models/hepatitis_model/              |
| Heart Failure   | backend/models/heart_failure_model/          |
| Stroke          | backend/models/stroke_model/                 |
