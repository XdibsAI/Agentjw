"""
Base Agent — Base class untuk semua agent
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class Agent(ABC):
    """Base class untuk semua agent"""

    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.status = "idle"  # idle, busy, done, error
        self.last_task = None
        self.last_result = None
        self.created_at = datetime.now().isoformat()

    @abstractmethod
    def execute(self, task: Dict) -> Dict:
        """Eksekusi task"""
        pass

    @abstractmethod
    def get_capabilities(self) -> list:
        """Dapatkan daftar capabilities"""
        pass

    def get_status(self) -> Dict:
        """Dapatkan status agent"""
        return {
            "name": self.name,
            "role": self.role,
            "status": self.status,
            "last_task": self.last_task,
            "last_result": self.last_result
        }

    def set_status(self, status: str):
        """Set status agent"""
        self.status = status


class AgentOrchestrator:
    """Orchestrator untuk multi-agent"""

    def __init__(self):
        self.agents = {}
        self.task_history = []

    def register(self, agent: Agent):
        """Register agent"""
        self.agents[agent.name] = agent
        print(f"[AGENT] Registered: {agent.name} ({agent.role})")

    def get_agent(self, name: str) -> Optional[Agent]:
        """Dapatkan agent by name"""
        return self.agents.get(name)

    def get_all_status(self) -> Dict:
        """Dapatkan status semua agent"""
        return {name: agent.get_status() for name, agent in self.agents.items()}

    def execute(self, task: Dict) -> Dict:
        """Eksekusi task dengan agent yang tepat"""
        agent_type = task.get("agent", "default")
        
        # Pilih agent berdasarkan tipe
        if agent_type == "trading":
            agent = self.get_agent("TradingAgent")
        elif agent_type == "analysis":
            agent = self.get_agent("AnalysisAgent")
        elif agent_type == "code":
            agent = self.get_agent("CodeAgent")
        elif agent_type == "research":
            agent = self.get_agent("ResearchAgent")
        elif agent_type == "report":
            agent = self.get_agent("ReportAgent")
        else:
            # Coba semua agent
            for a in self.agents.values():
                if any(c in task.get("type", "") for c in a.get_capabilities()):
                    agent = a
                    break
            else:
                return {"error": "No suitable agent found"}
        
        if not agent:
            return {"error": f"Agent '{agent_type}' not found"}
        
        agent.status = "busy"
        result = agent.execute(task)
        agent.status = "done"
        agent.last_task = task
        agent.last_result = result
        self.task_history.append({
            "task": task,
            "agent": agent.name,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        return result

    def get_history(self, limit: int = 10) -> list:
        """Dapatkan history task"""
        return self.task_history[-limit:]
