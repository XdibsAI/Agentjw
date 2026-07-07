"""
Syntax Repair — Perbaiki error sintaks secara deterministik tanpa LLM
"""

import ast
from sicuan.core.safe_patcher import get_safe_patcher
import subprocess
from pathlib import Path
from typing import Dict, Optional


class SyntaxRepair:


    def repair_with_ast(self, file_path: str = None) -> Dict:
        """Perbaiki error syntax dengan AST"""
        if file_path is None:
            # Default ke strategy.py
            file_path = "strategy.py"
            print(f"[SYNTAX] Using default file: {file_path}")
        full_path = self._resolve_path(file_path)
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {full_path}"}

        content = full_path.read_text()
        lines = content.splitlines()

        # Coba parse dengan AST untuk menemukan error
        try:
            ast.parse(content)
            return {"success": True, "message": "No syntax error found"}
        except SyntaxError as e:
            line = e.lineno
            if line and line <= len(lines):
                # Kurangi indentasi line yang error
                error_line = lines[line - 1]
                current_indent = len(error_line) - len(error_line.lstrip())
                new_indent = max(0, current_indent - 4)
                lines[line - 1] = ' ' * new_indent + error_line.lstrip()
                full_path.write_text('\n'.join(lines))

                # Verifikasi
                try:
                    ast.parse(full_path.read_text())
                    return {
                        "success": True,
                        "message": f"Fixed indent at line {line}",
                        "line": line
                    }
                except SyntaxError as e2:
                    return {
                        "success": False,
                        "error": f"Still error at line {e2.lineno}: {e2.msg}"
                    }
            return {"success": False, "error": f"Syntax error at line {line}"}

    """Perbaiki error sintaks secara deterministik"""

    def __init__(self):
        self.project_dir = Path("/home/dibs/agentjw/projects/godmeme_bot")

    def repair_indentation(self, file_path: str, line: int) -> Dict:
        """Perbaiki IndentationError dengan menghitung ulang indentasi"""
        full_path = self._resolve_path(file_path)
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {full_path}"}

        lines = full_path.read_text().splitlines()
        if line > len(lines):
            return {"success": False, "error": f"Line {line} out of range"}

        # Ambil baris yang error
        error_line = lines[line - 1]
        current_indent = len(error_line) - len(error_line.lstrip())

        # Cari indentasi yang benar dari baris sebelumnya
        prev_indent = 0
        for i in range(line - 2, -1, -1):
            if lines[i].strip():
                prev_indent = len(lines[i]) - len(lines[i].lstrip())
                break

        # Jika baris saat ini terlalu indent, kurangi
        if current_indent > prev_indent + 4:
            new_indent = prev_indent + 4
            lines[line - 1] = ' ' * new_indent + error_line.lstrip()
            full_path.write_text('\n'.join(lines))
            return {
                "success": True,
                "message": f"Indentation fixed: {current_indent} → {new_indent}",
                "line": line
            }

        return {"success": False, "error": "Indentation already correct"}

    def repair_syntax(self, file_path: str) -> Dict:
        """Perbaiki SyntaxError dengan AST"""
        # TODO: Implement AST-based repair
        return {"success": False, "error": "Syntax repair not implemented yet"}

    def validate_syntax(self, file_path: str) -> Dict:
        """Validasi syntax dengan py_compile"""
        full_path = self._resolve_path(file_path)
        if not full_path.exists():
            return {"success": False, "error": f"File not found: {full_path}"}

        result = subprocess.run(
            ["python3", "-m", "py_compile", str(full_path)],
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "error": result.stderr if result.returncode != 0 else None
        }

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
_repair = None

def get_syntax_repair():
    global _repair
    if _repair is None:
        _repair = SyntaxRepair()
    return _repair
