"""
RepairAgent - Full Repair Pipeline: Extract → Patch → Compile → Verify
"""

from pathlib import Path
import ast
import re
import subprocess
from typing import Dict, Optional
from sicuan.core.function_extractor import get_function_extractor
from sicuan.core.deterministic_repair import get_deterministic_repair


class RepairAgent:
    """Agent khusus untuk repair dengan pipeline lengkap"""

    def __init__(self):
        self.project_dir = Path("/home/dibs/agentjw/projects/godmeme_bot")
        self.max_attempts = 3

    def execute(self, instruction: str, error_context: Dict = None) -> dict:
        """Execute repair dengan full pipeline"""
        
        if not error_context:
            return {"success": False, "display": "❌ No error context provided"}
        
        file_name = error_context.get("file", "strategy.py")
        line = error_context.get("line", 0)
        error_msg = error_context.get("error_msg", "")
        
        if not line:
            return {"success": False, "display": "❌ No line number in context"}
        
        # Step 1: Extract function
        extractor = get_function_extractor()
        func_info = extractor.extract(file_name, line)
        
        if "error" in func_info:
            return {"success": False, "display": f"❌ {func_info['error']}"}
        
        # Step 2: Try deterministic repair first
        deterministic = get_deterministic_repair()
        result = deterministic.repair(str(self.project_dir / file_name), error_context)
        
        if result.get("success"):
            return {"success": True, "display": f"✅ {result.get('message')}"}
        
        # Step 3: AI repair (if deterministic fails)
        return self._ai_repair_func(func_info, error_msg)

    def _ai_repair_func(self, func_info: Dict, error_msg: str) -> dict:
        """AI repair untuk fungsi spesifik - perbaiki SELURUH fungsi"""
        import ast
        import traceback
        
        function_code = func_info.get("function_code", "")
        function_name = func_info.get("function_name", "")
        file_path = func_info.get("full_path", "")
        lines = func_info.get("lines", [])
        start = func_info.get("function_start", 0)
        end = func_info.get("function_end", 0)
        
        if not function_code or not file_path:
            return {"success": False, "display": "❌ Cannot extract function"}
        
        # Build prompt untuk repair - minta perbaiki SELURUH fungsi
        prompt = f"""Perbaiki fungsi Python berikut. Error: {error_msg}

Fungsi yang rusak (SELURUH fungsi):
```python
{function_code}
"""

        try:
            # Import LLM dengan benar (tanpa sys.path, tanpa model=)
            from core.llm_client import llm
            
            print(f"[REPAIR] Calling LLM for function: {function_name}")
            
            # Panggil dengan signature yang benar
            response = llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            )
            
            print(f"[REPAIR] LLM response received, length: {len(response) if response else 0}")
            
            # Ekstrak code dari response
            import re
            code_match = re.search(r'```python\s*(.*?)\s*```', response, re.DOTALL)
            if code_match:
                fixed_code = code_match.group(1)
            else:
                code_match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
                if code_match:
                    fixed_code = code_match.group(1)
                else:
                    fixed_code = response
            
            # Replace seluruh fungsi di file (bukan per baris)
            new_lines = lines[:start-1] + fixed_code.splitlines() + lines[end:]
            full_path = Path(file_path)
            full_path.write_text("\n".join(new_lines))
            
            # Verify
            try:
                ast.parse(full_path.read_text())
                return {
                    "success": True,
                    "display": f"✅ Repaired function '{function_name}' successfully"
                }
            except SyntaxError as e:
                return {
                    "success": False,
                    "display": f"❌ Still error: {e}"
                }
                
        except Exception as e:
            print(f"[REPAIR] ERROR: {e}")
            print(traceback.format_exc())
            
            # Fallback: deterministic repair untuk indentation saja
            det = get_deterministic_repair()
            result = det.repair(file_path, {"line": start, "error_msg": error_msg})
            if result.get("success"):
                return {"success": True, "display": f"✅ {result.get('message')}"}
            
            return {"success": False, "display": f"❌ Repair failed: {e}"}


def get_repair_agent():
    return RepairAgent()
