"""
HR Department — Team Management & Culture
"""

from typing import Dict, Any, List
from datetime import datetime

from sicuan.departments.base import Department


class HRDepartment(Department):
    """HR Department — Team Management & Culture"""

    def __init__(self, config: Dict = None):
        super().__init__("hr", config)
        self.team = self._init_team()

    def _init_team(self) -> Dict:
        """Inisialisasi tim"""
        return {
            "members": [
                {"name": "SiCuan", "role": "AI Partner", "status": "active"},
                {"name": "User", "role": "CEO / Founder", "status": "active"}
            ],
            "culture": {
                "values": ["Autonomous", "Data-driven", "Continuous Improvement"],
                "working_hours": "24/7",
                "communication": "Telegram + Vault"
            },
            "projects": [
                {"name": "Godmeme Bot", "status": "active"},
                {"name": "Flask Todo API", "status": "active"},
                {"name": "SiCuan AI", "status": "active"}
            ],
            "last_updated": datetime.now().isoformat()
        }

    def get_status(self) -> Dict:
        """Dapatkan status HR"""
        return {
            "name": "HR",
            "team_size": len(self.team.get("members", [])),
            "active_members": self._get_active_members(),
            "projects": self.team.get("projects", []),
            "culture": self.team.get("culture", {})
        }

    def get_summary(self) -> str:
        """Dapatkan ringkasan HR"""
        status = self.get_status()
        return f"""
👥 **HR Summary**
  Team Size      : {status['team_size']}
  Active Members : {', '.join(status['active_members'])}
  Projects       : {len(status['projects'])}
  Culture        : {', '.join(status['culture'].get('values', []))}
"""

    def execute(self, action: str, params: Dict) -> Dict:
        """Eksekusi action HR"""
        if action == "team":
            return {"status": "ok", "data": self.team["members"]}
        elif action == "projects":
            return {"status": "ok", "data": self.team["projects"]}
        elif action == "add_member":
            name = params.get("name")
            role = params.get("role", "Member")
            self.team["members"].append({"name": name, "role": role, "status": "active"})
            self.team["last_updated"] = datetime.now().isoformat()
            return {"status": "ok", "message": f"Member '{name}' added"}
        else:
            return {"error": f"Unknown action: {action}"}

    def _get_active_members(self) -> List[str]:
        """Dapatkan member active"""
        return [m["name"] for m in self.team.get("members", []) if m.get("status") == "active"]
