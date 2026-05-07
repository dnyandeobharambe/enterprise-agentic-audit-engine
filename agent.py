import os
from dotenv import load_dotenv
from typing import Annotated, TypedDict, Literal
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool

# Load keys from .env
load_dotenv()

import agentops

# 1. Define the "Audit State"
class AgentState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]

# 2. Define our Sensors (Tools)
from mcp_server import get_inventory, read_policy

@tool
def plan_remediation(site: str, current_version: str, target_version: str):
    """
    Generates the technical CLI commands to upgrade firmware for a specific site.
    Call this when a node is found to be non-compliant.
    """
    return f"""
    --- REMEDIATION PLAN FOR {site} ---
    1. Backup configuration: 'save config backup_{site}_pre_upgrade.cfg'
    2. Download Image: 'fetch http://repo.internal/fw/v{target_version}.bin'
    3. Install: 'system install-firmware --version {target_version} --validate'
    4. Reboot: 'reload --delayed 5'
    """

# Add the new remediation tool to the set
tools = [get_inventory, read_policy, plan_remediation]
tool_node = ToolNode(tools)

# 3. Setup the Brain (NVIDIA NIM)
# Note: Using a robust model to ensure complex planning logic is sound
llm = ChatNVIDIA(model="meta/llama-3.1-70b-instruct")
llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)

# 4. Logic Functions
def should_continue(state: AgentState) -> Literal["tools", END]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

def call_model(state: AgentState):
    try:
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}
    except Exception as e:
        agentops.record(agentops.ErrorEvent(message=str(e)))
        raise e

# 5. Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

checkpointer = MemorySaver()
app = workflow.compile(checkpointer=checkpointer)

# Initialize AgentOps
agentops.init(api_key=os.getenv("AGENTOPS_API_KEY"), tags=['Audit-Agent-Remediation'])

if __name__ == "__main__":
    config = {"configurable": {"thread_id": "audit_remediation_001"}}
    
    # Updated query to trigger the planning logic
    query = "Audit the Kirkland site. If it is non-compliant, generate a remediation plan."
    
    inputs = {"messages": [("user", query)]}
    
    for event in app.stream(inputs, config=config):
        for value in event.values():
            print(f"--- Agent Step ---")
            value["messages"][-1].pretty_print()
    
    agentops.end_trace(end_state='Success')
    