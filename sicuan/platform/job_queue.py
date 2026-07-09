"""
Job Queue - Async task processing
"""

import json
import threading
import time
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class Job:
    """Job object"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    workspace_id: str = ""
    type: str = ""
    data: Dict = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    progress: int = 0
    priority: int = 5


class JobQueue:
    """Job Queue - Async processing"""

    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.queue: List[str] = []  # Job IDs in order
        self.workers: Dict[str, Callable] = {}
        self.is_running = False
        self.queue_dir = Path("/home/dibs/agentjw/memory/jobs")
        self.queue_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()

    def register_worker(self, job_type: str, worker: Callable):
        """Register worker for job type"""
        self.workers[job_type] = worker

    def enqueue(self, workspace_id: str, job_type: str, data: Dict, priority: int = 5) -> str:
        """Add job to queue"""
        job = Job(
            workspace_id=workspace_id,
            type=job_type,
            data=data,
            priority=priority
        )
        
        with self._lock:
            self.jobs[job.id] = job
            self.queue.append(job.id)
            self._save(job)
        
        return job.id

    def process_next(self) -> bool:
        """Process next job in queue"""
        with self._lock:
            if not self.queue:
                return False
            
            job_id = self.queue.pop(0)
            job = self.jobs.get(job_id)
            if not job:
                return False
        
        return self._process_job(job)

    def _process_job(self, job: Job) -> bool:
        """Process single job"""
        job.status = "running"
        job.started_at = datetime.now().isoformat()
        self._save(job)
        
        try:
            worker = self.workers.get(job.type)
            if not worker:
                job.status = "failed"
                job.error = f"No worker for job type: {job.type}"
                self._save(job)
                return False
            
            result = worker(job.data)
            job.status = "completed"
            job.result = result
            job.completed_at = datetime.now().isoformat()
            job.progress = 100
            self._save(job)
            return True
            
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now().isoformat()
            self._save(job)
            return False

    def _save(self, job: Job):
        """Save job to disk"""
        job_file = self.queue_dir / f"{job.id}.json"
        data = {
            "id": job.id,
            "workspace_id": job.workspace_id,
            "type": job.type,
            "data": job.data,
            "status": job.status,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "result": job.result,
            "error": job.error,
            "progress": job.progress,
            "priority": job.priority
        }
        job_file.write_text(json.dumps(data, indent=2))

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        job_file = self.queue_dir / f"{job_id}.json"
        if job_file.exists():
            data = json.loads(job_file.read_text())
            job = Job(
                id=data["id"],
                workspace_id=data["workspace_id"],
                type=data["type"],
                data=data["data"],
                status=data["status"],
                created_at=data["created_at"],
                started_at=data.get("started_at"),
                completed_at=data.get("completed_at"),
                result=data.get("result"),
                error=data.get("error"),
                progress=data.get("progress", 0),
                priority=data.get("priority", 5)
            )
            return job
        return self.jobs.get(job_id)

    def get_jobs(self, workspace_id: str, status: str = None, limit: int = 20) -> List[Job]:
        """Get jobs for workspace"""
        jobs = []
        for job_id in self.queue[-limit:]:
            job = self.get_job(job_id)
            if job and job.workspace_id == workspace_id:
                if status is None or job.status == status:
                    jobs.append(job)
        return jobs[-limit:]


def get_job_queue():
    _queue = None
    if _queue is None:
        _queue = JobQueue()
    return _queue
