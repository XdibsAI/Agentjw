"""
Semantic Verifier — Memastikan perilaku program tidak berubah setelah repair
"""

import ast
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional


class SemanticVerifier:
    """Verifikasi semantic equivalence sebelum dan sesudah repair"""

    def __init__(self):
        self.project_dir = Path("/home/dibs/agentjw")

    def verify(self, file_path: str, original_content: str, repaired_content: str) -> Dict:
        """
        Verifikasi semantic equivalence:
        1. AST structural comparison
        2. Runtime behavior (if possible)
        3. Test execution (if available)
        """
        result = {
            "success": False,
            "ast_equivalent": False,
            "runtime_passed": False,
            "test_passed": False,
            "diff": [],
            "warnings": []
        }

        # 1. AST comparison
        ast_result = self._compare_ast(original_content, repaired_content)
        result["ast_equivalent"] = ast_result["equivalent"]
        result["diff"] = ast_result.get("diff", [])
        result["warnings"] = ast_result.get("warnings", [])

        # 2. Runtime test if possible
        if self._can_run(file_path):
            runtime_result = self._test_runtime(file_path)
            result["runtime_passed"] = runtime_result["success"]

        # 3. Run tests if available
        test_result = self._run_tests(file_path)
        result["test_passed"] = test_result["success"]

        result["success"] = (
            result["ast_equivalent"] or 
            (result["runtime_passed"] and not result.get("diff"))
        )

        return result

    def _compare_ast(self, original: str, repaired: str) -> Dict:
        """Bandingkan AST structure dengan deteksi operator"""
        try:
            orig_tree = ast.parse(original)
            repaired_tree = ast.parse(repaired)
        except SyntaxError as e:
            return {"equivalent": False, "error": str(e)}

        diff = []
        warnings = []

        # Compare operators
        orig_ops = []
        repaired_ops = []
        
        for node in ast.walk(orig_tree):
            if isinstance(node, ast.BinOp):
                orig_ops.append(type(node.op).__name__)
        
        for node in ast.walk(repaired_tree):
            if isinstance(node, ast.BinOp):
                repaired_ops.append(type(node.op).__name__)
        
        if orig_ops != repaired_ops:
            diff.append({
                "type": "operator_change",
                "original": orig_ops,
                "repaired": repaired_ops
            })
            return {"equivalent": False, "diff": diff, "warnings": warnings}

        # Compare constants
        orig_consts = []
        repaired_consts = []
        
        for node in ast.walk(orig_tree):
            if isinstance(node, ast.Constant):
                orig_consts.append(node.value)
        
        for node in ast.walk(repaired_tree):
            if isinstance(node, ast.Constant):
                repaired_consts.append(node.value)
        
        if orig_consts != repaired_consts:
            # Check if only numbers changed slightly
            if len(orig_consts) == len(repaired_consts):
                changes = []
                for o, r in zip(orig_consts, repaired_consts):
                    if o != r:
                        changes.append({"original": o, "repaired": r})
                if changes:
                    warnings.append(f"Constants changed: {changes}")

        # Compare number of functions/classes
        orig_defs = [n for n in ast.walk(orig_tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        repaired_defs = [n for n in ast.walk(repaired_tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))]

        if len(orig_defs) != len(repaired_defs):
            warnings.append(f"Number of definitions changed: {len(orig_defs)} → {len(repaired_defs)}")
            diff.append({"type": "def_count", "original": len(orig_defs), "repaired": len(repaired_defs)})

        # Compare function signatures
        for orig_def in orig_defs:
            if isinstance(orig_def, ast.FunctionDef):
                for repaired_def in repaired_defs:
                    if isinstance(repaired_def, ast.FunctionDef) and repaired_def.name == orig_def.name:
                        # Compare arguments
                        orig_args = len(orig_def.args.args)
                        repaired_args = len(repaired_def.args.args)
                        if orig_args != repaired_args:
                            diff.append({
                                "type": "arg_count",
                                "function": orig_def.name,
                                "original": orig_args,
                                "repaired": repaired_args
                            })
                        break

        return {
            "equivalent": len(diff) == 0,
            "diff": diff,
            "warnings": warnings
        }

    def _can_run(self, file_path: str) -> bool:
        """Cek apakah file bisa di-run"""
        return Path(file_path).exists() and file_path.endswith('.py')

    def _test_runtime(self, file_path: str) -> Dict:
        """Test runtime dengan import"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("test_module", file_path)
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": False}

    def _run_tests(self, file_path: str) -> Dict:
        """Run unit tests if available"""
        test_path = Path(file_path).parent / "tests"
        if not test_path.exists():
            return {"success": True, "message": "No tests found"}

        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", str(test_path), "-q", "--tb=no"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return {"success": result.returncode == 0}
        except:
            return {"success": False}


def get_semantic_verifier():
    return SemanticVerifier()
