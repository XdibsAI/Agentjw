"""
memory/context_manager.py - Context compression and window management
"""
from typing import List, Dict, Optional
from core.config import config
from core.logger import logger


class ContextManager:
    MAX_TOKENS = 12000
    COMPRESS_THRESHOLD = 8000

    def __init__(self):
        self.llm = None  # lazy load to avoid circular import

    def _get_llm(self):
        if self.llm is None:
            from core.llm_client import llm
            self.llm = llm
        return self.llm

    def trim_messages(self, messages: List[Dict], max_tokens: int = None) -> List[Dict]:
        """Keep most recent messages within token budget"""
        limit = max_tokens or self.MAX_TOKENS
        total = 0
        kept = []
        for msg in reversed(messages):
            tokens = len(msg.get("content", "").split()) * 2
            if total + tokens > limit:
                break
            kept.append(msg)
            total += tokens
        return list(reversed(kept))

    def compress_history(self, messages: List[Dict]) -> List[Dict]:
        """Summarize old messages to free context space"""
        if len(messages) <= 6:
            return messages

        old_messages = messages[:-4]
        recent_messages = messages[-4:]

        history_text = "\n".join([
            f"{m['role'].upper()}: {m['content'][:300]}"
            for m in old_messages
        ])

        summary_prompt = f"""Summarize this conversation history concisely in 3-5 sentences, 
preserving key decisions, errors found, and solutions applied:

{history_text}"""

        try:
            llm = self._get_llm()
            summary = llm.chat(
                messages=[{"role": "user", "content": summary_prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            compressed = [{"role": "system", "content": f"[CONVERSATION SUMMARY]: {summary}"}]
            compressed.extend(recent_messages)
            logger.info("Context compressed successfully")
            return compressed
        except Exception as e:
            logger.warning(f"Context compression failed: {e}")
            return messages[-6:]

    def build_agent_context(
        self,
        agent_role: str,
        user_request: str,
        chat_history: List[Dict],
        memory_snippets: List[str] = None,
        current_task: str = "",
    ) -> List[Dict]:
        """Build full context for an agent call"""
        messages = []

        if memory_snippets:
            mem_text = "\n".join(f"- {m}" for m in memory_snippets[:5])
            messages.append({
                "role": "user",
                "content": f"[RELEVANT MEMORY]:\n{mem_text}"
            })
            messages.append({"role": "assistant", "content": "Memory context acknowledged."})

        trimmed_history = self.trim_messages(chat_history)
        messages.extend(trimmed_history)

        if current_task and current_task != user_request:
            messages.append({
                "role": "user",
                "content": f"[CURRENT TASK]: {current_task}\n\nOriginal request: {user_request}"
            })
        else:
            messages.append({"role": "user", "content": user_request})

        return messages


context_manager = ContextManager()
