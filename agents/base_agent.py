"""
agents/base_agent.py - Abstract base agent
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.models import AgentRole, AgentMessage
from core.logger import logger, console


class BaseAgent(ABC):
    def __init__(self, role: AgentRole, system_prompt: str):
        self.role = role
        self.system_prompt = system_prompt
        self._llm = None
        self._memory = None

    @property
    def llm(self):
        if self._llm is None:
            from core.llm_client import llm
            self._llm = llm
        return self._llm

    @property
    def memory(self):
        if self._memory is None:
            from memory.memory_store import memory_store
            self._memory = memory_store
        return self._memory

    @abstractmethod
    def run(self, input: Any, context: Dict = None) -> Any:
        pass

    def _chat(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 4096, json_mode: bool = False) -> str:
        return self.llm.chat(
            messages=messages,
            system=self.system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )

    def _log(self, message: str, level: str = "info"):
        role_colors = {
            AgentRole.ORCHESTRATOR: "[agent.orchestrator]",
            AgentRole.PLANNER: "[agent.planner]",
            AgentRole.CODER: "[agent.coder]",
            AgentRole.REVIEWER: "[agent.reviewer]",
            AgentRole.REPAIR: "[agent.repair]",
            AgentRole.MEMORY: "[agent.memory]",
            AgentRole.CRITIC: "[agent.critic]",
        }
        prefix = role_colors.get(self.role, "")
        console.print(f"{prefix}[{self.role.value.upper()}] {message}")
