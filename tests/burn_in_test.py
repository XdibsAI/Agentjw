#!/usr/bin/env python3
"""
Burn-in Test — 24-72 jam continuous operation
"""

import sys
import time
import random
import threading
from datetime import datetime

sys.path.insert(0, '/home/dibs/agentjw')

from sicuan.core.scheduler import get_scheduler
from sicuan.core.execution_journal import get_execution_journal
from sicuan.core.observability import get_observability, ExecutionRecord
from sicuan.core.state_recovery import get_state_recovery

class BurnInTest:
    def __init__(self, duration_hours: int = 24):
        self.duration = duration_hours * 3600
        self.start_time = time.time()
        self.task_count = 0
        self.failed_count = 0
        
        # Setup components
        self.scheduler = get_scheduler()
        self.journal = get_execution_journal()
        self.observability = get_observability()
        self.state = get_state_recovery()
        
        # Register handlers
        self.scheduler.register_handler("burn_in_task", self._handle_task)
        self.scheduler.register_handler("chaos_task", self._handle_chaos)
        
        # Start scheduler
        self.scheduler.start()
        print(f"[BURN-IN] Started {duration_hours}h test")
    
    def _handle_task(self, payload):
        """Normal task handler"""
        task_id = payload.get("id")
        duration = random.uniform(0.1, 2.0)
        time.sleep(duration)
        return {"task_id": task_id, "duration": duration}
    
    def _handle_chaos(self, payload):
        """Chaos task — randomly fails"""
        if random.random() < 0.1:  # 10% failure rate
            raise Exception("Random chaos failure!")
        return self._handle_task(payload)
    
    def run(self):
        """Main burn-in loop"""
        print(f"[BURN-IN] Running for {self.duration/3600:.0f} hours...")
        
        while time.time() - self.start_time < self.duration:
            # Schedule tasks
            num_tasks = random.randint(1, 5)
            for i in range(num_tasks):
                task_type = random.choice(["burn_in_task", "chaos_task"])
                task_id = f"burn_{int(time.time())}_{i}"
                self.scheduler.schedule(task_type, {"id": task_id})
                self.task_count += 1
            
            # Record observability
            record = ExecutionRecord(
                task_id=f"burn_{int(time.time())}",
                capability="scheduler",
                provider="native",
                success=random.random() > 0.05,
                latency=random.uniform(0.1, 1.0),
                cost=0.0,
                retries=random.randint(0, 2)
            )
            self.observability.record(record)
            
            # Log to journal
            self.journal.log("burn_in", {
                "tasks_scheduled": num_tasks,
                "total_tasks": self.task_count,
                "uptime": time.time() - self.start_time
            })
            
            # Print progress every 5 minutes
            elapsed = time.time() - self.start_time
            if int(elapsed) % 300 < 1:  # Every 5 minutes
                self._print_status()
            
            time.sleep(1)
        
        self._print_final()
    
    def _print_status(self):
        elapsed = time.time() - self.start_time
        stats = self.scheduler.get_stats()
        print(f"\n[BURN-IN] {elapsed/3600:.1f}h | Tasks: {self.task_count} | Stats: {stats}")
    
    def _print_final(self):
        print("\n" + "=" * 60)
        print("🔥 BURN-IN TEST COMPLETE")
        print("=" * 60)
        print(f"  Duration: {(time.time() - self.start_time)/3600:.1f}h")
        print(f"  Total Tasks: {self.task_count}")
        print(f"  Scheduler Stats: {self.scheduler.get_stats()}")
        print(f"  Journal Stats: {self.journal.get_stats()}")
        print(f"  Observability: {self.observability.get_stats(24)}")
        print("=" * 60)

if __name__ == "__main__":
    # 1 hour test by default (24 hours for real test)
    duration = 1  # hours
    test = BurnInTest(duration)
    test.run()
