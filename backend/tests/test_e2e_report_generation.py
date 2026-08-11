import os
import uuid

from app.models.models import User, Patient, AIReport
from tests.conftest import TestingSessionLocal


def test_end_to_end_report_generation(tmp_path):
    # Use the testing DB session from conftest
    db = TestingSessionLocal()
    try:
        # Create a doctor user with a unique email
        email = f"test_doctor_{uuid.uuid4().hex[:6]}@example.com"
        user = User(email=email, hashed_password="x", full_name="Dr Test")
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create a patient
        patient = Patient(doctor_id=user.id, first_name="John", last_name="Doe", age=50, gender="M")
        db.add(patient)
        db.commit()
        db.refresh(patient)

        # Create an AIReport for the patient
        ai = AIReport(patient_id=patient.id, risk_assessment={}, rag_evidence={}, drug_safety_alerts={}, clinical_summary="All good")
        db.add(ai)
        db.commit()

        # Run the CLI generator in dry-run mode and ensure path list is returned
        from app.cli.generate_reports import run_reports

        out_dir = str(tmp_path / "reports")
        os.makedirs(out_dir, exist_ok=True)

        outputs = run_reports(
            patient_id=patient.id,
            out_dir=out_dir,
            dry_run=True,
            session_factory=TestingSessionLocal,
        )
        assert isinstance(outputs, list)
        # In dry-run we still return intended paths
        assert len(outputs) >= 1
    finally:
        db.close()
