"""
State Recovery — Auto-recovery setelah crash/reboot
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class StateRecovery:
    """
    Manajemen state dengan auto-recovery
    """
    
    def __init__(self, state_path: Optional[Path] = None):
        self.state_path = state_path or Path("memory/state.json")
        self.state: Dict[str, Any] = {}
        self._load()
        self._check_recovery()
    
    def _load(self):
        if self.state_path.exists():
            try:
                self.state = json.loads(self.state_path.read_text())
                print(f"[STATE] Loaded state: {len(self.state)} keys")
            except:
                self.state = {}
    
    def _save(self):
        self.state["_updated_at"] = time.time()
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=2))
    
    def _check_recovery(self):
        """Check if recovery is needed"""
        if self.state.get("_status") == "running":
            print("[STATE] ⚠️  Previous session was running — attempting recovery")
            self.state["_recovered"] = True
            self.state["_recovered_at"] = time.time()
            self._save()
    
    def save_state(self, key: str, value: Any):
        self.state[key] = value
        self.state["_status"] = "running"
        self._save()
    
    def get_state(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)
    
    def mark_complete(self):
        self.state["_status"] = "completed"
        self._save()
    
    def mark_failed(self, error: str):
        self.state["_status"] = "failed"
        self.state["_error"] = error
        self._save()
    
    def get_workflow_state(self, workflow_id: str) -> Optional[Dict]:
        workflows = self.state.get("workflows", {})
        return workflows.get(workflow_id)
    
    def save_workflow_state(self, workflow_id: str, step: int, data: Dict):
        if "workflows" not in self.state:
            self.state["workflows"] = {}
        if workflow_id not in self.state["workflows"]:
            self.state["workflows"][workflow_id] = {"steps": []}
        self.state["workflows"][workflow_id]["steps"].append({
            "step": step,
            "data": data,
            "timestamp": time.time()
        })
        self._save()
    
    def get_stats(self) -> Dict:
        return {
            "keys": len(self.state),
            "recovered": self.state.get("_recovered", False),
            "recovered_at": self.state.get("_recovered_at"),
            "status": self.state.get("_status", "unknown"),
            "workflows": len(self.state.get("workflows", {}))
        }

# Singleton
_recovery = None

def get_state_recovery() -> StateRecovery:
    global _recovery
    if _recovery is None:
        _recovery = StateRecovery()
    return _recovery
