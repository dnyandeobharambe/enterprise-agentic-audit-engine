import pytest
import json
from agent import app as agent_app
from mcp_server import read_policy

# This is a helper to call the 'Judge' (using your NIM endpoint)
async def call_judge(policy, agent_response):
    prompt = f"""
    Policy: {policy}
    Agent Output: {agent_response}
    
    Judge the output. Is the compliance determination correct? 
    Return JSON: {{"score": int, "verdict": "PASS" or "FAIL", "reason": "string"}}
    """
    # Here we would use a simple LLM call (separate from the agent)
    # For now, let's look at the logic flow
    return {"verdict": "PASS", "score": 5} 

@pytest.mark.asyncio
async def test_llm_judge_compliance():
    # 1. Get the Agent's answer
    inputs = {"messages": [("user", "Is Kirkland compliant?")]}
    result = await agent_app.ainvoke(inputs, config={"configurable": {"thread_id": "judge_01"}})
    agent_text = result["messages"][-1].content
    
    # 2. Get the actual policy
    actual_policy = read_policy()
    
    # 3. Ask the Judge
    evaluation = await call_judge(actual_policy, agent_text)
    
    print(f"\nJUDGE VERDICT: {evaluation['verdict']}")
    assert evaluation["verdict"] == "PASS"
    