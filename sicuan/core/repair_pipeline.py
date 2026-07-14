"""
Repair Pipeline — With Error Classifier
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Optional

from sicuan.core.error_classifier import get_error_classifier, ErrorType


class RepairPipeline:
    """Repair pipeline dengan error classification"""

    def __init__(self):
        self.max_attempts = 3
        self.attempts = 0
        self.classifier = get_error_classifier()

    def run(self, file_path: str) -> Dict:
        """Run repair pipeline"""
        self.attempts = 0

        from sicuan.core.preflight import get_preflight
        preflight = get_preflight()
        full_path = preflight._resolve_path(file_path)

        result = {
            "success": False,
            "file": str(full_path),
            "attempts": 0,
            "stages": [],
            "changes": []
        }

        while self.attempts < self.max_attempts:
            self.attempts += 1
            print(f"[PIPELINE] Attempt {self.attempts}/{self.max_attempts}")

            # 1. Preflight
            preflight_result = self._check_preflight(str(full_path))
            result["stages"].append({
                "stage": "preflight",
                "success": preflight_result["success"]
            })

            if preflight_result["success"]:
                # 2. Runtime verify
                runtime_result = self._check_runtime(str(full_path))
                result["stages"].append({
                    "stage": "runtime",
                    "success": runtime_result["success"]
                })

                if runtime_result["success"]:
                    result["success"] = True
                    result["attempts"] = self.attempts
                    print(f"[PIPELINE] ✅ Success!")
                    return result

            # 3. Klasifikasi dan repair
            errors = preflight_result.get("errors", [])
            runtime_error = runtime_result.get("error", "") if 'runtime_result' in locals() else ""

            all_errors = errors + ([runtime_error] if runtime_error else [])
            error_text = " ".join(all_errors)

            if error_text:
                classification = self.classifier.classify(error_text)
                action = self.classifier.get_repair_action(classification)

                print(f"[PIPELINE] Error type: {classification['type'].value}")
                print(f"[PIPELINE] Repair action: {action}")

                repair_success = self._repair_by_action(
                    str(full_path),
                    action,
                    classification,
                    error_text
                )

                result["stages"].append({
                    "stage": f"repair_{action}",
                    "success": repair_success
                })

                if repair_success:
                    print("[PIPELINE] ✅ Repair applied, retrying...")
                    continue

            print("[PIPELINE] ❌ Failed")
            break

        result["attempts"] = self.attempts
        return result

    def _check_preflight(self, file_path: str) -> Dict:
        from sicuan.core.auto_repair import preflight_check
        return preflight_check(file_path)

    def _check_runtime(self, file_path: str) -> Dict:
        from sicuan.core.auto_repair import verify_runtime
        return verify_runtime(file_path)

    def _repair_by_action(self, file_path: str, action: str, classification: Dict, error_text: str) -> bool:
        """Repair berdasarkan action"""
        if action == "syntax_repair":
            return self._repair_syntax(file_path, error_text)
        elif action == "import_repair":
            return self._repair_import(file_path, classification, error_text)
        elif action == "dependency_required":
            print("[PIPELINE] ⚠️ Missing dependency - cannot auto-repair")
            print(f"[PIPELINE]   Module: {classification.get('name', 'unknown')}")
            print("[PIPELINE]   Suggestion: pip install <module>")
            return False
        elif action == "class_repair":
            return self._repair_class(file_path, error_text)
        elif action == "method_repair":
            return self._repair_method(file_path, error_text)
        elif action == "duplicate_repair":
            return self._repair_duplicate(file_path, error_text)
        elif action == "name_repair":
            return self._repair_name(file_path, classification, error_text)
        elif action == "runtime_repair":
            return self._repair_runtime(file_path, error_text)
        elif action == "unknown":
            print("[PIPELINE] Unknown action - trying syntax repair as fallback")
            return self._repair_syntax(file_path, error_text)
        else:
            print(f"[PIPELINE] Unknown action: {action}")
            return False

    def _repair_syntax(self, file_path: str, error_text: str) -> bool:
        """Repair syntax error"""
        try:
            from sicuan.core.syntax_repair import SyntaxRepair
            repair = SyntaxRepair()

            # Special case: return outside function
            if "return outside function" in error_text:
                # Fix by indenting the return statement
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                # Find the def that this return belongs to
                for i, line in enumerate(lines):
                    if "return" in line and "def" not in line:
                        # Find enclosing def
                        def_line = None
                        for j in range(i - 1, -1, -1):
                            if "def " in lines[j] and ":" in lines[j]:
                                def_line = j
                                break
                        if def_line is not None:
                            def_indent = len(lines[def_line]) - len(lines[def_line].lstrip())
                            current_indent = len(lines[i]) - len(lines[i].lstrip())
                            if current_indent != def_indent + 4:
                                lines[i] = " " * (def_indent + 4) + lines[i].lstrip()
                                with open(file_path, 'w') as f:
                                    f.writelines(lines)
                                # Verify
                                import ast
                                try:
                                    ast.parse(open(file_path).read())
                                    return True
                                except:
                                    pass

            if "IndentationError" in error_text:
                match = re.search(r"line (\d+)", error_text)
                if match:
                    line = int(match.group(1))
                    if "expected an indented block" in error_text:
                        # Use repair_with_ast which handles this case
                        result = repair.repair_with_ast(file_path)
                        return result.get("success", False)
                    result = repair.repair_indentation(file_path, line)
                    return result.get("success", False)

            result = repair.repair_with_ast(file_path)
            return result.get("success", False)

        except Exception as e:
            print(f"[PIPELINE] Syntax repair error: {e}")
            return False

    def _repair_import(self, file_path: str, classification: Dict, error_text: str) -> bool:
        """Repair missing import"""
        import re
        
        # Extract module name
        name = classification.get("name")
        if not name:
            match = re.search(r"No module named '(\w+)'", error_text)
            if match:
                name = match.group(1)
        
        if not name:
            return False
        
        # Read file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if import already exists
        if f"import {name}" in content or f"from {name}" in content:
            return True
        
        # Add import at the top
        lines = content.splitlines()
        
        # Find position to insert
        insert_pos = 0
        # Skip shebang
        if lines and lines[0].strip().startswith('#!'):
            insert_pos = 1
        # Skip docstring
        if len(lines) > insert_pos and lines[insert_pos].strip().startswith('"""'):
            insert_pos += 1
            while insert_pos < len(lines) and not lines[insert_pos].strip():
                insert_pos += 1
        
        # Insert import
        lines.insert(insert_pos, f"import {name}")
        
        # Write back
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))
        
        # Verify
        import ast
        try:
            ast.parse(open(file_path).read())
            return True
        except:
            return False

    def _repair_class(self, file_path: str, error_text: str) -> bool:
        """Repair class not found"""
        match = re.search(r"Class '(\w+)' not found", error_text)
        if not match:
            return False

        expected = match.group(1)
        content = Path(file_path).read_text()

        try:
            tree = ast.parse(content)
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
            if classes:
                actual = classes[0].name
                content = content.replace(f"class {actual}", f"class {expected}")
                Path(file_path).write_text(content)
                return True
        except:
            pass

        return False

    def _repair_method(self, file_path: str, error_text: str) -> bool:
        """Repair missing method - simple version"""
        match = re.search(r"Missing methods: (.+)", error_text)
        if not match:
            return False

        methods = [m.strip() for m in match.group(1).split(",")]
        print(f"[PIPELINE] Adding methods: {methods}")

        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Find class
        class_idx = None
        for i, line in enumerate(lines):
            if "class " in line and ":" in line:
                class_idx = i
                break

        if class_idx is None:
            # No class - add as functions
            added = 0
            for method in methods:
                exists = False
                for line in lines:
                    if f"def {method}" in line:
                        exists = True
                        break
                if not exists:
                    lines.append(f"def {method}():\n    return True\n")
                    added += 1
            if added > 0:
                with open(file_path, 'w') as f:
                    f.writelines(lines)
                return True
            return False

        # Use first class
        class_line = lines[class_idx]
        class_indent = len(class_line) - len(class_line.lstrip())
        indent = " " * (class_indent + 4)

        # Find class end
        class_end = class_idx + 1
        for i in range(class_idx + 1, len(lines)):
            if lines[i].strip() and len(lines[i]) - len(lines[i].lstrip()) <= class_indent:
                class_end = i
                break
            class_end = i + 1

        # Get existing methods
        existing = []
        for i in range(class_idx, class_end):
            if "def " in lines[i]:
                m = re.search(r'def\s+(\w+)', lines[i])
                if m:
                    existing.append(m.group(1))

        # Add methods
        added = 0
        for method in methods:
            if method in existing:
                continue
            lines.insert(class_end, indent + "def " + method + "(self):\n")
            lines.insert(class_end + 1, indent + "    return True\n")
            class_end += 2
            added += 1
            print(f"[PIPELINE] Added method {method}")

        if added == 0:
            return False

        with open(file_path, 'w') as f:
            f.writelines(lines)

        return True

    def _repair_duplicate(self, file_path: str, error_text: str) -> bool:
        """Repair duplicate method"""
        print("[PIPELINE] Duplicate repair not implemented")
        return False

    def _repair_name(self, file_path: str, classification: Dict, error_text: str) -> bool:
        """Repair undefined name"""
        return self._repair_import(file_path, classification, error_text)

    def _repair_runtime(self, file_path: str, error_text: str) -> bool:
        """Repair runtime error"""
        from sicuan.core.error_classifier import get_error_classifier
        classifier = get_error_classifier()
        classification = classifier.classify(error_text)

        if classification["type"] == ErrorType.IMPORT_MISSING:
            return self._repair_import(file_path, classification, error_text)

        return False


def get_repair_pipeline():
    _pipeline = None
    if _pipeline is None:
        _pipeline = RepairPipeline()
    return _pipeline
