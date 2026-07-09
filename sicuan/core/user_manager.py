"""
User Manager - Isolasi data per user
"""

import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime


class UserManager:
    """Kelola user dan data terisolasi"""

    def __init__(self):
        self.user_dir = Path("/home/dibs/agentjw/memory/users")
        self.user_dir.mkdir(exist_ok=True)
        self._load_index()

    def _load_index(self):
        """Load index user"""
        index_file = self.user_dir / "index.json"
        if index_file.exists():
            try:
                self.index = json.loads(index_file.read_text())
            except:
                self.index = {}
        else:
            self.index = {}

    def _save_index(self):
        """Save index user"""
        index_file = self.user_dir / "index.json"
        index_file.write_text(json.dumps(self.index, indent=2))

    def get_user_data(self, user_id: int) -> Dict:
        """Dapatkan data user"""
        user_id = str(user_id)
        user_file = self.user_dir / f"{user_id}.json"
        
        if user_file.exists():
            try:
                return json.loads(user_file.read_text())
            except:
                return self._create_user_data(user_id)
        else:
            return self._create_user_data(user_id)

    def _create_user_data(self, user_id: str) -> Dict:
        """Buat data user baru"""
        data = {
            "user_id": user_id,
            "username": "",
            "created_at": datetime.now().isoformat(),
            "projects": {},
            "preferences": {
                "private_mode": True,
                "language": "id",
                "notifications": True
            },
            "memory": {
                "last_topic": "",
                "context": []
            },
            "state": {
                "current_project": None,
                "last_action": None,
                "task_queue": []
            }
        }
        
        # Save
        user_file = self.user_dir / f"{user_id}.json"
        user_file.write_text(json.dumps(data, indent=2))
        
        # Update index
        if user_id not in self.index:
            self.index[user_id] = {
                "created_at": datetime.now().isoformat(),
                "username": ""
            }
            self._save_index()
        
        return data

    def save_user_data(self, user_id: int, data: Dict):
        """Simpan data user"""
        user_id = str(user_id)
        user_file = self.user_dir / f"{user_id}.json"
        user_file.write_text(json.dumps(data, indent=2))

    def get_project(self, user_id: int, project_name: str) -> Optional[Dict]:
        """Dapatkan project user"""
        data = self.get_user_data(user_id)
        return data["projects"].get(project_name)

    def set_project(self, user_id: int, project_name: str, project_data: Dict):
        """Set project user"""
        data = self.get_user_data(user_id)
        data["projects"][project_name] = project_data
        self.save_user_data(user_id, data)

    def get_preference(self, user_id: int, key: str, default=None):
        """Dapatkan preferensi user"""
        data = self.get_user_data(user_id)
        return data["preferences"].get(key, default)

    def set_preference(self, user_id: int, key: str, value):
        """Set preferensi user"""
        data = self.get_user_data(user_id)
        data["preferences"][key] = value
        self.save_user_data(user_id, data)

    def get_context(self, user_id: int) -> Dict:
        """Dapatkan context user"""
        data = self.get_user_data(user_id)
        return data["memory"]

    def update_context(self, user_id: int, context: Dict):
        """Update context user"""
        data = self.get_user_data(user_id)
        data["memory"].update(context)
        self.save_user_data(user_id, data)


    def is_owner(self, user_id: int) -> bool:
        """Cek apakah user adalah owner (Mas Gen)"""
        # Owner ID dari environment atau hardcode
        import os
        owner_id = int(os.getenv("OWNER_USER_ID", "5090639343"))
        return user_id == owner_id

    def get_user_projects(self, user_id: int) -> Dict:
        """Dapatkan project user (hanya milik user tersebut)"""
        data = self.get_user_data(user_id)
        return data.get("projects", {})
    def get_state(self, user_id: int) -> Dict:
        """Dapatkan state user"""
        data = self.get_user_data(user_id)
        return data["state"]

    def update_state(self, user_id: int, state: Dict):
        """Update state user"""
        data = self.get_user_data(user_id)
        data["state"].update(state)
        self.save_user_data(user_id, data)


# Singleton
_manager = None

def get_user_manager():
    global _manager
    if _manager is None:
        _manager = UserManager()
    return _manager