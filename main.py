import os
from typing import Optional
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# Core Intelligence Imports
from agent import app as agent_app
from mcp_server import read_policy
from langchain_nvidia_ai_endpoints import ChatNVIDIA

# --- 1. Infrastructure Setup ---
# Pull rate limit from .env for HF deployment flexibility
RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "5")

limiter = Limiter(key_func=get_remote_address)
api = FastAPI(title="Enterprise Agentic Audit Gateway")
api.state.limiter = limiter
api.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- 2. Data Contracts (Schemas) ---
class JudgeSchema(BaseModel):
    verdict: str = Field(description="PASS or FAIL")
    reason: str = Field(description="Reasoning for the verdict")

class AuditRequest(BaseModel):
    query: str
    thread_id: str
    user_id: Optional[str] = "default_user"

class AuditResponse(BaseModel):
    status: str
    content: str
    verification: Optional[JudgeSchema] = None

class ExecuteRequest(BaseModel):
    command: str
    site: str

# --- 3. The "Silent Judge" Logic ---
async def call_judge(policy: str, agent_response: str) -> JudgeSchema:
    """Uses a high-reasoning model to verify the agent's work off-screen."""
    # Using Llama 3.3-70B for governance as planned
    judge_llm = ChatNVIDIA(model="meta/llama-3.3-70b-instruct") 
    structured_judge = judge_llm.with_structured_output(JudgeSchema)
    
    prompt = f"""
    You are a Senior Compliance Officer. 
    Compare the Agent's Audit against the Official Policy.
    
    OFFICIAL POLICY:
    {policy}
    
    AGENT'S AUDIT RESPONSE:
    {agent_response}
    
    Is the agent's determination correct based ONLY on the policy? 
    Return a verdict of PASS if correct, or FAIL if the agent hallucinated or missed a violation.
    """
    return await structured_judge.ainvoke(prompt)

# --- 4. Endpoints ---

@api.post("/audit", response_model=AuditResponse)
@limiter.limit(f"{RATE_LIMIT}/minute")
async def run_audit(request: Request, audit_data: AuditRequest):
    # A. Execute Agent Reasoning
    config = {"configurable": {"thread_id": audit_data.thread_id}}
    inputs = {"messages": [("user", audit_data.query)]}
    
    result = await agent_app.ainvoke(inputs, config=config)
    agent_text = result["messages"][-1].content

    # B. The Critical Verification Step
    try:
        policy_text = read_policy()
        # Force the Judge to run
        evaluation = await call_judge(policy_text, agent_text)
        
        # If the LLM returned None or empty for some reason, create a manual fail
        if not evaluation:
            evaluation = JudgeSchema(verdict="ERROR", reason="Judge returned empty response.")
            
    except Exception as e:
        # This will now show up in your UI so you can see the REAL error
        evaluation = JudgeSchema(verdict="ERROR", reason=f"Judge failed: {str(e)}")

    return AuditResponse(
        status="success",
        content=agent_text,
        verification=evaluation
    )

@api.post("/execute")
@limiter.limit("2/minute") # Stricter limit for write operations
async def run_execution(request: Request, exec_data: ExecuteRequest):
    from mcp_server import update_site_firmware
    # Execute the write operation to SQLite
    result = update_site_firmware(exec_data.site, "4.2") 
    return {"status": "success", "message": result}