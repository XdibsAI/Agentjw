"""
Conversation Slot - Ingat konteks percakapan
"""

from typing import Dict, Optional


class ConversationSlot:
    """Menyimpan konteks percakapan: file, error, project"""

    def __init__(self):
        self.slots = {
            "current_file": None,
            "current_error": None,
            "current_project": "godmeme_bot",
            "last_action": None,
            "last_topic": None,
            "error_context": None,
        }

    def set(self, key: str, value: any):
        """Set slot value"""
        if key in self.slots:
            self.slots[key] = value

    def get(self, key: str) -> any:
        """Get slot value"""
        return self.slots.get(key)

    def set_error(self, error: Dict):
        """Set error context"""
        self.slots["current_error"] = error
        self.slots["error_context"] = error.get("context", "")

    def clear_error(self):
        """Clear error context"""
        self.slots["current_error"] = None
        self.slots["error_context"] = None

    def get_context(self) -> str:
        """Get context summary"""
        lines = []
        if self.slots["current_file"]:
            lines.append(f"Current file: {self.slots['current_file']}")
        if self.slots["current_error"]:
            error = self.slots["current_error"]
            lines.append(f"Error: {error.get('msg', '')} at line {error.get('line', '')}")
        if self.slots["last_topic"]:
            lines.append(f"Last topic: {self.slots['last_topic']}")
        return "\n".join(lines) if lines else "No context"


# Singleton
_slot = None

def get_conversation_slot():
    global _slot
    if _slot is None:
        _slot = ConversationSlot()
    return _slot
