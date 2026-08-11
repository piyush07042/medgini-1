"""
Report generation service: centralize final report composition.
"""
from __future__ import annotations

import copy
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.agents.base.agent_state import AgentState
from app.clinical_intelligence.engine import generate_clinical_intelligence
from app.models.models import AIReport

logger = logging.getLogger(__name__)


def build_final_report(state: AgentState) -> dict[str, Any]:
    metadata = copy.deepcopy(state.metadata)
    metadata.pop("last_agent_output", None)
    metadata.pop("agent_outputs", None)
    metadata.pop("last_agent_confidence", None)
    metadata.pop("last_agent_execution_time", None)

    recommendation_output = state.recommendations[0] if state.recommendations and isinstance(state.recommendations[0], dict) else {}

    generated_at = state.metadata.get("generated_at") or datetime.utcnow().isoformat()

    report = {
        "generated_at": generated_at,
        "patient": state.patient,
        "patient_summary": _build_patient_summary(
            state.patient,
            state.patient_history,
            state.symptoms,
            state.medications,
            state.allergies,
        ),
        "patient_history": state.patient_history,
        "symptoms": state.symptoms,
        "medications": state.medications,
        "allergies": state.allergies,
        "ocr_findings": _build_ocr_findings(state),
        "prediction": _build_prediction(state.disease_risk),
        "probability": _safe_float(state.disease_risk.get("probability") or state.disease_risk.get("risk_score") or state.disease_risk.get("confidence")),
        "confidence": _safe_float(state.disease_risk.get("confidence") or state.disease_risk.get("probability") or state.disease_risk.get("risk_score")),
        "explainability": _build_explainability(state.disease_risk),
        "retrieved_evidence": _build_retrieved_evidence(state.knowledge_results),
        "drug_safety": state.drug_analysis,
        "recommendations": _extract_recommendation_items(state.recommendations),
        "follow_up": _build_follow_up(recommendation_output),
        "clinical_summary": _build_clinical_summary(state),
        "warnings": state.warnings,
        "errors": state.errors,
        "execution_trace": state.execution_trace,
        "metadata": metadata,
    }

    # Attach Clinical Intelligence (guideline-derived summary) when possible
    # Prefer clinical_intelligence already present (from persisted summary) so PDF/UI use single source of truth
    clinical_intel = None
    if isinstance(state.metadata, dict) and state.metadata.get("clinical_intelligence"):
        clinical_intel = state.metadata.get("clinical_intelligence")
    elif isinstance(state.final_report, dict) and state.final_report.get("clinical_intelligence"):
        clinical_intel = state.final_report.get("clinical_intelligence")
    else:
        # try common locations for disease identifier
        disease_key = (
            state.metadata.get("disease")
            or state.disease_risk.get("disease")
            or state.disease_risk.get("label")
            or state.disease_risk.get("prediction")
            or recommendation_output.get("disease")
            or None
        )
        try:
            clinical_intel = generate_clinical_intelligence(str(disease_key) if disease_key else "", state.disease_risk or {}, state.patient or {})
        except Exception:
            clinical_intel = {}

    # ── Section 9: References ── built from RAG citations ────────────────
    references: list[dict[str, Any]] = []
    for kr in (state.knowledge_results or []):
        if not isinstance(kr, dict):
            continue
        meta = kr.get("metadata") or {}
        src = meta.get("source") or meta.get("title") or "Clinical guideline"
        doc_excerpt = str(kr.get("document", ""))[:200]
        if src or doc_excerpt:
            references.append({"source": src, "excerpt": doc_excerpt, "similarity_score": kr.get("similarity_score")})
    # Also pull guideline reference from CI
    ci_guideline = (clinical_intel or {}).get("Guideline") or (clinical_intel or {}).get("Guideline Source")
    if ci_guideline and not any(r.get("source") == ci_guideline for r in references):
        references.append({"source": ci_guideline, "excerpt": "Official clinical guideline referenced by Clinical Intelligence engine.", "similarity_score": None})

    report["references"] = references

    # ── Guarantee all 9 mandatory sections are present ───────────────────
    report.setdefault("patient_information", report.get("patient_summary") or {"name": "Unknown", "age": None, "gender": None})
    report.setdefault("prediction_results", report.get("prediction") or {})
    report.setdefault("clinical_intelligence", clinical_intel or {})
    report.setdefault("guideline_recommendations", (
        recommendation_output.get("guideline_actions") or []
        if isinstance(recommendation_output, dict) else []
    ))
    report.setdefault("drug_safety", state.drug_analysis or {})
    report.setdefault("risk_assessment", {
        "risk_category": state.disease_risk.get("risk_category") or state.disease_risk.get("risk_level") or "Unknown",
        "probability": state.disease_risk.get("probability") or state.disease_risk.get("risk_score"),
        "confidence_label": state.disease_risk.get("confidence_label"),
        "top_factors": state.disease_risk.get("top_factors") or state.disease_risk.get("drivers") or [],
    })
    report.setdefault("ai_summary", report.get("clinical_summary") or "")
    report.setdefault("follow_up_plan", report.get("follow_up") or [])
    report.setdefault("references", references)

    # ── Section manifest ─────────────────────────────────────────────────
    report["sections"] = [
        "patient_information", "prediction_results", "clinical_intelligence",
        "guideline_recommendations", "drug_safety", "risk_assessment",
        "ai_summary", "follow_up_plan", "references",
    ]

    report["structured_recommendation"] = recommendation_output
    report["recommendation_summary"] = recommendation_output.get("recommendation_summary") if isinstance(recommendation_output, dict) else None
    report["drug_safety_summary"] = recommendation_output.get("drug_safety_summary") if isinstance(recommendation_output, dict) else {}
    report["medical_evidence"] = recommendation_output.get("medical_evidence") if isinstance(recommendation_output, dict) else []
    report["supporting_evidence"] = recommendation_output.get("supporting_evidence") if isinstance(recommendation_output, dict) else []
    report["patient_specific_recommendations"] = recommendation_output.get("patient_specific_recommendations") if isinstance(recommendation_output, dict) else []
    report["confidence_label"] = state.disease_risk.get("confidence_label") or state.disease_risk.get("risk_level")
    report["recommendation_priority"] = recommendation_output.get("recommendation_priority") if isinstance(recommendation_output, dict) else None

    # ── Digital Signature ────────────────────────────────────────────────
    from app.services.report.digital_signature import generate_digital_signature
    report["digital_signature"] = generate_digital_signature(report)

    return report



