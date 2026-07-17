<div align="center">

# 🧠 AgentJW — Autonomous AI Agent Platform & Business Partner

### Think • Plan • Execute • Reflect • Repair • Learn • Evolve • Scale

[![Version](https://img.shields.io/badge/version-v1.0.0-blue?style=flat-square)]()
[![Production](https://img.shields.io/badge/status-production_ready-brightgreen?style=flat-square)]()
[![Architecture](https://img.shields.io/badge/architecture-Multi_Agent-purple?style=flat-square)]()
[![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)
[![Burn-in](https://img.shields.io/badge/burn--in-passed-success?style=flat-square)]()
[![Stability](https://img.shields.io/badge/stability-stable-brightgreen?style=flat-square)]()

</div>

---

## 📋 Overview

**AgentJW v1.0.0** adalah **AI Agent Platform** dan **Autonomous Business Partner** yang telah melalui 4-day burn-in test dan siap digunakan di produksi.

### 🏆 Status Release

| Metrik | Target | Aktual | Status |
|--------|--------|--------|--------|
| Health Score | >90 | 97/100 | ✅ |
| Automation Rate | >85% | 96% | ✅ |
| Workflow Success | >95% | 96.1% | ✅ |
| Recovery Rate | >95% | 95.5% | ✅ |
| MTTR | <5s | 1.9s | ✅ |
| Uptime | >99% | 100% | ✅ |

### 🎯 Kemampuan Inti

| Komponen | Status | Keterangan |
|----------|--------|------------|
| **CEO Agent** | ✅ | Strategic decision-making with health scoring |
| **Production Metrics** | ✅ | MTBF, MTTR, Knowledge Reuse tracking |
| **Permission Engine** | ✅ | Role-based access control (Admin, Developer, Viewer) |
| **Customer OS** | ✅ | CRM, Customer, Sales, Support, Manager agents |
| **Workflow Engine** | ✅ | Multi-step workflow execution |
| **Brain & Chat** | ✅ | Central intelligence with conversational interface |
| **Monitoring Dashboard** | ✅ | Real-time health and metrics visualization |
| **Recovery Engine** | ✅ | Automatic crash recovery (95.5% success) |

---

## 🏗️ Architecture — Multi-Agent System

```

┌─────────────────────────────────────────────────────────────────────┐
│                         AGENTJW v1.0.0                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    CEO AGENT                                    ││
│  │  Strategic Decisions • Health Scoring • ROI Prediction         ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    CORE LAYER                                   ││
│  │  Workflow Engine • Permission Engine • Production Metrics      ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    CUSTOMER OS                                  ││
│  │  CRM • Customer • Sales • Support • Manager                    ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    BRAIN & CHAT                                 ││
│  │  Think_and_Respond • Route_Message • Execute_Plan             ││
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

---

## 🚀 Fitur Utama v1.0.0

### 🔹 CEO Agent
- **Health Score**: 0-100 composite scoring (Workflow 40%, Recovery 30%, LLM 30%)
- **Automation Rate**: Track autonomous operations
- **Priority Scoring**: Multi-factor project prioritization
- **ROI Prediction**: Investment return forecasting

### 🔹 Production Metrics
- **MTBF & MTTR**: Mean Time Between Failures and Mean Time To Recovery
- **Knowledge Reuse**: Track knowledge base effectiveness
- **LLM Performance**: Latency, token usage, and cost tracking
- **Health Score**: Real-time system health monitoring

### 🔹 Permission Engine
| Role | Permissions |
|------|-------------|
| **Admin** | Full access (all actions) |
| **Developer** | Read/Write code, Execute workflows, Deploy staging |
| **Viewer** | Read dashboard and metrics only |

### 🔹 Customer OS Agents
| Agent | Fungsi | Status |
|-------|--------|--------|
| **CRM Agent** | Full customer relationship management | ✅ |
| **Customer Agent** | Individual customer handling with history | ✅ |
| **Manager Agent** | Team coordination and oversight | ✅ |
| **Sales Agent** | Pipeline and sales operations | ✅ |
| **Support Agent** | Ticket management and resolution | ✅ |

### 🔹 Testing & Monitoring
- **Unit Tests**: 5/5 passing ✅
- **Regression Suite**: 6/6 passing ✅
- **Burn-in Test**: 4 days (96 hours) ✅
- **Monitoring Dashboard**: Real-time status ✅
- **Health Check**: Available ✅

---

## 📂 Repository Structure

```

agentjw/
├── core/
│   ├── llm_client.py          # Multi-LLM with fallback chain
│   └── ...
├── sicuan/
│   ├── brain.py               # Core agent loop with 50+ methods
│   ├── chat.py                # Chat with context management
│   ├── core/
│   │   ├── ceo_agent.py       # Strategic decision-making
│   │   ├── production_metrics.py # MTBF, MTTR tracking
│   │   ├── permission_engine.py # Role-based access control
│   │   ├── workflow_engine.py # Multi-step workflow execution
│   │   ├── config.py          # Centralized configuration
│   │   ├── models.py          # Data models
│   │   ├── router.py          # Request routing
│   │   ├── crm_agent.py       # Customer relationship management
│   │   ├── customer_agent.py  # Individual customer handling
│   │   ├── manager_agent.py   # Team coordination
│   │   ├── sales_agent.py     # Sales operations
│   │   └── support_agent.py   # Support tickets
│   └── ...
├── tests/
│   ├── unit/                  # Unit tests (5/5 passing)
│   ├── regression/            # Regression suite (6/6 passing)
│   └── burn_in/               # Burn-in monitoring tools
├── memory/
│   ├── production_metrics.json # Single source of truth
│   └── ...
└── RELEASE_NOTES_v1.0.0.md    # Full release documentation

```

---

## 🧪 Test Results

| Test Suite | Status | Keterangan |
|------------|--------|------------|
| Unit Tests | ✅ 5/5 | Permission Engine, Production Metrics |
| Integration Tests | ✅ 6/6 | Core components integration |
| Permission Tests | ✅ | RBAC working correctly |
| Recovery Tests | ✅ | 95.5% recovery rate |
| Smoke Tests | ✅ | Critical services operational |
| Burn-in Test | ✅ | 4 days (96 hours) stable |

---

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/XdibsAI/Agentjw.git
cd Agentjw

# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Start the system
python3 main.py
```

---

🚀 Quick Commands

Start System

```bash
python3 main.py
```

Monitoring Dashboard

```bash
python3 tests/burn_in/dashboard.py
```

Health Check

```bash
./tests/burn_in/health_check.sh
```

Run Regression Tests

```bash
python3 tests/regression/suite.py
```

API Health

```bash
curl http://localhost:18791/health
```

Chat with AgentJW

```bash
python3 -c "from sicuan.chat import get_chat_session; chat=get_chat_session(); print(chat.chat('Hello'))"
```

---

🔑 Environment Variables

```env
# LLM Providers
OPENROUTER_API_KEY=sk-...
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1

# NVIDIA NIM (fallback)
NVIDIA_NIM_API_KEY=...
NVIDIA_NIM_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_NIM_MODEL=meta/llama-3.1-70b-instruct

# Telegram (optional)
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
OWNER_USER_ID=...

# Security
MASTER_ENCRYPTION_KEY=...
DEFAULT_PLAN=free
```

---

🎯 Roadmap

```
✅ v0.8.0  → Customer OS (Released)
✅ v0.9.8  → Burn-in Passed (4 days)
✅ v1.0.0  → Stable Release (Current)
⏳ v1.1.0  → Multi-Workspace
⏳ v1.2.0  → Plugin Marketplace
⏳ v1.3.0  → Cloud Edition
⏳ v2.0.0  → AgentJW Platform
```

---

📄 License

MIT License

---

<div align="center">

AgentJW v1.0.0 — Production Ready 🚀

Built by XdibsAI

⭐ Star this repository if you find it useful!

</div>
