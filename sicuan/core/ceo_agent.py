"""
CEO Agent — Decision Maker, Prioritas, Resource, KPI, Strategy
"""
from typing import Dict, List, Optional
from datetime import datetime


class CEOAgent:
    """CEO Agent — Otak utama Business OS"""

    def __init__(self):
        self.divisions = {
            "engineering": {"priority": 1, "resource": 40, "status": "active"},
            "customer": {"priority": 2, "resource": 25, "status": "active"},
            "trading": {"priority": 3, "resource": 15, "status": "active"},
            "youtube": {"priority": 4, "resource": 10, "status": "idle"},
            "marketing": {"priority": 5, "resource": 5, "status": "idle"},
            "finance": {"priority": 6, "resource": 5, "status": "idle"}
        }
        self.kpi = {
            "daily_revenue": 0,
            "weekly_revenue": 0,
            "monthly_revenue": 0,
            "customer_satisfaction": 0,
            "project_completion_rate": 0
        }
        self.strategy = []
        self.decisions = []

    def set_priority(self, division: str, priority: int):
        if division in self.divisions:
            self.divisions[division]["priority"] = priority
            return {"status": "updated", "division": division, "priority": priority}
        return {"error": "Division not found"}

    def get_priorities(self) -> str:
        lines = []
        lines.append("📋 **PRIORITAS DIVISI**")
        lines.append("=" * 30)
        sorted_divs = sorted(self.divisions.items(), key=lambda x: x[1]["priority"])
        for name, data in sorted_divs:
            icon = "🟢" if data["status"] == "active" else "🟡" if data["status"] == "idle" else "🔴"
            lines.append(f"{icon} {name.capitalize()}: Priority {data['priority']} | Resource {data['resource']}%")
        return "\n".join(lines)

    def make_decision(self, context: str, options: List[str]) -> Dict:
        """Buat keputusan berdasarkan konteks"""
        decision = {
            "id": f"DEC-{len(self.decisions)+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "options": options,
            "chosen": options[0] if options else None,
            "status": "pending"
        }
        self.decisions.append(decision)
        return decision

    def approve_decision(self, decision_id: str, choice: str) -> Dict:
        for d in self.decisions:
            if d["id"] == decision_id:
                d["chosen"] = choice
                d["status"] = "approved"
                d["approved_at"] = datetime.now().isoformat()
                return d
        return {"error": "Decision not found"}

    def get_daily_brief(self) -> str:
        lines = []
        lines.append("📰 **CEO DAILY BRIEF**")
        lines.append("=" * 30)
        lines.append(f"📅 {datetime.now().strftime('%A, %d %B %Y')}")
        lines.append("")
        lines.append("📊 **KPI:**")
        lines.append(f"  Revenue: Rp {self.kpi['daily_revenue']:,}")
        lines.append(f"  Satisfaction: {self.kpi['customer_satisfaction']}%")
        lines.append(f"  Project Completion: {self.kpi['project_completion_rate']}%")
        lines.append("")
        lines.append("📋 **Prioritas Hari Ini:**")
        sorted_divs = sorted(self.divisions.items(), key=lambda x: x[1]["priority"])
        for name, data in sorted_divs[:3]:
            lines.append(f"  - {name.capitalize()} (Priority {data['priority']})")
        return "\n".join(lines)


_ceo = None


def get_ceo_agent() -> CEOAgent:
    global _ceo
    if _ceo is None:
        _ceo = CEOAgent()
    return _ceo
