import json
from sicuan.adapters.project_adapter import get_project_adapter
from pathlib import Path
from memory.project_registry import ProjectRegistry

ROOT = Path(__file__).resolve().parents[2]

SYSTEM_DIRS = [
    "agents",
    "core",
    "memory",
    "tools",
    "mcp",
    "runtime",
    "swarm",
    "sicuan"
]

IGNORE_DIRS = {
    "venv",
    "__pycache__",
    ".git",
    "uploads",
    "backups",
    "chroma_db",
    ".pytest_cache"
}

IGNORE_EXT = {
    ".pyc",
    ".log",
    ".bak",
    ".tmp"
}


class WorkspaceScanner:

    def scan(self):

        report = {
            "root": str(ROOT),
            "systems": {},
            "projects": {},
            "logs": [],
            "databases": [],
            "python_files": 0,
            "total_files": 0,
            "useful_files": 0,
            "projects_count": 0,
            "systems_count": 0
        }

        # ==========================
        # SYSTEMS
        # ==========================

        for name in SYSTEM_DIRS:

            p = ROOT / name

            if not p.exists():
                continue

            py_files = list(p.rglob("*.py"))

            report["systems"][name] = {
                "path": str(p),
                "python_files": len(py_files),
                "exists": True
            }

            report["python_files"] += len(py_files)

        report["systems_count"] = len(report["systems"])

        # ==========================
        # PROJECTS
        # ==========================

        projects_dir = ROOT / "projects"

        if projects_dir.exists():

            for p in projects_dir.iterdir():

                if not p.is_dir():
                    continue

                py_count = len(list(p.rglob("*.py")))

                report["projects"][p.name] = {
                    "path": str(p),
                    "python_files": py_count,
                    "status": "active"
                }

        report["projects_count"] = len(report["projects"])

        # ==========================
        # DATABASES
        # ==========================

        for ext in ("*.db", "*.sqlite", "*.sqlite3"):

            for db in ROOT.rglob(ext):

                report["databases"].append(str(db))

        # ==========================
        # LOGS
        # ==========================

        logs_dir = ROOT / "logs"

        if logs_dir.exists():

            for log in logs_dir.glob("*.log"):

                report["logs"].append(str(log))

        # ==========================
        # USEFUL FILE COUNT
        # ==========================

        useful = 0
        total = 0

        for path in ROOT.rglob("*"):

            if not path.is_file():
                continue

            total += 1

            parts = set(path.parts)

            if parts & IGNORE_DIRS:
                continue

            if path.suffix.lower() in IGNORE_EXT:
                continue

            useful += 1

        report["total_files"] = total
        report["useful_files"] = useful

        # ==========================
        # SAVE MEMORY
        # ==========================

        out = ROOT / "memory/workspace_state.json"

        out.write_text(
            json.dumps(
                report,
                indent=2,
                ensure_ascii=False
            )
        )

        return report

    def summary(self):

        r = self.scan()

        return {
            "systems": list(r["systems"].keys()),
            "projects": list(r["projects"].keys()),
            "python_files": r["python_files"],
            "useful_files": r["useful_files"],
            "databases": len(r["databases"]),
            "logs": len(r["logs"])
        }
