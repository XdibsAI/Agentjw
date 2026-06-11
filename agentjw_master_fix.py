#!/usr/bin/env python3
"""
agentjw_master_fix.py
=====================
Fix semua critical + warning dari sync analyzer:

CRITICAL:
  1. Port mismatch — api_server hardcode 8000, APK target 18790
  2. Missing GET /api/projects endpoint
  3. Missing GET /api/logs endpoint

WARNING:
  4. Orchestrator missing methods (_general_build, _repair_existing, _inspect_action,
     _run_project, _find_project_ref)
  5. Tools not in AI system prompt
  6. Router downgrade model untuk task kompleks
  7. Missing env vars (ANTHROPIC_API_KEY, ANTHROPIC_MODEL, CHROMA_PERSIST_DIR)
  8. Per-project .env missing vars
  9. Brain intents not detected (detection fix)

Jalankan: python3 agentjw_master_fix.py
"""

import re
import sys
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path.home() / "agentjw"
NOW = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_DIR = ROOT / "backups" / f"master_fix_{NOW}"

try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console()
    def ok(s): console.print(f"  [green]✅ {s}[/green]")
    def warn(s): console.print(f"  [yellow]⚠️  {s}[/yellow]")
    def err(s): console.print(f"  [red]❌ {s}[/red]")
    def fix(s): console.print(f"  [magenta]🔧 {s}[/magenta]")
    def h(s): console.print(f"\n[bold cyan]{'─'*55}[/bold cyan]\n[bold cyan]{s}[/bold cyan]")
except ImportError:
    def ok(s): print(f"  ✅ {s}")
    def warn(s): print(f"  ⚠️  {s}")
    def err(s): print(f"  ❌ {s}")
    def fix(s): print(f"  🔧 {s}")
    def h(s): print(f"\n{'─'*55}\n{s}")


def read(path: Path) -> str:
    try: return path.read_text(encoding="utf-8", errors="ignore")
    except: return ""

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def backup(path: Path):
    if path.exists():
        dest = BACKUP_DIR / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)


# ═══════════════════════════════════════════════════════════════════
# FIX 1: PORT — change api_server to use env PORT, default 18790
# ═══════════════════════════════════════════════════════════════════

def fix_port():
    h("FIX 1: PORT MISMATCH")

    api_path = ROOT / "api_server.py"
    env_path = ROOT / ".env"

    backup(api_path)
    backup(env_path)

    # Fix .env: change API_PORT from 8000 to 18790
    env_content = read(env_path)
    if "API_PORT=8000" in env_content:
        env_content = env_content.replace("API_PORT=8000", "API_PORT=18790")
        write(env_path, env_content)
        fix(".env: API_PORT 8000 → 18790")
    elif "API_PORT" not in env_content:
        env_content += "\nAPI_PORT=18790\n"
        write(env_path, env_content)
        fix(".env: Added API_PORT=18790")
    else:
        ok(".env API_PORT already set correctly")

    # Fix api_server.py: add startup block that reads PORT from env
    api_content = read(api_path)

    # Check if already has correct port logic
    if "API_PORT" in api_content and "18790" in api_content:
        ok("api_server.py already uses API_PORT env var")
        return

    # Add/fix the __main__ block
    old_main_patterns = [
        'if __name__ == "__main__":\n    import uvicorn\n    uvicorn.run(app, host="0.0.0.0", port=8000)',
        "if __name__ == '__main__':\n    import uvicorn\n    uvicorn.run(app, host='0.0.0.0', port=8000)",
        'uvicorn.run(app, host="0.0.0.0", port=8000)',
        "uvicorn.run(app, host='0.0.0.0', port=8000)",
    ]

    new_main = '''
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("API_PORT", "18790"))
    print(f"Starting AgentJW API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
'''

    replaced = False
    for pattern in old_main_patterns:
        if pattern in api_content:
            api_content = api_content.replace(pattern, new_main.strip())
            replaced = True
            break

    if not replaced:
        # Append if no __main__ block
        if '__name__ == "__main__"' not in api_content:
            api_content += new_main
            fix("api_server.py: Added __main__ block with env PORT")
        else:
            # Replace port number inline
            api_content = re.sub(r'port\s*=\s*8000', 'port=int(os.getenv("API_PORT","18790"))', api_content)
            fix("api_server.py: Replaced port=8000 with env var")
    else:
        fix("api_server.py: Updated __main__ block with env PORT")

    # Also fix any hardcoded port in uvicorn.run calls
    api_content = re.sub(
        r'uvicorn\.run\(app,\s*host=["\']0\.0\.0\.0["\'],\s*port=8000',
        'uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("API_PORT","18790"))',
        api_content
    )

    # Ensure os is imported
    if "import os" not in api_content[:500]:
        api_content = "import os\n" + api_content

    write(api_path, api_content)
    ok("api_server.py port fix applied")


