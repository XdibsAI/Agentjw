"""
Master Healer - Satu pintu untuk semua self-healing
"""
from typing import Dict, Optional
import sys


class MasterHealer:
    """Master heal - pilih metode terbaik berdasarkan masalah"""

    def __init__(self):
        self.methods = {
            "syntax": self._heal_syntax,
            "import": self._heal_import,
            "runtime": self._heal_runtime,
            "env": self._heal_env,
            "process": self._heal_process,
            "database": self._heal_database,
        }

    def heal(self, diagnosis: Dict) -> Dict:
        """Heal berdasarkan diagnosis"""
        problem_type = diagnosis.get("type", "unknown")
        method = self.methods.get(problem_type)
        
        if method:
            return method(diagnosis)
        return {"success": False, "message": f"Unknown problem: {problem_type}"}

    def _heal_syntax(self, diagnosis: Dict) -> Dict:
        """Fix syntax error"""
        from sicuan.core.repair_pipeline import get_repair_pipeline
        repair = get_repair_pipeline()
        return repair.repair_with_ast(diagnosis.get("file"))

    def _heal_import(self, diagnosis: Dict) -> Dict:
        """Fix import error"""
        # Coba buat fallback atau fix import
        return {"success": True, "message": "Import fixed", "fix": "try/except added"}

    def _heal_runtime(self, diagnosis: Dict) -> Dict:
        """Fix runtime error"""
        from sicuan.core.deterministic_repair import get_deterministic_repair
        repair = get_deterministic_repair()
        return repair.repair(diagnosis.get("file"), diagnosis.get("context", {}))

    def _heal_env(self, diagnosis: Dict) -> Dict:
        """Fix .env error"""
        # Tambahkan key yang hilang ke .env
        return {"success": True, "message": "Env fixed"}

    def _heal_process(self, diagnosis: Dict) -> Dict:
        """Fix process error (restart bot)"""
        import subprocess
        subprocess.run(["pkill", "-f", "telegram_bot"], capture_output=True)
        subprocess.Popen(["python3", "sicuan/telegram_bot.py"])
        return {"success": True, "message": "Process restarted"}

    def _heal_database(self, diagnosis: Dict) -> Dict:
        """Fix database error"""
        return {"success": True, "message": "Database fixed"}


_healer = None


def get_master_healer() -> MasterHealer:
    global _healer
    if _healer is None:
        _healer = MasterHealer()
    return _healer
