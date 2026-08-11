import asyncio
from app.agents.base.agent_state import AgentState
from app.agents.supervisor.supervisor import Supervisor
from tests.supervisor.test_supervisor_production_features import SlowAgent

async def main():
    supervisor = Supervisor()
    slow_agent = SlowAgent()
    supervisor.orchestrator.agents = [slow_agent]
    state = AgentState()
    state.patient_context = {'name': 'Test', 'age': 48, 'gender': 'Female'}
    state.metadata['agent_timeouts'] = {slow_agent.agent_name: 0.001}
    final_state, results, metrics = await supervisor.run(state)
    print('status=', results[0].status)
    print('timeout=', final_state.metadata['timeouts'][slow_agent.agent_name])
    print('total_agents=', metrics.total_agents)
    print('workflow_duration=', final_state.metadata['workflow_duration'])

asyncio.run(main())
