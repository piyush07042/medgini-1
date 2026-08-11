"""PDF report generator used by the reporting API."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas


def _safe_text(value: Any, default: str = "N/A") -> str:
    if value is None:
        return default
    if isinstance(value, (list, dict)):
        return ", ".join(str(value)) if not isinstance(value, dict) else default
    return str(value)


def _build_list_text(items: list[Any]) -> str:
    return "\n".join(f"- {item}" for item in items if item is not None)


def _footer(canvas: Canvas, doc) -> None:
    canvas.saveState()
    footer_text = "MediGenie Clinical Report — Confidential"
    page_text = f"Page {doc.page}"
    canvas.setFont("Helvetica", 8)
    canvas.drawString(36, 20, footer_text)
    canvas.drawRightString(letter[0] - 36, 20, page_text)
    canvas.restoreState()


def generate_clinical_pdf_report(report: dict[str, Any]) -> bytes:
    """Generate a clinical PDF report and return the raw bytes."""

    patient = report.get("patient", {}) or {}
    patient_summary = report.get("patient_summary", {}) or {}
    patient_name = _safe_text(patient_summary.get("name") or patient.get("name") or patient.get("first_name") or patient.get("last_name"), "Patient")
    patient_id = _safe_text(patient.get("id") or patient.get("patient_id"), "PT-UNKNOWN")
    age = _safe_text(patient_summary.get("age") or patient.get("age"), "N/A")
    gender = _safe_text(patient_summary.get("gender") or patient.get("gender"), "N/A")

    prediction = report.get("prediction", {}) or {}
    risk_category = _safe_text(prediction.get("risk_category"), "Unknown")
    probability = _safe_text(prediction.get("probability") or report.get("probability"), "N/A")
    confidence = _safe_text(prediction.get("confidence") or report.get("confidence"), "N/A")
    confidence_label = _safe_text(prediction.get("confidence_label"), "N/A")

    medications = report.get("medications") or []
    if isinstance(medications, str):
        medications = [medications]
    allergies = report.get("allergies") or []
    if isinstance(allergies, str):
        allergies = [allergies]

    patient_summary_text = _safe_text(patient_summary.get("summary_text") or "Patient details are provided.")
    ocr_findings = report.get("ocr_findings", {}) or {}
    extracted_metrics = ocr_findings.get("extracted_metrics") or {}
    knowledge = report.get("retrieved_evidence", {}) or {}
    drug_safety = report.get("drug_safety", {}) or {}
    recommendations = report.get("recommendations") or []
    follow_up = report.get("follow_up") or []
    clinical_summary = report.get("clinical_summary") or "No clinical summary available."
    clinical_intelligence = report.get("clinical_intelligence") or {}

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
    )

    story = []
    story.append(Paragraph("MediGenie Clinical Report", title_style))
    story.append(Spacer(1, 8))

    patient_info = [
        [Paragraph("<b>Patient ID</b>", body_style), Paragraph(patient_id, body_style), Paragraph("<b>Patient Name</b>", body_style), Paragraph(patient_name, body_style)],
        [Paragraph("<b>Age</b>", body_style), Paragraph(age, body_style), Paragraph("<b>Gender</b>", body_style), Paragraph(gender, body_style)],
        [Paragraph("<b>Medications</b>", body_style), Paragraph(", ".join(medications) or "None", body_style), Paragraph("<b>Allergies</b>", body_style), Paragraph(", ".join(allergies) or "None", body_style)],
    ]
    story.append(Table(patient_info, colWidths=[70, 180, 70, 180], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ])))
    story.append(Spacer(1, 12))

    risk_info = [
        [Paragraph("<b>Risk Category</b>", body_style), Paragraph(risk_category, body_style), Paragraph("<b>Probability</b>", body_style), Paragraph(f"{probability}", body_style)],
        [Paragraph("<b>Confidence</b>", body_style), Paragraph(confidence, body_style), Paragraph("<b>Confidence Label</b>", body_style), Paragraph(confidence_label, body_style)],
    ]
    story.append(Paragraph("Risk Summary", heading_style))
    story.append(Table(risk_info, colWidths=[90, 150, 110, 140], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ])))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Patient Summary", heading_style))
    story.append(Paragraph(patient_summary_text, body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Clinical Summary", heading_style))
    for line in str(clinical_summary).split("\n"):
        if line.strip():
            story.append(Paragraph(line.strip(), body_style))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))
    story.append(Paragraph("OCR Findings", heading_style))
    story.append(Paragraph(_safe_text(ocr_findings.get("raw_report_text"), "No OCR text available."), body_style))
    if extracted_metrics:
        metrics_text = ", ".join(f"{key}: {value}" for key, value in extracted_metrics.items())
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"Extracted metrics: {metrics_text}", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Explainability", heading_style))
    explainability = report.get("explainability", {}) or {}
    story.append(Paragraph(_safe_text(explainability.get("notes"), "No explainability data available."), body_style))
    top_factors = explainability.get("top_factors") or []
    if top_factors:
        story.append(Spacer(1, 4))
        story.append(Paragraph(_build_list_text(top_factors), body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Retrieved Evidence", heading_style))
    evidence_summary = _safe_text(knowledge.get("evidence_summary"), "No retrieved evidence available.")
    story.append(Paragraph(evidence_summary, body_style))
    sources = knowledge.get("knowledge_results") or []
    for idx, source in enumerate(sources, start=1):
        source_label = source.get("source") if isinstance(source, dict) else None
        source_text = source.get("text") if isinstance(source, dict) else None
        if source_text:
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"{idx}. {source_label or 'Source'}: {source_text}", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Drug Safety", heading_style))
    if drug_safety:
        story.append(Paragraph(_safe_text(drug_safety.get("status"), "No drug safety status."), body_style))
        if drug_safety.get("overall_risk"):
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"Overall risk: {_safe_text(drug_safety.get('overall_risk'))}", body_style))
    else:
        story.append(Paragraph("No drug safety information available.", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Recommendations", heading_style))
    if recommendations:
        for rec in recommendations:
            if isinstance(rec, dict):
                title = rec.get("title") or rec.get("priority") or "Recommendation"
                text = rec.get("recommendation") or rec.get("summary") or str(rec)
                story.append(Paragraph(f"<b>{title}</b>: {text}", body_style))
            else:
                story.append(Paragraph(str(rec), body_style))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No recommendations available.", body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Follow-up", heading_style))
    if follow_up:
        story.append(Paragraph(_build_list_text(follow_up), body_style))
    else:
        story.append(Paragraph("No follow-up actions provided.", body_style))
    story.append(Spacer(1, 16))

    if clinical_intelligence:
        story.append(Paragraph("Clinical Intelligence", heading_style))
        for key, value in clinical_intelligence.items():
            if isinstance(value, list):
                story.append(Paragraph(f"<b>{key}:</b>", body_style))
                for item in value:
                    story.append(Paragraph(f"• {item}", body_style))
                    story.append(Spacer(1, 2))
            else:
                story.append(Paragraph(f"<b>{key}:</b> {value}", body_style))
            story.append(Spacer(1, 6))
        story.append(Spacer(1, 10))

    generated_at = _safe_text(report.get("generated_at"), "Unknown")
    story.append(Paragraph(f"Report generated at: {generated_at}", body_style))
    story.append(Spacer(1, 10))
    story.append(Paragraph("References", heading_style))
    if sources:
        for idx, source in enumerate(sources, start=1):
            name = source.get("source") if isinstance(source, dict) else str(source)
            story.append(Paragraph(f"{idx}. {name}", body_style))
    else:
        story.append(Paragraph("No external references available.", body_style))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer.read()
