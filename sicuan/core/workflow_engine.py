"""
Workflow Engine — Orkestrasi pekerjaan kompleks antar agent
"""
from typing import Dict, List, Optional, Callable
from datetime import datetime
import uuid


class WorkflowStep:
    def __init__(self, name: str, agent: str, action: str, params: Dict = None):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.agent = agent
        self.action = action
        self.params = params or {}
        self.status = "pending"  # pending, running, done, failed
        self.result = None
        self.error = None
        self.dependencies = []
        self.started_at = None
        self.completed_at = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "agent": self.agent,
            "action": self.action,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "dependencies": self.dependencies
        }


class Workflow:
    def __init__(self, name: str, goal: str):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.goal = goal
        self.steps: List[WorkflowStep] = []
        self.status = "pending"
        self.created_at = datetime.now().isoformat()
        self.completed_at = None
        self.current_step_index = 0

    def add_step(self, name: str, agent: str, action: str, params: Dict = None, dependencies: List[str] = None) -> WorkflowStep:
        step = WorkflowStep(name, agent, action, params)
        if dependencies:
            step.dependencies = dependencies
        self.steps.append(step)
        return step

    def get_next_step(self) -> Optional[WorkflowStep]:
        for step in self.steps:
            if step.status == "pending":
                # Cek dependencies
                all_done = all(
                    any(s.id == dep_id and s.status == "done" for s in self.steps)
                    for dep_id in step.dependencies
                )
                if all_done:
                    return step
        return None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "goal": self.goal,
            "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }


class WorkflowEngine:
    """Orkestrasi multi-step workflows"""

    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.agent_map = {}

    def register_agent(self, name: str, executor: Callable):
        """Daftarkan agent yang bisa dipanggil"""
        self.agent_map[name] = executor

    def create_workflow(self, name: str, goal: str) -> Workflow:
        workflow = Workflow(name, goal)
        self.workflows[workflow.id] = workflow
        return workflow

    def execute(self, workflow_id: str) -> Dict:
        """Eksekusi workflow step by step"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"error": "Workflow not found"}

        workflow.status = "running"
        
        while True:
            step = workflow.get_next_step()
            if not step:
                break
            
            step.status = "running"
            step.started_at = datetime.now().isoformat()
            
            try:
                if step.agent in self.agent_map:
                    result = self.agent_map[step.agent](step.action, step.params)
                    step.result = result
                    step.status = "done"
                else:
                    step.status = "failed"
                    step.error = f"Agent {step.agent} not registered"
            except Exception as e:
                step.status = "failed"
                step.error = str(e)
            
            step.completed_at = datetime.now().isoformat()

        all_done = all(s.status == "done" for s in workflow.steps)
        has_failed = any(s.status == "failed" for s in workflow.steps)
        
        if has_failed:
            workflow.status = "failed"
        elif all_done:
            workflow.status = "done"
        else:
            workflow.status = "partial"
        
        workflow.completed_at = datetime.now().isoformat()
        return workflow.to_dict()

    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        wf = self.workflows.get(workflow_id)
        return wf.to_dict() if wf else None

    def list_workflows(self) -> List[str]:
        return list(self.workflows.keys())


_engine = None


def get_workflow_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine
