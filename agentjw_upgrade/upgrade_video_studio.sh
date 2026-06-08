#!/bin/bash
# ============================================================
# upgrade_video_studio.sh
# AgentJW → Video Studio Upgrade
# Run dari: ~/agentjw/
# Usage: bash upgrade_video_studio.sh
# ============================================================

set -e
AGENTJW_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$AGENTJW_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   🎬  AgentJW Video Studio Upgrade v2.0             ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 1. Backup ────────────────────────────────────────────────────────────────
echo "📦 [1/8] Backing up existing files..."
BACKUP_DIR="backups/pre_video_studio_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
for f in core/config.py agents/orchestrator.py interface/cli.py api_server.py; do
    [ -f "$f" ] && cp "$f" "$BACKUP_DIR/" && echo "  backed up: $f"
done
echo "  ✓ Backup: $BACKUP_DIR"

# ── 2. Install Python deps ───────────────────────────────────────────────────
echo ""
echo "📦 [2/8] Installing dependencies..."
source venv/bin/activate 2>/dev/null || true
pip install -q fastapi uvicorn requests python-multipart 2>&1 | tail -3
echo "  ✓ Dependencies installed"

# ── 3. Create tools/video/ module ───────────────────────────────────────────
echo ""
echo "🗂  [3/8] Creating tools/video/ module..."
mkdir -p tools/video

cat > tools/video/__init__.py << 'EOF'
EOF

# ── openrouter_client.py
cat > tools/video/openrouter_client.py << 'EOF'
"""
tools/video/openrouter_client.py - OpenRouter LLM Client
Drop-in supplement for core/llm_client.py using OpenRouter API
"""
import json
import time
from typing import List, Dict, Optional
from core.logger import logger


