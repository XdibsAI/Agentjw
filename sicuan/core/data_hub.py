"""
Data Hub — Single Source of Truth untuk semua data bisnis
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class DataHub:
    """Data Hub — Pusat data terpusat untuk semua modul"""

    def __init__(self):
        self.data_file = Path("/home/dibs/agentjw/memory/data_hub.json")
        self._data = self._load()
        self._listeners = []

    def _load(self) -> Dict:
        if self.data_file.exists():
            try:
                return json.loads(self.data_file.read_text())
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "revenue": {
                "today": 0,
                "week": 0,
                "month": 0,
                "last_updated": None
            },
            "customers": {
                "total": 0,
                "active": 0,
                "new_today": 0,
                "last_updated": None
            },
            "projects": {
                "total": 0,
                "completed": 0,
                "in_progress": 0,
                "by_priority": {},
                "last_updated": None
            },
            "trading": {
                "profit": 0,
                "trades": 0,
                "win_rate": 0,
                "last_updated": None
            },
            "youtube": {
                "subscribers": 0,
                "views": 0,
                "watch_time": 0,
                "last_updated": None
            },
            "roi": {},
            "priorities": {},
            "updated_at": None
        }

    def _save(self):
        self._data["updated_at"] = datetime.now().isoformat()
        self.data_file.write_text(json.dumps(self._data, indent=2))
        self._notify()

    def _notify(self):
        for listener in self._listeners:
            try:
                listener(self._data)
            except:
                pass

    def add_listener(self, listener):
        self._listeners.append(listener)

    # ── REVENUE ──
    def update_revenue(self, today: int = None, week: int = None, month: int = None):
        if today is not None:
            self._data["revenue"]["today"] = today
        if week is not None:
            self._data["revenue"]["week"] = week
        if month is not None:
            self._data["revenue"]["month"] = month
        self._data["revenue"]["last_updated"] = datetime.now().isoformat()
        self._save()

    # ── CUSTOMERS ──
    def update_customers(self, total: int = None, active: int = None, new_today: int = None):
        if total is not None:
            self._data["customers"]["total"] = total
        if active is not None:
            self._data["customers"]["active"] = active
        if new_today is not None:
            self._data["customers"]["new_today"] = new_today
        self._data["customers"]["last_updated"] = datetime.now().isoformat()
        self._save()

    # ── PROJECTS ──
    def update_projects(self, total: int = None, completed: int = None, in_progress: int = None):
        if total is not None:
            self._data["projects"]["total"] = total
        if completed is not None:
            self._data["projects"]["completed"] = completed
        if in_progress is not None:
            self._data["projects"]["in_progress"] = in_progress
        self._data["projects"]["last_updated"] = datetime.now().isoformat()
        self._save()

    # ── TRADING ──
    def update_trading(self, profit: float = None, trades: int = None, win_rate: int = None):
        if profit is not None:
            self._data["trading"]["profit"] = profit
        if trades is not None:
            self._data["trading"]["trades"] = trades
        if win_rate is not None:
            self._data["trading"]["win_rate"] = win_rate
        self._data["trading"]["last_updated"] = datetime.now().isoformat()
        self._save()

    # ── YOUTUBE ──
    def update_youtube(self, subscribers: int = None, views: int = None, watch_time: int = None):
        if subscribers is not None:
            self._data["youtube"]["subscribers"] = subscribers
        if views is not None:
            self._data["youtube"]["views"] = views
        if watch_time is not None:
            self._data["youtube"]["watch_time"] = watch_time
        self._data["youtube"]["last_updated"] = datetime.now().isoformat()
        self._save()

    # ── ROI ──
    def update_roi(self, project_name: str, roi_data: Dict):
        self._data["roi"][project_name] = {
            "score": roi_data.get("roi_score", 0),
            "revenue": roi_data.get("monthly_revenue", 0),
            "investment": roi_data.get("investment_hours", 0),
            "confidence": roi_data.get("confidence", 50),
            "recommendation": roi_data.get("recommendation", ""),
            "updated_at": datetime.now().isoformat()
        }
        self._save()

    # ── GETTERS ──
    def get_revenue(self) -> Dict:
        return self._data["revenue"]

    def get_customers(self) -> Dict:
        return self._data["customers"]

    def get_projects(self) -> Dict:
        return self._data["projects"]

    def get_trading(self) -> Dict:
        return self._data["trading"]

    def get_youtube(self) -> Dict:
        return self._data["youtube"]

    def get_roi(self, project_name: str = None) -> Dict:
        if project_name:
            return self._data["roi"].get(project_name, {})
        return self._data["roi"]

    def get_summary(self) -> str:
        lines = []
        lines.append("📊 **DATA HUB — BUSINESS SUMMARY**")
        lines.append("=" * 40)
        lines.append(f"📅 {datetime.now().strftime('%A, %d %B %Y %H:%M')}")
        lines.append("")
        
        r = self._data["revenue"]
        lines.append(f"💰 Revenue Today: Rp {r['today']:,}")
        lines.append(f"💰 Revenue Week: Rp {r['week']:,}")
        lines.append("")
        
        c = self._data["customers"]
        lines.append(f"👥 Customers: {c['total']} (Active: {c['active']})")
        lines.append("")
        
        p = self._data["projects"]
        lines.append(f"📂 Projects: {p['total']} (Completed: {p['completed']})")
        lines.append("")
        
        t = self._data["trading"]
        lines.append(f"📈 Trading: {t['trades']} trades, Win Rate: {t['win_rate']}%")
        lines.append("")
        
        y = self._data["youtube"]
        lines.append(f"🎬 YouTube: {y['subscribers']} subscribers, {y['views']:,} views")
        lines.append("")
        
        roi_data = self._data["roi"]
        if roi_data:
            lines.append("📊 **ROI Rankings:**")
            sorted_roi = sorted(roi_data.items(), key=lambda x: x[1].get("score", 0), reverse=True)
            for name, data in sorted_roi[:3]:
                lines.append(f"  - {name}: {data['score']}/100 (Confidence: {data['confidence']}%)")
        
        return "\n".join(lines)


_hub = None


def get_data_hub() -> DataHub:
    global _hub
    if _hub is None:
        _hub = DataHub()
    return _hub
