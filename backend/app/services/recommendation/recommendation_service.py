"""
Recommendation service: centralize recommendation generation logic
so agents can call a single API.
"""
from __future__ import annotations

from typing import Any

from app.agents.base.agent_state import AgentState
from app.core.config import settings
from app.services.recommendation.knowledge_evidence import (
    build_citations_from_knowledge,
    summarize_evidence,
)
from app.clinical_intelligence.engine import generate_clinical_intelligence


def _normalize_probability(value: Any) -> float:
    if value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _estimate_confidence_label(probability: float) -> str:
    if probability >= settings.HEART_CONFIDENCE_HIGH:
        return "High"
    if probability >= settings.HEART_CONFIDENCE_MEDIUM:
        return "Medium"
    return "Low"


def _build_evidence_payload(knowledge_results: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for entry in knowledge_results or []:
        if not isinstance(entry, dict):
            continue

        document = str(entry.get("document") or entry.get("text") or "").strip()
        metadata = entry.get("metadata") or {}
        source = metadata.get("source") or metadata.get("title") or "Clinical guideline"
        if not document:
            continue

        evidence.append({
            "source": source,
            "excerpt": document[:300],
            "relevance": float(entry.get("similarity_score") or 0.0),
        })

    return evidence


def _build_similarity_scores(knowledge_results: list[dict[str, Any]] | None) -> list[float]:
    scores: list[float] = []
    for entry in knowledge_results or []:
        if not isinstance(entry, dict):
            continue
        score = entry.get("similarity_score")
        if isinstance(score, (int, float)):
            scores.append(float(score))
    return scores


def _build_supporting_factors(
    disease_risk: dict[str, Any],
    knowledge_results: list[dict[str, Any]] | None,
    drug_analysis: dict[str, Any],
    patient: dict[str, Any],
    extracted_metrics: dict[str, Any],
) -> list[str]:
    factors: list[str] = []

    if patient.get("age") is not None:
        factors.append(f"Age {patient['age']}")
    if patient.get("gender"):
        factors.append(f"Gender {str(patient['gender']).title()}")
    if patient.get("smoking"):
        factors.append("Smoking history")
    if patient.get("bmi") is not None:
        factors.append(f"BMI {patient['bmi']}")
    if patient.get("cholesterol") is not None:
        factors.append(f"Cholesterol {patient['cholesterol']}")
    if patient.get("glucose") is not None:
        factors.append(f"Glucose {patient['glucose']}")

    probability = _normalize_probability(
        disease_risk.get("probability")
        or disease_risk.get("confidence")
        or disease_risk.get("risk_score")
    )
    if probability > 0:
        factors.append(f"Predicted risk probability {round(probability * 100, 1)}%")

    drivers = disease_risk.get("top_factors") or disease_risk.get("drivers") or []
    if isinstance(drivers, dict):
        drivers = [drivers]
    for driver in drivers[:4]:
        if isinstance(driver, dict):
            feature = driver.get("feature") or driver.get("name")
            importance = driver.get("importance")
            if feature:
                factors.append(f"{feature} importance {importance if importance is not None else 'unknown'}")
        else:
            factors.append(str(driver))

    for item in (drug_analysis.get("interactions") or []):
        if item.get("severity"):
            factors.append(f"Interaction {item.get('severity')}")
    for item in (drug_analysis.get("allergies") or []):
        if item.get("severity"):
            factors.append(f"Allergy {item.get('severity')}")
    if drug_analysis.get("status") == "FLAGGED":
        factors.append("Drug safety flagged")

    evidence_sources = {
        str(entry.get("metadata", {}).get("source") or entry.get("metadata", {}).get("title"))
        for entry in knowledge_results or []
        if isinstance(entry, dict) and entry.get("metadata")
    }
    for source in sorted(evidence_sources):
        if source:
            factors.append(f"Evidence source {source}")

    metric_keys = ["systolic_bp", "diastolic_bp", "heart_rate", "bmi", "glucose", "cholesterol"]
    for key in metric_keys:
        if extracted_metrics.get(key) is not None and f"{key}" not in factors:
            factors.append(f"{key.replace('_', ' ').title()} {extracted_metrics[key]}")

    return factors[:12] or ["No supporting factors available."]


def _build_drug_safety_payload(drug_analysis: dict[str, Any]) -> dict[str, Any]:
    interactions = [
        {
            "drugs_involved": item.get("drugs_involved", []),
            "severity": item.get("severity"),
            "explanation": item.get("explanation"),
            "recommendation": item.get("recommendation"),
        }
        for item in (drug_analysis.get("interactions") or [])
        if isinstance(item, dict)
    ]
    contraindications = [
        {
            "medication": item.get("medication"),
            "condition": item.get("condition"),
            "severity": item.get("severity"),
            "explanation": item.get("explanation"),
            "recommendation": item.get("recommendation"),
        }
        for item in (drug_analysis.get("contraindications") or [])
        if isinstance(item, dict)
    ]
    allergies = [
        {
            "medication": item.get("medication"),
            "allergy_type": item.get("allergy_type"),
            "severity": item.get("severity"),
            "explanation": item.get("explanation"),
            "recommendation": item.get("recommendation"),
        }
        for item in (drug_analysis.get("allergies") or [])
        if isinstance(item, dict)
    ]

    warnings: list[str] = []
    if drug_analysis.get("status") == "FLAGGED":
        warnings.append("Medication safety review flagged one or more concerns.")
    if interactions:
        warnings.extend(
            f"Interaction {item['severity']} between {', '.join(item['drugs_involved'])}."
            for item in interactions
            if item.get("severity") and item.get("drugs_involved")
        )
    if contraindications:
        warnings.extend(
            f"Contraindication: {item['medication']} for {item['condition']}."
            for item in contraindications
            if item.get("medication") and item.get("condition")
        )
    if allergies:
        warnings.extend(
            f"Allergy concern: {item['medication']} ({item['allergy_type']})."
            for item in allergies
            if item.get("medication") and item.get("allergy_type")
        )

    renal_adjustment = drug_analysis.get("renal_adjustment") or {}
    liver_adjustment = drug_analysis.get("liver_adjustment") or {}
    pregnancy = drug_analysis.get("pregnancy") or {}

    return {
        "risk_level": drug_analysis.get("overall_risk") or "Low",
        "warnings": warnings,
        "contraindications": contraindications,
        "interactions": interactions,
        "renal_adjustment": {
            "summary": ", ".join(
                rec.get("recommendation")
                for rec in (renal_adjustment.get("recommendations") or [])
                if isinstance(rec, dict) and rec.get("recommendation")
            )
            or renal_adjustment.get("monitoring_advice")
            or "No renal adjustment recommendations.",
            "egfr": renal_adjustment.get("egfr"),
            "ckd_stage": renal_adjustment.get("ckd_stage"),
        },
        "liver_adjustment": {
            "summary": ", ".join(
                rec.get("recommendation")
                for rec in (liver_adjustment.get("recommendations") or [])
                if isinstance(rec, dict) and rec.get("recommendation")
            )
            or liver_adjustment.get("monitoring_advice")
            or "No liver adjustment recommendations.",
            "alt": liver_adjustment.get("alt"),
            "ast": liver_adjustment.get("ast"),
            "bilirubin": liver_adjustment.get("bilirubin"),
        },
        "pregnancy": {
            "category": pregnancy.get("category") or "Not Applicable",
            "explanation": pregnancy.get("explanation") or "Pregnancy safety evaluation not indicated.",
        },
    }


def _determine_recommendation_priority(
    risk_summary: dict[str, Any],
    drug_safety_payload: dict[str, Any],
) -> str:
    probability = risk_summary.get("probability", 0.0)
    confidence = str(risk_summary.get("confidence") or "").title()
    drug_risk = str(drug_safety_payload.get("risk_level") or "").title()

    if confidence == "High" or probability >= 0.8 or drug_risk == "High":
        return "High"
    if confidence == "Medium" or probability >= 0.65 or drug_risk == "Medium":
        return "Medium"
    return "Low"


def _build_patient_specific_recommendations(
    risk_summary: dict[str, Any],
    medical_evidence: list[dict[str, Any]],
    drug_safety_payload: dict[str, Any],
    patient: dict[str, Any],
    extracted_metrics: dict[str, Any],
) -> list[str]:
    recommendations: list[str] = []
    probability = risk_summary.get("probability", 0.0)
    confidence = risk_summary.get("confidence", "Unknown")
    prediction = risk_summary.get("prediction", "heart disease")

    if probability >= 0.8 or confidence == "High":
        recommendations.append(
            f"High-risk cardiovascular management is indicated for {prediction} with an estimated probability of {round(probability * 100, 1)}%."
        )
    elif probability >= 0.65 or confidence == "Medium":
        recommendations.append(
            f"Moderate risk of {prediction} is present; optimize lifestyle, metabolic health, and monitoring."
        )
    else:
        recommendations.append(
            f"Low predicted risk for {prediction}; maintain preventive care and routine surveillance."
        )

    if medical_evidence:
        recommendations.append(
            "Incorporate the retrieved clinical evidence into treatment planning and monitoring."
        )

    if drug_safety_payload.get("warnings"):
        recommendations.append(
            "Review medications for safety issues and adjust therapy based on identified warnings."
        )
    else:
        recommendations.append(
            "Continue current medication therapy with periodic safety monitoring."
        )

    if patient.get("smoking"):
        recommendations.append("Provide smoking cessation counseling and support.")

    if patient.get("bmi") is not None and float(patient.get("bmi", 0)) >= 30:
        recommendations.append("Initiate weight management and nutrition counseling.")

    if extracted_metrics.get("glucose") is not None and float(extracted_metrics.get("glucose", 0)) >= 126:
        recommendations.append("Coordinate glycemic control with cardiovascular risk management.")

    if not recommendations:
        recommendations.append(
            "Maintain evidence-based preventive care and reassess risk periodically."
        )

    return recommendations[:6]


def _build_recommendation_objects(
    risk_summary: dict[str, Any],
    medical_evidence: list[dict[str, Any]],
    drug_safety_payload: dict[str, Any],
    patient: dict[str, Any],
    extracted_metrics: dict[str, Any],
    recommendation_priority: str,
) -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    probability = risk_summary.get("probability", 0.0)
    confidence = risk_summary.get("confidence", "Unknown")
    prediction = risk_summary.get("prediction", "heart disease")

    objects.append({
        "title": "Risk Assessment",
        "recommendation": (
            f"The model indicates a {confidence.lower()} confidence prediction of {prediction} "
            f"({round(probability * 100, 1)}%). Prioritize clinical evaluation accordingly."
        ),
        "priority": recommendation_priority,
        "category": "Risk",
    })

    if medical_evidence:
        sources = sorted({item.get("source") for item in medical_evidence if item.get("source")})
        evidence_text = (
            f"Align management with evidence from {', '.join(sources)}."
        )
    else:
        evidence_text = (
            "No evidence sources were retrieved; rely on best-practice guidelines and consider additional knowledge retrieval."
        )

    objects.append({
        "title": "Evidence Alignment",
        "recommendation": evidence_text,
        "priority": recommendation_priority,
        "category": "Evidence",
    })

    if drug_safety_payload.get("warnings"):
        drug_text = (
            f"Address medication safety concerns: {drug_safety_payload['warnings'][0]}"
            f"{' Additional concerns should be reviewed.' if len(drug_safety_payload['warnings']) > 1 else ''}"
        )
    else:
        drug_text = (
            "Medication review did not identify major safety issues; continue monitoring organ and metabolic function."
        )

    objects.append({
        "title": "Medication Safety",
        "recommendation": drug_text,
        "priority": recommendation_priority,
        "category": "Medication",
    })

    if patient.get("smoking"):
        objects.append({
            "title": "Smoking Cessation",
            "recommendation": "Provide smoking cessation support and counseling.",
            "priority": recommendation_priority,
            "category": "Lifestyle",
        })

    if patient.get("bmi") is not None and float(patient.get("bmi", 0)) >= 30:
        objects.append({
            "title": "Weight Management",
            "recommendation": "Recommend weight management and dietary modification to improve cardiovascular risk.",
            "priority": recommendation_priority,
            "category": "Lifestyle",
        })

    if extracted_metrics.get("glucose") is not None and float(extracted_metrics.get("glucose", 0)) >= 126:
        objects.append({
            "title": "Glycemic Control",
            "recommendation": "Monitor glycemic control and coordinate with diabetes management.",
            "priority": recommendation_priority,
            "category": "Metabolic",
        })

    if risk_summary.get("prediction") and str(risk_summary.get("prediction", "")).lower() == "diabetes":
        objects.extend([
            {
                "title": "Lifestyle",
                "recommendation": "Adopt a balanced meal plan, reduce sugary beverages, and maintain regular sleep and stress management habits.",
                "priority": recommendation_priority,
                "category": "Lifestyle",
            },
            {
                "title": "Exercise",
                "recommendation": "Aim for at least 150 minutes of moderate-intensity activity per week and include strength training twice weekly.",
                "priority": recommendation_priority,
                "category": "Exercise",
            },
            {
                "title": "Monitoring",
                "recommendation": "Track fasting glucose, HbA1c, blood pressure, and weight trends at regular intervals with your clinician.",
                "priority": recommendation_priority,
                "category": "Monitoring",
            },
            {
                "title": "Follow-up",
                "recommendation": "Schedule a follow-up visit within 3 months to review glucose trends, medication adherence, and complications screening.",
                "priority": recommendation_priority,
                "category": "Follow-up",
            },
        ])

    if not objects:
        objects.append({
            "title": "General Recommendation",
            "recommendation": "Continue preventive care and monitor clinical markers regularly.",
            "priority": recommendation_priority,
            "category": "General",
        })

    return objects[:6]


def _build_recommendations(
    risk_summary: dict[str, Any],
    medical_evidence: list[dict[str, Any]],
    drug_safety_payload: dict[str, Any],
    patient: dict[str, Any],
    extracted_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    recommendation_priority = _determine_recommendation_priority(risk_summary, drug_safety_payload)
    return _build_recommendation_objects(
        risk_summary,
        medical_evidence,
        drug_safety_payload,
        patient,
        extracted_metrics,
        recommendation_priority,
    )


def _build_follow_up(
    risk_summary: dict[str, Any],
    drug_safety_payload: dict[str, Any],
    patient: dict[str, Any],
) -> list[str]:
    follow_up: list[str] = []
    if risk_summary.get("confidence") == "High" or risk_summary.get("probability", 0.0) >= 0.8:
        follow_up.append("Refer to cardiology within 4 weeks.")
    else:
        follow_up.append("Reassess cardiovascular risk in 3 months.")

    if drug_safety_payload.get("warnings"):
        follow_up.append("Review medication regimen and laboratory monitoring for drug safety concerns.")

    if patient.get("smoking"):
        follow_up.append("Arrange smoking cessation support.")
    if patient.get("bmi") is not None and float(patient.get("bmi", 0)) >= 30:
        follow_up.append("Plan dietary and exercise counseling for weight management.")

    follow_up.append("Repeat lipid profile, renal function, and liver function tests as clinically indicated.")
    return follow_up[:5]


def _build_clinical_summary(
    patient: dict[str, Any],
    risk_summary: dict[str, Any],
    knowledge_results: list[dict[str, Any]] | None,
    drug_safety_payload: dict[str, Any],
    recommendations: list[dict[str, Any]] | list[str],
) -> str:
    lines: list[str] = []
    name = (
        patient.get("name")
        or patient.get("first_name")
        or patient.get("patient_name")
        or "Patient"
    )
    age = patient.get("age")
    gender = patient.get("gender")
    lines.append(f"Clinical synthesis for {name}.")
    if age is not None:
        lines.append(f"Age {age}.")
    if gender:
        lines.append(f"Gender {str(gender).title()}.")

    risk_sentence = (
        f"The heart disease model estimates {risk_summary.get('probability', 0.0) * 100:.1f}% probability "
        f"of {risk_summary.get('prediction', 'heart disease')} with {risk_summary.get('confidence', 'Unknown')} confidence."
    )
    lines.append(risk_sentence)

    if knowledge_results:
        sources = {
            str(entry.get("metadata", {}).get("source") or entry.get("metadata", {}).get("title"))
            for entry in knowledge_results
            if isinstance(entry, dict)
        }
        if sources:
            lines.append(
                f"Retrieved guideline evidence from {', '.join(sorted(source for source in sources if source))}."
            )
    else:
        lines.append(
            "No medical knowledge evidence was available for this patient query."
        )

    if drug_safety_payload.get("warnings"):
        lines.append(
            f"Drug safety review raised concerns: {drug_safety_payload['warnings'][0]}"
        )
    else:
        lines.append(
            "Medication safety review did not identify major contraindications or interactions."
        )

    if recommendations:
        recommendation_text = None
        first_recommendation = recommendations[0]
        if isinstance(first_recommendation, dict):
            recommendation_text = first_recommendation.get("recommendation") or first_recommendation.get("summary")
        elif isinstance(first_recommendation, str):
            recommendation_text = first_recommendation

        if recommendation_text and isinstance(recommendation_text, str):
            lines.append("Key synthesized recommendation summary:")
            lines.append(recommendation_text)

    return " ".join(lines)


def generate_recommendation(state: AgentState) -> dict[str, Any]:
    patient = state.patient or {}
    disease_risk = state.disease_risk or {}
    knowledge_results = state.knowledge_results or []
    drug_analysis = state.drug_analysis or {}
    extracted_metrics = state.extracted_metrics or {}

    # ── Pull Clinical Intelligence (Phase B) ──────────────────────────
    clinical_intelligence: dict[str, Any] = {}
    if isinstance(state.metadata, dict) and state.metadata.get("clinical_intelligence"):
        clinical_intelligence = state.metadata["clinical_intelligence"]
    elif isinstance(state.final_report, dict) and state.final_report.get("clinical_intelligence"):
        clinical_intelligence = state.final_report["clinical_intelligence"]
    else:
        disease_key = (
            disease_risk.get("disease")
            or disease_risk.get("condition")
            or disease_risk.get("label")
            or disease_risk.get("prediction")
            or disease_risk.get("risk_category")
        )
        if disease_key:
            try:
                clinical_intelligence = generate_clinical_intelligence(
                    str(disease_key), disease_risk, patient
                )
            except Exception:
                clinical_intelligence = {}

    # ── Lab values from extracted metrics ────────────────────────────
    lab_values: dict[str, Any] = {}
    for lab_key in (
        "glucose", "systolic_bp", "diastolic_bp", "heart_rate", "bmi",
        "cholesterol", "hemoglobin", "creatinine", "alt", "ast",
        "hba1c", "tsh", "potassium", "sodium",
    ):
        val = extracted_metrics.get(lab_key)
        if val is not None:
            lab_values[lab_key] = val

    risk_summary = {
        "prediction": str(
            disease_risk.get("risk_category")
            or disease_risk.get("disease")
            or disease_risk.get("condition")
            or disease_risk.get("evaluated_condition")
            or "heart disease"
        ).title(),
        "probability": round(
            _normalize_probability(
                disease_risk.get("probability")
                or disease_risk.get("confidence")
                or disease_risk.get("risk_score")
            ),
            3,
        ),
        "confidence": disease_risk.get("confidence_label")
        or disease_risk.get("risk_level")
        or _estimate_confidence_label(
            _normalize_probability(
                disease_risk.get("probability")
                or disease_risk.get("confidence")
                or disease_risk.get("risk_score")
            )
        ),
    }

    medical_evidence = _build_evidence_payload(knowledge_results)
    drug_safety_payload = _build_drug_safety_payload(drug_analysis)
    supporting_factors = _build_supporting_factors(
        disease_risk,
        knowledge_results,
        drug_analysis,
        patient,
        extracted_metrics,
    )
    recommendations = _build_recommendations(
        risk_summary,
        medical_evidence,
        drug_safety_payload,
        patient,
        extracted_metrics,
    )

    # ── Inject CI-derived guideline actions as additional recommendations ──
    guideline_actions: list[str] = []
    guideline_ref: str = ""
    if clinical_intelligence:
        guideline_ref = clinical_intelligence.get("Guideline", "")
        for key in ("Recommended Next Steps", "Recommended Actions", "Treatment Recommendations"):
            if isinstance(clinical_intelligence.get(key), list):
                guideline_actions = clinical_intelligence[key]
                break
        # Add a CI recommendation entry
        if guideline_ref or guideline_actions:
            priority = _determine_recommendation_priority(risk_summary, drug_safety_payload)
            recommendations.append({
                "title": "Clinical Intelligence – Guideline Recommendations",
                "recommendation": (
                    f"Per {guideline_ref}: " if guideline_ref else ""
                ) + (guideline_actions[0] if guideline_actions else "Follow disease-specific clinical guidelines."),
                "priority": priority,
                "category": "Clinical Intelligence",
                "guideline": guideline_ref,
                "guideline_actions": guideline_actions[:4],
            })

    follow_up = _build_follow_up(risk_summary, drug_safety_payload, patient)

    # ── Augment follow-up with CI monitoring schedule ─────────────────
    if clinical_intelligence:
        monitoring = clinical_intelligence.get("Monitoring Schedule", "")
        if monitoring and str(monitoring) not in follow_up:
            follow_up.append(str(monitoring))
        emergency = clinical_intelligence.get("Emergency Warning Signs", [])
        if isinstance(emergency, list) and emergency:
            follow_up.append("Watch for: " + "; ".join(str(e) for e in emergency[:3]))

    clinical_summary = _build_clinical_summary(
        patient,
        risk_summary,
        knowledge_results,
        drug_safety_payload,
        recommendations,
    )

    return {
        "clinical_summary": clinical_summary,
        "risk_summary": risk_summary,
        "supporting_factors": supporting_factors,
        "medical_evidence": medical_evidence,
        "evidence": medical_evidence,
        "citations": build_citations_from_knowledge(knowledge_results),
        "similarity_scores": [
            float(score)
            for score in (_build_similarity_scores(knowledge_results) or [])
        ],
        "drug_safety": drug_safety_payload,
        "recommendations": recommendations,
        "follow_up": follow_up,
        "evidence_summary": summarize_evidence(knowledge_results),
        "clinical_intelligence": clinical_intelligence,
        "lab_values": lab_values,
        "guideline_reference": guideline_ref,
        "guideline_actions": guideline_actions,
    }


def generate_recommendations(state: AgentState) -> list[dict[str, Any]]:
    return [generate_recommendation(state)]
