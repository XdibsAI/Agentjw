"""
Business Intelligence Dashboard — Semua data dalam satu tempat
"""
from typing import Dict, List
from datetime import datetime


class BIDashboard:
    """Business Intelligence Dashboard — Pusat data bisnis"""

    def __init__(self):
        self.data = {
            "revenue": {"today": 0, "week": 0, "month": 0},
            "customers": {"new": 0, "active": 0, "total": 0},
            "projects": {"total": 0, "completed": 0, "in_progress": 0},
            "trading": {"profit": 0, "trades": 0, "win_rate": 0},
            "youtube": {"subscribers": 0, "views": 0, "watch_time": 0},
            "marketing": {"campaigns": 0, "conversion_rate": 0},
            "costs": {"token": 0, "api": 0, "total": 0}
        }
        self._listeners = []

    def update(self, category: str, key: str, value):
        if category in self.data:
            if key in self.data[category]:
                self.data[category][key] = value
                self._notify(category, key, value)

    def increment(self, category: str, key: str, amount: int = 1):
        if category in self.data:
            if key in self.data[category]:
                self.data[category][key] += amount
                self._notify(category, key, self.data[category][key])

    def _notify(self, category: str, key: str, value):
        for listener in self._listeners:
            listener(category, key, value)

    def add_listener(self, listener):
        self._listeners.append(listener)

    def get_dashboard(self) -> str:
        lines = []
        lines.append("📊 **BUSINESS INTELLIGENCE DASHBOARD**")
        lines.append("=" * 40)
        lines.append(f"📅 {datetime.now().strftime('%A, %d %B %Y %H:%M')}")
        lines.append("")
        
        # Revenue
        lines.append("💰 **REVENUE**")
        lines.append(f"  Today: Rp {self.data['revenue']['today']:,}")
        lines.append(f"  Week: Rp {self.data['revenue']['week']:,}")
        lines.append(f"  Month: Rp {self.data['revenue']['month']:,}")
        lines.append("")
        
        # Customers
        lines.append("👥 **CUSTOMERS**")
        lines.append(f"  New: {self.data['customers']['new']}")
        lines.append(f"  Active: {self.data['customers']['active']}")
        lines.append(f"  Total: {self.data['customers']['total']}")
        lines.append("")
        
        # Projects
        lines.append("📂 **PROJECTS**")
        lines.append(f"  Total: {self.data['projects']['total']}")
        lines.append(f"  Completed: {self.data['projects']['completed']}")
        lines.append(f"  In Progress: {self.data['projects']['in_progress']}")
        lines.append("")
        
        # Trading
        lines.append("📈 **TRADING**")
        lines.append(f"  Profit: {self.data['trading']['profit']:.2f} SOL")
        lines.append(f"  Trades: {self.data['trading']['trades']}")
        lines.append(f"  Win Rate: {self.data['trading']['win_rate']}%")
        lines.append("")
        
        # YouTube
        lines.append("🎬 **YOUTUBE**")
        lines.append(f"  Subscribers: {self.data['youtube']['subscribers']}")
        lines.append(f"  Views: {self.data['youtube']['views']:,}")
        lines.append("")
        
        # Marketing
        lines.append("📢 **MARKETING**")
        lines.append(f"  Campaigns: {self.data['marketing']['campaigns']}")
        lines.append(f"  Conversion: {self.data['marketing']['conversion_rate']}%")
        lines.append("")
        
        # Costs
        lines.append("💳 **COSTS**")
        lines.append(f"  Token: ${self.data['costs']['token']:.2f}")
        lines.append(f"  API: ${self.data['costs']['api']:.2f}")
        lines.append(f"  Total: ${self.data['costs']['total']:.2f}")
        
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return self.data


_dashboard = None


def get_bi_dashboard() -> BIDashboard:
    global _dashboard
    if _dashboard is None:
        _dashboard = BIDashboard()
    return _dashboard
