"""
agents/workflow/agent_dialog.py - Intent Parser Agent
Parses user request into structured intent with full context
"""
import json
from typing import Dict, Any
from core.logger import logger, console
from rich.panel import Panel


DIALOG_SYSTEM = """You are AgentJW's Intent Parser. 
Analyze user requests and extract structured intent.

Respond ONLY with JSON:
{
  "intent": "build|repair|analyze|modify|continue|run|chat|mcp_tool",
  "category": "trading|youtube|general|solana|system",
  "action": "specific action description",
  "target": "project name/id if mentioned",
  "requirements": ["req1", "req2"],
  "complexity": "simple|medium|complex",
  "needs_clarification": false,
  "clarification_question": "",
  "context_summary": "brief summary of what user wants",
  "suggested_files": ["file1.py"],
  "suggested_tools": ["tool1"],
  "priority": "high|medium|low"
}"""


class AgentDialog:
    """
    Step 1 of workflow: Parse and understand user intent deeply.
    Acts as the conversation interface before any action is taken.
    """
    def __init__(self):
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

    def parse(self, user_request: str, chat_history: list = None) -> Dict:
        """Parse user intent with full context awareness"""
        # Get project context
        projects = self.memory.list_projects(limit=10)
        project_ctx = "\n".join(
            f"- [{p['id']}] {p['name']} ({p['tool_type']}, {p['status']})"
            for p in projects
        ) or "None"

        # Get recent memory
        recent_mem = self.memory.recall(limit=5)
        mem_ctx = "\n".join(f"- {m['content'][:100]}" for m in recent_mem) or "None"

        # Recent chat
        chat_ctx = ""
        if chat_history:
            for msg in chat_history[-4:]:
                role = "User" if msg["role"] == "user" else "Agent"
                chat_ctx += f"{role}: {msg['content'][:150]}\n"

        prompt = f"""Parse this user request into structured intent:

REQUEST: {user_request}

EXISTING PROJECTS:
{project_ctx}

RECENT MEMORY:
{mem_ctx}

RECENT CHAT:
{chat_ctx}

Respond ONLY with JSON."""

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system=DIALOG_SYSTEM,
                temperature=0.1,
                max_tokens=1000,
                json_mode=True,
            )
            parsed = json.loads(response)
            logger.info(f"Intent parsed: {parsed.get('intent')} / {parsed.get('category')}")
            return parsed
        except Exception as e:
            logger.error(f"Dialog parse failed: {e}")
            return {
                "intent": "chat",
                "category": "general",
                "action": user_request,
                "target": "",
                "requirements": [],
                "complexity": "simple",
                "needs_clarification": False,
                "clarification_question": "",
                "context_summary": user_request,
                "suggested_files": [],
                "suggested_tools": [],
                "priority": "medium",
            }

    def clarify(self, question: str) -> str:
        """Ask user for clarification"""
        console.print(Panel(
            f"[yellow]🤔 Need clarification:[/yellow]\n{question}",
            border_style="yellow"
        ))
        return question


agent_dialog = AgentDialog()
