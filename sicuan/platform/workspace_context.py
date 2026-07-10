"""
Workspace Context - Menyimpan konteks per workspace
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class WorkspaceContext:
    """Context manager per workspace"""
    
    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.context_dir = Path(f"/home/dibs/agentjw/memory/workspace_contexts/{workspace_id}")
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self.context_file = self.context_dir / "context.json"
        self._load()
    
    def _load(self):
        if self.context_file.exists():
            self.data = json.loads(self.context_file.read_text())
        else:
            self.data = {
                "workspace_id": self.workspace_id,
                "current_project": None,
                "current_folder": None,
                "current_file": None,
                "current_task": None,
                "history": [],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
    
    def _save(self):
        self.data["updated_at"] = datetime.now().isoformat()
        self.context_file.write_text(json.dumps(self.data, indent=2))
    
    def set_current_project(self, project_id: str):
        self.data["current_project"] = project_id
        self._save()
    
    def set_current_folder(self, folder: str):
        self.data["current_folder"] = folder
        self._save()
    
    def set_current_file(self, file: str):
        self.data["current_file"] = file
        self._save()
    
    def set_current_task(self, task: str):
        self.data["current_task"] = task
        self._save()
    
    def add_history(self, action: str, data: Dict):
        self.data["history"].append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "data": data
        })
        # Keep last 100 entries
        if len(self.data["history"]) > 100:
            self.data["history"] = self.data["history"][-100:]
        self._save()
    
    def get_context(self) -> Dict:
        return self.data
    
    def get_current_project(self) -> Optional[str]:
        return self.data.get("current_project")
    
    def get_current_folder(self) -> Optional[str]:
        return self.data.get("current_folder")
    
    def get_current_file(self) -> Optional[str]:
        return self.data.get("current_file")
    
    def get_current_task(self) -> Optional[str]:
        return self.data.get("current_task")


def get_workspace_context(workspace_id: str) -> WorkspaceContext:
    return WorkspaceContext(workspace_id)
