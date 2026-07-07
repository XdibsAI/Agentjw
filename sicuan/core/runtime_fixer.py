"""
Runtime Fixer — Perbaiki error runtime seperti AttributeError
"""

from pathlib import Path
from typing import Dict
from sicuan.core.method_restorer import get_method_restorer


class RuntimeFixer:
    """Fix runtime errors"""

    def __init__(self):
        self.restorer = get_method_restorer()

    def fix_attribute_error(self, error: str, file_path: str) -> Dict:
        """Fix AttributeError: method missing"""
        import re

        # Extract method name
        match = re.search(r"has no attribute '([^']+)'", error)
        if not match:
            return {"success": False, "error": "Could not extract method name"}

        method_name = match.group(1)

        # Cari class name (default: Strategy)
        class_name = "Strategy"

        # Restore method
        result = self.restorer.restore_method(file_path, method_name, class_name)

        if not result["success"]:
            return {"success": False, "error": "Could not restore method"}

        # Apply to file
        full_path = Path("projects/godmeme_bot") / file_path
        if not full_path.exists():
            full_path = Path(file_path)

        content = full_path.read_text()

        # Cek apakah method sudah ada
        if method_name in content:
            return {"success": True, "message": f"Method {method_name} already exists"}

        # Tambahkan method
        lines = content.splitlines()
        lines.append("")
        lines.append(result["content"])
        full_path.write_text("\n".join(lines))

        return {
            "success": True,
            "message": f"Method {method_name} restored from {result['source']}",
            "method": method_name,
            "source": result["source"]
        }


# Singleton
_fixer = None

def get_runtime_fixer():
    global _fixer
    if _fixer is None:
        _fixer = RuntimeFixer()
    return _fixer