# ═══════════════════════════════════════════════════════════════════
# FIX 2 & 3: MISSING ENDPOINTS /api/projects and /api/logs
# ═══════════════════════════════════════════════════════════════════

def fix_endpoints():
    h("FIX 2 & 3: MISSING ENDPOINTS")

    api_path = ROOT / "api_server.py"
    backup(api_path)
    content = read(api_path)

    new_endpoints = ""

    # /api/projects endpoint
    if '"/api/projects"' not in content and "'/api/projects'" not in content:
        new_endpoints += '''

@app.get("/api/projects")
async def get_projects():
    """List all projects — used by APK Projects tab"""
    try:
        sys.path.insert(0, str(ROOT))
        from memory.memory_store import memory_store
        projects = memory_store.list_projects(limit=50)
        formatted = []
        for p in projects:
            formatted.append({
                "id": p.get("id", ""),
                "name": p.get("name", ""),
                "status": p.get("status", "unknown"),
                "tool_type": p.get("tool_type", "general"),
                "created_at": p.get("created_at", ""),
                "project_dir": p.get("project_dir", ""),
                "description": p.get("description", ""),
            })
        return {
            "projects": formatted,
            "total": len(formatted),
            "status": "ok"
        }
    except Exception as e:
        logger.error(f"get_projects error: {e}")
        return {"projects": [], "total": 0, "error": str(e), "status": "error"}
'''
        fix("Added GET /api/projects endpoint")

    # /api/logs endpoint
    if '"/api/logs"' not in content and "'/api/logs'" not in content:
        new_endpoints += '''

@app.get("/api/logs")
async def get_logs(project_id: str = None, lines: int = 100):
    """Get logs — used by APK Log button"""
    try:
        sys.path.insert(0, str(ROOT))
        from memory.memory_store import memory_store
        from pathlib import Path as P

        log_data = {}

        # API server log
        api_log = P(__file__).parent / "api.log"
        if api_log.exists():
            all_lines = api_log.read_text(errors="ignore").splitlines()
            log_data["api_server"] = "\n".join(all_lines[-lines:])

        # Project-specific log
        if project_id:
            projects = memory_store.list_projects()
            proj = next((p for p in projects if p["id"] == project_id
                        or p["id"].startswith(project_id)), None)
            if proj:
                proj_dir = P(proj["project_dir"])
                for log_file in list(proj_dir.glob("*.log")) + list((proj_dir / "logs").glob("*.log") if (proj_dir / "logs").exists() else []):
                    all_lines = log_file.read_text(errors="ignore").splitlines()
                    log_data[log_file.name] = "\n".join(all_lines[-lines:])

        # Daily sync log
        sync_log = P(__file__).parent / "logs" / f"daily_{datetime.now().strftime('%Y%m%d')}.md"
        if sync_log.exists():
            log_data["sync_daily"] = sync_log.read_text(errors="ignore")[-2000:]

        return {
            "logs": log_data,
            "lines_requested": lines,
            "project_id": project_id,
            "status": "ok"
        }
    except Exception as e:
        logger.error(f"get_logs error: {e}")
        return {"logs": {}, "error": str(e), "status": "error"}
'''
        fix("Added GET /api/logs endpoint")

    if new_endpoints:
        # Insert before the last if __name__ block or at end
        if 'if __name__ == "__main__"' in content:
            idx = content.rfind('if __name__ == "__main__"')
            content = content[:idx] + new_endpoints + "\n" + content[idx:]
        else:
            content += new_endpoints

        # Ensure datetime imported
        if "from datetime import datetime" not in content and "import datetime" not in content:
            content = content.replace("import sys", "import sys\nfrom datetime import datetime", 1)

        write(api_path, content)
        ok("Endpoints added to api_server.py")
    else:
        ok("Both endpoints already exist")


# ═══════════════════════════════════════════════════════════════════
# FIX 4: ORCHESTRATOR MISSING METHODS
# ═══════════════════════════════════════════════════════════════════

