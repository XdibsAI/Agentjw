"""
Attribution Learner - Belajar dari attribution data
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict


class AttributionLearner:
    """Belajar dari trade attribution untuk improve strategy"""

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.attribution_file = self.memory_dir / "attribution_learnings.json"
        self.learnings = {}
        self._load()

    def update(self, attribution: Dict):
        """Update learning dari attribution"""
        reasons = attribution.get("reasons", [])
        patterns = attribution.get("patterns", [])
        win = attribution.get("win", False)
        
        # Update reason stats
        for reason in reasons:
            key = f"reason_{reason}"
            if key not in self.learnings:
                self.learnings[key] = {"total": 0, "wins": 0, "losses": 0}
            self.learnings[key]["total"] += 1
            if win:
                self.learnings[key]["wins"] += 1
            else:
                self.learnings[key]["losses"] += 1
        
        # Update pattern stats
        for pattern in patterns:
            key = f"pattern_{pattern}"
            if key not in self.learnings:
                self.learnings[key] = {"total": 0, "wins": 0, "losses": 0}
            self.learnings[key]["total"] += 1
            if win:
                self.learnings[key]["wins"] += 1
            else:
                self.learnings[key]["losses"] += 1
        
        self._save()

    def get_insights(self) -> List[Dict]:
        """Dapatkan insights untuk improvement"""
        insights = []
        
        for key, data in self.learnings.items():
            total = data["total"]
            if total < 3:
                continue
            
            wins = data["wins"]
            win_rate = (wins / total) * 100
            
            if win_rate < 30:
                insights.append({
                    "type": "avoid",
                    "key": key,
                    "win_rate": win_rate,
                    "total": total,
                    "suggestion": f"Hindari {key.replace('_', ' ')} (win_rate: {win_rate:.1f}%)"
                })
            elif win_rate > 70:
                insights.append({
                    "type": "encourage",
                    "key": key,
                    "win_rate": win_rate,
                    "total": total,
                    "suggestion": f"Perhatikan {key.replace('_', ' ')} (win_rate: {win_rate:.1f}%)"
                })
        
        return sorted(insights, key=lambda x: x["win_rate"])

    def get_summary(self) -> str:
        """Dapatkan summary learnings"""
        insights = self.get_insights()
        
        lines = []
        lines.append("📊 **Attribution Learning Summary**")
        lines.append("")
        
        if not insights:
            lines.append("Belum cukup data untuk learning.")
            return "\n".join(lines)
        
        avoid = [i for i in insights if i["type"] == "avoid"]
        encourage = [i for i in insights if i["type"] == "encourage"]
        
        if avoid:
            lines.append("❌ **Avoid these patterns:**")
            for i in avoid[:5]:
                lines.append(f"  • {i['suggestion']}")
            lines.append("")
        
        if encourage:
            lines.append("✅ **Encourage these patterns:**")
            for i in encourage[:5]:
                lines.append(f"  • {i['suggestion']}")
            lines.append("")
        
        return "\n".join(lines)

    def _load(self):
        """Load dari disk"""
        if self.attribution_file.exists():
            try:
                self.learnings = json.loads(self.attribution_file.read_text())
            except:
                self.learnings = {}

    def _save(self):
        """Save ke disk"""
        self.attribution_file.write_text(json.dumps(self.learnings, indent=2))


# Singleton
_learner = None

def get_attribution_learner():
    global _learner
    if _learner is None:
        _learner = AttributionLearner()
    return _learner
