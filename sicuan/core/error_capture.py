"""
Error Capture Layer — Tangkap error lengkap dari bot
"""

import subprocess
import time
from pathlib import Path
from typing import Dict, Optional


class ErrorCapture:
    """Capture error lengkap dari start bot"""

    def __init__(self, project_dir: str = "/home/dibs/agentjw/projects/godmeme_bot"):
        self.project_dir = Path(project_dir)
        self.bot_path = self.project_dir / "main.py"

    def capture(self) -> Dict:
        """
        Start bot dan capture semua output
        Returns:
        {
            "success": bool,
            "stdout": str,
            "stderr": str,
            "traceback": str,
            "exit_code": int,
            "error_type": str,  # ImportError, SyntaxError, AttributeError, dll
            "error_message": str,
            "file": str,
            "line": int
        }
        """
        result = {
            "success": False,
            "stdout": "",
            "stderr": "",
            "traceback": "",
            "exit_code": -1,
            "error_type": "unknown",
            "error_message": "",
            "file": "",
            "line": 0
        }

        if not self.bot_path.exists():
            result["error_message"] = f"Bot not found: {self.bot_path}"
            result["error_type"] = "FileNotFoundError"
            return result

        try:
            # Kill existing bot
            subprocess.run(["pkill", "-f", "main.py"], capture_output=True, timeout=5)
            time.sleep(2)

            # Start bot dengan capture
            process = subprocess.Popen(
                ["python3", str(self.bot_path)],
                cwd=str(self.project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Tunggu sebentar
            time.sleep(3)

            # Cek apakah masih running
            if process.poll() is not None:
                # Bot exited — ambil output
                stdout, stderr = process.communicate(timeout=5)
                result["stdout"] = stdout
                result["stderr"] = stderr
                result["exit_code"] = process.returncode
                result["success"] = False

                # Parse error
                output = stderr or stdout
                if output:
                    result["traceback"] = output[:2000]
                    self._parse_error(output, result)
            else:
                # Bot running
                result["success"] = True
                result["exit_code"] = 0
                # Kill bot setelah capture
                process.terminate()
                time.sleep(1)
                process.kill()

        except Exception as e:
            result["error_message"] = str(e)
            result["error_type"] = "Exception"

        return result

    def _parse_error(self, output: str, result: Dict):
        """Parse error dari output"""
        import re

        # Cari traceback
        lines = output.split('\n')
        error_lines = [l for l in lines if l.strip() and ('Error' in l or 'Exception' in l or 'Traceback' in l)]

        if error_lines:
            result["traceback"] = '\n'.join(error_lines)

            # Cari jenis error
            for line in error_lines:
                if 'Error:' in line or 'Exception:' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        result["error_type"] = parts[0].strip()
                        result["error_message"] = parts[1].strip()

            # Cari file dan line
            file_match = re.search(r'File "([^"]+)", line (\d+)', output)
            if file_match:
                result["file"] = file_match.group(1)
                result["line"] = int(file_match.group(2))

        # Jika tidak ada error spesifik, coba deteksi
        if result["error_type"] == "unknown":
            if "ModuleNotFoundError" in output:
                result["error_type"] = "ModuleNotFoundError"
            elif "ImportError" in output:
                result["error_type"] = "ImportError"
            elif "SyntaxError" in output:
                result["error_type"] = "SyntaxError"
            elif "AttributeError" in output:
                result["error_type"] = "AttributeError"
            elif "IndentationError" in output:
                result["error_type"] = "IndentationError"


# Singleton
_capturer = None

def get_error_capturer():
    global _capturer
    if _capturer is None:
        _capturer = ErrorCapture()
    return _capturer
