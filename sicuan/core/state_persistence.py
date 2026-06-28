"""
State Persistence - Simpan dan load conversation state
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from sicuan.core.conversation_state import ConversationState

# Gunakan path absolut yang benar
STATE_FILE = Path("/home/dibs/agentjw/memory/conversation_state.json")


def save_state(state: ConversationState) -> bool:
    """Save conversation state ke file"""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state.to_dict(), f, indent=2, default=str)
        print(f"[STATE] Saved to {STATE_FILE}")
        return True
    except Exception as e:
        print(f"[STATE] Error saving: {e}")
        return False


def load_state() -> Optional[ConversationState]:
    """Load conversation state dari file"""
    print(f"[STATE] Trying to load from {STATE_FILE}")
    if not STATE_FILE.exists():
        print("[STATE] No state file found")
        return None
    
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
        print(f"[STATE] Loaded data keys: {list(data.keys())}")
        
        # Buat state dari data
        state = ConversationState(
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
        print(f"[STATE] State loaded: {state.get_summary()[:100]}")
        return state
    except Exception as e:
        print(f"[STATE] Error loading: {e}")
        return None


def state_exists() -> bool:
    """Cek apakah ada state yang tersimpan"""
    exists = STATE_FILE.exists()
    print(f"[STATE] state_exists: {exists} ({STATE_FILE})")
    return exists
