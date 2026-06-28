"""
Conversation State - Mengelola state percakapan
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationState:

    @classmethod
    def from_dict(cls, data: dict) -> 'ConversationState':
        """Create ConversationState dari dict"""
        return cls(
            project=data.get("project"),
            last_action=data.get("last_action"),
            last_result=data.get("last_result"),
            status=data.get("status", "idle"),
            current_task=data.get("current_task"),
            completed_tasks=data.get("completed_tasks", []),
            pending_tasks=data.get("pending_tasks", []),
            goal=data.get("goal"),
            updated_at=data.get("updated_at", datetime.now().isoformat())
        )

    """State percakapan SiCuan"""
    
    # Proyek aktif
    project: Optional[str] = None
    
    # Aksi terakhir
    last_action: Optional[str] = None
    last_result: Optional[str] = None
    
    # Status pekerjaan
    status: str = "idle"  # idle, running, completed, waiting
    
    # Task management
    current_task: Optional[str] = None
    completed_tasks: List[str] = field(default_factory=list)
    pending_tasks: List[str] = field(default_factory=list)
    
    # Goal
    goal: Optional[str] = None
    
    # Timestamp
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_completed_task(self, task: str):
        """Tambahkan task ke completed"""
        if task not in self.completed_tasks:
            self.completed_tasks.append(task)
        self.updated_at = datetime.now().isoformat()
    
    def add_pending_task(self, task: str):
        """Tambahkan task ke pending"""
        if task not in self.pending_tasks:
            self.pending_tasks.append(task)
        self.updated_at = datetime.now().isoformat()
    
    def get_next_task(self) -> Optional[str]:
        """Dapatkan task berikutnya"""
        if self.pending_tasks:
            return self.pending_tasks[0]
        return None
    
    def advance_task(self):
        """Pindah ke task berikutnya"""
        if self.pending_tasks:
            next_task = self.pending_tasks.pop(0)
            self.current_task = next_task
            self.updated_at = datetime.now().isoformat()
            return next_task
        return None
    
    def get_summary(self) -> str:
        """Dapatkan ringkasan state"""
        lines = []
        if self.project:
            lines.append(f"Project: {self.project}")
        if self.current_task:
            lines.append(f"Current task: {self.current_task}")
        if self.completed_tasks:
            lines.append(f"Completed: {', '.join(self.completed_tasks)}")
        if self.pending_tasks:
            lines.append(f"Pending: {', '.join(self.pending_tasks)}")
        if self.last_result:
            lines.append(f"Last result: {self.last_result[:100]}...")
        return "\n".join(lines) if lines else "Tidak ada state"
    
    def to_dict(self) -> Dict:
        """Convert ke dict"""
        return {
            "project": self.project,
            "last_action": self.last_action,
            "last_result": self.last_result,
            "status": self.status,
            "current_task": self.current_task,
            "completed_tasks": self.completed_tasks,
            "pending_tasks": self.pending_tasks,
            "goal": self.goal,
            "updated_at": self.updated_at
        }
