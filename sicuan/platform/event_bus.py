"""
Event Bus - Decoupled communication antar komponen
"""

import json
import threading
import time
from datetime import datetime
from typing import Dict, List, Callable, Any
from dataclasses import dataclass, field


@dataclass
class Event:
    """Event object"""
    event_type: str
    source: str
    data: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    event_id: str = field(default_factory=lambda: f"evt_{int(time.time()*1000)}")


class EventBus:
    """Event Bus - Pub/Sub pattern"""

    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.history: List[Event] = []
        self.max_history = 1000
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to event"""
        with self._lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from event"""
        with self._lock:
            if event_type in self.subscribers:
                self.subscribers[event_type].remove(callback)

    def publish(self, event: Event):
        """Publish event to all subscribers"""
        with self._lock:
            # Save history
            self.history.append(event)
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]
            
            # Notify subscribers
            if event.event_type in self.subscribers:
                for callback in self.subscribers[event.event_type]:
                    try:
                        callback(event)
                    except Exception as e:
                        print(f"[EventBus] Error in subscriber: {e}")

    def get_history(self, event_type: str = None, limit: int = 50) -> List[Event]:
        """Get event history"""
        if event_type:
            events = [e for e in self.history if e.event_type == event_type]
            return events[-limit:]
        return self.history[-limit:]


# Singleton
_event_bus = None

def get_event_bus():
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus
