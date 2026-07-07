"""
Method Restorer — Cari dan restore method yang hilang dari history
"""

import subprocess
import re
from pathlib import Path
from typing import Dict, Optional, List


class MethodRestorer:
    """Cari method yang hilang dari git history atau file backup"""

    def __init__(self, project_dir: str = "/home/dibs/agentjw/projects/godmeme_bot"):
        self.project_dir = Path(project_dir)

    def find_method_in_history(self, file_path: str, method_name: str) -> Optional[str]:
        """Cari method di git history"""
        try:
            # Cari di git log untuk file
            result = subprocess.run(
                ["git", "log", "-p", "--", file_path],
                cwd=str(self.project_dir),
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            # Cari method
            pattern = rf"async def {method_name}|def {method_name}"
            matches = re.findall(
                rf"(async\s+def\s+{method_name}.*?)(?=\n\s*async\s+def|\n\s*def\s+|\Z)",
                result.stdout,
                re.DOTALL
            )

            if matches:
                return matches[-1]  # Ambil yang terbaru

            return None

        except Exception as e:
            print(f"[RESTORE] Error finding method: {e}")
            return None

    def generate_skeleton(self, method_name: str, class_name: str = "Strategy") -> str:
        """Generate skeleton method"""
        return f'''    async def {method_name}(self) -> bool:
        """Auto-generated skeleton for {method_name}"""
        logger.warning(f"{method_name} called (skeleton)")
        return True'''

    def restore_method(self, file_path: str, method_name: str, class_name: str = "Strategy") -> Dict:
        """Restore method dari history atau generate skeleton"""
        result = {
            "success": False,
            "method": method_name,
            "source": "none",
            "content": ""
        }

        # 1. Coba cari di history
        method_content = self.find_method_in_history(file_path, method_name)

        if method_content:
            result["success"] = True
            result["source"] = "history"
            result["content"] = method_content
            print(f"[RESTORE] ✅ Found {method_name} in history")
            return result

        # 2. Generate skeleton
        skeleton = self.generate_skeleton(method_name, class_name)
        result["success"] = True
        result["source"] = "skeleton"
        result["content"] = skeleton
        print(f"[RESTORE] ✅ Generated skeleton for {method_name}")

        return result


# Singleton
_restorer = None

def get_method_restorer():
    global _restorer
    if _restorer is None:
        _restorer = MethodRestorer()
    return _restorer
