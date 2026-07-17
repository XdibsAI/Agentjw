"""
Permission Engine — Kontrol izin setiap agent
"""
import json
from pathlib import Path
from typing import Dict, List, Optional


class PermissionEngine:
    """Permission Engine — Atur izin agent"""

    def __init__(self):
        self.permission_file = Path("/home/dibs/agentjw/memory/permissions.json")
        self._data = self._load()

    def _load(self) -> Dict:
        if self.permission_file.exists():
            try:
                return json.loads(self.permission_file.read_text())
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "agents": {
                "ceo": {
                    "permissions": ["read", "plan", "assign", "approve"],
                    "restrictions": ["delete_project", "delete_database", "transfer_funds"],
                    "level": 10
                },
                "coder": {
                    "permissions": ["read", "modify_code", "create_code"],
                    "restrictions": ["git_push", "deploy", "delete_project"],
                    "level": 8
                },
                "reviewer": {
                    "permissions": ["read", "review_code", "approve_changes"],
                    "restrictions": ["modify_code", "deploy"],
                    "level": 7
                },
                "deployer": {
                    "permissions": ["deploy", "rollback"],
                    "restrictions": ["delete_database", "modify_code"],
                    "level": 6
                },
                "finance": {
                    "permissions": ["read", "create_invoice", "view_payment"],
                    "restrictions": ["transfer_funds", "delete_transaction"],
                    "level": 5
                },
                "support": {
                    "permissions": ["read", "create_ticket", "view_customer"],
                    "restrictions": ["modify_code", "deploy"],
                    "level": 4
                }
            },
            "roles": {
                "admin": ["ceo", "coder", "reviewer", "deployer", "finance", "support"],
                "developer": ["coder", "reviewer"],
                "operator": ["deployer", "support"],
                "viewer": ["support"]
            }
        }

    def _save(self):
        self.permission_file.write_text(json.dumps(self._data, indent=2))

    def has_permission(self, agent: str, action: str) -> bool:
        """Cek apakah agent memiliki izin untuk action tertentu"""
        agent_data = self._data["agents"].get(agent)
        if not agent_data:
            return False
        
        permissions = agent_data.get("permissions", [])
        restrictions = agent_data.get("restrictions", [])
        
        if action in restrictions:
            return False
        if action in permissions:
            return True
        
        # Cek role-based
        for role, agents in self._data["roles"].items():
            if agent in agents:
                if self._role_has_permission(role, action):
                    return True
        
        return False

    def _role_has_permission(self, role: str, action: str) -> bool:
        """Cek apakah role memiliki izin"""
        role_permissions = {
            "admin": ["read", "write", "delete", "deploy", "manage"],
            "developer": ["read", "modify_code", "review_code"],
            "operator": ["read", "deploy", "rollback", "support"],
            "viewer": ["read", "view_customer", "create_ticket"]
        }
        return action in role_permissions.get(role, [])

    def get_agent_permissions(self, agent: str) -> str:
        """Dapatkan daftar izin agent"""
        agent_data = self._data["agents"].get(agent)
        if not agent_data:
            return f"Agent {agent} tidak ditemukan"
        
        lines = []
        lines.append(f"🔐 **{agent.capitalize()} Agent**")
        lines.append("=" * 30)
        lines.append(f"Level: {agent_data.get('level', 0)}")
        lines.append("")
        lines.append("✅ **Permissions:**")
        for p in agent_data.get("permissions", []):
            lines.append(f"  ✓ {p.replace('_', ' ').title()}")
        lines.append("")
        lines.append("🚫 **Restrictions:**")
        for r in agent_data.get("restrictions", []):
            lines.append(f"  ✗ {r.replace('_', ' ').title()}")
        return "\n".join(lines)

    def can_execute(self, agent: str, action: str) -> Dict:
        """Cek dan return detail izin"""
        allowed = self.has_permission(agent, action)
        return {
            "agent": agent,
            "action": action,
            "allowed": allowed,
            "reason": "Permission granted" if allowed else "Permission denied or restricted"
        }


_permission = None


def get_permission_engine() -> PermissionEngine:
    global _permission
    if _permission is None:
        _permission = PermissionEngine()
    return _permission
