"""
Project Manager - Project per workspace
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime


class ProjectManager:
    """Kelola project per workspace"""

    def __init__(self):
        self.workspace_dir = Path("/home/dibs/agentjw/memory/workspaces")

    def _get_project_dir(self, workspace_id: str) -> Path:
        """Dapatkan folder project untuk workspace"""
        ws_dir = self.workspace_dir / workspace_id / "projects"
        ws_dir.mkdir(parents=True, exist_ok=True)
        return ws_dir

    def create_project(self, workspace_id: str, name: str, data: Dict = None) -> Dict:
        """Buat project baru di workspace"""
        project_dir = self._get_project_dir(workspace_id)
        project_id = name.lower().replace(" ", "_")
        
        project = {
            "id": project_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "data": data or {},
            "status": "active",
            "files": []
        }
        
        project_file = project_dir / f"{project_id}.json"
        project_file.write_text(json.dumps(project, indent=2))
        
        return project

    def get_project(self, workspace_id: str, project_id: str) -> Optional[Dict]:
        """Dapatkan project"""
        project_file = self._get_project_dir(workspace_id) / f"{project_id}.json"
        if project_file.exists():
            return json.loads(project_file.read_text())
        return None

    def list_projects(self, workspace_id: str) -> List[Dict]:
        """List semua project di workspace"""
        project_dir = self._get_project_dir(workspace_id)
        projects = []
        for f in project_dir.glob("*.json"):
            try:
                project = json.loads(f.read_text())
                projects.append(project)
            except:
                continue
        return projects

    def update_project(self, workspace_id: str, project_id: str, data: Dict) -> bool:
        """Update project"""
        project = self.get_project(workspace_id, project_id)
        if not project:
            return False
        
        project.update(data)
        project["updated_at"] = datetime.now().isoformat()
        
        project_file = self._get_project_dir(workspace_id) / f"{project_id}.json"
        project_file.write_text(json.dumps(project, indent=2))
        return True

    def delete_project(self, workspace_id: str, project_id: str) -> bool:
        """Delete project"""
        project_file = self._get_project_dir(workspace_id) / f"{project_id}.json"
        if project_file.exists():
            project_file.unlink()
            return True
        return False


def get_project_manager():
    _manager = None
    if _manager is None:
        _manager = ProjectManager()
    return _manager
