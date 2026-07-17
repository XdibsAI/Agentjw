"""
Project Portfolio Manager — Scan, Progress, Error, Monetisasi, Prioritas
"""
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ProjectPortfolioManager:
    """Kelola semua project di VPS"""

    def __init__(self):
        self.projects_dir = Path("/home/dibs/agentjw/projects")
        self.projects = []
        self.scan()

    def scan(self) -> List[Dict]:
        """Scan semua project"""
        self.projects = []
        if not self.projects_dir.exists():
            return []
        
        for p in self.projects_dir.iterdir():
            if p.is_dir() and not p.name.startswith("."):
                project = self._analyze_project(p)
                self.projects.append(project)
        
        # Urutkan berdasarkan priority score
        self.projects.sort(key=lambda x: x.get("priority_score", 0), reverse=True)
        return self.projects

    def _analyze_project(self, project_path: Path) -> Dict:
        """Analisis satu project"""
        name = project_path.name
        
        # Hitung progress (estimasi berdasarkan file Python)
        py_files = list(project_path.glob("*.py"))
        total_files = len(py_files)
        
        # Cek error (dari log atau file)
        errors = self._detect_errors(project_path)
        
        # Estimasi monetisasi
        monetization = self._estimate_monetization(name)
        
        # Priority score
        priority_score = self._calculate_priority(total_files, errors, monetization)
        
        return {
            "name": name,
            "path": str(project_path),
            "total_files": total_files,
            "py_files": total_files,
            "errors": errors,
            "monetization": monetization,
            "priority_score": priority_score,
            "status": self._get_status(total_files, errors),
            "last_scanned": datetime.now().isoformat()
        }

    def _detect_errors(self, project_path: Path) -> List[str]:
        """Deteksi error dari log atau file"""
        errors = []
        log_files = list(project_path.glob("*.log"))
        for log in log_files:
            try:
                content = log.read_text()
                if "ERROR" in content or "Exception" in content:
                    errors.append(f"{log.name}: error ditemukan")
            except:
                pass
        
        # Cek .env
        env_file = project_path / ".env"
        if not env_file.exists():
            errors.append(".env tidak ada")
        
        return errors

    def _estimate_monetization(self, name: str) -> int:
        """Estimasi potensi monetisasi (1-100)"""
        monetization_map = {
            "godmeme": 90,
            "sniper": 85,
            "trading": 80,
            "youtube": 70,
            "video": 65,
            "api": 60,
            "bot": 55,
            "blog": 50,
            "todo": 40,
            "example": 30
        }
        
        for key, value in monetization_map.items():
            if key in name.lower():
                return value
        return 50

    def _calculate_priority(self, total_files: int, errors: List[str], monetization: int) -> int:
        """Hitung priority score"""
        # Semakin banyak file = semakin besar project
        size_score = min(total_files * 2, 30)
        
        # Error mengurangi priority (kecuali bisa dimonetisasi)
        error_penalty = len(errors) * 5
        
        # Monetisasi menambah priority
        monetization_score = monetization // 2
        
        priority = size_score + monetization_score - error_penalty
        return max(0, min(priority, 100))

    def _get_status(self, total_files: int, errors: List[str]) -> str:
        if total_files == 0:
            return "empty"
        if errors:
            return "needs_repair"
        return "healthy"

    def get_report(self) -> str:
        """Dapatkan laporan portfolio"""
        if not self.projects:
            self.scan()
        
        lines = []
        lines.append("📂 **PROJECT PORTFOLIO REPORT**")
        lines.append("=" * 40)
        lines.append(f"📅 {datetime.now().strftime('%d %B %Y')}")
        lines.append(f"📊 Total Projects: {len(self.projects)}")
        lines.append("")
        
        for i, p in enumerate(self.projects[:10], 1):
            status_icon = "🟢" if p["status"] == "healthy" else "🟡" if p["status"] == "needs_repair" else "🔴"
            lines.append(f"{status_icon} **{i}. {p['name']}**")
            lines.append(f"   📄 Files: {p['total_files']} | 🔧 Priority: {p['priority_score']}/100")
            lines.append(f"   💰 Monetisasi: {p['monetization']}/100")
            if p["errors"]:
                lines.append(f"   ⚠️ Errors: {len(p['errors'])}")
            lines.append("")
        
        return "\n".join(lines)

    def get_priorities(self) -> List[Dict]:
        """Dapatkan daftar prioritas"""
        if not self.projects:
            self.scan()
        return self.projects


_portfolio = None


def get_project_portfolio() -> ProjectPortfolioManager:
    global _portfolio
    if _portfolio is None:
        _portfolio = ProjectPortfolioManager()
    return _portfolio
