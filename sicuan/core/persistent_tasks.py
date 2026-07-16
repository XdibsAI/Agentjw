"""
Persistent Tasks — Big goals → small tasks → disk
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class PersistentTask:
    def __init__(self, id: str, description: str, goal: str = ""):
        self.id = id
        self.description = description
        self.goal = goal
        self.status = "pending"  # pending, in_progress, done, blocked, archived
        self.dependencies = []
        self.result = None
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.completed_at = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "goal": self.goal,
            "status": self.status,
            "dependencies": self.dependencies,
            "result": self.result,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "PersistentTask":
        task = cls(data["id"], data["description"], data.get("goal", ""))
        task.status = data.get("status", "pending")
        task.dependencies = data.get("dependencies", [])
        task.result = data.get("result")
        task.created_at = data.get("created_at", datetime.now().isoformat())
        task.updated_at = data.get("updated_at", task.created_at)
        task.completed_at = data.get("completed_at")
        return task


class TaskStore:
    def __init__(self, storage_path: Path = Path("/home/dibs/agentjw/memory/tasks.json")):
        self.storage_path = storage_path
        self.tasks: Dict[str, PersistentTask] = {}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for task_data in data.get("tasks", []):
                    task = PersistentTask.from_dict(task_data)
                    self.tasks[task.id] = task
            except:
                pass

    def _save(self):
        data = {
            "tasks": [t.to_dict() for t in self.tasks.values()],
            "updated_at": datetime.now().isoformat()
        }
        self.storage_path.write_text(json.dumps(data, indent=2))

    def create(self, description: str, goal: str = "") -> PersistentTask:
        import uuid
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = PersistentTask(task_id, description, goal)
        self.tasks[task_id] = task
        self._save()
        return task

    def get(self, task_id: str) -> Optional[PersistentTask]:
        return self.tasks.get(task_id)

    def list_by_status(self, status: str) -> List[PersistentTask]:
        return [t for t in self.tasks.values() if t.status == status]

    def list_by_goal(self, goal: str) -> List[PersistentTask]:
        return [t for t in self.tasks.values() if t.goal == goal]

    def update_status(self, task_id: str, status: str, result: str = None):
        task = self.get(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now().isoformat()
            if result:
                task.result = result
            if status == "done":
                task.completed_at = datetime.now().isoformat()
            self._save()

    def delete(self, task_id: str):
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save()


_task_store = None


def get_task_store() -> TaskStore:
    global _task_store
    if _task_store is None:
        _task_store = TaskStore()
    return _task_store
