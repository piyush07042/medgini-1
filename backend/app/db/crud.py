from sqlalchemy.orm import Session
import models


def create_patient_and_summary(
    db: Session, 
    patient_data: dict, 
    cdss_output: dict, 
    disease_risk: dict = None
):
    """Saves patient metrics and generated CDSS summary to SQLite."""
    # 1. Create Patient Record
    db_patient = models.PatientRecord(
        patient_id=patient_data.get("patient_id", "PT-DEMO-9941"),
        age=patient_data.get("age"),
        gender=patient_data.get("gender"),
        glucose=patient_data.get("glucose"),
        bmi=patient_data.get("bmi"),
        systolic_bp=patient_data.get("systolic_bp"),
        cholesterol=patient_data.get("cholesterol")
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    # Extract risk metadata if available
    risk_assessment = disease_risk.get("disease_risk_assessment", {}) if disease_risk else {}
    score = risk_assessment.get("estimated_risk_score_percent")
    category = risk_assessment.get("risk_category")

    # 2. Create Clinical Summary Record
    cdss_data = cdss_output.get("cdss_agent_output", {})
    db_summary = models.ClinicalSummary(
        patient_record_id=db_patient.id,
        status=cdss_data.get("status", "unknown"),
        risk_score=score,
        risk_category=category,
        summary_text=cdss_data.get("summary", ""),
        raw_payload=patient_data
    )
    db.add(db_summary)
    db.commit()
    db.refresh(db_summary)

    return db_patient, db_summary


def get_all_patients(db: Session, limit: int = 20):
    """Retrieve recent patient records with summaries."""
    return db.query(models.PatientRecord).order_by(models.PatientRecord.id.desc()).limit(limit).all()