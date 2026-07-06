"""
Error-to-Fix Mapping — Pengetahuan SiCuan untuk memperbaiki error
"""

import re
from typing import Dict, List, Optional, Tuple


class ErrorFixMap:
    """Mapping error ke solusi perbaikan"""

    # Mapping error pattern → fix action
    ERROR_FIX_MAP = {
        # Module not found
        "ModuleNotFoundError: No module named 'sicuan'": {
            "action": "modify_logic",
            "target": "strategy.py",
            "fix": "Tambahkan sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) di awal file",
            "code": """
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
""",
            "file": "strategy.py"
        },
        
        # Indentation error
        "IndentationError: unexpected indent": {
            "action": "modify_logic",
            "target": None,  # akan diisi dari error
            "fix": "Perbaiki indentasi di line {line}",
            "file": None
        },
        
        # Attribute error
        "AttributeError: .* has no attribute '([^']+)'": {
            "action": "modify_logic",
            "target": None,
            "fix": "Tambahkan method {method} di class {class}",
            "file": None
        },
        
        # Import error
        "ImportError: cannot import name '([^']+)'": {
            "action": "modify_logic",
            "target": None,
            "fix": "Perbaiki import {name} di file {file}",
            "file": None
        },
        
        # Syntax error
        "SyntaxError: invalid syntax": {
            "action": "modify_logic",
            "target": None,
            "fix": "Perbaiki syntax error di line {line}",
            "file": None
        },
        
        # Restart failed
        "Restart failed": {
            "action": "modify_logic",
            "target": "strategy.py",
            "fix": "Perbaiki error yang menyebabkan bot tidak bisa start",
            "file": "strategy.py"
        },

        # ModuleNotFoundError dengan path
        "ModuleNotFoundError: No module named 'sicuan'": {
            "action": "modify_logic",
            "target": "strategy.py",
            "fix": "Ganti sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) dengan sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))",
            "file": "strategy.py"
        },
        # Path error
        "File.*strategy.py.*No module named": {
            "action": "modify_logic",
            "target": "strategy.py",
            "fix": "Perbaiki import path di strategy.py",
            "file": "strategy.py"
        },
        
        # AttributeError: _check_cooldown missing
        "AttributeError: 'Strategy' object has no attribute '_check_cooldown'": {
            "action": "modify_logic",
            "target": "strategy.py",
            "fix": "Tambahkan method _check_cooldown di class Strategy",
            "file": "strategy.py"
        },
        # Generic AttributeError
        "AttributeError: '([^']+)' object has no attribute '([^']+)'": {
            "action": "modify_logic",
            "target": "strategy.py",
            "fix": "Tambahkan method {2} di class {1} di strategy.py",
            "file": "strategy.py"
        },
        
        # IndentationError
        "IndentationError: unexpected indent": {
            "action": "modify_logic",
            "target": "strategy.py",
            "fix": "Perbaiki indentasi di file yang error",
            "file": None
        },
        "IndentationError: expected an indented block": {
            "action": "modify_logic",
            "target": "strategy.py",
            "fix": "Tambahkan indentasi yang hilang",
            "file": None
        },
        
        "IndentationError: unexpected indent": {
            "action": "syntax_repair",
            "target": None,
            "fix": "Perbaiki indentasi otomatis",
            "file": None
        },
        "IndentationError: expected an indented block": {
            "action": "syntax_repair",
            "target": None,
            "fix": "Tambahkan indentasi yang hilang",
            "file": None
        },
        
        # AttributeError: _check_cooldown missing — deterministic fix
        "AttributeError: 'Strategy' object has no attribute '_check_cooldown'": {
            "action": "add_method",
            "target": "strategy.py",
            "fix": "Tambahkan method _check_cooldown di class Strategy",
            "file": "strategy.py",
            "method_name": "_check_cooldown",
            "method_body": "async def _check_cooldown(self) -> bool:\n        if not hasattr(self, '_cooldown_until'):\n            self._cooldown_until = 0\n            self._cooldown_mode = False\n        if self._cooldown_until and time.time() < self._cooldown_until:\n            remaining = int(self._cooldown_until - time.time())\n            if remaining % 60 == 0:\n                logger.info(f'COOLDOWN: {remaining//60}m remaining')\n            return True\n        return False"
        },
        # Generic AttributeError (fallback)
        "AttributeError: '([^']+)' object has no attribute '([^']+)'": {
            "action": "modify_logic",
            "target": "strategy.py",
            "fix": "Tambahkan method {2} di class {1} di strategy.py",
            "file": "strategy.py"
        },
                # General error fallback
        "default": {
            "action": "analyze_project",
            "target": None,
            "fix": "Analisis error dan berikan rekomendasi",
            "file": None
        }
    }

    def __init__(self):
        self.fix_history = []
        self.error_patterns = self._compile_patterns()

    def _compile_patterns(self) -> List[Tuple[str, str]]:
        """Compile semua pattern untuk matching"""
        patterns = []
        for pattern in self.ERROR_FIX_MAP.keys():
            if pattern != "default":
                try:
                    patterns.append((re.compile(pattern), pattern))
                except:
                    patterns.append((re.compile(re.escape(pattern)), pattern))
        return patterns

    def diagnose(self, error_message: str) -> Dict:
        """Diagnose error dan dapatkan fix action"""
        # Coba match dengan pattern
        for pattern, key in self.error_patterns:
            match = pattern.search(error_message)
            if match:
                fix_data = self.ERROR_FIX_MAP.get(key, {})
                
                # Extract info dari match
                result = {
                    "action": fix_data.get("action", "analyze_project"),
                    "target": fix_data.get("target"),
                    "file": fix_data.get("file"),
                    "fix": fix_data.get("fix", "Perbaiki error"),
                    "matched_pattern": key,
                    "confidence": 0.9
                }
                
                # Replace placeholders
                if match.groups():
                    for i, group in enumerate(match.groups(), 1):
                        result["fix"] = result["fix"].replace(f"{{{i}}}", group)
                
                # Extract file and line jika ada
                file_match = re.search(r'File "([^"]+)", line (\d+)', error_message)
                if file_match:
                    result["file"] = file_match.group(1)
                    result["line"] = int(file_match.group(2))
                
                return result
        
        # Default fallback
        return {
            "action": "analyze_project",
            "target": None,
            "file": None,
            "fix": "Analisis error dan berikan rekomendasi",
            "confidence": 0.3
        }

    def get_fix_command(self, diagnosis: Dict) -> str:
        """Generate fix command dari diagnosis"""
        action = diagnosis.get("action")
        target = diagnosis.get("target", "godmeme_bot")
        fix = diagnosis.get("fix", "")
        
        if action == "modify_logic":
            return f"Perbaiki {target}: {fix}"
        elif action == "repair_project":
            return f"Repair project {target}"
        else:
            return f"Analisis error di {target}"

    def record_fix(self, error: str, fix: Dict, success: bool):
        """Record fix history untuk learning"""
        self.fix_history.append({
            "error": error[:200],
            "action": fix.get("action"),
            "success": success,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        })


# Singleton
_error_fixer = None

def get_error_fixer():
    global _error_fixer
    if _error_fixer is None:
        _error_fixer = ErrorFixMap()
    return _error_fixer
