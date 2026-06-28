"""
Reflection Query - Query layer untuk reflection journal
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json


class ReflectionQuery:
    """Query reflection journal tanpa harus scan ulang"""
    
    REFLECTION_DIR = Path("/home/dibs/agentjw/memory/reflections")
    
    def __init__(self):
        self.reflections: List[Dict] = []
        self._load()
    
    def _load(self):
        """Load reflection dari file"""
        if not self.REFLECTION_DIR.exists():
            return
        
        for f in self.REFLECTION_DIR.glob("*.json"):
            try:
                with open(f) as file:
                    data = json.load(file)
                    self.reflections.append(data)
            except Exception as e:
                print(f"[REFLECTION] Error loading {f}: {e}")
    
    def get_by_action(self, action: str) -> List[Dict]:
        """Dapatkan reflection berdasarkan action"""
        return [r for r in self.reflections if r.get("action") == action]
    
    def get_latest(self, action: str) -> Optional[Dict]:
        """Dapatkan reflection terbaru untuk action"""
        reflections = self.get_by_action(action)
        if reflections:
            return reflections[-1]
        return None
    
    def get_risks(self, action: str) -> List[str]:
        """Dapatkan risiko dari reflection"""
        reflection = self.get_latest(action)
        if reflection:
            return reflection.get("concerns", [])
        return []
    
    def get_learnings(self, action: str) -> List[str]:
        """Dapatkan pembelajaran dari reflection"""
        reflection = self.get_latest(action)
        if reflection:
            return reflection.get("learnings", [])
        return []
    
    def explain(self, action: str) -> str:
        """Jelaskan reflection untuk suatu action"""
        reflection = self.get_latest(action)
        if not reflection:
            return f"Tidak ada reflection untuk {action}"
        
        lines = [
            f"💭 Reflection untuk {action}:",
            f"  Confidence: {reflection.get('confidence', 0):.0%}",
            f"  Learnings: {', '.join(reflection.get('learnings', []))}",
            f"  Risks: {', '.join(reflection.get('concerns', []))}",
            f"  Next: {', '.join(reflection.get('next_actions', []))}"
        ]
        return "\n".join(lines)
