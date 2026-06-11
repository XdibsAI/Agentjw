#!/usr/bin/env python3
"""
patch_agentjw_video.py
Jalankan dari: ~/agentjw/
Usage: python3 patch_agentjw_video.py
"""
import os, sys, shutil
from pathlib import Path
from datetime import datetime

BASE = Path(os.path.abspath(__file__)).parent
BACKUP = BASE / f"backups/patch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
BACKUP.mkdir(parents=True, exist_ok=True)

def backup(f):
    src = BASE / f
    if src.exists():
        shutil.copy(src, BACKUP / Path(f).name)
        print(f"  backed up: {f}")

def patch_file(path, old, new, label):
    p = BASE / path
    content = p.read_text(encoding="utf-8")
    if old not in content:
        print(f"  ⚠  [{label}] marker not found — skipping (may already be patched)")
        return False
    p.write_text(content.replace(old, new), encoding="utf-8")
    print(f"  ✓  [{label}] patched")
    return True

print("\n╔══════════════════════════════════════════╗")
print("║  AgentJW Video Studio Patch v2.0        ║")
print("╚══════════════════════════════════════════╝\n")

# ── BACKUP ────────────────────────────────────────────────────────────────
print("📦 Backing up...")
for f in ["core/config.py","agents/orchestrator.py","interface/cli.py"]:
    backup(f)

# ══════════════════════════════════════════════════════════════════════════
# PATCH 1 — core/config.py
# ══════════════════════════════════════════════════════════════════════════
print("\n🔧 [1/3] Patching core/config.py...")
backup("core/config.py")

CONFIG_OLD = '    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")'
CONFIG_NEW = '''    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # ── OpenRouter + Video Studio ──────────────────────────────────────────
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    VIDEO_STUDIO_MODEL: str = os.getenv("VIDEO_STUDIO_MODEL", "deepseek/deepseek-r1-0528:free")
    VIDEO_STUDIO_MAX_TOKENS: int = int(os.getenv("VIDEO_STUDIO_MAX_TOKENS", "4096"))
    VIDEO_STUDIO_TEMPERATURE: float = float(os.getenv("VIDEO_STUDIO_TEMPERATURE", "0.75"))
    VIDEO_PROJECTS_DIR: "Path" = BASE_DIR / os.getenv("VIDEO_PROJECTS_DIR", "projects/video")
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))'''

patch_file("core/config.py", CONFIG_OLD, CONFIG_NEW, "config OpenRouter")

# patch ensure_dirs
patch_file(
    "core/config.py",
    "cls.PROJECTS_DIR,",
    "cls.PROJECTS_DIR,\n            cls.VIDEO_PROJECTS_DIR,",
    "config ensure_dirs"
)

# patch has_* helpers before config = Config()
patch_file(
    "core/config.py",
    "config = Config()",
    """
    @classmethod
    def has_openrouter(cls) -> bool:
        return bool(cls.OPENROUTER_API_KEY)

    @classmethod
    def has_video_studio(cls) -> bool:
        return bool(cls.OPENROUTER_API_KEY)


config = Config()""",
    "config helpers"
)

# ══════════════════════════════════════════════════════════════════════════
# PATCH 2 — agents/orchestrator.py
# ══════════════════════════════════════════════════════════════════════════
print("\n🔧 [2/3] Patching agents/orchestrator.py...")

# 2a. route_intent — add video_keywords after youtube block
ORCH_ROUTE_OLD = '''        youtube_keywords = ["youtube", "upload youtube", "thumbnail",
            "youtube seo", "youtube analytics", "auto upload"]
        if any(k in lower for k in youtube_keywords):
            return {"type": "youtube_build", "confidence": 0.9}'''

ORCH_ROUTE_NEW = '''        youtube_keywords = ["youtube", "upload youtube", "thumbnail",
            "youtube seo", "youtube analytics", "auto upload"]
        if any(k in lower for k in youtube_keywords):
            return {"type": "youtube_build", "confidence": 0.9}

        video_keywords = [
            "video studio", "buat video", "generate video", "bikin video",
            "production package", "higgsfield", "elevenlabs script",
            "video package", "script youtube", "scenes video",
            "thumbnail video", "sound design", "editing plan",
            "create video", "video documentary",
        ]
        if any(k in lower for k in video_keywords):
            return {"type": "video_build", "confidence": 0.92}'''

patch_file("agents/orchestrator.py", ORCH_ROUTE_OLD, ORCH_ROUTE_NEW, "orchestrator route")

# 2b. smart_build — add video_build dispatch
ORCH_DISPATCH_OLD = '''        elif intent["type"] == "youtube_build":
            return self._build_youtube(user_request, session_id)'''

ORCH_DISPATCH_NEW = '''        elif intent["type"] == "youtube_build":
            return self._build_youtube(user_request, session_id)
        elif intent["type"] == "video_build":
            return self._build_video(user_request, session_id)'''

patch_file("agents/orchestrator.py", ORCH_DISPATCH_OLD, ORCH_DISPATCH_NEW, "orchestrator dispatch")

