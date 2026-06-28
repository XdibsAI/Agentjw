"""
Execution Event Bus - Merekam semua event eksekusi untuk audit dan testing
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class ExecutionEvent:
    """Event yang direkam selama eksekusi"""
    event_type: str  # "planner", "executor", "filesystem", "database", "response"
    action: str
    target: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    data: Dict = field(default_factory=dict)
    source: Optional[str] = None  # Untuk provenance


class ExecutionEventBus:
    """Event bus untuk merekam semua event eksekusi"""
    
    _instance = None
    _events: List[ExecutionEvent] = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def clear(self):
        """Clear semua event"""
        self._events = []
    
    def emit(self, event_type: str, action: str, target: str = "", data: Dict = None, source: str = None):
        """Emit event"""
        event = ExecutionEvent(
            event_type=event_type,
            action=action,
            target=target,
            data=data or {},
            source=source
        )
        self._events.append(event)
        return event
    
    def get_events(self, event_type: Optional[str] = None) -> List[ExecutionEvent]:
        """Dapatkan event berdasarkan tipe"""
        if event_type:
            return [e for e in self._events if e.event_type == event_type]
        return self._events.copy()
    
    def get_planner_events(self) -> List[ExecutionEvent]:
        """Dapatkan event dari planner"""
        return self.get_events("planner")
    
    def get_executor_events(self) -> List[ExecutionEvent]:
        """Dapatkan event dari executor"""
        return self.get_events("executor")
    
    def get_filesystem_events(self) -> List[ExecutionEvent]:
        """Dapatkan event dari filesystem"""
        return self.get_events("filesystem")
    
    def get_actions(self) -> List[str]:
        """Dapatkan semua action yang dieksekusi"""
        return [e.action for e in self._events if e.event_type == "executor"]
    
    def get_planned_actions(self) -> List[str]:
        """Dapatkan semua action yang direncanakan"""
        return [e.action for e in self._events if e.event_type == "planner"]
    
    def verify_consistency(self) -> Dict:
        """Verifikasi konsistensi antara planner dan executor"""
        planned = set(self.get_planned_actions())
        executed = set(self.get_actions())
        
        return {
            "planned": list(planned),
            "executed": list(executed),
            "missing": list(planned - executed),
            "extra": list(executed - planned),
            "consistent": planned == executed
        }
    
    def get_report(self) -> str:
        """Dapatkan laporan event"""
        lines = ["📋 EXECUTION EVENT REPORT", "=" * 40]
        
        for event in self._events[-20:]:  # Last 20 events
            lines.append(f"[{event.event_type}] {event.action} -> {event.target}")
            if event.data:
                lines.append(f"  Data: {json.dumps(event.data, default=str)[:100]}")
            if event.source:
                lines.append(f"  Source: {event.source}")
        
        return "\n".join(lines)
