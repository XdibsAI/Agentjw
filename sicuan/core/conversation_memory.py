"""
Conversation Memory - Mengingat konteks percakapan
"""

from typing import Dict, List, Optional
from datetime import datetime


class ConversationMemory:
    """Mengingat konteks percakapan"""
    
    def __init__(self):
        self.current_project: Optional[str] = None
        self.last_file: Optional[str] = None
        self.last_action: Optional[str] = None
        self.pending_tasks: List[str] = []
        self.conversation_style: str = "santai"
        self.mood: str = "netral"
        self.context: Dict = {}
        self.history: List[Dict] = []
    
    def update(self, **kwargs):
        """Update memory"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def add_interaction(self, user_message: str, response: str):
        """Tambahkan interaksi ke history"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message[:200],
            "response": response[:200]
        })
        # Keep last 50 interactions
        if len(self.history) > 50:
            self.history = self.history[-50:]
    
    def get_context(self) -> str:
        """Dapatkan ringkasan konteks"""
        lines = []
        if self.current_project:
            lines.append(f"Project: {self.current_project}")
        if self.last_file:
            lines.append(f"Last file: {self.last_file}")
        if self.last_action:
            lines.append(f"Last action: {self.last_action}")
        if self.pending_tasks:
            lines.append(f"Pending tasks: {', '.join(self.pending_tasks)}")
        if self.mood != "netral":
            lines.append(f"Mood: {self.mood}")
        return "\n".join(lines) if lines else "Tidak ada konteks"
    
    def get_recent_history(self, limit: int = 3) -> str:
        """Dapatkan history terbaru"""
        if not self.history:
            return "Belum ada percakapan"
        lines = []
        for h in self.history[-limit:]:
            lines.append(f"User: {h['user'][:50]}...")
            lines.append(f"SiCuan: {h['response'][:50]}...")
        return "\n".join(lines)
