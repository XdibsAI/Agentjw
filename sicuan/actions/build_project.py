"""
build_project - Bangun project baru dengan Result Contract
"""

from agents.orchestrator import orchestrator
from sicuan.core.result_contract import ResultContract
from core.logger import logger


def execute(task: dict) -> dict:
    """Execute build_project dengan Result Contract"""
    target = task.get("target", "")
    user_request = task.get("user_request", "")
    context = task.get("context", {})
    session_id = context.get("session_id", "default")
    
    logger.info(f"Build project: target={target}, request={user_request[:100]}...")
    
    try:
        result = orchestrator.execute(user_request, [], session_id)
        status = result.get("status", "running")
        message = result.get("message", "")
        
        if status == "completed" or status == "success":
            display = f"🏗️ Project '{target}' berhasil dibangun"
            confidence = 0.95
        elif status == "needs_clarification":
            display = f"📝 Project '{target}' membutuhkan klarifikasi: {message}"
            confidence = 0.5
        else:
            display = f"🏗️ Project '{target}' sedang dibangun. Status: {status}"
            confidence = 0.7
        
        contract = ResultContract(
            success=True,
            action="build_project",
            entity=target,
            display=display,
            metrics={"status": status},
            confidence=confidence,
            data={"result": result}
        )
        return contract.to_dict()
        
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="build_project",
            entity=target,
            display=f"❌ Gagal membangun project: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
