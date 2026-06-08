<div align="center">

# 🤖 AgentJW

### Autonomous GOD MODE AI Agent

*Think · Plan · Build · Repair · Evolve · Remember*

[![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)](https://python.org)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Powered-orange?style=flat-square)](https://openrouter.ai)
[![FastAPI](https://img.shields.io/badge/FastAPI-REST%20API-green?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)

</div>

---

## 🧠 What is AgentJW?

AgentJW is an autonomous AI software engineer built for real-world deployment on a Linux VPS. It orchestrates multi-agent workflows powered by OpenRouter, with persistent memory, MCP tool integration, swarm intelligence, self-repair capabilities, and a built-in **AI Video Production Studio**.

---

## ⚡ Features

### 🤖 Multi-Agent Orchestration (GOD MODE)
| Agent | Role |
|-------|------|
| **Orchestrator** | Routes intent, coordinates all agents |
| **Planner** | Breaks tasks into structured project plans |
| **Coder** | Generates production-ready code |
| **Critic** | Evaluates quality and catches issues |
| **Reviewer** | Final review before delivery |
| **Repair** | Auto-detects and fixes broken code |
| **Memory** | Persistent context across sessions |

### 🎬 Video Studio
Generate full YouTube production packages from a single prompt:
- **Script** — Bilingual VO (English + Indonesian subtitle) with director notes
- **Scenes** — Higgsfield AI cinematic prompts per scene
- **Voice** — ElevenLabs voice direction with emotional cues
- **Sound** — Timestamped sound design plan
- **Editing** — Cut timing, transitions, text overlays
- **Thumbnails** — 3 CTR-optimized concepts (1280×720)

### 🔧 MCP Tool Integration
- Filesystem tools (read, scan, hash, execute)
- OpenClaw gateway
- Extensible external MCP server support

### 🐝 Swarm Intelligence
- Parallel multi-agent solution generation
- Voting mechanism for best output selection

### 💾 Persistent Memory
- SQLite-backed project registry
- ChromaDB vector memory
- Cross-session context retention

### 🌐 REST API
Full FastAPI server exposing all capabilities:
```
POST /chat              → Chat with AgentJW
POST /build             → Trigger autonomous build
POST /video/package     → Generate full video package (async)
POST /video/section     → Generate single video section
POST /video/parse-jsx   → Parse Claude JSX production package
GET  /video/jobs/{id}   → Poll background job status
GET  /projects          → List all projects
```

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/XdibsAI/Agentjw.git
cd Agentjw
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
nano .env
```

```env
# Required — pick one LLM provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Required for Video Studio
OPENROUTER_API_KEY=sk-or-v1-...
VIDEO_STUDIO_MODEL=deepseek/deepseek-r1-0528:free
```

### 3. Run
```bash
# Interactive CLI
python main.py

# Or single command
python main.py chat "build me a crypto trading bot"
python main.py build "YouTube analytics dashboard"
```

---

## 💬 CLI Commands

```bash
# Chat naturally
⚡ agentjw > build a Flask REST API with auth

# Build commands
⚡ agentjw > build trading bot for Binance with RSI strategy
⚡ agentjw > build youtube auto-upload tool

# Swarm mode (3 agents + voting)
⚡ agentjw > build+ a crypto sniper bot for Solana

# Video Studio
⚡ agentjw > video status
⚡ agentjw > video How AI Will Destroy 50% of Jobs by 2030
⚡ agentjw > video section script My video topic here
⚡ agentjw > video projects

# Project management
⚡ agentjw > projects
⚡ agentjw > repair <project-id>
⚡ agentjw > scan <project-id>

# MCP tools
⚡ agentjw > mcp tools
⚡ agentjw > check token <solana-address>
```

---

## 🌐 API Server

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

**Generate video package via API:**
```bash
curl -X POST http://localhost:8000/video/package \
  -H "Content-Type: application/json" \
  -d '{
    "title": "How AI Will Destroy 50% of Jobs by 2030",
    "duration": "12-15",
    "lang": "bilingual",
    "style": "cinematic documentary",
    "tone": "confident, urgent, no fluff"
  }'

# Returns job_id — poll for result:
curl http://localhost:8000/video/jobs/{job_id}
```

---

## 🏗️ Architecture

```
agentjw/
├── agents/
│   ├── orchestrator.py      ← GOD MODE router + coordinator
│   ├── planner_agent.py     ← Project planning
│   ├── coder_agent.py       ← Code generation
│   ├── critic_agent.py      ← Quality evaluation
│   ├── reviewer_agent.py    ← Final review
│   ├── repair_agent.py      ← Auto-repair
│   ├── memory_agent.py      ← Context management
│   ├── specialist/          ← Repair specialist
│   └── workflow/            ← Agent dialog & runner
├── tools/
│   ├── video/               ← 🎬 Video Studio
│   │   ├── video_studio_tool.py
│   │   └── openrouter_client.py
│   ├── trading/             ← Trading bot builder
│   ├── youtube/             ← YouTube automation builder
│   └── project_manager/     ← Project registry
├── core/
│   ├── config.py            ← Central config + env
│   ├── llm_client.py        ← OpenAI + Anthropic client
│   ├── models.py            ← Pydantic data models
│   └── logger.py            ← Rich logging
├── mcp/                     ← MCP tool integration
├── memory/                  ← SQLite + ChromaDB
├── swarm/                   ← Parallel agent swarm
├── runtime/                 ← Code execution + AST validator
├── api_server.py            ← FastAPI REST server
└── main.py                  ← Entry point
```

---

## 🤖 Supported Models (via OpenRouter)

| Model | Use Case |
|-------|----------|
| `deepseek/deepseek-r1-0528:free` | Video Studio (free, powerful) |
| `deepseek/deepseek-chat-v3-0324:free` | General coding (free) |
| `meta-llama/llama-3.3-70b-instruct:free` | Chat + planning (free) |
| `openai/gpt-4o` | Premium coding |
| `anthropic/claude-sonnet-4-5` | Premium reasoning |
| `qwen/qwen3-coder` | Coding specialist |

---

## 📋 Requirements

```
Python 3.12+
FastAPI + Uvicorn
OpenAI SDK / Anthropic SDK
SQLite (built-in)
ChromaDB
Rich (terminal UI)
Prompt Toolkit
Requests
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">

Built by [@XdibsAI](https://github.com/XdibsAI) · Powered by [OpenRouter](https://openrouter.ai)

