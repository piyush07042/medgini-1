"""Regression tests for Phase 2 packaged-model loading."""

from __future__ import annotations

from app.services.heart_disease_service import HeartDiseaseService


def test_heart_disease_service_resolves_packaged_model_directory(tmp_path):
    service = HeartDiseaseService(tmp_path)

    assert service.model_directory == tmp_path.resolve()

    fallback_service = HeartDiseaseService("/tmp/does-not-exist")

    assert fallback_service.model_directory.exists()
    assert fallback_service.model_directory.name == "heart_disease"
