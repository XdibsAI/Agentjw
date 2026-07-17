"""
ROI Engine — Single Source of Truth untuk semua perhitungan ROI
"""
from typing import Dict, List, Optional
from datetime import datetime


class ROIEngine:
    """ROI Engine — Sumber data terpusat untuk semua modul"""

    def __init__(self):
        self._cache = {}
        self._last_update = None

    def calculate(self, project: Dict) -> Dict:
        """Hitung ROI dengan data yang konsisten"""
        name = project.get("name", "unknown")
        
        # Cek cache
        if name in self._cache:
            return self._cache[name]
        
        # Ambil data dari project
        completion = project.get("completion", 0)
        monetization = project.get("monetization", 50)
        total_files = project.get("total_files", 0)
        errors = project.get("errors", [])
        
        # Hitung investment hours (estimasi)
        investment_hours = max(1, total_files * 0.5) if total_files > 0 else 1
        
        # Hitung monthly revenue
        monthly_revenue = monetization * 100000
        
        # Hitung technical health
        technical_health = 100 - min(len(errors) * 10, 50)
        
        # Hitung user demand
        user_demand = 50 + (monetization // 2)
        
        # Hitung maintenance cost
        maintenance_cost = total_files * 0.1
        
        # Hitung ROI
        yearly_revenue = monthly_revenue * 12
        investment_cost = investment_hours * 200000
        
        if investment_cost > 0:
            # ROI yang lebih realistis dengan faktor skala
            raw_roi = (yearly_revenue / investment_cost) * 100
            
            # Skala logaritmik untuk memberi daya pembeda
            # ROI 100% = skor 50, ROI 300% = skor 80, ROI 500%+ = skor 95
            import math
            if raw_roi <= 100:
                roi_score = int(raw_roi * 0.5)  # 0-50
            elif raw_roi <= 300:
                roi_score = int(50 + ((raw_roi - 100) * 0.15))  # 50-80
            elif raw_roi <= 500:
                roi_score = int(80 + ((raw_roi - 300) * 0.075))  # 80-95
            else:
                roi_score = min(98, int(95 + ((raw_roi - 500) * 0.005)))  # 95-98
        else:
            roi_score = 0
        
        # Rekomendasi
        if roi_score > 80:
            recommendation = "🔥 Kerjakan minggu ini"
        elif roi_score > 60:
            recommendation = "📌 Kerjakan setelah project prioritas"
        elif roi_score > 40:
            recommendation = "⏳ Pertimbangkan untuk nanti"
        else:
            recommendation = "❌ ROI rendah, tinjau ulang"
        
        result = {
            "project_name": name,
            "completion": completion,
            "monetization": monetization,
            "investment_hours": investment_hours,
            "monthly_revenue": monthly_revenue,
            "yearly_revenue": yearly_revenue,
            "technical_health": technical_health,
            "user_demand": user_demand,
            "maintenance_cost": maintenance_cost,
            "roi_score": roi_score,
            "recommendation": recommendation,
            "confidence": 82,  # Estimasi, akan meningkat dengan data nyata
            "data_source": "estimate",
            "calculated_at": datetime.now().isoformat()
        }
        
        # Cache
        self._cache[name] = result
        self._last_update = datetime.now().isoformat()
        
        return result

    def get_roi_report(self, projects: List[Dict]) -> str:
        """Dapatkan laporan ROI untuk semua project"""
        if not projects:
            return "Tidak ada project untuk dianalisa"
        
        lines = []
        lines.append("📈 **PROJECT ROI REPORT**")
        lines.append("=" * 40)
        lines.append(f"📅 {datetime.now().strftime('%d %B %Y %H:%M')}")
        lines.append(f"📊 Total Projects: {len(projects)}")
        lines.append("")
        
        # Urutkan berdasarkan ROI
        sorted_projects = []
        for p in projects:
            roi_data = self.calculate(p)
            sorted_projects.append((p, roi_data))
        sorted_projects.sort(key=lambda x: x[1]["roi_score"], reverse=True)
        
        for p, roi in sorted_projects[:5]:
            lines.append(f"📊 **{p['name']}**")
            lines.append(f"   Priority: {roi['roi_score']}/100")
            lines.append(f"   Revenue: Rp {roi['monthly_revenue']:,}/bulan")
            lines.append(f"   Investment: {roi['investment_hours']:.0f} jam")
            lines.append(f"   Confidence: {roi['confidence']}%")
            lines.append(f"   💡 {roi['recommendation']}")
            lines.append("")
        
        return "\n".join(lines)

    def get_project_roi(self, project_name: str) -> Optional[Dict]:
        """Dapatkan ROI untuk satu project"""
        if project_name in self._cache:
            return self._cache[project_name]
        return None


_roi_engine = None


def get_roi_engine() -> ROIEngine:
    global _roi_engine
    if _roi_engine is None:
        _roi_engine = ROIEngine()
    return _roi_engine
