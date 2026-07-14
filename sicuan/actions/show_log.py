"""
show_log - Tampilkan log dengan Result Contract
"""

import os
from pathlib import Path
from sicuan.core.result_contract import ResultContract
from sicuan.adapters.project_adapter import get_project_adapter


def execute(task: dict) -> dict:
    """Execute show_log dengan Result Contract"""
    target = task.get("target", "")
    target_lower = str(target).lower()

    # Cek apakah ada target yang valid
    if not target_lower or target_lower in ["", "godmeme", "godmeme_bot"]:
        # Cek apakah ada project godmeme_bot
        adapter = get_project_adapter()
        projects = adapter.get_projects()
        godmeme_project = None
        for p in projects:
            if "godmeme" in p["name"].lower():
                godmeme_project = p
                break

        if godmeme_project:
            project_dir = Path(godmeme_project["project_dir"])
            # Cari log file
            log_files = list(project_dir.glob("*.log"))
            if log_files:
                log_file = log_files[0]
                if log_file.exists():
                    content = log_file.read_text()
                    return {
                        "success": True,
                        "display": f"📄 Log dari {godmeme_project['name']}:\n\n{content[:1000]}",
                        "data": {"log": content[:1000]}
                    }
            return {
                "success": False,
                "display": f"❌ Tidak ada log file di {godmeme_project['name']}",
                "data": {}
            }
    
    # Jika target spesifik
    adapter = get_project_adapter()
    project = adapter.find_project(target)
    if project:
        project_dir = Path(project["project_dir"])
        log_files = list(project_dir.glob("*.log"))
        if log_files:
            log_file = log_files[0]
            if log_file.exists():
                content = log_file.read_text()
                return {
                    "success": True,
                    "display": f"📄 Log dari {project['name']}:\n\n{content[:1000]}",
                    "data": {"log": content[:1000]}
                }
        return {
            "success": False,
            "display": f"❌ Tidak ada log file di {project['name']}",
            "data": {}
        }
    
    return {
        "success": False,
        "display": f"❌ Project '{target}' tidak ditemukan",
        "data": {}
    }
