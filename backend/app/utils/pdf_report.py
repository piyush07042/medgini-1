from io import BytesIO
from typing import Any, Dict, List, Optional
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
)

# Non-clinical patient meta-fields that should be excluded when
# deriving a "Clinical Input Summary" from raw patient data.
_PATIENT_NON_CLINICAL_FIELDS = frozenset({
    "id", "patient_id", "doctor_id", "first_name", "last_name",
    "name", "avatar_url", "created_at", "updated_at",
    "medical_history", "allergies", "current_medications",
})


def _format_datetime(ts: Optional[str]) -> str:
    if not ts:
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    try:
        return datetime.fromisoformat(str(ts)).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(ts)


def _safe_get(d: Dict[str, Any], key: str, default: Any = "") -> Any:
    return d.get(key) if d and key in d else default


def _fmt_pct(value: Any, default: str = "N/A") -> str:
    """Convert a fraction (0-1) or percentage (>1) to a display string like 88.0%."""
    if value is None:
        return default
    try:
        f = float(value)
        if f <= 1.0:
            return f"{f * 100:.1f}%"
        return f"{f:.1f}%"
    except Exception:
        return str(value) if value is not None else default


def _prediction_label(pred_raw: Any, disease: str = "") -> str:
    """
    Translate a raw ML prediction value (0, 1, string) into a clinician-friendly label.
    Crucially, integer 0 is a valid 'negative' result and must NOT be treated as falsy.
    """
    # Binary numeric predictions
    if pred_raw is not None and not isinstance(pred_raw, str):
        try:
            val = int(pred_raw)
            if val == 1:
                label = f"{disease} Risk Detected" if disease else "Positive"
                return label
            if val == 0:
                label = f"{disease} Risk Not Detected" if disease else "Negative"
                return label
        except (TypeError, ValueError):
            pass

    # String predictions
    if pred_raw is not None:
        s = str(pred_raw).strip()
        if s.lower() in ("n/a", "", "none", "null"):
            return "Pending ML Evaluation"
        return s

    return "Pending ML Evaluation"


