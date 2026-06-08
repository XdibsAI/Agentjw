import uuid
import json
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


class OrchestratorAgent:

    def __init__(self):
        self._fs = None

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

        projects = memory_store.list_projects()
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
        existing = memory_store.list_projects(tool_type="trading")
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

        projects = memory_store.list_projects()
        real_data = ""
        if projects:
            proj = projects[0]
            scan = self.fs.scan_project(proj["project_dir"])
            logs = self.fs.read_log(proj["project_dir"], lines=10)
            real_data = (
                "\nREAL PROJECT DATA (from disk):\n"
                "Project: " + proj["name"] + "\n"
                "Files: " + str([f["name"] for f in scan.get("python_files", [])]) + "\n"
                "Valid: " + str(scan.get("valid_syntax", 0)) + "/" + str(scan.get("total_py", 0)) + "\n"
                "Logs: " + (str(logs)[:300] if logs and "error" not in str(logs) else "no logs") + "\n"
            )

        proj_ctx = "\n".join("[" + p["id"] + "] " + p["name"] + " | " + p["status"] for p in projects)
        chat_ctx = ""
        if history:
            for msg in history[-4:]:
                chat_ctx += ("User" if msg["role"] == "user" else "You") + ": " + msg["content"][:100] + "\n"

        mem = memory_agent.run({"action": "retrieve", "query": user_message, "limit": 3})
        snippets = mem.get("snippets", [])
        project_hits = mem.get("project_hits", [])

        system = (
            "You are AgentJW, GOD MODE autonomous AI software engineer.\n\n"
            "RULES:\n"
            "1. NEVER fabricate file contents, ROI, profits, hashes\n"
            "2. Only state what is in REAL PROJECT DATA\n"
            "3. If file content exists in PROJECT CONTEXT, explain it directly. Only ask for tampilkan kode when file content is unavailable\n"
            "4. If performance data not in logs: say 'Bot running in paper mode, no real trades yet'\n\n"
            "PROJECTS:\n" + proj_ctx + "\n"
            + real_data + "\nCHAT:\n" + chat_ctx
        )
        if snippets:
            system += "\nMEMORY:\n" + "\n".join("- " + s[:100] for s in snippets)

        if project_hits:

            system += "\n\nPROJECT CONTEXT:\n"

            for hit in project_hits[:3]:

                system += (
                    f"\nFILE: {hit['path']}\n"
                    f"{hit['content'][:1200]}\n"
                )

        messages = [{"role": m["role"], "content": m["content"]} for m in history[-8:]]
        messages.append({"role": "user", "content": user_message})
        response = llm.chat(messages=messages, system=system, temperature=0.7, max_tokens=2048)
        memory_store.save_chat(session_id, "user", user_message)
        memory_store.save_chat(session_id, "assistant", response)
        return response

    def smart_build(self, user_request: str, session_id: str = None) -> Dict:
        session_id = session_id or str(uuid.uuid4())
        return self.execute(user_request, [], session_id)

    def route_intent(self, user_input: str) -> Dict:
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


orchestrator = OrchestratorAgent()
