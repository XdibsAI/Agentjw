"""
Alerting - Notifikasi jika ada masalah
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class Alerting:
    """Alert system untuk monitoring"""

    def __init__(self):
        self.alerts_dir = Path("/home/dibs/agentjw/memory/alerts")
        self.alerts_dir.mkdir(exist_ok=True)

    def send_alert(self, level: str, title: str, message: str, data: Dict = None):
        """Send alert"""
        alert = {
            "level": level,  # info, warning, error, critical
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Save to file
        alert_file = self.alerts_dir / f"{datetime.now().strftime('%Y%m%d')}.json"
        alerts = []
        if alert_file.exists():
            try:
                alerts = json.loads(alert_file.read_text())
            except:
                pass
        
        alerts.append(alert)
        if len(alerts) > 1000:
            alerts = alerts[-1000:]
        
        alert_file.write_text(json.dumps(alerts, indent=2))
        
        # Print to console
        emoji = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}
        print(f"[{alert['level'].upper()}] {title}: {message}")
        
        # TODO: Send to Telegram too

    def get_alerts(self, level: str = None, limit: int = 50) -> List[Dict]:
        """Get recent alerts"""
        alerts = []
        for f in sorted(self.alerts_dir.glob("*.json"), reverse=True)[:5]:
            try:
                data = json.loads(f.read_text())
                for a in data:
                    if level is None or a.get("level") == level:
                        alerts.append(a)
            except:
                pass
        
        return alerts[:limit]


def get_alerting():
    _alerting = None
    if _alerting is None:
        _alerting = Alerting()
    return _alerting