def get_patient_id_from_context(patient: dict[str, Any] | None) -> int | None:
    if not patient:
        return None

    patient_id = patient.get("patient_id") or patient.get("id")
    if patient_id is None:
        return None

    try:
        return int(patient_id)
    except (TypeError, ValueError):
        return None


def save_ai_report(db: Session, patient_id: int, final_state: AgentState) -> AIReport:
    logger.info("Saving report... Patient ID=%s", patient_id)

    # Build the final report dict to capture any computed fields (but prefer stored clinical_intelligence when present)
    try:
        final_report_dict = build_final_report(final_state)
    except Exception:
        final_report_dict = {}

    clinical_intel = None
    # Prefer any clinical_intelligence already present on the AgentState metadata/final_report
    if isinstance(final_state.metadata, dict) and final_state.metadata.get("clinical_intelligence"):
        clinical_intel = final_state.metadata.get("clinical_intelligence")
    elif isinstance(final_state.final_report, dict) and final_state.final_report.get("clinical_intelligence"):
        clinical_intel = final_state.final_report.get("clinical_intelligence")
    else:
        clinical_intel = final_report_dict.get("clinical_intelligence")

    report_payload = AIReport(
        patient_id=patient_id,
        risk_assessment=final_state.disease_risk or {},
        rag_evidence=final_state.knowledge_results or [],
        drug_safety_alerts=final_state.drug_analysis or {},
        clinical_summary=(final_report_dict or {}).get("clinical_summary", "") or "",
        clinical_intelligence=clinical_intel,
    )

    db.add(report_payload)
    db.commit()
    db.refresh(report_payload)

    logger.info(
        "Report saved successfully. Patient ID=%s Report ID=%s Commit successful",
        report_payload.patient_id,
        report_payload.id,
    )

    return report_payload


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_patient_summary(
    patient: dict[str, Any],
    patient_history: dict[str, Any],
    symptoms: list[str],
    medications: list[str],
    allergies: list[str],
) -> dict[str, Any]:
    name = patient.get("name") or f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or "Patient"
    age = patient.get("age")
    gender = patient.get("gender")
    summary_text = [f"{name}"]
    if age is not None:
        summary_text.append(f"Age {age}")
    if gender:
        summary_text.append(f"Gender {gender}")

    if symptoms:
        summary_text.append("presenting symptoms include " + ", ".join(symptoms))
    if medications:
        summary_text.append("current medications include " + ", ".join(medications))
    if allergies:
        summary_text.append("documented allergies include " + ", ".join(allergies))

    return {
        "name": name,
        "age": age,
        "gender": gender,
        "summary_text": ". ".join(summary_text) + "." if summary_text else "Patient information not available.",
        "history": patient_history,
        "symptoms": symptoms,
        "medications": medications,
        "allergies": allergies,
    }


