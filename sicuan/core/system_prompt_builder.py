"""
System Prompt Builder — Terinspirasi dari Claude Code
"""
from typing import List, Dict, Optional


class SystemPromptBuilder:
    """Bangun system prompt dinamis untuk LLM"""

    def __init__(self):
        self.identity = ""
        self.tools = []
        self.context = ""

    def set_identity(self, identity: str):
        self.identity = identity
        return self

    def add_tool(self, tool_name: str, description: str, schema: Dict = None):
        self.tools.append({
            "name": tool_name,
            "description": description,
            "schema": schema or {}
        })
        return self

    def set_context(self, context: str):
        self.context = context
        return self

    def build(self, user_message: str) -> str:
        parts = []
        
        # 1. Identity
        if self.identity:
            parts.append(self.identity)
        
        # 2. Tools
        if self.tools:
            tool_prompt = "TOOLS YANG TERSEDIA:\n"
            for t in self.tools:
                tool_prompt += f"- {t['name']}: {t['description']}\n"
            parts.append(tool_prompt)
        
        # 3. Context
        if self.context:
            parts.append(f"KONTEKS:\n{self.context}")
        
        # 4. User message
        parts.append(f"USER: {user_message}")
        
        return "\n\n".join(parts)


_builder = None


def get_prompt_builder() -> SystemPromptBuilder:
    global _builder
    if _builder is None:
        _builder = SystemPromptBuilder()
    return _builder
