"""
Artifact Subscriber Registry - Mengelola subscriber yang menerima artifact events
"""

from typing import List, Callable
from sicuan.core.artifact_event import ArtifactEvent


class ArtifactSubscriberRegistry:
    """Registry untuk subscriber artifact events"""
    
    _instance = None
    _subscribers: List[Callable] = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, subscriber: Callable):
        """Daftarkan subscriber"""
        if subscriber not in self._subscribers:
            self._subscribers.append(subscriber)
            print(f"[SUBSCRIBER] Registered: {subscriber.__name__}")
    
    def publish(self, event: ArtifactEvent):
        """Publish event ke semua subscriber dengan failure isolation"""
        from sicuan.core.artifact_validator import ArtifactValidator
        
        # Validasi artifact
        try:
            validation = ArtifactValidator.validate(event)
            if not validation["valid"]:
                print(f"[ARTIFACT] Invalid artifact: {validation['errors']}")
                return
            if validation["warnings"]:
                print(f"[ARTIFACT] Warnings: {validation['warnings']}")
        except Exception as e:
            print(f"[ARTIFACT] Validation error: {e}")
            return
        
        print(f"[ARTIFACT] Publishing: {event.artifact_id} ({event.action})")
        failed_subscribers = []
        
        for subscriber in self._subscribers:
            try:
                subscriber(event)
            except Exception as e:
                print(f"[SUBSCRIBER] ❌ Error in {subscriber.__name__}: {e}")
                failed_subscribers.append(subscriber.__name__)
        
        if failed_subscribers:
            print(f"[ARTIFACT] Failed subscribers: {failed_subscribers}")
        else:
            print(f"[ARTIFACT] All subscribers succeeded")
    
    def clear(self):
        """Clear semua subscriber"""
        self._subscribers = []
