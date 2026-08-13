"""
API Routes for Model Verification & Evaluation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(prefix="/evaluation", tags=["Model Evaluation"])

BASE_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = BASE_DIR / "evaluation" / "results"

DISEASES = [
    {"key": "heart_disease", "name": "Heart Disease", "model": "heart_disease"},
    {"key": "diabetes", "name": "Diabetes", "model": "diabetes_model"},
    {"key": "kidney_disease", "name": "Kidney Disease", "model": "kidney_disease_model"},
    {"key": "liver_disease", "name": "Liver Disease", "model": "liver_disease_model"},
    {"key": "breast_cancer", "name": "Breast Cancer", "model": "breast_cancer_model"},
    {"key": "parkinsons", "name": "Parkinson's", "model": "parkinsons_model"},
    {"key": "hepatitis", "name": "Hepatitis", "model": "hepatitis_model"},
    {"key": "heart_failure", "name": "Heart Failure", "model": "heart_failure_model"},
    {"key": "stroke", "name": "Stroke", "model": "stroke_model"},
]


@router.get("/summary", response_model=Dict[str, Any])
def get_evaluation_summary():
    """Returns overview summary for all 9 evaluated models."""
    models_summary = []
    total_models = len(DISEASES)
    verified_count = 0

    for d in DISEASES:
        key = d["key"]
        metrics_file = RESULTS_DIR / key / "metrics.json"

        if metrics_file.exists():
            try:
                with open(metrics_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                
                is_verified = data.get("model_verification", {}).get("100_percent_ml_validation", False)
                if is_verified:
                    verified_count += 1

                models_summary.append({
                    "disease_key": key,
                    "disease_name": d["name"],
                    "model_folder": d["model"],
                    "verified": is_verified,
                    "metrics": {
                        "accuracy": data.get("metrics", {}).get("accuracy"),
                        "f1_score": data.get("metrics", {}).get("f1_score"),
                        "roc_auc": data.get("metrics", {}).get("roc_auc"),
                        "pr_auc": data.get("metrics", {}).get("pr_auc"),
                        "sensitivity": data.get("metrics", {}).get("sensitivity"),
                        "specificity": data.get("metrics", {}).get("specificity"),
                    },
                    "samples": data.get("dataset_verification", {}).get("raw_samples"),
                    "features_count": data.get("dataset_verification", {}).get("feature_count"),
                })
            except Exception as e:
                models_summary.append({
                    "disease_key": key,
                    "disease_name": d["name"],
                    "model_folder": d["model"],
                    "verified": False,
                    "error": str(e),
                })
        else:
            models_summary.append({
                "disease_key": key,
                "disease_name": d["name"],
                "model_folder": d["model"],
                "verified": False,
                "status": "Not Evaluated",
            })

    return {
        "success": True,
        "total_models": total_models,
        "verified_models": verified_count,
        "validation_percentage": round((verified_count / total_models) * 100, 1) if total_models > 0 else 0,
        "models": models_summary,
    }


@router.get("/detail/{disease_key}")
def get_model_evaluation_detail(disease_key: str):
    """Returns complete evaluation metrics, dataset verification, CV and explainability for disease_key."""
    metrics_file = RESULTS_DIR / disease_key / "metrics.json"
    if not metrics_file.exists():
        raise HTTPException(status_code=404, detail=f"Evaluation results not found for disease: {disease_key}")

    try:
        with open(metrics_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return {"success": True, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading metrics for {disease_key}: {e}")


@router.get("/report/{disease_key}")
def get_model_classification_report(disease_key: str):
    """Returns classification report text."""
    report_file = RESULTS_DIR / disease_key / "classification_report.txt"
    if not report_file.exists():
        raise HTTPException(status_code=404, detail=f"Report file not found for disease: {disease_key}")

    content = report_file.read_text(encoding="utf-8")
    return {"success": True, "report": content}


@router.get("/plot/{disease_key}/{image_name}")
def get_evaluation_plot(disease_key: str, image_name: str):
    """Serve evaluation PNG plots (confusion_matrix.png, roc_curve.png, etc.)."""
    allowed_images = {
        "confusion_matrix.png",
        "roc_curve.png",
        "pr_curve.png",
        "feature_importance.png",
        "shap_summary.png",
    }
    if image_name not in allowed_images:
        raise HTTPException(status_code=400, detail="Invalid image requested")

    img_path = RESULTS_DIR / disease_key / image_name
    if not img_path.exists():
        raise HTTPException(status_code=404, detail=f"Image {image_name} not found for {disease_key}")

    return FileResponse(img_path, media_type="image/png")


@router.get("/xai/global")
def get_global_xai_summary():
    """
    Returns aggregated global feature importance / SHAP data for all 9 disease models.
    Used by the XAI Explainability Dashboard page.
    """
    result = []

    for d in DISEASES:
        key = d["key"]
        metrics_file = RESULTS_DIR / key / "metrics.json"
        shap_img = RESULTS_DIR / key / "shap_summary.png"
        feat_img = RESULTS_DIR / key / "feature_importance.png"

        entry = {
            "disease_key": key,
            "disease_name": d["name"],
            "has_shap_plot": shap_img.exists(),
            "has_feature_importance_plot": feat_img.exists(),
            "top_features": [],
            "metrics": {},
        }

        if metrics_file.exists():
            try:
                with open(metrics_file, "r", encoding="utf-8") as fh:
                    data = json.load(fh)

                # Pull top SHAP features
                shap_data = data.get("explainability", {}).get("shap_summary", {})
                if shap_data:
                    sorted_features = sorted(
                        shap_data.items(),
                        key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0,
                        reverse=True,
                    )
                    entry["top_features"] = [
                        {"feature": k, "importance": abs(v)}
                        for k, v in sorted_features[:8]
                        if isinstance(v, (int, float))
                    ]

                # Summary metrics for comparison
                m = data.get("metrics", {})
                entry["metrics"] = {
                    "accuracy": m.get("accuracy"),
                    "f1_score": m.get("f1_score"),
                    "roc_auc": m.get("roc_auc"),
                    "precision": m.get("precision"),
                    "recall": m.get("recall"),
                }
            except Exception as e:
                entry["error"] = str(e)

        result.append(entry)

    return {
        "success": True,
        "total_models": len(result),
        "models": result,
    }


@router.get("/xai/local/{disease_key}")
def get_local_xai_explanation(disease_key: str):
    """
    Returns local feature-level explanation for a specific disease model,
    including feature names, SHAP values, and top contributing features.
    """
    metrics_file = RESULTS_DIR / disease_key / "metrics.json"

    if not metrics_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Evaluation results not found for disease: {disease_key}",
        )

    try:
        with open(metrics_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        shap_data = data.get("explainability", {}).get("shap_summary", {})
        feature_names = data.get("dataset_verification", {}).get("feature_names", [])

        top_features = []
        if shap_data:
            sorted_features = sorted(
                shap_data.items(),
                key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0,
                reverse=True,
            )
            top_features = [
                {"feature": k, "importance": abs(v), "raw_shap": v}
                for k, v in sorted_features
                if isinstance(v, (int, float))
            ]

        return {
            "success": True,
            "disease_key": disease_key,
            "feature_names": feature_names,
            "top_features": top_features,
            "model_folder": next((d["model"] for d in DISEASES if d["key"] == disease_key), ""),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building XAI explanation: {e}")

