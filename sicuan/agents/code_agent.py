"""
Code Agent — Generate & modify code
"""

from typing import Dict, Any, List
from pathlib import Path

from sicuan.agents.base import Agent


class CodeAgent(Agent):
    """Code Agent — Generate & modify code"""

    def __init__(self):
        super().__init__("CodeAgent", "Code Generator")

    def get_capabilities(self) -> list:
        return ["code", "generate", "modify", "repair", "fix"]

    def execute(self, task: Dict) -> Dict:
        """Eksekusi task code"""
        action = task.get("action", "generate")
        
        if action == "generate":
            return self._generate_code(task.get("spec", ""))
        elif action == "modify":
            return self._modify_code(task.get("file", ""), task.get("changes", ""))
        elif action == "read":
            return self._read_code(task.get("file", ""))
        else:
            return {"error": f"Unknown action: {action}"}

    def _generate_code(self, spec: str) -> Dict:
        """Generate code from spec"""
        return {
            "status": "ok",
            "data": {
                "message": f"Code generation for: {spec[:50]}...",
                "spec": spec
            }
        }

    def _modify_code(self, file_path: str, changes: str) -> Dict:
        """Modify code"""
        return {
            "status": "ok",
            "data": {
                "message": f"Modifying {file_path}",
                "changes": changes
            }
        }

    def _read_code(self, file_path: str) -> Dict:
        """Read code file"""
        try:
            path = Path(file_path)
            if path.exists():
                content = path.read_text()
                return {
                    "status": "ok",
                    "data": {
                        "content": content[:500],
                        "lines": len(content.split('\n')),
                        "size": len(content)
                    }
                }
            return {"status": "error", "message": f"File not found: {file_path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
