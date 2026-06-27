"""
Runtime Bus - Read/write runtime state.
Setiap operasi: load → modify → save (tanpa cache di memory).
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Dict, List

ROOT = Path("/home/dibs/agentjw")
RUNTIME_FILE = ROOT / "sicuan_audit_report" / "runtime_state.json"


class RuntimeBus:
    """Read/write layer untuk runtime state - load → modify → save"""
    
    def __init__(self):
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Pastikan file state ada"""
        RUNTIME_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not RUNTIME_FILE.exists():
            self._save(self._default_state())
    
    def _default_state(self) -> dict:
        """Default state"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "active_projects": [],
            "active_agents": [],
            "active_capabilities": [],
            "runtime_status": {},
            "execution_history": [],
            "reflections": [],
            "errors": [],
            "task_count": 0,
            "success_count": 0,
            "failure_count": 0,
        }
    
    def _load(self) -> dict:
        """Load state dari file"""
        try:
            return json.loads(RUNTIME_FILE.read_text())
        except:
            return self._default_state()
    
    def _save(self, state: dict):
        """Save state ke file"""
        state["timestamp"] = datetime.utcnow().isoformat()
        RUNTIME_FILE.write_text(json.dumps(state, indent=2, default=str))
    
    # ===== Read Methods =====
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from state - load setiap kali"""
        state = self._load()
        return state.get(key, default)
    
    def get_all(self) -> dict:
        """Get entire state"""
        return self._load()
    
    def get_execution_history(self, limit: int = 50) -> List[Dict]:
        """Get last N execution history"""
        state = self._load()
        history = state.get("execution_history", [])
        return history[-limit:] if history else []
    
    def get_reflections(self, limit: int = 20) -> List[Dict]:
        """Get last N reflections"""
        state = self._load()
        reflections = state.get("reflections", [])
        return reflections[-limit:] if reflections else []
    
    def get_errors(self, limit: int = 20) -> List[Dict]:
        """Get last N errors"""
        state = self._load()
        errors = state.get("errors", [])
        return errors[-limit:] if errors else []
    
    # ===== Write Methods =====
    
    def set(self, key: str, value: Any):
        """Set value dan save langsung - load → modify → save"""
        state = self._load()
        state[key] = value
        self._save(state)
    
    def update(self, data: dict):
        """Update multiple keys - load → modify → save"""
        state = self._load()
        state.update(data)
        self._save(state)
    
    def add_execution(self, task: dict, result: dict, duration: float = 0):
        """Tambahkan execution history dengan status task - load → modify → save"""
        state = self._load()
        
        history = state.get("execution_history", [])
        history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task.get("id"),
            "action": task.get("action"),
            "target": task.get("target"),
            "success": result.get("success", False),
            "summary": result.get("summary", ""),
            "duration": duration,
            "status": "completed" if result.get("success", False) else "failed",
            "started_at": task.get("created_at"),
            "finished_at": datetime.utcnow().isoformat(),
        })
        if len(history) > 100:
            history = history[-100:]
        state["execution_history"] = history
        
        # Update counters
        state["task_count"] = state.get("task_count", 0) + 1
        if result.get("success", False):
            state["success_count"] = state.get("success_count", 0) + 1
        else:
            state["failure_count"] = state.get("failure_count", 0) + 1
        
        self._save(state)
    
    def add_reflection(self, reflection: dict):
        """Tambahkan reflection - load → modify → save"""
        state = self._load()
        
        reflections = state.get("reflections", [])
        reflections.append({
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": reflection.get("task_id"),
            "action": reflection.get("action"),
            "valid": reflection.get("validation", {}).get("valid", False),
            "confidence": reflection.get("confidence", 0),
            "should_retry": reflection.get("should_retry", False),
            "next_action": reflection.get("next_action"),
            "reason": reflection.get("reason", ""),
            "learned": reflection.get("learned", []),
        })
        if len(reflections) > 50:
            reflections = reflections[-50:]
        state["reflections"] = reflections
        self._save(state)
    
    def add_error(self, task: dict, result: dict, validation: dict):
        """Tambahkan error - load → modify → save"""
        state = self._load()
        
        errors = state.get("errors", [])
        errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "task_id": task.get("id"),
            "action": task.get("action"),
            "target": task.get("target"),
            "error": result.get("error", "Unknown error"),
            "validation": validation,
        })
        if len(errors) > 50:
            errors = errors[-50:]
        state["errors"] = errors
        self._save(state)
    
    def update_project_status(self, project_name: str, status: str, details: dict = None):
        """Update status project - load → modify → save"""
        state = self._load()
        
        statuses = state.get("runtime_status", {})
        statuses[project_name] = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        state["runtime_status"] = statuses
        self._save(state)
    
    def get_stats(self) -> dict:
        """Dapatkan statistik - load setiap kali"""
        state = self._load()
        total = state.get("task_count", 0)
        success = state.get("success_count", 0)
        failure = state.get("failure_count", 0)
        
        return {
            "task_count": total,
            "success_count": success,
            "failure_count": failure,
            "success_rate": round((success / total * 100) if total > 0 else 0, 2),
        }
    def clear(self):
        """Reset state"""
        self._save(self._default_state())
