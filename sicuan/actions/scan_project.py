"""
scan_project - Scan struktur project dengan Result Contract
"""

from mcp.tools.filesystem_tool import filesystem_tool
# # Migrated to adapter  # Migrated to adapter
from sicuan.core.result_contract import ResultContract
from sicuan.adapters.project_adapter import get_project_adapter


def execute(task: dict) -> dict:
    """Execute scan_project dengan Result Contract"""
    target = task.get("target", "")
    adapter = get_project_adapter()
    projects = adapter.get_projects()
    
    # Cari project
    p = None
    for proj in projects:
        if target and target.lower() in proj["name"].lower():
            p = proj
            break
    
    if not p:
        contract = ResultContract(
            success=False,
            action="scan_project",
            entity=target,
            display=f"❌ Project '{target}' tidak ditemukan",
            errors=[f"Project '{target}' tidak ditemukan"]
        )
        return contract.to_dict()
    
    try:
        data = filesystem_tool.scan_project(p["project_dir"])
        total = data.get("total_py", 0)
        valid = data.get("valid_syntax", 0)
        
        contract = ResultContract(
            success=True,
            action="scan_project",
            entity=p["name"],
            display=f"Scan {p['name']}: {valid}/{total} files valid",
            metrics={
                "total_files": total,
                "valid_files": valid
            },
            confidence=0.95,
            data=data
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="scan_project",
            entity=target,
            display=f"❌ Scan gagal: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