def _build_ocr_findings(state: AgentState) -> dict[str, Any]:
    return {
        "raw_report_text": state.report_text or "",
        "ocr_result": state.ocr_result,
        "extracted_metrics": state.extracted_metrics,
    }


def _build_prediction(disease_risk: dict[str, Any]) -> dict[str, Any]:
    if not disease_risk:
        return {
            "risk_category": "Pending ML Evaluation",
            "risk_score": 0.0,
            "probability": None,
            "confidence": None,
            "confidence_label": "Baseline Intake",
            "prediction": "Pending ML Screening",
            "class_probabilities": {"0": 1.0, "1": 0.0},
        }

    risk_cat = disease_risk.get("risk_category") or disease_risk.get("risk_level") or "Low"
    if str(risk_cat).lower() in ("unknown", "n/a", "none"):
        risk_cat = "Low"

    return {
        "risk_category": risk_cat,
        "risk_score": _safe_float(disease_risk.get("risk_score") or disease_risk.get("estimated_risk_score_percent") or disease_risk.get("probability") or disease_risk.get("confidence")),
        "probability": _safe_float(disease_risk.get("probability") or disease_risk.get("risk_score") or disease_risk.get("confidence")),
        "confidence": _safe_float(disease_risk.get("confidence") or disease_risk.get("probability") or disease_risk.get("risk_score")),
        "confidence_label": disease_risk.get("confidence_label") or disease_risk.get("risk_level") or risk_cat,
        "prediction": disease_risk.get("prediction") if disease_risk.get("prediction") is not None else (1 if _safe_float(disease_risk.get("probability", disease_risk.get("risk_score", 0.0))) >= 0.5 else 0),
        "class_probabilities": disease_risk.get("class_probabilities") or {
            "0": round(max(0.0, 1.0 - _safe_float(disease_risk.get("probability", disease_risk.get("risk_score", 0.0)))), 3),
            "1": round(min(1.0, _safe_float(disease_risk.get("probability", disease_risk.get("risk_score", 0.0)))), 3),
        },
    }


def _build_explainability(disease_risk: dict[str, Any]) -> dict[str, Any]:
    top_factors = disease_risk.get("top_factors") or disease_risk.get("drivers") or []
    explanations = disease_risk.get("explanations") or disease_risk.get("drivers") or disease_risk.get("top_factors") or []
    if isinstance(explanations, dict):
        explanations = [explanations]

    if not top_factors and isinstance(explanations, list):
        computed_factors: list[str] = []
        for entry in explanations:
            if isinstance(entry, dict):
                feature = entry.get("feature") or entry.get("label") or entry.get("name")
                value = entry.get("value") or entry.get("description")
                if feature and value is not None:
                    computed_factors.append(f"{feature}: {value}")
                elif feature:
                    computed_factors.append(str(feature))
                elif value is not None:
                    computed_factors.append(str(value))
                else:
                    computed_factors.append(str(entry))
            else:
                computed_factors.append(str(entry))
        top_factors = computed_factors

    return {
        "top_factors": top_factors,
        "explanations": explanations,
        "notes": disease_risk.get("explainability") or disease_risk.get("explanations") or [],
    }


def _build_retrieved_evidence(knowledge_results: list[dict[str, Any]] | None) -> dict[str, Any]:
    knowledge_results = knowledge_results or []
    evidence_summary = "".join(
        f"{item.get('source', 'Source')}: {item.get('text', '')}. "
        for item in knowledge_results
        if item
    )
    return {
        "knowledge_results": knowledge_results,
        "evidence_summary": evidence_summary.strip(),
    }


def _build_follow_up(recommendation_output: dict[str, Any]) -> list[Any]:
    follow_up = []
    if isinstance(recommendation_output, dict):
        follow_up = recommendation_output.get("follow_up_plan") or recommendation_output.get("follow_up") or []
    return follow_up if isinstance(follow_up, list) else [follow_up]


