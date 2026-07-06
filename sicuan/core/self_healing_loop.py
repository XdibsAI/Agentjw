"""
Self-Healing Loop — Deteksi, Diagnose, Perbaiki, Laporkan
"""

import subprocess
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class SelfHealingLoop:
    """Loop otomatis untuk deteksi dan perbaikan error"""

    def __init__(self):
        self.log_file = Path("projects/godmeme_bot/trading_bot_live.log")
        self.last_check = None
        self.healing_history = []

    def check_bot(self) -> Dict:
        """Cek status bot"""
        result = {
            "running": False,
            "pid": None,
            "last_error": None,
            "uptime": None
        }
        
        # Cek proses
        try:
            proc = subprocess.run(
                ["pgrep", "-f", "main.py"],
                capture_output=True,
                timeout=5
            )
            if proc.returncode == 0:
                result["running"] = True
                result["pid"] = proc.stdout.decode().strip()
        except:
            pass
        
        # Cek log terakhir
        if self.log_file.exists():
            try:
                lines = self.log_file.read_text().splitlines()[-20:]
                errors = [l for l in lines if "ERROR" in l or "Exception" in l]
                if errors:
                    result["last_error"] = errors[-1]
            except:
                pass
        
        return result

    def diagnose(self, status: Dict) -> str:
        """Diagnose masalah"""
        if status["running"]:
            if status["last_error"]:
                return "WARNING: Bot running but has errors"
            return "OK: Bot running normally"
        
        if not status["running"]:
            if status["last_error"]:
                return f"CRITICAL: Bot stopped. Last error: {status['last_error'][:100]}"
            return "WARNING: Bot stopped (no error found)"

    def heal(self, diagnosis: str) -> bool:
        """Perbaiki masalah"""
        if "CRITICAL" in diagnosis:
            print("[HEAL] 🔄 Restarting bot...")
            try:
                subprocess.run(["pkill", "-f", "main.py"], capture_output=True)
                time.sleep(2)
                subprocess.Popen(
                    ["python3", "main.py"],
                    cwd="projects/godmeme_bot"
                )
                time.sleep(3)
                return True
            except Exception as e:
                print(f"[HEAL] ❌ Failed to restart: {e}")
                return False
        
        if "WARNING" in diagnosis:
            print("[HEAL] ⚠️ Logging warning...")
            # Simpan untuk analisis
            return True
        
        return False

    def report(self) -> str:
        """Laporan status dan healing"""
        status = self.check_bot()
        diagnosis = self.diagnose(status)
        
        lines = []
        lines.append("🔄 **Self-Healing Report**")
        lines.append("")
        lines.append(f"📊 Bot Running: {'✅' if status['running'] else '❌'}")
        lines.append(f"📝 Diagnosis: {diagnosis}")
        
        if status.get("pid"):
            lines.append(f"🆔 PID: {status['pid']}")
        
        if status.get("last_error"):
            lines.append(f"⚠️ Last Error: {status['last_error'][:200]}")
        
        return "\n".join(lines)

    def loop(self):
        """Main loop — jalankan setiap 5 menit"""
        while True:
            status = self.check_bot()
            diagnosis = self.diagnose(status)
            
            if "CRITICAL" in diagnosis or "WARNING" in diagnosis:
                self.heal(diagnosis)
            
            time.sleep(300)  # 5 menit
