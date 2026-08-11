from app.agents.base.agent_state import AgentState
from app.agents.report_generation.report_generation_agent import ReportGenerationAgent
from app.services.report.report_service import build_final_report

state = AgentState()
state.patient_context = {
    "name": "John Doe",
    "age": 45,
    "gender": "Female",
}
state.symptoms = ["fatigue"]
state.medications = ["aspirin"]
state.allergies = ["penicillin"]
state.disease_risk = {
    "risk_category": "Moderate",
    "probability": 0.42,
    "confidence_label": "Medium",
    "explanations": [{"feature": "age", "value": 45}],
}
state.knowledge_results = [
    {"source": "Clinical Guidelines", "text": "Follow-up within 3 months."},
]
state.drug_analysis = {"status": "PASS", "overall_risk": "Low"}
state.recommendations = [
    {"title": "Lifestyle", "recommendation": "Exercise regularly.", "follow_up_plan": ["Repeat labs in 2 weeks."]},
]

report = build_final_report(state)
print('report keys', list(report.keys()))
print('generated_at', report.get('generated_at'))
print('patient_summary', report.get('patient_summary'))
print('recommendations', report.get('recommendations'))
print('follow_up', report.get('follow_up'))
print('confidence', report.get('confidence'))
print('clinical_summary', report.get('clinical_summary'))
print('prediction', report.get('prediction'))
print('confidence_label', report.get('confidence_label'))
print('structured_recommendation', report.get('structured_recommendation'))
