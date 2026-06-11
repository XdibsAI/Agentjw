#!/bin/bash
# Fix: tambahkan brain.decide() yang compatible dengan orchestrator VPS
cd ~/agentjw
source venv/bin/activate 2>/dev/null || true

echo "🔧 Fixing agents/brain.py — tambah method decide()..."

cat > agents/brain.py << 'PYEOF'
"""
agents/brain.py - AgentJW Brain
Fix: tambah brain.decide() yang dipakai orchestrator.execute()
     + safe json guard untuk semua LLM response
"""
import json
import traceback
from typing import Dict, List, Optional
from core.logger import logger


def _safe_json(raw: Optional[str], fallback: Dict = None) -> Dict:
    """Safe json.loads — tidak pernah crash pada None atau malformed"""
    if not raw:
        return fallback or {}
    raw = raw.strip()
    # Strip markdown fences
    if "```" in raw:
        import re
        raw = re.sub(r'```(?:json)?\s*', '', raw).strip()
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return fallback or {}


# ── Action mapping dari intent type ──────────────────────────────────────────
_INTENT_TO_ACTION = {
    "general_build":    "build",
    "trading_build":    "build",
    "youtube_build":    "build",
    "video_build":      "build",
    "continue_project": "build",
    "modify_strategy":  "build",
    "project_repair":   "repair",
    "inspect":          "inspect",
    "run_project":      "run",
    "analysis":         "inspect",
    "mcp_tool":         "mcp",
    "chat":             "chat",
}

# Keywords yang paksa action = run
_RUN_KEYWORDS = [
    "jalankan", "coba jalankan", "jalanin", "run project",
    "execute", "start project", "running", "coba run",
]

# Keywords yang paksa action = build
_BUILD_KEYWORDS = [
    "buatkan", "buat", "bikin", "build", "create", "generate",
    "buatin", "second brain", "aplikasi", "program", "tool",
]


class Brain:
    """
    Central brain — classifies intent dan dispatch ke orchestrator.

    Methods:
        decide(user_input, chat_history) → Dict
            Dipakai oleh orchestrator.execute()
            Returns: { action, target_project, target_file, confidence, intent_type }

        run(user_input, file, project) → Dict
            Legacy method — tetap tersedia
    """

    # ── decide() — dipanggil oleh orchestrator.execute() ─────────────────────
    def decide(
        self,
        user_input: str,
        chat_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Classify intent dan return decision dict.

        Returns:
            {
                "action": "chat"|"build"|"run"|"repair"|"inspect"|"mcp",
                "target_project": str|None,
                "target_file":    str|None,
                "confidence":     float,
                "intent_type":    str,
                "user_input":     str,
            }
        """
        try:
            from agents.orchestrator import orchestrator
            from memory.memory_store import memory_store

            lower = user_input.lower()
            intent = orchestrator.route_intent(user_input)
            intent_type = intent.get("type", "chat")
            confidence  = intent.get("confidence", 0.7)

            # Override: run keywords → action = run
            if any(k in lower for k in _RUN_KEYWORDS):
                action = "run"
                intent_type = "run_project"
                confidence = 0.95

            # Override: build keywords → action = build
            elif any(k in lower for k in _BUILD_KEYWORDS):
                action = "build"
                confidence = max(confidence, 0.85)

            else:
                action = _INTENT_TO_ACTION.get(intent_type, "chat")

            # Resolve target project from text
            target_project = None
            target_file    = None

            try:
                projects = memory_store.list_projects()
                lower_inp = user_input.lower()
                for p in projects:
                    if p["id"] in user_input or p["name"].lower() in lower_inp:
                        target_project = p["id"]
                        break
                if not target_project and projects and action in ("run", "repair", "inspect"):
                    target_project = projects[0]["id"]
            except Exception:
                pass

            # Extract filename if mentioned
            import re
            fm = re.search(r'(\w[\w.-]*\.(py|log|txt|md|json|env))', user_input)
            if fm:
                target_file = fm.group(1)

            decision = {
                "action":         action,
                "target_project": target_project,
                "target_file":    target_file,
                "confidence":     confidence,
                "intent_type":    intent_type,
                "user_input":     user_input,
            }

            logger.debug(
                f"Brain.decide: {intent_type} → {action} "
                f"(conf={confidence:.2f}, proj={target_project})"
            )
            return decision

        except Exception as e:
            logger.error(f"Brain.decide failed: {e}")
            logger.debug(traceback.format_exc())
            # Safe fallback — tetap jalan
            return {
                "action":         "chat",
                "target_project": None,
                "target_file":    None,
                "confidence":     0.5,
                "intent_type":    "chat",
                "user_input":     user_input,
            }

    # ── run() — legacy method ─────────────────────────────────────────────────
    def run(
        self,
        user_input: str,
        file: Optional[str] = None,
        project: Optional[str] = None,
    ) -> Dict:
        """Legacy entry point — wraps decide() + execute"""
        try:
            from agents.orchestrator import orchestrator
            decision = self.decide(user_input)
            action = decision["action"]

            if action in ("build", "run", "repair", "inspect", "mcp"):
                result = orchestrator.smart_build(user_input, None)
                return {
                    "type":     action,
                    "result":   result,
                    "response": str(result.get("status", "done")),
                }

            # Chat
            from memory.memory_store import memory_store
            session_id = "brain-session"
            history = memory_store.get_chat_history(session_id, limit=8) or []
            response = orchestrator.chat(user_input, history, session_id)
            if not response:
                response = "Tidak ada respons dari model. Coba lagi."
            return {"type": "chat", "response": response, "result": None}

        except Exception as e:
            logger.error(f"Brain.run failed: {e}")
            return {
                "type":     "error",
                "response": f"AgentJW error: {e}",
                "result":   None,
            }


brain = Brain()
PYEOF

echo "  ✓ agents/brain.py fixed"
echo ""
echo "Test:"
echo "  python main.py"
echo "  ⚡ agentjw > buatkan second brain dan jalankan"
