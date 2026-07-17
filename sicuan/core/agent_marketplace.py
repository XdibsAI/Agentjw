"""
Agent Marketplace — Pasang dan lepas agent seperti plugin
"""
import json
from pathlib import Path
from typing import Dict, List, Optional


class AgentMarketplace:
    """Agent Marketplace — Modular agents"""

    def __init__(self):
        self.marketplace_file = Path("/home/dibs/agentjw/memory/marketplace.json")
        self._data = self._load()
        self.agents_dir = Path("/home/dibs/agentjw/agents/modules")
        self.agents_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict:
        if self.marketplace_file.exists():
            try:
                return json.loads(self.marketplace_file.read_text())
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "installed": [],
            "available": [
                {
                    "id": "coding_agent",
                    "name": "Coding Agent",
                    "description": "Generate, review, and repair code",
                    "version": "1.0.0",
                    "dependencies": ["python", "ast"],
                    "active": True
                },
                {
                    "id": "sales_agent",
                    "name": "Sales Agent",
                    "description": "CRM, negotiation, closing",
                    "version": "1.0.0",
                    "dependencies": [],
                    "active": True
                },
                {
                    "id": "support_agent",
                    "name": "Support Agent",
                    "description": "Troubleshooting, customer handling",
                    "version": "1.0.0",
                    "dependencies": [],
                    "active": True
                },
                {
                    "id": "marketing_agent",
                    "name": "Marketing Agent",
                    "description": "Campaigns, broadcasts, promotions",
                    "version": "1.0.0",
                    "dependencies": [],
                    "active": False
                },
                {
                    "id": "finance_agent",
                    "name": "Finance Agent",
                    "description": "Invoices, payments, balance",
                    "version": "1.0.0",
                    "dependencies": [],
                    "active": False
                },
                {
                    "id": "youtube_agent",
                    "name": "YouTube Agent",
                    "description": "Channel analytics, content strategy",
                    "version": "1.0.0",
                    "dependencies": ["youtube_api"],
                    "active": False
                },
                {
                    "id": "trading_agent",
                    "name": "Trading Agent",
                    "description": "Market analysis, trading strategies",
                    "version": "1.0.0",
                    "dependencies": ["dex_screener", "jupiter"],
                    "active": False
                }
            ]
        }

    def _save(self):
        self.marketplace_file.write_text(json.dumps(self._data, indent=2))

    def install_agent(self, agent_id: str) -> Dict:
        """Install agent dari marketplace"""
        for agent in self._data["available"]:
            if agent["id"] == agent_id:
                if agent_id not in self._data["installed"]:
                    self._data["installed"].append(agent_id)
                    agent["active"] = True
                    self._save()
                    return {"status": "installed", "agent": agent}
                return {"status": "already_installed", "agent": agent}
        return {"error": "Agent not found"}

    def uninstall_agent(self, agent_id: str) -> Dict:
        """Uninstall agent"""
        if agent_id in self._data["installed"]:
            self._data["installed"].remove(agent_id)
            for agent in self._data["available"]:
                if agent["id"] == agent_id:
                    agent["active"] = False
                    break
            self._save()
            return {"status": "uninstalled", "agent_id": agent_id}
        return {"error": "Agent not installed"}

    def get_installed_agents(self) -> List[Dict]:
        """Dapatkan daftar agent terinstall"""
        return [a for a in self._data["available"] if a["id"] in self._data["installed"]]

    def get_available_agents(self) -> List[Dict]:
        """Dapatkan daftar agent tersedia"""
        return [a for a in self._data["available"] if a["id"] not in self._data["installed"]]

    def get_status(self) -> str:
        """Dapatkan status marketplace"""
        installed = self.get_installed_agents()
        available = self.get_available_agents()
        
        lines = []
        lines.append("🛒 **AGENT MARKETPLACE**")
        lines.append("=" * 30)
        lines.append(f"📦 Installed: {len(installed)} agents")
        lines.append(f"📦 Available: {len(available)} agents")
        lines.append("")
        lines.append("✅ **Installed:**")
        for a in installed:
            lines.append(f"  - {a['name']} v{a['version']} ({a['id']})")
        lines.append("")
        lines.append("📥 **Available:**")
        for a in available[:5]:
            lines.append(f"  - {a['name']} ({a['description'][:40]}...)")
        return "\n".join(lines)


_marketplace = None


def get_agent_marketplace() -> AgentMarketplace:
    global _marketplace
    if _marketplace is None:
        _marketplace = AgentMarketplace()
    return _marketplace
