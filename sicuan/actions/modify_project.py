"""
modify_project - Modifikasi project dengan Result Contract
"""

from agents.orchestrator import orchestrator
from agents.auditor_agent import auditor_agent
from memory.unified_projects import unified_projects
from pathlib import Path
from sicuan.core.result_contract import ResultContract
from core.logger import logger


def execute(task: dict) -> dict:
    """Execute modify_project dengan Result Contract"""
    target = task.get("target", "")
    user_request = task.get("user_request", "")
    context = task.get("context", {})
    session_id = context.get("session_id", "default")
    
    logger.info(f"Modify project: target={target}, request={user_request[:100]}...")
    
    projects = unified_projects.list_projects()
    p = None
    for proj in projects:
        if target and target.lower() in proj["name"].lower():
            p = proj
            break
    
    if not p:
        contract = ResultContract(
            success=False,
            action="modify_project",
            entity=target,
            display=f"❌ Project '{target}' tidak ditemukan",
            errors=[f"Project '{target}' tidak ditemukan"]
        )
        return contract.to_dict()
    
    try:
        project_dir = Path(p["project_dir"])
        py_files = list(project_dir.glob("*.py"))
        before_snapshot = auditor_agent.snapshot([str(f) for f in py_files])
        
        instruction = f"""
Modifikasi project {p['name']}.

Request user:
{user_request}

Rules:
- Jangan merusak fitur existing
- Production ready
- Jelaskan perubahan
"""
        
        result = orchestrator.execute(instruction, [], session_id)
        verdict = auditor_agent.verify(
            user_request=user_request,
            before_snapshot=before_snapshot,
            repair_result=result
        )
        response = auditor_agent.format_response(verdict)
        
        contract = ResultContract(
            success=True,
            action="modify_project",
            entity=p['name'],
            display=response,
            metrics={"verified": verdict.get("verified", False)},
            confidence=0.9,
            data={"result": result, "verdict": verdict}
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="modify_project",
            entity=target,
            display=f"❌ Gagal memodifikasi project: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
