import os
import sys
sys.path.insert(0, os.getcwd())
from app.agents.base.agent_state import AgentState
from app.services.recommendation.recommendation_service import generate_recommendation

state = AgentState()
state.patient = {'name': 'Test', 'age': 63, 'gender': 'male'}
state.disease_risk = {'risk_category': 'High', 'probability': 0.85, 'confidence_label': 'High'}
state.knowledge_results = []
state.drug_analysis = {'warnings': []}
state.extracted_metrics = {}
output = generate_recommendation(state)
print('clinical_summary:', output['clinical_summary'])
print('recommendations len:', len(output['recommendations']))
print('recommendations type:', type(output['recommendations'][0]))
print('recommendations[0]:', output['recommendations'][0])
print('module file:', generate_recommendation.__code__.co_filename)
print('function line:', generate_recommendation.__code__.co_firstlineno)
print('build file:', generate_recommendation.__globals__['_build_clinical_summary'].__code__.co_filename)
print('build line:', generate_recommendation.__globals__['_build_clinical_summary'].__code__.co_firstlineno)
print('source snippet:')
import inspect
print(inspect.getsource(generate_recommendation.__globals__['_build_clinical_summary']))
