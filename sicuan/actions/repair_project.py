"""
repair_project - Perbaiki project dengan Result Contract
"""

from pathlib import Path
from agents.orchestrator import orchestrator
from agents.auditor_agent import auditor_agent
# # Migrated to adapter  # Migrated to adapter
from sicuan.core.result_contract import ResultContract
from core.logger import logger
from sicuan.adapters.project_adapter import get_project_adapter


def execute(task: dict) -> dict:
    """Execute repair_project dengan Result Contract"""
    target = task.get("target", "")
    context = task.get("context", {})
    session_id = context.get("session_id", "default")
    
    # Parse target
    proj_name = target
    if target and ":" in target:
        proj_name, _, _ = target.partition(":")
        proj_name = proj_name.strip()
    
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
            action="repair_project",
            entity=proj_name,
            display=f"❌ Project tidak ditemukan: {proj_name}",
            errors=[f"Project tidak ditemukan: {proj_name}"]
        )
        return contract.to_dict()
    
    try:
        project_dir = Path(proj["project_dir"])
        
        # Snapshot sebelum repair
        py_files = list(project_dir.glob("*.py"))
        before_snapshot = auditor_agent.snapshot([str(f) for f in py_files])
        
        # Jalankan repair melalui orchestrator
        result = orchestrator.execute(
            f"perbaiki project {proj['name']}",
            [],
            session_id
        )
        
        # Ambil status dari result
        if isinstance(result, dict):
            repaired = result.get("repaired", [])
            failed = result.get("failed", [])
            status = result.get("status", "completed")
        else:
            repaired = []
            failed = []
            status = "completed" if result else "failed"
        
        total = len(py_files)
        success_count = len(repaired)
        
        if success_count == total:
            display = f"✅ Repair {proj['name']}: {success_count}/{total} files valid"
        elif success_count > 0:
            display = f"⚠️ Repair {proj['name']}: {success_count}/{total} files valid, {len(failed)} failed"
        else:
            display = f"✅ Repair {proj['name']}: {success_count}/{total} files valid (no changes needed)"
        
        contract = ResultContract(
            success=True,
            action="repair_project",
            entity=proj['name'],
            display=display,
            metrics={
                "total_files": total,
                "repaired": success_count,
                "failed": len(failed)
            },
            confidence=0.9 if success_count == total else 0.5,
            data={"result": result, "before_snapshot": before_snapshot}
        )
        return contract.to_dict()
        
    except Exception as e:
        logger.error(f"Repair project error: {e}")
        contract = ResultContract(
            success=False,
            action="repair_project",
            entity=proj_name,
            display=f"❌ Gagal memperbaiki project: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
