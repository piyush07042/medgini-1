import asyncio
from app.api.chat import _build_chat_reply, _build_rag_sources
from app.agents.base.agent_state import AgentState
from app.core.rag import seed_sample_guidelines, query_knowledge_base

async def test_stroke_chat():
    # 1. Seed data
    seed_sample_guidelines()
    
    # 2. Query knowledge base for stroke
    question = "List 5 common risk factors for stroke. For each risk factor, provide the exact source document used to support the statement."
    knowledge_results = query_knowledge_base(question, n_results=5)
    
    # 3. Create mock AgentState
    state = AgentState()
    state.knowledge_results = knowledge_results
    
    # 4. Test chat reply generation
    reply, cited_sources = _build_chat_reply(state, user_message=question)
    sources = _build_rag_sources(state, cited_sources)
    
    print("="*50)
    print("REPLY:")
    print(reply)
    print("="*50)
    print("CITED SOURCES:")
    print(cited_sources)
    print("="*50)
    print("FORMATTED SOURCES:")
    print(sources)
    
if __name__ == "__main__":
    asyncio.run(test_stroke_chat())
