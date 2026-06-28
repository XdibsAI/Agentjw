"""
show_log - Tampilkan log dengan Result Contract
"""

import os
from pathlib import Path
from memory.unified_projects import unified_projects
from sicuan.core.result_contract import ResultContract


def execute(task: dict) -> dict:
    """Execute show_log dengan Result Contract"""
    target = task.get("target", "")
    target_lower = str(target).lower()
    
    # Cek apakah ada target yang valid
    if not target_lower or target_lower in ["", "godmeme", "godmeme_bot"]:
        # Cek apakah ada project godmeme_bot
        projects = unified_projects.list_projects()
        godmeme_project = None
        for p in projects:
            if "godmeme" in p["name"].lower():
                godmeme_project = p
                break
        
        if godmeme_project:
            project_dir = Path(godmeme_project["project_dir"])
            # Cek apakah ada log file
            log_files = list(project_dir.glob("*.log"))
            if log_files:
                latest = max(log_files, key=lambda f: f.stat().st_mtime)
                lines = latest.read_text(errors='ignore').splitlines()
                content = "\n".join(lines[-200:])
                contract = ResultContract(
                    success=True,
                    action="show_log",
                    entity=godmeme_project["name"],
                    display=f"📋 LOG FILE: {latest.name}\n\n{content[:500]}...",
                    metrics={"lines": len(lines), "file": latest.name},
                    confidence=0.95,
                    data={"content": content, "total_lines": len(lines)}
                )
                return contract.to_dict()
            else:
                contract = ResultContract(
                    success=False,
                    action="show_log",
                    entity=godmeme_project["name"],
                    display="📋 Log tidak ditemukan. Data trade history tidak tersedia.",
                    errors=["Log tidak ditemukan"],
                    warnings=["Data trade history tidak tersedia"]
                )
                return contract.to_dict()
        
        contract = ResultContract(
            success=False,
            action="show_log",
            entity=target,
            display="📋 Log tidak ditemukan. Data trade history tidak tersedia.",
            errors=["Log tidak ditemukan"],
            warnings=["Data trade history tidak tersedia"]
        )
        return contract.to_dict()
    
    # Generic: cari project di registry
    projects = unified_projects.list_projects()
    proj = None
    for p in projects:
        if target and target.lower() in p["name"].lower():
            proj = p
            break
    
    if not proj:
        contract = ResultContract(
            success=False,
            action="show_log",
            entity=target,
            display=f"📋 Project '{target}' tidak ditemukan. Data trade history tidak tersedia.",
            errors=[f"Project '{target}' tidak ditemukan"],
            warnings=["Data trade history tidak tersedia"]
        )
        return contract.to_dict()
    
    project_dir = Path(proj["project_dir"])
    log_files = list(project_dir.glob("*.log")) + list(project_dir.glob("logs/*.log"))
    
    if not log_files:
        contract = ResultContract(
            success=False,
            action="show_log",
            entity=proj['name'],
            display=f"📋 Log tidak ditemukan di project {proj['name']}. Data trade history tidak tersedia.",
            errors=[f"Log tidak ditemukan di project {proj['name']}"],
            warnings=["Data trade history tidak tersedia"]
        )
        return contract.to_dict()
    
    latest = max(log_files, key=lambda f: f.stat().st_mtime)
    
    try:
        lines = latest.read_text(errors='ignore').splitlines()
        content = "\n".join(lines[-200:])
        
        contract = ResultContract(
            success=True,
            action="show_log",
            entity=proj['name'],
            display=f"📋 LOG FILE: {latest.name}\n\n{content[:500]}...",
            metrics={"lines": len(lines), "file": latest.name},
            confidence=0.95,
            data={"content": content, "total_lines": len(lines)}
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="show_log",
            entity=proj['name'],
            display=f"📋 Gagal membaca log: {str(e)}. Data trade history tidak tersedia.",
            errors=[str(e)],
            warnings=["Data trade history tidak tersedia"]
        )
        return contract.to_dict()
