"""
Scheduler — Background worker dengan task queue persisten
"""

import time
import json
import threading
import queue
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class Task:
    id: str
    name: str
    payload: Dict[str, Any]
    status: str = "pending"  # pending, running, completed, failed
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3

class TaskQueue:
    """Persistent task queue"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("memory/tasks.json")
        self.tasks: Dict[str, Task] = {}
        self._load()
    
    def _load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for item in data:
                    task = Task(**item)
                    self.tasks[task.id] = task
                print(f"[TASK] Loaded {len(self.tasks)} tasks")
            except:
                pass
    
    def _save(self):
        data = [vars(t) for t in self.tasks.values()]
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def add(self, name: str, payload: Dict) -> str:
        task = Task(id=str(uuid.uuid4())[:8], name=name, payload=payload)
        self.tasks[task.id] = task
        self._save()
        return task.id
    
    def get_next(self) -> Optional[Task]:
        for task in self.tasks.values():
            if task.status == "pending":
                return task
        return None
    
    def start_task(self, task_id: str):
        if task_id in self.tasks:
            self.tasks[task_id].status = "running"
            self.tasks[task_id].started_at = time.time()
            self._save()
    
    def complete_task(self, task_id: str, error: str = None):
        if task_id in self.tasks:
            self.tasks[task_id].status = "completed" if not error else "failed"
            self.tasks[task_id].completed_at = time.time()
            self.tasks[task_id].error = error
            self._save()
    
    def get_pending(self) -> int:
        return sum(1 for t in self.tasks.values() if t.status == "pending")
    
    def get_stats(self) -> Dict:
        stats = {"total": len(self.tasks), "pending": 0, "running": 0, "completed": 0, "failed": 0}
        for t in self.tasks.values():
            stats[t.status] = stats.get(t.status, 0) + 1
        return stats

class Scheduler:
    """Background worker dengan task queue"""
    
    def __init__(self):
        self.queue = TaskQueue()
        self.running = False
        self.thread = None
        self.handlers: Dict[str, Callable] = {}
    
    def register_handler(self, name: str, handler: Callable):
        self.handlers[name] = handler
        print(f"[SCHEDULER] Registered handler: {name}")
    
    def schedule(self, name: str, payload: Dict) -> str:
        return self.queue.add(name, payload)
    
    def _worker_loop(self):
        print("[SCHEDULER] Worker started")
        while self.running:
            task = self.queue.get_next()
            if task:
                print(f"[SCHEDULER] Processing task: {task.id} ({task.name})")
                self.queue.start_task(task.id)
                
                if task.name in self.handlers:
                    try:
                        result = self.handlers[task.name](task.payload)
                        self.queue.complete_task(task.id)
                        print(f"[SCHEDULER] Task {task.id} completed")
                    except Exception as e:
                        self.queue.complete_task(task.id, str(e))
                        print(f"[SCHEDULER] Task {task.id} failed: {e}")
                else:
                    self.queue.complete_task(task.id, f"Handler '{task.name}' not found")
            else:
                time.sleep(1)
    
    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.thread.start()
        print("[SCHEDULER] Started")
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("[SCHEDULER] Stopped")
    
    def get_stats(self) -> Dict:
        return self.queue.get_stats()

# Singleton
_scheduler = None

def get_scheduler() -> Scheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler
