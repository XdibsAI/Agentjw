"""
Workspace Resolver - Mapping Telegram chat ke Workspace
"""

import json
from pathlib import Path
from typing import Dict, Optional


class WorkspaceResolver:
    """Resolve Telegram chat/group ke workspace"""

    def __init__(self):
        self.mapping_dir = Path("/home/dibs/agentjw/memory/workspace_mappings")
        self.mapping_dir.mkdir(exist_ok=True)
        self._load_mappings()

    def _load_mappings(self):
        """Load all mappings"""
        self.mappings = {}
        mapping_file = self.mapping_dir / "mappings.json"
        if mapping_file.exists():
            try:
                self.mappings = json.loads(mapping_file.read_text())
            except:
                self.mappings = {}

    def _save_mappings(self):
        """Save mappings"""
        mapping_file = self.mapping_dir / "mappings.json"
        mapping_file.write_text(json.dumps(self.mappings, indent=2))

    def register_chat(self, chat_id: int, workspace_id: str, chat_type: str = "group") -> bool:
        """Register chat ke workspace"""
        chat_id = str(chat_id)
        self.mappings[chat_id] = {
            "workspace_id": workspace_id,
            "chat_type": chat_type,
            "registered_at": __import__('datetime').datetime.now().isoformat()
        }
        self._save_mappings()
        return True

    def resolve(self, chat_id: int) -> Optional[str]:
        """Resolve chat_id ke workspace_id"""
        chat_id = str(chat_id)
        mapping = self.mappings.get(chat_id)
        if mapping:
            return mapping["workspace_id"]
        return None

    def get_workspace_chats(self, workspace_id: str) -> list:
        """Dapatkan semua chat untuk workspace"""
        result = []
        for chat_id, mapping in self.mappings.items():
            if mapping["workspace_id"] == workspace_id:
                result.append({
                    "chat_id": int(chat_id),
                    "chat_type": mapping["chat_type"]
                })
        return result


def get_workspace_resolver():
    _resolver = None
    if _resolver is None:
        _resolver = WorkspaceResolver()
    return _resolver
