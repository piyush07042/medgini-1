"""Run a lightweight end-to-end pipeline that generates a clinical report PDF/HTML from a sample patient.

This script is intentionally low-dependency: it uses the existing report renderer and PDF generator
and does not require running the full Supervisor or external AI services.

Usage:
    python scripts/run_full_pipeline.py --template report_short_template.html

Outputs:
    - temp_reports/MediGenie_FullPipeline_<timestamp>.pdf
    - temp_reports/MediGenie_FullPipeline_<timestamp>.html
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from app.core.pdf_generator import generate_clinical_pdf_report
from app.core.report_renderer import render_report_html

TEMP_DIR = Path("temp_reports")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

SAMPLE_PATIENT = {
    "id": 1,
    "name": "John Doe",
    "age": 58,
    "gender": "Male",
}

SAMPLE_REPORT = {
    "generated_at": datetime.utcnow().isoformat(),
    "patient": SAMPLE_PATIENT,
    "patient_history": "History of hypertension and type 2 diabetes.",
    "symptoms": ["fatigue", "exertional dyspnea"],
    "medications": ["metformin", "lisinopril"],
    "allergies": ["penicillin"],
    "extracted_metrics": {"systolic_bp": 150, "diastolic_bp": 92, "glucose": 140},
    "disease_risk": {"risk_category": "High", "risk_score": 0.82, "top_factors": [{"feature": "systolic_bp", "value": 150}]},
    "knowledge_results": [],
    "drug_analysis": {"status": "FLAGGED", "interaction_warnings": [], "allergy_conflicts": []},
    "recommendations": [{"priority": "High", "title": "Follow-up", "recommendation": "Refer to cardiology."}],
    "warnings": [],
    "errors": [],
    "execution_trace": [],
    "metadata": {},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a MediGenie sample clinical report.")
    parser.add_argument(
        "--template",
        default="report_template.html",
        help="Template file to use for HTML rendering.",
    )
    parser.add_argument(
        "--output-dir",
        default="temp_reports",
        help="Directory to write generated files.",
    )
    return parser.parse_args()


def generate_report_files(report: dict[str, Any], template_name: str, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    html = render_report_html(report, template_name=template_name)
    html_path = output_dir / f"MediGenie_FullPipeline_{timestamp}.html"
    html_path.write_text(html, encoding="utf-8")

    pdf_bytes = generate_clinical_pdf_report(report)
    pdf_path = output_dir / f"MediGenie_FullPipeline_{timestamp}.pdf"
    pdf_path.write_bytes(pdf_bytes)

    return html_path, pdf_path


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    html_path, pdf_path = generate_report_files(
        SAMPLE_REPORT,
        template_name=args.template,
        output_dir=output_dir,
    )

    print("Generated files:")
    print(f" - {html_path}")
    print(f" - {pdf_path}")


if __name__ == "__main__":
    main()
