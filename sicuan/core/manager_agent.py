"""
Manager Agent — Mengelola semua agent, KPI, prioritas, laporan
"""
from typing import Dict, List, Optional
from datetime import datetime


class ManagerAgent:
    """Manager Agent — Otak utama Customer OS"""

    def __init__(self):
        self.agents = {
            "reception": {"status": "active", "tasks": 0},
            "crm": {"status": "active", "tasks": 0},
            "sales": {"status": "active", "tasks": 0},
            "support": {"status": "active", "tasks": 0},
            "marketing": {"status": "idle", "tasks": 0},
            "finance": {"status": "idle", "tasks": 0}
        }
        self.metrics = {
            "total_customers": 0,
            "total_tickets": 0,
            "total_sales": 0,
            "revenue": 0,
            "satisfaction_score": 0
        }
        self.reports = []

    def register_customer(self) -> Dict:
        """Catat customer baru"""
        self.metrics["total_customers"] += 1
        return {"status": "registered", "total": self.metrics["total_customers"]}

    def record_sale(self, amount: float) -> Dict:
        """Catat penjualan"""
        self.metrics["total_sales"] += 1
        self.metrics["revenue"] += amount
        return {"status": "recorded", "revenue": self.metrics["revenue"]}

    def record_ticket(self) -> Dict:
        """Catat tiket support"""
        self.metrics["total_tickets"] += 1
        return {"status": "recorded", "total": self.metrics["total_tickets"]}

    def get_dashboard(self) -> str:
        """Dashboard KPI"""
        lines = []
        lines.append("📊 **MANAGER DASHBOARD**")
        lines.append("=" * 30)
        lines.append(f"👥 Total Customers: {self.metrics['total_customers']}")
        lines.append(f"🎫 Total Tickets: {self.metrics['total_tickets']}")
        lines.append(f"💰 Total Sales: {self.metrics['total_sales']}")
        lines.append(f"💵 Revenue: Rp {self.metrics['revenue']:,}")
        lines.append(f"⭐ Satisfaction: {self.metrics['satisfaction_score']}%")
        lines.append("")
        lines.append("🤖 **Agent Status:**")
        for name, status in self.agents.items():
            icon = "🟢" if status["status"] == "active" else "🟡" if status["status"] == "idle" else "🔴"
            lines.append(f"  {icon} {name.capitalize()}: {status['status']} ({status['tasks']} tasks)")
        return "\n".join(lines)

    def generate_report(self) -> Dict:
        """Generate laporan harian"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": self.metrics.copy(),
            "agents": self.agents.copy(),
            "summary": {
                "total_customers": self.metrics["total_customers"],
                "total_revenue": self.metrics["revenue"],
                "active_agents": sum(1 for a in self.agents.values() if a["status"] == "active")
            }
        }
        self.reports.append(report)
        return report

    def get_report_summary(self) -> str:
        report = self.generate_report()
        lines = []
        lines.append("📋 **LAPORAN HARIAN**")
        lines.append("=" * 30)
        lines.append(f"📅 {report['timestamp'][:16]}")
        lines.append(f"👥 Total Customers: {report['summary']['total_customers']}")
        lines.append(f"💰 Total Revenue: Rp {report['summary']['total_revenue']:,}")
        lines.append(f"🤖 Active Agents: {report['summary']['active_agents']}/6")
        return "\n".join(lines)


_manager = None


def get_manager_agent() -> ManagerAgent:
    global _manager
    if _manager is None:
        _manager = ManagerAgent()
    return _manager