MISSING_METHODS = '''
    # ═══════════════════════════════════════════
    # METHODS RESTORED BY agentjw_master_fix.py
    # ═══════════════════════════════════════════

    def _general_build(self, user_request: str, session_id: str) -> Dict:
        """General purpose build via workflow engine"""
        from agents.workflow.workflow_engine import workflow_engine
        result = workflow_engine.run(user_request, session_id=session_id)
        # Post-build env check
        if isinstance(result, dict) and result.get("project_dir"):
            env_msg = self._post_build_env_check(
                result["project_dir"],
                result.get("project_name", ""),
                session_id
            )
            if env_msg:
                result["env_setup_message"] = env_msg
        return result

    def _repair_existing(self, user_request: str, session_id: str = None) -> Dict:
        """Auto-repair most recent or referenced project"""
        from agents.specialist.repair_specialist import repair_specialist
        projects = memory_store.list_projects()
        target = self._find_project_ref(user_request, projects)
        if not target and projects:
            target = projects[0]
        if not target:
            project_manager.display_all_projects()
            return {"status": "needs_selection"}
        console.print(f"[yellow]🔧 Repairing: {target['name']}[/yellow]")
        return repair_specialist.auto_repair_project(target["id"], deep=True)

    def _inspect_action(self, user_request: str) -> Dict:
        """Inspect project files, logs, hashes — NO hallucination"""
        lower = user_request.lower()
        projects = memory_store.list_projects()
        proj = self._find_project_ref(user_request, projects) or (projects[0] if projects else None)
        if not proj:
            console.print("[yellow]No project found[/yellow]")
            return {"status": "no_project"}

        pd = proj["project_dir"]

        if any(k in lower for k in ["log", "trading_bot.log", "error.log"]):
            data = self.fs.read_log(pd)
            self._show_json("📋 Real Log (from disk)", data)

        elif any(k in lower for k in ["hash", "sha256"]):
            fname = self._extract_filename(user_request)
            data = self.fs.read_file(str(Path(pd) / fname))
            self._show_json("🔐 Real Hash (from disk)", {"sha256": data.get("sha256"), "file": fname})

        elif any(k in lower for k in ["jalankan", "run", "python main", "roi", "performance"]):
            console.print("[cyan]▶️  Running (10s capture)...[/cyan]")
            data = self.fs.run_and_capture(pd, timeout=10)
            self._show_json("▶️  Real Output (from disk)", data)

        elif any(k in lower for k in ["baca", "isi", "read", "tampilkan isi"]):
            fname = self._extract_filename(user_request)
            data = self.fs.read_file(str(Path(pd) / fname))
            if data.get("content"):
                lines = data["content"].splitlines()[:60]
                console.print(Panel(
                    "\\n".join(lines),
                    title=f"📄 {fname} (real file)",
                    border_style="cyan"
                ))
            else:
                self._show_json(f"📄 {fname}", data)
        else:
            data = self.fs.scan_project(pd)
            self._show_scan(data)

        return {"status": "done", "project_id": proj["id"]}

    def _run_project(self, user_request: str) -> Dict:
        """Run a project and capture output"""
        projects = memory_store.list_projects()
        proj = self._find_project_ref(user_request, projects) or (projects[0] if projects else None)
        if not proj:
            return {"status": "no_project"}
        console.print(f"[cyan]▶️  Running: {proj['name']}[/cyan]")
        result = self.fs.run_and_capture(proj["project_dir"], timeout=10)
        self._show_json("▶️  Real Output", result)
        return {"status": "done"}

    def _find_project_ref(self, text: str, projects: List[Dict]) -> Optional[Dict]:
        """Find project by ID, name, or partial keyword match"""
        if not text or not projects:
            return None
        text_lower = text.lower()
        # Exact ID match
        for p in projects:
            if p["id"] in text:
                return p
        # Name match
        for p in projects:
            parts = p["name"].lower().split("_")
            if p["name"].lower() in text_lower or any(
                    w in text_lower for w in parts if len(w) > 3):
                return p
        return None
'''

