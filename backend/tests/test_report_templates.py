"""Tests for report template rendering and automation."""

from __future__ import annotations

from pathlib import Path

from app.core.report_renderer import list_report_templates, render_report_html


def test_list_report_templates_contains_variants():
    templates = list_report_templates()

    assert "report_template.html" in templates
    assert "report_short_template.html" in templates
    assert "report_long_template.html" in templates


def test_render_report_html_variants():
    sample_report = {
        "patient": {"name": "Jane Doe", "id": 1},
        "generated_at": "2026-08-03T00:00:00Z",
        "clinical_summary": "Sample summary.",
        "disease_risk": {"risk_category": "Moderate", "risk_score": 0.55},
        "medications": ["metformin"],
        "allergies": ["penicillin"],
        "recommendations": [{"priority": "Medium", "title": "Monitor", "recommendation": "Check follow-up labs."}],
    }

    for template in list_report_templates():
        html = render_report_html(sample_report, template_name=template)
        assert "MediGenie Clinical Report" in html
        assert "Jane Doe" in html


def test_generate_report_files_creates_files(tmp_path: Path):
    from app.core.pdf_generator import generate_clinical_pdf_report
    from app.core.report_renderer import render_report_html

    sample_report = {
        "patient": {"name": "Jane Doe", "id": 1},
        "generated_at": "2026-08-03T00:00:00Z",
        "clinical_summary": "Sample summary.",
        "disease_risk": {"risk_category": "Moderate", "risk_score": 0.55},
        "medications": ["metformin"],
        "allergies": ["penicillin"],
        "recommendations": [{"priority": "Medium", "title": "Monitor", "recommendation": "Check follow-up labs."}],
    }

    html = render_report_html(sample_report, template_name="report_short_template.html")
    path = tmp_path / "report.html"
    path.write_text(html, encoding="utf-8")

    assert path.exists()
    assert "Jane Doe" in path.read_text(encoding="utf-8")

    pdf_bytes = generate_clinical_pdf_report(sample_report)
    assert isinstance(pdf_bytes, (bytes, bytearray))
    assert len(pdf_bytes) > 0
