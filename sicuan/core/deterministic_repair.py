"""
DeterministicRepair — fixes a small set of well-understood, mechanical
error patterns WITHOUT calling any LLM.
"""

import ast
from pathlib import Path
from typing import Dict


class DeterministicRepair:

    def repair(self, file_path: str, error_context: Dict) -> Dict:
        full_path = Path(file_path)
        error_msg = error_context.get("error_msg", "") or ""
        line = error_context.get("line", 0)

        if not full_path.exists():
            return {"success": False, "message": f"File not found: {full_path}"}

        try:
            original = full_path.read_text()
        except Exception as e:
            return {"success": False, "message": f"Read failed: {e}"}

        fixed = None

        if "IndentationError" in error_msg or "unexpected indent" in error_msg or \
           "unindent does not match" in error_msg:
            fixed = self._fix_indentation(original, line)
        elif "EOL while scanning" in error_msg or "unterminated string" in error_msg.lower():
            fixed = self._fix_unterminated_string(original, line)

        if fixed is None or fixed == original:
            return {"success": False, "message": "No deterministic fix pattern matched"}

        try:
            ast.parse(fixed)
        except SyntaxError as e:
            return {"success": False, "message": f"Deterministic fix did not resolve syntax: {e}"}

        try:
            full_path.write_text(fixed)
        except Exception as e:
            return {"success": False, "message": f"Write failed: {e}"}

        return {"success": True, "message": f"Deterministic repair applied to {full_path.name} (line {line})"}

    def _fix_indentation(self, source: str, line: int) -> str:
        lines = source.splitlines()
        if not (1 <= line <= len(lines)):
            return source

        idx = line - 1
        prev_indent = 0
        for i in range(idx - 1, -1, -1):
            stripped = lines[i].strip()
            if stripped:
                prev_indent = len(lines[i]) - len(lines[i].lstrip(" "))
                if lines[i].rstrip().endswith(":"):
                    prev_indent += 4
                break

        current = lines[idx]
        content = current.lstrip(" \t")
        lines[idx] = " " * prev_indent + content
        return "\n".join(lines)

    def _fix_unterminated_string(self, source: str, line: int) -> str:
        lines = source.splitlines()
        if not (1 <= line <= len(lines)):
            return source
        idx = line - 1
        target = lines[idx]
        for q in ('"""', "'''", '"', "'"):
            if target.count(q) % 2 == 1:
                lines[idx] = target + q
                return "\n".join(lines)
        return source


_repair = None


def get_deterministic_repair() -> DeterministicRepair:
    global _repair
    if _repair is None:
        _repair = DeterministicRepair()
    return _repair
