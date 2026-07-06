"""
Agents Module — Multi-Agent Collaboration
"""

from sicuan.agents.base import Agent, AgentOrchestrator
from sicuan.agents.trading_agent import TradingAgent
from sicuan.agents.analysis_agent import AnalysisAgent
from sicuan.agents.code_agent import CodeAgent

# Create orchestrator
orchestrator = AgentOrchestrator()

# Register agents
orchestrator.register(TradingAgent())
orchestrator.register(AnalysisAgent())
orchestrator.register(CodeAgent())

print(f"[AGENT] Registered agents: {list(orchestrator.agents.keys())}")
