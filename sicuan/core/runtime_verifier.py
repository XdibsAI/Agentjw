"""
Runtime Verifier — Verifikasi dengan Health Comparison
"""

import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional


class RuntimeVerifier:
    """Runtime Verification dengan health comparison"""

    def __init__(self, project_dir: str = "/home/dibs/agentjw/projects/godmeme_bot"):
        self.project_dir = Path(project_dir)
        self.log_file = self.project_dir / "trading_bot_live.log"
        self.bot_log = self.project_dir / "bot.log"
        self.paper_log = self.project_dir / "paper_24h.log"
        self.error_patterns = [
            "AttributeError",
            "ModuleNotFoundError",
            "SyntaxError",
            "IndentationError",
            "TypeError",
            "KeyError",
            "ValueError",
            "Exception"
        ]

    def verify(self, error: str, wait_time: int = 30) -> Dict:
        """
        Verifikasi dengan health comparison
        """
        result = {
            "success": False,
            "error_found": False,
            "errors": [],
            "message": "",
            "pid_before": None,
            "pid_after": None,
            "health_before": None,
            "health_after": None,
            "health_improved": False
        }

        # 0. Health BEFORE
        print("[VERIFY] 📊 Health BEFORE...")
        health_before = self._check_worker_health()
        result["health_before"] = health_before
        print(f"[VERIFY] Workers before: {health_before.get('workers_alive', 0)}/3")

        # 1. Restart bot
        print("[VERIFY] 🔄 Restarting bot...")
        if not self._restart_bot():
            result["message"] = "Bot restart failed"
            return result

        # 2. Cek PID baru
        pid_after = self._get_pid()
        result["pid_after"] = pid_after
        print(f"[VERIFY] PID after: {pid_after}")

        if pid_after is None:
            result["message"] = "Bot did not restart properly"
            return result

        # 3. Tunggu
        print(f"[VERIFY] ⏳ Waiting {wait_time}s...")
        time.sleep(wait_time)

        # 4. Cek process
        if not self._is_running():
            result["message"] = "Bot crashed during runtime"
            print("[VERIFY] ❌ Bot crashed")
            return result

        # 5. Cek log errors
        print("[VERIFY] 📝 Checking logs...")
        errors = self._check_logs_for_error(error)
        if errors:
            result["error_found"] = True
            result["errors"] = errors
            result["message"] = f"Found {len(errors)} errors"
            print(f"[VERIFY] ❌ Errors found: {len(errors)}")
            return result

        # 6. Cek log growth
        if not self._check_log_growth():
            result["message"] = "Log not growing"
            print("[VERIFY] ❌ Log not growing")
            return result

        # 7. Health AFTER (compare)
        print("[VERIFY] 📊 Health AFTER...")
        health_after = self._check_worker_health()
        result["health_after"] = health_after
        print(f"[VERIFY] Workers after: {health_after.get('workers_alive', 0)}/3")

        before_alive = health_before.get("workers_alive", 0)
        after_alive = health_after.get("workers_alive", 0)
        result["health_improved"] = after_alive > before_alive

        if after_alive >= 2:
            result["success"] = True
            result["message"] = f"✅ Workers: {before_alive} → {after_alive}"
            print(f"[VERIFY] ✅ Workers improved: {before_alive} → {after_alive}")
        else:
            result["success"] = False
            result["message"] = f"❌ Workers not healthy: {before_alive} → {after_alive}"
            print(f"[VERIFY] ❌ Workers not healthy: {before_alive} → {after_alive}")

        return result

    def _get_pid(self) -> Optional[int]:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "main.py"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split()[0])
        except:
            pass
        return None

    def _is_running(self) -> bool:
        return self._get_pid() is not None

    def _restart_bot(self) -> bool:
        try:
            subprocess.run(["pkill", "-f", "main.py"], capture_output=True, timeout=5)
            time.sleep(2)
            subprocess.Popen(
                ["python3", "main.py"],
                cwd=str(self.project_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(3)
            return self._is_running()
        except:
            return False

    def _check_logs_for_error(self, error: str) -> List[str]:
        if not self.log_file.exists():
            return []
        found = []
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()[-100:]
            for line in lines:
                for pattern in self.error_patterns:
                    if pattern in line:
                        found.append(line.strip())
            if error:
                for line in lines:
                    if error in line:
                        found.append(f"[SPECIFIC] {line.strip()}")
        except:
            pass
        return found

    def _check_log_growth(self) -> bool:
        if not self.log_file.exists():
            return False
        try:
            size_before = self.log_file.stat().st_size
            time.sleep(2)
            size_after = self.log_file.stat().st_size
            return size_after > size_before
        except:
            return False

    def _check_worker_health(self) -> Dict:
        result = {
            "token_monitor": False,
            "position_monitor": False,
            "strategy_loop": False,
            "last_heartbeat": 0,
            "exception_count": 0,
            "workers_alive": 0,
            "message": ""
        }

        log_files = [self.log_file, self.bot_log, self.paper_log]
        latest_log = None
        for f in log_files:
            if f.exists():
                if latest_log is None or f.stat().st_mtime > latest_log.stat().st_mtime:
                    latest_log = f

        if latest_log is None:
            result["message"] = "No log files found"
            return result

        try:
            with open(latest_log, "r") as f:
                lines = f.readlines()[-100:]

            token_lines = [l for l in lines if "Token monitor" in l]
            if token_lines and ("started" in token_lines[-1] or "scanning" in token_lines[-1]):
                result["token_monitor"] = True

            pos_lines = [l for l in lines if "Position monitor" in l]
            if pos_lines and ("started" in pos_lines[-1] or "monitoring" in pos_lines[-1]):
                result["position_monitor"] = True

            strategy_lines = [l for l in lines if "Strategy" in l and ("running" in l or "started" in l)]
            if strategy_lines:
                result["strategy_loop"] = True

            exceptions = [l for l in lines if "ERROR" in l or "Exception" in l]
            result["exception_count"] = len(exceptions)

            if lines:
                import re
                match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', lines[-1])
                if match:
                    from datetime import datetime
                    last_time = datetime.fromisoformat(match.group(1).replace(" ", "T"))
                    now = datetime.now()
                    result["last_heartbeat"] = int((now - last_time).total_seconds())

            workers = [result["token_monitor"], result["position_monitor"], result["strategy_loop"]]
            result["workers_alive"] = sum(workers)
            result["message"] = f"{result['workers_alive']}/3 workers alive"

        except Exception as e:
            result["message"] = f"Health check error: {e}"

        return result


# Singleton
_verifier = None

def get_runtime_verifier():
    global _verifier
    if _verifier is None:
        _verifier = RuntimeVerifier()
    return _verifier
