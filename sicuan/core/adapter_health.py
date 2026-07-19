"""
Adapter Health Manager — Monitor status dan kesehatan adapter
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import time

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

@dataclass
class HealthRecord:
    status: HealthStatus
    last_check: float = field(default_factory=time.time)
    last_error: Optional[str] = None
    success_rate: float = 100.0
    avg_latency: float = 0.0
    total_calls: int = 0
    failed_calls: int = 0

class AdapterHealthManager:
    """Monitor health of all adapters"""
    
    def __init__(self):
        self._records: Dict[str, HealthRecord] = {}
        self._init_defaults()
    
    def _init_defaults(self):
        self._records = {
            "openclaw": HealthRecord(status=HealthStatus.HEALTHY),
            "hermes": HealthRecord(status=HealthStatus.HEALTHY),
            "native": HealthRecord(status=HealthStatus.HEALTHY),
        }
    
    def record_call(self, adapter: str, success: bool, latency: float, error: str = None):
        """Record a call to an adapter"""
        if adapter not in self._records:
            self._records[adapter] = HealthRecord(status=HealthStatus.UNKNOWN)
        
        record = self._records[adapter]
        record.total_calls += 1
        record.avg_latency = (record.avg_latency * (record.total_calls - 1) + latency) / record.total_calls
        
        if not success:
            record.failed_calls += 1
            record.last_error = error
        
        # Update success rate
        if record.total_calls > 0:
            record.success_rate = ((record.total_calls - record.failed_calls) / record.total_calls) * 100
        
        # Update status based on success rate
        if record.success_rate >= 80:
            record.status = HealthStatus.HEALTHY
        elif record.success_rate >= 50:
            record.status = HealthStatus.DEGRADED
        else:
            record.status = HealthStatus.OFFLINE
        
        record.last_check = time.time()
    
    def get_status(self, adapter: str) -> HealthStatus:
        """Get health status of an adapter"""
        if adapter not in self._records:
            return HealthStatus.UNKNOWN
        return self._records[adapter].status
    
    def get_all_status(self) -> Dict[str, Dict]:
        """Get status of all adapters"""
        return {
            name: {
                "status": record.status.value,
                "success_rate": record.success_rate,
                "avg_latency": record.avg_latency,
                "total_calls": record.total_calls,
                "failed_calls": record.failed_calls,
                "last_error": record.last_error,
                "last_check": record.last_check
            }
            for name, record in self._records.items()
        }
    
    def is_healthy(self, adapter: str) -> bool:
        """Check if adapter is healthy"""
        return self.get_status(adapter) in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]

# Singleton
_health = None

def get_adapter_health() -> AdapterHealthManager:
    global _health
    if _health is None:
        _health = AdapterHealthManager()
    return _health
