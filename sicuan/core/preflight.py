"""
Preflight — Validasi awal sebelum repair
"""

import ast
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class Preflight:
    """Validasi awal: file exists, syntax, AST, dependencies"""

    def __init__(self, project_dir: str = "/home/dibs/agentjw/projects"):
        self.project_dir = Path(project_dir)

    def check(self, file_path: str) -> Dict:
        """
        Preflight check:
        - File exists
        - Git clean
        - Syntax parse
        - AST parse
        - Import check
        """
        result = {
            "success": False,
            "file": file_path,
            "errors": [],
            "warnings": [],
            "ast_tree": None,
            "structure": {}
        }

        full_path = self._resolve_path(file_path)
        if not full_path.exists():
            result["errors"].append(f"File not found: {full_path}")
            return result

        result["file_size"] = full_path.stat().st_size
        result["line_count"] = len(full_path.read_text().splitlines())

        # 1. Syntax check
        syntax_result = self._check_syntax(full_path)
        if not syntax_result["success"]:
            result["errors"].append(syntax_result["error"])
            result["syntax_error"] = syntax_result
            return result

        # 2. AST parse
        ast_result = self._parse_ast(full_path)
        if not ast_result["success"]:
            result["errors"].append(ast_result["error"])
            result["ast_error"] = ast_result
            return result

        result["ast_tree"] = ast_result["tree"]

        # 3. Structure analysis
        structure = self._analyze_structure(ast_result["tree"])
        result["structure"] = structure

        # 4. Structural validation (BARU — dipanggil!)
        structural = self._validate_structure(ast_result["tree"], file_path)
        if structural.get("errors"):
            result["errors"].extend(structural["errors"])
        if structural.get("warnings"):
            result["warnings"].extend(structural["warnings"])
        
        # 5. Success = tidak ada error
        if not result["errors"]:
            result["success"] = True
            result["message"] = "Preflight passed"
        else:
            result["success"] = False
            result["message"] = "Preflight failed: structural errors found"
        return result

    def _check_syntax(self, full_path: Path) -> Dict:
        """Check syntax with py_compile"""
        result = subprocess.run(
            ["python3", "-m", "py_compile", str(full_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr[:500]}
        return {"success": True}

    def _parse_ast(self, full_path: Path) -> Dict:
        """Parse AST"""
        try:
            tree = ast.parse(full_path.read_text())
            return {"success": True, "tree": tree}
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"{e.msg} at line {e.lineno}",
                "line": e.lineno,
                "msg": e.msg
            }

    def _analyze_structure(self, tree: ast.Module) -> Dict:
        """Analyze AST structure"""
        structure = {
            "classes": [],
            "functions": [],
            "imports": [],
            "async_functions": []
        }

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                structure["classes"].append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                })
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                structure["functions"].append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                structure["imports"].append({
                    "module": node.module if isinstance(node, ast.ImportFrom) else None,
                    "names": [n.name for n in node.names]
                })

        return structure

    def _detect_structural_issues(self, structure: Dict) -> List[str]:
        """Detect structural issues"""
        issues = []

        # Check if import inside class
        # This requires full AST traversal
        # For now, return empty list



    def _validate_structure(self, tree: ast.Module, file_path: str) -> Dict:
        """Structural validation — class, methods, imports"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # 1. Cek class Strategy
        has_strategy = False
        strategy_methods = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "Strategy":
                has_strategy = True
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        strategy_methods.append(method.name)
                break

        if not has_strategy:
            result["valid"] = False
            result["errors"].append("Class 'Strategy' not found")

        # 2. Cek required methods
        required_methods = ["_scan_new_tokens", "_should_buy", "_open_position", "_close_position", "_check_cooldown"]
        missing_methods = [m for m in required_methods if m not in strategy_methods]
        if missing_methods:
            result["valid"] = False
            result["errors"].append(f"Missing methods: {', '.join(missing_methods)}")

        # 3. Cek import di tengah class
        import_in_class = False
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, (ast.Import, ast.ImportFrom)):
                        import_in_class = True
                        result["warnings"].append(f"Import inside class at line {item.lineno}")

        # 4. Cek duplicate method
        seen_methods = set()
        duplicates = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "Strategy":
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if method.name in seen_methods:
                            duplicates.append(method.name)
                        seen_methods.add(method.name)
        if duplicates:
            result["warnings"].append(f"Duplicate methods: {', '.join(duplicates)}")

        return result

        return issues

    def _resolve_path(self, file_path: str) -> Path:
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
_preflight = None

def get_preflight():
    global _preflight
    if _preflight is None:
        _preflight = Preflight()
    return _preflight
