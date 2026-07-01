"""
Goal Engine - Extended Goal Management dengan Priority & Progress Tracking
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid


class GoalPriority:
    """Prioritas Goal"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    
    @classmethod
    def values(cls):
        return [cls.CRITICAL, cls.HIGH, cls.MEDIUM, cls.LOW]


class GoalStatus:
    """Status Goal"""
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    PAUSED = "paused"
    
    @classmethod
    def values(cls):
        return [cls.ACTIVE, cls.IN_PROGRESS, cls.COMPLETED, cls.FAILED, cls.BLOCKED, cls.PAUSED]


class GoalEngine:
    """
    Extended Goal Manager dengan:
    - Priority levels
    - Progress tracking
    - Sub-goals
    - Task management
    - Auto-prioritization
    """
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.goals_file = self.memory_dir / "goals_engine.json"
        self.goals: Dict[str, Dict] = {}
        self.active_goal_id: Optional[str] = None
        self._load()
    
    def create_goal(
        self,
        title: str,
        description: str = "",
        priority: str = GoalPriority.MEDIUM,
        parent_id: str = None,
        success_criteria: List[str] = None,
        tasks: List[str] = None
    ) -> Dict:
        """Buat goal baru"""
        goal_id = f"goal_{uuid.uuid4().hex[:8]}"
        
        goal = {
            "id": goal_id,
            "title": title,
            "description": description,
            "priority": priority,
            "status": GoalStatus.ACTIVE,
            "parent_id": parent_id,
            "sub_goals": [],
            "tasks": tasks or [],
            "completed_tasks": [],
            "blocked_tasks": [],
            "success_criteria": success_criteria or [],
            "progress": 0.0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        self.goals[goal_id] = goal
        
        if parent_id and parent_id in self.goals:
            self.goals[parent_id]["sub_goals"].append(goal_id)
        
        if not self.active_goal_id or priority == GoalPriority.CRITICAL:
            self.active_goal_id = goal_id
        
        self._save()
        print(f"[GOAL] Created: {title} (priority={priority})")
        return goal
    
    def get_goal(self, goal_id: str) -> Optional[Dict]:
        return self.goals.get(goal_id)
    
    def get_active_goal(self) -> Optional[Dict]:
        if self.active_goal_id:
            return self.goals.get(self.active_goal_id)
        return None
    
    def get_priority_goals(self, limit: int = 5) -> List[Dict]:
        priority_order = {
            GoalPriority.CRITICAL: 0,
            GoalPriority.HIGH: 1,
            GoalPriority.MEDIUM: 2,
            GoalPriority.LOW: 3
        }
        
        active_goals = [g for g in self.goals.values() if g["status"] != GoalStatus.COMPLETED]
        sorted_goals = sorted(
            active_goals,
            key=lambda g: (priority_order.get(g["priority"], 99), -g["progress"])
        )
        return sorted_goals[:limit]
    
    def update_progress(self, goal_id: str, progress: float):
        goal = self.get_goal(goal_id)
        if goal:
            goal["progress"] = min(100, max(0, progress))
            goal["updated_at"] = datetime.now().isoformat()
            if goal["progress"] >= 100:
                goal["status"] = GoalStatus.COMPLETED
                goal["completed_at"] = datetime.now().isoformat()
            self._save()
            print(f"[GOAL] Progress updated: {goal['title']} = {progress}%")
    
    def add_task(self, goal_id: str, task: str):
        goal = self.get_goal(goal_id)
        if goal and task not in goal["tasks"]:
            goal["tasks"].append(task)
            goal["updated_at"] = datetime.now().isoformat()
            self._save()
            print(f"[GOAL] Task added: {task} -> {goal['title']}")
    
    def complete_task(self, goal_id: str, task: str):
        goal = self.get_goal(goal_id)
        if goal and task in goal["tasks"]:
            goal["tasks"].remove(task)
            goal["completed_tasks"].append(task)
            total = len(goal["tasks"]) + len(goal["completed_tasks"])
            if total > 0:
                progress = (len(goal["completed_tasks"]) / total) * 100
                self.update_progress(goal_id, progress)
    
    def get_summary(self, goal_id: str = None) -> str:
        if goal_id:
            goal = self.get_goal(goal_id)
            if not goal:
                return "Goal tidak ditemukan"
            return self._format_goal(goal)
        return self.get_all_summary()
    
    def get_all_summary(self) -> str:
        if not self.goals:
            return "Belum ada goals yang dibuat."
        
        lines = ["📋 GOALS SUMMARY", "=" * 40]
        
        for goal in self.get_priority_goals(10):
            status_icon = {
                GoalStatus.ACTIVE: "🟢",
                GoalStatus.IN_PROGRESS: "🟡",
                GoalStatus.COMPLETED: "✅",
                GoalStatus.FAILED: "❌",
                GoalStatus.BLOCKED: "🔴",
                GoalStatus.PAUSED: "⏸️"
            }.get(goal["status"], "⚪")
            
            lines.append(f"{status_icon} {goal['title']} ({goal['progress']:.0f}%)")
            lines.append(f"   Priority: {goal['priority']} | Tasks: {len(goal['tasks'])}")
        
        return "\n".join(lines)
    
    def _format_goal(self, goal: Dict) -> str:
        lines = [
            f"🎯 {goal['title']}",
            f"   Deskripsi: {goal['description']}",
            f"   Prioritas: {goal['priority']}",
            f"   Status: {goal['status']}",
            f"   Progress: {goal['progress']:.1f}%",
            f"   Tasks: {len(goal['tasks'])} tersisa",
            f"   Completed: {len(goal['completed_tasks'])}"
        ]
        
        if goal.get("success_criteria"):
            lines.append("   Kriteria sukses:")
            for c in goal["success_criteria"][:3]:
                lines.append(f"     - {c}")
        
        if goal.get("tasks"):
            lines.append("   Tasks tersisa:")
            for t in goal["tasks"][:5]:
                lines.append(f"     - {t}")
        
        return "\n".join(lines)
    
    def _save(self):
        data = {
            "goals": self.goals,
            "active_goal_id": self.active_goal_id,
            "updated_at": datetime.now().isoformat()
        }
        with open(self.goals_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        if not self.goals_file.exists():
            return
        
        try:
            with open(self.goals_file, "r") as f:
                data = json.load(f)
            self.goals = data.get("goals", {})
            self.active_goal_id = data.get("active_goal_id")
            print(f"[GOAL] Loaded {len(self.goals)} goals from {self.goals_file}")
        except Exception as e:
            print(f"[GOAL] Failed to load: {e}")
