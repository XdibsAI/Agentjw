"""
User Memory - Simpan preferensi privasi per user
"""

import json
from pathlib import Path
from typing import Dict, Optional


class UserMemory:
    """Memory per user untuk privasi dan preferensi"""

    def __init__(self):
        self.memory_file = Path("/home/dibs/agentjw/memory/user_memory.json")
        self._load()

    def _load(self):
        if self.memory_file.exists():
            try:
                self.data = json.loads(self.memory_file.read_text())
            except:
                self.data = {}
        else:
            self.data = {}

    def _save(self):
        self.memory_file.write_text(json.dumps(self.data, indent=2))


    def get_all_users(self) -> Dict:
        """Dapatkan semua user yang terdaftar"""
        return self.data

    def is_registered(self, user_id: int) -> bool:
        """Cek apakah user sudah terdaftar"""
        return str(user_id) in self.data
    def get_user_preference(self, user_id: int, key: str, default=None):
        """Dapatkan preferensi user"""
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {}
        return self.data[user_id].get(key, default)

    def set_user_preference(self, user_id: int, key: str, value):
        """Set preferensi user"""
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {}
        self.data[user_id][key] = value
        self._save()

    def is_private_mode(self, user_id: int) -> bool:
        """Cek apakah user ingin private mode"""
        return self.get_user_preference(user_id, "private_mode", True)

    def set_private_mode(self, user_id: int, enabled: bool):
        """Set private mode"""
        self.set_user_preference(user_id, "private_mode", enabled)


def get_user_memory():
    _memory = None
    if _memory is None:
        _memory = UserMemory()
    return _memory