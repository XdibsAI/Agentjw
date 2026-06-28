"""
Decision History - Menyimpan riwayat keputusan
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class DecisionHistory:
    """Riwayat keputusan yang pernah diambil"""
    
    HISTORY_FILE = Path("/home/dibs/agentjw/memory/decision_history.json")
    
    def __init__(self):
        self.decisions: List[Dict] = []
        self._load()
    
    def add(self, action: str, reason: str, candidates: List[str], 
            confidence: float, evidence: Dict, constraints: List[str],
            artifact_id: str, project: str, session_id: str):
        """Tambahkan keputusan"""
        decision = {
            "artifact_id": artifact_id,
            "action": action,
            "reason": reason,
            "candidates": candidates,
            "confidence": confidence,
            "evidence": evidence,
            "constraints": constraints,
            "project": project,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        self.decisions.append(decision)
        self._save()
    
    def get_by_action(self, action: str, limit: int = 5) -> List[Dict]:
        """Dapatkan keputusan berdasarkan action"""
        results = [d for d in self.decisions if d["action"] == action]
        return results[-limit:]
    
    def get_by_project(self, project: str, limit: int = 10) -> List[Dict]:
        """Dapatkan keputusan berdasarkan project"""
        results = [d for d in self.decisions if d["project"] == project]
        return results[-limit:]
    
    def get_by_artifact(self, artifact_id: str) -> Optional[Dict]:
        """Dapatkan keputusan berdasarkan artifact_id"""
        for d in self.decisions:
            if d["artifact_id"] == artifact_id:
                return d
        return None
    
    def explain(self, action: str) -> str:
        """Jelaskan keputusan untuk suatu action"""
        decisions = self.get_by_action(action)
        if not decisions:
            return f"Tidak ada keputusan tentang {action}"
        
        last = decisions[-1]
        return f"""
Keputusan: {last['action']}
Alasan: {last['reason']}
Confidence: {last['confidence']:.0%}
Kandidat: {', '.join(last['candidates'])}
Timestamp: {last['timestamp']}
"""
    
    def _save(self):
        """Simpan ke file"""
        try:
            self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.HISTORY_FILE, "w") as f:
                json.dump(self.decisions, f, indent=2, default=str)
        except Exception as e:
            print(f"[DECISION] Error saving: {e}")
    
    def _load(self):
        """Load dari file"""
        if not self.HISTORY_FILE.exists():
            return
        try:
            with open(self.HISTORY_FILE) as f:
                self.decisions = json.load(f)
        except Exception as e:
            print(f"[DECISION] Error loading: {e}")