class OpenRouterClient:
    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "deepseek/deepseek-r1-0528:free"):
        self.api_key = api_key
        self.model = model
        logger.info(f"OpenRouter client initialized: {model}")

    def chat(
        self,
        messages: List[Dict],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> str:
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)
        return self._call(full_messages, temperature, max_tokens)

    def chat_openrouter(
        self,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        return self._call(messages, temperature, max_tokens)

    def _call(self, messages: List[Dict], temperature: float, max_tokens: int) -> str:
        import requests
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://agentjw.local",
            "X-Title": "AgentJW Video Studio",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        for attempt in range(3):
            try:
                resp = requests.post(self.BASE_URL, headers=headers, json=payload, timeout=120)
                resp.raise_for_status()
                data = resp.json()
                if "error" in data:
                    raise ValueError(f"OpenRouter error: {data['error']}")
                content = data["choices"][0]["message"]["content"]
                logger.debug(f"OpenRouter response: {len(content)} chars")
                return content
            except Exception as e:
                logger.warning(f"OpenRouter attempt {attempt+1}/3 failed: {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise

    def count_tokens(self, text: str) -> int:
        return len(text.split()) * 2
EOF

# ── video_studio_tool.py
cat > tools/video/video_studio_tool.py << 'EOF'
"""
tools/video/video_studio_tool.py - AgentJW Video Studio Tool
Generates full AI video production packages via OpenRouter
"""
import re
import json
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from core.config import config
from core.logger import logger, console
from core.models import CodeFile
from rich.panel import Panel

VIDEO_SECTIONS = ["script", "scenes", "voice", "sound", "editing", "thumbnails"]

SECTION_PROMPTS = {
    "script": {
        "system": (
            "You are an expert YouTube documentary scriptwriter. "
            "Write viral, high-retention scripts. "
            "Format: [HOOK], [MAIN CONTENT - Act I, II, III], [ENDING]. "
            "For bilingual: each segment = English VO | Indonesian subtitle | Director note. "
            "Sentences tight and impactful. Contractions throughout. No fluff."
        ),
        "user": (
            "Write a complete viral documentary script.\n"
            "- Format: [HOOK] [MAIN CONTENT Act I/II/III] [ENDING]\n"
            "- Each segment: English VO | Indonesian subtitle | Director delivery note\n"
            "- Hook creates immediate curiosity in first 5 seconds\n"
            "- Use real data, statistics, surprising facts\n"
            "TOPIC: {title}\nDURATION: {duration} minutes\nTONE: {tone}\nLANGUAGE: {lang}"
        ),
    },
    "scenes": {
        "system": (
            "You are a cinematic director specializing in Higgsfield AI video generation. "
            "Create extremely detailed visual prompts. Be specific about every element."
        ),
        "user": (
            "Create 9-12 cinematic scenes with Higgsfield AI prompts.\n"
            "For EACH scene:\n"
            "1. SCENE NUMBER & SECTION (Hook/Act I/II/III/Ending)\n"
            "2. SCRIPT REF: VO line it covers\n"
            "3. HIGGSFIELD PROMPT: 80-120 words, ultra detailed\n"
            "4. CAMERA: movement type\n"
            "5. LIGHTING: mood and color palette\n"
            "6. STYLE REF: film/director reference\n"
            "TOPIC: {title}\nSTYLE: {style}\nTONE: {tone}"
        ),
    },
    "voice": {
        "system": (
            "You are an ElevenLabs voice director. "
            "Provide precise voice casting and delivery cues for documentary narration."
        ),
        "user": (
            "Create complete ElevenLabs voice direction.\n"
            "- Voice recommendation (name, characteristics)\n"
            "- Global pacing rules\n"
            "- Per key-line emotional cues: SLOW/FAST/PAUSE/EMPHASIS/WHISPER\n"
            "- Dramatic silence moments\n"
            "Recommend: deep British/American male, authoritative, calm with escalating urgency.\n"
            "TOPIC: {title}\nTONE: {tone}\nDURATION: {duration} minutes"
        ),
    },
    "sound": {
        "system": (
            "You are a professional sound designer for documentary films."
        ),
        "user": (
            "Create full sound design plan with timestamps.\n"
            "For each section:\n"
            "- Background music style & reference artist\n"
            "- Music dynamics (rise/drop/swell/silence)\n"
            "- SFX (whooshes, hits, ambience)\n"
            "- Strategic silence moments\n"
            "Overall: Hans Zimmer cinematic tension + industrial electronic.\n"
            "TOPIC: {title}\nDURATION: {duration} minutes"
        ),
    },
    "editing": {
        "system": (
            "You are a YouTube video editor expert in documentary pacing and retention."
        ),
        "user": (
            "Create detailed editing plan maximizing viewer retention.\n"
            "For each timestamp range:\n"
            "- Cut style (hard/jump/match/L-cut/J-cut)\n"
            "- Transition type\n"
            "- Text overlay design and animation\n"
            "- B-roll notes\n"
            "- Retention hook placement\n"
            "Style: Cold Fusion × Kurzgesagt × Johnny Harris.\n"
            "TOPIC: {title}\nDURATION: {duration} minutes"
        ),
    },
    "thumbnails": {
        "system": (
            "You are a YouTube thumbnail strategist focused on maximum CTR."
        ),
        "user": (
            "Create 3 YouTube thumbnail variants (1280×720px, 16:9).\n"
            "For each:\n"
            "- VARIANT NAME & CONCEPT\n"
            "- BACKGROUND description\n"
            "- HEADLINE: max 4 bold words\n"
            "- SUBTEXT\n"
            "- DOMINANT VISUAL element\n"
            "- EMOTION TRIGGER\n"
            "- HEX COLORS (bg, text, accent)\n"
            "- LAYOUT NOTES for Canva/Nano Banana\n"
            "TOPIC: {title}\nTONE: {tone}"
        ),
    },
}


class VideoStudioTool:
    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            if config.OPENROUTER_API_KEY:
                from tools.video.openrouter_client import OpenRouterClient
                self._llm = OpenRouterClient(
                    api_key=config.OPENROUTER_API_KEY,
                    model=config.VIDEO_STUDIO_MODEL,
                )
            else:
                from core.llm_client import llm
                self._llm = llm
        return self._llm

    def detect_video_intent(self, user_request: str) -> Dict:
        req = user_request.lower()
        intent = {
            "action": "full_package",
            "title": user_request[:200],
            "duration": "12-15",
            "lang": "bilingual",
            "style": "cinematic documentary",
            "tone": "confident, urgent, no fluff",
        }
        for kw in ["buat video", "generate video", "video studio", "bikin video", "create video"]:
            if kw in req:
                idx = req.find(kw) + len(kw)
                title_part = user_request[idx:].strip().strip(":").strip()
                if title_part:
                    intent["title"] = title_part[:200]
                break
        if "3 menit" in req or "short" in req:
            intent["duration"] = "3-5"
        elif "7 menit" in req or "medium" in req:
            intent["duration"] = "7-10"
        elif "20 menit" in req or "deep dive" in req:
            intent["duration"] = "20+"
        if "english only" in req:
            intent["lang"] = "english"
        elif "indonesia" in req and "subtitle" not in req:
            intent["lang"] = "indonesian"
        return intent

    def generate_section(self, section: str, intent: Dict) -> str:
        if section not in SECTION_PROMPTS:
            raise ValueError(f"Unknown section: {section}")
        cfg = SECTION_PROMPTS[section]
        user_prompt = cfg["user"].format(
            title=intent.get("title", ""),
            duration=intent.get("duration", "12-15"),
            tone=intent.get("tone", "confident, urgent"),
            lang=intent.get("lang", "bilingual"),
            style=intent.get("style", "cinematic documentary"),
        )
        console.print(f"[cyan]  📽  Generating: {section}...[/cyan]")
        try:
            if hasattr(self.llm, "chat_openrouter"):
                result = self.llm.chat_openrouter(
                    system=cfg["system"],
                    user=user_prompt,
                    temperature=config.VIDEO_STUDIO_TEMPERATURE,
                    max_tokens=config.VIDEO_STUDIO_MAX_TOKENS,
                )
            else:
                result = self.llm.chat(
                    messages=[{"role": "user", "content": user_prompt}],
                    system=cfg["system"],
                    temperature=config.VIDEO_STUDIO_TEMPERATURE,
                    max_tokens=config.VIDEO_STUDIO_MAX_TOKENS,
                )
            logger.info(f"Section '{section}' generated: {len(result)} chars")
            return result
        except Exception as e:
            logger.error(f"Failed section '{section}': {e}")
            raise

    def build_video_package(self, user_request: str, sections: Optional[List[str]] = None) -> Dict:
        intent = self.detect_video_intent(user_request)
        sections = sections or VIDEO_SECTIONS
        console.print(Panel(
            f"[cyan]Title:[/cyan] {intent['title']}\n"
            f"[cyan]Duration:[/cyan] {intent['duration']} min | "
            f"[cyan]Lang:[/cyan] {intent['lang']}\n"
            f"[cyan]Model:[/cyan] {config.VIDEO_STUDIO_MODEL}",
            title="🎬 VIDEO STUDIO — Generating",
            border_style="red",
        ))
        package = {
            "id": str(uuid.uuid4())[:8],
            "created_at": datetime.now().isoformat(),
            "intent": intent,
            "sections": {},
        }
        for section in sections:
            try:
                content = self.generate_section(section, intent)
                package["sections"][section] = content
                console.print(f"  [green]✓[/green] {section} ({len(content)} chars)")
            except Exception as e:
                package["sections"][section] = f"ERROR: {e}"
                console.print(f"  [red]✗[/red] {section}: {e}")
        return package

    def save_package(self, package: Dict, project_dir: Path) -> List[Path]:
        project_dir.mkdir(parents=True, exist_ok=True)
        saved = []
        for section, content in package["sections"].items():
            fpath = project_dir / f"{section}.txt"
            fpath.write_text(content, encoding="utf-8")
            saved.append(fpath)
        json_path = project_dir / "video_package.json"
        json_path.write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")
        saved.append(json_path)
        readme = project_dir / "README.md"
        readme.write_text(self._make_readme(package), encoding="utf-8")
        saved.append(readme)
        return saved

    def _make_readme(self, package: Dict) -> str:
        intent = package["intent"]
        done = [s for s, v in package["sections"].items() if not v.startswith("ERROR")]
        return (
            f"# 🎬 Video Production Package\n\n"
            f"**ID:** {package['id']}  \n"
            f"**Title:** {intent['title']}  \n"
            f"**Duration:** {intent['duration']} min | **Lang:** {intent['lang']}\n\n"
            f"## Sections ({len(done)}/{len(VIDEO_SECTIONS)})\n"
            + "\n".join(f"- ✅ {s}" for s in done)
            + "\n\n## Files\n"
            "- `script.txt` — Bilingual script (VO + subtitle + director notes)\n"
            "- `scenes.txt` — Higgsfield AI prompts per scene\n"
            "- `voice.txt` — ElevenLabs voice direction\n"
            "- `sound.txt` — Sound design plan\n"
            "- `editing.txt` — Cut timing & text overlays\n"
            "- `thumbnails.txt` — 3 thumbnail concepts (1280×720)\n"
            "- `video_package.json` — Full machine-readable package\n\n"
            "*Generated by AgentJW Video Studio*\n"
        )

    def display_package_summary(self, package: Dict, project_dir: Path):
        done = sum(1 for v in package["sections"].values() if not v.startswith("ERROR"))
        console.print(Panel(
            f"[green]✅ Package Complete![/green]\n\n"
            f"📁 {project_dir}\n"
            f"🆔 Package ID: {package['id']}\n"
            f"✓ Sections: {done}/{len(VIDEO_SECTIONS)}\n\n"
            + "\n".join(f"  • {s}.txt" for s in package["sections"].keys()),
            title="🎬 VIDEO STUDIO DONE",
            border_style="green",
        ))


video_studio_tool = VideoStudioTool()
EOF

echo "  ✓ tools/video/ module created"

# ── 4. Patch core/config.py ──────────────────────────────────────────────────
echo ""
echo "🔧 [4/8] Patching core/config.py..."

python3 - << 'PYEOF'
import re

path = "core/config.py"
with open(path, "r") as f:
    content = f.read()

# Check if already patched
if "OPENROUTER_API_KEY" in content:
    print("  ⚠  Already patched — skipping config.py")
else:
    # Insert OpenRouter + Video Studio config after ANTHROPIC_MODEL line
    insert_after = 'ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")'
    new_block = '''ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

    # ── OpenRouter (Video Studio) ──────────────────────────────────────────
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # ── Video Studio ───────────────────────────────────────────────────────
    VIDEO_STUDIO_MODEL: str = os.getenv("VIDEO_STUDIO_MODEL", "deepseek/deepseek-r1-0528:free")
    VIDEO_STUDIO_MAX_TOKENS: int = int(os.getenv("VIDEO_STUDIO_MAX_TOKENS", "4096"))
    VIDEO_STUDIO_TEMPERATURE: float = float(os.getenv("VIDEO_STUDIO_TEMPERATURE", "0.75"))
    VIDEO_PROJECTS_DIR = BASE_DIR / os.getenv("VIDEO_PROJECTS_DIR", "projects/video")

    # ── API Server ─────────────────────────────────────────────────────────
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))'''

    content = content.replace(insert_after, new_block)

    # Patch ensure_dirs to include VIDEO_PROJECTS_DIR
    old_ensure = "cls.PROJECTS_DIR,"
    new_ensure = "cls.PROJECTS_DIR,\n            cls.VIDEO_PROJECTS_DIR,"
    content = content.replace(old_ensure, new_ensure)

    # Add has_openrouter and has_video_studio methods before last line
    helper_methods = '''
    @classmethod
    def has_openrouter(cls) -> bool:
        return bool(cls.OPENROUTER_API_KEY)

    @classmethod
    def has_video_studio(cls) -> bool:
        return bool(cls.OPENROUTER_API_KEY)

'''
    # Insert before "config = Config()"
    content = content.replace("config = Config()", helper_methods + "config = Config()")

    with open(path, "w") as f:
        f.write(content)
    print("  ✓ core/config.py patched")
PYEOF

# ── 5. Patch agents/orchestrator.py ─────────────────────────────────────────
echo ""
echo "🔧 [5/8] Patching agents/orchestrator.py..."

python3 - << 'PYEOF'
path = "agents/orchestrator.py"
with open(path, "r") as f:
    content = f.read()

if "video_build" in content:
    print("  ⚠  Already patched — skipping orchestrator.py")
else:
    # 1. Add video_keywords in route_intent after youtube_keywords block
    youtube_block = '''        youtube_keywords = ["youtube", "upload youtube", "thumbnail",
            "youtube seo", "youtube analytics", "auto upload"]
        if any(k in lower for k in youtube_keywords):
            return {"type": "youtube_build", "confidence": 0.9}'''

    video_block = '''        youtube_keywords = ["youtube", "upload youtube", "thumbnail",
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

    content = content.replace(youtube_block, video_block)

    # 2. Add video_build route in smart_build after youtube_build
    old_route = '''        elif intent["type"] == "youtube_build":
            return self._build_youtube(user_request, session_id)'''
    new_route = '''        elif intent["type"] == "youtube_build":
            return self._build_youtube(user_request, session_id)
        elif intent["type"] == "video_build":
            return self._build_video(user_request, session_id)'''
    content = content.replace(old_route, new_route)

    # 3. Add _build_video method before the last method or before orchestrator = OrchestratorAgent()
    build_video_method = '''
    def _build_video(self, user_request: str, session_id: str) -> Dict:
        """Build full video production package via Video Studio"""
        from tools.video.video_studio_tool import video_studio_tool
        from core.config import config

        if not config.has_video_studio():
            console.print(
                "[red]❌ Video Studio requires OPENROUTER_API_KEY in .env[/red]\\n"
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

'''
    content = content.replace(
        "\norchestrator = OrchestratorAgent()",
        build_video_method + "\norchestrator = OrchestratorAgent()"
    )

    with open(path, "w") as f:
        f.write(content)
    print("  ✓ agents/orchestrator.py patched")
PYEOF

# ── 6. Patch interface/cli.py ────────────────────────────────────────────────
echo ""
echo "🔧 [6/8] Patching interface/cli.py..."

python3 - << 'PYEOF'
path = "interface/cli.py"
with open(path, "r") as f:
    content = f.read()

if "video studio" in content.lower():
    print("  ⚠  Already patched — skipping cli.py")
else:
    # 1. Add video commands to HELP_TEXT
    old_help_section = "[bold cyan]═══ SYSTEM ═══[/bold cyan]"
    new_help_section = """[bold cyan]═══ VIDEO STUDIO ═══[/bold cyan]
  [green]video <topic>[/green]             Generate full video production package
  [green]video section <s> <topic>[/green] Generate single section (script/scenes/voice/sound/editing/thumbnails)
  [green]video projects[/green]            List video projects
  [green]video status[/green]              Check OpenRouter + Video Studio status

[bold cyan]═══ SYSTEM ═══[/bold cyan]"""
    content = content.replace(old_help_section, new_help_section)

    # 2. Add video command handler in _handle_input before the else clause
    old_else = '''        else:
            self._run_smart_chat(user_input)'''
    new_else = '''        elif lower.startswith("video section "):
            parts = user_input[14:].strip().split(" ", 1)
            if len(parts) == 2:
                self._run_video_section(parts[0], parts[1])
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
    content = content.replace(old_else, new_else)

    # 3. Add video methods before _exit
    video_methods = '''
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

'''
    content = content.replace(
        "    def _exit(self):",
        video_methods + "    def _exit(self):"
    )

    with open(path, "w") as f:
        f.write(content)
    print("  ✓ interface/cli.py patched")
PYEOF

# ── 7. Create/update api_server.py ──────────────────────────────────────────
echo ""
echo "🔧 [7/8] Creating api_server.py..."

cat > api_server.py << 'EOF'
"""
api_server.py - AgentJW REST API Server v2.0
FastAPI exposing chat, build, and Video Studio endpoints
Run: uvicorn api_server:app --host 0.0.0.0 --port 8000
"""
import uuid, json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="AgentJW API", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

# ── Models ───────────────────────────────────────────────────────────────────
class ChatReq(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: Optional[List[Dict]] = []

class BuildReq(BaseModel):
    task: str
    session_id: Optional[str] = None

class VideoReq(BaseModel):
    title: str
    duration: Optional[str] = "12-15"
    lang: Optional[str] = "bilingual"
    style: Optional[str] = "cinematic documentary"
    tone: Optional[str] = "confident, urgent, no fluff"
    sections: Optional[List[str]] = None
    model: Optional[str] = None

class VideoSectionReq(BaseModel):
    section: str
    title: str
    duration: Optional[str] = "12-15"
    lang: Optional[str] = "bilingual"
    style: Optional[str] = "cinematic documentary"
    tone: Optional[str] = "confident, urgent, no fluff"

class JSXReq(BaseModel):
    jsx_content: str
    title: Optional[str] = None

# ── Job tracker ───────────────────────────────────────────────────────────────
_jobs: Dict[str, Dict] = {}

def _set_job(jid, status, result=None, error=None):
    _jobs[jid] = {"job_id": jid, "status": status,
                  "result": result, "error": error,
                  "updated_at": datetime.now().isoformat()}

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    from core.config import config
    return {"status": "ok", "version": "2.0.0",
            "model": config.get_model(), "provider": config.LLM_PROVIDER,
            "video_studio": config.has_video_studio(),
            "timestamp": datetime.now().isoformat()}

@app.get("/")
def root():
    return {"name": "AgentJW API v2.0",
            "endpoints": ["GET /health", "POST /chat", "POST /build",
                          "POST /video/package", "POST /video/section",
                          "POST /video/parse-jsx",
                          "GET /video/jobs/{id}", "GET /video/projects",
                          "GET /projects"]}

@app.post("/chat")
def chat(req: ChatReq):
    try:
        from agents.orchestrator import orchestrator
        sid = req.session_id or str(uuid.uuid4())
        resp = orchestrator.chat(req.message, req.history or [], sid)
        return {"response": resp, "session_id": sid}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/build")
def build(req: BuildReq):
    try:
        from agents.orchestrator import orchestrator
        sid = req.session_id or str(uuid.uuid4())
        result = orchestrator.smart_build(req.task, sid)
        return {"status": "success", "result": result, "session_id": sid}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/video/package")
def video_package(req: VideoReq, bg: BackgroundTasks):
    from core.config import config
    if not config.has_video_studio():
        raise HTTPException(400, "OPENROUTER_API_KEY not set in .env")
    jid = str(uuid.uuid4())[:8]
    _set_job(jid, "queued")

    def _run():
        try:
            _set_job(jid, "running")
            from tools.video.video_studio_tool import video_studio_tool
            if req.model:
                config.VIDEO_STUDIO_MODEL = req.model
            intent = {"title": req.title, "duration": req.duration,
                      "lang": req.lang, "style": req.style, "tone": req.tone}
            secs = req.sections or ["script","scenes","voice","sound","editing","thumbnails"]
            pkg = video_studio_tool.build_video_package(req.title, secs)
            pkg["intent"] = intent
            pdir = config.PROJECTS_DIR / f"video_{jid}"
            files = video_studio_tool.save_package(pkg, pdir)
            from tools.project_manager.manager import project_manager
            pid = project_manager.register_project(
                name=f"video_{jid}", description=req.title,
                project_dir=str(pdir), tool_type="youtube")
            _set_job(jid, "done", {
                "project_id": pid, "project_dir": str(pdir),
                "package_id": pkg["id"],
                "sections_done": [s for s,v in pkg["sections"].items() if not v.startswith("ERROR")],
                "files": [str(f) for f in files], "title": req.title,
            })
        except Exception as e:
            _set_job(jid, "error", error=str(e))

    bg.add_task(_run)
    return {"job_id": jid, "status": "queued",
            "poll": f"GET /video/jobs/{jid}"}

@app.post("/video/section")
def video_section(req: VideoSectionReq):
    from core.config import config
    if not config.has_video_studio():
        raise HTTPException(400, "OPENROUTER_API_KEY not set")
    try:
        from tools.video.video_studio_tool import video_studio_tool
        intent = {"title": req.title, "duration": req.duration,
                  "lang": req.lang, "style": req.style, "tone": req.tone}
        content = video_studio_tool.generate_section(req.section, intent)
        return {"section": req.section, "content": content,
                "chars": len(content), "title": req.title}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/video/parse-jsx")
def parse_jsx(req: JSXReq):
    import re
    jsx = req.jsx_content
    if not jsx.strip():
        raise HTTPException(400, "Empty JSX content")
    title_m = re.search(r'title(?:En)?:\s*["\']([^"\']+)["\']', jsx)
    higgsfield = re.findall(r'higgsfieldPrompt:\s*["\']([^"\']{20,})["\']', jsx, re.DOTALL)
    vo_lines = re.findall(r'\bvo:\s*["\']([^"\']+)["\']', jsx)
    sub_lines = re.findall(r'\bsub:\s*["\']([^"\']+)["\']', jsx)
    thumbs = re.findall(r'concept:\s*["\']([^"\']+)["\']', jsx)
    cameras = re.findall(r'camera:\s*["\']([^"\']+)["\']', jsx)
    styles = re.findall(r'style:\s*["\']([^"\']+)["\']', jsx)
    return {
        "parsed": True,
        "title": title_m.group(1) if title_m else (req.title or "Unknown"),
        "stats": {
            "scenes": len(re.findall(r'higgsfieldPrompt:', jsx)),
            "vo_lines": len(vo_lines), "subtitle_lines": len(sub_lines),
            "thumbnails": len(thumbs), "jsx_size_kb": round(len(jsx)/1024, 1),
        },
        "higgsfield_prompts": higgsfield[:12],
        "vo_lines": vo_lines[:20], "subtitle_lines": sub_lines[:20],
        "thumbnail_concepts": thumbs, "camera_movements": cameras[:12],
        "style_references": styles[:12],
    }

@app.get("/video/jobs/{job_id}")
def get_job(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} not found")
    return job

@app.get("/video/projects")
def video_projects():
    from memory.memory_store import memory_store
    projects = memory_store.list_projects(tool_type="youtube")
    return {"projects": projects, "total": len(projects)}

@app.get("/video/download/{project_id}")
def download(project_id: str):
    from memory.memory_store import memory_store
    proj = memory_store.get_project(project_id)
    if not proj:
        raise HTTPException(404, "Project not found")
    p = Path(proj["project_dir"]) / "video_package.json"
    if not p.exists():
        raise HTTPException(404, "Package file not found")
    return FileResponse(str(p), media_type="application/json",
                        filename=f"video_package_{project_id}.json")

@app.get("/projects")
def projects():
    from memory.memory_store import memory_store
    return {"projects": memory_store.list_projects()}

@app.get("/projects/{pid}")
def get_project(pid: str):
    from memory.memory_store import memory_store
    p = memory_store.get_project(pid)
    if not p:
        raise HTTPException(404, "Project not found")
    return p

if __name__ == "__main__":
    import uvicorn
    from core.config import config
    uvicorn.run("api_server:app", host=config.API_HOST, port=config.API_PORT, reload=False)
EOF

echo "  ✓ api_server.py created"

# ── 8. Update .env ───────────────────────────────────────────────────────────
echo ""
echo "🔧 [8/8] Updating .env..."

if [ ! -f ".env" ]; then
    cp .env.example .env 2>/dev/null || touch .env
fi

# Add Video Studio section if not present
if ! grep -q "OPENROUTER_API_KEY" .env; then
    cat >> .env << 'ENVEOF'

# ── Video Studio (AgentJW v2.0) ───────────────────────────────────────────────
OPENROUTER_API_KEY=sk-or-v1-PASTE_YOUR_KEY_HERE
VIDEO_STUDIO_MODEL=deepseek/deepseek-r1-0528:free
VIDEO_STUDIO_MAX_TOKENS=4096
VIDEO_STUDIO_TEMPERATURE=0.75
VIDEO_PROJECTS_DIR=projects/video
API_HOST=0.0.0.0
API_PORT=8000
ENVEOF
    echo "  ✓ .env updated — edit OPENROUTER_API_KEY"
else
    echo "  ⚠  .env already has OPENROUTER_API_KEY — skipping"
fi

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅  Upgrade Complete!                             ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "NEXT STEPS:"
echo "  1. Edit .env → set OPENROUTER_API_KEY=sk-or-v1-..."
echo ""
echo "  2. Test Video Studio from CLI:"
echo "     cd ~/agentjw && source venv/bin/activate"
echo "     python main.py"
echo "     ⚡ agentjw > video status"
echo "     ⚡ agentjw > video Bagaimana AI Akan Menghancurkan 50% Pekerjaan"
echo ""
echo "  3. Or generate single section:"
echo "     ⚡ agentjw > video section script Bagaimana AI Mengganti Pekerjaan"
echo ""
echo "  4. Start API server:"
echo "     uvicorn api_server:app --host 0.0.0.0 --port 8000"
echo "     # Test: curl http://localhost:8000/health"
echo ""
echo "  5. Connect JSX Studio (web tool dari Claude) ke:"
echo "     http://94.100.26.128:8000/video/parse-jsx"
echo "     http://94.100.26.128:8000/video/package"
echo ""
