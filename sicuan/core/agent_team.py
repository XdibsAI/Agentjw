"""
Agent Teams + Autonomous Agents + Worktree Isolation
Terinspirasi dari Claude Code: coordinator mode, auto-claim, worktree isolation
"""
import uuid
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field


# ─── WORKTREE ISOLATION ──────────────────────────────────────────────
@dataclass
class Worktree:
    """Setiap agent punya workspace sendiri"""
    id: str
    name: str
    path: Path
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    active_agent: Optional[str] = None
    tasks: List[str] = field(default_factory=list)


class WorktreeManager:
    """Kelola worktree per agent"""

    def __init__(self, base_path: Path = Path("/home/dibs/agentjw/memory/worktrees")):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.worktrees: Dict[str, Worktree] = {}
        self._load()

    def _load(self):
        index_file = self.base_path / "index.json"
        if index_file.exists():
            try:
                data = json.loads(index_file.read_text())
                for wt_data in data.get("worktrees", []):
                    wt = Worktree(
                        id=wt_data["id"],
                        name=wt_data["name"],
                        path=Path(wt_data["path"]),
                        created_at=wt_data.get("created_at", datetime.now().isoformat()),
                        active_agent=wt_data.get("active_agent"),
                        tasks=wt_data.get("tasks", [])
                    )
                    self.worktrees[wt.id] = wt
            except:
                pass

    def _save(self):
        data = {
            "worktrees": [
                {
                    "id": wt.id,
                    "name": wt.name,
                    "path": str(wt.path),
                    "created_at": wt.created_at,
                    "active_agent": wt.active_agent,
                    "tasks": wt.tasks
                }
                for wt in self.worktrees.values()
            ]
        }
        (self.base_path / "index.json").write_text(json.dumps(data, indent=2))

    def create(self, name: str) -> Worktree:
        """Buat worktree baru"""
        wt_id = f"wt_{uuid.uuid4().hex[:8]}"
        wt_path = self.base_path / wt_id
        wt_path.mkdir(parents=True, exist_ok=True)

        wt = Worktree(
            id=wt_id,
            name=name,
            path=wt_path
        )
        self.worktrees[wt_id] = wt
        self._save()
        return wt

    def get(self, wt_id: str) -> Optional[Worktree]:
        return self.worktrees.get(wt_id)

    def assign_agent(self, wt_id: str, agent_id: str):
        wt = self.get(wt_id)
        if wt:
            wt.active_agent = agent_id
            self._save()

    def add_task(self, wt_id: str, task_id: str):
        wt = self.get(wt_id)
        if wt:
            wt.tasks.append(task_id)
            self._save()


# ─── AGENT TEAM ──────────────────────────────────────────────────────
@dataclass
class TeamAgent:
    """Agent dalam sebuah tim"""
    id: str
    name: str
    role: str  # lead, specialist, executor, reviewer
    status: str = "idle"  # idle, working, blocked, done
    worktree_id: Optional[str] = None
    task: Optional[str] = None
    result: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class AgentTeam:
    """Tim agent yang bekerja bersama"""

    def __init__(self, name: str, goal: str):
        self.id = f"team_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.goal = goal
        self.agents: Dict[str, TeamAgent] = {}
        self.lead_id: Optional[str] = None
        self.status = "forming"  # forming, active, done, failed
        self.created_at = datetime.now().isoformat()
        self.completed_at: Optional[str] = None

    def add_agent(self, name: str, role: str) -> str:
        """Tambahkan agent ke tim"""
        agent_id = f"agent_{uuid.uuid4().hex[:8]}"
        agent = TeamAgent(
            id=agent_id,
            name=name,
            role=role
        )
        self.agents[agent_id] = agent
        if role == "lead":
            self.lead_id = agent_id
        return agent_id

    def assign_task(self, agent_id: str, task: str, worktree_id: str = None):
        """Assign task ke agent"""
        agent = self.agents.get(agent_id)
        if agent:
            agent.task = task
            agent.status = "working"
            agent.worktree_id = worktree_id

    def complete_task(self, agent_id: str, result: str):
        """Agent selesai mengerjakan task"""
        agent = self.agents.get(agent_id)
        if agent:
            agent.status = "done"
            agent.result = result

    def is_complete(self) -> bool:
        """Cek apakah semua agent selesai"""
        return all(a.status == "done" for a in self.agents.values())

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "goal": self.goal,
            "status": self.status,
            "agents": [
                {
                    "id": a.id,
                    "name": a.name,
                    "role": a.role,
                    "status": a.status,
                    "task": a.task,
                    "result": a.result
                }
                for a in self.agents.values()
            ],
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }


# ─── AUTONOMOUS AGENT ──────────────────────────────────────────────
class AutonomousAgent:
    """Agent yang bisa bekerja sendiri tanpa diawasi"""

    def __init__(self, name: str, brain, worktree: Worktree = None):
        self.id = f"auto_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.brain = brain
        self.worktree = worktree
        self.status = "idle"  # idle, working, done, failed
        self.task = None
        self.result = None
        self.thread = None
        self._stop = False

    def start(self, task: str):
        """Mulai bekerja autonomous"""
        self.task = task
        self.status = "working"
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        """Jalankan task di background"""
        try:
            # Gunakan brain dengan context terpisah
            if self.worktree:
                # Simpan context lama
                old_context = getattr(self.brain, '_context', [])
                # Set worktree sebagai context
                self.brain._context = {
                    "worktree": str(self.worktree.path),
                    "agent": self.name
                }

            result = self.brain.think_and_respond(
                self.task,
                chat_history=[],
                force_model="deepseek/deepseek-chat"
            )

            self.result = result
            self.status = "done"

            # Restore context
            if self.worktree:
                self.brain._context = old_context

        except Exception as e:
            self.result = {"error": str(e)}
            self.status = "failed"

    def get_status(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "task": self.task,
            "result": self.result,
            "worktree": str(self.worktree.path) if self.worktree else None
        }

    def stop(self):
        self._stop = True


class AutonomousAgentManager:
    """Manager untuk autonomous agents"""

    def __init__(self):
        self.agents: Dict[str, AutonomousAgent] = {}
        self.teams: Dict[str, AgentTeam] = {}
        self.worktrees = WorktreeManager()

    def create_agent(self, name: str, brain) -> AutonomousAgent:
        """Buat autonomous agent baru"""
        # Buat worktree untuk agent
        wt = self.worktrees.create(f"workspace_{name}")
        agent = AutonomousAgent(name, brain, wt)
        self.agents[agent.id] = agent
        return agent

    def create_team(self, name: str, goal: str) -> AgentTeam:
        """Buat team baru"""
        team = AgentTeam(name, goal)
        self.teams[team.id] = team
        return team

    def assign_to_team(self, team_id: str, agent_id: str, role: str):
        """Assign autonomous agent ke team"""
        team = self.teams.get(team_id)
        agent = self.agents.get(agent_id)
        if team and agent:
            team.add_agent(agent.name, role)
            # Buat worktree untuk agent di team
            wt = self.worktrees.create(f"team_{team.name}_{agent.name}")
            agent.worktree = wt
            self.worktrees.assign_agent(wt.id, agent.id)

    def get_team_status(self, team_id: str) -> Dict:
        team = self.teams.get(team_id)
        return team.to_dict() if team else None

    def list_teams(self) -> List[str]:
        return list(self.teams.keys())


_manager = None


def get_agent_team_manager() -> AutonomousAgentManager:
    global _manager
    if _manager is None:
        _manager = AutonomousAgentManager()
    return _manager
