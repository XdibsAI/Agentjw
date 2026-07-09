"""
Workspace Runtime - Setiap workspace hidup sendiri
"""

import json
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class WorkspaceRuntime:
    """Runtime instance per workspace"""
    workspace_id: str
    config: Dict = field(default_factory=dict)
    memory: Dict = field(default_factory=dict)
    goals: list = field(default_factory=list)
    agents: list = field(default_factory=list)
    router: Optional[object] = None
    cost_tracker: Optional[object] = None
    scheduler: Optional[object] = None
    is_running: bool = False
    started_at: Optional[str] = None
    last_activity: Optional[str] = None


class RuntimeManager:
    """Manager untuk semua workspace runtime"""

    def __init__(self):
        self.runtimes: Dict[str, WorkspaceRuntime] = {}
        self.runtime_dir = Path("/home/dibs/agentjw/memory/runtimes")
        self.runtime_dir.mkdir(exist_ok=True)

    def load_or_create(self, workspace_id: str, config: Dict = None) -> WorkspaceRuntime:
        """Load atau create runtime untuk workspace"""
        if workspace_id in self.runtimes:
            return self.runtimes[workspace_id]
        
        runtime_file = self.runtime_dir / f"{workspace_id}.json"
        if runtime_file.exists():
            data = json.loads(runtime_file.read_text())
            runtime = WorkspaceRuntime(
                workspace_id=workspace_id,
                config=data.get("config", {}),
                memory=data.get("memory", {}),
                goals=data.get("goals", []),
                agents=data.get("agents", []),
                is_running=data.get("is_running", False),
                started_at=data.get("started_at"),
                last_activity=data.get("last_activity")
            )
        else:
            runtime = WorkspaceRuntime(
                workspace_id=workspace_id,
                config=config or {},
                is_running=False
            )
        
        self.runtimes[workspace_id] = runtime
        return runtime

    def start(self, workspace_id: str) -> bool:
        """Start workspace runtime"""
        runtime = self.load_or_create(workspace_id)
        if runtime.is_running:
            return True
        
        runtime.is_running = True
        runtime.started_at = datetime.now().isoformat()
        self._save(runtime)
        return True

    def stop(self, workspace_id: str) -> bool:
        """Stop workspace runtime"""
        if workspace_id not in self.runtimes:
            return False
        
        runtime = self.runtimes[workspace_id]
        runtime.is_running = False
        self._save(runtime)
        return True

    def _save(self, runtime: WorkspaceRuntime):
        """Save runtime state"""
        runtime_file = self.runtime_dir / f"{runtime.workspace_id}.json"
        data = {
            "workspace_id": runtime.workspace_id,
            "config": runtime.config,
            "memory": runtime.memory,
            "goals": runtime.goals,
            "agents": runtime.agents,
            "is_running": runtime.is_running,
            "started_at": runtime.started_at,
            "last_activity": datetime.now().isoformat()
        }
        runtime_file.write_text(json.dumps(data, indent=2))

    def update_activity(self, workspace_id: str):
        """Update last activity"""
        if workspace_id in self.runtimes:
            self.runtimes[workspace_id].last_activity = datetime.now().isoformat()
            self._save(self.runtimes[workspace_id])

    def get_status(self, workspace_id: str) -> Dict:
        """Get workspace runtime status"""
        runtime = self.load_or_create(workspace_id)
        return {
            "workspace_id": workspace_id,
            "is_running": runtime.is_running,
            "started_at": runtime.started_at,
            "last_activity": runtime.last_activity,
            "agents": len(runtime.agents),
            "config": runtime.config
        }


def get_runtime_manager():
    _manager = None
    if _manager is None:
        _manager = RuntimeManager()
    return _manager
