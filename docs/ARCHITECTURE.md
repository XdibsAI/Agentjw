# AgentJW V2 Architecture

## Overview
AgentJW V2 adalah Autonomous AI Software Engineering Agent dengan Executive Brain Architecture.

## Core Components

### Executive Brain
State machine yang mengelola seluruh workflow:
- IDLE → PLANNING → EXECUTING → REFLECTING → DECIDING → COMPLETED/FAILED

### Planner DAG
Multi-step workflow planning dengan dependency management.

### Executor Engine
Generic executor dengan lazy loading action handlers.

### Reflection Engine
Post-execution analysis dengan confidence scoring.

### Runtime Bus
Shared state management antar komponen.

## Data Flow
```

User Input → Brain → Executive Brain → Planner DAG → Executor → Handler → Reflection → Result

```

## Dependency Map
```

AgentJW V2
├── Python 3.12+
├── OpenRouter API (LLM)
├── SQLite (Memory)
├── FastAPI (Optional)
└── FFmpeg (Video processing)

```
