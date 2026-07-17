"""
Continuous Learning Pipeline — Knowledge yang terus berkembang
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ContinuousLearning:
    """Continuous Learning — Belajar dari setiap interaksi"""

    def __init__(self):
        self.learnings_file = Path("/home/dibs/agentjw/memory/learnings.json")
        self._data = self._load()

    def _load(self) -> Dict:
        if self.learnings_file.exists():
            try:
                return json.loads(self.learnings_file.read_text())
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "learnings": [],
            "categories": {
                "trading": [],
                "coding": [],
                "customer": [],
                "marketing": [],
                "finance": [],
                "youtube": []
            },
            "stats": {
                "total_learnings": 0,
                "last_learning": None
            }
        }

    def _save(self):
        self.learnings_file.write_text(json.dumps(self._data, indent=2))

    def add_learning(self, topic: str, insight: str, category: str = "general", source: str = "interaction"):
        """Tambahkan pembelajaran baru"""
        learning = {
            "id": f"LRN-{len(self._data['learnings'])+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "insight": insight,
            "category": category,
            "source": source,
            "applied": False,
            "result": None
        }
        self._data["learnings"].append(learning)
        
        if category in self._data["categories"]:
            self._data["categories"][category].append(learning["id"])
        
        self._data["stats"]["total_learnings"] += 1
        self._data["stats"]["last_learning"] = learning["timestamp"]
        self._save()
        return learning

    def get_learnings(self, category: str = None, limit: int = 10) -> List[Dict]:
        """Dapatkan pembelajaran berdasarkan kategori"""
        if category:
            ids = self._data["categories"].get(category, [])
            return [l for l in self._data["learnings"] if l["id"] in ids][-limit:]
        return self._data["learnings"][-limit:]

    def mark_applied(self, learning_id: str, result: str):
        """Tandai pembelajaran sudah diterapkan"""
        for l in self._data["learnings"]:
            if l["id"] == learning_id:
                l["applied"] = True
                l["result"] = result
                self._save()
                return l
        return None

    def get_summary(self) -> str:
        """Dapatkan ringkasan pembelajaran"""
        total = self._data["stats"]["total_learnings"]
        last = self._data["stats"]["last_learning"]
        
        lines = []
        lines.append("📚 **CONTINUOUS LEARNING SUMMARY**")
        lines.append("=" * 30)
        lines.append(f"📊 Total Learnings: {total}")
        lines.append(f"🕐 Last: {last[:16] if last else 'Never'}")
        lines.append("")
        lines.append("📂 **By Category:**")
        for cat, ids in self._data["categories"].items():
            if ids:
                lines.append(f"  - {cat.capitalize()}: {len(ids)}")
        return "\n".join(lines)

    def get_context(self, query: str) -> str:
        """Dapatkan konteks dari pembelajaran"""
        results = []
        query_lower = query.lower()
        for l in self._data["learnings"]:
            if query_lower in l["topic"].lower() or query_lower in l["insight"].lower():
                results.append(l)
        
        if not results:
            return ""
        
        lines = ["📚 **Relevant Learnings:**"]
        for l in results[-3:]:
            status = "✅" if l["applied"] else "⏳"
            lines.append(f"  {status} {l['topic']}: {l['insight'][:100]}...")
        return "\n".join(lines)


_learning = None


def get_continuous_learning() -> ContinuousLearning:
    global _learning
    if _learning is None:
        _learning = ContinuousLearning()
    return _learning
