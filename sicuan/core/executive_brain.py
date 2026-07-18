"""
Executive Brain - State Machine untuk mengelola workflow
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from sicuan.core.planner_dag import PlannerDAG
# from sicuan.core.executor_engine import ExecutorEngine  # Lazy import
from sicuan.core.workflow_context import WorkflowContext
from sicuan.core.reflection_engine import ReflectionEngine
from sicuan.action_registry import ActionRegistry
from core.logger import logger


class ExecutiveState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    DECIDING = "deciding"
    RETRYING = "retrying"
    REPLANNING = "replanning"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class ExecutiveBrain:
    def __init__(self):
        self.state = ExecutiveState.IDLE
        self.planner = PlannerDAG()
        self.executor = ExecutorEngine()
        self.reflection_engine = ReflectionEngine()
        self.registry = ActionRegistry()
        self.context = None
        self.plan = None
        self.current_step_index = 0
        self.retry_counts = {}
        self.history = []
        self.session_id = str(uuid.uuid4())[:8]
        self.max_retries = 3
        self.max_steps = 20

    def run(self, goal: str, target: str = "", user_message: str = "", context: dict = None) -> Dict:
        self.session_id = str(uuid.uuid4())[:8]
        self.history = []
        self.retry_counts = {}
        self.current_step_index = 0

        logger.info(f"ExecutiveBrain started: goal={goal}, target={target}")

        # Planning
        self.state = ExecutiveState.PLANNING
        self.plan = self.planner.plan(goal, target, context)

        # Setup context
        self.context = WorkflowContext(goal=goal, target=target, context=context or {})
        for step in self.plan.get("steps", []):
            self.context.add_step(step.copy())

        logger.info(f"Plan created: {self.plan.get('plan_id')} with {len(self.plan.get('steps', []))} steps")

        # Execute loop
        while True:
            if len(self.history) > self.max_steps:
                self.state = ExecutiveState.FAILED
                return self._finalize("Max steps exceeded")

            next_steps = self.planner.get_next_steps(self.plan)

            if not next_steps:
                # Cek apakah ada step yang failed
                has_failed = any(s.get("status") == "failed" for s in self.plan.get("steps", []))
                if has_failed:
                    self.state = ExecutiveState.FAILED
                    return self._finalize("Some steps failed")
                self.state = ExecutiveState.COMPLETED
                return self._finalize("All steps completed")

            for step in next_steps:
                self.state = ExecutiveState.EXECUTING
                result = self._execute_step(step)

                self.state = ExecutiveState.REFLECTING
                reflection = self._reflect_step(step, result)

                self.state = ExecutiveState.DECIDING
                decision = self._decide(step, result, reflection)

                if decision == "continue":
                    self.current_step_index += 1
                    continue
                elif decision == "retry":
                    self.state = ExecutiveState.RETRYING
                    self.retry_counts[step.get("id")] = self.retry_counts.get(step.get("id"), 0) + 1
                    if self.retry_counts[step.get("id")] >= self.max_retries:
                        self.state = ExecutiveState.FAILED
                        return self._finalize(f"Max retries exceeded for step {step.get('id')}")
                    self.state = ExecutiveState.EXECUTING
                    result = self._execute_step(step)
                    continue
                elif decision == "replan":
                    self.state = ExecutiveState.REPLANNING
                    new_plan = self.planner.plan_with_reflection(self.plan, reflection)
                    if new_plan:
                        self.plan = new_plan
                    self.state = ExecutiveState.PLANNING
                    continue
                elif decision == "escalate":
                    self.state = ExecutiveState.ESCALATED
                    return self._finalize("Escalated - manual intervention required")
                else:
                    self.current_step_index += 1
                    continue

        return self._finalize("Workflow completed")

    
    
    
    
    def _execute_step(self, step: Dict) -> Dict:
        action = step.get("action")
        target = step.get("target", "")

        logger.info(f"Executing step {step.get('id')}: {action} -> {target}")

        try:
            task = self.executor.push_task(
                action=action,
                target=target,
                user_request=f"Execute step {step.get('id')}",
                context=self.context.shared_data if self.context else {}
            )
            result = self.executor.execute_next()

            is_success = result.get("success", False)
            validation = result.get("validation", {})
            is_valid = validation.get("valid", False)

            logger.info(f"Step {step.get('id')}: success={is_success}, valid={is_valid}")

            if self.context:
                if is_success and is_valid:
                    self.context.update_step(step.get("id"), "completed", result)
                    step["status"] = "completed"
                else:
                    error_msg = result.get("error") or result.get("summary") or "Unknown error"
                    self.context.update_step(step.get("id"), "failed", result, error_msg)
                    step["status"] = "failed"
                step["result"] = result

            # === HISTORY: Pastikan result disimpan ===
            self.history.append({
                "step_id": step.get("id"),
                "action": action,
                "target": target,
                "result": result,
                "summary": result.get("summary", ""),
                "success": is_success and is_valid,
                "timestamp": datetime.utcnow().isoformat()
            })

            return result

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "errors": [str(e)]
            }
            if self.context:
                self.context.update_step(step.get("id"), "failed", error_result, str(e))
                step["status"] = "failed"
                step["error"] = str(e)
            self.history.append({
                "step_id": step.get("id"),
                "action": action,
                "target": target,
                "result": error_result,
                "summary": "",
                "success": False,
                "timestamp": datetime.utcnow().isoformat()
            })
            return error_result
    def _reflect_step(self, step: Dict, result: Dict) -> Dict:
        validation = {"valid": result.get("success", False)}
        reflection = self.reflection_engine.analyze(
            task=step,
            result=result,
            validation=validation,
            step_context={"retry_count": self.retry_counts.get(step.get("id"), 0)}
        )
        if self.context:
            step["reflection"] = reflection
        self.history.append({
            "step_id": step.get("id"),
            "reflection": reflection,
            "timestamp": datetime.utcnow().isoformat()
        })
        return reflection

    
    
    
    def _decide(self, step: Dict, result: Dict, reflection: Dict) -> str:
        """Decide next action based on reflection"""
        validation = result.get("validation", {})
        is_valid = validation.get("valid", False)
        is_success = result.get("success", False)
        
        # Action sederhana: langsung continue jika sukses
        action = step.get("action")
        if action in ["scan_project", "analyze_project", "list_projects", "gallery", "get_file", "project_summary"]:
            if is_success:
                return "continue"
        
        if is_success and is_valid:
            return "continue"
        
        # Expected failures - continue (jangan retry)
        error_msg = str(result.get("error", "")).lower()
        expected_failures = ["tidak ditemukan", "not found", "does not exist", "empty", "belum di-render"]
        for pattern in expected_failures:
            if pattern in error_msg:
                return "continue"
        
        # API errors - continue (jangan retry)
        if "402" in error_msg or "429" in error_msg:
            return "continue"
        
        # Retry untuk failure yang bisa diatasi (max 2)
        retry_count = self.retry_counts.get(step.get("id"), 0)
        if retry_count < 2:
            return "retry"
        else:
            return "replan"
    def _finalize(self, reason: str) -> Dict:
        result = {
            "session_id": self.session_id,
            "state": self.state.value,
            "reason": reason,
            "history": self.history,
            "context": self.context.to_dict() if self.context else {},
            "plan": self.plan,
            "timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"ExecutiveBrain finalized: {self.state.value} - {reason}")
        return result

    def status(self) -> Dict:
        return {
            "state": self.state.value,
            "session_id": self.session_id,
            "current_step": self.current_step_index,
            "history_count": len(self.history),
            "plan": self.plan
        }
