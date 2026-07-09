"""
Workspace - Platform Core dengan struktur scalable
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List


class Workspace:
    """Workspace dengan struktur scalable"""

    def __init__(self):
        self.workspace_dir = Path("/home/dibs/agentjw/memory/workspaces")
        self.workspace_dir.mkdir(exist_ok=True)

    def create(self, owner_id: int, name: str, config: Dict = None) -> Dict:
        """Buat workspace baru"""
        workspace_id = uuid.uuid4().hex[:16]
        
        # Buat folder workspace
        ws_dir = self.workspace_dir / workspace_id
        ws_dir.mkdir(exist_ok=True)
        
        # Workspace metadata
        metadata = {
            "id": workspace_id,
            "name": name,
            "owner_id": owner_id,
            "members": [
                {"id": owner_id, "role": "owner"}
            ],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "config": config or {},
            "billing": {
                "plan": "free",
                "quota": {
                    "monthly_tokens": 10000,
                    "used_tokens": 0,
                    "reset_date": datetime.now().replace(day=1).isoformat()
                }
            },
            "providers": {
                "openai": {"enabled": False},
                "anthropic": {"enabled": False},
                "groq": {"enabled": False},
                "openrouter": {"enabled": True}
            },
            "agents": [],
            "plugins": [],
            "settings": {
                "default_language": "id",
                "default_model": "deepseek/deepseek-chat"
            }
        }
        
        # Save metadata
        metadata_file = ws_dir / "workspace.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        
        # Buat folder untuk data
        for folder in ["memory", "projects", "logs", "tasks"]:
            (ws_dir / folder).mkdir(exist_ok=True)
        
        # Initialize memory DB
        self._init_memory(ws_dir)
        
        return metadata

    def _init_memory(self, ws_dir: Path):
        """Initialize memory database"""
        import sqlite3
        db_path = ws_dir / "memory" / "context.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp REAL,
                metadata TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provenance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                target TEXT,
                user_id INTEGER,
                timestamp REAL,
                result TEXT
            )
        """)
        conn.commit()
        conn.close()

    def get(self, workspace_id: str) -> Optional[Dict]:
        """Dapatkan workspace"""
        ws_dir = self.workspace_dir / workspace_id
        metadata_file = ws_dir / "workspace.json"
        if metadata_file.exists():
            return json.loads(metadata_file.read_text())
        return None

    def update(self, workspace_id: str, data: Dict) -> bool:
        """Update workspace"""
        ws_dir = self.workspace_dir / workspace_id
        metadata_file = ws_dir / "workspace.json"
        if metadata_file.exists():
            metadata = json.loads(metadata_file.read_text())
            metadata.update(data)
            metadata["updated_at"] = datetime.now().isoformat()
            metadata_file.write_text(json.dumps(metadata, indent=2))
            return True
        return False

    def add_member(self, workspace_id: str, user_id: int, role: str = "viewer") -> bool:
        """Tambah member"""
        workspace = self.get(workspace_id)
        if not workspace:
            return False
        
        for member in workspace["members"]:
            if member["id"] == user_id:
                return True
        
        workspace["members"].append({"id": user_id, "role": role})
        return self.update(workspace_id, workspace)

    def get_member_role(self, workspace_id: str, user_id: int) -> Optional[str]:
        """Dapatkan role member"""
        workspace = self.get(workspace_id)
        if not workspace:
            return None
        
        for member in workspace["members"]:
            if member["id"] == user_id:
                return member["role"]
        return None


def get_workspace():
    _workspace = None
    if _workspace is None:
        _workspace = Workspace()
    return _workspace
