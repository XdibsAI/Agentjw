"""
Constraint Engine - Memahami dan menghormati constraint pengguna
"""

from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class UserConstraint:
    """Constraint dari user"""
    no_code_change: bool = False
    no_llm: bool = False
    only_read: bool = False
    require_data: bool = False
    max_actions: int = 5
    allowed_actions: Set[str] = None
    forbidden_actions: Set[str] = None
    
    def __post_init__(self):
        if self.allowed_actions is None:
            self.allowed_actions = set()
        if self.forbidden_actions is None:
            self.forbidden_actions = set()


class ConstraintEngine:
    """Engine untuk mengekstrak dan menerapkan constraint"""
    
    # Pattern untuk mendeteksi constraint
    CONSTRAINTS = {
        "no_code_change": [
            "jangan ubah kode",
            "jangan edit",
            "jangan modifikasi",
            "jangan patch",
            "jangan perbaiki",
            "jangan repair",
            "baca saja",
            "analisa saja",
            "lihat saja",
        ],
        "only_read": [
            "baca",
            "lihat",
            "tampilkan",
            "cek",
            "analisa",
            "evaluate",
            "evaluasi",
        ],
        "require_data": [
            "buktikan",
            "data",
            "angka",
            "statistik",
            "metric",
            "metrik",
            "trade history",
        ],
    }
    
    # Action yang membaca data (read-only)
    READ_ACTIONS = {
        "show_log", "list_projects", "project_summary", 
        "analyze_project", "trace_code", "get_file",
        "godmeme_status", "gallery", "video_info",
        "business_analysis", "evaluate_strategy"
    }
    
    # Action yang mengubah kode (write)
    WRITE_ACTIONS = {
        "modify_logic", "repair_project", "build_project",
        "modify_project", "run_bot"
    }
    
    @classmethod
    def extract_constraints(cls, user_message: str) -> UserConstraint:
        """Ekstrak constraint dari pesan user"""
        user_message_lower = user_message.lower()
        
        constraints = UserConstraint()
        
        # Deteksi "jangan ubah kode"
        for pattern in cls.CONSTRAINTS["no_code_change"]:
            if pattern in user_message_lower:
                constraints.no_code_change = True
                constraints.forbidden_actions.update(cls.WRITE_ACTIONS)
                break
        
        # Deteksi "baca saja"
        for pattern in cls.CONSTRAINTS["only_read"]:
            if pattern in user_message_lower:
                constraints.only_read = True
                constraints.allowed_actions.update(cls.READ_ACTIONS)
                break
        
        # Deteksi "butuh data"
        for pattern in cls.CONSTRAINTS["require_data"]:
            if pattern in user_message_lower:
                constraints.require_data = True
                break
        
        return constraints
    
    @classmethod
    def apply_constraints(cls, plan: List[Dict], constraints: UserConstraint) -> List[Dict]:
        """Filter plan berdasarkan constraint"""
        if not constraints.no_code_change and not constraints.only_read:
            return plan
        
        filtered_plan = []
        for step in plan:
            action = step.get("action", "")
            
            # Jika ada forbidden_actions, skip
            if action in constraints.forbidden_actions:
                continue
            
            # Jika ada allowed_actions, hanya yang diizinkan
            if constraints.allowed_actions and action not in constraints.allowed_actions:
                continue
            
            filtered_plan.append(step)
        
        return filtered_plan
    
    @classmethod
    def get_data_actions(cls) -> Set[str]:
        """Dapatkan action yang membaca data"""
        return cls.READ_ACTIONS
