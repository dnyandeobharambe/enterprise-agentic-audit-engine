# 🛡️ Enterprise Agentic Audit Engine

> An autonomous infrastructure compliance system that audits distributed hardware sites, detects firmware violations, and generates remediation plans — with human-in-the-loop governance baked in.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_Orchestration-green)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Gateway-teal?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)](https://docker.com)
[![AgentOps](https://img.shields.io/badge/AgentOps-Observability-orange)](https://agentops.ai)
[![MCP](https://img.shields.io/badge/MCP-Model_Context_Protocol-purple)](https://modelcontextprotocol.io)

---

## The Problem This Solves

Enterprise infrastructure teams — telecoms, data centers, manufacturing — manage hundreds of hardware nodes spread across multiple geographic sites. Auditing these for firmware compliance is a manual, error-prone process that typically consumes **10+ engineering hours per week**.

This engine automates that workflow end-to-end: from live inventory inspection, to policy comparison, to remediation plan generation — while keeping a human in control of every write operation.

> **Built by an architect with hands-on experience managing 15M daily IoT messages for a Tier-1 U.S. telecom operator.** The patterns here — event-driven sensors, governance gates, observability trails — come directly from production infrastructure at scale.

---

## What It Does

Given a natural language query like *"Audit the Kirkland site. If non-compliant, generate a remediation plan"*, the system:

1. **Routes the request** through a FastAPI Gateway that classifies intent (SIMPLE vs AUDIT) using Gemini 2.5 Flash, with NVIDIA NIM as a failover
2. **Dispatches an Audit Agent** (LangGraph state machine) that queries live device inventory via MCP tools
3. **Compares inventory data** against a central compliance policy file
4. **Generates a remediation plan** with step-by-step CLI commands if violations are found
5. **Gates all write operations** behind a human approval click — no automated changes without sign-off
6. **Records every decision** in AgentOps for a full forensic audit trail

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    INTERFACE LAYER                       │
│                   Streamlit UI (:8501)                   │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   GATEWAY LAYER (:8000)                  │
│              FastAPI + SlowAPI Rate Limiting             │
│                         │                               │
│              Intent Classifier (Gemini 2.5)             │
│             [NVIDIA NIM Llama 3.3 — Failover]           │
│                    ┌────┴────┐                           │
│                 SIMPLE     AUDIT                         │
└──────────────────────────────┬──────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│                  EXECUTION TIER                          │
│           LangGraph Audit Agent (State Machine)          │
│                                                          │
│   ┌─ Reasoning Loop ──────────────────────────────┐     │
│   │  call_model → should_continue → tool_node     │     │
│   │       ↑                ↓                      │     │
│   │    [tools: get_inventory | read_policy         │     │
│   │            | plan_remediation]                │     │
│   └───────────────────────────────────────────────┘     │
└──────────────────────────────┬──────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│                   SENSOR LAYER (MCP)                     │
│              MCP Server → SQLite Inventory DB            │
│                       → Policy Text File                 │
└──────────────────────────────┬──────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────┐
│               GOVERNANCE & OBSERVABILITY                 │
│     HITL Safety Gate (approve before any DB write)       │
│     AgentOps — full session replay + compliance trail    │
└─────────────────────────────────────────────────────────┘
```

---

## Key Architecture Decisions (and Why)

This section is intentionally included — architecture is about tradeoffs, not just technology choices.

**Why MCP instead of RAG for the sensor layer?**
Traditional RAG indexes static documents. Infrastructure auditing needs live interaction with device databases and real-time file reads. MCP exposes the SQLite inventory as callable tools (`get_inventory()`, `read_policy()`), allowing the agent to act on live data rather than stale embeddings.

**Why a Gateway instead of direct LLM access?**
Exposing an agent endpoint directly has no rate limiting, no intent classification, and no centralized logging. The FastAPI Gateway enforces per-IP quotas via SlowAPI, routes queries to the right model tier, and feeds everything into AgentOps before it touches the agent — exactly how you'd build this in production.

**Why dual-LLM routing (Gemini + NVIDIA NIM)?**
Cost and resilience. Simple classification tasks (SIMPLE vs AUDIT) don't need a 70B parameter model. Gemini 2.5 Flash handles classification cheaply; NVIDIA NIM Llama 3.1-70B handles the complex audit reasoning. If Gemini's API is unavailable, the gateway automatically fails over to NVIDIA — zero single point of failure.

**Why Human-in-the-Loop on write operations?**
An agent that can autonomously reboot production hardware is a liability, not a feature. HITL gates any DB write behind a manual "Approve & Execute" action in the UI. The agent *recommends* the remediation plan; the human *authorizes* it. This is the only responsible pattern for infrastructure that touches physical systems.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent Orchestration | LangGraph (StateGraph + ToolNode + MemorySaver) |
| Gateway | FastAPI + SlowAPI rate limiting |
| Primary LLM | NVIDIA NIM — Llama 3.1-70B |
| Classifier / Failover | Gemini 2.5 Flash / NVIDIA Gemma 4-31B |
| Sensor Protocol | Model Context Protocol (MCP) |
| Data Store | SQLite (inventory) |
| Observability | AgentOps (session replay, error events, compliance trail) |
| UI | Streamlit |
| Containerization | Docker (ports 8000 + 8501) |

---

## Project Structure

```
enterprise-agentic-audit-engine/
├── gateway.py          # FastAPI gateway — intent routing, rate limiting, failover
├── agent.py            # LangGraph audit agent — state machine + tool binding
├── mcp_server.py       # MCP server — exposes inventory DB and policy as tools
├── main.py             # Application entry point
├── ui.py               # Streamlit frontend — query input + HITL approval UI
├── utils.py            # Shared utilities
├── check_db.py         # Inventory DB health check
├── setup_data.py       # Seeds the SQLite inventory with sample site data
├── data/               # Sample hardware inventory and compliance policy files
├── tests/              # Unit tests
├── Dockerfile          # Multi-service container (gateway :8000 + UI :8501)
└── requirements.txt
```

---

## Quickstart

### Prerequisites
- Docker installed
- API keys for: NVIDIA NIM, Google Gemini, AgentOps

### Run with Docker

```bash
git clone https://github.com/dnyandeobharambe/enterprise-agentic-audit-engine.git
cd enterprise-agentic-audit-engine

# Create your .env file
cp .env.example .env
# Add your NVIDIA_API_KEY, GOOGLE_API_KEY, AGENTOPS_API_KEY

# Build and run
docker build -t audit-engine .
docker run -p 8000:8000 -p 8501:8501 --env-file .env audit-engine
```

Then open:
- **UI:** `http://localhost:8501`
- **API docs:** `http://localhost:8000/docs`

### Seed the inventory database

```bash
python setup_data.py
```

This creates sample hardware sites (Kirkland, Seattle, Bellevue) with firmware versions and compliance states.

### Example Queries

Try these in the Streamlit UI:

```
"Audit the Kirkland site and report on firmware compliance."
"Check all sites for policy violations."
"Audit Bellevue. If non-compliant, generate a remediation plan."
```

---

## Sample Output

When a non-compliant node is found, the agent produces a remediation plan like this:

```
--- AUDIT RESULT: Kirkland Site ---
Node: KRK-NODE-04
Current Firmware: v2.1.3
Required Firmware: v2.3.0
Status: NON-COMPLIANT ❌

--- REMEDIATION PLAN ---
1. Backup configuration: 'save config backup_kirkland_pre_upgrade.cfg'
2. Download image: 'fetch http://repo.internal/fw/v2.3.0.bin'
3. Install: 'system install-firmware --version 2.3.0 --validate'
4. Reboot: 'reload --delayed 5'

[Approve & Execute] ← Human sign-off required before any write operation
```

---

## Observability

Every agent run is fully traced in AgentOps:
- Which tools were called and in what order
- LLM reasoning steps between tool calls
- Judge verdicts (compliance pass/fail decisions)
- Error events and exception traces
- Full session replay for forensic review

This creates a permanent, queryable compliance trail — critical for regulated industries like telecom and healthcare.

---

## What's Next

- [ ] Azure AKS deployment with Kubernetes manifests
- [ ] Webhook integration to push audit alerts to Slack/Teams
- [ ] Swap SQLite for Azure SQL for production-scale inventory
- [ ] Add streaming responses to the Streamlit UI for real-time agent reasoning visibility
- [ ] Export audit reports as PDF with timestamp and approver signature

---

## About the Author

Built by **Danny Bharambe** — Principal AI Architect with a background in designing distributed systems for enterprise telecoms (15M+ daily IoT messages, Tier-1 operator scale). This project applies those infrastructure patterns — sensor layers, governance gates, observability trails — to the emerging domain of Agentic AI.

[LinkedIn](https://linkedin.com/in/dnyandeo) · [GitHub](https://github.com/dnyandeobharambe)
