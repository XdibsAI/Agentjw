"""
Input Validator - Cegah prompt injection dan input berbahaya
"""

import re
from typing import Dict, Any

class InputValidator:
    """Validasi input user sebelum diproses"""
    
    FORBIDDEN_PATTERNS = [
        r'rm\s+-rf\s+/',  # rm -rf /
        r'sudo\s+',       # sudo commands
        r'curl.*\|.*sh',  # curl pipe sh
        r'wget.*\|.*sh',  # wget pipe sh
        r'chmod\s+777',   # chmod 777
        r'chown\s+-R',    # chown -R
        r'dd\s+if=',      # dd if=
        r':\s*;\s*:',     # command injection
        r'\$\{',          # variable expansion
        r'`.*`',          # backticks
        r'\$\(.*\)',      # $() execution
    ]
    
    @classmethod
    def validate(cls, input_text: str, max_length: int = 10000) -> Dict[str, Any]:
        """Validasi input dan return result"""
        if not input_text or len(input_text.strip()) == 0:
            return {"valid": False, "error": "Input kosong"}
        
        if len(input_text) > max_length:
            return {"valid": False, "error": f"Input terlalu panjang (max {max_length} chars)"}
        
        # Cek pattern berbahaya
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, input_text, re.IGNORECASE):
                return {
                    "valid": False,
                    "error": f"Input mengandung pattern yang tidak diizinkan: {pattern}"
                }
        
        # White-list: hanya karakter yang diizinkan
        if not re.match(r'^[\w\s.,!?()\-:;\/@#$%^&*+=~`\'"\[\]{}|<>]+$', input_text):
            return {
                "valid": False,
                "error": "Input mengandung karakter yang tidak diizinkan"
            }
        
        return {"valid": True, "cleaned": input_text.strip()}
