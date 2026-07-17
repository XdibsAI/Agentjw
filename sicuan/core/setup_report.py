"""
Setup Report — Startup configuration report
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class SetupReport:
    """Generate setup configuration report"""

    def __init__(self):
        self.root = Path("/home/dibs/agentjw")
        self.report = {
            "timestamp": datetime.now().isoformat(),
            "system": {},
            "environment": {},
            "components": {},
            "services": {}
        }

    def generate(self) -> Dict:
        """Generate full setup report"""
        self._check_system()
        self._check_environment()
        self._check_components()
        self._check_services()
        return self.report

    def _check_system(self):
        """Check system info"""
        self.report["system"] = {
            "python_version": sys.version,
            "platform": sys.platform,
            "cwd": str(Path.cwd()),
            "root": str(self.root)
        }

    def _check_environment(self):
        """Check environment variables"""
        env_keys = [
            "OPENROUTER_API_KEY",
            "OPENAI_API_KEY",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_CHAT_ID",
            "NVIDIA_NIM_API_KEY",
            "MASTER_ENCRYPTION_KEY"
        ]
        env_status = {}
        for key in env_keys:
            env_status[key] = "✅" if os.getenv(key) else "❌"
        self.report["environment"] = env_status

    def _check_components(self):
        """Check core components"""
        components = {
            "brain": self.root / "sicuan/brain.py",
            "chat": self.root / "sicuan/chat.py",
            "llm_client": self.root / "core/llm_client.py",
            "semantic_router": self.root / "sicuan/core/semantic_router.py",
            "context_manager": self.root / "sicuan/core/context_manager.py",
            "planning": self.root / "sicuan/core/planning.py",
            "sub_agent": self.root / "sicuan/core/sub_agent.py",
            "agent_team": self.root / "sicuan/core/agent_team.py",
            "session_manager": self.root / "sicuan/core/session_manager.py",
        }
        self.report["components"] = {
            name: "✅" if path.exists() else "❌"
            for name, path in components.items()
        }

    def _check_services(self):
        """Check running services"""
        import subprocess
        services = ["sicuan-telegram", "ollama"]
        self.report["services"] = {}
        for svc in services:
            result = subprocess.run(
                ["systemctl", "is-active", svc],
                capture_output=True, text=True
            )
            self.report["services"][svc] = result.stdout.strip() if result.returncode == 0 else "inactive"

    def to_markdown(self) -> str:
        """Convert report to markdown"""
        lines = ["# Setup Report\n"]
        lines.append(f"**Generated:** {self.report['timestamp']}\n")

        lines.append("## System")
        for k, v in self.report["system"].items():
            lines.append(f"- **{k}:** {v}")

        lines.append("\n## Environment")
        for k, v in self.report["environment"].items():
            lines.append(f"- **{k}:** {v}")

        lines.append("\n## Components")
        for k, v in self.report["components"].items():
            lines.append(f"- **{k}:** {v}")

        lines.append("\n## Services")
        for k, v in self.report["services"].items():
            lines.append(f"- **{k}:** {v}")

        return "\n".join(lines)


def get_setup_report() -> SetupReport:
    return SetupReport()
