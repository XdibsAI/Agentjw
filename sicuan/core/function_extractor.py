"""
FunctionExtractor — locate the enclosing function for a given file+line
using AST, so RepairAgent can operate on a single function instead of
the whole file.
"""

import ast
from pathlib import Path
from typing import Dict

DEFAULT_PROJECT_DIR = Path("/home/dibs/agentjw/projects/godmeme_bot")


class FunctionExtractor:
    def __init__(self, project_dir: Path = DEFAULT_PROJECT_DIR):
        self.project_dir = Path(project_dir)

    def _resolve(self, file_name: str) -> Path:
        p = Path(file_name)
        if p.is_absolute():
            return p
        return self.project_dir / file_name

    def extract(self, file_name: str, line: int) -> Dict:
        full_path = self._resolve(file_name)
        if not full_path.exists():
            return {"error": f"File not found: {full_path}"}

        try:
            source = full_path.read_text()
        except Exception as e:
            return {"error": f"Read failed: {e}"}

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return {"error": f"File has syntax error, cannot extract: {e}"}

        lines = source.splitlines()
        best = None

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = getattr(node, "end_lineno", None)
                if end is None:
                    end = max(
                        (getattr(child, "lineno", start) for child in ast.walk(node)),
                        default=start,
                    )
                if start <= line <= end:
                    if best is None or (end - start) < (best[1] - best[0]):
                        best = (start, end, node.name)

        if best is None:
            return {"error": f"No function found containing line {line}"}

        start, end, name = best
        function_code = "\n".join(lines[start - 1:end])

        return {
            "function_code": function_code,
            "function_name": name,
            "full_path": str(full_path),
            "lines": lines,
            "function_start": start,
            "function_end": end,
        }


_extractor = None


def get_function_extractor() -> FunctionExtractor:
    global _extractor
    if _extractor is None:
        _extractor = FunctionExtractor()
    return _extractor