def generate_medigenie_report(report: Dict[str, Any]) -> bytes:
    """
    Generate a professional clinical PDF report for MediGenie.

    Accepts the canonical report dict produced by build_final_report /
    build_report_from_storage (keys: patient, prediction / prediction_results /
    risk_assessment, metadata / meta, clinical_summary, recommendations, etc.)
    as well as any dict previously passed with explicit 'result' and 'meta' keys.

    Returns PDF bytes.
    """
    buffer = BytesIO()

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.spaceAfter = 6
    normal.fontName = "Helvetica"
    heading = ParagraphStyle(
        "Heading", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=12,
        textColor=colors.HexColor("#0B68D8"),
    )
    section_title = ParagraphStyle(
        "SectionTitle", parent=styles["Heading3"],
        fontName="Helvetica-Bold", fontSize=10,
        textColor=colors.HexColor("#0B68D8"),
    )
    small = ParagraphStyle(
        "Small", parent=normal, fontSize=9,
        textColor=colors.grey,
    )

    doc = BaseDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=24 * mm, bottomMargin=18 * mm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - 12 * mm, id="normal")

    # ── Resolve meta / metadata dual lookup ──────────────────────────────────
    meta: Dict[str, Any] = report.get("meta") or report.get("metadata") or {}
    report_id = (
        meta.get("report_id")
        or meta.get("id")
        or report.get("report_id")
        or "-"
    )
    gen_ts = _format_datetime(
        meta.get("generated_at") or report.get("generated_at")
    )
    version = meta.get("version") or meta.get("model_version") or "1.0"
    disease_label = (
        meta.get("disease")
        or report.get("disease")
        or ""
    )

    def _header_footer(canvas, doc_obj):
        canvas.saveState()
        # Header
        logo_path = meta.get("logo_path")
        if logo_path:
            try:
                img = Image(logo_path, width=32, height=32)
                img.drawOn(canvas, doc.leftMargin, A4[1] - 40)
            except Exception:
                pass

        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawString(doc.leftMargin + (36 if logo_path else 0), A4[1] - 30, "MEDIGENIE")
        canvas.setFont("Helvetica", 8)
        canvas.drawString(doc.leftMargin + (36 if logo_path else 0), A4[1] - 42, "AI Clinical Decision Support System")
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawRightString(A4[0] - doc.rightMargin, A4[1] - 30, "AI Generated Clinical Report")

        # Report metadata line
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(
            A4[0] - doc.rightMargin, A4[1] - 42,
            f"Report ID: {report_id}    Generated: {gen_ts}    Version: {version}",
        )

        # Footer
        canvas.setFont("Helvetica", 8)
        canvas.drawString(doc.leftMargin, 18 * mm, "MediGenie AI CDSS")
        canvas.drawCentredString(A4[0] / 2, 18 * mm, gen_ts)
        canvas.drawRightString(A4[0] - doc.rightMargin, 18 * mm, f"Page {doc_obj.page}")
        canvas.restoreState()

    doc.addPageTemplates([PageTemplate(id="Report", frames=[frame], onPage=_header_footer)])

    elements: List[Any] = []

    # Title
    elements.append(Paragraph("AI Clinical Report", heading))
    elements.append(Spacer(1, 6))

    # ── PATIENT INFORMATION ──────────────────────────────────────────────────
    patient: Dict[str, Any] = report.get("patient", {}) or {}
    patient_summary: Dict[str, Any] = report.get("patient_summary", {}) or {}

    pat_rows = []

    def add_row(label, value):
        if value is None or (isinstance(value, str) and not value.strip()):
            return
        pat_rows.append([Paragraph(f"<b>{label}</b>", normal), Paragraph(str(value), normal)])

    patient_name = (
        patient_summary.get("name")
        or f"{patient.get('first_name', '')} {patient.get('last_name', '')}".strip()
        or patient.get("name")
        or ""
    )
    add_row("Patient Name", patient_name)
    add_row("Age", patient_summary.get("age") or patient.get("age"))
    add_row("Gender", patient_summary.get("gender") or patient.get("gender"))
    add_row("Disease", disease_label or meta.get("disease"))
    add_row("Report Date", gen_ts)
    add_row("Patient ID", patient.get("id") or patient.get("patient_id"))

    if pat_rows:
        t = Table(pat_rows, colWidths=[50 * mm, doc.width - 50 * mm])
        t.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1e4ff")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.whitesmoke),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f8fbff")),
        ]))
        elements.append(Paragraph("Patient Information", section_title))
        elements.append(Spacer(1, 4))
        elements.append(t)
        elements.append(Spacer(1, 8))

    # ── CLINICAL INPUT SUMMARY ───────────────────────────────────────────────
    # Prefer an explicit 'inputs' key; fall back to filtering clinical patient fields
    inputs: Dict[str, Any] = report.get("inputs") or {}
    if not inputs and patient:
        inputs = {
            k: v for k, v in patient.items()
            if k not in _PATIENT_NON_CLINICAL_FIELDS and v is not None
        }

    input_rows = []
    for key, val in inputs.items():
        if val is None or (isinstance(val, str) and not str(val).strip()):
            continue
        input_rows.append([
            Paragraph(f"{key.replace('_', ' ').title()}", normal),
            Paragraph(str(val), normal),
        ])

    if input_rows:
        t = Table(input_rows, colWidths=[60 * mm, doc.width - 60 * mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#fbfbfe")]),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#eef3ff")),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.whitesmoke),
        ]))
        elements.append(Paragraph("Clinical Input Summary", section_title))
        elements.append(Spacer(1, 4))
        elements.append(t)
        elements.append(Spacer(1, 8))

    # ── PREDICTION RESULT ────────────────────────────────────────────────────
    # Canonical source is report["prediction"] (from build_final_report).
    # Legacy callers may pass report["result"] directly.
    prediction_block: Dict[str, Any] = (
        report.get("prediction")
        or report.get("prediction_results")
        or report.get("risk_assessment")
        or report.get("result")
        or {}
    )

    # Raw prediction value — NOTE: 0 is a valid value, must NOT use falsy check
    pred_raw = prediction_block.get("prediction")
    if pred_raw is None:
        pred_raw = prediction_block.get("label")

    # Determine disease name for the label
    _disease_name = (
        disease_label
        or (report.get("patient_summary") or {}).get("disease")
        or meta.get("disease")
        or ""
    )
    # Also try to infer from disease_risk.disease stored inside prediction_block
    if not _disease_name:
        _disease_name = prediction_block.get("disease", "")

    pred_display = _prediction_label(pred_raw, _disease_name)

    # Risk level
    raw_risk = (
        prediction_block.get("risk_category")
        or prediction_block.get("risk_level")
        or prediction_block.get("risk")
        or prediction_block.get("confidence_label")
    )
    if raw_risk and str(raw_risk).upper() not in ("UNKNOWN", "N/A", "NONE", ""):
        risk_display = str(raw_risk).upper()
    else:
        risk_display = "PENDING ML EVALUATION"

    # Probability
    prob = prediction_block.get("probability") or prediction_block.get("risk_score")
    prob_text = _fmt_pct(prob, default="Not available")

    # Confidence
    conf = prediction_block.get("confidence")
    conf_text = _fmt_pct(conf, default="Not available")

    # Model metadata
    model_name = (
        meta.get("model_name")
        or meta.get("model")
        or prediction_block.get("model_name")
        or prediction_block.get("model")
        or (_disease_name.title() + " Prediction Model" if _disease_name else "MediGenie Prediction Model")
    )
    model_version = (
        meta.get("model_version")
        or prediction_block.get("model_version")
        or version
        or "1.0.0"
    )

    # Color by risk level
    risk_upper = risk_display.upper()
    if "HIGH" in risk_upper or "CRITICAL" in risk_upper or "SEVERE" in risk_upper:
        box_color = colors.HexColor("#ffe6e6")
        border_color = colors.HexColor("#e04d4d")
    elif "MED" in risk_upper or "MOD" in risk_upper:
        box_color = colors.HexColor("#fff6e6")
        border_color = colors.HexColor("#e08b1f")
    else:
        box_color = colors.HexColor("#e8fff0")
        border_color = colors.HexColor("#1f9b4a")

    pred_table = Table(
        [
            [Paragraph("<b>Prediction</b>", normal),    Paragraph(pred_display, heading)],
            [Paragraph("<b>Risk Level</b>", normal),    Paragraph(risk_display, normal)],
            [Paragraph("<b>Probability</b>", normal),   Paragraph(prob_text, normal)],
            [Paragraph("<b>Confidence</b>", normal),    Paragraph(conf_text, normal)],
            [Paragraph("<b>Model</b>", normal),         Paragraph(model_name, normal)],
            [Paragraph("<b>Model Version</b>", normal), Paragraph(model_version, normal)],
        ],
        colWidths=[50 * mm, doc.width - 50 * mm],
    )
    pred_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), box_color),
        ("BOX", (0, 0), (-1, -1), 1.0, border_color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))

    elements.append(Paragraph("Prediction Result", section_title))
    elements.append(Spacer(1, 4))
    elements.append(pred_table)
    elements.append(Spacer(1, 8))

    # ── CLINICAL SUMMARY ─────────────────────────────────────────────────────
    clinical_summary = report.get("clinical_summary") or report.get("summary") or report.get("ai_summary")
    if clinical_summary:
        # Replace generic "Estimated probability" with clearer ML-sourced label
        clinical_summary = str(clinical_summary).replace(
            "Estimated probability:", "ML predicted probability:"
        )
        elements.append(Paragraph("Clinical Summary", section_title))
        elements.append(Spacer(1, 4))
        elements.append(Paragraph(clinical_summary, normal))
        elements.append(Spacer(1, 8))

    # ── KEY RISK FACTORS ─────────────────────────────────────────────────────
    factors = (
        report.get("key_risk_factors")
        or report.get("risk_factors")
        or (report.get("explainability") or {}).get("top_factors")
        or []
    )
    if factors:
        bullets = [Paragraph(f"• {str(x)}", normal) for x in factors]
        elements.append(Paragraph("Key Risk Factors", section_title))
        elements.append(Spacer(1, 4))
        elements.extend(bullets)
        elements.append(Spacer(1, 8))

    # ── RECOMMENDATIONS ──────────────────────────────────────────────────────
    raw_recs = report.get("recommendations") or []
    recs = []
    for r in raw_recs:
        if isinstance(r, dict):
            if "recommendations" in r and isinstance(r["recommendations"], list):
                recs.extend(r["recommendations"])
            elif "title" in r or "recommendation" in r or "summary" in r or "action" in r:
                recs.append(r)
        elif isinstance(r, str) and r.strip():
            recs.append({"title": "Recommendation", "recommendation": r.strip()})

    if recs:
        elements.append(Paragraph("AI Recommendations", section_title))
        elements.append(Spacer(1, 4))
        for i, r in enumerate(recs[:20], start=1):
            if isinstance(r, dict):
                title = r.get("title") or r.get("category") or r.get("priority") or f"Recommendation {i}"
                text = r.get("recommendation") or r.get("summary") or r.get("action") or ""
                if not text:
                    continue
                # Soften any remaining aggressive recommendation language
                text = text.replace(
                    "Aggressive treatment protocol should be considered",
                    "Urgent clinical evaluation is recommended. Further management should be determined by a qualified clinician according to applicable clinical guidelines.",
                )
                elements.append(Paragraph(f"{i}. <b>{title}:</b> {text}", normal))
            elif isinstance(r, str):
                elements.append(Paragraph(f"{i}. {r}", normal))
        elements.append(Spacer(1, 8))

    # ── CLINICAL INTELLIGENCE ────────────────────────────────────────────────
    clinical = report.get("clinical_intelligence") or {}
    if clinical:
        elements.append(Paragraph("Clinical Intelligence", section_title))
        elements.append(Spacer(1, 4))
        for key, value in clinical.items():
            if isinstance(value, list):
                elements.append(Paragraph(f"<b>{key}:</b>", normal))
                for item in value:
                    elements.append(Paragraph(f"• {item}", normal))
            else:
                elements.append(Paragraph(f"<b>{key}:</b> {value}", normal))
            elements.append(Spacer(1, 4))
        elements.append(Spacer(1, 8))

    # ── MEDICATION SAFETY ────────────────────────────────────────────────────
    med = report.get("medication_safety") or report.get("drug_safety") or {}
    if isinstance(med, dict) and med:
        rows = []
        if med.get("risk_level"):
            rows.append([Paragraph("Risk Level", normal), Paragraph(str(med.get("risk_level") or "None"), normal)])
        if med.get("warnings"):
            rows.append([Paragraph("Warnings", normal), Paragraph(", ".join(med.get("warnings") or []) or "None", normal)])
        if med.get("interactions"):
            rows.append([Paragraph("Drug interactions", normal), Paragraph(", ".join(str(x) for x in (med.get("interactions") or [])) or "None", normal)])
        if med.get("contraindications"):
            rows.append([Paragraph("Contraindications", normal), Paragraph(", ".join(str(x) for x in (med.get("contraindications") or [])) or "None", normal)])
        if rows:
            t = Table(rows, colWidths=[60 * mm, doc.width - 60 * mm])
            t.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#eef3ff")),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#fbfbfe")]),
            ]))
            elements.append(Paragraph("Medication Safety", section_title))
            elements.append(Spacer(1, 4))
            elements.append(t)
            elements.append(Spacer(1, 8))

    # ── MEDICAL EVIDENCE ─────────────────────────────────────────────────────
    evidence = report.get("evidence") or report.get("medical_evidence") or []
    if evidence:
        elements.append(Paragraph("Medical Evidence", section_title))
        elements.append(Spacer(1, 4))
        for ev in evidence[:3]:
            if not isinstance(ev, dict):
                continue
            src = ev.get("source") or ev.get("source_name") or ev.get("title") or "Unknown"
            cat = ev.get("category") or ev.get("type") or ""
            excerpt = ev.get("excerpt") or ev.get("snippet") or ev.get("summary") or ""
            if isinstance(excerpt, str) and len(excerpt) > 300:
                excerpt = excerpt[:300].rsplit(" ", 1)[0] + "..."
            score = ev.get("score") or ev.get("similarity") or ""
            elements.append(Paragraph(f"Source: <b>{src}</b>", normal))
            if cat:
                elements.append(Paragraph(f"Category: {cat}", small))
            if excerpt:
                elements.append(Paragraph(excerpt, normal))
            if score:
                elements.append(Paragraph(f"Similarity: {score}", small))
            elements.append(Spacer(1, 6))

    # ── FOLLOW-UP PLAN ───────────────────────────────────────────────────────
    follow = report.get("follow_up") or report.get("followup") or report.get("follow_up_plan") or []
    if follow:
        elements.append(Paragraph("Follow-up Plan", section_title))
        elements.append(Spacer(1, 4))
        for item in follow:
            elements.append(Paragraph(f"• {item}", normal))
        elements.append(Spacer(1, 8))

    # ── EXPLAINABILITY ───────────────────────────────────────────────────────
    explain = report.get("explainability") or report.get("explain") or {}
    elements.append(Paragraph("AI Explainability", section_title))
    elements.append(Spacer(1, 4))
    if explain and (explain.get("top_factors") or explain.get("feature_importance") or explain.get("shap")):
        if explain.get("top_factors"):
            elements.append(Paragraph("Top contributing factors:", small))
            for f in explain.get("top_factors")[:10]:
                elements.append(Paragraph(f"• {f}", normal))
        if explain.get("feature_importance"):
            elements.append(Paragraph("Feature importance:", small))
            elements.append(Paragraph(str(explain.get("feature_importance")), normal))
        if explain.get("shap"):
            elements.append(Paragraph("SHAP summary available.", small))
    else:
        elements.append(Paragraph("Explainability: Not available for this model.", normal))

    elements.append(Spacer(1, 8))

    # ── REFERENCES / SOURCES ─────────────────────────────────────────────────
    references = report.get("references") or []
    if references:
        elements.append(Paragraph("References / Sources", section_title))
        elements.append(Spacer(1, 4))
        for idx, ref in enumerate(references[:10], start=1):
            if isinstance(ref, dict):
                src = ref.get("source") or ref.get("title") or f"Reference {idx}"
                excerpt = ref.get("excerpt") or ""
                if excerpt:
                    elements.append(Paragraph(f"{idx}. <b>{src}</b> — {excerpt[:200]}", normal))
                else:
                    elements.append(Paragraph(f"{idx}. {src}", normal))
            else:
                elements.append(Paragraph(f"{idx}. {ref}", normal))
        elements.append(Spacer(1, 8))

    # ── DISCLAIMER ───────────────────────────────────────────────────────────
    disclaimer = (
        "This report is AI-assisted and is intended to support qualified healthcare professionals. "
        "It should not replace clinical judgement. Use in conjunction with clinical assessment and local protocols. "
        "Further management should be determined by a qualified clinician according to applicable clinical guidelines."
    )
    disc_table = Table(
        [[Paragraph(disclaimer, small)]],
        colWidths=[doc.width],
    )
    disc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff7e6")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#f1c27d")),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(disc_table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
