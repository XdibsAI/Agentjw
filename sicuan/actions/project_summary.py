"""
project_summary - Ringkasan project dengan Result Contract
"""

# # Migrated to adapter  # Migrated to adapter
from sicuan.core.result_contract import ResultContract
from sicuan.adapters.project_adapter import get_project_adapter


def execute(task: dict) -> dict:
    """Execute project_summary dengan Result Contract"""
    target = task.get("target", "")
    adapter = get_project_adapter()
    projects = adapter.get_projects()
    
    if not projects:
        contract = ResultContract(
            success=True,
            action="project_summary",
            entity="",
            display="📂 Belum ada project terdaftar",
            metrics={"total": 0}
        )
        return contract.to_dict()
    
    # Jika target diberikan, cari project spesifik
    if target:
        proj = None
        for p in projects:
            if target.lower() in p["name"].lower():
                proj = p
                break
        
        if not proj:
            contract = ResultContract(
                success=False,
                action="project_summary",
                entity=target,
                display=f"❌ Project '{target}' tidak ditemukan",
                errors=[f"Project '{target}' tidak ditemukan"]
            )
            return contract.to_dict()
        
        display = f"📌 {proj['name']}\nStatus: {proj['status']}\nPath: {proj['project_dir']}\nFiles: {proj.get('python_files', 0)} Python files"
        
        contract = ResultContract(
            success=True,
            action="project_summary",
            entity=proj['name'],
            display=display,
            metrics={"python_files": proj.get('python_files', 0)},
            data={"project": proj}
        )
        return contract.to_dict()
    
    # Semua project
    lines = ["💰 ANALISA PROJECT KITA:\n"]
    for p in projects:
        lines.append(f"📌 {p['name']}")
        lines.append(f"Status: {p['status']}")
        lines.append(f"Path: {p['project_dir']}")
        lines.append(f"Files: {p.get('python_files', 0)} Python files\n")
    
    contract = ResultContract(
        success=True,
        action="project_summary",
        entity="",
        display="\n".join(lines),
        metrics={"total": len(projects)},
        data={"projects": projects}
    )
    return contract.to_dict()
