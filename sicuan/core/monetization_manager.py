"""
Monetization Manager — Mencari dan mengelola peluang cuan
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class MonetizationManager:
    """Monetization Manager — Cari peluang pendapatan"""

    def __init__(self):
        self.data_file = Path("/home/dibs/agentjw/memory/monetization.json")
        self._data = self._load()

    def _load(self) -> Dict:
        if self.data_file.exists():
            try:
                return json.loads(self.data_file.read_text())
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "opportunities": [],
            "projects": {},
            "revenue": {
                "total": 0,
                "monthly": 0,
                "by_project": {}
            },
            "reports": []
        }

    def _save(self):
        self.data_file.write_text(json.dumps(self._data, indent=2))

    def analyze_project(self, project_name: str, completion: int, category: str, potential: int) -> Dict:
        """Analisis potensi monetisasi project"""
        opportunity = {
            "id": f"OPP-{len(self._data['opportunities'])+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "project": project_name,
            "completion": completion,
            "category": category,  # SaaS, API, Subscription, White Label, etc
            "potential": potential,  # Estimated monthly revenue in IDR
            "priority_score": self._calculate_priority(completion, potential),
            "status": "pending",
            "action_plan": []
        }
        self._data["opportunities"].append(opportunity)
        self._save()
        return opportunity

    def _calculate_priority(self, completion: int, potential: int) -> int:
        """Hitung priority score"""
        # Completion weight: 60%, Potential weight: 40%
        return int((completion * 0.6) + ((potential / 100) * 40))

    def get_priorities(self) -> List[Dict]:
        """Dapatkan daftar prioritas monetisasi"""
        sorted_ops = sorted(
            self._data["opportunities"],
            key=lambda x: x["priority_score"],
            reverse=True
        )
        return sorted_ops

    def get_report(self) -> str:
        """Dapatkan laporan monetisasi"""
        opportunities = self.get_priorities()
        total_potential = sum(o["potential"] for o in opportunities)
        
        lines = []
        lines.append("💰 **MONETIZATION REPORT**")
        lines.append("=" * 30)
        lines.append(f"📅 {datetime.now().strftime('%d %B %Y')}")
        lines.append(f"📊 Total Opportunities: {len(opportunities)}")
        lines.append(f"💵 Total Potential: Rp {total_potential:,}/bulan")
        lines.append("")
        lines.append("🎯 **Priorities:**")
        
        for i, opp in enumerate(opportunities[:5], 1):
            status_icon = "🟢" if opp["status"] == "active" else "🟡" if opp["status"] == "pending" else "🔴"
            lines.append(f"{status_icon} {i}. **{opp['project']}**")
            lines.append(f"   Completion: {opp['completion']}% | Potential: Rp {opp['potential']:,}/bulan")
            lines.append(f"   Category: {opp['category']} | Priority: {opp['priority_score']}/100")
            lines.append("")
        
        return "\n".join(lines)


_monetization = None


def get_monetization_manager() -> MonetizationManager:
    global _monetization
    if _monetization is None:
        _monetization = MonetizationManager()
    return _monetization
