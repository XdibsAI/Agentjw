"""
analyze_project - Analisa project dengan Result Contract
"""

from memory.unified_projects import unified_projects
from sicuan.project_trace import audit_project
from sicuan.core.result_contract import ResultContract


def execute(task: dict) -> dict:
    """Execute analyze_project dengan Result Contract"""
    target = task.get("target", "")
    projects = unified_projects.list_projects()
    
    p = None
    for proj in projects:
        if target and target.lower() in proj["name"].lower():
            p = proj
            break
    
    if not p:
        contract = ResultContract(
            success=False,
            action="analyze_project",
            entity=target,
            display=f"❌ Project '{target}' tidak ditemukan",
            errors=[f"Project '{target}' tidak ditemukan"]
        )
        return contract.to_dict()
    
    try:
        audit = audit_project(p["project_dir"])
        confidence = audit.get("confidence", 0)
        functions = audit.get("functions", 0)
        
        contract = ResultContract(
            success=True,
            action="analyze_project",
            entity=p["name"],
            display=f"Project {p['name']}: confidence {confidence}%, {functions} functions",
            metrics={
                "confidence": confidence,
                "functions": functions
            },
            confidence=confidence / 100,
            data=audit
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="analyze_project",
            entity=target,
            display=f"❌ Analisa gagal: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