def fix_orchestrator_methods():
    h("FIX 4: ORCHESTRATOR MISSING METHODS")

    orch_path = ROOT / "agents" / "orchestrator.py"
    backup(orch_path)
    content = read(orch_path)

    methods_to_check = [
        "_general_build", "_repair_existing", "_inspect_action",
        "_run_project", "_find_project_ref"
    ]

    missing = [m for m in methods_to_check if f"def {m}" not in content]

    if not missing:
        ok("All orchestrator methods already present")
        return

    warn(f"Missing methods: {missing}")

    # Insert before the closing singleton line
    marker = "\norchestrator = OrchestratorAgent()"
    if marker in content:
        content = content.replace(marker, MISSING_METHODS + marker)
        fix(f"Inserted {len(missing)} missing methods into orchestrator.py")
    else:
        # Append before last line
        content = content.rstrip() + "\n" + MISSING_METHODS + "\norchestrator = OrchestratorAgent()\n"
        fix("Appended missing methods to orchestrator.py")

    write(orch_path, content)

    # Verify syntax
    import subprocess
    r = subprocess.run(["python3", "-m", "py_compile", str(orch_path)],
                      capture_output=True, text=True)
    if r.returncode == 0:
        ok("orchestrator.py syntax verified")
    else:
        err(f"Syntax error after patch: {r.stderr[:150]}")
        # Restore backup
        backup_file = BACKUP_DIR / "agents" / "orchestrator.py"
        if backup_file.exists():
            shutil.copy2(backup_file, orch_path)
            err("Restored backup — manual fix needed")


# ═══════════════════════════════════════════════════════════════════
# FIX 5: ADD TOOLS TO AI SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════

def fix_tools_in_prompt():
    h("FIX 5: TOOLS IN AI SYSTEM PROMPT")

    orch_path = ROOT / "agents" / "orchestrator.py"
    backup(orch_path)
    content = read(orch_path)

    if "AVAILABLE TOOLS" in content:
        ok("Tools already in AI system prompt")
        return

    tools_section = """
AVAILABLE TOOLS (gunakan ini untuk menjalankan tugas):
  - trading_tool: build/analyze/modify trading bots (Solana, CEX, DEX)
  - youtube_tool: build YouTube automation (upload, SEO, thumbnail, analytics)
  - video_studio_tool: generate video scripts, scenes, packages via AI
  - filesystem_tool: scan/read/write/run project files (REAL data, no hallucination)
  - openclaw_tool: check Solana token safety, market data, MCP operations
  - env_manager: detect, prompt, and write .env API keys for any project
  - repair_specialist: auto-repair broken projects (syntax, logic, imports)
  - workflow_engine: full build pipeline (plan → code → review → fix → save)

CARA EKSEKUSI TOOL:
  Ketik intent yang sesuai, orchestrator akan route ke tool yang tepat.
  Contoh: "buat trading bot" → trading_tool.build_trading_project()
  Contoh: "perbaiki godmeme" → repair_specialist.auto_repair_project()
  Contoh: "cek log" → filesystem_tool.read_log()
"""

    # Inject into chat() system prompt
    # Find the system prompt string and add tools section
    old_marker = "CARA USER BISA PASTE API KEY:"
    if old_marker in content:
        content = content.replace(old_marker, tools_section + "\n" + old_marker)
        fix("Tools section injected into chat() system prompt")
    else:
        # Find any system = f""" block
        old_projects_ctx = 'PROJECTS ({len(projects)} total):'
        if old_projects_ctx in content:
            content = content.replace(
                old_projects_ctx,
                tools_section + "\nPROJECTS ({len(projects)} total):"
            )
            fix("Tools section injected before PROJECTS context in system prompt")
        else:
            warn("Could not find exact injection point — tools section not added")
            return

    write(orch_path, content)
    ok("orchestrator.py updated with tools in AI prompt")


# ═══════════════════════════════════════════════════════════════════
# FIX 6: ROUTER MODEL SELECTION — prevent downgrade for complex tasks
# ═══════════════════════════════════════════════════════════════════

