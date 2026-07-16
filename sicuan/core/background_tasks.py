"""
Background Tasks — Run slow operations in background
"""
import threading
import uuid
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class BackgroundTask:
    id: str
    name: str
    status: str  # pending, running, done, failed
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: int = 0  # 0-100
    message: str = ""


class BackgroundTaskManager:
    """Kelola task yang berjalan di background"""

    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self._lock = threading.Lock()

    def create(self, name: str, func: Callable, *args, **kwargs) -> str:
        """Buat task baru dan jalankan di background"""
        task_id = f"bg_{uuid.uuid4().hex[:8]}"
        task = BackgroundTask(id=task_id, name=name, status="pending")
        
        with self._lock:
            self.tasks[task_id] = task
        
        # Jalankan di thread terpisah
        thread = threading.Thread(
            target=self._run_task,
            args=(task_id, func, args, kwargs),
            daemon=True
        )
        thread.start()
        
        return task_id

    def _run_task(self, task_id: str, func: Callable, args: tuple, kwargs: dict):
        """Jalankan task di background"""
        with self._lock:
            task = self.tasks.get(task_id)
            if task:
                task.status = "running"
                task.started_at = datetime.now().isoformat()
                task.message = "Menjalankan task..."
        
        try:
            result = func(*args, **kwargs)
            with self._lock:
                task = self.tasks.get(task_id)
                if task:
                    task.status = "done"
                    task.result = str(result) if result else "Selesai"
                    task.completed_at = datetime.now().isoformat()
                    task.progress = 100
                    task.message = "Task selesai"
        except Exception as e:
            with self._lock:
                task = self.tasks.get(task_id)
                if task:
                    task.status = "failed"
                    task.error = str(e)
                    task.completed_at = datetime.now().isoformat()
                    task.message = f"Gagal: {str(e)[:100]}"

    def get_status(self, task_id: str) -> Optional[Dict]:
        """Dapatkan status task"""
        with self._lock:
            task = self.tasks.get(task_id)
            if not task:
                return None
            return {
                "id": task.id,
                "name": task.name,
                "status": task.status,
                "progress": task.progress,
                "message": task.message,
                "result": task.result,
                "error": task.error,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at
            }

    def list_running(self) -> List[Dict]:
        """List semua task yang sedang running"""
        with self._lock:
            return [
                self.get_status(task_id)
                for task_id, task in self.tasks.items()
                if task.status in ("pending", "running")
            ]

    def list_all(self) -> List[Dict]:
        """List semua task"""
        with self._lock:
            return [self.get_status(task_id) for task_id in self.tasks]

    def wait(self, task_id: str, timeout: int = 300) -> Optional[Dict]:
        """Tunggu task selesai"""
        import time
        start = time.time()
        while time.time() - start < timeout:
            status = self.get_status(task_id)
            if status and status["status"] in ("done", "failed"):
                return status
            time.sleep(1)
        return self.get_status(task_id)


_manager = None


def get_background_task_manager() -> BackgroundTaskManager:
    global _manager
    if _manager is None:
        _manager = BackgroundTaskManager()
    return _manager
