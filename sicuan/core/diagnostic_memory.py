"""
Diagnostic Memory - Menyimpan error terakhir yang terjadi
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
import json
from pathlib import Path


@dataclass
class DiagnosticEvent:
    timestamp: datetime
    event_type: str  # "error", "warning", "timeout", "parse_error"
    source: str  # "telegram", "llm", "brain", "action"
    message: str
    details: Dict[str, Any]


class DiagnosticMemory:
    """Menyimpan error terakhir untuk konteks percakapan"""

    def __init__(self):
        self._last_error: Optional[DiagnosticEvent] = None
        self._history: list[DiagnosticEvent] = []
        self._max_history = 10

    def record_error(self, event_type: str, source: str, message: str, details: Dict = None):
        """Record an error event"""
        event = DiagnosticEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            source=source,
            message=message,
            details=details or {}
        )
        self._last_error = event
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def get_last_error(self) -> Optional[DiagnosticEvent]:
        """Get the last error that occurred"""
        return self._last_error

    def get_recent_errors(self, count: int = 3) -> list[DiagnosticEvent]:
        """Get recent errors"""
        return self._history[-count:] if self._history else []

    def clear(self):
        """Clear error history"""
        self._last_error = None
        self._history = []

    def has_error(self) -> bool:
        """Check if there's a recent error"""
        if not self._last_error:
            return False
        # Check if error is within last 5 minutes
        delta = datetime.now() - self._last_error.timestamp
        return delta.total_seconds() < 300  # 5 minutes


_diagnostic_memory = None


def get_diagnostic_memory() -> DiagnosticMemory:
    global _diagnostic_memory
    if _diagnostic_memory is None:
        _diagnostic_memory = DiagnosticMemory()
    return _diagnostic_memory
