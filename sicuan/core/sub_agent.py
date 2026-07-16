"""
Sub-Agent — Break big tasks; clean context per subtask
"""
from typing import Dict, List, Optional, Callable


class SubAgent:
    def __init__(self, name: str, task: str, tools: List[str] = None):
        self.name = name
        self.task = task
        self.tools = tools or []
        self.result = None
        self.status = "pending"  # pending, running, done, failed
        self.context = []

    def execute(self, brain) -> Dict:
        """Execute sub-agent dengan context terpisah"""
        self.status = "running"
        try:
            # Simpan context utama
            main_context = brain._context if hasattr(brain, '_context') else []
            
            # Jalankan dengan context terpisah
            result = brain.think_and_respond(
                self.task,
                chat_history=[],  # Fresh context
                force_model="deepseek/deepseek-chat"
            )
            
            self.result = result
            self.status = "done"
            return {"success": True, "result": result}
        except Exception as e:
            self.status = "failed"
            return {"success": False, "error": str(e)}


_agents = {}


def create_sub_agent(name: str, task: str, tools: List[str] = None) -> SubAgent:
    agent = SubAgent(name, task, tools)
    _agents[name] = agent
    return agent


def get_sub_agent(name: str) -> Optional[SubAgent]:
    return _agents.get(name)


def list_sub_agents() -> List[str]:
    return list(_agents.keys())
