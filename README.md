<div align="center">

# 🧠 AgentJW — SiCuan AI Partner Bisnis & Platform AI Agent

### Think • Plan • Execute • Reflect • Repair • Learn • Evolve • Scale

[![Version](https://img.shields.io/badge/version-v3.0.0-blue?style=flat-square)]()
[![Production](https://img.shields.io/badge/status-production_ready-brightgreen?style=flat-square)]()
[![Architecture](https://img.shields.io/badge/architecture-Multi_Agent-purple?style=flat-square)]()
[![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)

</div>

---

## 📋 Overview

**AgentJW (SiCuan)** adalah **AI Agent Platform** dan **Autonomous Business Partner** yang dibangun dengan arsitektur multi-agent terinspirasi dari Claude Code.

### 🎯 Kemampuan Inti

| Komponen | Status | Keterangan |
|----------|--------|------------|
| **12 Claude Code Patterns** | ✅ | The Loop, Planning, Sub-Agents, Agent Teams |
| **Multi-LLM Fallback** | ✅ | OpenAI → OpenRouter → NVIDIA NIM → Ollama |
| **Auto-Repair** | ✅ | Generalized Repair Engine |
| **Planning Mode** | ✅ | Step-by-step execution |
| **Sub-Agents** | ✅ | Fresh context per subtask |
| **Agent Teams** | ✅ | Multi-agent collaboration |
| **Worktree Isolation** | ✅ | Each agent has isolated workspace |
| **Persistent Tasks** | ✅ | Disk-based task persistence |
| **Context Compression** | ✅ | Auto-summarize long conversations |
| **Knowledge on Demand** | ✅ | Load knowledge when needed |
| **Background Tasks** | ✅ | Run slow ops in background |
| **Semantic Router** | ✅ | LLM-based intent classification |

---

## 🏗️ Architecture — 12 Claude Code Patterns

```

┌─────────────────────────────────────────────────────────────────────┐
│                         AGENTJW                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    CORE LOOP                                    ││
│  │  User → Brain (think_and_respond) → Action (execute_action)    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    PLANNING LAYER                               ││
│  │  Planning → Sub-Agents → Background Tasks → Persistent Tasks   ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    TEAM LAYER                                   ││
│  │  Agent Teams → Autonomous Agents → Worktree Isolation          ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    LLM CHAIN                                    ││
│  │  OpenAI → OpenRouter → NVIDIA NIM → Ollama (fallback)          ││
│  └─────────────────────────────────────────────────────────────────┘│
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

```

### 🔹 12 Claude Code Patterns Implemented

| # | Pattern | Status | File |
|---|---------|--------|------|
| 1 | The Loop | ✅ | `brain.py` |
| 2 | Tool Dispatch | ✅ | `action_registry.py` |
| 3 | Planning | ✅ | `planning.py` |
| 4 | System Prompt Builder | ✅ | `system_prompt_builder.py` |
| 5 | Sub-Agents | ✅ | `sub_agent.py` |
| 6 | Persistent Tasks | ✅ | `persistent_tasks.py` |
| 7 | Context Compression | ✅ | `context_compressor.py` |
| 8 | Knowledge on Demand | ✅ | `knowledge_loader.py` |
| 9 | Background Tasks | ✅ | `background_tasks.py` |
| 10 | Agent Teams | ✅ | `agent_team.py` |
| 11 | Autonomous Agents | ✅ | `agent_team.py` |
| 12 | Worktree Isolation | ✅ | `agent_team.py` |

---

## 🚀 Fitur Utama

### 🔹 Multi-LLM Fallback Chain
| Layer | Provider | Status |
|-------|----------|--------|
| 1 | OpenAI | ✅ |
| 2 | OpenRouter | ✅ |
| 3 | NVIDIA NIM | ✅ |
| 4 | Ollama (local) | ✅ |

### 🔹 Agents
| Agent | Fungsi | Status |
|-------|--------|--------|
| **Planner** | Step-by-step planning | ✅ |
| **Sub-Agent** | Fresh context per subtask | ✅ |
| **Agent Teams** | Multi-agent collaboration | ✅ |
| **Autonomous Agent** | Self-working without supervision | ✅ |
| **Repair Agent** | Generalized repair engine | ✅ |

### 🔹 Tools
- `planning.py` — Planning mode with step tracking
- `sub_agent.py` — Sub-agent with isolated context
- `agent_team.py` — Agent teams + worktree isolation
- `persistent_tasks.py` — Disk-based task persistence
- `context_compressor.py` — Auto-summarize long conversations
- `knowledge_loader.py` — Load knowledge when needed
- `background_tasks.py` — Run slow ops in background

---

## 📂 Repository Structure

```

agentjw/
├── core/
│   └── llm_client.py          # Multi-LLM with fallback chain
├── sicuan/
│   ├── brain.py               # Core agent loop
│   ├── chat.py                # Chat handler
│   ├── core/
│   │   ├── planning.py        # Planning mode
│   │   ├── sub_agent.py       # Sub-agent system
│   │   ├── agent_team.py      # Agent teams + worktree
│   │   ├── persistent_tasks.py # Task persistence
│   │   ├── context_compressor.py # Context compression
│   │   ├── knowledge_loader.py # Knowledge on demand
│   │   ├── background_tasks.py # Background tasks
│   │   ├── system_prompt_builder.py # Dynamic prompt assembly
│   │   ├── semantic_router.py # LLM-based routing
│   │   └── generalized_repair.py # Auto-repair engine
│   └── actions/               # 21 actions
├── agents/
│   └── orchestrator.py        # Agent orchestrator
├── memory/
│   ├── workspaces/            # Per workspace data
│   ├── users/                 # User data
│   └── worktrees/             # Worktree isolation
└── projects/
└── godmeme_bot/           # Example project

```

---

## 🧪 Test Results

| Test | Status | Keterangan |
|------|--------|------------|
| Chat | ✅ | Respons berhasil |
| Auto-Repair | ✅ | Generalized repair engine |
| Planning | ✅ | Step-by-step execution |
| Sub-Agent | ✅ | Fresh context per subtask |
| Agent Team | ✅ | Multi-agent collaboration |
| Semantic Router | ✅ | LLM-based routing |
| Memory Extraction | ✅ | JSON fallback |
| Fallback Chain | ✅ | OpenAI → OpenRouter → NVIDIA NIM → Ollama |

---

## 📦 Installation

```bash
git clone https://github.com/XdibsAI/Agentjw.git
cd Agentjw

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy .env
cp .env.example .env
# Edit .env with your API keys
```

---

▶ Run

Telegram Bot (Production)

```bash
sudo systemctl start sicuan-telegram.service
```

CLI Chat

```bash
python3 main.py chat "halo cu"
```

Interactive CLI

```bash
python3 main.py
```

---

🛠️ Commands

Telegram Commands

Command Fungsi
/start Start bot, show user ID
/status Status bot
/metrics Metrics dashboard (owner only)

User Commands

Command Fungsi
@godmemeku_bot list project List project di workspace
@godmemeku_bot auto-repair godmeme Auto-repair project
@godmemeku_bot buat plan untuk ... Planning mode
@godmemeku_bot status godmeme Cek status trading
@godmemeku_bot analyze godmeme Analisis project

---

🔑 Environment Variables

```env
# LLM
OPENROUTER_API_KEY=sk-...
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# NVIDIA NIM (fallback)
NVIDIA_NIM_API_KEY=...
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=meta/llama-3.1-70b-instruct

# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
OWNER_USER_ID=...

# Platform
MASTER_ENCRYPTION_KEY=...
DEFAULT_PLAN=free
```

---

📄 License

MIT License

---

<div align="center">

Built by XdibsAI

AgentJW — Autonomous AI Agent Platform

Production Ready 🚀

</div>