def fix_router_model():
    h("FIX 6: ROUTER MODEL SELECTION")

    router_path = ROOT / "core" / "router.py"
    if not router_path.exists():
        warn("core/router.py not found — skipping")
        return

    backup(router_path)
    content = read(router_path)

    # Check if it downgrades to gpt-5-mini for builds
    if "gpt-5-mini" in content:
        # Find the condition that triggers gpt-5-mini
        # We want: build/repair/trading tasks should use the main model, not mini
        new_logic = '''
def select_model(task_type: str, complexity: int = 5) -> str:
    """
    Select appropriate model based on task type and complexity.
    Build/repair/trading tasks ALWAYS use the full model.
    Only simple chat can use mini model.
    """
    import os
    main_model = os.getenv("OPENAI_MODEL", "qwen/qwen3-coder")
    mini_model = os.getenv("MINI_MODEL", main_model)  # default: same as main

    # Tasks that MUST use full model
    full_model_tasks = {
        "trading_build", "youtube_build", "general_build",
        "project_repair", "continue_project", "modify_strategy",
        "analysis", "code_generation", "repair"
    }

    if task_type in full_model_tasks:
        return main_model
    if complexity >= 7:
        return main_model

    # Only simple chat/inspect can use mini
    if task_type in ("chat", "inspect") and complexity < 5:
        return mini_model

    return main_model
'''
        if "def select_model" in content:
            # Replace existing select_model
            content = re.sub(
                r'def select_model\(.*?\n(?=\ndef |\nclass |\Z)',
                new_logic + "\n",
                content, flags=re.DOTALL
            )
            fix("Replaced select_model() — full model for build/repair tasks")
        else:
            content += "\n" + new_logic
            fix("Added select_model() to router.py")

        write(router_path, content)
        ok("Router updated — build tasks use full model")
    else:
        ok("Router model selection looks fine")


# ═══════════════════════════════════════════════════════════════════
# FIX 7: MISSING ENV VARS IN ROOT .env
# ═══════════════════════════════════════════════════════════════════

def fix_root_env():
    h("FIX 7: ROOT .env MISSING VARS")

    env_path = ROOT / ".env"
    backup(env_path)
    content = read(env_path)

    additions = []

    if "ANTHROPIC_API_KEY" not in content:
        additions.append("ANTHROPIC_API_KEY=")
        additions.append("ANTHROPIC_MODEL=claude-3-5-sonnet-20241022")

    if "CHROMA_PERSIST_DIR" not in content:
        additions.append("CHROMA_PERSIST_DIR=memory/chroma_db")

    if "MINI_MODEL" not in content:
        additions.append("MINI_MODEL=openai/gpt-4o-mini")

    if "MAX_REPAIR_ITERATIONS" not in content:
        additions.append("MAX_REPAIR_ITERATIONS=5")

    if "MAX_BUILD_ITERATIONS" not in content:
        additions.append("MAX_BUILD_ITERATIONS=10")

    if "EXECUTION_TIMEOUT" not in content:
        additions.append("EXECUTION_TIMEOUT=30")

    if additions:
        content = content.rstrip() + "\n\n# Added by agentjw_master_fix.py\n"
        content += "\n".join(additions) + "\n"
        write(env_path, content)
        fix(f"Added {len(additions)} vars to root .env: {additions}")
    else:
        ok("Root .env has all required vars")


# ═══════════════════════════════════════════════════════════════════
# FIX 8: PER-PROJECT .env DEFAULTS
# ═══════════════════════════════════════════════════════════════════

PROJECT_ENV_DEFAULTS = {
    "godmeme_bot": {
        "DATABASE_PATH": "projects/godmeme_bot/trading.db",
        "DASHBOARD_INTERVAL": "30",
        "IS_PAPER_TRADING": "true",
        "SOLANA_WS_URL": "wss://api.mainnet-beta.solana.com",
        "MAX_OPEN_POSITIONS": "5",
        "STOP_LOSS_PERCENT": "10",
        "TAKE_PROFIT_MULTIPLIER": "2.0",
        "SLIPPAGE_BPS": "100",
        "MIN_LIQUIDITY_USD": "10000",
        "DEFAULT_POSITION_SIZE_SOL": "0.1",
        "MAX_DAILY_LOSS_SOL": "1.0",
        "ENVIRONMENT": "production",
    },
    "youtube_clip_extractor": {
        "CLIPS_DIR": "output/clips",
        "OUTPUT_DIR": "output",
        "WHISPER_MODEL": "base",
        "DEFAULT_CLIP_DURATION": "60",
    },
    "youtube_full_suite": {
        "THUMBNAIL_FONT_PATH": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "THUMBNAIL_FONT_SIZE": "48",
        "COMMENT_DELAY_MAX": "300",
    },
}

