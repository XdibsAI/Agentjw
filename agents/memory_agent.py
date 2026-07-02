"""
agents/memory_agent.py - Memory management and retrieval agent
"""

from typing import Dict, Any

from agents.base_agent import BaseAgent
from core.models import AgentRole
from memory.project_indexer import ProjectIndexer


MEMORY_SYSTEM = """You are a memory management specialist for an AI system.
Your job is to identify and extract important information worth remembering from conversations and executions.
"""


class MemoryAgent(BaseAgent):

    def __init__(self):
        super().__init__(AgentRole.MEMORY, MEMORY_SYSTEM)

        try:
            self.project_indexer = ProjectIndexer()
        except Exception:
            self.project_indexer = None

    def run(self, input: Dict, context: Dict = None) -> Dict:

        action = input.get("action", "retrieve")

        if action == "extract_and_store":
            return self._extract_and_store(input)

        elif action == "retrieve":
            return self._retrieve(input)

        elif action == "summarize_session":
            return self._summarize_session(input)

        return {}

    def _extract_and_store(self, input: Dict) -> Dict:

        session_summary = input.get("session_summary", "")
        execution_success = input.get("success", False)
        project_name = input.get("project_name", "")

        if not session_summary:
            return {"stored": 0}

        messages = [
            {
                "role": "user",
                "content": f"""
PROJECT: {project_name}
SUCCESS: {execution_success}
SUMMARY: {session_summary}

Extract important memories as JSON.
"""
            }
        ]

        try:

            import json

            response = self._chat(
                messages,
                temperature=0.3,
                max_tokens=16000,
                json_mode=True
            )

            data = json.loads(response)

            memories = data.get("memories", [])

            stored_count = 0

            for mem in memories:

                self.memory.store(
                    type=mem.get("type", "fact"),
                    content=mem.get("content", ""),
                    importance=mem.get("importance", 1.0),
                    metadata={
                        "project": project_name,
                        "success": execution_success
                    },
                )

                stored_count += 1

            return {"stored": stored_count}

        except Exception as e:

            self._log(f"Memory extraction failed: {e}")

            return {"stored": 0}

    def _retrieve(self, input: Dict) -> Dict:

        query = input.get("query", "")
        memory_type = input.get("type")
        limit = input.get("limit", 5)

        if query:
            memories = self.memory.search_memories(
                query,
                type=memory_type,
                limit=limit
            )
        else:
            memories = self.memory.recall(
                type=memory_type,
                limit=limit
            )

        snippets = [
            m["content"]
            for m in memories
        ]

        project_hits = []

        if query and self.project_indexer:

            try:

                hits = self.project_indexer.search(query)

                for path in hits[:5]:

                    project_hits.append(
                        {
                            "path": path,
                            "content": self.project_indexer.get_content(
                                path,
                                max_chars=1500
                            )
                        }
                    )

            except Exception as e:

                self._log(
                    f"Project search failed: {e}"
                )

        return {
            "memories": memories,
            "snippets": snippets,
            "project_hits": project_hits,
        }

    def _summarize_session(self, input: Dict) -> str:

        request = input.get("request", "")
        files = input.get("files", [])
        success = input.get("success", False)
        errors = input.get("errors", [])

        file_list = ", ".join(files[:10])

        error_summary = (
            "; ".join(errors[:3])
            if errors
            else "none"
        )

        return (
            f"Task: {request[:200]}. "
            f"Files created: {file_list}. "
            f"Success: {success}. "
            f"Errors encountered: {error_summary}."
        )


memory_agent = MemoryAgent()

