"""
Unit tests for Digital Signature generation and verification.
"""
import pytest

from app.services.report.digital_signature import (
    generate_digital_signature,
    verify_report_signature,
)


SAMPLE_REPORT = {
    "patient_summary": {"name": "John Doe", "age": 55, "gender": "Male"},
    "patient_information": {"name": "John Doe", "age": 55, "gender": "Male"},
    "prediction_results": {"risk_category": "High", "risk_score": 0.87},
    "prediction": {"risk_category": "High", "risk_score": 0.87},
    "clinical_intelligence": {"Guideline": "ACC/AHA 2019"},
    "drug_safety": {"interactions": []},
    "risk_assessment": {"risk_category": "High", "probability": 0.87},
    "recommendations": [{"title": "Follow up", "recommendation": "Schedule appointment"}],
    "follow_up_plan": [{"timeline": "1 month", "action": "Cardiology follow-up"}],
    "follow_up": [{"timeline": "1 month", "action": "Cardiology follow-up"}],
    "generated_at": "2026-08-08T08:00:00Z",
}


class TestDigitalSignatureGeneration:
    """Test digital signature creation."""

    def test_signature_returns_required_fields(self):
        signature = generate_digital_signature(SAMPLE_REPORT)
        assert "verification_id" in signature
        assert "signature_hash" in signature
        assert "signature_preview" in signature
        assert "signed_at" in signature
        assert "signed_by" in signature
        assert "algorithm" in signature
        assert "integrity_status" in signature
        assert "seal_label" in signature

    def test_verification_id_format(self):
        signature = generate_digital_signature(SAMPLE_REPORT)
        verification_id = signature["verification_id"]
        assert verification_id.startswith("VERIF-")
        parts = verification_id.split("-")
        assert len(parts) == 3
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4

    def test_signature_hash_is_64_hex_chars(self):
        signature = generate_digital_signature(SAMPLE_REPORT)
        assert len(signature["signature_hash"]) == 64
        # SHA-256 produces only hex digits
        int(signature["signature_hash"], 16)  # Should not raise

    def test_signature_preview_is_16_chars(self):
        signature = generate_digital_signature(SAMPLE_REPORT)
        assert len(signature["signature_preview"]) == 16

    def test_algorithm_is_sha256(self):
        signature = generate_digital_signature(SAMPLE_REPORT)
        assert signature["algorithm"] == "SHA-256"

    def test_integrity_status_is_verified(self):
        signature = generate_digital_signature(SAMPLE_REPORT)
        assert signature["integrity_status"] == "verified"

    def test_signed_by_is_medigenie(self):
        signature = generate_digital_signature(SAMPLE_REPORT)
        assert "MediGenie" in signature["signed_by"]

    def test_same_report_produces_same_hash(self):
        sig1 = generate_digital_signature(SAMPLE_REPORT)
        sig2 = generate_digital_signature(SAMPLE_REPORT)
        assert sig1["signature_hash"] == sig2["signature_hash"]

    def test_different_report_produces_different_hash(self):
        altered = {**SAMPLE_REPORT, "generated_at": "2025-01-01T00:00:00Z"}
        sig_original = generate_digital_signature(SAMPLE_REPORT)
        sig_altered = generate_digital_signature(altered)
        assert sig_original["signature_hash"] != sig_altered["signature_hash"]

    def test_unique_verification_ids(self):
        sig1 = generate_digital_signature(SAMPLE_REPORT)
        sig2 = generate_digital_signature(SAMPLE_REPORT)
        assert sig1["verification_id"] != sig2["verification_id"]


class TestSignatureVerification:
    """Test report integrity verification."""

    def test_verify_valid_signature(self):
        signature = generate_digital_signature(SAMPLE_REPORT)
        assert verify_report_signature(SAMPLE_REPORT, signature["signature_hash"]) is True

    def test_verify_tampered_report_fails(self):
        signature = generate_digital_signature(SAMPLE_REPORT)
        tampered = {**SAMPLE_REPORT, "generated_at": "1999-01-01T00:00:00Z"}
        assert verify_report_signature(tampered, signature["signature_hash"]) is False

    def test_verify_wrong_hash_fails(self):
        assert verify_report_signature(SAMPLE_REPORT, "0" * 64) is False

    def test_empty_report_signature(self):
        empty_report: dict = {}
        signature = generate_digital_signature(empty_report)
        assert verify_report_signature(empty_report, signature["signature_hash"]) is True
