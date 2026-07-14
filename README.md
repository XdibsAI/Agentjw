<div align="center">

# 🧠 SiCuan — AI Partner Bisnis & Platform AI Agent

### Think • Plan • Execute • Reflect • Repair • Learn • Evolve • Scale

[![Version](https://img.shields.io/badge/version-v2.1.0-blue?style=flat-square)]()
[![Production](https://img.shields.io/badge/status-production_ready-brightgreen?style=flat-square)]()
[![Architecture](https://img.shields.io/badge/architecture-Multi_Workspace-purple?style=flat-square)]()
[![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-SaaS-orange?style=flat-square)]()
[![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)

</div>

---

## 📋 Overview

**SiCuan** (Si Paling Cuan) adalah **AI Partner Bisnis** dan **Platform AI Agent Multi-Workspace** yang dibangun di atas VPS dengan 12 vCPU dan 48GB RAM.

### 🎯 Kemampuan Inti

| Komponen | Status | Keterangan |
|----------|--------|------------|
| **Multi-Workspace** | ✅ | Isolasi data per user/chat |
| **Telegram Bot** | ✅ | Group & private chat |
| **Coder Agent** | ✅ | Generate & repair code |
| **Reviewer Agent** | ✅ | Code review dengan AST |
| **Analyzer Agent** | ✅ | Data & trading analysis |
| **Repair Agent** | ✅ | Deterministic + AI repair |
| **Multi-Model** | ✅ | 7 model spesialis |
| **Context Memory** | ✅ | Per workspace memory |
| **Billing** | ✅ | Quota based |

---

## 🏗️ Architecture

```

User
│
▼
Telegram Gateway
│
▼
Workspace Resolver
│
▼
┌─────────────────────────────────────────────┐
│           Workspace Runtime                  │
│  ┌─────────────────────────────────────────┐ │
│  │           Event Bus                      │ │
│  │  ┌───────────────────────────────────┐  │ │
│  │  │          Job Queue                │  │ │
│  │  │  ┌─────────────────────────────┐  │  │ │
│  │  │  │   Agents (Coder, Reviewer,  │  │  │ │
│  │  │  │   Analyzer, Repair)         │  │  │ │
│  │  │  └─────────────────────────────┘  │  │ │
│  │  └───────────────────────────────────┘  │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
│
▼
Response

```

---

## 🚀 Fitur Utama

### 🔹 Multi-Workspace
- Setiap user/chat punya workspace sendiri
- Data terisolasi (project, memory, context)
- Auto-create workspace
- 100+ workspace support

### 🔹 Agents
| Agent | Fungsi | Status |
|-------|--------|--------|
| **CoderAgent** | Generate, modify, repair code | ✅ |
| **ReviewerAgent** | Code review dengan AST | ✅ |
| **AnalyzerAgent** | Data & trading analysis | ✅ |
| **RepairAgent** | Deterministic + AI repair | ✅ |

### 🔹 Multi-Model Routing
| Role | Model | Fungsi |
|------|-------|--------|
| Coder | qwen/qwen3-coder | Generate & repair code |
| Reviewer | openai/gpt-4-turbo | Code review & validation |
| Planner | anthropic/claude-3.5-sonnet | Planning & strategy |
| Analyzer | x-ai/grok-2-1212 | Data analysis & pattern |
| Vision | google/gemini-2.0-flash-exp | Image analysis |
| Chat | deepseek/deepseek-chat | Conversation |
| Fast | deepseek/deepseek-chat | Quick responses |

### 🔹 Platform
- **Workspace Manager**: Create, list, delete workspace
- **Project Manager**: Create, list project per workspace
- **Billing**: Quota based (free: 10.000 token/bulan)
- **Secret Vault**: Encrypted API keys
- **Runtime**: Per workspace runtime
- **Event Bus**: Decoupled communication
- **Job Queue**: Async task processing
- **Provider Failover**: Auto switch if provider fails

### 🔹 Telegram Bot
- Multi-workspace support
- Auto-register user
- Mention-based (`@godmemeku_bot` or `cuan`)
- Command: `/start`, `/metrics`, `/admin`, `/status`
- Privacy: Sensitive data only in private chat

---

## 📂 Repository Structure

```

agentjw/
├── sicuan/
│   ├── platform/          # Multi-workspace platform
│   │   ├── workspace.py
│   │   ├── runtime.py
│   │   ├── billing.py
│   │   ├── vault.py
│   │   ├── event_bus.py
│   │   ├── job_queue.py
│   │   ├── admin.py
│   │   ├── metrics.py
│   │   └── provider_failover.py
│   ├── agents/            # AI Agents
│   │   ├── coder_agent.py
│   │   ├── reviewer_agent.py
│   │   ├── analyzer_agent.py
│   │   └── repair_agent.py
│   ├── core/              # Core utilities
│   │   ├── user_manager.py
│   │   ├── intent_engine.py
│   │   └── dispatcher.py
│   ├── actions/           # Actions
│   └── tests/             # Test suite
├── memory/
│   ├── workspaces/        # Per workspace data
│   ├── users/             # User data
│   ├── metrics/           # Metrics
│   └── backups/           # Backups
├── projects/              # Projects
└── logs/                  # Logs

```

---

## 🧪 Test Results

| Test | Status | Keterangan |
|------|--------|------------|
| Isolation Test | ✅ | Data terisolasi per workspace |
| Parallel Job Test | ✅ | Queue per workspace |
| Stress Test | ✅ | 100 workspaces, 1000 jobs |
| Recovery Test | ✅ | 104 workspaces recovered |
| Routing Accuracy | ✅ | 96% (150+ prompts) |

---

## 📊 Performance

| Metric | Result |
|--------|--------|
| Workspaces | 100+ |
| Jobs | 1000+ processed |
| Avg Job Time | 0.104s |
| Recovery | 100% |
| Routing Accuracy | 96% |

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
python3 main.py
```

API Server

```bash
uvicorn api_server:app --host 0.0.0.0 --port 18790
```

---

🛠️ Commands

Telegram Commands

Command Fungsi
/start Start bot, show user ID
/status Status bot
/metrics Metrics dashboard (owner only)
/admin Admin console (owner only)

User Commands

Command Fungsi
@godmemeku_bot list project List project di workspace
@godmemeku_bot buat project <nama> Buat project baru
@godmemeku_bot review kode strategy.py Review code
@godmemeku_bot buat fungsi python Generate function
@godmemeku_bot analisis trading Analyze trading data

---

🔑 Environment Variables

```env
# LLM
OPENROUTER_API_KEY=sk-...
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...

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

SiCuan — AI Partner Bisnis & Platform AI Agent

Production Ready 🚀

</div>
