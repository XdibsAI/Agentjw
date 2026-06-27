import json
from pathlib import Path
from datetime import datetime

ROOT = Path("/home/dibs/agentjw")

RUNTIME_FILE = ROOT / "sicuan_audit_report" / "runtime_state.json"


def collect_runtime_state():

    state = {
        "timestamp": datetime.utcnow().isoformat(),
        "active_projects": [],
        "active_agents": [],
        "active_capabilities": [],
        "runtime_status": {}
    }

    graph_file = ROOT / "sicuan_audit_report" / "integration_v3.json"

    if graph_file.exists():
        try:
            data = json.loads(graph_file.read_text())

            state["active_capabilities"] = list(
                data.get("capabilities", {}).keys()
            )

        except Exception:
            pass

    projects_dir = ROOT / "projects"

    if projects_dir.exists():
        state["active_projects"] = [
            p.name
            for p in projects_dir.iterdir()
            if p.is_dir()
        ]

    agents_dir = ROOT / "agents"

    if agents_dir.exists():
        state["active_agents"] = [
            p.stem
            for p in agents_dir.glob("*.py")
        ]

    return state


def save_runtime_state():

    state = collect_runtime_state()

    RUNTIME_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(RUNTIME_FILE, "w") as f:
        json.dump(
            state,
            f,
            indent=2
        )

    return state


def load_runtime_state():

    if not RUNTIME_FILE.exists():
        return save_runtime_state()

    try:
        return json.loads(
            RUNTIME_FILE.read_text()
        )
    except Exception:
        return save_runtime_state()


if __name__ == "__main__":
    save_runtime_state()
