"""
Dispatcher - Deterministic Agent Dispatch
Router memilih → Dispatcher langsung eksekusi, tanpa Brain override
"""

import logging
from typing import Dict, Any
from sicuan.core.agent_registry import get_agent_registry

logger = logging.getLogger(__name__)


class Dispatcher:
    """Deterministic dispatcher - no Brain override"""

    def __init__(self):
        self.registry = get_agent_registry()

    def dispatch(self, role: str, user_message: str, context: Dict = None) -> Dict:
        """Dispatch langsung ke agent berdasarkan role"""
        logger.info(f"[DISPATCHER] 🎯 Dispatching to {role}: {user_message[:50]}...")
        
        agent = self.registry.get(role)
        if agent:
            result = agent.execute(user_message)
            logger.info(f"[DISPATCHER] ✅ Agent {role} completed")
            return {
                "action": f"{role}_dispatch",
                "response": result.get("display", "✅ Task completed"),
                "result": result
            }
        
        # Fallback: chat
        logger.info(f"[DISPATCHER] ⚠️ Role {role} not found, fallback to chat")
        return {
            "action": "chat",
            "response": f"Role {role} belum tersedia. Coba perintah lain.",
            "result": {"status": "not_found"}
        }

    def _dispatch_coder(self, user_message: str, context: Dict = None) -> Dict:
        """Coder Agent"""
        from sicuan.agents.coder_agent import get_coder_agent
        agent = get_coder_agent()
        result = agent.execute(user_message)
        return {
            "action": "coder_dispatch",
            "response": result.get("display", "✅ Task executed"),
            "result": result
        }

    def _dispatch_reviewer(self, user_message: str, context: Dict = None) -> Dict:
        """Reviewer Agent"""
        from sicuan.agents.reviewer_agent import get_reviewer_agent
        agent = get_reviewer_agent()
        result = agent.execute(user_message)
        return {
            "action": "reviewer_dispatch",
            "response": result.get("display", "✅ Review completed"),
            "result": result
        }

    def _dispatch_analyzer(self, user_message: str, context: Dict = None) -> Dict:
        """Analyzer Agent"""
        from sicuan.agents.analyzer_agent import get_analyzer_agent
        agent = get_analyzer_agent()
        result = agent.execute(user_message)
        return {
            "action": "analyzer_dispatch",
            "response": result.get("display", "✅ Analysis completed"),
            "result": result
        }

    def _dispatch_planner(self, user_message: str, context: Dict = None) -> Dict:
        """Planner Agent"""
        return {
            "action": "planner_dispatch",
            "response": "📋 Planning feature coming soon",
            "result": {"status": "pending"}
        }

    def _dispatch_vision(self, user_message: str, context: Dict = None) -> Dict:
        """Vision Agent"""
        return {
            "action": "vision_dispatch",
            "response": "🖼️ Vision feature coming soon",
            "result": {"status": "pending"}
        }

    def _dispatch_chat(self, user_message: str, context: Dict = None) -> Dict:
        """Chat - default fallback"""
        return {
            "action": "chat",
            "response": "💬 Chat mode",
            "result": {"status": "chat"}
        }


def get_dispatcher():
    _dispatcher = None
    if _dispatcher is None:
        _dispatcher = Dispatcher()
    return _dispatcher