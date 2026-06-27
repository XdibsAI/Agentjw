"""
WorkflowContext - Shared context untuk workflow
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class WorkflowContext:
    """
    WorkflowContext - tempat shared data antar step dalam workflow.
    
    Setiap handler bisa membaca dan mengisi shared_data.
    Ini memungkinkan step berikutnya menggunakan hasil step sebelumnya.
    """
    
    def __init__(self, goal: str = "", target: str = "", context: dict = None):
        self.goal = goal
        self.target = target
        self.context = context or {}
        self.steps: List[Dict] = []
        self.completed: List[Dict] = []
        self.failed: List[Dict] = []
        self.shared_data: Dict = {}
        self.metadata: Dict = {
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
    
    def add_step(self, step: Dict):
        """Tambahkan step ke workflow"""
        step["status"] = "pending"
        self.steps.append(step)
    
    def update_step(self, step_id: str, status: str, result: Any = None, error: str = None):
        """Update status step"""
        for step in self.steps:
            if step.get("id") == step_id:
                step["status"] = status
                if result is not None:
                    step["result"] = result
                    self.shared_data[f"step_{step_id}_result"] = result
                if error is not None:
                    step["error"] = error
                break
        
        if status == "completed":
            self.completed.append({"step_id": step_id, "timestamp": datetime.utcnow().isoformat()})
        elif status == "failed":
            self.failed.append({"step_id": step_id, "timestamp": datetime.utcnow().isoformat()})
        
        self.metadata["updated_at"] = datetime.utcnow().isoformat()
    
    def get_result(self, step_id: str) -> Optional[Any]:
        """Dapatkan hasil dari step sebelumnya"""
        return self.shared_data.get(f"step_{step_id}_result")
    
    def set_data(self, key: str, value: Any):
        """Set shared data"""
        self.shared_data[key] = value
        self.metadata["updated_at"] = datetime.utcnow().isoformat()
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get shared data"""
        return self.shared_data.get(key, default)
    
    def get_last_result(self) -> Optional[Any]:
        """Dapatkan hasil step terakhir yang completed"""
        if self.completed:
            last = self.completed[-1]
            return self.get_result(last.get("step_id"))
        return None
    
    def is_complete(self) -> bool:
        """Cek apakah semua step selesai"""
        pending = [s for s in self.steps if s.get("status") == "pending"]
        return len(pending) == 0
    
    def has_failed(self) -> bool:
        """Cek apakah ada step yang gagal"""
        return len(self.failed) > 0
    
    def to_dict(self) -> dict:
        """Convert ke dictionary"""
        return {
            "goal": self.goal,
            "target": self.target,
            "context": self.context,
            "steps": self.steps,
            "completed": self.completed,
            "failed": self.failed,
            "shared_data": self.shared_data,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert ke JSON"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WorkflowContext':
        """Create from dictionary"""
        ctx = cls(
            goal=data.get("goal", ""),
            target=data.get("target", ""),
            context=data.get("context", {})
        )
        ctx.steps = data.get("steps", [])
        ctx.completed = data.get("completed", [])
        ctx.failed = data.get("failed", [])
        ctx.shared_data = data.get("shared_data", {})
        ctx.metadata = data.get("metadata", {})
        return ctx
