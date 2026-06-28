"""
Decision Query - Query layer untuk decision history
"""

from typing import Dict, List, Optional, Any
from sicuan.core.decision_history import DecisionHistory


class DecisionQuery:
    """Query decision history tanpa harus scan ulang"""
    
    def __init__(self):
        self.history = DecisionHistory()
    
    def get_by_action(self, action: str) -> List[Dict]:
        """Dapatkan decision berdasarkan action"""
        return self.history.get_by_action(action)
    
    def get_by_project(self, project: str) -> List[Dict]:
        """Dapatkan decision berdasarkan project"""
        return self.history.get_by_project(project)
    
    def get_latest(self, action: str) -> Optional[Dict]:
        """Dapatkan decision terbaru untuk action"""
        decisions = self.get_by_action(action)
        if decisions:
            return decisions[-1]
        return None
    
    def explain(self, action: str) -> str:
        """Jelaskan decision untuk suatu action"""
        decision = self.get_latest(action)
        if not decision:
            return f"Tidak ada keputusan tentang {action}"
        
        lines = [
            f"📋 Keputusan: {decision['action']}",
            f"  Alasan: {decision['reason']}",
            f"  Confidence: {decision['confidence']:.0%}",
            f"  Kandidat: {', '.join(decision['candidates'][:3])}",
            f"  Timestamp: {decision['timestamp']}"
        ]
        return "\n".join(lines)
    
    def trace(self, action: str) -> str:
        """Trace keputusan dari waktu ke waktu"""
        decisions = self.get_by_action(action)
        if not decisions:
            return f"Tidak ada trace untuk {action}"
        
        lines = [f"📈 Trace untuk {action}:"]
        for i, d in enumerate(decisions[-5:], 1):
            lines.append(f"  {i}. {d['reason']} (confidence: {d['confidence']:.0%}) - {d['timestamp'][:10]}")
        return "\n".join(lines)
