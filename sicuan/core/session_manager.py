"""
Session Manager — Load/save session per user
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List


class SessionManager:
    """Kelola session per user"""

    def __init__(self, user_id: str):
        self.user_id = str(user_id)
        self.session_dir = Path("/home/dibs/agentjw/memory/sessions")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / f"{self.user_id}.json"
        self._session = self._load()

    def _load(self) -> Dict:
        if self.session_file.exists():
            try:
                return json.loads(self.session_file.read_text())
            except:
                return self._default_session()
        return self._default_session()

    def _default_session(self) -> Dict:
        return {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": "",
            "last_topic": "",
            "last_action": "",
            "topics": [],
            "actions": [],
            "context": {},
            "session_id": ""
        }

    def save(self):
        self._session["updated_at"] = datetime.now().isoformat()
        self.session_file.write_text(json.dumps(self._session, indent=2))

    def update_topic(self, topic: str):
        self._session["last_topic"] = topic
        topics = self._session.get("topics", [])
        topics.append(topic)
        if len(topics) > 50:
            topics = topics[-50:]
        self._session["topics"] = topics
        self.save()

    def update_action(self, action: str):
        self._session["last_action"] = action
        actions = self._session.get("actions", [])
        actions.append(action)
        if len(actions) > 50:
            actions = actions[-50:]
        self._session["actions"] = actions
        self.save()

    def get_context(self) -> str:
        topics = self._session.get("topics", [])
        last_topic = self._session.get("last_topic", "")
        if not topics and not last_topic:
            return ""
        lines = ["=== SESSION CONTEXT ==="]
        if last_topic:
            lines.append(f"Topik terakhir: {last_topic}")
        if topics:
            lines.append("Topik sebelumnya:")
            for t in topics[-5:]:
                lines.append(f"  - {t[:100]}")
        return "\n".join(lines)


_sessions = {}


def get_session_manager(user_id: str) -> SessionManager:
    global _sessions
    if user_id not in _sessions:
        _sessions[user_id] = SessionManager(user_id)
    return _sessions[user_id]
