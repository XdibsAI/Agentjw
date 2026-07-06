"""
Curriculum Department — Learning roadmap & training
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from sicuan.departments.base import Department


class CurriculumDepartment(Department):
    """Curriculum Department — Learning roadmap & training"""

    def __init__(self, config: Dict = None):
        super().__init__("curriculum", config)
        self.curriculum = self._init_curriculum()

    def _init_curriculum(self) -> Dict:
        """Inisialisasi curriculum"""
        return {
            "trading_bot": {
                "name": "Trading Bot Development",
                "status": "active",
                "progress": 85,
                "modules": [
                    {"name": "Scanning & Discovery", "done": True},
                    {"name": "Entry Strategy", "done": True},
                    {"name": "Risk Management", "done": True},
                    {"name": "Exit Strategy", "done": False},
                    {"name": "Optimization", "done": False}
                ],
                "last_updated": datetime.now().isoformat()
            },
            "ai_agent": {
                "name": "AI Agent Development",
                "status": "active",
                "progress": 70,
                "modules": [
                    {"name": "Context Engine", "done": True},
                    {"name": "Memory & Learning", "done": True},
                    {"name": "Self-Review", "done": True},
                    {"name": "Multi-Modal", "done": False},
                    {"name": "Department Modules", "done": False}
                ],
                "last_updated": datetime.now().isoformat()
            },
            "business": {
                "name": "Business Development",
                "status": "planning",
                "progress": 20,
                "modules": [
                    {"name": "Market Research", "done": True},
                    {"name": "Branding", "done": False},
                    {"name": "Monetization", "done": False},
                    {"name": "Scaling", "done": False}
                ],
                "last_updated": datetime.now().isoformat()
            }
        }

    def get_status(self) -> Dict:
        """Dapatkan status curriculum"""
        return {
            "name": "Curriculum",
            "total_modules": self._get_total_modules(),
            "completed_modules": self._get_completed_modules(),
            "overall_progress": self._get_overall_progress(),
            "active_courses": self._get_active_courses(),
            "curriculum": self.curriculum
        }

    def get_summary(self) -> str:
        """Dapatkan ringkasan curriculum"""
        status = self.get_status()
        return f"""
📚 **Curriculum Summary**
  Total Modules   : {status['total_modules']}
  Completed       : {status['completed_modules']}
  Progress        : {status['overall_progress']:.1f}%
  Active Courses  : {', '.join(status['active_courses'])}
"""

    def execute(self, action: str, params: Dict) -> Dict:
        """Eksekusi action curriculum"""
        if action == "progress":
            return {"status": "ok", "data": self.get_status()}
        elif action == "update_module":
            return self._update_module(params.get("course"), params.get("module"))
        elif action == "courses":
            return {"status": "ok", "data": self._get_active_courses()}
        else:
            return {"error": f"Unknown action: {action}"}

    def _get_total_modules(self) -> int:
        """Total modules"""
        total = 0
        for course in self.curriculum.values():
            total += len(course.get("modules", []))
        return total

    def _get_completed_modules(self) -> int:
        """Completed modules"""
        completed = 0
        for course in self.curriculum.values():
            for module in course.get("modules", []):
                if module.get("done", False):
                    completed += 1
        return completed

    def _get_overall_progress(self) -> float:
        """Overall progress"""
        total = self._get_total_modules()
        completed = self._get_completed_modules()
        return (completed / total * 100) if total > 0 else 0

    def _get_active_courses(self) -> List[str]:
        """Active courses"""
        return [c["name"] for c in self.curriculum.values() if c.get("status") == "active"]

    def _update_module(self, course_name: str, module_name: str) -> Dict:
        """Update module status"""
        for course in self.curriculum.values():
            if course["name"] == course_name:
                for module in course.get("modules", []):
                    if module["name"] == module_name:
                        module["done"] = not module.get("done", False)
                        course["last_updated"] = datetime.now().isoformat()
                        # Recalculate progress
                        done = sum(1 for m in course["modules"] if m.get("done", False))
                        course["progress"] = int(done / len(course["modules"]) * 100)
                        return {
                            "status": "ok",
                            "message": f"Module '{module_name}' updated",
                            "done": module["done"]
                        }
        return {"error": f"Module '{module_name}' not found in '{course_name}'"}
