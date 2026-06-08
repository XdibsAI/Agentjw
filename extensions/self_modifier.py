"""
extensions/self_modifier.py - Controlled self-modification engine
"""
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from core.config import config
from core.logger import logger, console
from runtime.ast_validator import ast_validator


class SelfModifier:
    """
    Allows the system to safely rewrite its own modules.
    All changes are versioned with rollback capability.
    """
    VERSIONS_DIR = config.BASE_DIR / "extensions" / ".versions"

    def __init__(self):
        self.VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    def propose_modification(self, module_path: str, new_code: str, reason: str) -> Dict:
        """Validate and propose a modification (does not apply yet)"""
        path = Path(module_path)
        if not path.exists():
            return {"approved": False, "reason": "Module not found"}

        valid, errors = ast_validator.validate_python(new_code)
        if not valid:
            return {"approved": False, "reason": f"Code validation failed: {errors}"}

        return {
            "approved": True,
            "module": str(path),
            "reason": reason,
            "errors": errors,
        }

    def apply_modification(self, module_path: str, new_code: str, reason: str = "") -> bool:
        """Apply a validated modification with automatic backup"""
        path = config.BASE_DIR / module_path

        if not path.exists():
            logger.error(f"Module not found: {path}")
            return False

        # Validate first
        valid, errors = ast_validator.validate_python(new_code)
        if not valid:
            logger.error(f"Cannot apply invalid code: {errors}")
            return False

        # Backup
        backup_path = self._backup(path)
        logger.info(f"Backed up {path.name} to {backup_path}")

        # Apply
        path.write_text(new_code)
        console.print(f"[agent.critic]🔄 Self-modification applied to {module_path}[/agent.critic]")
        logger.info(f"Self-modification: {reason}")
        return True

    def rollback(self, module_path: str, version: Optional[str] = None) -> bool:
        """Rollback a module to a previous version"""
        path = config.BASE_DIR / module_path
        module_name = path.name

        versions = sorted(self.VERSIONS_DIR.glob(f"{module_name}_v*"), reverse=True)
        if not versions:
            logger.warning(f"No backups found for {module_name}")
            return False

        backup = versions[0] if not version else (self.VERSIONS_DIR / f"{module_name}_{version}")
        if not backup.exists():
            return False

        shutil.copy2(str(backup), str(path))
        console.print(f"[status.warning]⏮️ Rolled back {module_path}[/status.warning]")
        return True

    def _backup(self, path: Path) -> Path:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.VERSIONS_DIR / f"{path.name}_v{ts}.bak"
        shutil.copy2(str(path), str(backup_path))
        return backup_path

    def list_versions(self, module_path: str) -> list:
        module_name = Path(module_path).name
        versions = sorted(self.VERSIONS_DIR.glob(f"{module_name}_v*"), reverse=True)
        return [v.name for v in versions]


# Fix missing import
from typing import Dict
self_modifier = SelfModifier()
