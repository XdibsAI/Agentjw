"""
autonomous_project - Meta-workflow dengan Result Contract
"""

# from sicuan.core.executive_brain import ExecutiveBrain  # Lazy import
from sicuan.core.result_contract import ResultContract
from core.logger import logger


def execute(task: dict) -> dict:
    """Execute autonomous_project dengan Result Contract"""
    target = task.get("target", "")
    user_request = task.get("user_request", "")
    context = task.get("context", {})
    
    goal = "autonomous"
    if "repair" in user_request.lower() or "perbaiki" in user_request.lower():
        goal = "repair"
    elif "build" in user_request.lower() or "bangun" in user_request.lower():
        goal = "build"
    elif "analyze" in user_request.lower() or "analisa" in user_request.lower():
        goal = "analyze"
    elif "scan" in user_request.lower():
        goal = "scan"
    
    logger.info(f"autonomous_project: goal={goal}, target={target}")
    
    try:
        executive = ExecutiveBrain()
        result = executive.run(goal, target, user_request, context)
        
        if result.get("state") == "completed":
            history = result.get("history", [])
            if history:
                last = history[-1]
                result_data = last.get("result", {})
                display = result_data.get("display", "🤖 Autonomous project selesai")
                summary = result_data.get("summary", display)
                
                contract = ResultContract(
                    success=True,
                    action="autonomous_project",
                    entity=target,
                    display=display,
                    metrics={"steps": len(history)},
                    confidence=0.9,
                    data={"result": result}
                )
                return contract.to_dict()
            
            contract = ResultContract(
                success=True,
                action="autonomous_project",
                entity=target,
                display="🤖 Autonomous project selesai",
                confidence=0.9
            )
            return contract.to_dict()
        else:
            contract = ResultContract(
                success=False,
                action="autonomous_project",
                entity=target,
                display=f"❌ Autonomous project gagal: {result.get('reason', 'Unknown error')}",
                errors=[result.get('reason', 'Unknown error')]
            )
            return contract.to_dict()
            
    except Exception as e:
        contract = ResultContract(
            success=False,
            action="autonomous_project",
            entity=target,
            display=f"❌ Gagal menjalankan autonomous project: {str(e)}",
            errors=[str(e)]
        )
        return contract.to_dict()
