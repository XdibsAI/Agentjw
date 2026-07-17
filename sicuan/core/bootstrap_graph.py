"""
Bootstrap Graph — Phase graph for system startup
"""
from typing import Dict, List


class BootstrapGraph:
    """Bootstrap phase graph untuk startup"""

    def __init__(self):
        self.phases = [
            {"name": "Phase 0", "description": "Environment Load", "status": "✅"},
            {"name": "Phase 1", "description": "Config Load", "status": "✅"},
            {"name": "Phase 2", "description": "LLM Client Init", "status": "✅"},
            {"name": "Phase 3", "description": "Context Manager Init", "status": "✅"},
            {"name": "Phase 4", "description": "Brain Load", "status": "✅"},
            {"name": "Phase 5", "description": "Actions Load", "status": "✅"},
            {"name": "Phase 6", "description": "Tools Load", "status": "✅"},
            {"name": "Phase 7", "description": "Agent Teams Init", "status": "✅"},
            {"name": "Phase 8", "description": "Session Init", "status": "✅"},
            {"name": "Phase 9", "description": "Service Ready", "status": "⏳"},
        ]

    def get_graph(self) -> List[Dict]:
        return self.phases

    def get_summary(self) -> str:
        lines = ["🚀 Bootstrap Graph"]
        lines.append("=" * 40)
        for phase in self.phases:
            status = phase["status"]
            icon = "🟢" if status == "✅" else "⏳" if status == "⏳" else "🔴"
            lines.append(f"{icon} {phase['name']}: {phase['description']}")
        return "\n".join(lines)


def get_bootstrap_graph() -> BootstrapGraph:
    return BootstrapGraph()
