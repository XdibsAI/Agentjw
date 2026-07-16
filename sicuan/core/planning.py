"""
Planning Mode — Terinspirasi dari Claude Code
"""
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PlanStep:
    id: int
    description: str
    status: str = "pending"  # pending, in_progress, done, blocked
    result: Optional[str] = None
    dependencies: List[int] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class Plan:
    def __init__(self, goal: str):
        self.goal = goal
        self.steps: List[PlanStep] = []
        self.current_step = 0
        self.created_at = datetime.now().isoformat()
        self.completed = False

    def add_step(self, description: str, dependencies: List[int] = None) -> int:
        step_id = len(self.steps) + 1
        self.steps.append(PlanStep(
            id=step_id,
            description=description,
            dependencies=dependencies or []
        ))
        return step_id

    def get_next_step(self) -> Optional[PlanStep]:
        for step in self.steps:
            if step.status == "pending":
                # Cek dependencies
                all_done = all(
                    self.steps[d-1].status == "done" for d in step.dependencies
                )
                if all_done:
                    return step
        return None

    def mark_done(self, step_id: int, result: str = ""):
        for step in self.steps:
            if step.id == step_id:
                step.status = "done"
                step.result = result
                step.completed_at = datetime.now().isoformat()
                break

    def mark_blocked(self, step_id: int, reason: str = ""):
        for step in self.steps:
            if step.id == step_id:
                step.status = "blocked"
                step.result = reason
                break

    def to_string(self) -> str:
        lines = [f"📋 PLAN: {self.goal}"]
        lines.append("=" * 40)
        for step in self.steps:
            status_icon = {
                "pending": "⏳",
                "in_progress": "🔄",
                "done": "✅",
                "blocked": "🚫"
            }.get(step.status, "❓")
            lines.append(f"{status_icon} [{step.id}] {step.description}")
            if step.result:
                lines.append(f"   Result: {step.result}")
        return "\n".join(lines)


_plans = {}


def create_plan(goal: str) -> Plan:
    plan = Plan(goal)
    return plan


def get_plan(plan_id: str) -> Optional[Plan]:
    return _plans.get(plan_id)


def list_plans() -> List[str]:
    return list(_plans.keys())
