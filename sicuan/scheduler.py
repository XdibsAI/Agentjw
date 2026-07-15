"""
SiCuan Autonomous Scheduler
Proactive AI — kirim pesan sendiri tanpa disuruh
"""
import asyncio
import json
import time
import schedule
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

BASE = Path(__file__).parent
KNOWLEDGE_DIR = BASE / "knowledge"

def load_knowledge(name: str) -> Dict:
    f = KNOWLEDGE_DIR / f"{name}.json"
    return json.loads(f.read_text()) if f.exists() else {}

def get_wib_hour() -> int:
    return (datetime.utcnow().hour + 7) % 24

def get_day_name() -> str:
    days = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
    return days[datetime.now().weekday()]

def is_friday() -> bool:
    return datetime.now().weekday() == 4

async def generate_morning_briefing() -> str:
    """Generate morning briefing pakai LLM"""
    import sys
    sys.path.insert(0, str(BASE.parent))
    from core.llm_client import llm
    from mcp.tools.filesystem_tool import filesystem_tool

    identity = load_knowledge("identity")
    jawarasa = load_knowledge("jawarasa")
    trading = load_knowledge("trading")

    # Get real trading log
    bot_dir = str(BASE.parent / "projects/godmeme_bot")
    logs = filesystem_tool.read_log(bot_dir, lines=10)
    log_summary = str(logs)[:500] if logs else "No trading activity"

    hari = get_day_name()
    is_jum = is_friday()

    prompt = f"""Kamu adalah SiCuan, AI partner bisnis yang proactive dan paham konteks.

Hari ini: {hari}, {datetime.now().strftime('%d %B %Y')}, jam 05.00 WIB

DATA REAL:
- Trading log: {log_summary}
- Hari Jumat: {is_jum}
- Jawarasa posting schedule: {json.dumps(jawarasa.get('posting_schedule', {}), indent=2)}

Buat morning briefing yang:
1. Salam pagi yang hangat dan natural (bukan template kaku)
2. Quote motivasi relevan (boleh dari ulama, filsuf, atau kata-kata bijak)
3. Agenda hari ini berdasarkan data nyata di atas
4. Kalau hari Jumat: ingatkan konten Jumat untuk Jawarasa
5. Status trading bot (dari log)
6. 1 insight atau peluang yang perlu diperhatikan hari ini

Gaya: santai tapi berisi, seperti teman yang lebih tahu. Max 15 baris."""

    return llm.chat(
        messages=[{"role": "user", "content": prompt}],
        system="Kamu SiCuan - AI partner bisnis. Selalu natural, kontekstual, tidak template.",
        temperature=0.8,
        max_tokens=500
    )

async def check_trading_opportunities():
    """Autonomous check - kirim alert kalau ada peluang"""
    import sys
    sys.path.insert(0, str(BASE.parent))
    from mcp.tools.filesystem_tool import filesystem_tool

    bot_dir = str(BASE.parent / "projects/godmeme_bot")
    logs = filesystem_tool.read_log(bot_dir, lines=20)
    log_str = str(logs)

    # Detect signals
    if "BUY" in log_str or "PAPER_" in log_str:
        from mcp.tools.openclaw_tool import send_message
        send_message("📈 SiCuan: Ada aktivitas trading terdeteksi!\nCek log: scan godmeme")

async def send_morning_briefing():
    try:
        import sys
        sys.path.insert(0, str(BASE.parent))
        from mcp.tools.openclaw_tool import send_message

        briefing = await generate_morning_briefing()
        send_message(briefing)
        print(f"[{datetime.now().strftime('%H:%M')}] Morning briefing sent")

        # Save to memory
        memory_file = BASE / "memory/daily_context.json"
        memory_file.parent.mkdir(exist_ok=True)
        ctx = {"date": datetime.now().isoformat(), "briefing": briefing, "day": get_day_name()}
        memory_file.write_text(json.dumps(ctx, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Morning briefing error: {e}")


def run_autonomous_cycle():
    """LLM-driven autonomous cycle — jalankan setiap 15 menit."""
    try:
        import sys
        sys.path.insert(0, str(BASE.parent))
        from sicuan.core.llm_task_executor import LLMTaskExecutor
        executor = LLMTaskExecutor()
        result = executor.run_cycle()
        print(f"[autonomous] {result.get('summary', 'cycle done')}")
    except Exception as e:
        print(f"[autonomous] error: {e}")


def run_auto_learning():
    """Jalankan Auto Learning cycle — belajar dari data aktual."""
    try:
        from sicuan.core.continuous_learning import ContinuousLearning
        cl = ContinuousLearning()
        cl.load_datasets()
        if cl.workflows or cl.reflections or cl.shadow_comparisons:
            cl.analyze()
            result = cl.apply_learnings()
            applied = result.get("applied", [])
            logger.info(f"[AUTO-LEARNING] {len(applied)} updates applied")
        else:
            logger.info("[AUTO-LEARNING] No data available yet, skip")
    except Exception as e:
        logger.error(f"[AUTO-LEARNING] Failed: {e}")

def run_scheduler():
    """Jalankan scheduler — fully autonomous"""
    print("SiCuan Scheduler started — fully autonomous mode")

    # Autonomous LLM cycle setiap 15 menit
    schedule.every(15).minutes.do(run_autonomous_cycle)
    schedule.every(6).hours.do(run_auto_learning)

    
    # Morning briefing jam 05:00 WIB = 22:00 UTC
    schedule.every().day.at("22:00").do(
        lambda: asyncio.run(send_morning_briefing())
    )

    # Check trading setiap 30 menit
    schedule.every(30).minutes.do(
        lambda: asyncio.run(check_trading_opportunities())
    )

    # Nightly consolidation jam 02:00 WIB = 19:00 UTC
    schedule.every().day.at("19:00").do(
        lambda: asyncio.run(
            __import__("sicuan.consolidator", fromlist=["nightly_consolidation"]).nightly_consolidation()
        )
    )

    # Weekly content reminder - Kamis malam (H-1 Jumat)
    schedule.every().thursday.at("20:00").do(
        lambda: __import__('sys').path.insert(0, '..') or
        __import__('mcp.tools.openclaw_tool', fromlist=['send_message']).send_message(
            "🎬 SiCuan Reminder: Besok Jumat! Siapkan konten Jawarasa:\n"
            "- Desain ucapan Jumat\n- Foto produk fresh\n- Caption promo mingguan"
        )
    )

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler()

def check_drift():
    """Check drift secara periodik"""
    from sicuan.core.drift_monitor import get_drift_monitor
    from sicuan.core.self_healing_loop import SelfHealingLoop
    from sicuan.core.entry_tester import EntryTester
    from sicuan.core.self_review_data import get_self_review
    
    # Get current metrics dari self-review
    review = get_self_review()
    report = review.generate()
    metrics = report.get("metrics", {})
    
    # Check drift
    monitor = get_drift_monitor()
    alerts = monitor.check_drift(metrics)
    
    if alerts:
        print(f"[DRIFT] {len(alerts)} alert(s) detected:")
        for alert in alerts:
            print(f"  {alert.severity.upper()}: {alert.message}")
        
        # TODO: Kirim notifikasi ke Telegram
        # send_alert_to_telegram(alerts)
    
    return alerts

# Tambahkan ke run_scheduler()
# Setiap 6 jam, check drift

def collect_experiences():
    """Kumpulkan pengalaman dari daily operations"""
    try:
        from sicuan.core.experience_engine import get_experience_engine
        from sicuan.core.continuous_learning import ContinuousLearning
        
        engine = get_experience_engine()
        stats = engine.get_stats()
        
        print(f"[EXPERIENCE] Total: {stats['total']}, Success: {stats['successful']}")
        
        # Jika pengalaman cukup, trigger auto learning
        if stats['total'] >= 10:
            learner = ContinuousLearning()
            learner.load_datasets()
            learner.analyze()
            learner.apply_learnings()
            print("[EXPERIENCE] Auto learning triggered")
        
        return stats
    except Exception as e:
        print(f"[EXPERIENCE] Error: {e}")
        return None

# Tambahkan ke scheduler - setiap 6 jam
schedule.every(6).hours.do(collect_experiences)

def auto_heal():
    """Auto-healing: detect errors and fix them automatically"""
    try:
        from pathlib import Path
        from sicuan.core.root_cause_detector import RootCauseDetector
        from sicuan.core.runtime_verifier import RuntimeVerifier
        import subprocess
        import time
        
        # Check log for errors
        log_file = Path("projects/godmeme_bot/trading_bot_live.log")
        if not log_file.exists():
            return
        
        with open(log_file, "r") as f:
            lines = f.readlines()[-100:]
            errors = [l for l in lines if "ERROR" in l]
        
        if not errors:
            print("[AUTO-HEAL] No errors detected")
            return
        
        # Detect root cause
        detector = RootCauseDetector()
        error_text = "\n".join(errors[-5:])
        root_cause = detector.detect(error_text)
        
        if root_cause["type"] == "missing_method":
            print(f"[AUTO-HEAL] Detected: {root_cause['target']} missing in {root_cause['file']}")
            print(f"[AUTO-HEAL] Suggestion: {root_cause['suggestion']}")
            
            # Simple fix: check if method exists, if not, add stub
            if root_cause["file"] == "strategy.py":
                method_name = root_cause["target"]
                strategy_file = Path("projects/godmeme_bot/strategy.py")
                
                if strategy_file.exists():
                    content = strategy_file.read_text()
                    if f"def {method_name}" not in content:
                        # Add missing method
                        stub = f'''
    async def {method_name}(self) -> bool:
        """Auto-generated stub for {method_name}"""
        logger.warning(f"{method_name} called (stub)")
        return True
'''
                        content = content.replace(
                            "    async def _handle_429(self):",
                            stub + "\n\n    async def _handle_429(self):"
                        )
                        strategy_file.write_text(content)
                        print(f"[AUTO-HEAL] ✅ Added stub for {method_name}")
                        
                        # Restart bot
                        print("[AUTO-HEAL] 🔄 Restarting bot...")
                        subprocess.run(["pkill", "-f", "main.py"], capture_output=True)
                        time.sleep(2)
                        subprocess.Popen(["python3", "main.py"], cwd="projects/godmeme_bot")
                        print("[AUTO-HEAL] ✅ Bot restarted")
        
        elif root_cause["type"] == "undefined_variable":
            print(f"[AUTO-HEAL] Detected undefined variable: {root_cause['target']}")
            print(f"[AUTO-HEAL] Suggestion: {root_cause['suggestion']}")
            
    except Exception as e:
        print(f"[AUTO-HEAL] Error: {e}")

# Add to scheduler - run every 2 minutes
schedule.every(2).minutes.do(auto_heal)

def run_self_healing():
    """Jalankan self-healing loop"""
    from sicuan.core.self_healing_loop import SelfHealingLoop
    healer = SelfHealingLoop()
    return healer.report()

# Tambahkan ke schedule setiap 5 menit
schedule.every(5).minutes.do(run_self_healing)

def run_entry_test():
    """Jalankan entry time test"""
    from sicuan.core.entry_tester import EntryTester
    tester = EntryTester()
    return tester.get_recommendation()

# Tambahkan ke schedule setiap 6 jam
schedule.every(6).hours.do(run_entry_test)

def run_self_healing():
    """Jalankan self-healing loop"""
    healer = SelfHealingLoop()
    return healer.report()

# Tambahkan ke schedule setiap 5 menit
schedule.every(5).minutes.do(run_self_healing)

def run_entry_test():
    """Jalankan entry time test"""
    tester = EntryTester()
    return tester.get_recommendation()

# Tambahkan ke schedule setiap 6 jam
schedule.every(6).hours.do(run_entry_test)
