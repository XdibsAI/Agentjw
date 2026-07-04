"""
Runtime Verifier - Verifikasi patch dengan restart + health check
"""

import asyncio
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional


class RuntimeVerifier:
    """Verifikasi runtime setelah patch"""

    def __init__(self, project_dir: str = "projects/godmeme_bot"):
        self.project_dir = Path(project_dir)
        self.log_file = self.project_dir / "trading_bot_live.log"
        self.max_wait = 30  # detik

    def verify(self, patch_result: Dict) -> Dict:
        """Verifikasi patch dengan restart dan health check"""
        result = {
            "status": "pending",
            "restart_success": False,
            "runtime_ok": False,
            "error_free": False,
            "regression_pass": False,
            "details": []
        }

        # 1. Restart bot
        result["details"].append("🔄 Restarting bot...")
        restart_ok = self._restart_bot()
        result["restart_success"] = restart_ok
        
        if not restart_ok:
            result["status"] = "failed"
            result["details"].append("❌ Bot restart failed")
            return result

        result["details"].append("✅ Bot restarted")

        # 2. Wait and check runtime
        result["details"].append(f"⏳ Waiting {self.max_wait}s for runtime...")
        time.sleep(self.max_wait)

        # 3. Check for errors
        errors = self._check_errors()
        if errors:
            result["details"].append(f"❌ Errors found: {len(errors)}")
            result["details"].extend([f"  • {e}" for e in errors[:3]])
            result["error_free"] = False
            result["status"] = "failed"
            return result

        result["details"].append("✅ No errors found")
        result["error_free"] = True

        # 4. Check if bot is running
        is_running = self._is_bot_running()
        result["runtime_ok"] = is_running
        result["details"].append(f"✅ Bot running: {is_running}")

        if not is_running:
            result["status"] = "failed"
            return result

        # 5. Regression check
        regression = self._run_regression()
        result["regression_pass"] = regression
        result["details"].append(f"✅ Regression: {regression}")

        if regression:
            result["status"] = "verified"
            result["details"].append("🎉 Patch verified successfully!")
        else:
            result["status"] = "partial"
            result["details"].append("⚠️ Patch applied but regression pending")

        return result

    def _restart_bot(self) -> bool:
        """Restart bot"""
        try:
            # Kill existing
            subprocess.run(
                ["pkill", "-f", "main.py"],
                capture_output=True,
                timeout=5
            )
            time.sleep(2)

            # Start bot (background)
            subprocess.Popen(
                ["python3", "main.py"],
                cwd=str(self.project_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            print(f"Restart failed: {e}")
            return False

    def _check_errors(self) -> List[str]:
        """Check log for errors"""
        errors = []
        if not self.log_file.exists():
            return ["Log file not found"]

        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()[-50:]  # Last 50 lines
                for line in lines:
                    if "ERROR" in line or "WARNING" in line:
                        errors.append(line.strip())
        except Exception:
            pass

        return errors

    def _is_bot_running(self) -> bool:
        """Check if bot is running"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "main.py"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_regression(self) -> bool:
        """Run regression test"""
        try:
            result = subprocess.run(
                ["python3", "scripts/regression_suite.py"],
                cwd="/home/dibs/agentjw",
                capture_output=True,
                timeout=30
            )
            return "✅ Passed: 10" in str(result.stdout)
        except Exception:
            return False
