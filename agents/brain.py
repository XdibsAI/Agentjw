import json
from typing import Dict, List, Optional
from core.logger import logger
from memory.memory_store import memory_store


BRAIN_SYSTEM = """You are AgentJW's routing brain.
Analyze user input and decide the exact action.

Respond ONLY with JSON:
{
  "action": "read_file|scan_project|show_log|run_project|build_trading|build_youtube|build_general|repair|analyze|continue|modify|chat|mcp_token|mcp_trending",
  "target_project": "project_id_or_name_or_null",
  "target_file": "filename.py_or_null",
  "params": {},
  "reasoning": "brief reason",
  "confidence": 0.95
}

Rules:
- "tampilkan kode X.py" or "baca X.py" → read_file, target_file: X.py
- "tampilkan struktur" or "scan" → scan_project
- "tampilkan log" or "lihat log" → show_log
- "jalankan" or "run bot" → run_project
- "buat trading bot" or "build bot" → build_trading
- "perbaiki" or "repair" or "fix" → repair
- "analisa" or "analyze" → analyze
- "lanjutkan" or "continue" → continue
- "ubah strategi" or "modify" → modify
- "check token" or "cek token" → mcp_token
- "trending" or "token baru" → mcp_trending
- everything else → chat
"""


class Brain:
    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from core.llm_client import llm
            self._llm = llm
        return self._llm

    def decide(self, user_input: str, chat_history: List[Dict] = None) -> Dict:
        projects = memory_store.list_projects()
        proj_ctx = "\n".join(
            "[" + p["id"] + "] " + p["name"] + " | " + p["tool_type"] + " | " + p["project_dir"]
            for p in projects
        ) or "No projects"

        recent = ""
        if chat_history:
            for msg in chat_history[-4:]:
                role = "User" if msg["role"] == "user" else "Agent"
                recent += role + ": " + msg["content"][:100] + "\n"

        prompt = (
            "User: " + user_input + "\n\n"
            "Projects:\n" + proj_ctx + "\n\n"
            "Recent chat:\n" + (recent or "none") + "\n\n"
            "Decide action. JSON only."
        )

        try:
            resp = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system=BRAIN_SYSTEM,
                temperature=0.1,
                max_tokens=200,
                json_mode=True,
            )
            decision = json.loads(resp)
            logger.info("Brain: " + decision.get("action","?") + " | " + decision.get("reasoning","")[:50])
            return decision
        except Exception as e:
            logger.error("Brain failed: " + str(e))
            return {"action": "chat", "target_project": None, "target_file": None, "params": {}, "reasoning": "fallback", "confidence": 0.5}

    def resolve_project(self, ref: Optional[str], projects: List[Dict]) -> Optional[Dict]:
        if not ref or not projects:
            return projects[0] if projects else None
        ref_lower = ref.lower()
        for p in projects:
            if p["id"] == ref or p["id"].startswith(ref[:6]):
                return p
        for p in projects:
            if ref_lower in p["name"].lower() or p["name"].lower() in ref_lower:
                return p
        return projects[0] if projects else None


brain = Brain()
