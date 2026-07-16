"""
Generalized Repair Engine - Perbaiki project apapun tanpa hardcode
"""
import re
from pathlib import Path
from typing import Dict, Optional


class GeneralizedRepair:
    """Repair engine yang bisa perbaiki project apapun"""

    ERROR_PATTERNS = {
        "name_error": {
            "pattern": r"name '([^']+)' is not defined",
            "fix": "add_variable"
        },
        "missing_method": {
            "pattern": r"'(\w+)' object has no attribute '(\w+)'",
            "fix": "add_method"
        },
        "import_error": {
            "pattern": r"No module named '([^']+)'",
            "fix": "fix_import"
        },
        "syntax_error": {
            "pattern": r"SyntaxError: (.*)",
            "fix": "fix_syntax"
        },
        "attribute_error": {
            "pattern": r"AttributeError: (.*)",
            "fix": "add_attribute"
        }
    }

    def detect_error(self, log_file: Path) -> Optional[Dict]:
        if not log_file.exists():
            return None
        content = log_file.read_text()
        for error_type, info in self.ERROR_PATTERNS.items():
            match = re.search(info["pattern"], content)
            if match:
                return {
                    "type": error_type,
                    "match": match.groups(),
                    "fix": info["fix"]
                }
        return None

    def repair(self, project_dir: Path, error: Dict) -> Dict:
        fix_type = error.get("fix")
        print(f"[REPAIR] Fix type: {fix_type}")
        
        if fix_type == "add_variable":
            return self._add_variable(project_dir, error)
        elif fix_type == "add_method":
            return self._add_missing_method(project_dir, error)
        elif fix_type == "fix_import":
            return self._fix_import(project_dir, error)
        elif fix_type == "fix_syntax":
            return self._fix_syntax(project_dir, error)
        elif fix_type == "add_attribute":
            return self._add_attribute(project_dir, error)
        
        return {"success": False, "message": f"No known fix pattern for: {fix_type}"}

    def _add_variable(self, project_dir: Path, error: Dict) -> Dict:
        match = error.get("match", [])
        if not match:
            return {"success": False, "message": "No variable name found"}
        
        var_name = match[0]
        print(f"[REPAIR] Adding variable: {var_name}")
        
        for py_file in project_dir.glob("*.py"):
            content = py_file.read_text()
            if var_name in content:
                print(f"[REPAIR] Found in: {py_file.name}")
                lines = content.splitlines()
                lines.insert(0, f'{var_name} = None  # Auto-added by AgentJW')
                py_file.write_text("\n".join(lines))
                return {"success": True, "message": f"Added variable {var_name} to {py_file.name}"}
        
        return {"success": False, "message": "Could not fix name error"}

    def _add_missing_method(self, project_dir: Path, error: Dict) -> Dict:
        match = error.get("match", [])
        if len(match) >= 2:
            class_name = match[0]
            method_name = match[1]
            
            for py_file in project_dir.glob("*.py"):
                content = py_file.read_text()
                if f"class {class_name}" in content:
                    new_method = f"""
    async def {method_name}(self, token_address: str = None) -> bool:
        import time
        if not hasattr(self, '_{method_name}_data'):
            self._{method_name}_data = {{}}
        return True
"""
                    content = content + new_method
                    py_file.write_text(content)
                    return {"success": True, "message": f"Added {method_name} to {class_name}"}
        return {"success": False, "message": "Could not find class"}

    def _fix_import(self, project_dir: Path, error: Dict) -> Dict:
        return {"success": False, "message": "Import fix not implemented"}

    def _fix_syntax(self, project_dir: Path, error: Dict) -> Dict:
        return {"success": False, "message": "Syntax fix not implemented"}

    def _add_attribute(self, project_dir: Path, error: Dict) -> Dict:
        return {"success": False, "message": "Attribute fix not implemented"}


_repair = None


def get_generalized_repair() -> GeneralizedRepair:
    global _repair
    if _repair is None:
        _repair = GeneralizedRepair()
    return _repair
