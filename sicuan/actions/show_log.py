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
    
    # Special case: godmeme
    if "godmeme" in target_lower:
        project_dir = Path("/home/dibs/agentjw/projects/godmeme_bot")
        candidates = [
            "trading_bot_live.log",
            "paper_24h.log",
            "trading_bot_live_old.log",
            "trading_bot.log"
        ]
        
        for f in candidates:
            path = project_dir / f
            if path.exists():
                try:
                    lines = path.read_text(errors='ignore').splitlines()
                    content = "\n".join(lines[-200:])
                    contract = ResultContract(
                        success=True,
                        action="show_log",
                        entity="godmeme_bot",
                        display=f"📋 LOG FILE: {f}\n\n{content[:500]}...",
                        metrics={"lines": len(lines), "file": f},
                        confidence=0.95,
                        data={"content": content, "total_lines": len(lines)}
                    )
                    return contract.to_dict()
                except Exception as e:
                    contract = ResultContract(
                        success=False,
                        action="show_log",
                        entity="godmeme_bot",
                        display=f"❌ Gagal membaca log: {str(e)}",
                        errors=[str(e)]
                    )
                    return contract.to_dict()
        
        contract = ResultContract(
            success=False,
            action="show_log",
            entity="godmeme_bot",
            display="❌ Tidak ada log ditemukan pada godmeme_bot",
            errors=["Tidak ada log ditemukan pada godmeme_bot"]
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
            display=f"❌ Project '{target}' tidak ditemukan",
            errors=[f"Project '{target}' tidak ditemukan"]
        )
        return contract.to_dict()
    
    project_dir = Path(proj["project_dir"])
    log_files = list(project_dir.glob("*.log")) + list(project_dir.glob("logs/*.log"))
    
    if not log_files:
        contract = ResultContract(
            success=False,
            action="show_log",
            entity=proj['name'],
            display=f"❌ Tidak ada log ditemukan di project {proj['name']}",
            errors=[f"Tidak ada log ditemukan di project {proj['name']}"]
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
            display=f"❌ Gagal membaca log: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
