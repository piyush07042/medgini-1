import asyncio
from app.agents.base.agent_state import AgentState
from app.agents.report_generation.report_generation_agent import ReportGenerationAgent

async def main():
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

    agent = ReportGenerationAgent()
    result = await agent.run(state)
    print('result success', result.success)
    print('report keys', list(state.final_report.keys()))
    print('recommendations', state.final_report.get('recommendations'))
    print('follow_up', state.final_report.get('follow_up'))
    print('patient_summary', state.final_report.get('patient_summary'))
    print('confidence', state.final_report.get('confidence'))
    print('clinical_summary', state.final_report.get('clinical_summary'))

asyncio.run(main())
