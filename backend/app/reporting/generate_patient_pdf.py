from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_patient_pdf(filename="patient_demo_report.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'HeaderTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'HeaderSub',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=15
    )
    
    story.append(Paragraph("METRO GENERAL HOSPITAL & DIAGNOSTICS", title_style))
    story.append(Paragraph("100 Clinical Parkway, Suite 400 | Phone: (555) 019-2831", subtitle_style))
    story.append(Spacer(1, 10))

    patient_data = [
        [Paragraph("<b>Patient Name:</b> Jane Doe", styles['Normal']), Paragraph("<b>Patient ID:</b> PT-2026-9941", styles['Normal'])],
        [Paragraph("<b>Age / Gender:</b> 52 / Female", styles['Normal']), Paragraph("<b>Date of Birth:</b> 1974-05-12", styles['Normal'])],
        [Paragraph("<b>Date of Evaluation:</b> 2026-07-29", styles['Normal']), Paragraph("<b>Attending Physician:</b> Dr. A. Sharma, MD", styles['Normal'])]
    ]
    t_patient = Table(patient_data, colWidths=[270, 270])
    t_patient.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_patient)
    story.append(Spacer(1, 15))

    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor("#1E3A8A"),
        spaceAfter=8
    )
    story.append(Paragraph("COMPREHENSIVE METABOLIC & LAB PANEL", section_style))

    results_data = [
        ["Test / Metric", "Observed Value", "Reference Interval", "Interpretation"],
        ["Fasting Blood Glucose", "145.0 mg/dL", "70.0 - 99.0 mg/dL", "HIGH"],
        ["Systolic Blood Pressure", "138 mmHg", "< 120 mmHg", "ELEVATED"],
        ["Body Mass Index (BMI)", "31.5 kg/m²", "18.5 - 24.9 kg/m²", "HIGH (Obese Class I)"],
        ["Total Cholesterol", "210.0 mg/dL", "< 200.0 mg/dL", "ELEVATED"],
        ["Serum Creatinine", "0.9 mg/dL", "0.6 - 1.1 mg/dL", "NORMAL"],
        ["HbA1c", "7.1 %", "< 5.7 %", "HIGH"]
    ]

    t_results = Table(results_data, colWidths=[180, 110, 130, 120])
    t_results.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1E40AF")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('TEXTCOLOR', (3, 1), (3, 4), colors.HexColor("#DC2626")),
        ('TEXTCOLOR', (3, 6), (3, 6), colors.HexColor("#DC2626")),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_results)
    story.append(Spacer(1, 15))

    story.append(Paragraph("CURRENT MEDICATIONS & ALLERGIES", section_style))
    med_data = [
        [Paragraph("<b>Active Medications:</b> Lisinopril 10mg QD, Metformin 500mg BID", styles['Normal'])],
        [Paragraph("<b>Documented Allergies:</b> Penicillin (Rash / Mild Severe)", styles['Normal'])]
    ]
    t_meds = Table(med_data, colWidths=[540])
    t_meds.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF2F2")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#FCA5A5")),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_meds)
    story.append(Spacer(1, 15))

    story.append(Paragraph("CLINICAL IMPRESSION & CDSS NOTES", section_style))
    impression_text = (
        "Patient exhibits signs of uncontrolled hyperglycemia with Fasting Glucose at 145 mg/dL "
        "and HbA1c at 7.1%. Blood pressure remains pre-hypertensive at 138 mmHg. "
        "Class I obesity (BMI 31.5) poses ongoing metabolic and cardiovascular risk factors."
    )
    story.append(Paragraph(impression_text, styles['Normal']))

    doc.build(story)
    print(f"🎉 Demo Patient PDF generated successfully: '{filename}'")

if __name__ == "__main__":
    generate_patient_pdf()