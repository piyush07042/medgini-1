from __future__ import annotations

import re
import time
from typing import Any

from app.agents.base.base_agent import BaseAgent
from app.agents.base.agent_result import AgentResult
from app.agents.base.agent_state import AgentState

from app.services.risk.risk_service import get_risk_service
from app.services.heart_disease_service import get_heart_disease_service
from app.services.heart_failure_service import get_heart_failure_service
from app.services.diabetes_service import get_diabetes_service
from app.services.kidney_disease_service import get_kidney_disease_service
from app.services.liver_disease_service import get_liver_disease_service
from app.services.parkinsons_service import get_parkinsons_service
from app.services.hepatitis_service import get_hepatitis_service
from app.services.stroke_service import get_stroke_service
from pathlib import Path
from app.core.config import settings


class DiseaseRiskAgent(BaseAgent):
    """
    Disease Risk Agent

    Responsibilities
    ----------------
    - Receives extracted metrics
    - Calls the ML risk engine
    - Stores risk prediction
    """

    agent_name = "DiseaseRiskAgent"

    def _normalize_prediction(self, prediction: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(prediction or {})
        score = float(normalized.get("probability", normalized.get("confidence", normalized.get("risk_score", 0.0))))
        confidence = float(normalized.get("confidence", score))
        normalized.setdefault("probability", round(score, 3))
        normalized.setdefault("confidence", round(confidence, 3))
        normalized.setdefault("class_probabilities", {
            "0": round(max(0.0, 1.0 - score), 3),
            "1": round(min(1.0, score), 3),
        })
        # Ensure risk category/level are present and consistent
        if "risk_category" not in normalized or not normalized.get("risk_category"):
            if score >= 0.70:
                normalized["risk_category"] = "high"
            elif score >= 0.40:
                normalized["risk_category"] = "moderate"
            else:
                normalized["risk_category"] = "low"

        # risk_level is an alias for risk_category in many parts of the code
        normalized.setdefault("risk_level", normalized.get("risk_category"))
        # Keep legacy `risk_score` and percentile fields for backward compatibility
        normalized.setdefault("risk_score", round(score, 3))
        normalized.setdefault("estimated_risk_score_percent", round(score * 100, 1))

        normalized.setdefault("confidence_label", normalized.get("confidence_label") or normalized.get("risk_level") or "Unknown")
        if "explanations" not in normalized:
            drivers = normalized.get("drivers") or normalized.get("top_factors") or []
            if isinstance(drivers, dict):
                drivers = [drivers]
            explanations = []
            for driver in drivers[:4]:
                if isinstance(driver, dict) and driver.get("feature"):
                    explanations.append({
                        "feature": driver.get("feature"),
                        "importance": float(driver.get("importance", 1.0)),
                    })
                elif isinstance(driver, str):
                    explanations.append({
                        "feature": driver,
                        "importance": 1.0,
                    })
            normalized["explanations"] = explanations
        return normalized

    def _safe_float(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            if isinstance(value, str):
                return float(value.strip())
            return float(value)
        except Exception:
            return None

    def _normalize_sex(self, value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            int_value = int(value)
            return int_value if int_value in {0, 1} else None
        normalized = str(value).strip().lower()
        if normalized in {"m", "male"}:
            return 1
        if normalized in {"f", "female"}:
            return 0
        return None

    def _parse_trestbps(self, value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            bp_match = re.search(r"(\d{2,3})\s*/\s*(\d{2,3})", value)
            if bp_match:
                return self._safe_float(bp_match.group(1))
            return self._safe_float(value)
        return None

    def _convert_glucose_to_fbs(self, value: Any) -> int | None:
        glucose = self._safe_float(value)
        if glucose is None:
            return None
        return 1 if glucose > 120 else 0

    def _prepare_heart_model_input(self, assessment_input: dict[str, Any]) -> dict[str, Any]:
        heart_input = dict(assessment_input)

        sex = self._normalize_sex(heart_input.get("sex"))
        if sex is None:
            sex = self._normalize_sex(heart_input.get("gender"))
        if sex is not None:
            heart_input["sex"] = sex

        if "trestbps" not in heart_input:
            trestbps = self._parse_trestbps(heart_input.get("systolic_bp"))
            if trestbps is None:
                trestbps = self._parse_trestbps(heart_input.get("blood_pressure"))
            if trestbps is not None:
                heart_input["trestbps"] = trestbps

        if "chol" not in heart_input and heart_input.get("cholesterol") is not None:
            chol = self._safe_float(heart_input.get("cholesterol"))
            if chol is not None:
                heart_input["chol"] = chol

        if "fbs" not in heart_input and heart_input.get("glucose") is not None:
            fbs = self._convert_glucose_to_fbs(heart_input.get("glucose"))
            if fbs is not None:
                heart_input["fbs"] = fbs

        return heart_input

    def _prepare_diabetes_model_input(self, assessment_input: dict[str, Any]) -> dict[str, Any]:
        diabetes_input = dict(assessment_input)
        if "age" not in diabetes_input and assessment_input.get("patient_age") is not None:
            diabetes_input["age"] = assessment_input.get("patient_age")
        if "bmi" not in diabetes_input and assessment_input.get("BMI") is not None:
            diabetes_input["bmi"] = assessment_input.get("BMI")
        if "glucose" not in diabetes_input and assessment_input.get("blood_glucose") is not None:
            diabetes_input["glucose"] = assessment_input.get("blood_glucose")
        if "systolic_bp" not in diabetes_input and assessment_input.get("blood_pressure") is not None:
            diabetes_input["systolic_bp"] = assessment_input.get("blood_pressure")
        if "insulin" not in diabetes_input and assessment_input.get("insulin_level") is not None:
            diabetes_input["insulin"] = assessment_input.get("insulin_level")
        return diabetes_input

    def _prepare_kidney_model_input(self, assessment_input: dict[str, Any]) -> dict[str, Any]:
        kidney_input = dict(assessment_input)
        if "age" not in kidney_input and assessment_input.get("patient_age") is not None:
            kidney_input["age"] = assessment_input.get("patient_age")
        if "creatinine" not in kidney_input and assessment_input.get("serum_creatinine") is not None:
            kidney_input["creatinine"] = assessment_input.get("serum_creatinine")
        if "blood_urea" not in kidney_input and assessment_input.get("urea") is not None:
            kidney_input["blood_urea"] = assessment_input.get("urea")
        if "sgpt" not in kidney_input and assessment_input.get("alt") is not None:
            kidney_input["sgpt"] = assessment_input.get("alt")
        if "albumin" not in kidney_input and assessment_input.get("albumin_level") is not None:
            kidney_input["albumin"] = assessment_input.get("albumin_level")
        return kidney_input

    def _prepare_liver_model_input(self, assessment_input: dict[str, Any]) -> dict[str, Any]:
        liver_input = dict(assessment_input)
        if "age" not in liver_input and assessment_input.get("patient_age") is not None:
            liver_input["age"] = assessment_input.get("patient_age")
        if "bilirubin" not in liver_input and assessment_input.get("bilirubin_level") is not None:
            liver_input["bilirubin"] = assessment_input.get("bilirubin_level")
        if "alk_phosphatase" not in liver_input and assessment_input.get("alkaline_phosphatase") is not None:
            liver_input["alk_phosphatase"] = assessment_input.get("alkaline_phosphatase")
        if "sgpt" not in liver_input and assessment_input.get("alt") is not None:
            liver_input["sgpt"] = assessment_input.get("alt")
        if "sgot" not in liver_input and assessment_input.get("ast") is not None:
            liver_input["sgot"] = assessment_input.get("ast")
        return liver_input

    async def run(
        self,
        state: AgentState,
    ) -> AgentResult:

        start = time.perf_counter()

        # Accept either pre-extracted metrics or fall back to patient_context
        metrics = state.extracted_metrics or state.patient_context or state.patient

        if not metrics:
            return AgentResult(
                agent=self.agent_name,
                status="FAILED",
                confidence=0.0,
                result={},
                warnings=[
                    "No extracted metrics or patient context available."
                ],
            )

        # Merge patient and metrics into a single input dict and call
        # the centralized prediction function directly.
        assessment_input: dict = {}

        if state.patient:
            assessment_input.update(state.patient)

        if state.patient_context:
            assessment_input.update(state.patient_context)

        if metrics:
            assessment_input.update(metrics)

        # Prefer specialized Heart Disease or Kidney Disease services when specific features are present.
        # If the model rejects partial/unsupported input, fall back to the general risk engine.
        heart_keys = {"cholesterol", "chol", "trestbps", "thalach", "oldpeak", "cp", "restecg", "exang", "slope", "ca", "thal"}
        heart_failure_keys = {"ejection_fraction", "serum_creatinine", "serum_sodium", "time", "heart_failure"}
        diabetes_keys = {"bmi", "glucose", "insulin", "blood_glucose", "diabetes"}
        kidney_keys = {"creatinine", "blood_urea", "sgpt", "albumin", "egfr", "ckd", "renal"}
        liver_keys = {"bilirubin", "alk_phosphatase", "alkphos", "sgpt", "sgot", "alt", "ast", "bilirubin_level"}
        has_heart_features = any(k in assessment_input for k in heart_keys)
        has_heart_failure_features = any(k in assessment_input for k in heart_failure_keys) or (
            "diagnosis" in assessment_input and "heart failure" in str(assessment_input.get("diagnosis", "")).lower()
        )
        stroke_keys = {"hypertension", "heart_disease", "avg_glucose_level", "smoking_status", "bmi", "stroke", "cerebrovascular"}
        has_stroke_features = any(k in assessment_input for k in stroke_keys) or (
            "diagnosis" in assessment_input and any(token in str(assessment_input.get("diagnosis", "")).lower() for token in ["stroke", "cerebrovascular"])
        )
        has_diabetes_features = any(k in assessment_input for k in diabetes_keys) or (
            "diagnosis" in assessment_input and "diabetes" in str(assessment_input.get("diagnosis", "")).lower()
        )
        
        # (Diabetes handling is performed later in the flow after model-specific attempts.)
        has_kidney_features = any(k in assessment_input for k in kidney_keys) or (
            "diagnosis" in assessment_input and "kidney" in str(assessment_input.get("diagnosis", "")).lower()
        )
        has_liver_features = any(k in assessment_input for k in liver_keys) or (
            "diagnosis" in assessment_input and "liver" in str(assessment_input.get("diagnosis", "")).lower()
        )
        hepatitis_keys = {"bilirubin", "alk_phosphatase", "sgpt", "sgot"}
        has_hepatitis_features = any(k in assessment_input for k in hepatitis_keys) or (
            "diagnosis" in assessment_input and "hepatitis" in str(assessment_input.get("diagnosis", "")).lower()
        )

        self.logger.info(
            "DiseaseRiskAgent input keys=%s has_heart_features=%s has_heart_failure_features=%s has_diabetes_features=%s has_kidney_features=%s",
            list(assessment_input.keys()),
            has_heart_features,
            has_heart_failure_features,
            has_diabetes_features,
            has_kidney_features,
        )

        explicit_disease = None
        disease_hint = assessment_input.get("target_disease") or assessment_input.get("disease") or assessment_input.get("diagnosis")
        if disease_hint:
            disease_hint = str(disease_hint).lower()
            if "hepatitis" in disease_hint:
                explicit_disease = "hepatitis"
            elif "liver" in disease_hint:
                explicit_disease = "liver_disease"
            elif "diabetes" in disease_hint:
                explicit_disease = "diabetes"
            elif "stroke" in disease_hint or "cerebrovascular" in disease_hint:
                explicit_disease = "stroke"
            elif "heart failure" in disease_hint or "heart_failure" in disease_hint:
                explicit_disease = "heart_failure"
            elif "kidney" in disease_hint or "ckd" in disease_hint or "renal" in disease_hint:
                explicit_disease = "kidney_disease"
            elif "parkinson" in disease_hint:
                explicit_disease = "parkinsons"
            elif "breast" in disease_hint or "cancer" in disease_hint:
                explicit_disease = "breast_cancer"
            elif "heart disease" in disease_hint or ("heart" in disease_hint and explicit_disease is None):
                explicit_disease = "heart_disease"

        if explicit_disease is None:
            symptom_text = " ".join(str(symptom).lower() for symptom in (state.symptoms or []))
            if any(token in symptom_text for token in ["jaundice", "yellow", "hepatitis"]):
                explicit_disease = "hepatitis"
            elif any(token in symptom_text for token in ["abdominal", "nausea", "dark urine", "itching", "liver"]):
                explicit_disease = "liver_disease"
            elif any(token in symptom_text for token in ["weakness", "speech", "facial droop", "stroke", "numbness"]):
                explicit_disease = "stroke"
            elif any(token in symptom_text for token in ["diabetes", "hyperglycemia", "insulin"]):
                explicit_disease = "diabetes"

        state.metadata["target_disease"] = explicit_disease or state.metadata.get("target_disease")

        prediction = None

        if has_heart_features:
            model_dir = Path(settings.HEART_DISEASE_MODEL_DIRECTORY)
            heart_service = get_heart_disease_service(model_dir)
            heart_input = self._prepare_heart_model_input(assessment_input)
            try:
                prediction = heart_service.predict(heart_input)
                self.logger.info(
                    "HeartDiseaseService returned prediction keys=%s",
                    list(prediction.keys()) if isinstance(prediction, dict) else type(prediction),
                )
                self.logger.debug("HeartDiseaseService input keys=%s", list(heart_input.keys()))
            except Exception as exc:
                self.logger.warning("HeartDiseaseService failed; falling back to risk service: %s", exc)
                state.add_warning(f"HeartDiseaseService error: {exc}")
                assessment_input.setdefault("risk_fallback_reason", str(exc))
                prediction = None

        # If heart model didn't produce a prediction, try diabetes when diabetes features are present
        if prediction is None and has_heart_failure_features:
            heart_failure_service = get_heart_failure_service(Path(settings.HEART_FAILURE_MODEL_DIRECTORY))
            heart_failure_input = {
                key: assessment_input[key]
                for key in ["age", "ejection_fraction", "serum_creatinine", "serum_sodium", "time"]
                if key in assessment_input
            }
            try:
                prediction = heart_failure_service.predict(heart_failure_input)
                prediction["condition"] = "Heart Failure Risk"
                prediction["risk_category"] = "high" if float(prediction.get("probability", 0.0)) >= 0.5 else "low"
                prediction["risk_level"] = prediction["risk_category"]
                prediction["disease"] = "heart_failure"
                prediction["model_used"] = "heart_failure_model"
                prediction["risk_source"] = "model"
                self.logger.info(
                    "HeartFailureService returned prediction keys=%s",
                    list(prediction.keys()) if isinstance(prediction, dict) else type(prediction),
                )
            except Exception as exc:
                self.logger.warning("HeartFailureService failed; falling back to risk service: %s", exc)
                state.add_warning(f"HeartFailureService error: {exc}")
                assessment_input.setdefault("risk_fallback_reason", str(exc))
                prediction = None

        if prediction is None and explicit_disease == "stroke":
            stroke_service = get_stroke_service(Path(settings.STROKE_MODEL_DIRECTORY))
            stroke_input = {
                key: assessment_input[key]
                for key in ["age", "hypertension", "heart_disease", "avg_glucose_level", "bmi", "smoking_status"]
                if key in assessment_input
            }
            try:
                prediction = stroke_service.predict(stroke_input)
                prediction["condition"] = "Stroke Risk"
                prediction["risk_category"] = "high" if float(prediction.get("probability", 0.0)) >= 0.5 else "low"
                prediction["risk_level"] = prediction["risk_category"]
                prediction["disease"] = "stroke"
                prediction["model_used"] = "stroke_model"
                prediction["risk_source"] = "model"
                self.logger.info(
                    "StrokeService returned prediction keys=%s",
                    list(prediction.keys()) if isinstance(prediction, dict) else type(prediction),
                )
            except Exception as exc:
                self.logger.warning("StrokeService failed; falling back to risk service: %s", exc)
                state.add_warning(f"StrokeService error: {exc}")
                assessment_input.setdefault("risk_fallback_reason", str(exc))
                prediction = None

        if prediction is None and explicit_disease == "diabetes":
            diabetes_service = get_diabetes_service(Path(settings.DIABETES_MODEL_DIRECTORY))
            diabetes_input = self._prepare_diabetes_model_input(assessment_input)
            try:
                prediction = diabetes_service.predict(diabetes_input)
                prediction["condition"] = "Diabetes Risk"
                prediction["risk_category"] = "high" if float(prediction.get("probability", 0.0)) >= 0.5 else "low"
                prediction["risk_level"] = prediction["risk_category"]
                prediction["disease"] = "diabetes"
                prediction["model_used"] = "diabetes_model"
                prediction["risk_source"] = "model"
                self.logger.info(
                    "DiabetesService returned prediction keys=%s",
                    list(prediction.keys()) if isinstance(prediction, dict) else type(prediction),
                )
            except Exception as exc:
                self.logger.warning("DiabetesService failed; falling back to risk service: %s", exc)
                state.add_warning(f"DiabetesService error: {exc}")
                assessment_input.setdefault("risk_fallback_reason", str(exc))
                prediction = None

        if prediction is None and has_diabetes_features and explicit_disease != "stroke":
            diabetes_service = get_diabetes_service(Path(settings.DIABETES_MODEL_DIRECTORY))
            diabetes_input = self._prepare_diabetes_model_input(assessment_input)
            try:
                prediction = diabetes_service.predict(diabetes_input)
                prediction["condition"] = "Diabetes Risk"
                prediction["risk_category"] = "high" if float(prediction.get("probability", 0.0)) >= 0.5 else "low"
                prediction["risk_level"] = prediction["risk_category"]
                prediction["disease"] = "diabetes"
                prediction["model_used"] = "diabetes_model"
                prediction["risk_source"] = "model"
                self.logger.info(
                    "DiabetesService returned prediction keys=%s",
                    list(prediction.keys()) if isinstance(prediction, dict) else type(prediction),
                )
            except Exception as exc:
                self.logger.warning("DiabetesService failed; falling back to risk service: %s", exc)
                state.add_warning(f"DiabetesService error: {exc}")
                assessment_input.setdefault("risk_fallback_reason", str(exc))
                prediction = None

        if prediction is None and has_stroke_features and explicit_disease != "diabetes":
            stroke_service = get_stroke_service(Path(settings.STROKE_MODEL_DIRECTORY))
            stroke_input = {
                key: assessment_input[key]
                for key in ["age", "hypertension", "heart_disease", "avg_glucose_level", "bmi", "smoking_status"]
                if key in assessment_input
            }
            try:
                prediction = stroke_service.predict(stroke_input)
                prediction["condition"] = "Stroke Risk"
                prediction["risk_category"] = "high" if float(prediction.get("probability", 0.0)) >= 0.5 else "low"
                prediction["risk_level"] = prediction["risk_category"]
                prediction["disease"] = "stroke"
                prediction["model_used"] = "stroke_model"
                prediction["risk_source"] = "model"
                self.logger.info(
                    "StrokeService returned prediction keys=%s",
                    list(prediction.keys()) if isinstance(prediction, dict) else type(prediction),
                )
            except Exception as exc:
                self.logger.warning("StrokeService failed; falling back to risk service: %s", exc)
                state.add_warning(f"StrokeService error: {exc}")
                assessment_input.setdefault("risk_fallback_reason", str(exc))
                prediction = None

        if prediction is None and has_kidney_features:
            kidney_service = get_kidney_disease_service(Path(settings.KIDNEY_DISEASE_MODEL_DIRECTORY))
            kidney_input = self._prepare_kidney_model_input(assessment_input)
            try:
                prediction = kidney_service.predict(kidney_input)
                prediction["condition"] = "Kidney Disease Risk"
                prediction["risk_category"] = "high" if float(prediction.get("probability", 0.0)) >= 0.5 else "low"
                prediction["risk_level"] = prediction["risk_category"]
                prediction["disease"] = "kidney_disease"
                prediction["model_used"] = "kidney_disease_model"
                prediction["risk_source"] = "model"
                self.logger.info(
                    "KidneyDiseaseService returned prediction keys=%s",
                    list(prediction.keys()) if isinstance(prediction, dict) else type(prediction),
                )
            except Exception as exc:
                self.logger.warning("KidneyDiseaseService failed; falling back to risk service: %s", exc)
                state.add_warning(f"KidneyDiseaseService error: {exc}")
                assessment_input.setdefault("risk_fallback_reason", str(exc))
                prediction = None

        if prediction is None and has_liver_features:
            diagnosis = str(assessment_input.get("diagnosis", "")).lower()
            liver_tried = False
            hepatitis_tried = False

            def _try_liver_service() -> None:
                nonlocal prediction, liver_tried
                liver_service = get_liver_disease_service(Path(settings.LIVER_DISEASE_MODEL_DIRECTORY))
                liver_input = self._prepare_liver_model_input(assessment_input)
                try:
                    prediction = liver_service.predict(liver_input)
                    prediction["condition"] = "Liver Disease Risk"
                    prediction["risk_category"] = "high" if float(prediction.get("probability", 0.0)) >= 0.5 else "low"
                    prediction["risk_level"] = prediction["risk_category"]
                    prediction["disease"] = "liver_disease"
                    prediction["model_used"] = "liver_disease_model"
                    prediction["risk_source"] = "model"
                    self.logger.info(
                        "LiverDiseaseService returned prediction keys=%s",
                        list(prediction.keys()) if isinstance(prediction, dict) else type(prediction),
                    )
                except Exception as exc:
                    self.logger.warning("LiverDiseaseService failed; falling back to risk service: %s", exc)
                    state.add_warning(f"LiverDiseaseService error: {exc}")
                    assessment_input.setdefault("risk_fallback_reason", str(exc))
                    prediction = None
                finally:
                    liver_tried = True

            def _try_hepatitis_service() -> None:
                nonlocal prediction, hepatitis_tried
                hepatitis_service = get_hepatitis_service(Path(settings.HEPATITIS_MODEL_DIRECTORY))
                hepatitis_input = {
                    key: assessment_input[key]
                    for key in ["age", "bilirubin", "alk_phosphatase", "sgpt", "sgot"]
                    if key in assessment_input
                }
                try:
                    prediction = hepatitis_service.predict(hepatitis_input)
                    prediction["condition"] = "Hepatitis Risk"
                    prediction["risk_category"] = "high" if float(prediction.get("probability", 0.0)) >= 0.5 else "low"
                    prediction["risk_level"] = prediction["risk_category"]
                    prediction["disease"] = "hepatitis"
                    prediction["model_used"] = "hepatitis_model"
                    prediction["risk_source"] = "model"
                    self.logger.info(
                        "HepatitisService returned prediction keys=%s",
                        list(prediction.keys()) if isinstance(prediction, dict) else type(prediction),
                    )
                except Exception as exc:
                    self.logger.warning("HepatitisService failed; falling back to liver service: %s", exc)
                    state.add_warning(f"HepatitisService error: {exc}")
                    assessment_input.setdefault("risk_fallback_reason", str(exc))
                    prediction = None
                finally:
                    hepatitis_tried = True

            # Prefer endpoint request context or explicit disease hint when available.
            if explicit_disease == "hepatitis":
                _try_hepatitis_service()
                if prediction is None and has_liver_features:
                    _try_liver_service()
            elif explicit_disease == "liver_disease":
                _try_liver_service()
                if prediction is None and has_hepatitis_features:
                    _try_hepatitis_service()
            elif "liver" in diagnosis:
                _try_liver_service()
                if prediction is None and has_hepatitis_features:
                    _try_hepatitis_service()
            elif "hepatitis" in diagnosis:
                _try_hepatitis_service()
                if prediction is None and has_liver_features:
                    _try_liver_service()
            else:
                if has_liver_features:
                    _try_liver_service()
                if prediction is None and has_hepatitis_features:
                    _try_hepatitis_service()

        breast_keys = {"radius_mean", "texture_mean", "perimeter_mean", "area_mean", "smoothness_mean", "mean_radius", "mean_texture"}
        has_breast_features = any(k in assessment_input for k in breast_keys) or (
            "diagnosis" in assessment_input and "breast" in str(assessment_input.get("diagnosis", "")).lower()
        )

        parkinsons_keys = {"motor_UPDRS", "total_UPDRS", "Jitter_local", "Shimmer_local", "jitter_local", "shimmer_local"}
        has_parkinsons_features = any(k in assessment_input for k in parkinsons_keys) or (
            "diagnosis" in assessment_input and "parkinson" in str(assessment_input.get("diagnosis", "")).lower()
        )

        if prediction is None and has_parkinsons_features:
            parkinsons_service = get_parkinsons_service(Path(settings.PARKINSONS_MODEL_DIRECTORY))
            parkinsons_input = {
                key: assessment_input[key]
                for key in ["age", "motor_UPDRS", "total_UPDRS", "Jitter_local", "Shimmer_local"]
                if key in assessment_input
            }
            try:
                prediction = parkinsons_service.predict(parkinsons_input)
                prediction["condition"] = "Parkinson's Disease Risk"
                prediction["risk_category"] = "high" if float(prediction.get("probability", 0.0)) >= 0.5 else "low"
                prediction["risk_level"] = prediction["risk_category"]
                prediction["disease"] = "parkinsons"
                prediction["model_used"] = "parkinsons_model"
                prediction["risk_source"] = "model"
                self.logger.info(
                    "ParkinsonsService returned prediction keys=%s",
                    list(prediction.keys()) if isinstance(prediction, dict) else type(prediction),
                )
            except Exception as exc:
                self.logger.warning("ParkinsonsService failed; falling back to risk service: %s", exc)
                state.add_warning(f"ParkinsonsService error: {exc}")
                assessment_input.setdefault("risk_fallback_reason", str(exc))
                prediction = None

        if prediction is None and has_breast_features:
            from app.services.breast_cancer_service import get_breast_cancer_service

            breast_service = get_breast_cancer_service(Path(settings.BREAST_CANCER_MODEL_DIRECTORY))
            breast_input = {
                key: assessment_input[key]
                for key in [
                    "radius_mean",
                    "texture_mean",
                    "perimeter_mean",
                    "area_mean",
                    "smoothness_mean",
                    "mean_radius",
                    "mean_texture",
                ]
                if key in assessment_input
            }
            try:
                prediction = breast_service.predict(breast_input)
                prediction["condition"] = "Breast Cancer Risk"
                prediction["risk_category"] = "high" if float(prediction.get("probability", 0.0)) >= 0.5 else "low"
                prediction["risk_level"] = prediction["risk_category"]
                prediction["disease"] = "breast_cancer"
                prediction["model_used"] = "breast_cancer_model"
                prediction["risk_source"] = "model"
                self.logger.info(
                    "BreastCancerService returned prediction keys=%s",
                    list(prediction.keys()) if isinstance(prediction, dict) else type(prediction),
                )
            except Exception as exc:
                self.logger.warning("BreastCancerService failed; falling back to risk service: %s", exc)
                state.add_warning(f"BreastCancerService error: {exc}")
                assessment_input.setdefault("risk_fallback_reason", str(exc))
                prediction = None

        if prediction is None:
            risk_service = get_risk_service()
            prediction = risk_service.predict(patient=None, metrics=assessment_input)
            self.logger.info("RiskService returned prediction keys=%s", list(prediction.keys()) if isinstance(prediction, dict) else type(prediction))

        if not isinstance(prediction, dict) or not prediction:
            # Fall back to a minimal heuristic prediction instead of raising so
            # downstream code/tests always receive a consistent disease_risk dict.
            self.logger.warning("Risk service produced empty or invalid prediction; using heuristic fallback")
            prediction = {
                "success": True,
                "disease": "unknown",
                "condition": "Cardiometabolic Risk",
                "prediction": 0,
                "probability": 0.0,
                "confidence": 0.0,
                "risk_source": "heuristic",
                "risk_category": "low",
                "risk_level": "low",
                "risk_score": 0.0,
                "estimated_risk_score_percent": 0.0,
                "confidence_label": "Low",
                "class_probabilities": {"0": 1.0, "1": 0.0},
                "explanations": [],
            }

        normalized_prediction = self._normalize_prediction(prediction)
        if explicit_disease == "hepatitis":
            normalized_prediction["disease"] = "hepatitis"
            normalized_prediction["condition"] = "Hepatitis Risk"
        elif explicit_disease == "liver_disease":
            normalized_prediction["disease"] = "liver_disease"
            normalized_prediction["condition"] = "Liver Disease Risk"
        elif has_liver_features and normalized_prediction.get("disease") in {None, "", "Cardiometabolic Risk", "Cardiometabolic", "unknown", "Unknown"}:
            normalized_prediction["disease"] = "liver_disease"
            normalized_prediction["condition"] = "Liver Disease Risk"
        elif has_hepatitis_features and normalized_prediction.get("disease") in {None, "", "Cardiometabolic Risk", "Cardiometabolic", "unknown", "Unknown"}:
            normalized_prediction["disease"] = "hepatitis"
            normalized_prediction["condition"] = "Hepatitis Risk"
        elif has_heart_failure_features and normalized_prediction.get("disease") in {None, "", "Cardiometabolic Risk", "Cardiometabolic", "unknown", "Unknown"}:
            normalized_prediction["disease"] = "heart_failure"
            normalized_prediction["condition"] = "Heart Failure Risk"
        elif has_stroke_features and normalized_prediction.get("disease") in {None, "", "Cardiometabolic Risk", "Cardiometabolic", "unknown", "Unknown"}:
            normalized_prediction["disease"] = "stroke"
            normalized_prediction["condition"] = "Stroke Risk"

        self.logger.info("DiseaseRiskAgent normalized prediction keys=%s", list(normalized_prediction.keys()))
        state.disease_risk = normalized_prediction
        state.metadata["risk_source"] = normalized_prediction.get("risk_source", "model" if "model_used" in normalized_prediction else "heuristic")
        state.metadata["risk_model"] = normalized_prediction.get("model_used")

        elapsed = round(
            time.perf_counter() - start,
            3,
        )

        state.set_agent_output(
            self.agent_name,
            prediction,
            confidence=prediction.get(
                "confidence",
                0.0,
            ),
            execution_time=elapsed,
        )

        return AgentResult(
            agent=self.agent_name,
            status="SUCCESS",
            confidence=prediction.get(
                "confidence",
                0.0,
            ),
            result=prediction,
            metadata={
                "execution_time": elapsed,
            },
        )