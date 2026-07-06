"""
SOP Department — Standard Operating Procedures
"""

from typing import Dict, Any, List
from datetime import datetime

from sicuan.departments.base import Department


class SOPDepartment(Department):
    """SOP Department — Standard Operating Procedures"""

    def __init__(self, config: Dict = None):
        super().__init__("sop", config)
        self.sops = self._init_sops()

    def _init_sops(self) -> Dict:
        """Inisialisasi SOPs"""
        return {
            "trading_bot": {
                "name": "Trading Bot SOP",
                "version": "1.2",
                "steps": [
                    {"step": 1, "name": "Start Bot", "status": "active"},
                    {"step": 2, "name": "Monitor Positions", "status": "active"},
                    {"step": 3, "name": "Risk Check", "status": "active"},
                    {"step": 4, "name": "Exit Strategy", "status": "draft"},
                    {"step": 5, "name": "Report Generation", "status": "draft"}
                ],
                "last_updated": datetime.now().isoformat()
            },
            "ai_agent": {
                "name": "AI Agent SOP",
                "version": "1.0",
                "steps": [
                    {"step": 1, "name": "Receive Request", "status": "active"},
                    {"step": 2, "name": "Analyze Context", "status": "active"},
                    {"step": 3, "name": "Route Intent", "status": "active"},
                    {"step": 4, "name": "Execute Action", "status": "active"},
                    {"step": 5, "name": "Self-Review", "status": "active"}
                ],
                "last_updated": datetime.now().isoformat()
            }
        }

    def get_status(self) -> Dict:
        """Dapatkan status SOP"""
        return {
            "name": "SOP",
            "total_sops": len(self.sops),
            "active_sops": self._get_active_sops(),
            "sops": self.sops
        }

    def get_summary(self) -> str:
        """Dapatkan ringkasan SOP"""
        status = self.get_status()
        return f"""
📋 **SOP Summary**
  Total SOPs   : {status['total_sops']}
  Active SOPs  : {', '.join(status['active_sops'])}
"""

    def execute(self, action: str, params: Dict) -> Dict:
        """Eksekusi action SOP"""
        if action == "list":
            return {"status": "ok", "data": list(self.sops.keys())}
        elif action == "get":
            name = params.get("name")
            return {"status": "ok", "data": self.sops.get(name, {})}
        else:
            return {"error": f"Unknown action: {action}"}

    def _get_active_sops(self) -> List[str]:
        """Dapatkan SOP yang active"""
        active = []
        for sop in self.sops.values():
            if any(s.get("status") == "active" for s in sop.get("steps", [])):
                active.append(sop["name"])
        return active
