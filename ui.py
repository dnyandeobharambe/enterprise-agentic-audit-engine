import streamlit as st
import requests
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

st.set_page_config(page_title="Enterprise Audit Engine", layout="wide")

# --- Security Gate ---
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        # Pull secret from .env (e.g., UI_PASSWORD=Architect2026)
        if st.session_state["password"] == os.getenv("UI_PASSWORD"):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password in session
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Secure Access")
        st.text_input("Enter Access Key", type="password", on_change=password_entered, key="password")
        st.info("Authorized personnel only. Access is monitored via AgentOps.")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔐 Secure Access")
        st.text_input("Enter Access Key", type="password", on_change=password_entered, key="password")
        st.error("❌ Invalid Access Key.")
        return False
    return True

# Halt execution if password is not correct
if not check_password():
    st.stop()
# --- End Security Gate ---

st.title("🛡️ Enterprise Agentic Audit Engine")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Session Settings")
    thread_id = st.text_input("Session ID", value="audit_001")
    st.info("Human-in-the-Loop: Review and Approve AI remediation plans.")
    if st.button("Clear Dashboard"):
        if 'last_audit' in st.session_state:
            del st.session_state['last_audit']
        st.rerun()

query = st.text_input("Enter Audit Command:", placeholder="e.g., Audit Kirkland and provide a fix...")

# 1. RUN AUDIT LOGIC
if st.button("Run Audit"):
    if not query:
        st.warning("Please enter a query first.")
    else:
        with st.spinner("Agent is reasoning and Judge is verifying..."):
            try:
                payload = {"query": query, "thread_id": thread_id}
                response = requests.post("http://127.0.0.1:8000/audit", json=payload)
                
                if response.status_code == 200:
                    st.session_state['last_audit'] = response.json()
                elif response.status_code == 429:
                    st.error("Rate limit exceeded.")
                else:
                    st.error(f"Gateway Error: {response.status_code}")
            except Exception as e:
                st.error(f"Could not connect to Gateway: {e}")

# 2. DISPLAY RESULTS
if 'last_audit' in st.session_state:
    data = st.session_state['last_audit']
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Agent Findings")
        st.write(data["content"])
        
        content_lower = data["content"].lower()
        if any(word in content_lower for word in ["non-compliant", "not compliant", "remediate", "remediation"]):
            st.markdown("---")
            st.markdown("### 🛠️ Staged Remediation")
            
            site_match = re.search(r"kirkland", content_lower)
            target_site = site_match.group(0).capitalize() if site_match else "Kirkland"
            
            st.warning(f"AI has generated a fix for **{target_site}**. Review below:")
            cmd = "system upgrade --version 4.2 --validate"
            st.code(cmd, language="bash")
            
            if st.button("✅ Approve & Execute Upgrade"):
                with st.spinner(f"Pushing update to {target_site}..."):
                    exec_payload = {"command": cmd, "site": target_site}
                    try:
                        exec_resp = requests.post("http://127.0.0.1:8000/execute", json=exec_payload)
                        if exec_resp.status_code == 200:
                            st.success(f"Successfully executed: {exec_resp.json()['message']}")
                            st.balloons()
                        else:
                            st.error("Execution failed at the Gateway.")
                    except Exception as e:
                        st.error(f"Execution Error: {e}")

    with col2:
        st.subheader("🛡️ Verification (Judge)")
        v_data = data.get("verification")
        if v_data:
            if v_data["verdict"] == "PASS":
                st.success(f"**STATUS: {v_data['verdict']}**")
            else:
                st.error(f"**STATUS: {v_data['verdict']}**")
            st.info(f"**Reasoning:** {v_data['reason']}")
            