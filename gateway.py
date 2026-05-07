import os
from google import genai  # Import the base package
from google.genai import types  # Useful for structured data later
from openai import OpenAI
from dotenv import load_dotenv
from agent import AuditorAgent
import agentops


load_dotenv()

# Initialize Observability
agentops.init(api_key=os.getenv("AGENTOPS_API_KEY"), default_tags=["Gateway"])

class Gateway:
    def __init__(self):
        # New Google SDK Initialization
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model_id = "gemini-2.5-flash" # Use the stable 2026 workhorse

        self.nv_client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY")
        )
        self.auditor = AuditorAgent()

    def route_query(self, user_input: str):
        prompt = (
            "Classify as 'SIMPLE' or 'AUDIT'. "
            "SIMPLE: Greetings, math, general info. "
            "AUDIT: Hardware, firmware, inventory, policy. "
            f"Input: {user_input}"
        )
        
        try:
            # New SDK syntax
            response = self.client.models.generate_content(
                model=self.model_id, contents=prompt
            )
            intent = response.text.strip().upper()
        except Exception as e:
            print(f"Failover to NVIDIA: {e}")
            response = self.nv_client.chat.completions.create(
                model="google/gemma-4-31b-it",
                messages=[{"role": "user", "content": prompt}]
            )
            intent = response.choices[0].message.content.strip().upper()

        if "AUDIT" in intent:
            # Instead of returning a string, call the Auditor
            print(f"DEBUG: Routing '{user_input}' to Auditor Agent...")
            return self.auditor.perform_audit(user_input)

    def handle_simple(self, user_input: str):
        response = self.client.models.generate_content(
            model=self.model_id, contents=user_input
        )
        return response.text

if __name__ == "__main__":
    current_trace = agentops.start_trace("Gateway-Test-Run")
    gateway = Gateway()
    print("--- Testing Gateway Logic ---")
    print(f"Math Test: {gateway.route_query('What is 15% of 200?')}")
    print(f"Audit Test: {gateway.route_query('Check for firmware mismatches.')}")
    
    # Updated to follow deprecation warning
    agentops.end_trace(trace_context=current_trace, end_state="Success")
