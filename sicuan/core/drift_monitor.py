"""
Drift Monitoring - Pantau perubahan performa sistem secara real-time
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class DriftAlert:
    """Alert ketika terjadi drift"""
    timestamp: str
    metric: str
    current_value: float
    previous_value: float
    threshold: float
    severity: str  # "warning", "critical"
    message: str


class DriftMonitor:
    """Monitor drift performa sistem"""

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.history_file = self.memory_dir / "drift_history.json"
        self.alerts_file = self.memory_dir / "drift_alerts.json"
        self.alerts: List[DriftAlert] = []
        self._load_alerts()
        
        # Threshold default
        self.thresholds = {
            "shadow_match_rate": {"warning": 5.0, "critical": 10.0},  # penurunan % dalam 7 hari
            "workflow_success_rate": {"warning": 5.0, "critical": 10.0},
            "avg_confidence": {"warning": 5.0, "critical": 10.0},
            "retry_rate": {"warning": 3.0, "critical": 7.0},  # kenaikan % dalam 7 hari
            "planner_accuracy": {"warning": 5.0, "critical": 10.0},
            "execution_latency": {"warning": 5.0, "critical": 10.0},  # kenaikan %
        }
    
    def check_drift(self, current_metrics: Dict[str, float]) -> List[DriftAlert]:
        """Check drift dari data terbaru"""
        alerts = []
        history = self._load_history()
        
        if not history:
            return alerts
        
        # Ambil data 7 hari lalu
        seven_days_ago = datetime.now() - timedelta(days=7)
        old_data = None
        for entry in history:
            try:
                entry_date = datetime.fromisoformat(entry.get("timestamp", ""))
                if entry_date < seven_days_ago:
                    old_data = entry
                    break
            except:
                continue
        
        if not old_data:
            return alerts
        
        # Check setiap metric
        for metric, threshold in self.thresholds.items():
            if metric not in current_metrics or metric not in old_data:
                continue
            
            current = current_metrics[metric]
            previous = old_data[metric]
            
            # Hitung perubahan
            if metric in ["retry_rate", "execution_latency"]:
                # Untuk metric yang naik = buruk
                change = ((current - previous) / previous * 100) if previous > 0 else 0
                is_degradation = change > 0
            else:
                # Untuk metric yang turun = buruk
                change = ((previous - current) / previous * 100) if previous > 0 else 0
                is_degradation = change > 0
            
            if is_degradation and change > threshold["warning"]:
                severity = "critical" if change > threshold["critical"] else "warning"
                
                alert = DriftAlert(
                    timestamp=datetime.now().isoformat(),
                    metric=metric,
                    current_value=current,
                    previous_value=previous,
                    threshold=threshold["warning"],
                    severity=severity,
                    message=self._generate_alert_message(metric, current, previous, change, severity)
                )
                alerts.append(alert)
        
        # Simpan alerts
        self.alerts.extend(alerts)
        self._save_alerts()
        
        return alerts
    
    def _generate_alert_message(self, metric: str, current: float, previous: float, 
                                change: float, severity: str) -> str:
        """Generate alert message"""
        metric_names = {
            "shadow_match_rate": "Shadow Match Rate",
            "workflow_success_rate": "Workflow Success Rate",
            "avg_confidence": "Average Confidence",
            "retry_rate": "Retry Rate",
            "planner_accuracy": "Planner Accuracy",
            "execution_latency": "Execution Latency"
        }
        
        name = metric_names.get(metric, metric)
        
        if metric in ["retry_rate", "execution_latency"]:
            direction = "naik" if change > 0 else "turun"
        else:
            direction = "turun" if change > 0 else "naik"
        
        return f"{name} {direction} {change:.1f}% ({previous:.1f}% → {current:.1f}%) [{severity}]"
    
    def get_alerts(self, severity: str = None, limit: int = 10) -> List[Dict]:
        """Get alerts dengan filter"""
        if severity:
            alerts = [a for a in self.alerts if a.severity == severity]
        else:
            alerts = self.alerts
        return [a.__dict__ for a in alerts[-limit:]]
    
    def get_summary(self) -> Dict:
        """Get drift summary"""
        total = len(self.alerts)
        warning = len([a for a in self.alerts if a.severity == "warning"])
        critical = len([a for a in self.alerts if a.severity == "critical"])
        
        # Last alert
        last_alert = self.alerts[-1].__dict__ if self.alerts else None
        
        return {
            "total_alerts": total,
            "warning": warning,
            "critical": critical,
            "last_alert": last_alert,
            "timestamp": datetime.now().isoformat()
        }
    
    def _load_history(self) -> List[Dict]:
        """Load history dari self-review"""
        history_file = self.memory_dir / "self_review_history.json"
        if history_file.exists():
            try:
                return json.loads(history_file.read_text())
            except:
                pass
        return []
    
    def _load_alerts(self):
        """Load alerts dari file"""
        if self.alerts_file.exists():
            try:
                data = json.loads(self.alerts_file.read_text())
                self.alerts = [DriftAlert(**a) for a in data.get("alerts", [])]
            except:
                self.alerts = []
    
    def _save_alerts(self):
        """Save alerts ke file"""
        data = {
            "alerts": [a.__dict__ for a in self.alerts],
            "updated_at": datetime.now().isoformat()
        }
        self.alerts_file.write_text(json.dumps(data, indent=2))
    
    def print_summary(self):
        """Print summary ke console"""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("📊 DRIFT MONITORING SUMMARY")
        print("=" * 60)
        print(f"Total Alerts   : {summary['total_alerts']}")
        print(f"Warning        : {summary['warning']}")
        print(f"Critical       : {summary['critical']}")
        
        if summary['last_alert']:
            alert = summary['last_alert']
            print(f"\n📋 Last Alert:")
            print(f"   Metric   : {alert['metric']}")
            print(f"   Severity : {alert['severity']}")
            print(f"   Message  : {alert['message']}")
        
        print("=" * 60)


# Singleton
_monitor = None

def get_drift_monitor():
    global _monitor
    if _monitor is None:
        _monitor = DriftMonitor()
    return _monitor
