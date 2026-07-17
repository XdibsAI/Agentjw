"""
Production Metrics — KPI untuk sistem AgentJW
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

class ProductionMetrics:
    """Production Metrics — Track KPI sistem"""

    def __init__(self):
        self.metrics_file = Path("/home/dibs/agentjw/memory/production_metrics.json")
        self._data = self._load()

    def _load(self) -> Dict:
        if self.metrics_file.exists():
            try:
                return json.loads(self.metrics_file.read_text())
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "workflow": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "success_rate": 0
            },
            "recovery": {
                "total_crashes": 0,
                "recovered": 0,
                "mttr": 0,
                "mtbf": 0
            },
            "llm": {
                "total_requests": 0,
                "total_calls": 0,
                "avg_latency": 0,
                "tokens_used": 0,
                "total_tokens": 0,
                "total_cost": 0
            },
            "business": {
                "customers": 0,
                "revenue": 0,
                "cost_per_customer": 0
            },
            "knowledge": {
                "total_entries": 0,
                "reuse_rate": 0,
                "hits": 0,
                "total_queries": 0
            },
            "agents": {
                "coder": {"accuracy": 0, "tasks": 0},
                "reviewer": {"accuracy": 0, "tasks": 0},
                "ceo": {"accuracy": 0, "decisions": 0}
            },
            "history": []
        }

    def reset(self):
        """Reset all metrics to initial state"""
        self._data = {
            "workflow": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "success_rate": 0,
                "avg_duration": 0
            },
            "recovery": {
                "mttr": 0,
                "total_crashes": 0,
                "recovered": 0,
                "failed_recoveries": 0,
                "mtbf": 0,
                "total_uptime": 0
            },
            "llm": {
                "total_requests": 0,
                "total_calls": 0,
                "avg_latency": 0,
                "tokens_used": 0,
                "total_tokens": 0,
                "total_cost": 0
            },
            "knowledge": {
                "total_entries": 0,
                "reuse_rate": 0,
                "hits": 0,
                "total_queries": 0
            }
        }
        self._save()

    def _save(self):
        self.metrics_file.write_text(json.dumps(self._data, indent=2))

    def record_uptime(self, duration: float):
        """Record total uptime"""
        self._data["recovery"]["total_uptime"] = self._data["recovery"].get("total_uptime", 0) + duration
        self._save()

    def record_uptime(self, duration: float):
        """Record total uptime"""
        self._data["recovery"]["total_uptime"] = self._data["recovery"].get("total_uptime", 0) + duration
        self._save()

    def record_workflow(self, success: bool, duration: float):
        self._data["workflow"]["total"] += 1
        if success:
            self._data["workflow"]["success"] += 1
        else:
            self._data["workflow"]["failed"] += 1
        
        total = self._data["workflow"]["total"]
        success_count = self._data["workflow"]["success"]
        self._data["workflow"]["success_rate"] = round((success_count / total) * 100, 1) if total > 0 else 0
        
        self._save()

    

    
    def record_recovery(self, recovered: bool, duration: float):
        """Record recovery attempt"""
        if "mttr" not in self._data["recovery"]:
            self._data["recovery"]["mttr"] = 0
        
        self._data["recovery"]["total_crashes"] += 1
        if recovered:
            self._data["recovery"]["recovered"] += 1
            current_mttr = self._data["recovery"]["mttr"]
            if current_mttr == 0:
                self._data["recovery"]["mttr"] = duration
            else:
                self._data["recovery"]["mttr"] = (current_mttr + duration) / 2
        else:
            self._data["recovery"]["failed_recoveries"] += 1
        
        self._save()
    def record_llm_call(self, latency: float, tokens: int, cost: float):
        self._data["llm"]["total_calls"] += 1
        self._data["llm"]["total_tokens"] += tokens
        self._data["llm"]["total_cost"] += cost
        
        current_avg = self._data["llm"]["avg_latency"]
        if current_avg == 0:
            self._data["llm"]["avg_latency"] = latency
        else:
            self._data["llm"]["avg_latency"] = (current_avg + latency) / 2
        
        self._save()

    def get_dashboard(self) -> str:
        w = self._data["workflow"]
        r = self._data["recovery"]
        l = self._data["llm"]
        b = self._data["business"]
        k = self._data["knowledge"]
        
        lines = []
        lines.append("📊 **PRODUCTION METRICS**")
        lines.append("=" * 40)
        lines.append("")
        lines.append("📈 **Workflow:**")
        lines.append(f"  Total: {w['total']} | Success: {w['success_rate']}%")
        lines.append("")
        lines.append("🔄 **Recovery:**")
        lines.append(f"  MTTR: {r['mttr']:.1f}s | MTBF: {r['mtbf']:.1f}s")
        lines.append("")
        lines.append("🤖 **LLM:**")
        lines.append(f"  Calls: {l['total_calls']} | Avg Latency: {l['avg_latency']:.1f}s")
        lines.append(f"  Cost: ${l['total_cost']:.2f} | Tokens: {l['total_tokens']:,}")
        lines.append("")
        lines.append("💼 **Business:**")
        lines.append(f"  Customers: {b['customers']} | Revenue: ${b['revenue']:.2f}")
        lines.append("")
        lines.append("📚 **Knowledge:**")
        lines.append(f"  Entries: {k['total_entries']} | Reuse: {k['reuse_rate']}%")
        return "\n".join(lines)

_metrics = None

def get_production_metrics() -> ProductionMetrics:
    global _metrics
    if _metrics is None:
        _metrics = ProductionMetrics()
    return _metrics