def fix_project_envs():
    h("FIX 8: PER-PROJECT .env DEFAULTS")

    projects_dir = ROOT / "projects"
    if not projects_dir.exists():
        warn("projects/ dir not found")
        return

    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir():
            continue

        env_path = proj_dir / ".env"

        # Find matching defaults
        defaults = {}
        for key, vals in PROJECT_ENV_DEFAULTS.items():
            if key in proj_dir.name.lower():
                defaults.update(vals)

        if not defaults:
            continue

        # Read existing
        existing = {}
        if env_path.exists():
            for line in read(env_path).splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, _, v = line.partition("=")
                    existing[k.strip()] = v.strip()

        # Add missing defaults
        to_add = {k: v for k, v in defaults.items()
                  if k not in existing or not existing[k]}

        if to_add:
            backup(env_path)
            lines = []
            if env_path.exists():
                lines = read(env_path).splitlines()
            lines.append("")
            lines.append("# Defaults added by agentjw_master_fix.py")
            for k, v in to_add.items():
                lines.append(f"{k}={v}")
            write(env_path, "\n".join(lines) + "\n")
            fix(f"{proj_dir.name}/.env: added {len(to_add)} defaults")
        else:
            ok(f"{proj_dir.name}/.env: no defaults needed")


# ═══════════════════════════════════════════════════════════════════
# FIX 9: BRAIN INTENT DETECTION — ensure all orchestrator intents covered
# ═══════════════════════════════════════════════════════════════════

def fix_brain_intents():
    h("FIX 9: BRAIN INTENT COMPLETENESS")

    brain_path = ROOT / "agents" / "brain.py"
    if not brain_path.exists():
        err("brain.py not found!")
        return

    backup(brain_path)
    content = read(brain_path)

    # Required intents from orchestrator
    required_intents = [
        "inspect", "project_repair", "trading_build", "youtube_build",
        "analysis", "continue_project", "modify_strategy", "mcp_tool",
        "general_build", "run_project", "chat"
    ]

    # Check which are covered in brain.py
    missing_intents = []
    for intent in required_intents:
        if f'"{intent}"' not in content and f"'{intent}'" not in content:
            missing_intents.append(intent)

    if not missing_intents:
        ok("Brain covers all required intents")
        return

    warn(f"Brain missing intents: {missing_intents}")

    # Add or replace decide() function
    decide_func = '''

def decide(user_input: str) -> dict:
    """
    Brain decision — maps user input to orchestrator intent.
    Updated by agentjw_master_fix.py to cover all intents.
    """
    lower = user_input.lower()

    # ── Inspect / read / run ──────────────────────────────────────
    if any(k in lower for k in [
        "scan", "tampilkan", "lihat", "baca", "log", "cek log",
        "show", "read", "struktur", "hash", "list file", "status bot",
    ]):
        return {"intent": "inspect", "confidence": 0.95}

    # ── Run project ───────────────────────────────────────────────
    if any(k in lower for k in [
        "jalankan", "run bot", "python main", "start bot", "mulai bot",
        "execute", "run project",
    ]):
        return {"intent": "run_project", "confidence": 0.92}

    # ── Repair ───────────────────────────────────────────────────
    if any(k in lower for k in [
        "perbaiki", "fix", "repair", "debug", "benerin",
        "not working", "broken", "crash", "gagal", "rusak", "error",
        "tidak jalan", "tidak bisa",
    ]):
        return {"intent": "project_repair", "confidence": 0.9}

    # ── Trading build ─────────────────────────────────────────────
    if any(k in lower for k in [
        "trading bot", "trade bot", "crypto bot", "dex bot", "cex bot",
        "arbitrage", "grid bot", "scalping", "signal bot", "backtest",
        "binance bot", "bybit bot", "raydium", "jupiter", "sniper bot",
        "algo trading", "buat bot trading", "solana bot", "meme coin",
        "trading strategy",
    ]):
        return {"intent": "trading_build", "confidence": 0.9}

    # ── YouTube ───────────────────────────────────────────────────
    if any(k in lower for k in [
        "youtube", "upload youtube", "thumbnail", "youtube seo",
        "auto upload", "youtube analytics", "channel youtube",
        "video automation", "yt bot",
    ]):
        return {"intent": "youtube_build", "confidence": 0.9}

    # ── Analysis ──────────────────────────────────────────────────
    if any(k in lower for k in [
        "analisa", "analyze", "review strategi", "bedah",
        "evaluasi strategi", "audit kode", "gimana strategi",
        "cek project", "semua project",
    ]):
        return {"intent": "analysis", "confidence": 0.85}

    # ── Continue project ──────────────────────────────────────────
    if any(k in lower for k in [
        "lanjutkan", "continue", "resume", "teruskan",
        "lanjutin", "selesaikan", "tambahkan fitur",
    ]):
        return {"intent": "continue_project", "confidence": 0.85}

    # ── Modify strategy ───────────────────────────────────────────
    if any(k in lower for k in [
        "ubah strategi", "ganti logic", "modify strategy",
        "update strategi", "rubah logika", "edit strategy",
        "tambah stop loss", "ganti parameter",
    ]):
        return {"intent": "modify_strategy", "confidence": 0.85}

    # ── MCP tools ─────────────────────────────────────────────────
    if any(k in lower for k in [
        "check token", "cek token", "token safety", "market sentiment",
        "trading signal", "mcp tool", "trending token", "scan token",
    ]):
        return {"intent": "mcp_tool", "confidence": 0.85}

    # ── General build ─────────────────────────────────────────────
    if any(k in lower for k in [
        "buat", "build", "create", "generate", "buatkan",
        "bikin", "develop", "buat aplikasi", "buat script",
    ]):
        return {"intent": "general_build", "confidence": 0.7}

    # ── Default: chat ─────────────────────────────────────────────
    return {"intent": "chat", "confidence": 1.0}
'''

    # Replace existing decide() or add new one
    if "def decide" in content:
        content = re.sub(
            r'\ndef decide\(.*?\n(?=\ndef |\nclass |\Z)',
            decide_func + "\n",
            content, flags=re.DOTALL
        )
        fix("Replaced brain.decide() with complete version")
    else:
        content += decide_func
        fix("Added brain.decide() with all intents")

    write(brain_path, content)

    import subprocess
    r = subprocess.run(["python3", "-m", "py_compile", str(brain_path)],
                      capture_output=True, text=True)
    if r.returncode == 0:
        ok("brain.py syntax verified")
    else:
        err(f"Syntax error: {r.stderr[:150]}")


