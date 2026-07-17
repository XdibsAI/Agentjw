import uuid
import json
from sicuan.adapters.project_adapter import get_project_adapter
from pathlib import Path
from typing import Dict, List, Optional
from rich.panel import Panel
from rich.table import Table

from core.config import config
from core.models import BuildSession, TaskStatus
from core.logger import logger, console
from memory.memory_store import memory_store
from tools.project_manager.manager import project_manager
from agents.brain import brain
from tools.video.video_renderer import video_renderer_tool


class OrchestratorAgent:

    def __init__(self):
        self._fs = None
        self.pending_actions = {}  # session_id -> pending action dict

    @property
    def fs(self):
        if self._fs is None:
            from mcp.tools.filesystem_tool import filesystem_tool
            self._fs = filesystem_tool
        return self._fs

    def execute(self, user_input: str, chat_history: List[Dict], session_id: str) -> Dict:
        decision = brain.decide(user_input, chat_history)
        action = decision.get("action", "chat")
        target_project = decision.get("target_project")
        target_file = decision.get("target_file")
        params = decision.get("params", {})

        console.print("[dim]Brain: " + action + " | file=" + str(target_file) + " | project=" + str(target_project) + "[/dim]")

        adapter = get_project_adapter()
        projects = adapter.get_projects()
        proj = brain.resolve_project(target_project, projects)

        if action == "read_file":
            return self._read_file(target_file, proj)

        elif action == "scan_project":
            pd = proj["project_dir"] if proj else ""
            self._show_scan(self.fs.scan_project(pd))
            return {"status": "done"}

        elif action == "show_log":
            pd = proj["project_dir"] if proj else ""
            data = self.fs.read_log(pd, lines=50)
            console.print(Panel(json.dumps(data, indent=2, default=str)[:3000], title="Real Log", border_style="cyan"))
            return {"status": "done"}

        elif action == "run_project":
            pd = proj["project_dir"] if proj else ""
            console.print("[cyan]Running (10s)...[/cyan]")
            result = self.fs.run_and_capture(pd, timeout=10)
            console.print(Panel(json.dumps(result, indent=2, default=str)[:2000], title="Real Output", border_style="green"))
            try:
                from mcp.tools.openclaw_tool import notify_bot_status
                notify_bot_status(proj["name"] if proj else "bot", result.get("stdout", ""), result.get("success", False))
            except Exception:
                pass
            return {"status": "done"}

        elif action == "build_trading":
            return self._build_trading(user_input, session_id)

        elif action == "build_youtube":
            return self._build_youtube(user_input, session_id)

        elif action == "build_general":
            return self._build_general(user_input, session_id)

        elif action == "repair":
            if not proj:
                project_manager.display_all_projects()
                return {"status": "needs_selection"}
            from agents.specialist.repair_specialist import repair_specialist
            result = repair_specialist.auto_repair_project(proj["id"], deep=True)
            try:
                from mcp.tools.openclaw_tool import notify_repair_done
                notify_repair_done(proj["name"], result.get("repaired", []), result.get("failed", []))
            except Exception:
                pass
            return result

        elif action == "analyze":
            if not proj:
                return {"status": "no_project"}
            from tools.trading.trading_tool import trading_tool
            analysis = trading_tool.analyze_strategy(proj["id"], user_input)
            console.print(Panel(analysis, title="Analysis", border_style="cyan"))
            return {"status": "done"}

        elif action == "continue":
            if not proj:
                return {"status": "no_project"}
            from agents.specialist.repair_specialist import repair_specialist
            files = repair_specialist.continue_project(proj["id"], user_input)
            console.print("[green]Continued: " + str(len(files)) + " files[/green]")
            return {"status": "done"}

        elif action == "modify":
            if not proj:
                return {"status": "no_project"}
            from tools.trading.trading_tool import trading_tool
            files = trading_tool.modify_strategy(proj["id"], user_input)
            console.print("[green]Modified " + str(len(files)) + " files[/green]")
            return {"status": "done"}

        elif action == "mcp_token":
            addr = params.get("address", user_input.split()[-1])
            from mcp.mcp_client import mcp_client
            result = mcp_client._execute_tool("solana_check_rug", {"token_address": addr})
            console.print(Panel(json.dumps(result, indent=2, default=str), title="Token Safety", border_style="yellow"))
            return result

        elif action == "mcp_trending":
            from mcp.mcp_client import mcp_client
            result = mcp_client._execute_tool("market_get_trending", {"chain": "solana", "limit": 10})
            console.print(Panel(json.dumps(result, indent=2, default=str)[:2000], title="Trending", border_style="yellow"))
            return result

        else:
            return {"action": "chat"}

    def _read_file(self, filename: Optional[str], proj: Optional[Dict]) -> Dict:
        if not filename:
            console.print("[yellow]File mana? Contoh: tampilkan kode main.py[/yellow]")
            return {"status": "needs_filename"}

        fp = None
        if proj:
            candidate = Path(proj["project_dir"]) / filename
            if candidate.exists():
                fp = str(candidate)
        if not fp and Path(filename).exists():
            fp = filename
        if not fp:
            console.print("[yellow]File tidak ditemukan: " + filename + "[/yellow]")
            if proj:
                files = list(Path(proj["project_dir"]).glob("*.py"))
                console.print("[dim]File tersedia: " + ", ".join(f.name for f in files) + "[/dim]")
            return {"status": "not_found"}

        data = self.fs.read_file(fp)
        if "error" in data:
            console.print("[red]" + data["error"] + "[/red]")
            return {"status": "error"}

        lines = data["content"].splitlines()
        display = "\n".join(lines[:80])
        title = filename + " | " + str(data["lines"]) + " lines | " + str(data["size_bytes"] // 1024) + "KB | sha256:" + data["sha256"][:16]
        console.print(Panel(display, title=title, border_style="cyan"))
        if data["lines"] > 80:
            console.print("[dim]... " + str(data["lines"] - 80) + " more lines[/dim]")
        return {"status": "done"}

    def _build_trading(self, user_request: str, session_id: str) -> Dict:
        from tools.trading.trading_tool import trading_tool
        existing = adapter.get_projects()
        if existing:
            console.print("[yellow]Existing trading projects: " + str(len(existing)) + "[/yellow]")
        console.print(Panel("TRADING BOT BUILDER", border_style="yellow"))
        files = (trading_tool.build_trading_project_detailed(user_request)
                 if len(user_request) > 300 else trading_tool.build_trading_project(user_request))
        intent_data = trading_tool.detect_trading_intent(user_request)
        project_name = "trading_" + intent_data["template"] + "_" + session_id[:4]
        project_dir = config.PROJECTS_DIR / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            fp = project_dir / f.path
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(f.content)
        pid = project_manager.register_project(
            name=project_name, description=user_request,
            project_dir=str(project_dir), tool_type="trading",
            tasks=["Configure API keys", "Paper trading test", "Enable live trading"],
        )
        project_manager.save_files(pid, files)
        from runtime.ast_validator import ast_validator
        valid = sum(1 for f in files if f.language == "python" and ast_validator.validate_python(f.content)[0])
        project_manager.set_status(pid, "success")
        try:
            from mcp.tools.openclaw_tool import notify_build_done
            notify_build_done(project_name, "success", pid)
        except Exception:
            pass
        console.print(Panel("Done!\nDir: " + str(project_dir) + "\nID: " + pid + "\nFiles: " + str(len(files)) + " | Valid: " + str(valid), title="Trading Bot", border_style="yellow"))
        return {"status": "success", "project_id": pid, "project_dir": str(project_dir)}

    def _build_youtube(self, user_request: str, session_id: str) -> Dict:
        from tools.youtube.youtube_tool import youtube_tool
        files = youtube_tool.build_youtube_tools(user_request)
        intent_data = youtube_tool.detect_youtube_intent(user_request)
        project_name = "youtube_" + intent_data["template"] + "_" + session_id[:4]
        project_dir = config.PROJECTS_DIR / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        for f in files:
            (project_dir / f.path).write_text(f.content)
        pid = project_manager.register_project(name=project_name, description=user_request, project_dir=str(project_dir), tool_type="youtube")
        project_manager.save_files(pid, files)
        project_manager.set_status(pid, "success")
        console.print("[green]YouTube: " + str(project_dir) + " [" + pid + "][/green]")
        return {"status": "success", "project_id": pid}

    def _build_general(self, user_request: str, session_id: str) -> Dict:
        from agents.workflow.workflow_engine import workflow_engine
        return workflow_engine.run(user_request, session_id=session_id)


    def chat(self, user_message: str, history: List[Dict], session_id: str) -> str:
        from core.llm_client import llm
        from agents.memory_agent import memory_agent

        lower = user_message.lower()

        pending = self.get_pending(session_id)

        if pending:
            if lower.strip() in ["lanjut", "ok", "ya", "yes"]:
                payload = pending.get("payload", {})

                if pending.get("type") == "video_build":
                    self.clear_pending(session_id)
                    return str(
                        self._build_video(
                            payload.get("prompt", ""),
                            session_id
                        )
                    )

        # ── Check if user is pasting env vars ──────────────────────────────
        env_result = self._handle_env_paste(user_message, session_id)
        if env_result:
            keys = env_result.get("keys_saved", [])
            return (
                f"✅ Disimpan {len(keys)} variabel ke {env_result['project']}/.env:\n"
                + "\n".join(f"  • {k}" for k in keys)
                + "\n\nBot siap dijalankan. Ketik: `jalankan` untuk start."
            )

        # ── Build rich project context ──────────────────────────────────────
        adapter = get_project_adapter()
        projects = adapter.get_projects()
        proj_ctx = ""
        real_data = ""

        if projects:
            proj_lines = []
            for p in projects:
                env_path = Path(p["project_dir"]) / ".env"
                has_env = env_path.exists()
                env_complete = False
                if has_env:
                    try:
                        from tools.env_manager import env_manager
                        required = env_manager.scan_required_vars(p["project_dir"])
                        existing = env_manager.read_env_file(env_path)
                        missing = [v for v in required if not existing.get(v)]
                        env_complete = len(missing) == 0
                        env_status = f"✅ lengkap" if env_complete else f"⚠️  missing: {missing[:3]}"
                    except Exception:
                        env_status = "exists"
                else:
                    env_status = "❌ tidak ada"

                proj_lines.append(
                    f"- [{p['id']}] {p['name']} | {p['status']} | {p.get('tool_type', 'general')} "
                    f"| .env: {env_status} | {p.get('created_at', 'N/A')[:10]}"
                )
            proj_ctx = "\n".join(proj_lines)

            # Inject real file data for relevant questions
            file_keywords = [
                "log", "isi file", "tampilkan", "baca", "struktur",
                "hash", "sha256", "roi", "profit", "loss", "balance",
                "trade", "transaksi", "file", "kode", "status", "error"
            ]
            if any(k in lower for k in file_keywords):
                target = self._find_project_ref(user_message, projects) or projects[0]
                try:
                    scan = self.fs.scan_project(target["project_dir"])
                    logs = self.fs.read_log(target["project_dir"], lines=20)
                    real_data = f"""
REAL DATA — {target['name']} (from disk: {target['project_dir']}):
Files: {[f['name'] for f in scan.get('python_files',[])]}
Valid syntax: {scan.get('valid_syntax',0)}/{scan.get('total_py',0)}
Size: {scan.get('total_size_kb',0)}KB
.env: {'exists' if scan.get('has_env') else 'MISSING'}
RECENT LOG:
{str(logs.get('content','') if isinstance(logs,dict) else logs)[:800]}
"""
                except Exception as e:
                    real_data = f"(scan failed: {e})"

        mem = memory_agent.run({"action": "retrieve", "query": user_message, "limit": 3})
        snippets = mem.get("snippets", [])

        chat_ctx = ""
        if history and len(history) > 2:
            for msg in history[-4:]:
                role = "You" if msg["role"] == "assistant" else "User"
                chat_ctx += f"{role}: {msg['content'][:150]}\n"

        system = f"""Kamu adalah AgentJW — autonomous AI engineer GOD MODE.
Kamu PROAKTIF: jika project butuh API key atau config, langsung minta dan tulis ke .env.
Kamu TIDAK minta user copy-paste perintah manual jika bisa dilakukan sendiri.

STRICT RULES:
1. JANGAN fabrikasi data, angka ROI, profit, atau hash
2. Jawab berdasarkan REAL PROJECT DATA di bawah
3. Jika data tidak tersedia: "Data tidak tersedia. Ketik: scan [nama project]"
4. Untuk trading performance: HANYA dari log files nyata
5. Jika project butuh API key → tampilkan template .env dan minta user paste nilainya

PROJECTS ({len(projects)} total):
{proj_ctx}
{real_data}

THINGS YOU REMEMBER ABOUT THIS USER/PROJECT (from past conversations):
{chr(10).join(f"- {s}" for s in snippets) if snippets else "(belum ada memori relevan)"}

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

CARA USER BISA PASTE API KEY:
User cukup ketik: NAMA_KEY=nilainya
AgentJW akan simpan otomatis ke .env project terkait.

RECENT CHAT:
{chat_ctx}"""


        messages = [{"role": m["role"], "content": m["content"]} for m in history[-8:]]
        messages.append({"role": "user", "content": user_message})
        response = llm.chat(messages=messages, system=system, temperature=0.7, max_tokens=2048)
        memory_store.save_chat(session_id, "user", user_message)
        memory_store.save_chat(session_id, "assistant", response)

        # ── Second brain: extract & store durable facts from this turn ─────
        try:
            memory_agent.run({
                "action": "extract_and_store",
                "session_summary": f"User: {user_message}\nAssistant: {response[:1000]}",
                "success": True,
                "project_name": session_id,
            })
        except Exception as e:
            console.print(f"[dim]Memory extraction skipped: {e}[/dim]")

        return response


    def set_pending(self, session_id, action_type, payload):
        self.pending_actions[session_id] = {
            "type": action_type,
            "payload": payload
        }

    def get_pending(self, session_id):
        return self.pending_actions.get(session_id)

    def clear_pending(self, session_id):
        self.pending_actions.pop(session_id, None)



    def smart_build(self, user_request: str, session_id: str = None) -> Dict:
        session_id = session_id or str(uuid.uuid4())

        # ── Check if user is pasting env vars ──────────────────────────────
        env_result = self._handle_env_paste(user_request, session_id)
        if env_result:
            return env_result

        intent = self.route_intent(user_request)
        console.print(f"[dim]→ {intent['type']} ({intent['confidence']})[/dim]")

        handlers = {
            "inspect":         self._inspect_action,
            "project_repair":  self._repair_existing,
            "trading_build":   self._build_trading,
            "youtube_build":   self._build_youtube,
            "analysis":        self._analyze_project,
            "continue_project":self._continue_project,
            "modify_strategy": self._modify_strategy,
            "run_project":     self._run_project,
            "mcp_tool":        self._mcp_action,
            "general_build":   self._general_build,
            "render_video":    self._render_video,
        }
        handler = handlers.get(intent["type"])
        if handler:
            result = handler(user_request, session_id) if intent["type"] not in (
                "inspect", "run_project", "mcp_tool"
            ) else handler(user_request)

            # ── Post-build: proactive env check ────────────────────────────
            if intent["type"].endswith("_build") or intent["type"] in ("general_build", "continue_project"):
                if isinstance(result, dict) and result.get("project_dir"):
                    env_msg = self._post_build_env_check(
                        result["project_dir"],
                        result.get("project_name", ""),
                        session_id
                    )
                    if env_msg:
                        result["env_setup_message"] = env_msg
                        # Show in console too
                        console.print(Panel(env_msg[:600], title="🔑 Setup API Keys", border_style="yellow"))

            return result

        return {"type": "chat"}


    def route_intent(self, user_input: str) -> Dict:
        lower = user_input.lower()
        render_keywords = [
            "render video", "jadikan video", "generate video file",
            "buatkan videonya", "render videonya", "convert ke video",
            "render final video", "lanjut render",
        ]
        if any(k in lower for k in render_keywords):
            return {"type": "render_video", "confidence": 0.92}
        return {"type": "chat", "confidence": 0.5}

    def build(self, user_request: str, session_id: str = None) -> BuildSession:
        result = self.smart_build(user_request, session_id)
        session = BuildSession(session_id=session_id or str(uuid.uuid4()), user_request=user_request)
        session.status = TaskStatus.SUCCESS if result.get("status") == "success" else TaskStatus.FAILED
        return session

    def _show_scan(self, data: Dict):
        if "error" in data:
            console.print("[red]" + data["error"] + "[/red]")
            return
        table = Table(title="📁 " + Path(data["project_dir"]).name + " (real data)", border_style="cyan")
        table.add_column("File", style="green", width=26)
        table.add_column("KB", width=6)
        table.add_column("Lines", width=7)
        table.add_column("Syntax", width=10)
        table.add_column("Hash", style="dim", width=14)
        for f in data["python_files"]:
            ok = f.get("syntax_ok", False)
            status = "[green]✓[/green]" if ok else "[red]✗[/red]"
            table.add_row(f["name"], str(f.get("size_kb", 0)), str(f.get("lines", 0)), status, f.get("sha256_short", "?"))
        console.print(table)
        console.print("[cyan]Valid:[/cyan] " + str(data["valid_syntax"]) + "/" + str(data["total_py"]) + " | [cyan]Size:[/cyan] " + str(data["total_size_kb"]) + "KB | [cyan].env:[/cyan] " + ("✓" if data["has_env"] else "✗"))


    def _build_video(self, user_request: str, session_id: str) -> Dict:
        """Build full video production package via Video Studio"""
        from tools.video.video_studio_tool import video_studio_tool
        from core.config import config

        if not config.has_video_studio():
            console.print(
                "[red]❌ Video Studio requires OPENROUTER_API_KEY in .env[/red]\n"
                "[yellow]Add: OPENROUTER_API_KEY=sk-or-v1-...[/yellow]"
            )
            return {"status": "error", "reason": "OPENROUTER_API_KEY not set"}

        console.print(Panel("🎬 VIDEO STUDIO MODE", border_style="red"))
        package = video_studio_tool.build_video_package(user_request)

        project_name = f"video_{session_id[:6]}"
        project_dir = config.PROJECTS_DIR / project_name
        saved_files = video_studio_tool.save_package(package, project_dir)

        from core.models import CodeFile as CF
        pid = project_manager.register_project(
            name=project_name,
            description=user_request[:200],
            project_dir=str(project_dir),
            tool_type="youtube",
            tasks=["Review script", "Generate Higgsfield visuals",
                   "Record ElevenLabs VO", "Edit video", "Upload to YouTube"],
            metadata={"package_id": package["id"], "video_studio": True},
        )
        project_manager.save_files(pid, [
            CF(path=f.name,
               content=f.read_text(encoding="utf-8"),
               language="text",
               description=f"Video: {f.stem}")
            for f in saved_files
            if f.suffix in (".txt", ".json", ".md")
        ])
        project_manager.set_status(pid, "success")
        video_studio_tool.display_package_summary(package, project_dir)
        return {
            "status": "success",
            "project_id": pid,
            "project_dir": str(project_dir),
            "package_id": package["id"],
        }


    def _build_video(self, user_request: str, session_id: str) -> Dict:
        """Build full video production package via Video Studio"""
        from tools.video.video_studio_tool import video_studio_tool
        from core.config import config

        if not config.has_video_studio():
            console.print(
                "[red]❌ Video Studio memerlukan OPENROUTER_API_KEY di .env[/red]\n"
                "[yellow]Tambahkan: OPENROUTER_API_KEY=sk-or-v1-...[/yellow]"
            )
            return {"status": "error", "reason": "OPENROUTER_API_KEY not set"}

        console.print(Panel("🎬 VIDEO STUDIO MODE", border_style="red"))
        package = video_studio_tool.build_video_package(user_request)

        project_name = f"video_{session_id[:6]}"
        project_dir = config.PROJECTS_DIR / project_name
        saved_files = video_studio_tool.save_package(package, project_dir)

        from core.models import CodeFile as CF
        pid = project_manager.register_project(
            name=project_name,
            description=user_request[:200],
            project_dir=str(project_dir),
            tool_type="youtube",
            tasks=["Review script", "Generate Higgsfield visuals",
                   "Record ElevenLabs VO", "Edit video", "Upload YouTube"],
            metadata={"package_id": package["id"], "video_studio": True},
        )
        project_manager.save_files(pid, [
            CF(path=f.name,
               content=f.read_text(encoding="utf-8"),
               language="text",
               description=f"Video: {f.stem}")
            for f in saved_files
            if f.suffix in (".txt", ".json", ".md")
        ])
        project_manager.set_status(pid, "success")
        video_studio_tool.display_package_summary(package, project_dir)
        return {
            "status": "success",
            "project_id": pid,
            "project_dir": str(project_dir),
            "package_id": package["id"],
        }


    # ═══════════════════════════════════════════
    # PROACTIVE ENV SETUP (inject after any build)
    # ═══════════════════════════════════════════
    def _post_build_env_check(self, project_dir: str, project_name: str, session_id: str) -> str:
        """
        After building a project, check for missing env vars.
        In CLI mode: interactive prompt.
        In API mode (from APK): return template string.
        Returns message to show user.
        """
        try:
            from tools.env_manager import env_manager
            import os

            # Detect if running interactively (CLI) or via API
            is_interactive = os.isatty(0) if hasattr(os, "isatty") else False

            if is_interactive:
                filled = env_manager.check_and_prompt(project_dir, project_name)
                if filled:
                    return f"✅ {len(filled)} API keys disimpan ke .env"
                return ""
            else:
                # API mode: return template for user to fill
                template = env_manager.generate_env_template(project_dir)
                missing_count = template.count("⚠")
                if missing_count > 0:
                    return (
                        f"\n\n📋 **Setup Required** — {missing_count} env vars perlu diisi:\n"
                        f"```\n{template[:800]}\n```\n"
                        f"Paste API keys ke chat, format:\n"
                        f"`NAMA_VAR=nilai_kamu`\n"
                        f"AgentJW akan simpan otomatis ke .env"
                    )
                return ""
        except Exception as e:
            logger.warning(f"post_build_env_check failed: {e}")
            return ""

    def _handle_env_paste(self, user_input: str, session_id: str) -> Optional[Dict]:
        """
        Detect if user pasted env var values like KEY=value.
        Auto-save to the most recent project .env.
        Returns result dict if handled, None otherwise.
        """
        import re
        lines = user_input.strip().splitlines()
        env_pairs = {}
        for line in lines:
            line = line.strip()
            m = re.match(r'^([A-Z][A-Z0-9_]{2,})\s*=\s*(.+)$', line)
            if m:
                env_pairs[m.group(1)] = m.group(2).strip()

        if not env_pairs:
            return None

        # Find target project
        adapter = get_project_adapter()
        projects = adapter.get_projects()
        if not projects:
            return None

        proj = self._find_project_ref(user_input, projects) or projects[0]
        env_path = Path(proj["project_dir"]) / ".env"

        try:
            from tools.env_manager import env_manager
            existing = env_manager.read_env_file(env_path)
            existing.update(env_pairs)
            env_manager.write_env_file(env_path, existing)

            keys_saved = list(env_pairs.keys())
            console.print(Panel(
                f"[green]✅ {len(keys_saved)} variabel disimpan ke {proj['name']}/.env[/green]\n"
                + "\n".join(f"  • {k}" for k in keys_saved),
                title="💾 .env Updated",
                border_style="green"
            ))
            return {
                "status": "env_saved",
                "project": proj["name"],
                "keys_saved": keys_saved,
                "env_path": str(env_path),
            }
        except Exception as e:
            logger.error(f"env paste save failed: {e}")
            return None

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
        adapter = get_project_adapter()
        projects = adapter.get_projects()
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
        adapter = get_project_adapter()
        projects = adapter.get_projects()
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
                    "\n".join(lines),
                    title=f"📄 {fname} (real file)",
                    border_style="cyan"
                ))
            else:
                self._show_json(f"📄 {fname}", data)
        else:
            data = self.fs.scan_project(pd)
            self._show_scan(data)

        return {"status": "done", "project_id": proj["id"]}

    def _render_video(self, user_request: str, session_id: str) -> Dict:
        """Render final_video.mp4 from the most recent (or referenced) video project."""
        import json

        adapter = get_project_adapter()
        adapter = get_project_adapter()
        projects = adapter.get_projects()
        video_projects = [p for p in projects if p["name"].startswith("video_")]
        if not video_projects:
            return {"status": "error", "reason": "Belum ada project video. Generate dulu dengan 'buat video ...'"}

        proj = self._find_project_ref(user_request, video_projects) or video_projects[0]
        project_dir = Path(proj["project_dir"])
        package_path = project_dir / "video_package.json"
        if not package_path.exists():
            return {"status": "error", "reason": f"video_package.json tidak ditemukan di {project_dir}"}

        package = json.loads(package_path.read_text(encoding="utf-8"))
        console.print(Panel(f"🎬 RENDERING VIDEO: {proj['name']}", border_style="magenta"))
        try:
            out_path = video_renderer_tool.render(package, project_dir)
        except Exception as e:
            return {"status": "error", "reason": f"Render gagal: {e}"}

        project_manager.set_status(proj["id"], "success")
        return {
            "status": "success",
            "project_id": proj["id"],
            "project_dir": str(project_dir),
            "video_path": str(out_path),
        }

    def _run_project(self, user_request: str) -> Dict:
        """Run a project and capture output"""
        adapter = get_project_adapter()
        adapter = get_project_adapter()
        projects = adapter.get_projects()
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

orchestrator = OrchestratorAgent()