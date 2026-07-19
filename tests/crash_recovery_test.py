#!/usr/bin/env python3
"""
Crash Recovery Test — Simulate crash and verify recovery
"""

import sys
import time
import os
import signal
import subprocess
import json
from pathlib import Path

sys.path.insert(0, '/home/dibs/agentjw')

from sicuan.core.state_recovery import get_state_recovery
from sicuan.core.scheduler import get_scheduler, TaskQueue
from sicuan.core.execution_journal import get_execution_journal

class CrashRecoveryTest:
    def __init__(self):
        self.state = get_state_recovery()
        self.journal = get_execution_journal()
        self.task_queue = TaskQueue()
    
    def simulate_crash(self):
        """Simulate a crash by saving state and exiting"""
        print("[CRASH] Simulating crash...")
        self.state.save_state("_status", "running")
        self.state.save_state("_crash_simulated", True)
        print("[CRASH] State saved, exiting...")
        os._exit(1)
    
    def verify_recovery(self):
        """Verify recovery after crash"""
        print("[CRASH] Verifying recovery...")
        
        # Check state
        recovered = self.state.get_state("_recovered", False)
        crash_simulated = self.state.get_state("_crash_simulated", False)
        status = self.state.get_state("_status", "unknown")
        
        print(f"  Recovered: {recovered}")
        print(f"  Crash simulated: {crash_simulated}")
        print(f"  Status: {status}")
        
        # Check journal
        events = self.journal.get_events(limit=10)
        print(f"  Journal events: {len(events)}")
        
        # Check task queue
        stats = self.task_queue.get_stats()
        print(f"  Task queue: {stats}")
        
        return recovered and crash_simulated
    
    def run(self):
        print("=" * 60)
        print("💥 CRASH RECOVERY TEST")
        print("=" * 60)
        
        # Save some state
        print("\n📌 Saving pre-crash state...")
        self.state.save_state("workflow_1", {"step": 5, "status": "running"})
        self.state.save_state("workflow_2", {"step": 2, "status": "pending"})
        self.journal.log("pre_crash", {"message": "Before crash"})
        
        # Schedule some tasks
        scheduler = get_scheduler()
        scheduler.register_handler("test", lambda x: {"status": "ok"})
        for i in range(3):
            scheduler.schedule("test", {"id": i})
        
        print("\n📌 Simulating crash...")
        self.simulate_crash()
    
    def run_recovery(self):
        """Run recovery verification (called after process restart)"""
        print("\n" + "=" * 60)
        print("🔄 RECOVERY VERIFICATION")
        print("=" * 60)
        result = self.verify_recovery()
        
        if result:
            print("\n✅ RECOVERY SUCCESSFUL!")
        else:
            print("\n❌ RECOVERY FAILED!")
        
        return result

if __name__ == "__main__":
    import sys
    
    if "--recover" in sys.argv:
        test = CrashRecoveryTest()
        test.run_recovery()
    else:
        test = CrashRecoveryTest()
        test.run()
