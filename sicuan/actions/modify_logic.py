"""
modify_logic - Modifikasi logic dengan Result Contract
"""

from pathlib import Path
# # Migrated to adapter  # Migrated to adapter
from sicuan.core.repair_trace_guard import must_trace_before_repair
from agents.specialist.logic_modifier import logic_modifier
from sicuan.core.result_contract import ResultContract
from sicuan.adapters.project_adapter import get_project_adapter


def execute(task: dict) -> dict:
    """Execute modify_logic dengan Result Contract"""
    target = task.get("target", "")
    user_request = task.get("user_request", "")
    
    # target format: "nama_project: instruksi"
    proj_name = target
    instruction = user_request
    if target and ":" in target:
        proj_name, _, instruction_part = target.partition(":")
        if instruction_part.strip():
            instruction = instruction_part.strip()
    
    adapter = get_project_adapter()
    projects = adapter.get_projects()
    proj = None
    for p in projects:
        if proj_name and proj_name.lower() in p["name"].lower():
            proj = p
            break
    
    if not proj:
        contract = ResultContract(
            success=False,
            action="modify_logic",
            entity=proj_name,
            display=f"❌ Project tidak ditemukan: {proj_name}",
            errors=[f"Project tidak ditemukan: {proj_name}"]
        )
        return contract.to_dict()
    
    try:
        project_dir = Path(proj["project_dir"])
        trace_ctx = must_trace_before_repair(str(project_dir))
        result = logic_modifier.modify(project_dir, instruction)
        
        modified = result.get("modified", [])
        failed = result.get("failed", [])
        
        if modified:
            display = f"🔧 Logic modified: {len(modified)} files"
        elif failed:
            display = f"⚠️ Logic modification failed: {len(failed)} files"
        else:
            display = "🔧 Logic modified"
        
        contract = ResultContract(
            success=True,
            action="modify_logic",
            entity=proj['name'],
            display=display,
            metrics={
                "modified": len(modified),
                "failed": len(failed)
            },
            confidence=0.9,
            data={"modified": modified, "failed": failed, "trace": trace_ctx}
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="modify_logic",
            entity=proj_name,
            display=f"❌ Gagal memodifikasi logic: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
