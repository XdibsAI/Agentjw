"""
interface/session.py - Persistent session management
"""
import json
from pathlib import Path
from core.config import config

SESSION_FILE = config.LOGS_DIR / ".session_state.json"

def load_session() -> dict:
    if SESSION_FILE.exists():
        try:
            return json.loads(SESSION_FILE.read_text())
        except Exception:
            pass
    return {}

def save_session(data: dict):
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps(data, indent=2, default=str))

def get_or_create_session_id() -> str:
    import uuid
    state = load_session()
    if "session_id" not in state:
        state["session_id"] = str(uuid.uuid4())
        save_session(state)
    return state["session_id"]
