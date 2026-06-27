"""
list_projects - Daftar project dengan Result Contract
"""

from memory.project_registry import ProjectRegistry
from sicuan.core.result_contract import ResultContract


def execute(task: dict) -> dict:
    """Execute list_projects dengan Result Contract"""
    try:
        registry = ProjectRegistry()
        projects = registry.list_projects()
        
        if not projects:
            contract = ResultContract(
                success=True,
                action="list_projects",
                entity="",
                display="📂 Belum ada project terdaftar",
                metrics={"total": 0}
            )
            return contract.to_dict()
        
        # Build display
        lines = ["📂 DAFTAR PROJECT KITA:\n"]
        for p in projects:
            name = p[0] if isinstance(p, tuple) else p.get("name", "unknown")
            status = p[4] if isinstance(p, tuple) else p.get("status", "unknown")
            path = p[1] if isinstance(p, tuple) else p.get("path", "")
            lines.append(f"• {name}")
            lines.append(f"  Status: {status}")
            lines.append(f"  Path: {path}\n")
        
        contract = ResultContract(
            success=True,
            action="list_projects",
            entity="",
            display="\n".join(lines),
            metrics={"total": len(projects)},
            confidence=1.0,
            data={"projects": projects}
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="list_projects",
            entity="",
            display=f"❌ Gagal mengambil daftar project: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
