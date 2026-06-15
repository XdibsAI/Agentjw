"""
interface/cli.py - SiCuan CLI
Semua input user → SiCuan brain, tidak ada keyword/template
"""
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style
from rich.panel import Panel
from rich.text import Text

from core.config import config
from core.logger import logger, console
from memory.memory_store import memory_store

PROMPT_STYLE = Style.from_dict({"prompt": "#FFD700 bold", "": "#ffffff"})

BANNER = """
╔══════════════════════════════════════════════════╗
║  💰  S I C U A N  —  Si Paling Cuan            ║
║  AI Partner Bisnis  ·  Autonomous  ·  Real Data ║
╚══════════════════════════════════════════════════╝"""


class CLI:
    def __init__(self):
        from interface.session import get_or_create_session_id
        self.session_id = get_or_create_session_id()

        # Load SiCuan dengan session
        from sicuan.chat import SiCuanChat
        self.sicuan = SiCuanChat()
        self.sicuan.session_id = self.session_id

        # Load history
        try:
            saved = memory_store.get_chat_history(self.session_id, limit=20)
            if saved:
                self.sicuan.history = saved
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
        console.print(f"[bold yellow]{BANNER}[/bold yellow]")
        projects = memory_store.list_projects()
        msgs = len(self.sicuan.history)
        console.print(
            f"[dim]Session: {self.session_id[:8]} | "
            f"Projects: {len(projects)} | "
            f"Model: {config.get_model()}[/dim]"
        )
        if msgs > 0:
            console.print(f"[dim]Loaded {msgs} pesan sebelumnya[/dim]")
        console.print(
            "\n[yellow]Ngobrol aja langsung — SiCuan paham konteks.[/yellow]\n"
            "[dim]'exit' untuk keluar | 'projects' untuk daftar project[/dim]\n"
        )

        while True:
            try:
                user_input = self.prompt_session.prompt(
                    "💰 > ", style=PROMPT_STYLE
                ).strip()
                if not user_input:
                    continue
                self._handle(user_input)
            except KeyboardInterrupt:
                console.print("\n[yellow]Ctrl+C — ketik 'exit' untuk keluar[/yellow]")
            except EOFError:
                self._exit()
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                logger.exception("CLI error")

    def _handle(self, inp: str):
        lower = inp.lower().strip()

        # Hanya hard-exit dan system commands
        if lower in ("exit", "quit", "q"):
            self._exit()
        elif lower == "projects":
            self._show_projects()
        elif lower == "status":
            self._show_status()
        elif lower == "memory":
            self._show_memory()
        elif lower == "reset":
            self.sicuan.history = []
            memory_store.clear_all()
            console.print("[yellow]Memory direset[/yellow]")
        else:
            # SEMUA input → SiCuan brain
            self._chat(inp)

    def _chat(self, user_input: str):
        try:
            response = self.sicuan.chat(user_input)
            console.print(Panel(
                Text(response),
                title="[yellow]💰 SiCuan[/yellow]",
                border_style="yellow"
            ))
        except Exception as e:
            console.print(f"[red]SiCuan error: {e}[/red]")
            logger.exception("SiCuan chat failed")

    def _show_projects(self):
        from rich.table import Table
        projects = memory_store.list_projects()
        if not projects:
            console.print("[dim]Belum ada project[/dim]")
            return
        table = Table(title="Projects", border_style="yellow")
        table.add_column("ID", style="dim", width=10)
        table.add_column("Nama", style="white")
        table.add_column("Type", style="yellow", width=10)
        table.add_column("Status", style="green", width=10)
        for p in projects:
            status_color = "green" if p["status"] == "success" else "red" if p["status"] == "failed" else "yellow"
            table.add_row(
                p["id"][:8],
                p["name"],
                p["tool_type"],
                f"[{status_color}]{p['status']}[/{status_color}]"
            )
        console.print(table)

    def _show_status(self):
        from rich.table import Table
        table = Table(title="SiCuan Status", border_style="yellow")
        table.add_column("Setting", style="yellow")
        table.add_column("Value", style="white")
        table.add_row("Identity", "SiCuan — Si Paling Cuan")
        table.add_row("Model", config.get_model())
        table.add_row("Session", self.session_id[:16] + "...")
        table.add_row("Chat history", str(len(self.sicuan.history)))
        table.add_row("Projects", str(len(memory_store.list_projects())))
        table.add_row("Memory DB", str(config.SQLITE_PATH))
        console.print(table)

    def _show_memory(self):
        from rich.table import Table
        memories = memory_store.recall(limit=10)
        if not memories:
            console.print("[dim]Memory kosong[/dim]")
            return
        table = Table(title="Memory SiCuan", border_style="yellow")
        table.add_column("Type", style="yellow", width=12)
        table.add_column("Content", style="white")
        for m in memories:
            table.add_row(m["type"], m["content"][:70])
        console.print(table)

    def _exit(self):
        console.print("[yellow]SiCuan signing off. Sampai jumpa! 💰[/yellow]")
        sys.exit(0)
