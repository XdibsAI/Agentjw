"""
Safe Patcher — Patch file dengan temporary file + compile validation
"""

import ast
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Optional


class SafePatcher:
    """
    Patch file dengan aman:
    1. Buat temporary file
    2. Tulis patch ke temporary file
    3. Compile temporary file
    4. Jika OK → replace original
    5. Jika FAIL → discard
    """

    def __init__(self, project_dir: str = "/home/dibs/agentjw/projects"):
        self.project_dir = Path(project_dir)

    def patch_file(self, file_path: str, new_content: str) -> Dict:
        """
        Patch file dengan aman
        """
        result = {
            "success": False,
            "file": file_path,
            "message": "",
            "error": None
        }

        # 1. Resolve full path
        full_path = self._resolve_path(file_path)
        if not full_path.exists():
            result["error"] = f"File not found: {full_path}"
            return result

        # 2. Backup original
        backup = full_path.with_suffix(".bak.patch")
        backup.write_text(full_path.read_text())

        try:
            # 3. Tulis ke temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(new_content)
                tmp_path = Path(tmp.name)

            # 4. Compile temporary file
            compile_result = subprocess.run(
                ["python3", "-m", "py_compile", str(tmp_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if compile_result.returncode != 0:
                # Compile failed → discard
                result["error"] = compile_result.stderr[:200]
                result["message"] = "Compilation failed"
                tmp_path.unlink()
                return result

            # 5. Compile OK → replace original
            full_path.write_text(new_content)
            result["success"] = True
            result["message"] = "Patch applied successfully"

            # 6. Hapus backup
            backup.unlink()

        except Exception as e:
            # Rollback jika error
            if backup.exists():
                full_path.write_text(backup.read_text())
                backup.unlink()
            result["error"] = str(e)
            result["message"] = "Patch failed, rolled back"

        return result

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path"""
        p = Path(file_path)
        if p.exists():
            return p
        p = self.project_dir / file_path
        if p.exists():
            return p
        p = self.project_dir / "godmeme_bot" / Path(file_path).name
        if p.exists():
            return p
        return Path(file_path)


# Singleton
_patcher = None

def get_safe_patcher():
    global _patcher
    if _patcher is None:
        _patcher = SafePatcher()
    return _patcher
