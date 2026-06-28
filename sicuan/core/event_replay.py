"""
Event Replay - Memutar ulang artifact untuk membangun ulang state
"""

from pathlib import Path
import json
from typing import Dict, List, Optional
from datetime import datetime


class EventReplay:
    """Replay artifact events untuk membangun ulang state"""
    
    ARTIFACT_DIR = Path("/home/dibs/agentjw/memory/artifacts")
    
    def __init__(self):
        self.artifacts: List[Dict] = []
        self.knowledge: Dict = {}
        self.decisions: List[Dict] = []
    
    def load_all_artifacts(self, limit: int = 1000):
        """Load semua artifact dari direktori"""
        if not self.ARTIFACT_DIR.exists():
            return
        
        for f in sorted(self.ARTIFACT_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime)[-limit:]:
            try:
                with open(f) as file:
                    self.artifacts.append(json.load(file))
            except Exception as e:
                print(f"[REPLAY] Error loading {f}: {e}")
        
        print(f"[REPLAY] Loaded {len(self.artifacts)} artifacts")
    
    def replay_knowledge(self):
        """Replay knowledge dari artifacts"""
        self.knowledge = {}
        for artifact in self.artifacts:
            for k in artifact.get("knowledge", []):
                entity = k.get("entity", "unknown")
                attribute = k.get("attribute", "")
                value = k.get("value")
                if entity not in self.knowledge:
                    self.knowledge[entity] = {}
                self.knowledge[entity][attribute] = {
                    "value": value,
                    "confidence": k.get("confidence", 1.0),
                    "source": k.get("source", ""),
                    "timestamp": artifact.get("timestamp", "")
                }
        print(f"[REPLAY] Replayed {len(self.knowledge)} entities")
    
    def replay_decisions(self):
        """Replay decisions dari artifacts"""
        self.decisions = []
        for artifact in self.artifacts:
            decision = artifact.get("decision")
            if decision:
                self.decisions.append({
                    "artifact_id": artifact.get("artifact_id"),
                    "action": decision.get("selected_action"),
                    "reason": decision.get("reason_code"),
                    "candidates": decision.get("candidate_actions", []),
                    "confidence": decision.get("confidence", 0),
                    "timestamp": artifact.get("timestamp", "")
                })
        print(f"[REPLAY] Replayed {len(self.decisions)} decisions")
    
    def get_knowledge(self, entity: str, attribute: str = None) -> Optional[Dict]:
        """Dapatkan knowledge dari hasil replay"""
        if entity not in self.knowledge:
            return None
        if attribute:
            return self.knowledge[entity].get(attribute)
        return self.knowledge[entity]
    
    def get_decision(self, action: str) -> Optional[Dict]:
        """Dapatkan decision terakhir untuk action"""
        for d in reversed(self.decisions):
            if d["action"] == action:
                return d
        return None
    
    def explain_decision(self, action: str) -> str:
        """Jelaskan keputusan berdasarkan replay"""
        decision = self.get_decision(action)
        if not decision:
            return f"Tidak ada keputusan tentang {action}"
        
        return f"""
Keputusan: {decision['action']}
Alasan: {decision['reason']}
Confidence: {decision['confidence']:.0%}
Kandidat: {', '.join([c['action'] for c in decision['candidates']])}
Timestamp: {decision['timestamp']}
"""
