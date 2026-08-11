import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_cdss_pdf(filename: str, patient_data: dict, summary_text: str, risk_score: float, risk_category: str):
    """
    Generates a structured clinical summary PDF report for clinicians.
    """
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748")
    )
    
    story = []

    # Document Header
    story.append(Paragraph("MediGenie CDSS — Clinical Summary Report", title_style))
    story.append(Spacer(1, 8))

    # Patient Context Metadata Table
    p_id = str(patient_data.get("patient_id", "PT-UNKNOWN"))
    age = str(patient_data.get("age", "N/A"))
    gender = str(patient_data.get("gender", "N/A"))
    glucose = str(patient_data.get("glucose", "N/A"))
    bp = str(patient_data.get("systolic_bp", "N/A"))
    bmi = str(patient_data.get("bmi", "N/A"))

    meta_table_data = [
        [
            Paragraph("<b>Patient ID:</b>", body_style), Paragraph(p_id, body_style),
            Paragraph("<b>Risk Level:</b>", body_style), Paragraph(f"<b>{risk_category} ({risk_score}%)</b>", body_style)
        ],
        [
            Paragraph("<b>Age / Gender:</b>", body_style), Paragraph(f"{age} / {gender}", body_style),
            Paragraph("<b>Fasting Glucose:</b>", body_style), Paragraph(f"{glucose} mg/dL", body_style)
        ],
        [
            Paragraph("<b>BMI:</b>", body_style), Paragraph(bmi, body_style),
            Paragraph("<b>Systolic BP:</b>", body_style), Paragraph(f"{bp} mmHg", body_style)
        ]
    ]

    table = Table(meta_table_data, colWidths=[100, 150, 110, 180])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 14))

    # Clinical Analysis & Findings Section
    story.append(Paragraph("Clinical Findings & Directives", heading_style))
    
    # Process and append summary lines
    for line in summary_text.split('\n'):
        line_clean = line.strip()
        if line_clean:
            story.append(Paragraph(line_clean, body_style))
            story.append(Spacer(1, 4))

    doc.build(story)
    return filename