<div align="center">

# 🤖 AgentJW V2

### Autonomous Executive Brain AI Software Engineer

*Think • Plan • Execute • Reflect • Repair • Learn • Evolve*

[![Version](https://img.shields.io/badge/version-v2.0.1-blue?style=flat-square)]()
[![Production](https://img.shields.io/badge/status-production_ready-brightgreen?style=flat-square)]()
[![Architecture](https://img.shields.io/badge/architecture-Executive_Brain-purple?style=flat-square)]()
[![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)](https://python.org)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Powered-orange?style=flat-square)](https://openrouter.ai)
[![License](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE)

</div>

---

# 🧠 Overview

AgentJW V2 adalah Autonomous AI Software Engineering Agent yang dibangun untuk berjalan penuh di Linux VPS.

Versi V2 memperkenalkan Executive Brain Architecture yang menggantikan pendekatan IF-ELIF tradisional menjadi workflow berbasis Planner DAG, Reflection, Runtime Bus, dan Generic Executor.

AgentJW mampu:

- memahami project
- melakukan analisis kode
- memperbaiki bug
- memodifikasi logic
- menjalankan build
- menjalankan bot
- melakukan evaluasi hasil
- belajar dari workflow sebelumnya

---

# 🚀 Executive Brain Architecture

```
User
   │
   ▼
Executive Brain
   │
   ▼
Planner DAG
   │
   ▼
Executor Engine
   │
   ▼
Action Registry
   │
   ▼
Specialist Actions
   │
   ▼
Reflection Engine
```

Seluruh workflow diproses melalui Executive Brain.

---

# ⚙ Core Components

- Executive Brain
- Planner DAG
- Executor Engine
- Runtime Bus
- Workflow Context
- Reflection Engine
- Result Contract
- Action Registry
- Shadow Mode
- Continuous Learning
- Observability Dashboard

---

# 🎯 Core Actions

- scan_project
- analyze_project
- trace_code
- modify_logic
- repair_project
- build_project
- modify_project
- get_file
- run_bot
- list_projects
- show_log
- project_summary

Semua action menggunakan Generic Executor.

---

# 🔦 Shadow Mode

Shadow Mode menjalankan Executive Brain dan Legacy Executor secara paralel.

Status pilot:

- Overall Match Rate : **80.6%**
- Core Actions Match : **100%**

Core actions yang sudah 100%:

- scan_project
- analyze_project
- trace_code
- modify_logic
- repair_project
- build_project
- modify_project
- get_file
- run_bot
- list_projects

---

# 📊 Pilot Production Result

Hasil pilot production:

| Metric | Result |
|--------|---------|
| Workflow Success Rate | **98%** |
| Retry Rate | **4%** |
| Average Confidence | **92%** |
| Health Score | **100/100** |
| Shadow Match (Core) | **100%** |

---

# 🩺 Observability

AgentJW Doctor Dashboard menyediakan monitoring realtime:

- Workflow statistics
- Planner performance
- Reflection confidence
- Retry metrics
- Runtime memory
- Token usage
- Health score
- Action performance
- Shadow Mode comparison

Jalankan:

```bash
python3 agentjw_doctor.py
```

---

# 📚 Continuous Learning

Continuous Learning menggunakan workflow nyata untuk:

- Planner optimization
- Reflection calibration
- Retry optimization
- Token optimization
- Cost optimization

Dataset tersimpan pada:

```
datasets/
```

---

# 🌐 REST API

AgentJW menyediakan REST API melalui FastAPI.

Contoh:

```
POST /chat
POST /build
POST /video/package
GET  /projects
```

---

# 📂 Repository Structure

```
agentjw/
├── agents/
├── memory/
├── projects/
├── sicuan/
│   ├── actions/
│   ├── core/
│   └── tools/
├── datasets/
├── api_server.py
└── main.py
```

---

# 📦 Installation

```bash
git clone https://github.com/XdibsAI/Agentjw.git
cd Agentjw

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

# ▶ Run

CLI

```bash
python main.py
```

Doctor Dashboard

```bash
python3 agentjw_doctor.py
```

API

```bash
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

---

# 🛣 Roadmap

- Executive Brain Optimization
- Planner Accuracy Improvement
- Shadow Mode ≥95%
- Continuous Learning V2
- Autonomous Multi-Agent Collaboration

---

# 📄 License

MIT License

---

<div align="center">

Built by **XdibsAI**

AgentJW V2 — Executive Brain Architecture

Production Ready 🚀

</div>

## 📋 Version History

| Version | Date | Changes |
|---------|------|---------|
| **v2.1.1** | 2026-06-28 | Documentation & cleanup, add ROADMAP.md, move unused files to archive |
| **v2.1.0** | 2026-06-28 | Remove backup files, clean __pycache__, update .gitignore |
| **v2.0.1** | 2026-06-27 | README rewrite, cleanup backup files |
| **v2.0.0** | 2026-06-26 | Executive Brain architecture, 100% core actions match |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- Issues: [GitHub Issues](https://github.com/XdibsAI/Agentjw/issues)
- Documentation: [Wiki](https://github.com/XdibsAI/Agentjw/wiki)

## ⚠️ Disclaimer

AgentJW V2 is designed as an AI assistant for software engineering tasks. 
Always review code changes before deployment. 
The creator is not responsible for any damages or losses caused by the use of this software.

