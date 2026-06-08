import sys
import uuid
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from core.config import config
from core.logger import logger, console
from memory.memory_store import memory_store
from tools.project_manager.manager import project_manager

PROMPT_STYLE = Style.from_dict({"prompt": "#00bcd4 bold", "": "#ffffff"})

BANNER = "\n╔══════════════════════════════════════════════════════╗\n║  🤖  A G E N T J W  ⚡  G O D  M O D E             ║\n║  Think · Plan · Build · Repair · Evolve · Remember  ║\n╚══════════════════════════════════════════════════════╝"


class CLI:
    def __init__(self):
        from interface.session import get_or_create_session_id
        self.session_id = get_or_create_session_id()
        self.chat_history = []
        try:
            saved = memory_store.get_chat_history(self.session_id, limit=20)
            if saved:
                self.chat_history = saved
        except Exception:
            pass
        history_file = config.LOGS_DIR / ".cli_history"
        history_file.parent.mkdir(parents=True, exist_ok=True)
        self.prompt_session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            style=PROMPT_STYLE,
        )

    def run(self):
        config.ensure_dirs()
        console.print("[bold cyan]" + BANNER + "[/bold cyan]")
        projects = memory_store.list_projects()
        msgs = len(self.chat_history)
        console.print("[dim]Session: " + self.session_id[:8] + " | Model: " + config.get_model() + " | Projects: " + str(len(projects)) + " | Messages: " + str(msgs) + "[/dim]")
        if msgs > 0:
            console.print("[dim]Loaded " + str(msgs) + " previous messages[/dim]")
        console.print("\nJust type naturally. Type [green]help[/green] for commands.\n")
        while True:
            try:
                user_input = self.prompt_session.prompt("⚡ agentjw > ", style=PROMPT_STYLE).strip()
                if not user_input:
                    continue
                self._handle(user_input)
            except KeyboardInterrupt:
                console.print("\n[yellow]Ctrl+C - type exit to quit[/yellow]")
            except EOFError:
                self._exit()
            except Exception as e:
                console.print("[red]Error: " + str(e) + "[/red]")
                logger.exception("CLI error")

    def _handle(self, inp):
        lower = inp.lower().strip()
        if lower in ("exit", "quit", "q"):
            self._exit()
        elif lower == "help":
            self._show_help()
        elif lower == "status":
            self._show_status()
        elif lower == "memory":
            self._show_memory()
        elif lower == "reset memory":
            memory_store.clear_all()
            self.chat_history = []
            console.print("[yellow]Memory cleared[/yellow]")
        elif lower == "projects":
            project_manager.display_all_projects()
        elif lower == "worklog":
            project_manager.display_work_log()
        elif lower.startswith("worklog "):
            project_manager.display_work_log(inp[8:].strip())
        elif lower.startswith("project "):
            project_manager.display_project(inp[8:].strip())
        elif lower == "mcp tools":
            from mcp.mcp_client import mcp_client
            mcp_client.display_tools()
        else:
            self._brain_execute(inp)

    def _brain_execute(self, user_input):
        try:
            from agents.orchestrator import orchestrator
            result = orchestrator.execute(user_input, self.chat_history, self.session_id)
            if not result or result.get("action") == "chat" or result.get("status") not in ("done", "success"):
                response = orchestrator.chat(user_input, self.chat_history, self.session_id)
                self.chat_history.append({"role": "user", "content": user_input})
                self.chat_history.append({"role": "assistant", "content": response})
                if len(self.chat_history) > 30:
                    self.chat_history = self.chat_history[-30:]
                console.print(Panel(Text(response), title="[cyan]AgentJW[/cyan]", border_style="cyan"))
        except Exception as e:
            console.print("[red]Error: " + str(e) + "[/red]")
            logger.exception("Brain execute failed")

    def _show_help(self):
        help_lines = [
            "[bold cyan]AgentJW GOD MODE - Just type naturally![/bold cyan]",
            "",
            "[cyan]Examples:[/cyan]",
            "  tampilkan kode main.py",
            "  baca strategy.py",
            "  tampilkan log",
            "  jalankan bot",
            "  perbaiki bot",
            "  buat trading bot solana meme coin",
            "  analisa strategi",
            "  ubah strategi, tambah trailing stop",
            "  check token <address>",
            "",
            "[cyan]System:[/cyan]",
            "  projects | worklog | status | memory",
            "  mcp tools | reset memory | help | exit",
        ]
        console.print(Panel("\n".join(help_lines), title="Help", border_style="cyan"))

    def _show_status(self):
        projects = memory_store.list_projects()
        table = Table(title="AgentJW Status", border_style="cyan")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("Model", config.get_model())
        table.add_row("Provider", config.LLM_PROVIDER)
        table.add_row("Session", self.session_id[:16] + "...")
        table.add_row("Chat messages", str(len(self.chat_history)))
        table.add_row("Total projects", str(len(projects)))
        table.add_row("Projects dir", str(config.PROJECTS_DIR))
        table.add_row("Memory DB", str(config.SQLITE_PATH))
        console.print(table)

    def _show_memory(self):
        memories = memory_store.recall(limit=10)
        if not memories:
            console.print("[dim]Memory empty[/dim]")
            return
        table = Table(title="Memory", border_style="magenta")
        table.add_column("Type", style="magenta", width=12)
        table.add_column("Content", style="white")
        table.add_column("Imp", style="yellow", width=5)
        for m in memories:
            table.add_row(m["type"], m["content"][:70], str(round(m["importance"], 1)))
        console.print(table)


    def _run_video_build(self, topic: str):
        if not topic:
            console.print("[yellow]Usage: video <topic>[/yellow]")
            return
        try:
            from agents.orchestrator import orchestrator
            orchestrator._build_video(topic, self.session_id)
        except Exception as e:
            console.print(f"[red]Video Studio error: {e}[/red]")
            logger.exception("Video build failed")

    def _run_video_section(self, section: str, topic: str):
        valid = ["script", "scenes", "voice", "sound", "editing", "thumbnails"]
        if section not in valid:
            console.print(f"[red]Invalid section. Choose: {', '.join(valid)}[/red]")
            return
        try:
            from tools.video.video_studio_tool import video_studio_tool
            intent = video_studio_tool.detect_video_intent(topic)
            intent["title"] = topic
            content = video_studio_tool.generate_section(section, intent)
            from rich.panel import Panel
            console.print(Panel(content[:3000], title=f"🎬 {section.upper()}", border_style="red"))
        except Exception as e:
            console.print(f"[red]Section error: {e}[/red]")

    def _list_video_projects(self):
        try:
            from memory.memory_store import memory_store
            from rich.table import Table
            projects = memory_store.list_projects(tool_type="youtube")
            if not projects:
                console.print("[dim]No video projects yet.[/dim]")
                return
            table = Table(title="🎬 Video Projects", border_style="red")
            table.add_column("ID", style="cyan", width=10)
            table.add_column("Name", style="white", width=30)
            table.add_column("Status", style="green", width=10)
            table.add_column("Dir", style="dim", width=35)
            for p in projects:
                table.add_row(p["id"][:8], p["name"], p["status"], p.get("project_dir","")[-35:])
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _video_status(self):
        from core.config import config
        from rich.table import Table
        table = Table(title="🎬 Video Studio Status", border_style="red")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        table.add_row("OpenRouter Key", "✓ Set" if config.OPENROUTER_API_KEY else "✗ NOT SET")
        table.add_row("Video Model", config.VIDEO_STUDIO_MODEL)
        table.add_row("Max Tokens", str(config.VIDEO_STUDIO_MAX_TOKENS))
        table.add_row("Temperature", str(config.VIDEO_STUDIO_TEMPERATURE))
        table.add_row("Video Projects Dir", str(config.VIDEO_PROJECTS_DIR))
        console.print(table)
        if not config.OPENROUTER_API_KEY:
            console.print("[yellow]Add OPENROUTER_API_KEY=sk-or-v1-... to .env[/yellow]")

    def _exit(self):
        console.print("[cyan]AgentJW signing off. 🤖[/cyan]")
        sys.exit(0)
