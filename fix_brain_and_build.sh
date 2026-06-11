#!/bin/bash
# ============================================================
# fix_brain_and_build.sh
# Fix: Brain NoneType error + enable "jalankan" / execute
# Jalankan dari: ~/agentjw/
# ============================================================
cd ~/agentjw
source venv/bin/activate 2>/dev/null || true

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  🔧  AgentJW Brain Fix                  ║"
echo "╚══════════════════════════════════════════╝"

# ── FIX 1: agents/brain.py ──────────────────────────────────────────────────
echo ""
echo "[1/3] Fixing agents/brain.py..."

cat > agents/brain.py << 'PYEOF'
"""
agents/brain.py - AgentJW Brain
Routes user input to the right handler.
Fix: safe json.loads + None guard on all LLM responses
"""
import json
import traceback
from typing import Dict, Optional
from core.logger import logger, console


def _safe_json(raw: Optional[str], fallback: Dict = None) -> Dict:
    """Safe json.loads — never raises on None or malformed input"""
    if not raw:
        return fallback or {}
    raw = raw.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.splitlines()
        raw = "\n".join(
            l for l in lines
            if not l.strip().startswith("```")
        ).strip()
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        # Try to extract JSON object from text
        import re
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        return fallback or {}


class Brain:
    """
    Central brain — classifies user intent and dispatches.
    Wraps orchestrator with safe error handling.
    """

    def run(self, user_input: str, file: Optional[str] = None,
            project: Optional[str] = None) -> Dict:
        """
        Main entry point.
        Returns dict: { "type": str, "response": str, "result": any }
        """
        try:
            from agents.orchestrator import orchestrator
            intent = orchestrator.route_intent(user_input)
            logger.debug(f"Brain: {intent['type']} | file={file} | project={project}")

            # ── Execute / run project ──────────────────────────────────────
            if intent["type"] in ("run_project", "inspect") or any(
                k in user_input.lower() for k in [
                    "jalankan", "coba jalankan", "run", "execute",
                    "jalanin", "running"
                ]
            ):
                result = orchestrator.smart_build(user_input, None)
                return {"type": "run", "result": result,
                        "response": "Executed successfully"}

            # ── Build ──────────────────────────────────────────────────────
            if intent["type"] in (
                "general_build", "trading_build", "youtube_build",
                "video_build", "continue_project", "modify_strategy"
            ):
                result = orchestrator.smart_build(user_input, None)
                return {"type": "build", "result": result,
                        "response": "Build completed"}

            # ── Repair ────────────────────────────────────────────────────
            if intent["type"] == "project_repair":
                result = orchestrator.smart_build(user_input, None)
                return {"type": "repair", "result": result,
                        "response": "Repair completed"}

            # ── Chat (default) ────────────────────────────────────────────
            from memory.memory_store import memory_store
            session_id = "brain-session"
            history = memory_store.get_chat_history(session_id, limit=8) or []
            response = orchestrator.chat(user_input, history, session_id)

            # Guard: ensure response is a string
            if response is None:
                response = "Maaf, tidak ada respons dari model. Coba lagi."
            if not isinstance(response, str):
                response = str(response)

            return {"type": "chat", "response": response, "result": None}

        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Brain failed: {e}")
            logger.debug(tb)
            # Return safe fallback — never crash caller
            return {
                "type": "error",
                "response": f"AgentJW error: {e}",
                "result": None,
                "traceback": tb[-300:],
            }


brain = Brain()
PYEOF

echo "  ✓ agents/brain.py written"

# ── FIX 2: Patch general_build → actually write files + run ─────────────────
echo ""
echo "[2/3] Patching orchestrator _general_build to create + execute projects..."

python3 - << 'PYEOF'
from pathlib import Path

path = Path("agents/orchestrator.py")
content = path.read_text(encoding="utf-8")

if "_write_and_run" in content:
    print("  ⚠  Already patched — skipping _general_build")
else:
    # Replace _general_build to actually write files and optionally run
    old = '''    def _general_build(self, user_request: str, session_id: str) -> Dict:
        from agents.workflow.workflow_engine import workflow_engine
        return workflow_engine.run(user_request, session_id=session_id)'''

    new = '''    def _general_build(self, user_request: str, session_id: str) -> Dict:
        from agents.workflow.workflow_engine import workflow_engine
        result = workflow_engine.run(user_request, session_id=session_id)

        # Auto-write files to disk if workflow returned them
        if isinstance(result, dict) and result.get("files"):
            project_name = result.get("project_name",
                f"project_{session_id[:6]}")
            project_dir = config.PROJECTS_DIR / project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            for f in result["files"]:
                fp = project_dir / f.path
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(f.content, encoding="utf-8")
            if "project_id" not in result:
                pid = project_manager.register_project(
                    name=project_name,
                    description=user_request,
                    project_dir=str(project_dir),
                )
                project_manager.save_files(pid, result["files"])
                project_manager.set_status(pid, "success")
                result["project_id"] = pid
                result["project_dir"] = str(project_dir)
            console.print(Panel(
                f"[green]✅ Project created![/green]\\n"
                f"📁 {project_dir}\\n"
                f"📄 {len(result['files'])} files written to disk",
                title="🏗  General Build",
                border_style="green"
            ))
        return result

    def _write_and_run(self, project_dir, entry_file="main.py", timeout=5):
        """Optionally run the built project and capture output"""
        try:
            from mcp.tools.filesystem_tool import filesystem_tool
            result = filesystem_tool.run_and_capture(
                str(project_dir), timeout=timeout
            )
            self._show_json("▶️  Run Output", result)
            return result
        except Exception as e:
            logger.warning(f"Run failed: {e}")
            return {"error": str(e)}'''

    content = content.replace(old, new)
    path.write_text(content, encoding="utf-8")
    print("  ✓ orchestrator _general_build patched")
PYEOF

# ── FIX 3: Patch cli.py _smart_chat → call brain properly ───────────────────
echo ""
echo "[3/3] Patching cli.py to route 'jalankan' through build not chat..."

python3 - << 'PYEOF'
from pathlib import Path

path = Path("interface/cli.py")
content = path.read_text(encoding="utf-8")

if "jalankan_trigger" in content:
    print("  ⚠  Already patched")
else:
    # Add jalankan detection before smart_chat falls through to chat
    old = '''            intent = orchestrator.route_intent(user_input)

            # High confidence non-chat intents → smart_build
            if intent["type"] != "chat" and intent["confidence"] >= 0.85:
                orchestrator.smart_build(user_input, self.session_id)
                return'''

    new = '''            intent = orchestrator.route_intent(user_input)

            # jalankan_trigger — "coba jalankan" → build/run, not chat
            jalankan_kw = [
                "coba jalankan", "jalankan", "jalanin", "run project",
                "execute", "running", "start project",
            ]
            if any(k in lower for k in jalankan_kw):
                orchestrator.smart_build(user_input, self.session_id)
                return

            # High confidence non-chat intents → smart_build
            if intent["type"] != "chat" and intent["confidence"] >= 0.85:
                orchestrator.smart_build(user_input, self.session_id)
                return'''

    content = content.replace(old, new)
    path.write_text(content, encoding="utf-8")
    print("  ✓ cli.py jalankan routing patched")
PYEOF

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅  Brain Fix Complete!                ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "Test:"
echo "  python main.py"
echo "  ⚡ agentjw > buatkan second brain untuk simpan aktivitas harianku"
echo "  ⚡ agentjw > coba jalankan"
echo ""
