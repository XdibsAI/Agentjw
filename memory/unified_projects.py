"""
Unified Projects Reader — SATU sumber kebenaran untuk semua project.
Baca dari memory/projects_db/project_registry.db
"""
import sqlite3
import json
from pathlib import Path

DB = Path("/home/dibs/agentjw/memory/projects_db/project_registry.db")


class UnifiedProjects:

    def list_projects(self) -> list:
        """Baca SEMUA project dari project_registry.db (source of truth)"""
        if not DB.exists():
            return []

        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM projects").fetchall()
        conn.close()

        result = []
        for r in rows:
            d = dict(r)
            try:
                meta = json.loads(d.get("metadata") or "{}")
            except Exception:
                meta = {}
            result.append({
                "name": d.get("name", ""),
                "project_dir": d.get("path", ""),
                "status": d.get("status", "unknown"),
                "tool_type": self._infer_type(d.get("name", "")),
                "python_files": meta.get("python_files", 0),
                "log_path": d.get("log_path", ""),
                "created_at": d.get("created_at", ""),
            })
        return result

    def count(self) -> int:
        return len(self.list_projects())

    def get(self, name: str) -> dict:
        for p in self.list_projects():
            if name.lower() in p["name"].lower():
                return p
        return None

    def _infer_type(self, name: str) -> str:
        name_l = name.lower()
        if "bot" in name_l or "trading" in name_l or "godmeme" in name_l:
            return "trading"
        if "video" in name_l or "youtube" in name_l:
            return "youtube"
        return "general"


unified_projects = UnifiedProjects()

# Backward-compat alias
def get_real_projects() -> list:
    return unified_projects.list_projects()

def count_real_projects() -> int:
    return unified_projects.count()
