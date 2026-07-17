"""
Metrics Collector — Kumpulkan dan track semua metrik
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class MetricsCollector:
    """Metrics Collector — Track semua metrik sistem"""

    def __init__(self):
        self.metrics_file = Path("/home/dibs/agentjw/memory/metrics.json")
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
            "started_at": datetime.now().isoformat(),
            "last_updated": None,
            "counters": {
                "workflows_executed": 0,
                "workflows_failed": 0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "customers_served": 0,
                "errors": 0,
                "api_calls": 0
            },
            "gauges": {
                "active_workflows": 0,
                "queue_size": 0,
                "memory_usage": 0,
                "cpu_usage": 0
            },
            "timers": {
                "avg_workflow_time": 0,
                "avg_task_time": 0,
                "avg_response_time": 0
            },
            "history": []
        }

    def _save(self):
        self._data["last_updated"] = datetime.now().isoformat()
        self.metrics_file.write_text(json.dumps(self._data, indent=2))

    def increment_counter(self, name: str, value: int = 1):
        if name in self._data["counters"]:
            self._data["counters"][name] += value
            self._save()

    def set_gauge(self, name: str, value: float):
        if name in self._data["gauges"]:
            self._data["gauges"][name] = value
            self._save()

    def record_timer(self, name: str, value: float):
        if name in self._data["timers"]:
            current = self._data["timers"][name]
            # Exponential moving average
            self._data["timers"][name] = (current * 0.8) + (value * 0.2)
            self._save()

    def record_workflow(self, duration: float, success: bool):
        self.increment_counter("workflows_executed")
        if not success:
            self.increment_counter("workflows_failed")
        self.record_timer("avg_workflow_time", duration)

    def get_metrics(self) -> str:
        lines = []
        lines.append("📊 **METRICS DASHBOARD**")
        lines.append("=" * 40)
        lines.append(f"🕐 Started: {self._data['started_at'][:16]}")
        lines.append(f"🕐 Last Updated: {self._data['last_updated'][:16] if self._data['last_updated'] else 'N/A'}")
        lines.append("")
        lines.append("📈 **Counters:**")
        for name, value in self._data["counters"].items():
            lines.append(f"  {name.replace('_', ' ').title()}: {value:,}")
        lines.append("")
        lines.append("📊 **Gauges:**")
        for name, value in self._data["gauges"].items():
            lines.append(f"  {name.replace('_', ' ').title()}: {value}")
        lines.append("")
        lines.append("⏱️ **Timers:**")
        for name, value in self._data["timers"].items():
            lines.append(f"  {name.replace('_', ' ').title()}: {value:.2f}s")
        return "\n".join(lines)

    def get_summary(self) -> Dict:
        return {
            "uptime": (datetime.now() - datetime.fromisoformat(self._data["started_at"])).total_seconds(),
            "workflows": self._data["counters"]["workflows_executed"],
            "success_rate": self._calculate_success_rate(),
            "errors": self._data["counters"]["errors"]
        }

    def _calculate_success_rate(self) -> float:
        total = self._data["counters"]["workflows_executed"]
        failed = self._data["counters"]["workflows_failed"]
        if total == 0:
            return 100.0
        return round(((total - failed) / total) * 100, 1)


_metrics = None


def get_metrics_collector() -> MetricsCollector:
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics
