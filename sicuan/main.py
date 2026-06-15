"""
SiCuan — Si Paling Cuan
Autonomous AI partner bisnis
"""
import sys
import threading
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE.parent))

def start():
    print("""
╔══════════════════════════════════════════╗
║   💰  S I C U A N  — Si Paling Cuan    ║
║   Autonomous AI Partner Bisnis          ║
╚══════════════════════════════════════════╝
""")
    # Start scheduler di background thread
    from sicuan.scheduler import run_scheduler
    t = threading.Thread(target=run_scheduler, daemon=True)
    t.start()
    print("✓ SiCuan scheduler running (fully autonomous)")
    print("✓ Morning briefing: 05:00 WIB")
    print("✓ Trading monitor: every 30 minutes")
    print("✓ Content reminder: Kamis malam")

if __name__ == "__main__":
    start()
    # Keep alive
    import time
    while True:
        time.sleep(60)
