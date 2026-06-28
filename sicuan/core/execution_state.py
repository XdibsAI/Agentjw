"""
Execution State - Melacak progress tugas
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExecutionState:
    """State eksekusi tugas"""
    
    task: Optional[str] = None
    total_steps: int = 0
    completed_steps: int = 0
    current_step: Optional[str] = None
    checkpoint: Optional[Dict] = None
    artifacts: Dict = field(default_factory=dict)
    status: str = "idle"  # idle, running, paused, completed
    started_at: Optional[str] = None
    paused_at: Optional[str] = None
    resumed_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def start(self, task: str, total_steps: int = 0):
        """Mulai tugas"""
        self.task = task
        self.total_steps = total_steps
        self.completed_steps = 0
        self.status = "running"
        self.started_at = datetime.now().isoformat()
    
    def progress(self, step: str, checkpoint: Dict = None):
        """Update progress"""
        self.completed_steps += 1
        self.current_step = step
        if checkpoint:
            self.checkpoint = checkpoint
        # Auto-update total jika belum diset
        if self.total_steps == 0 and self.completed_steps > 0:
            self.total_steps = 1
    
    def pause(self):
        """Pause tugas"""
        self.status = "paused"
        self.paused_at = datetime.now().isoformat()
    
    def resume(self):
        """Resume tugas"""
        self.status = "running"
        self.resumed_at = datetime.now().isoformat()
    
    def complete(self):
        """Selesai"""
        self.status = "completed"
        self.completed_at = datetime.now().isoformat()
    
    def get_progress(self) -> str:
        """Dapatkan progress string"""
        if self.total_steps == 0:
            return f"Task: {self.task} (no progress tracking)"
        return f"{self.completed_steps}/{self.total_steps} - Current: {self.current_step}"
    

    def get_progress_percent(self) -> float:
        """Dapatkan progress dalam persen"""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100
    
    def get_progress_bar(self, width: int = 20) -> str:
        """Dapatkan progress bar"""
        percent = self.get_progress_percent()
        filled = int((percent / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"{bar} {percent:.0f}%"
    def get_summary(self) -> str:
        """Dapatkan ringkasan"""
        lines = []
        if self.task:
            lines.append(f"Task: {self.task}")
        if self.total_steps > 0:
            lines.append(f"Progress: {self.completed_steps}/{self.total_steps}")
        if self.current_step:
            lines.append(f"Current: {self.current_step}")
        if self.checkpoint:
            lines.append(f"Checkpoint: {self.checkpoint}")
        if self.status != "idle":
            lines.append(f"Status: {self.status}")
        return "\n".join(lines) if lines else "No execution state"
