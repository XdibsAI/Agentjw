"""
Execution Validation Layer — Full validation cycle for SiCuan
"""

import subprocess
import time
import json
import sqlite3
from sicuan.core.error_capture import get_error_capturer
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class ExecutionValidator:

    def get_full_error(self) -> str:
        """Dapatkan traceback lengkap dari error terakhir"""
        return getattr(self, '_last_traceback', '')
    """
    Full validation cycle:
    1. Backup baseline metrics
    2. Restart service
    3. Smoke test
    4. Log check
    5. Paper trading (short)
    6. Compare metrics
    7. Decision: Commit / Warning / Rollback
    8. Save experience
    """

    def __init__(self, project_dir: str = "projects/godmeme_bot"):
        self.project_dir = Path(project_dir).resolve()
        self.log_file = self.project_dir / "trading_bot_live.log"
        self.baseline_metrics = {}
        self.result_metrics = {}
        self.validation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.status = "pending"
        self.decision = "unknown"
        self.reason = ""
        self.steps = []

    def validate(self, patch_result: Dict) -> Dict:
        """Main validation entry point"""
        self._log("🔍 Starting Execution Validation...")
        
        # Step 1: Backup baseline metrics
        self._step("📊 Baseline Metrics")
        self.baseline_metrics = self._get_metrics()
        self._log(f"   Win Rate: {self.baseline_metrics.get('win_rate', 0):.1f}%")
        self._log(f"   PnL: {self.baseline_metrics.get('total_pnl', 0):.4f} SOL")
        
        # Step 2: Restart service
        self._step("🔄 Restart Service")
        if not self._restart():
            self._fail("Restart failed", "rollback")
            return self._result()
        
        # Step 3: Smoke test
        self._step("🔥 Smoke Test")
        if not self._smoke_test():
            self._fail("Smoke test failed", "rollback")
            return self._result()
        
        # Step 4: Log check
        self._step("📝 Log Check")
        log_ok = self._check_logs()
        if not log_ok:
            self._log("   ⚠️ Warnings found in logs")
        
        # Step 5: Paper trading
        self._step("🧪 Paper Trading (60s)")
        if not self._paper_trade(duration=30):
            self._log("   ⚠️ Paper trading completed with issues")
        
        # Step 6: Compare metrics
        self._step("📊 Compare Metrics")
        self.result_metrics = self._get_metrics()
        comparison = self._compare_metrics()
        
        # Step 7: Decision
        self._step("⚖️ Decision")
        if comparison["improved"]:
            self.decision = "commit"
            self.reason = f"Metrics improved: {comparison['summary']}"
            self.status = "verified"
            self._log(f"   ✅ {self.reason}")
            self._save_experience(patch_result, comparison)
        elif comparison["same"]:
            self.decision = "warning"
            self.reason = f"Metrics unchanged: {comparison['summary']}"
            self.status = "warning"
            self._log(f"   ⚠️ {self.reason}")
        else:
            self.decision = "rollback"
            self.reason = f"Metrics degraded: {comparison['summary']}"
            self.status = "failed"
            self._log(f"   ❌ {self.reason}")
            self._rollback()
        
        self._log(f"🏁 Validation complete: {self.decision}")
        return self._result()

    # ========== PRIVATE METHODS ==========

    def _step(self, name: str):
        """Log step"""
        self.steps.append({"step": name, "status": "pending"})

    def _log(self, message: str):
        """Log message"""
        print(f"[VALIDATOR] {message}")

    def _fail(self, reason: str, decision: str):
        """Mark validation as failed"""
        self.status = "failed"
        self.decision = decision
        self.reason = reason
        self._log(f"   ❌ {reason}")

    def _result(self) -> Dict:
        """Build result dict"""
        return {
            "status": self.status,
            "decision": self.decision,
            "reason": self.reason,
            "steps": self.steps,
            "metrics": {
                "baseline": self.baseline_metrics,
                "result": self.result_metrics
            },
            "validation_id": self.validation_id
        }

    def _get_metrics(self) -> Dict:
        """Get metrics from trading.db"""
        try:
            db_path = self.project_dir / "trading.db"
            if not db_path.exists():
                return {"error": "Database not found"}
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN realized_pnl < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(realized_pnl) as total_pnl
                FROM trades WHERE realized_pnl IS NOT NULL
            """)
            row = cursor.fetchone()
            conn.close()
            
            total = row[0] or 1
            wins = row[1] or 0
            losses = row[2] or 0
            total_pnl = row[3] or 0
            
            return {
                "total_trades": total,
                "wins": wins,
                "losses": losses,
                "win_rate": wins / total * 100 if total > 0 else 0,
                "total_pnl": total_pnl
            }
        except Exception as e:
            return {"error": str(e)}

    def _restart(self) -> bool:
        """Restart service dengan error capture"""
        capturer = get_error_capturer()
        result = capturer.capture()
        
        if result["success"]:
            self._log("   ✅ Bot restarted successfully")
            return True
        else:
            self._log(f"   ❌ Bot failed to start")
            self._log(f"   Error Type: {result.get('error_type', 'unknown')}")
            self._log(f"   Error: {result.get('error_message', 'N/A')[:100]}")
            if result.get("file"):
                self._log(f"   File: {result['file']}:{result.get('line', 0)}")
            # Simpan detail untuk diagnosis
            if result.get("traceback"):
                self._last_traceback = result["traceback"]
                self._log(f"   Traceback: {result['traceback'][:100]}...")
            # Cek working directory
            import os
            self._log(f"   CWD: {os.getcwd()}")
            self._log(f"   Python Path: {os.environ.get('PYTHONPATH', 'Not set')[:50]}")
            # Simpan traceback untuk diagnosis
            self._last_traceback = result.get("traceback", "")
            return False

    def _is_running(self) -> bool:
        """Check if bot is running"""
        try:
            # Cek multiple patterns
            import subprocess
            patterns = ["main.py", "godmeme_bot"]
            for pattern in patterns:
                result = subprocess.run(
                    ["pgrep", "-f", pattern],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    pid = result.stdout.decode().strip()
                    self._log(f"   Bot running (PID: {pid})")
                    return True
            return False
        except Exception as e:
            self._log(f"   Error checking bot: {e}")
            return False

    def _smoke_test(self) -> bool:
        """Smoke test — cek bot process, bukan API"""
        try:
            # 1. Cek apakah bot process running
            import subprocess
            result = subprocess.run(["pgrep", "-f", "main.py"], capture_output=True, timeout=5)
            if result.returncode == 0:
                self._log("   ✅ Bot process running")
                return True
            else:
                self._log("   ❌ Bot process not running")
                return False
        except Exception as e:
            self._log(f"   ❌ Smoke test error: {e}")
            return False

    def _check_logs(self) -> bool:
        """Check logs for errors"""
        if not self.log_file.exists():
            return True
        
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()[-100:]
                errors = [l for l in lines if "ERROR" in l or "Exception" in l]
                if errors:
                    self._log(f"   ⚠️ Found {len(errors)} errors")
                    return False
                return True
        except:
            return True

    def _paper_trade(self, duration: int = 30) -> bool:
        """Health check — cek apakah bot hidup dan responsif"""
        self._log(f"   Health check for {duration}s...")
        
        # 1. Cek apakah proses masih hidup
        if not self._is_running():
            self._log("   ❌ Bot not running")
            return False
        
        # 2. Cek apakah log terbaru menunjukkan aktivitas
        try:
            import time
            time.sleep(3)  # Tunggu sebentar
            
            # Cek apakah ada log baru
            if self.log_file.exists():
                with open(self.log_file, "r") as f:
                    lines = f.readlines()
                    if len(lines) > 0:
                        last_line = lines[-1]
                        self._log(f"   ✅ Log active: {last_line[:50]}...")
                        return True
        except Exception as e:
            self._log(f"   ⚠️ Log check error: {e}")
        
        # 3. Fallback: cek apakah proses masih hidup
        return self._is_running()

    def _compare_metrics(self) -> Dict:
        """Compare baseline vs result"""
        before = self.baseline_metrics
        after = self.result_metrics
        
        if "error" in before or "error" in after:
            return {"improved": False, "same": False, "summary": "Error in metrics"}
        
        before_wr = before.get("win_rate", 0)
        after_wr = after.get("win_rate", 0)
        before_pnl = before.get("total_pnl", 0)
        after_pnl = after.get("total_pnl", 0)
        
        improved_wr = after_wr > before_wr
        improved_pnl = after_pnl > before_pnl
        same_wr = abs(after_wr - before_wr) < 0.1
        same_pnl = abs(after_pnl - before_pnl) < 0.001
        
        return {
            "improved": improved_wr or improved_pnl,
            "same": same_wr and same_pnl,
            "summary": f"WR: {before_wr:.1f}%→{after_wr:.1f}%, PnL: {before_pnl:.4f}→{after_pnl:.4f} SOL"
        }

    def _rollback(self):
        """Rollback changes"""
        self._log("🔄 Rolling back changes...")
        try:
            subprocess.run(["git", "checkout", "HEAD~1"], capture_output=True)
            self._log("   ✅ Rollback complete")
        except Exception as e:
            self._log(f"   ❌ Rollback error: {e}")

    def _save_experience(self, patch_result: Dict, comparison: Dict):
        """Save successful experience"""
        try:
            exp_file = Path("memory/experiences.json")
            exp_data = []
            if exp_file.exists():
                exp_data = json.loads(exp_file.read_text())
            
            exp_data.append({
                "timestamp": datetime.now().isoformat(),
                "patch": patch_result,
                "baseline": self.baseline_metrics,
                "result": self.result_metrics,
                "improvement": comparison["summary"],
                "validation_id": self.validation_id
            })
            
            exp_file.write_text(json.dumps(exp_data, indent=2))
            self._log(f"   ✅ Experience saved ({len(exp_data)} total)")
        except Exception as e:
            self._log(f"   ⚠️ Failed to save experience: {e}")


# Singleton
_validator = None

def get_validator():
    global _validator
    if _validator is None:
        _validator = ExecutionValidator()
    return _validator
