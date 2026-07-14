"""
ProjectAdapter - Transparent data access layer for projects.
Currently backed by ProjectManager (SQLite).
Can be swapped to other backends without changing brain.py.
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from sicuan.platform.project_manager import get_project_manager


class ProjectAdapter:
    """Adapter untuk mengakses data project dengan backend yang bisa diganti"""

    def __init__(self):
        # Backend: ProjectManager (SQLite)
        self._pm = None
        self._cache = None

    def _get_pm(self):
        """Lazy-load ProjectManager"""
        if self._pm is None:
            self._pm = get_project_manager()
        return self._pm

    def get_projects(self, workspace_id: Optional[str] = None) -> List[Dict]:
        """
        Get all projects from ProjectManager.
        If workspace_id is provided, filter by workspace.
        """
        pm = self._get_pm()
        
        # If workspace_id not provided, try to get from active workspace
        if not workspace_id:
            # Try to get from workspace_state.json as fallback
            ws_file = Path("/home/dibs/agentjw/memory/workspace_state.json")
            if ws_file.exists():
                try:
                    data = json.loads(ws_file.read_text())
                    # Use first workspace from state or default
                    workspace_dir = Path("/home/dibs/agentjw/memory/workspaces")
                    workspaces = [d.name for d in workspace_dir.iterdir() if d.is_dir()]
                    if workspaces:
                        workspace_id = workspaces[0]
                except:
                    pass
        
        # If still no workspace_id, use default
        if not workspace_id:
            workspace_id = "default"
        
        # Get projects from ProjectManager
        try:
            projects = pm.list_projects(workspace_id)
            if projects:
                result = []
                for p in projects:
                    # ProjectManager returns dict with 'id' and 'name'
                    # We need to map to expected format for brain.py
                    result.append({
                        "name": p.get("name", p.get("id", "")),
                        "project_dir": p.get("data", {}).get("path", ""),
                        "path": p.get("data", {}).get("path", ""),
                        "python_files": p.get("data", {}).get("python_files", 0),
                        "status": p.get("data", {}).get("status", "active"),
                        "id": p.get("id", ""),
                    })
                return result
        except Exception as e:
            print(f"[ProjectAdapter] Error getting projects from ProjectManager: {e}")
        
        # Fallback: read from workspace_state.json
        return self._fallback_get_projects()

    def _fallback_get_projects(self) -> List[Dict]:
        """Fallback to workspace_state.json if ProjectManager fails"""
        ws_file = Path("/home/dibs/agentjw/memory/workspace_state.json")
        if not ws_file.exists():
            return []
        
        try:
            with open(ws_file, 'r') as f:
                data = json.load(f)
            projects_data = data.get("projects", {})
            result = []
            for name, info in projects_data.items():
                if name == "__pycache__":
                    continue
                result.append({
                    "name": name,
                    "project_dir": info.get("path", ""),
                    "path": info.get("path", ""),
                    "python_files": info.get("python_files", 0),
                    "status": info.get("status", "active"),
                    "id": name,
                })
            return result
        except Exception as e:
            print(f"[ProjectAdapter] Fallback error: {e}")
            return []

    def find_project(self, target: str, workspace_id: Optional[str] = None) -> Optional[Dict]:
        """
        Fuzzy-match a target string to a project name.
        This replicates the behavior of brain._find_project exactly.
        """
        projects = self.get_projects(workspace_id)
        
        if not projects:
            return None
        if not target:
            return projects[0] if projects else None

        t = target.lower()
        
        # 1) exact / substring either direction
        for p in projects:
            name = p["name"].lower()
            if name in t or t in name:
                return p
        
        # 2) token overlap (split on non-alnum)
        import re
        t_tokens = set(w for w in re.split(r"[^a-z0-9]+", t) if len(w) > 2)
        for p in projects:
            name_tokens = set(w for w in re.split(r"[^a-z0-9]+", p["name"].lower()) if len(w) > 2)
            if t_tokens & name_tokens:
                return p
        
        return None

    def get_project_by_name(self, name: str, workspace_id: Optional[str] = None) -> Optional[Dict]:
        """Get project by exact name"""
        projects = self.get_projects(workspace_id)
        for p in projects:
            if p["name"].lower() == name.lower():
                return p
        return None


# Singleton
_adapter = None

def get_project_adapter() -> ProjectAdapter:
    global _adapter
    if _adapter is None:
        _adapter = ProjectAdapter()
    return _adapter
