"""
Task Tracker - Lacak task yang sedang dikerjakan
"""

from datetime import datetime
from typing import Dict, Optional


class TaskTracker:
    """Lacak status task"""

    def __init__(self):
        self.current_task: Optional[Dict] = None
        self.history = []

    def start_task(self, description: str, action: str, target: str):
        """Mulai task baru"""
        self.current_task = {
            "description": description,
            "action": action,
            "target": target,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress"
        }
        self.history.append(self.current_task)

    def complete_task(self, result: str = ""):
        """Selesaikan task"""
        if self.current_task:
            self.current_task["status"] = "completed"
            self.current_task["completed_at"] = datetime.now().isoformat()
            self.current_task["result"] = result

    def get_status(self) -> str:
        """Dapatkan status task"""
        if not self.current_task:
            return "Tidak ada task yang sedang dikerjakan."
        
        task = self.current_task
        return f"Task: {task['description']} | Status: {task['status']} | Action: {task['action']}"

    def reset(self):
        """Reset task"""
        self.current_task = None
