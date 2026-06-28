"""
Artifact Query - Query layer untuk artifact storage
"""

from pathlib import Path
import json
from typing import Dict, List, Optional, Any
from datetime import datetime


class ArtifactQuery:
    """Query artifact tanpa harus load semua"""
    
    ARTIFACT_DIR = Path("/home/dibs/agentjw/memory/artifacts")
    
    def __init__(self):
        self.artifacts: List[Dict] = []
        self._load_index()
    
    def _load_index(self):
        """Load index dari artifact files"""
        if not self.ARTIFACT_DIR.exists():
            return
        
        for f in self.ARTIFACT_DIR.glob("*.json"):
            try:
                with open(f) as file:
                    data = json.load(file)
                    # Tambahkan metadata
                    data["_file"] = f.name
                    data["_loaded_at"] = datetime.now().isoformat()
                    self.artifacts.append(data)
            except Exception as e:
                print(f"[ARTIFACT] Error loading {f}: {e}")
    
    def get_by_action(self, action: str) -> List[Dict]:
        """Dapatkan artifact berdasarkan action"""
        return [a for a in self.artifacts if a.get("action") == action]
    
    def get_by_project(self, project: str) -> List[Dict]:
        """Dapatkan artifact berdasarkan project"""
        return [a for a in self.artifacts if a.get("project") == project]
    
    def get_latest(self, action: str) -> Optional[Dict]:
        """Dapatkan artifact terbaru untuk action"""
        artifacts = self.get_by_action(action)
        if artifacts:
            return artifacts[-1]
        return None
    
    def get_by_date(self, date: str) -> List[Dict]:
        """Dapatkan artifact berdasarkan tanggal"""
        return [a for a in self.artifacts if date in a.get("timestamp", "")]
    
    def get_timeline(self, action: str, limit: int = 10) -> str:
        """Dapatkan timeline untuk action"""
        artifacts = self.get_by_action(action)
        if not artifacts:
            return f"Tidak ada artifact untuk {action}"
        
        lines = [f"📊 Timeline untuk {action}:"]
        for a in artifacts[-limit:]:
            timestamp = a.get("timestamp", "unknown")[:10]
            outcome = a.get("outcome", {}).get("success", False)
            status = "✅" if outcome else "❌"
            lines.append(f"  {status} {timestamp}: {a.get('artifact_id', 'unknown')}")
        return "\n".join(lines)
