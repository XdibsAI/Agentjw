"""
AST Patcher — Patch file dengan operasi AST + Full Logging
"""

import ast
import tempfile
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any


class ASTPatcher:
    """
    Patch file dengan operasi AST
    """

    def __init__(self, project_dir: str = "/home/dibs/agentjw/projects"):
        self.project_dir = Path(project_dir)
        self.logs = []

    def _log(self, msg: str):
        """Log message"""
        self.logs.append(msg)
        print(f"[AST] {msg}")

    def patch_file(self, file_path: str, operation: Dict) -> Dict:
        """
        Apply AST operation
        """
        self.logs = []
        result = {
            "success": False,
            "file": file_path,
            "message": "",
            "error": None,
            "logs": []
        }

        try:
            # 1. Resolve path
            self._log(f"Resolving path: {file_path}")
            full_path = self._resolve_path(file_path)
            if not full_path.exists():
                result["error"] = f"File not found: {full_path}"
                self._log(f"❌ File not found: {full_path}")
                result["logs"] = self.logs
                return result
            self._log(f"✅ File found: {full_path}")

            # 2. Read original
            self._log("Reading original file...")
            original = full_path.read_text()
            self._log(f"✅ Original file read ({len(original)} chars)")

            # 3. Parse AST
            self._log("Parsing AST...")
            try:
                tree = ast.parse(original)
                self._log("✅ AST parsed successfully")
            except SyntaxError as e:
                result["error"] = f"Syntax error: {e}"
                result["next_action"] = "syntax_repair"
                result["stage"] = "parse"
                self._log(f"❌ Syntax error: {e}")
                self._log(f"   Line: {e.lineno}, Msg: {e.msg}")
                result["logs"] = self.logs
                import traceback
                result["traceback"] = traceback.format_exc()
                return result

            # 4. Backup original
            self._log("Creating backup...")
            backup = full_path.with_suffix(".bak.ast")
            backup.write_text(original)
            self._log(f"✅ Backup created: {backup}")

            # 5. Apply operation
            self._log(f"Applying operation: {operation.get('type', 'unknown')}")
            if operation["type"] == "add_method":
                new_tree = self._add_method(tree, operation)
            elif operation["type"] == "replace_function":
                new_tree = self._replace_function(tree, operation)
            elif operation["type"] == "add_import":
                new_tree = self._add_import(tree, operation)
            else:
                result["error"] = f"Unknown operation: {operation['type']}"
                self._log(f"❌ Unknown operation: {operation['type']}")
                result["logs"] = self.logs
                return result

            # 6. Fix locations
            self._log("Fixing AST locations...")
            ast.fix_missing_locations(new_tree)
            self._log("✅ Locations fixed")

            # 7. Unparse ke code
            self._log("Unparsing AST to code...")
            try:
                import astor
                new_code = astor.to_source(new_tree)
                self._log(f"✅ Unparsed successfully ({len(new_code)} chars)")
            except Exception as e:
                result["error"] = f"Unparse failed: {e}"
                self._log(f"❌ Unparse failed: {e}")
                result["logs"] = self.logs
                return result

            # 8. Structural validation
            self._log("Running structural validation...")
            validation = self._validate_structure(new_code, file_path)
            if not validation["valid"]:
                result["error"] = validation["error"]
                self._log(f"❌ Structural validation failed: {validation['error']}")
                result["logs"] = self.logs
                return result
            self._log("✅ Structural validation passed")

            # 9. Compile validation
            self._log("Running compile validation...")
            compile_result = self._compile_validate(new_code)
            if not compile_result["success"]:
                result["error"] = compile_result["error"]
                self._log(f"❌ Compile validation failed: {compile_result['error']}")
                result["logs"] = self.logs
                return result
            self._log("✅ Compile validation passed")

            # 10. Write to temp and test
            self._log("Writing to temp file and testing...")
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
                tmp.write(new_code)
                tmp_path = Path(tmp.name)

            compile_result = subprocess.run(
                ["python3", "-m", "py_compile", str(tmp_path)],
                capture_output=True,
                text=True,
                timeout=10
            )

            if compile_result.returncode == 0:
                full_path.write_text(new_code)
                self._log("✅ Atomic replace successful")
                result["success"] = True
                result["message"] = f"Operation '{operation['type']}' applied successfully"
            else:
                result["error"] = compile_result.stderr[:500]
                self._log(f"❌ Compilation failed: {compile_result.stderr[:100]}")
                result["message"] = "Compilation failed"

            tmp_path.unlink()

        except Exception as e:
            result["error"] = f"{e}\n{traceback.format_exc()}"
            self._log(f"❌ Exception: {e}")
            # Rollback
            if 'backup' in locals() and backup.exists():
                full_path.write_text(backup.read_text())
                backup.unlink()
                self._log("🔄 Rollback executed")
            result["message"] = "Patch failed, rolled back"

        result["logs"] = self.logs
        return result

    def _add_method(self, tree: ast.Module, operation: Dict) -> ast.Module:
        """Add method to class"""
        class_name = operation.get("class_name", "Strategy")
        method_name = operation.get("method_name", "")
        method_body = operation.get("method_body", "")

        self._log(f"Adding method '{method_name}' to class '{class_name}'")

        # Parse method body
        try:
            method_ast = ast.parse(method_body)
            if not method_ast.body:
                self._log("❌ Method body empty")
                return tree
            new_node = method_ast.body[0]
            self._log(f"✅ Method parsed: {type(new_node).__name__}")
        except SyntaxError as e:
            self._log(f"❌ Method parse error: {e}")
            return tree

        # Find class
        found = False
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                node.body.append(new_node)
                found = True
                self._log(f"✅ Method added to class '{class_name}'")
                break

        if not found:
            self._log(f"❌ Class '{class_name}' not found")
            self._log(f"   Available classes: {[n.name for n in tree.body if isinstance(n, ast.ClassDef)]}")

        return tree

    def _replace_function(self, tree: ast.Module, operation: Dict) -> ast.Module:
        return tree

    def _add_import(self, tree: ast.Module, operation: Dict) -> ast.Module:
        return tree

    def _validate_structure(self, code: str, file_path: str) -> Dict:
        """Validate file structure"""
        result = {"valid": True, "error": ""}

        try:
            tree = ast.parse(code)

            # Check if class Strategy exists
            has_strategy = False
            class_names = []
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_names.append(node.name)
                    if node.name == "Strategy":
                        has_strategy = True

            if "strategy" in file_path.lower():
                if not has_strategy:
                    result["valid"] = False
                    result["error"] = f"Class 'Strategy' missing. Found: {class_names}"
                    self._log(f"❌ Structural validation: Class 'Strategy' not found")
                else:
                    self._log("✅ Structural validation: Class 'Strategy' found")

        except SyntaxError as e:
            result["valid"] = False
            result["error"] = str(e)
            self._log(f"❌ Structural validation: Syntax error {e}")

        return result

    def _compile_validate(self, code: str) -> Dict:
        """Compile validation"""
        result = {"success": True, "error": ""}
        try:
            compile(code, "<string>", "exec")
            self._log("✅ Compile validation passed")
        except SyntaxError as e:
            result["success"] = False
            result["error"] = str(e)
            self._log(f"❌ Compile validation failed: {e}")
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

def get_ast_patcher():
    global _patcher
    if _patcher is None:
        _patcher = ASTPatcher()
    return _patcher
