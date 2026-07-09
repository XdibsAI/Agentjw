"""
ReviewerAgent - Code Review with structured output
"""

from pathlib import Path
import ast
import re


class ReviewerAgent:
    """Agent khusus untuk code review - structured output"""

    def __init__(self):
        self.project_dir = Path("/home/dibs/agentjw/projects/godmeme_bot")

    def execute(self, instruction: str) -> dict:
        """Execute review task with structured output"""
        target_file = self._extract_target(instruction)
        
        if not target_file:
            return {
                "success": False,
                "display": "❌ Tidak ada file yang disebutkan untuk direview",
                "data": {"error": "no_file"}
            }
        
        file_path = self.project_dir / target_file
        if not file_path.exists():
            return {
                "success": False,
                "display": f"❌ File '{target_file}' tidak ditemukan",
                "data": {"error": "file_not_found", "file": target_file}
            }
        
        content = file_path.read_text()
        lines = content.splitlines()
        
        # Analyze
        analysis = self._analyze_code(content, target_file, lines, file_path)
        
        return {
            "success": analysis.get("success", False),
            "display": analysis.get("display", ""),
            "data": analysis.get("data", {})
        }

    def _analyze_code(self, content: str, target_file: str, lines: list, full_path: Path) -> dict:
        """Comprehensive code analysis with structured data"""
        
        functions = []
        classes = []
        imports = []
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": len(node.args.args)
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": len([m for m in node.body if isinstance(m, ast.FunctionDef)])
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module)
        except SyntaxError as e:
            # Return structured syntax error
            function_name = self._find_function_name(lines, e.lineno) if lines else ""
            
            error_data = {
                "file": target_file,
                "path": str(full_path),
                "line": e.lineno,
                "column": e.offset,
                "error": e.msg,
                "function": function_name,
                "snippet": lines[max(0, e.lineno-3):min(len(lines), e.lineno+2)] if lines else []
            }
            
            display = f"❌ Syntax Error di {target_file}: {e.msg}\n\n"
            if e.lineno:
                display += f"Line {e.lineno}: {e.text.strip() if e.text else ''}\n\nContext:\n"
                start = max(0, e.lineno - 3)
                end = min(len(lines), e.lineno + 2)
                for i in range(start, end):
                    if i < len(lines):
                        prefix = ">>> " if i == e.lineno - 1 else "    "
                        display += f"{prefix}{i+1}: {lines[i]}\n"
            
            return {
                "success": False,
                "display": display,
                "data": error_data
            }
        except Exception as e:
            return {
                "success": False,
                "display": f"❌ Error parsing {target_file}: {e}",
                "data": {"error": str(e), "file": target_file}
            }
        
        # Success - no syntax error
        return {
            "success": True,
            "display": f"✅ No syntax errors found in {target_file}",
            "data": {
                "file": target_file,
                "path": str(full_path),
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "total_lines": len(lines)
            }
        }

    def _find_function_name(self, lines: list, line: int) -> str:
        """Cari nama fungsi di sekitar line"""
        for i in range(line - 1, max(0, line - 20), -1):
            if i < len(lines):
                stripped = lines[i].strip()
                if stripped.startswith("def ") or stripped.startswith("async def "):
                    parts = stripped.split("(")[0].split()
                    return parts[-1] if parts else ""
        return ""

    def _extract_target(self, instruction: str) -> str:
        """Extract target file from instruction"""
        match = re.search(r'(\w+\.py)', instruction)
        if match:
            return match.group(1)
        
        common = ["strategy.py", "sniper.py", "risk_manager.py", "config.py", "main.py"]
        for f in common:
            if f in instruction.lower():
                return f
        
        if any(kw in instruction.lower() for kw in ["kode", "code", "strategi", "strategy"]):
            return "strategy.py"
        
        return None


def get_reviewer_agent():
    return ReviewerAgent()