# ═══════════════════════════════════════════════════════════════════
# VERIFY ALL FIXES
# ═══════════════════════════════════════════════════════════════════

def verify():
    h("VERIFICATION")

    import subprocess
    files_to_check = [
        ROOT / "api_server.py",
        ROOT / "agents" / "orchestrator.py",
        ROOT / "agents" / "brain.py",
        ROOT / "core" / "config.py",
    ]

    all_ok = True
    for f in files_to_check:
        if not f.exists():
            err(f"Missing: {f.name}")
            all_ok = False
            continue
        r = subprocess.run(["python3", "-m", "py_compile", str(f)],
                          capture_output=True, text=True)
        if r.returncode == 0:
            ok(f"Syntax OK: {f.relative_to(ROOT)}")
        else:
            err(f"Syntax error: {f.relative_to(ROOT)}: {r.stderr[:100]}")
            all_ok = False

    return all_ok


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    try:
        from rich.console import Console
        c = Console()
        c.print("\n[bold cyan]╔══════════════════════════════════════════════╗[/bold cyan]")
        c.print("[bold cyan]║  🔧  AgentJW Master Fix                     ║[/bold cyan]")
        c.print("[bold cyan]╚══════════════════════════════════════════════╝[/bold cyan]")
    except:
        print("\n╔══════════════════════════════════════════════╗")
        print("║  🔧  AgentJW Master Fix                     ║")
        print("╚══════════════════════════════════════════════╝")

    print(f"\nBackup dir: {BACKUP_DIR}")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    fix_port()
    fix_endpoints()
    fix_orchestrator_methods()
    fix_tools_in_prompt()
    fix_router_model()
    fix_root_env()
    fix_project_envs()
    fix_brain_intents()
    all_ok = verify()

    h("DONE")
    if all_ok:
        print("""
✅ All fixes applied! Now restart API server:

  pkill -f uvicorn
  cd ~/agentjw
  nohup uvicorn api_server:app --host 0.0.0.0 --port 18790 > api.log 2>&1 &
  sleep 2 && curl -s http://localhost:18790/api/status

Then re-run analyzer to verify score:
  python3 agentjw_sync_analyzer.py
""")
    else:
        print("""
⚠️  Some files have syntax errors — check above.
Backups saved in: """ + str(BACKUP_DIR))


if __name__ == "__main__":
    main()
