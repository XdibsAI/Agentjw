"""
Data Aware Planner - Menambahkan data check ke planner
"""

from pathlib import Path
from memory.unified_projects import unified_projects


def check_data_availability(target: str) -> dict:
    """Cek ketersediaan data untuk target"""
    if not target:
        return {"available": False, "reason": "Target tidak ditentukan"}

    # Cari project
    project_dir = Path("/home/dibs/agentjw/projects") / target
    if not project_dir.exists():
        projects = unified_projects.list_projects()
        for p in projects:
            if target.lower() in p["name"].lower():
                project_dir = Path(p["project_dir"])
                break

    if not project_dir.exists():
        return {"available": False, "reason": f"Project '{target}' tidak ditemukan"}

    # Cek trade_history.db
    db_path = project_dir / "trade_history.db"
    if db_path.exists():
        return {"available": True, "source": str(db_path)}
    else:
        return {"available": False, "reason": "Trade history tidak tersedia"}


def filter_plan_by_data(plan: list, target: str) -> list:
    """Filter plan berdasarkan data availability"""
    data_status = check_data_availability(target)
    
    # Action yang membutuhkan data
    data_actions = ["analyze_project", "show_log", "project_summary"]
    
    filtered_plan = []
    for step in plan:
        action = step.get("action", "")
        if action in data_actions and not data_status["available"]:
            # Ganti dengan action yang tidak butuh data
            step["action"] = "godmeme_status"
            step["purpose"] = "Data tidak tersedia, menampilkan status saja"
        filtered_plan.append(step)
    
    return filtered_plan