def _build_clinical_summary(state: AgentState) -> str:
    patient = state.patient or {}
    patient_name = patient.get("name") or f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip() or "Patient"
    age = patient.get("age")
    gender = patient.get("gender")
    lines: list[str] = [f"Clinical Summary for {patient_name}."]

    if age is not None:
        lines.append(f"Age: {age}.")
    if gender:
        lines.append(f"Gender: {gender}.")

    prediction = state.disease_risk or {}
    if prediction:
        category = prediction.get("risk_category") or prediction.get("risk_level") or "Unknown"
        probability = prediction.get("probability") or prediction.get("risk_score") or prediction.get("confidence")
        lines.append(f"Predicted risk category: {category}.")
        if probability is not None:
            lines.append(f"ML predicted probability: {round(_safe_float(probability) * 100, 1)}%.")

        if prediction.get("explanations"):
            lines.append("Key explainability factors:")
            for entry in prediction.get("explanations"):
                if isinstance(entry, dict):
                    feat = entry.get('feature') or entry.get('label') or 'Factor'
                    val = entry.get('importance') if entry.get('importance') is not None else entry.get('value', entry.get('description', ''))
                    lines.append(f"- {feat}: {val}" if val != '' else f"- {feat}")
                elif isinstance(entry, str):
                    lines.append(f"- {entry}")

    if state.ocr_result or state.report_text:
        lines.append("OCR findings and extracted report information were reviewed.")

    if state.knowledge_results:
        lines.append("Retrieved evidence from clinical knowledge sources was incorporated into the recommendation plan.")

    if state.drug_analysis:
        status = state.drug_analysis.get("status", "PASS")
        lines.append(f"Drug safety review status: {status}.")

    return "\n".join(lines)


def _extract_recommendation_items(recs: list[Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for r in recs or []:
        if isinstance(r, dict):
            if "recommendations" in r and isinstance(r["recommendations"], list):
                items.extend(_extract_recommendation_items(r["recommendations"]))
            elif "title" in r or "recommendation" in r or "summary" in r or "action" in r:
                title = r.get("title") or r.get("category") or r.get("priority") or "Recommendation"
                text = r.get("recommendation") or r.get("summary") or r.get("action") or ""
                if text:
                    items.append({"title": title, "recommendation": text, "category": r.get("category", "General"), "priority": r.get("priority", "Medium")})
        elif isinstance(r, str) and r.strip():
            items.append({"title": "Recommendation", "recommendation": r.strip(), "category": "General", "priority": "Medium"})
    return items


def build_report_from_storage(
    patient: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    """Build a standardized report object from persisted patient and AI report data."""
    patient = patient or {}
    summary = summary or {}

    state = AgentState()
    state.patient = patient
    state.patient_history = summary.get("medical_history") or patient.get("medical_history") or {}
    state.symptoms = summary.get("symptoms") or []
    state.medications = summary.get("medications") or patient.get("current_medications") or []
    state.allergies = summary.get("allergies") or patient.get("allergies") or []
    state.report_text = summary.get("report_text") or summary.get("clinical_summary") or ""
    state.ocr_result = summary.get("ocr_result") or {}
    state.extracted_metrics = summary.get("extracted_metrics") or {}
    state.disease_risk = summary.get("risk_assessment") or summary.get("disease_risk") or {}
    state.knowledge_results = summary.get("rag_evidence") or summary.get("knowledge_results") or []
    state.drug_analysis = summary.get("drug_safety_alerts") or summary.get("drug_analysis") or {}
    state.recommendations = summary.get("recommendations") or []
    state.warnings = summary.get("warnings") or []
    state.errors = summary.get("errors") or []
    state.metadata = summary.get("metadata") or {}

    # ── Inject the persisted AIReport database ID so the PDF can display it ──
    report_id = summary.get("id")
    if report_id is not None:
        state.metadata["report_id"] = str(report_id)

    # If the persisted AIReport includes a clinical_intelligence section, preserve it
    if isinstance(summary, dict) and summary.get("clinical_intelligence"):
        state.metadata["clinical_intelligence"] = summary.get("clinical_intelligence")

    if generated_at:
        state.metadata["generated_at"] = generated_at
    else:
        created_at = (
            summary.get("created_at")
            if isinstance(summary, dict)
            else getattr(summary, "created_at", None)
        )
        if created_at is not None:
            if hasattr(created_at, "isoformat"):
                state.metadata["generated_at"] = created_at.isoformat()
            else:
                state.metadata["generated_at"] = str(created_at)

    # ── Reconstruct recommendations when they were not persisted in the summary ──
    if not state.recommendations and state.disease_risk:
        try:
            from app.services.recommendation.recommendation_service import generate_recommendations as _gen_recs
            state.recommendations = _gen_recs(state)
        except Exception:
            state.recommendations = []

    return build_final_report(state)