# 2c. add _build_video method before singleton
ORCH_METHOD_OLD = "\norchestrator = OrchestratorAgent()"

ORCH_METHOD_NEW = '''
    def _build_video(self, user_request: str, session_id: str) -> Dict:
        """Build full video production package via Video Studio"""
        from tools.video.video_studio_tool import video_studio_tool
        from core.config import config

        if not config.has_video_studio():
            console.print(
                "[red]❌ Video Studio memerlukan OPENROUTER_API_KEY di .env[/red]\\n"
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


orchestrator = OrchestratorAgent()'''

patch_file("agents/orchestrator.py", ORCH_METHOD_OLD, ORCH_METHOD_NEW, "orchestrator _build_video")

# ══════════════════════════════════════════════════════════════════════════
# PATCH 3 — interface/cli.py
# ══════════════════════════════════════════════════════════════════════════
print("\n🔧 [3/3] Patching interface/cli.py...")

# 3a. HELP_TEXT — add video section
CLI_HELP_OLD = "[bold cyan]═══ SYSTEM ═══[/bold cyan]"
CLI_HELP_NEW = """[bold cyan]═══ VIDEO STUDIO ═══[/bold cyan]
  [green]video <topic>[/green]             Generate full video production package
  [green]video section <s> <topic>[/green] Generate single section
  [green]video projects[/green]            List video projects
  [green]video status[/green]              Check Video Studio config

[bold cyan]═══ SYSTEM ═══[/bold cyan]"""

patch_file("interface/cli.py", CLI_HELP_OLD, CLI_HELP_NEW, "cli HELP_TEXT")

# 3b. _handle_input — add video commands before else
CLI_ELSE_OLD = '''        else:
            self._run_smart_chat(user_input)'''

CLI_ELSE_NEW = '''        elif lower.startswith("video section "):
            parts = user_input[14:].strip().split(" ", 1)
            if len(parts) == 2:
                self._run_video_section(parts[0].strip(), parts[1].strip())
            else:
                console.print("[yellow]Usage: video section <section> <topic>[/yellow]")
        elif lower == "video projects":
            self._list_video_projects()
        elif lower == "video status":
            self._video_status()
        elif lower.startswith("video "):
            self._run_video_build(user_input[6:].strip())
        else:
            self._run_smart_chat(user_input)'''

patch_file("interface/cli.py", CLI_ELSE_OLD, CLI_ELSE_NEW, "cli video commands")

# 3c. add video methods before _exit
CLI_EXIT_OLD = "    def _exit(self):"

CLI_EXIT_NEW = '''    def _run_video_build(self, topic: str):
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
            console.print(f"[red]Section tidak valid. Pilih: {', '.join(valid)}[/red]")
            return
        try:
            from tools.video.video_studio_tool import video_studio_tool
            intent = {"title": topic, "duration": "12-15", "lang": "bilingual",
                      "style": "cinematic documentary", "tone": "confident, urgent, no fluff"}
            content = video_studio_tool.generate_section(section, intent)
            console.print(Panel(content[:3000],
                                title=f"🎬 {section.upper()}", border_style="red"))
        except Exception as e:
            console.print(f"[red]Section error: {e}[/red]")

    def _list_video_projects(self):
        try:
            from memory.memory_store import memory_store
            from rich.table import Table
            projects = memory_store.list_projects(tool_type="youtube")
            if not projects:
                console.print("[dim]Belum ada video project.[/dim]")
                return
            table = Table(title="🎬 Video Projects", border_style="red")
            table.add_column("ID", style="cyan", width=10)
            table.add_column("Name", style="white", width=30)
            table.add_column("Status", style="green", width=10)
            table.add_column("Dir", style="dim", width=35)
            for p in projects:
                table.add_row(p["id"][:8], p["name"],
                              p["status"], p.get("project_dir","")[-35:])
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _video_status(self):
        from core.config import config
        from rich.table import Table
        table = Table(title="🎬 Video Studio Status", border_style="red")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        ok = "✓ SET" if config.OPENROUTER_API_KEY else "✗ BELUM DISET"
        table.add_row("OpenRouter Key", ok)
        table.add_row("Video Model", config.VIDEO_STUDIO_MODEL)
        table.add_row("Max Tokens", str(config.VIDEO_STUDIO_MAX_TOKENS))
        table.add_row("Temperature", str(config.VIDEO_STUDIO_TEMPERATURE))
        table.add_row("Video Projects Dir", str(config.VIDEO_PROJECTS_DIR))
        console.print(table)
        if not config.OPENROUTER_API_KEY:
            console.print("[yellow]→ Tambahkan OPENROUTER_API_KEY=sk-or-v1-... ke .env[/yellow]")
        else:
            console.print("[green]✓ Video Studio siap digunakan![/green]")

    def _exit(self):'''

patch_file("interface/cli.py", CLI_EXIT_OLD, CLI_EXIT_NEW, "cli video methods")

print("\n✅ Semua patch selesai!")
print(f"   Backup: {BACKUP}")
print("\nTest sekarang:")
print("  python main.py")
print("  ⚡ agentjw > video status")
