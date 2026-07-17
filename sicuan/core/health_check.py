"""
Health Check — Cek status semua komponen
"""
from typing import Dict
import subprocess
from pathlib import Path


class HealthCheck:
    """Health Check untuk semua komponen"""

    def check_all(self) -> Dict:
        return {
            "bot": self.check_bot(),
            "ollama": self.check_ollama(),
            "database": self.check_database(),
            "memory": self.check_memory(),
            "components": self.check_components()
        }

    def check_bot(self) -> Dict:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", "sicuan-telegram"],
                capture_output=True, text=True, timeout=5
            )
            return {
                "status": "running" if result.returncode == 0 else "stopped",
                "details": result.stdout.strip()
            }
        except:
            return {"status": "unknown", "details": "Check failed"}

    def check_ollama(self) -> Dict:
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                return {"status": "running", "details": "OK"}
            return {"status": "error", "details": f"HTTP {response.status_code}"}
        except:
            return {"status": "stopped", "details": "Connection refused"}

    def check_database(self) -> Dict:
        db_path = Path("/home/dibs/agentjw/memory/agentjw.db")
        if db_path.exists():
            size = db_path.stat().st_size
            return {"status": "ok", "details": f"{size} bytes"}
        return {"status": "error", "details": "Database not found"}

    def check_memory(self) -> Dict:
        memory_dir = Path("/home/dibs/agentjw/memory")
        if memory_dir.exists():
            files = len(list(memory_dir.glob("*.json")))
            return {"status": "ok", "details": f"{files} files"}
        return {"status": "error", "details": "Memory directory not found"}

    def check_components(self) -> Dict:
        components = [
            "sicuan/core/ceo_agent.py",
            "sicuan/core/data_hub.py",
            "sicuan/core/roi_engine.py",
            "sicuan/core/workflow_engine.py",
            "sicuan/core/project_portfolio.py"
        ]
        results = {}
        for comp in components:
            path = Path("/home/dibs/agentjw") / comp
            results[comp] = "✅" if path.exists() else "❌"
        return results


_health = None


def get_health_check() -> HealthCheck:
    global _health
    if _health is None:
        _health = HealthCheck()
    return _health
