"""
Context Manager - Kelola konteks percakapan secara struktural
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ContextManager:
    """Kelola konteks percakapan dengan struktur yang konsisten"""

    def __init__(self):
        self.context_file = Path("/home/dibs/agentjw/memory/conversation_context.json")
        self._context = self._load()

    def _load(self) -> Dict:
        """Load context dari file"""
        if self.context_file.exists():
            try:
                return json.loads(self.context_file.read_text())
            except:
                return self._default_context()
        return self._default_context()

    def _default_context(self) -> Dict:
        """Default context structure"""
        return {
            "last_topic": "",
            "last_action": "",
            "last_intent": "",
            "last_entity": "",
            "last_result": "",
            "topics": [],
            "actions": [],
            "entities": [],
            "current_focus": "",
            "session_id": ""
        }

    def get_current_topic(self) -> str:
        """Dapatkan topik saat ini"""
        return self._context.get("last_topic", "")

    def get_last_action(self) -> str:
        """Dapatkan action terakhir"""
        return self._context.get("last_action", "")

    def get_current_focus(self) -> str:
        """Dapatkan fokus saat ini (project/entity/channel)"""
        return self._context.get("current_focus", "")

    def set_current_focus(self, focus: str):
        """Set fokus saat ini"""
        self._context["current_focus"] = focus
        self._save()

    def is_focus_on(self, entity: str) -> bool:
        """Cek apakah fokus saat ini pada entity tertentu"""
        current = self._context.get("current_focus", "").lower()
        return entity.lower() in current or current in entity.lower()

    def get_recent_topics(self, count: int = 5) -> List[str]:
        """Dapatkan N topik terakhir"""
        topics = self._context.get("topics", [])
        return topics[-count:] if topics else []

    def get_context_summary(self) -> str:
        """Dapatkan ringkasan konteks untuk prompt"""
        lines = []
        lines.append("=== KONTEKS PERCAKAPAN ===")
        
        last_topic = self.get_current_topic()
        if last_topic:
            lines.append(f"Topik saat ini: {last_topic}")
        
        last_action = self.get_last_action()
        if last_action:
            lines.append(f"Action terakhir: {last_action}")
        
        current_focus = self.get_current_focus()
        if current_focus:
            lines.append(f"Fokus saat ini: {current_focus}")
        
        recent = self.get_recent_topics(3)
        if recent:
            lines.append("Topik terakhir:")
            for t in recent:
                lines.append(f"  - {t[:80]}")
        
        return "\n".join(lines)

    def is_same_topic(self, topic: str) -> bool:
        """Cek apakah topik ini sama dengan topik saat ini"""
        current = self.get_current_topic().lower()
        return topic.lower() in current or current in topic.lower()

    def update(self, topic: str = None, action: str = None, focus: str = None):
        """Update context"""
        if topic:
            self._context["last_topic"] = topic
            topics = self._context.get("topics", [])
            topics.append(topic)
            if len(topics) > 50:
                topics = topics[-50:]
            self._context["topics"] = topics
        
        if action:
            self._context["last_action"] = action
            actions = self._context.get("actions", [])
            actions.append(action)
            if len(actions) > 50:
                actions = actions[-50:]
            self._context["actions"] = actions
        
        if focus:
            self._context["current_focus"] = focus
        
        self._context["updated_at"] = datetime.now().isoformat()
        self._save()

    def _save(self):
        """Save context ke file"""
        try:
            self.context_file.write_text(json.dumps(self._context, indent=2))
        except Exception as e:
            print(f"[ContextManager] Error saving: {e}")

    def clear(self):
        """Clear context"""
        self._context = self._default_context()
        self._save()


_context_manager = None


def get_context_manager(user_id: Optional[str] = None) -> ContextManager:
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
