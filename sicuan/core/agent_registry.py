"""
AgentRegistry — lazy-loads agent implementations by role name so the
Dispatcher never needs a hard import (and never crashes) if a given
agent module isn't wired up yet.
"""

import logging
from typing import Dict, Optional, Callable, Any

logger = logging.getLogger(__name__)


class AgentRegistry:

    def __init__(self):
        self._factories: Dict[str, Callable[[], Any]] = {
            "coder": self._load_coder,
            "reviewer": self._load_reviewer,
            "analyzer": self._load_analyzer,
            "repair": self._load_repair,
        }
        self._cache: Dict[str, Any] = {}

    def get(self, role: str) -> Optional[Any]:
        if role in self._cache:
            return self._cache[role]

        factory = self._factories.get(role)
        if factory is None:
            logger.warning(f"[AGENT_REGISTRY] Unknown role: {role}")
            return None

        try:
            agent = factory()
            self._cache[role] = agent
            return agent
        except Exception as e:
            logger.warning(f"[AGENT_REGISTRY] Failed to load agent '{role}': {e}")
            return None

    def register(self, role: str, factory: Callable[[], Any]) -> None:
        self._factories[role] = factory
        self._cache.pop(role, None)

    def _load_coder(self):
        from sicuan.agents.coder_agent import get_coder_agent
        return get_coder_agent()

    def _load_reviewer(self):
        from sicuan.agents.reviewer_agent import get_reviewer_agent
        return get_reviewer_agent()

    def _load_analyzer(self):
        from sicuan.agents.analyzer_agent import get_analyzer_agent
        return get_analyzer_agent()

    def _load_repair(self):
        from sicuan.agents.repair_agent import get_repair_agent
        return get_repair_agent()


_registry = None


def get_agent_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
