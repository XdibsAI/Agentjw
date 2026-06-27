"""
Planner DAG - Menghasilkan multi-step workflow dengan dependency
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid


class PlannerDAG:
    """Menghasilkan DAG (multi-step plan) berdasarkan goal"""

    # Template DAG untuk setiap jenis plan
    TEMPLATES = {
        "repair": [
            {"id": "step_1", "action": "scan_project", "depends_on": [], "optional": False},
            {"id": "step_2", "action": "analyze_project", "depends_on": ["step_1"], "optional": False},
            {"id": "step_3", "action": "repair_project", "depends_on": ["step_2"], "optional": False},
            {"id": "step_4", "action": "analyze_project", "depends_on": ["step_3"], "optional": False},
        ],
        "modify": [
            {"id": "step_1", "action": "trace_code", "depends_on": [], "optional": False},
            {"id": "step_2", "action": "modify_logic", "depends_on": ["step_1"], "optional": False},
            {"id": "step_3", "action": "scan_project", "depends_on": ["step_2"], "optional": False},
        ],
        "analyze": [
            {"id": "step_1", "action": "analyze_project", "depends_on": [], "optional": False},
        ],
        "scan": [
            {"id": "step_1", "action": "scan_project", "depends_on": [], "optional": False},
        ],
        "trace": [
            {"id": "step_1", "action": "trace_code", "depends_on": [], "optional": False},
        ],
        "build": [
            {"id": "step_1", "action": "build_project", "depends_on": [], "optional": False},
        ],
        "modify_project": [
            {"id": "step_1", "action": "trace_code", "depends_on": [], "optional": False},
            {"id": "step_2", "action": "modify_logic", "depends_on": ["step_1"], "optional": False},
            {"id": "step_3", "action": "scan_project", "depends_on": ["step_2"], "optional": False},
        ],
        "get_file": [
            {"id": "step_1", "action": "get_file", "depends_on": [], "optional": False},
        ],
        "project_summary": [
            {"id": "step_1", "action": "project_summary", "depends_on": [], "optional": False},
        ],
        "show_log": [
            {"id": "step_1", "action": "show_log", "depends_on": [], "optional": False},
        ],
        "godmeme_status": [
            {"id": "step_1", "action": "godmeme_status", "depends_on": [], "optional": False},
        ],
        "run_bot": [
            {"id": "step_1", "action": "run_bot", "depends_on": [], "optional": False},
        ],
        "list_projects": [
            {"id": "step_1", "action": "list_projects", "depends_on": [], "optional": False},
        ],
        "business_analysis": [
            {"id": "step_1", "action": "business_analysis", "depends_on": [], "optional": False},
        ],
        "gallery": [
            {"id": "step_1", "action": "gallery", "depends_on": [], "optional": False},
        ],
        "video_info": [
            {"id": "step_1", "action": "video_info", "depends_on": [], "optional": False},
        ],
        "autonomous_project": [
            {"id": "step_1", "action": "autonomous_project", "depends_on": [], "optional": False},
        ],
    }

    def __init__(self):
        self._execution_context = {}
        self._reflections = []

    def plan(self, goal: str, target: str, context: Dict = None) -> Dict:
        context = context or {}
        self._execution_context = context

        plan_type = self._detect_plan_type(goal)

        template = self.TEMPLATES.get(plan_type, [])
        if not template:
            template = [{"id": "step_1", "action": goal, "depends_on": [], "optional": False}]

        steps = []
        for step in template:
            step_copy = step.copy()
            step_copy["target"] = target
            step_copy["status"] = "pending"
            step_copy["result"] = None
            step_copy["reflection"] = None
            steps.append(step_copy)

        return {
            "plan_id": f"plan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
            "goal": goal,
            "target": target,
            "steps": steps,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }

    def _detect_plan_type(self, goal: str) -> str:
        goal_lower = goal.lower()

        if any(k in goal_lower for k in ["repair", "fix", "perbaiki", "perbaikan"]):
            return "repair"
        elif any(k in goal_lower for k in ["modify", "ubah", "tambah", "logic", "modifikasi"]):
            return "modify"
        elif any(k in goal_lower for k in ["analyze", "analisa", "audit", "analisis"]):
            return "analyze"
        elif any(k in goal_lower for k in ["scan", "scanning", "pindai"]):
            return "scan"
        elif any(k in goal_lower for k in ["trace", "track", "telusuri"]):
            return "trace"
        elif any(k in goal_lower for k in ["build", "bangun", "buat", "create"]):
            return "build"
        elif any(k in goal_lower for k in ["modify_project"]):
            return "modify_project"
        elif any(k in goal_lower for k in ["get_file", "get file"]):
            return "get_file"
        elif any(k in goal_lower for k in ["project_summary", "project summary"]):
            return "project_summary"
        elif any(k in goal_lower for k in ["show_log", "show log", "log"]):
            return "show_log"
        elif any(k in goal_lower for k in ["godmeme_status", "godmeme status"]):
            return "godmeme_status"
        elif any(k in goal_lower for k in ["run_bot", "run bot", "jalankan bot"]):
            return "run_bot"
        elif any(k in goal_lower for k in ["list_projects", "list projects", "daftar project"]):
            return "list_projects"
        elif any(k in goal_lower for k in ["business_analysis", "business analysis", "analisa bisnis"]):
            return "business_analysis"
        elif any(k in goal_lower for k in ["gallery", "galeri"]):
            return "gallery"
        elif any(k in goal_lower for k in ["video_info", "video info", "info video"]):
            return "video_info"
        elif any(k in goal_lower for k in ["autonomous", "autonomous_project"]):
            return "autonomous_project"
        else:
            return "analyze"

    def get_next_steps(self, plan: Dict) -> List[Dict]:
        steps = plan.get("steps", [])
        ready = []

        for step in steps:
            if step.get("status") != "pending":
                continue

            depends_on = step.get("depends_on", [])
            all_done = True

            for dep_id in depends_on:
                dep_step = self._find_step(steps, dep_id)
                if not dep_step or dep_step.get("status") not in ["completed", "skipped"]:
                    all_done = False
                    break

            if all_done:
                ready.append(step)

        return ready

    def _find_step(self, steps: List[Dict], step_id: str) -> Optional[Dict]:
        for step in steps:
            if step.get("id") == step_id:
                return step
        return None

    def update_step(self, plan: Dict, step_id: str, status: str, result: Any = None, reflection: Dict = None):
        steps = plan.get("steps", [])
        for step in steps:
            if step.get("id") == step_id:
                step["status"] = status
                if result is not None:
                    step["result"] = result
                if reflection is not None:
                    step["reflection"] = reflection
                break

        all_done = all(s.get("status") in ["completed", "skipped"] for s in steps)
        if all_done:
            plan["status"] = "completed"
        elif any(s.get("status") == "failed" for s in steps):
            plan["status"] = "failed"
        else:
            plan["status"] = "running"

        return plan

    def is_complete(self, plan: Dict) -> bool:
        return plan.get("status") in ["completed", "failed"]

    def plan_from_audit(self, audit_result: Dict, target: str = "godmeme_bot") -> Dict:
        features = audit_result.get("trace", {}).get("features", {})
        confidence = audit_result.get("trace", {}).get("confidence", 0)

        missing = []
        for name, files in features.items():
            if not files:
                missing.append(name)

        if missing:
            return self.plan("modify", target)

        if confidence < 90:
            return self.plan("analyze", target)

        return self.plan("analyze", target)

    def plan_with_reflection(self, plan: Dict, reflection: Dict) -> Dict:
        if reflection.get("should_retry", False):
            failed_step_id = reflection.get("step_id")
            steps = plan.get("steps", [])

            retry_step = {
                "id": f"retry_{failed_step_id}",
                "action": reflection.get("action", "analyze_project"),
                "target": plan.get("target"),
                "depends_on": [failed_step_id],
                "optional": False,
                "status": "pending",
                "result": None,
                "reflection": None
            }
            steps.append(retry_step)
            plan["steps"] = steps

        return plan
