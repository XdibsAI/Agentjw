"""
Self Improvement Engine — Evaluate, Learn, Improve, Repeat
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class SelfImprovementEngine:
    """Self Improvement Engine — Agent belajar dari pengalaman"""

    def __init__(self):
        self.log_file = Path("/home/dibs/agentjw/memory/self_improvement.json")
        self._data = self._load()

    def _load(self) -> Dict:
        if self.log_file.exists():
            try:
                return json.loads(self.log_file.read_text())
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "history": [],
            "metrics": {
                "total_bugs_fixed": 0,
                "total_customers_served": 0,
                "total_campaigns": 0,
                "total_revenue": 0,
                "avg_satisfaction": 0,
                "improvement_notes": []
            }
        }

    def _save(self):
        self.log_file.write_text(json.dumps(self._data, indent=2))

    def record_day(self, metrics: Dict) -> Dict:
        """Catat hasil hari ini"""
        entry = {
            "date": datetime.now().isoformat(),
            "metrics": metrics,
            "improvements": [],
            "lessons": []
        }
        self._data["history"].append(entry)
        
        # Update total metrics
        m = self._data["metrics"]
        m["total_bugs_fixed"] += metrics.get("bugs_fixed", 0)
        m["total_customers_served"] += metrics.get("customers_served", 0)
        m["total_campaigns"] += metrics.get("campaigns", 0)
        m["total_revenue"] += metrics.get("revenue", 0)
        
        self._save()
        return entry

    def add_lesson(self, lesson: str):
        """Tambahkan pelajaran"""
        self._data["metrics"]["improvement_notes"].append({
            "timestamp": datetime.now().isoformat(),
            "lesson": lesson
        })
        self._save()

    def get_daily_report(self) -> str:
        """Dapatkan laporan self improvement"""
        if not self._data["history"]:
            return "Belum ada data improvement"
        
        last = self._data["history"][-1]
        metrics = last.get("metrics", {})
        improvements = last.get("improvements", [])
        lessons = last.get("lessons", [])
        
        lines = []
        lines.append("📈 **SELF IMPROVEMENT REPORT**")
        lines.append("=" * 30)
        lines.append(f"📅 {last['date'][:16]}")
        lines.append("")
        lines.append("📊 **Today's Metrics:**")
        lines.append(f"  Bugs Fixed: {metrics.get('bugs_fixed', 0)}")
        lines.append(f"  Customers Served: {metrics.get('customers_served', 0)}")
        lines.append(f"  Campaigns: {metrics.get('campaigns', 0)}")
        lines.append(f"  Revenue: Rp {metrics.get('revenue', 0):,}")
        lines.append("")
        if lessons:
            lines.append("💡 **Lessons Learned:**")
            for l in lessons:
                lines.append(f"  - {l}")
        return "\n".join(lines)

    def get_summary(self) -> str:
        """Dapatkan ringkasan total"""
        m = self._data["metrics"]
        lines = []
        lines.append("📊 **SELF IMPROVEMENT SUMMARY**")
        lines.append("=" * 30)
        lines.append(f"🐛 Total Bugs Fixed: {m['total_bugs_fixed']}")
        lines.append(f"👥 Total Customers Served: {m['total_customers_served']}")
        lines.append(f"📢 Total Campaigns: {m['total_campaigns']}")
        lines.append(f"💰 Total Revenue: Rp {m['total_revenue']:,}")
        lines.append(f"📝 Total Lessons: {len(m['improvement_notes'])}")
        return "\n".join(lines)


_improvement = None


def get_self_improvement() -> SelfImprovementEngine:
    global _improvement
    if _improvement is None:
        _improvement = SelfImprovementEngine()
    return _improvement
