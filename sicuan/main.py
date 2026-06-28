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

import signal
import sys

def graceful_shutdown(signum, frame):
    """Handle SIGINT dan SIGTERM dengan graceful shutdown"""
    logger.info("Received shutdown signal. Cleaning up...")
    # Save state
    if hasattr(brain, 'executor'):
        brain.executor.clear_queue()
    # Save runtime state
    if hasattr(brain, 'runtime_bus'):
        brain.runtime_bus.clear()
    logger.info("Shutdown complete.")
    sys.exit(0)

signal.signal(signal.SIGINT, graceful_shutdown)
signal.signal(signal.SIGTERM, graceful_shutdown)
