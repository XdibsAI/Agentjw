"""
CEO Agent — Decision Maker, Prioritas, Resource, KPI, Strategy
"""
from typing import Dict, List, Optional
from datetime import datetime


class CEOAgent:
    """CEO Agent — Otak utama Business OS"""

    def __init__(self):
        self.divisions = {
            "engineering": {"priority": 1, "resource": 40, "status": "active"},
            "customer": {"priority": 2, "resource": 25, "status": "active"},
            "trading": {"priority": 3, "resource": 15, "status": "active"},
            "youtube": {"priority": 4, "resource": 10, "status": "idle"},
            "marketing": {"priority": 5, "resource": 5, "status": "idle"},
            "finance": {"priority": 6, "resource": 5, "status": "idle"}
        }
        self.kpi = {
            "daily_revenue": 0,
            "weekly_revenue": 0,
            "monthly_revenue": 0,
            "customer_satisfaction": 0,
            "project_completion_rate": 0
        }
        self.strategy = []
        self.decisions = []

    def set_priority(self, division: str, priority: int):
        if division in self.divisions:
            self.divisions[division]["priority"] = priority
            return {"status": "updated", "division": division, "priority": priority}
        return {"error": "Division not found"}

    def get_priorities(self) -> str:
        lines = []
        lines.append("📋 **PRIORITAS DIVISI**")
        lines.append("=" * 30)
        sorted_divs = sorted(self.divisions.items(), key=lambda x: x[1]["priority"])
        for name, data in sorted_divs:
            icon = "🟢" if data["status"] == "active" else "🟡" if data["status"] == "idle" else "🔴"
            lines.append(f"{icon} {name.capitalize()}: Priority {data['priority']} | Resource {data['resource']}%")
        return "\n".join(lines)

    def make_decision(self, context: str, options: List[str]) -> Dict:
        decision = {
            "id": f"DEC-{len(self.decisions)+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "options": options,
            "chosen": options[0] if options else None,
            "status": "pending"
        }
        self.decisions.append(decision)
        return decision

    def approve_decision(self, decision_id: str, choice: str) -> Dict:
        for d in self.decisions:
            if d["id"] == decision_id:
                d["chosen"] = choice
                d["status"] = "approved"
                d["approved_at"] = datetime.now().isoformat()
                return d
        return {"error": "Decision not found"}

    def get_daily_brief(self) -> str:
        lines = []
        lines.append("📰 **CEO DAILY BRIEF**")
        lines.append("=" * 30)
        lines.append(f"📅 {datetime.now().strftime('%A, %d %B %Y')}")
        lines.append("")
        lines.append("📊 **KPI:**")
        lines.append(f"  Revenue: Rp {self.kpi['daily_revenue']:,}")
        lines.append(f"  Satisfaction: {self.kpi['customer_satisfaction']}%")
        lines.append(f"  Project Completion: {self.kpi['project_completion_rate']}%")
        lines.append("")
        lines.append("📋 **Prioritas Hari Ini:**")
        sorted_divs = sorted(self.divisions.items(), key=lambda x: x[1]["priority"])
        for name, data in sorted_divs[:3]:
            lines.append(f"  - {name.capitalize()} (Priority {data['priority']})")
        return "\n".join(lines)

    def calculate_priority_score(self, project: Dict) -> int:
        """Hitung priority score dengan multi-factor"""
        factors = {
            "monetization_potential": 0.30,
            "completion": 0.25,
            "technical_health": 0.20,
            "user_demand": 0.10,
            "maintenance_cost": 0.10,
            "strategic_value": 0.05
        }
        
        monetization = project.get("monetization", 50)
        completion = project.get("completion", 0)
        technical_health = project.get("technical_health", 70)
        user_demand = project.get("user_demand", 50)
        maintenance_cost = 100 - project.get("maintenance_cost", 50)
        strategic_value = project.get("strategic_value", 50)
        
        score = (
            monetization * factors["monetization_potential"] +
            completion * factors["completion"] +
            technical_health * factors["technical_health"] +
            user_demand * factors["user_demand"] +
            maintenance_cost * factors["maintenance_cost"] +
            strategic_value * factors["strategic_value"]
        )
        return int(min(100, max(0, score)))

    def predict_roi(self, project: Dict) -> Dict:
        """Prediksi ROI project"""
        investment_hours = project.get("investment_hours", 0)
        revenue_per_month = project.get("revenue_per_month", 0)
        
        monthly_revenue = revenue_per_month
        yearly_revenue = monthly_revenue * 12
        
        if investment_hours == 0:
            roi_score = 0
            recommendation = "Data tidak lengkap untuk menghitung ROI"
        else:
            investment_cost = investment_hours * 200000
            
            if investment_cost > 0:
                roi_score = min(100, int((yearly_revenue / investment_cost) * 100))
            else:
                roi_score = 0
            
            if roi_score > 80:
                recommendation = "🔥 Kerjakan minggu ini"
            elif roi_score > 60:
                recommendation = "📌 Kerjakan setelah project prioritas"
            elif roi_score > 40:
                recommendation = "⏳ Pertimbangkan untuk nanti"
            else:
                recommendation = "❌ ROI rendah, tinjau ulang"
        
        return {
            "investment_hours": investment_hours,
            "investment_cost": investment_hours * 200000,
            "monthly_revenue": monthly_revenue,
            "yearly_revenue": yearly_revenue,
            "roi_score": roi_score,
            "recommendation": recommendation
        }

    def get_roi_report(self) -> str:
        """Dapatkan laporan ROI untuk semua project"""
        try:
            from sicuan.core.project_portfolio import get_project_portfolio
            portfolio = get_project_portfolio()
            projects = portfolio.scan()
        except:
            projects = []
        
        if not projects:
            return "Tidak ada project untuk dianalisa"
        
        lines = []
        lines.append("📈 **PROJECT ROI REPORT**")
        lines.append("=" * 40)
        
        for p in projects[:5]:
            p["investment_hours"] = p.get("total_files", 0) * 0.5
            p["revenue_per_month"] = p.get("monetization", 50) * 100000
            p["technical_health"] = 100 - min(len(p.get("errors", [])) * 10, 50)
            p["user_demand"] = 50 + (p.get("monetization", 50) // 2)
            p["maintenance_cost"] = p.get("total_files", 0) * 0.1
            
            roi = self.predict_roi(p)
            priority = self.calculate_priority_score(p)
            
            lines.append(f"📊 **{p['name']}**")
            lines.append(f"   Priority: {priority}/100")
            lines.append(f"   ROI Score: {roi['roi_score']}/100")
            lines.append(f"   Revenue: Rp {roi['monthly_revenue']:,}/bulan")
            lines.append(f"   Investment: {roi['investment_hours']:.0f} jam")
            lines.append(f"   💡 {roi['recommendation']}")
            lines.append("")
        
        return "\n".join(lines)




    def get_health_score(self) -> int:
        """Hitung health score berdasarkan metrics"""
        try:
            from sicuan.core.production_metrics import get_production_metrics
            metrics = get_production_metrics()
            data = metrics._data
            
            # Weighted score
            workflow_rate = data["workflow"]["success_rate"]
            recovery_rate = (data["recovery"]["recovered"] / max(data["recovery"]["total_crashes"], 1)) * 100
            llm_latency = max(0, 100 - (data["llm"]["avg_latency"] * 5))
            
            score = int((workflow_rate * 0.4) + (recovery_rate * 0.3) + (llm_latency * 0.3))
            return min(100, max(0, score))
        except:
            return 50

    def get_automation_rate(self) -> int:
        """Hitung automation rate"""
        try:
            from sicuan.core.production_metrics import get_production_metrics
            metrics = get_production_metrics()
            data = metrics._data
            
            total = data["workflow"]["total"]
            if total == 0:
                return 0
            
            # Asumsi: workflows yang sukses tanpa human intervention = automation
            automated = data["workflow"]["success"]
            return int((automated / total) * 100)
        except:
            return 0

    def get_health_score(self) -> int:
        """Hitung health score berdasarkan metrics"""
        try:
            from sicuan.core.production_metrics import get_production_metrics
            metrics = get_production_metrics()
            data = metrics._data
            
            # Weighted score
            workflow_rate = data["workflow"]["success_rate"]
            recovery_rate = (data["recovery"]["recovered"] / max(data["recovery"]["total_crashes"], 1)) * 100
            llm_latency = max(0, 100 - (data["llm"]["avg_latency"] * 5))
            
            score = int((workflow_rate * 0.4) + (recovery_rate * 0.3) + (llm_latency * 0.3))
            return min(100, max(0, score))
        except:
            return 50

    def get_automation_rate(self) -> int:
        """Hitung automation rate"""
        try:
            from sicuan.core.production_metrics import get_production_metrics
            metrics = get_production_metrics()
            data = metrics._data
            
            total = data["workflow"]["total"]
            if total == 0:
                return 0
            
            # Asumsi: workflows yang sukses tanpa human intervention = automation
            automated = data["workflow"]["success"]
            return int((automated / total) * 100)
        except:
            return 0

    def get_health_score(self) -> int:
        """Hitung health score berdasarkan metrics"""
        try:
            from sicuan.core.production_metrics import get_production_metrics
            metrics = get_production_metrics()
            data = metrics._data
            
            # Weighted score
            workflow_rate = data["workflow"]["success_rate"]
            recovery_rate = (data["recovery"]["recovered"] / max(data["recovery"]["total_crashes"], 1)) * 100
            llm_latency = max(0, 100 - (data["llm"]["avg_latency"] * 5))
            
            score = int((workflow_rate * 0.4) + (recovery_rate * 0.3) + (llm_latency * 0.3))
            return min(100, max(0, score))
        except:
            return 50

    def get_automation_rate(self) -> int:
        """Hitung automation rate"""
        try:
            from sicuan.core.production_metrics import get_production_metrics
            metrics = get_production_metrics()
            data = metrics._data
            
            total = data["workflow"]["total"]
            if total == 0:
                return 0
            
            # Asumsi: workflows yang sukses tanpa human intervention = automation
            automated = data["workflow"]["success"]
            return int((automated / total) * 100)
        except:
            return 0

_ceo = None


def get_ceo_agent() -> CEOAgent:
    global _ceo
    if _ceo is None:
        _ceo = CEOAgent()
    return _ceo
