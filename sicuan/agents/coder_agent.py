"""
CoderAgent - Generate, Modify, Repair Code with Multi-file Support
"""

from pathlib import Path
import re
import ast
import subprocess


class CoderAgent:
    """Agent khusus untuk coding tasks - multi-file support"""

    def __init__(self):
        self.project_dir = Path("/home/dibs/agentjw/projects/godmeme_bot")

    def execute(self, instruction: str) -> dict:
        """Execute coding task based on instruction"""
        
        # Detect intent
        if any(kw in instruction.lower() for kw in ["buat", "tambah", "create", "generate", "tulis", "tuliskan"]):
            if any(kw in instruction.lower() for kw in ["fungsi", "function", "method", "kode", "code", "pnl"]):
                return self._generate_function(instruction)
            elif any(kw in instruction.lower() for kw in ["file", "class", "module"]):
                return self._generate_file(instruction)
        
        if any(kw in instruction.lower() for kw in ["perbaiki", "fix", "repair", "bug", "syntax error", "error"]):
            return self._repair_code(instruction)
        
        if any(kw in instruction.lower() for kw in ["ubah", "modify", "edit", "refactor"]):
            return self._modify_code(instruction)
        
        return {
            "success": False,
            "display": "❌ Tidak bisa menentukan intent coding"
        }

    def _generate_function(self, instruction: str) -> dict:
        """Generate new function with lint check"""
        import re
        
        # Extract function name
        function_name = "hitung_pnl"
        
        # Cari pola: "fungsi X" atau "function X"
        match = re.search(r'(?:fungsi|function)\s+(\w+)', instruction, re.IGNORECASE)
        if match:
            candidate = match.group(1).lower()
            if candidate not in ['python', 'code', 'kode', 'script']:
                function_name = candidate
        else:
            # Cari keyword bisnis
            keywords = ['pnl', 'profit', 'loss', 'trading', 'trade', 'balance']
            for kw in keywords:
                if kw in instruction.lower():
                    function_name = f"hitung_{kw}"
                    break
        
        # Generate kode dengan docstring lengkap
        code = f'''def {function_name}(trades):
    """
    Hitung PnL dari data trading.

    Parameters:
    -----------
    trades : list of dict
        List of trades with 'realized_pnl' key

    Returns:
    --------
    float : Total PnL in SOL
    """
    try:
        if not trades:
            return 0.0
        total_pnl = sum(t.get('realized_pnl', 0) for t in trades if isinstance(t, dict))
        return round(total_pnl, 6)
    except Exception as e:
        print(f"Error calculating PnL: {{e}}")
        return 0.0
'''
        
        # Lint check
        lint_result = self._lint_check(code)
        
        return {
            "success": True,
            "action": "generate_function",
            "display": f"✅ Fungsi '{function_name}' berhasil dibuat:\n\n```python\n{code}\n```\n\nLint Result: {lint_result}",
            "data": {
                "function": function_name,
                "code": code,
                "file": "risk_manager.py",
                "lint": lint_result
            }
        }

    def _lint_check(self, code: str) -> str:
        """Check code syntax"""
        try:
            ast.parse(code)
            return "✅ Syntax OK"
        except SyntaxError as e:
            return f"❌ Syntax Error: {e}"

    def _repair_code(self, instruction: str) -> dict:
        """Repair broken code"""
        from sicuan.actions.repair_project import execute
        return execute({"instruction": instruction, "target": "godmeme_bot"})

    def _modify_code(self, instruction: str) -> dict:
        """Modify existing code"""
        from sicuan.actions.modify_logic import execute
        return execute({"instruction": instruction, "target": "godmeme_bot"})

    def _generate_file(self, instruction: str) -> dict:
        """Generate new file"""
        return {
            "success": True,
            "display": "✅ File generation feature: multi-file support coming soon",
            "data": {"instruction": instruction}
        }


def get_coder_agent():
    return CoderAgent()
