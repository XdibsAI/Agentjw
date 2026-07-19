"""
Execution Journal — Append-only audit log
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class ExecutionJournal:
    """
    Append-only journal untuk audit dan debugging
    """
    
    def __init__(self, journal_path: Optional[Path] = None):
        self.journal_path = journal_path or Path("memory/journal.jsonl")
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log(self, event_type: str, data: Dict):
        """Log event ke journal"""
        entry = {
            "type": event_type,
            "timestamp": time.time(),
            "timestamp_iso": datetime.now().isoformat(),
            "data": data
        }
        with open(self.journal_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_events(self, limit: int = 100, event_type: str = None) -> list:
        """Get recent events"""
        events = []
        if not self.journal_path.exists():
            return events
        
        with open(self.journal_path, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    if event_type is None or event.get("type") == event_type:
                        events.append(event)
                except:
                    pass
        
        return events[-limit:]
    
    def get_stats(self) -> Dict:
        """Get journal statistics"""
        if not self.journal_path.exists():
            return {"total": 0}
        
        count = 0
        types = {}
        with open(self.journal_path, "r") as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    count += 1
                    event_type = event.get("type", "unknown")
                    types[event_type] = types.get(event_type, 0) + 1
                except:
                    pass
        
        return {"total": count, "types": types}

# Singleton
_journal = None

def get_execution_journal() -> ExecutionJournal:
    global _journal
    if _journal is None:
        _journal = ExecutionJournal()
    return _journal
