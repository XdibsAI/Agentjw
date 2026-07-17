"""
Capability Registry — Profil kemampuan setiap agent
"""
import json
from pathlib import Path
from typing import Dict, List


class CapabilityRegistry:
    """Registry kemampuan agent"""

    def __init__(self):
        self.registry_file = Path("/home/dibs/agentjw/memory/capabilities.json")
        self._data = self._load()

    def _load(self) -> Dict:
        if self.registry_file.exists():
            try:
                data = json.loads(self.registry_file.read_text())
                # Validasi data
                if "agents" not in data:
                    return self._default()
                return data
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "agents": {
                "coder": {
                    "skills": {
                        "python": 95,
                        "javascript": 70,
                        "rust": 20,
                        "go": 30,
                        "sql": 80
                    },
                    "experience": 0,
                    "success_rate": 0
                },
                "reviewer": {
                    "skills": {
                        "code_review": 90,
                        "security": 75,
                        "performance": 70
                    },
                    "experience": 0,
                    "success_rate": 0
                },
                "sales": {
                    "skills": {
                        "negotiation": 85,
                        "crm": 80,
                        "presentation": 75,
                        "closing": 70
                    },
                    "experience": 0,
                    "success_rate": 0
                },
                "support": {
                    "skills": {
                        "troubleshooting": 90,
                        "customer_handling": 85,
                        "communication": 80
                    },
                    "experience": 0,
                    "success_rate": 0
                }
            }
        }

    def _save(self):
        self.registry_file.write_text(json.dumps(self._data, indent=2))

    def get_agent_skills(self, agent_name: str) -> Dict:
        """Dapatkan skill agent"""
        return self._data["agents"].get(agent_name, {}).get("skills", {})

    def get_skill_level(self, agent_name: str, skill: str) -> int:
        """Dapatkan level skill tertentu"""
        return self._data["agents"].get(agent_name, {}).get("skills", {}).get(skill, 0)

    def update_skill(self, agent_name: str, skill: str, level: int):
        """Update skill level"""
        if "agents" not in self._data:
            self._data = self._default()
        if agent_name not in self._data["agents"]:
            self._data["agents"][agent_name] = {"skills": {}, "experience": 0, "success_rate": 0}
        self._data["agents"][agent_name]["skills"][skill] = level
        self._save()

    def increment_experience(self, agent_name: str, amount: int = 1):
        """Tambah pengalaman agent"""
        if agent_name in self._data["agents"]:
            self._data["agents"][agent_name]["experience"] += amount
            self._save()

    def update_success_rate(self, agent_name: str, success: bool):
        """Update success rate"""
        if agent_name in self._data["agents"]:
            current = self._data["agents"][agent_name].get("success_rate", 0)
            exp = self._data["agents"][agent_name].get("experience", 1)
            # Weighted average
            new_rate = ((current * (exp - 1)) + (100 if success else 0)) / exp
            self._data["agents"][agent_name]["success_rate"] = round(new_rate, 1)
            self._save()

    def get_agent_profile(self, agent_name: str) -> str:
        """Dapatkan profil agent dalam format string"""
        agent = self._data["agents"].get(agent_name)
        if not agent:
            return f"Agent {agent_name} tidak ditemukan"
        
        skills = agent.get("skills", {})
        exp = agent.get("experience", 0)
        rate = agent.get("success_rate", 0)
        
        lines = []
        lines.append(f"🤖 **{agent_name.capitalize()} Agent**")
        lines.append(f"📊 Experience: {exp} tasks")
        lines.append(f"📈 Success Rate: {rate}%")
        lines.append("🎯 **Skills:**")
        for skill, level in sorted(skills.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * (level // 10) + "░" * (10 - (level // 10))
            lines.append(f"  {skill}: {bar} {level}%")
        return "\n".join(lines)


_registry = None


def get_capability_registry() -> CapabilityRegistry:
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry
