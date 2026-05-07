import pytest
from agent import app as agent_app

@pytest.mark.asyncio
async def test_kirkland_compliance_logic():
    # Input simulating a user asking about the specific site
    inputs = {"messages": [("user", "Is Kirkland site compliant?")]}
    config = {"configurable": {"thread_id": "pytest_session_001"}}
    
    # Run the graph
    result = await agent_app.ainvoke(inputs, config=config)
    output = result["messages"][-1].content
    
    # The 'Hard STEM' check
    assert "not compliant" in output.lower()
    assert "3.9" in output
    assert "4.2" in output
    