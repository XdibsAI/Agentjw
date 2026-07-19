"""
Observability — Dashboard & Metrics untuk AgentJW
"""

import time
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class ExecutionRecord:
    """Record of a single execution"""
    task_id: str
    capability: str
    provider: str
    success: bool
    latency: float
    cost: float
    retries: int
    fallback: Optional[str] = None
    error: Optional[str] = None
    tokens: int = 0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        from datetime import datetime
        return {
            "task_id": self.task_id,
            "capability": self.capability,
            "provider": self.provider,
            "success": self.success,
            "latency": round(self.latency, 3),
            "cost": round(self.cost, 4),
            "retries": self.retries,
            "fallback": self.fallback,
            "error": self.error[:100] if self.error else None,
            "tokens": self.tokens,
            "timestamp": self.timestamp,
            "timestamp_iso": datetime.fromtimestamp(self.timestamp).isoformat()
        }

class Observability:
    """
    Observability Dashboard — Metrics, Stats, Provider Performance
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("memory/observability.json")
        self._records: List[ExecutionRecord] = []
        self._load()
    

    def _load(self):
        """Load records from storage"""
        if self.storage_path.exists():
            try:
                import json
                from datetime import datetime
                data = json.loads(self.storage_path.read_text())
                for item in data:
                    # Parse timestamp
                    ts = item.get("timestamp")
                    if isinstance(ts, str):
                        try:
                            ts = datetime.fromisoformat(ts.replace('Z', '+00:00')).timestamp()
                        except:
                            ts = time.time()
                    elif ts is None:
                        ts = time.time()
                    
                    record = ExecutionRecord(
                        task_id=item.get("task_id", ""),
                        capability=item.get("capability", ""),
                        provider=item.get("provider", ""),
                        success=item.get("success", False),
                        latency=item.get("latency", 0.0),
                        cost=item.get("cost", 0.0),
                        retries=item.get("retries", 0),
                        fallback=item.get("fallback"),
                        error=item.get("error"),
                        tokens=item.get("tokens", 0),
                        timestamp=ts
                    )
                    self._records.append(record)
                print(f"[OBSERVABILITY] Loaded {len(self._records)} records")
            except Exception as e:
                print(f"[OBSERVABILITY] Error loading records: {e}")
            except Exception as e:
                print(f"[OBSERVABILITY] Error loading records: {e}")

            except:
                pass
    
    def _save(self):
        """Save records to storage"""
        data = [r.to_dict() for r in self._records[-1000:]]  # Keep last 1000
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def record(self, record: ExecutionRecord):
        """Record an execution"""
        self._records.append(record)
        self._save()
    
    def get_stats(self, hours: int = 24) -> Dict:
        """Get statistics for last N hours"""
        cutoff = time.time() - (hours * 3600)
        records = [r for r in self._records if r.timestamp >= cutoff]
        
        if not records:
            return {"message": "No records in timeframe"}
        
        total = len(records)
        success = sum(1 for r in records if r.success)
        failed = total - success
        
        # Per provider stats
        provider_stats = {}
        for r in records:
            if r.provider not in provider_stats:
                provider_stats[r.provider] = {
                    "total": 0,
                    "success": 0,
                    "failed": 0,
                    "total_latency": 0,
                    "total_cost": 0,
                    "total_tokens": 0
                }
            ps = provider_stats[r.provider]
            ps["total"] += 1
            if r.success:
                ps["success"] += 1
            else:
                ps["failed"] += 1
            ps["total_latency"] += r.latency
            ps["total_cost"] += r.cost
            ps["total_tokens"] += r.tokens
        
        # Per capability stats
        capability_stats = {}
        for r in records:
            if r.capability not in capability_stats:
                capability_stats[r.capability] = {"total": 0, "success": 0, "failed": 0}
            cs = capability_stats[r.capability]
            cs["total"] += 1
            if r.success:
                cs["success"] += 1
            else:
                cs["failed"] += 1
        
        return {
            "timeframe": f"{hours}h",
            "total_calls": total,
            "success_rate": round((success / total) * 100, 2) if total > 0 else 0,
            "failed": failed,
            "avg_latency": round(sum(r.latency for r in records) / total, 3) if total > 0 else 0,
            "total_cost": round(sum(r.cost for r in records), 4),
            "provider_stats": {
                p: {
                    "total": s["total"],
                    "success_rate": round((s["success"] / s["total"]) * 100, 2) if s["total"] > 0 else 0,
                    "avg_latency": round(s["total_latency"] / s["total"], 3) if s["total"] > 0 else 0,
                    "avg_cost": round(s["total_cost"] / s["total"], 4) if s["total"] > 0 else 0,
                }
                for p, s in provider_stats.items()
            },
            "capability_stats": {
                c: {
                    "total": cs["total"],
                    "success_rate": round((cs["success"] / cs["total"]) * 100, 2) if cs["total"] > 0 else 0,
                }
                for c, cs in capability_stats.items()
            }
        }
    
    def get_dashboard(self) -> str:
        """Get ASCII dashboard"""
        stats = self.get_stats(24)
        
        lines = []
        lines.append("=" * 60)
        lines.append("📊 AGENTJW OBSERVABILITY DASHBOARD")
        lines.append("=" * 60)
        lines.append(f"\n📈 Overall (24h):")
        lines.append(f"  Total Calls: {stats.get('total_calls', 0)}")
        lines.append(f"  Success Rate: {stats.get('success_rate', 0)}%")
        lines.append(f"  Avg Latency: {stats.get('avg_latency', 0)}s")
        lines.append(f"  Total Cost: ${stats.get('total_cost', 0)}")
        
        lines.append(f"\n🔌 Provider Performance:")
        for provider, ps in stats.get('provider_stats', {}).items():
            status_icon = "🟢" if ps.get('success_rate', 0) >= 95 else "🟡" if ps.get('success_rate', 0) >= 80 else "🔴"
            lines.append(f"  {status_icon} {provider}: {ps.get('success_rate', 0)}% ({ps.get('total', 0)} calls, {ps.get('avg_latency', 0)}s, ${ps.get('avg_cost', 0)})")
        
        lines.append(f"\n📋 Capability Usage:")
        for cap, cs in stats.get('capability_stats', {}).items():
            lines.append(f"  {cap}: {cs.get('total', 0)} calls ({cs.get('success_rate', 0)}%)")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

# Singleton
_observability = None

def get_observability() -> Observability:
    global _observability
    if _observability is None:
        _observability = Observability()
    return _observability
