"""
Execution Manager — Retry, Timeout, Fallback, Circuit Breaker, Tracing
"""

import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CIRCUIT_OPEN = "circuit_open"

@dataclass
class ExecutionTrace:
    """Trace of a single execution"""
    id: str
    tool: str
    provider: str
    status: ExecutionStatus
    start_time: float
    end_time: float = 0.0
    duration: float = 0.0
    attempts: int = 0
    error: Optional[str] = None
    result: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class CircuitBreaker:
    """Circuit Breaker untuk mencegah cascade failure"""
    
    def __init__(self, name: str, failure_threshold: int = 5, timeout: int = 300):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout  # seconds to stay open
        self.failures = 0
        self.state = "closed"  # closed, open, half-open
        self.last_failure = 0
        self.last_success = 0
    
    def record_success(self):
        self.failures = 0
        self.state = "closed"
        self.last_success = time.time()
    
    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.failure_threshold:
            self.state = "open"
    
    def allow_request(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            # Check if timeout has elapsed
            if time.time() - self.last_failure > self.timeout:
                self.state = "half-open"
                return True
            return False
        if self.state == "half-open":
            # Only allow one request to test
            self.state = "open"
            return True
        return False
    
    def get_status(self) -> str:
        return self.state

class ExecutionManager:
    """
    Execution Manager — Retry, Timeout, Fallback, Circuit Breaker, Tracing
    """
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.traces: List[ExecutionTrace] = []
        self.max_traces = 1000
        self.trace_file = Path("memory/execution_traces.json")
        self._load_traces()
    
    def _load_traces(self):
        """Load traces from file"""
        if self.trace_file.exists():
            try:
                data = json.loads(self.trace_file.read_text())
                # TODO: Convert dict to ExecutionTrace
                pass
            except:
                pass
    
    def _save_traces(self):
        """Save traces to file"""
        data = []
        for trace in self.traces[-100:]:  # Keep last 100
            data.append({
                "id": trace.id,
                "tool": trace.tool,
                "provider": trace.provider,
                "status": trace.status.value,
                "start_time": trace.start_time,
                "end_time": trace.end_time,
                "duration": trace.duration,
                "attempts": trace.attempts,
                "error": trace.error,
                "result": str(trace.result)[:200] if trace.result else None,
                "metadata": trace.metadata
            })
        self.trace_file.parent.mkdir(parents=True, exist_ok=True)
        self.trace_file.write_text(json.dumps(data, indent=2))
    
    def _get_circuit_breaker(self, provider: str) -> CircuitBreaker:
        """Get or create circuit breaker for provider"""
        if provider not in self.circuit_breakers:
            self.circuit_breakers[provider] = CircuitBreaker(provider)
        return self.circuit_breakers[provider]
    
    def execute(self, tool: str, provider: str, executor, params: Dict = None,
                timeout: int = 60, retries: int = 3, fallback: List[str] = None) -> Dict:
        """
        Execute with retry, timeout, fallback, circuit breaker
        """
        params = params or {}
        fallback = fallback or []
        
        # Create trace
        trace = ExecutionTrace(
            id=f"{tool}_{int(time.time())}",
            tool=tool,
            provider=provider,
            status=ExecutionStatus.PENDING,
            start_time=time.time()
        )
        
        # Get circuit breaker
        cb = self._get_circuit_breaker(provider)
        
        # Check circuit breaker
        if not cb.allow_request():
            trace.status = ExecutionStatus.CIRCUIT_OPEN
            trace.error = f"Circuit open for provider: {provider}"
            self.traces.append(trace)
            self._save_traces()
            return {
                "status": "error",
                "message": trace.error,
                "provider": provider,
                "circuit_open": True
            }
        
        # Try execution with retries
        trace.attempts = 0
        last_error = None
        
        for attempt in range(retries + 1):
            trace.attempts = attempt + 1
            
            try:
                # Execute with timeout
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(executor, params)
                    result = future.result(timeout=timeout)
                
                # Success
                cb.record_success()
                trace.status = ExecutionStatus.SUCCESS
                trace.result = result
                trace.end_time = time.time()
                trace.duration = trace.end_time - trace.start_time
                self.traces.append(trace)
                self._save_traces()
                
                return {
                    "status": "success",
                    "result": result,
                    "provider": provider,
                    "attempts": trace.attempts,
                    "duration": trace.duration
                }
                
            except concurrent.futures.TimeoutError:
                last_error = f"Timeout after {timeout}s"
                trace.error = last_error
                print(f"[EXEC] Attempt {attempt+1} failed: {last_error}")
                
            except Exception as e:
                last_error = str(e)
                trace.error = last_error
                print(f"[EXEC] Attempt {attempt+1} failed: {last_error}")
        
        # All retries failed
        cb.record_failure()
        trace.status = ExecutionStatus.FAILED
        trace.end_time = time.time()
        trace.duration = trace.end_time - trace.start_time
        trace.error = last_error
        self.traces.append(trace)
        self._save_traces()
        
        # Try fallbacks
        for fallback_provider in fallback:
            print(f"[EXEC] Trying fallback: {fallback_provider}")
            result = self.execute(
                tool, fallback_provider, executor,
                params, timeout, retries, []
            )
            if result.get("status") == "success":
                result["fallback"] = True
                result["fallback_from"] = provider
                return result
        
        return {
            "status": "error",
            "message": last_error,
            "provider": provider,
            "attempts": trace.attempts,
            "duration": trace.duration
        }
    
    def get_traces(self, limit: int = 50) -> List[Dict]:
        """Get recent traces"""
        traces = self.traces[-limit:]
        return [
            {
                "id": t.id,
                "tool": t.tool,
                "provider": t.provider,
                "status": t.status.value,
                "duration": t.duration,
                "attempts": t.attempts,
                "error": t.error
            }
            for t in traces
        ]
    
    def get_stats(self) -> Dict:
        """Get execution statistics"""
        total = len(self.traces)
        if total == 0:
            return {"total": 0}
        
        success = sum(1 for t in self.traces if t.status == ExecutionStatus.SUCCESS)
        failed = sum(1 for t in self.traces if t.status == ExecutionStatus.FAILED)
        timeout = sum(1 for t in self.traces if t.status == ExecutionStatus.TIMEOUT)
        circuit_open = sum(1 for t in self.traces if t.status == ExecutionStatus.CIRCUIT_OPEN)
        
        avg_duration = sum(t.duration for t in self.traces if t.duration > 0) / max(1, success)
        
        # Per provider stats
        provider_stats = {}
        for t in self.traces:
            if t.provider not in provider_stats:
                provider_stats[t.provider] = {"total": 0, "success": 0, "failed": 0}
            provider_stats[t.provider]["total"] += 1
            if t.status == ExecutionStatus.SUCCESS:
                provider_stats[t.provider]["success"] += 1
            elif t.status == ExecutionStatus.FAILED:
                provider_stats[t.provider]["failed"] += 1
        
        return {
            "total": total,
            "success": success,
            "failed": failed,
            "timeout": timeout,
            "circuit_open": circuit_open,
            "success_rate": (success / total) * 100 if total > 0 else 0,
            "avg_duration": avg_duration,
            "provider_stats": provider_stats
        }
    
    def get_circuit_status(self) -> Dict:
        """Get circuit breaker status"""
        return {
            name: cb.get_status()
            for name, cb in self.circuit_breakers.items()
        }

# Singleton
_manager = None

def get_execution_manager() -> ExecutionManager:
    global _manager
    if _manager is None:
        _manager = ExecutionManager()
    return _manager
