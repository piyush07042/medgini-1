import os
import sys
sys.path.insert(0, os.getcwd())

from app.agents.supervisor.supervisor import Supervisor
from app.agents.base.agent_state import AgentState
from app.schemas.heart_disease import REQUEST_EXAMPLE

supervisor = Supervisor()
state = AgentState()
state.patient = REQUEST_EXAMPLE.copy()
state.patient.setdefault('name', 'Test Patient')
state.patient.setdefault('gender', 'unknown')
state.symptoms = ['chest pain']

print('Starting workflow...')
final_state, results, metrics = supervisor.run(state)
print('Finished:', type(final_state), type(results), type(metrics))
print('State disease_risk:', final_state.disease_risk)
print('State knowledge_results length:', len(final_state.knowledge_results or []))
print('State drug_analysis:', final_state.drug_analysis)
print('State recommendations:', final_state.recommendations)
print('State final_report:', final_state.final_report)
print('Results:', results)
print('Metrics:', metrics)
