"""
RefactorEngine — executes a pre-approved, "safe" refactor plan.
"""

import ast
from pathlib import Path
from typing import Dict, List, Optional


class RefactorEngine:
    def __init__(self):
        self.applied = []

    def execute_safe_plan(self, plan: Optional[List[Dict]] = None) -> Dict:
        plan = plan or []
        results = []

        for item in plan:
            file_path = Path(item.get("file", ""))
            action = item.get("action")
            line = item.get("line")

            if not file_path.exists() or action != "remove_line" or not line:
                results.append({"file": str(file_path), "success": False, "error": "invalid plan item"})
                continue

            try:
                source = file_path.read_text()
                lines = source.splitlines()
                if not (1 <= line <= len(lines)):
                    results.append({"file": str(file_path), "success": False, "error": "line out of range"})
                    continue

                new_lines = lines[:]
                del new_lines[line - 1]
                new_source = "\n".join(new_lines)

                ast.parse(new_source)
                file_path.write_text(new_source)
                results.append({"file": str(file_path), "success": True, "action": "removed_line", "line": line})
                self.applied.append(item)
            except SyntaxError:
                results.append({"file": str(file_path), "success": False, "error": "would break syntax, skipped"})
            except Exception as e:
                results.append({"file": str(file_path), "success": False, "error": str(e)})

        return {"plan_size": len(plan), "results": results}
