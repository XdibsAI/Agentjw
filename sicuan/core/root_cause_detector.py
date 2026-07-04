"""
Root Cause Detector - Identifikasi akar masalah dari error logs
"""

import re
from typing import Dict, List, Optional


class RootCauseDetector:
    """Deteksi akar masalah dari error message"""

    PATTERNS = {
        "missing_method": re.compile(r"'(\w+)' object has no attribute '(\w+)'"),
        "missing_import": re.compile(r"ModuleNotFoundError: No module named '(\w+)'"),
        "undefined_variable": re.compile(r"cannot access local variable '(\w+)'"),
        "syntax_error": re.compile(r"SyntaxError: (.*)"),
        "attribute_error": re.compile(r"AttributeError: (.*)"),
        "type_error": re.compile(r"TypeError: (.*)"),
        "key_error": re.compile(r"KeyError: '(.*)'"),
        "file_not_found": re.compile(r"FileNotFoundError: (.*)"),
    }

    def detect(self, error_log: str) -> Dict:
        """Deteksi root cause dari error log"""
        result = {
            "type": "unknown",
            "file": None,
            "target": None,
            "suggestion": "",
            "confidence": 0.0
        }

        for error_type, pattern in self.PATTERNS.items():
            match = pattern.search(error_log)
            if match:
                result["type"] = error_type
                result["confidence"] = 0.9
                
                if error_type == "missing_method":
                    obj = match.group(1)
                    method = match.group(2)
                    result["target"] = method
                    result["file"] = self._find_file_with_class(obj)
                    result["suggestion"] = f"Tambahkan method '{method}' di class '{obj}'"
                
                elif error_type == "undefined_variable":
                    var = match.group(1)
                    result["target"] = var
                    result["suggestion"] = f"Definisikan variable '{var}' sebelum digunakan"
                
                elif error_type == "missing_import":
                    module = match.group(1)
                    result["target"] = module
                    result["suggestion"] = f"Tambahkan import '{module}'"
                
                elif error_type == "file_not_found":
                    filepath = match.group(1)
                    result["target"] = filepath
                    result["suggestion"] = f"Pastikan file '{filepath}' ada"
                
                break

        return result

    def _find_file_with_class(self, class_name: str) -> Optional[str]:
        """Cari file yang mengandung class tertentu"""
        # Simple mapping untuk file yang umum
        common_files = {
            "Strategy": "strategy.py",
            "RiskManager": "risk_manager.py",
            "Notifier": "notifier.py",
            "Database": "database.py",
            "Wallet": "wallet.py",
            "Jupiter": "jupiter_client.py",
            "Config": "config.py",
        }
        return common_files.get(class_name, None)
