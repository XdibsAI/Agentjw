"""
Repair Planner — Rencana perbaikan berdasarkan error type
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import hashlib


@dataclass
class RepairAttempt:
    """Satu percobaan perbaikan"""
    strategy: str
    file: str
    success: bool
    error: str


class RepairMemory:
    """Memory untuk percobaan perbaikan"""

    def __init__(self):
        self.attempts: Dict[str, List[RepairAttempt]] = {}

    def get_key(self, error: Dict) -> str:
        """Buat key unik untuk error"""
        error_type = error.get("error_type", "unknown")
        error_msg = error.get("error_message", "")[:50]
        file = error.get("file", "")
        return hashlib.md5(f"{error_type}:{error_msg}:{file}".encode()).hexdigest()[:8]

    def add_attempt(self, error: Dict, strategy: str, file: str, success: bool, error_msg: str = ""):
        """Tambahkan percobaan"""
        key = self.get_key(error)
        if key not in self.attempts:
            self.attempts[key] = []
        self.attempts[key].append(RepairAttempt(strategy, file, success, error_msg))

    def get_used_strategies(self, error: Dict) -> List[str]:
        """Dapatkan strategi yang sudah dicoba"""
        key = self.get_key(error)
        if key not in self.attempts:
            return []
        return [a.strategy for a in self.attempts[key]]

    def get_next_strategy(self, error: Dict) -> Optional[str]:
        """Dapatkan strategi berikutnya yang belum dicoba"""
        used = self.get_used_strategies(error)
        strategies = self._get_strategies_for_error(error)
        
        for strategy in strategies:
            if strategy not in used:
                return strategy
        return None

    def _get_strategies_for_error(self, error: Dict) -> List[str]:
        """Dapatkan daftar strategi berdasarkan error type"""
        error_type = error.get("error_type", "unknown")
        
        strategies = {
            "ModuleNotFoundError": [
                "fix_sys_path",
                "fix_import",
                "fix_install_module"
            ],
            "ImportError": [
                "fix_import",
                "fix_sys_path",
                "fix_module_name"
            ],
            "SyntaxError": [
                "fix_syntax",
                "fix_indentation"
            ],
            "AttributeError": [
                "add_method",
                "fix_attribute_name",
                "fix_import"
            ],
            "IndentationError": [
                "fix_indentation",
                "fix_syntax"
            ],
            "default": [
                "analyze_and_fix",
                "retry_with_different_approach"
            ]
        }
        
        return strategies.get(error_type, strategies["default"])


# Singleton
_memory = None

def get_repair_memory():
    global _memory
    if _memory is None:
        _memory = RepairMemory()
    return _memory
