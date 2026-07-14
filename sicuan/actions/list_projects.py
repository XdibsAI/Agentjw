"""
list_projects - List all projects with Result Contract
"""

from sicuan.core.result_contract import ResultContract
from sicuan.adapters.project_adapter import get_project_adapter


def execute(task: dict) -> dict:
    """Execute list_projects dengan Result Contract"""
    try:
        adapter = get_project_adapter()
        projects = adapter.get_projects()
        
        if not projects:
            contract = ResultContract(
                success=False,
                action="list_projects",
                entity="projects",
                display="📂 Belum ada project terdaftar.",
                errors=["No projects found"]
            )
            return contract.to_dict()
        
        # Build response
        lines = ["📂 DAFTAR PROJECT KITA:\n"]
        for p in projects:
            name = p.get("name", "unknown")
            status = p.get("status", "active")
            path = p.get("path", "")
            lines.append(f"• {name}")
            lines.append(f"  Status: {status}")
            lines.append(f"  Path: {path}\n")
        
        display = "\n".join(lines)
        
        contract = ResultContract(
            success=True,
            action="list_projects",
            entity="projects",
            display=display,
            data={"projects": projects}
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="list_projects",
            entity="projects",
            display=f"❌ Error listing projects: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
