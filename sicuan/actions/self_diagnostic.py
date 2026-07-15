"""
Self Diagnostic Action - Cek kesehatan AgentJW
"""
import os
import subprocess
from pathlib import Path


def execute(task: dict) -> dict:
    """Execute self-diagnostic"""
    try:
        lines = []
        lines.append("=== SELF-DIAGNOSTIC AGENTJW ===\n")
        
        # 1. Cek proses
        lines.append("1. PROSES:")
        processes = ["telegram_bot", "scheduler", "api_server"]
        for p in processes:
            result = subprocess.run(["pgrep", "-f", p], capture_output=True)
            status = "✅ RUNNING" if result.returncode == 0 else "❌ STOPPED"
            lines.append(f"   {p}: {status}")
        
        # 2. Cek error log
        lines.append("\n2. ERROR LOG (5 terakhir):")
        log_file = Path("/home/dibs/agentjw/logs/sicuan_telegram.log")
        if log_file.exists():
            errors = []
            with open(log_file) as f:
                for line in f:
                    if "ERROR" in line or "Exception" in line:
                        errors.append(line.strip())
            for e in errors[-5:]:
                lines.append(f"   {e[:100]}...")
        else:
            lines.append("   Log tidak ditemukan")
        
        # 3. Cek scheduler
        lines.append("\n3. SCHEDULER:")
        result = subprocess.run(["pgrep", "-f", "scheduler"], capture_output=True)
        lines.append(f"   Status: {'✅ RUNNING' if result.returncode == 0 else '❌ STOPPED'}")
        
        # 4. Cek .env
        lines.append("\n4. ENV CHECK:")
        env_keys = ["HELIUS_API_KEY", "OPENROUTER_API_KEY", "TELEGRAM_BOT_TOKEN"]
        for key in env_keys:
            value = os.getenv(key)
            status = "✅ ADA" if value else "❌ KOSONG"
            lines.append(f"   {key}: {status}")
        
        display = "\n".join(lines)
        return {
            "success": True,
            "display": display,
            "data": {"diagnostic": lines}
        }
    except Exception as e:
        return {
            "success": False,
            "display": f"❌ Self-diagnostic error: {str(e)}",
            "data": {"error": str(e)}
        }
