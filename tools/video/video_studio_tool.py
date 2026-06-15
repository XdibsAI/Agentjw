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
            "- MINIMUM 100 English narration words.\n"
            "- Target words based on duration: 3-5min=200, 7-10min=600, 12+=1000.\n"
            "- Produce 30-50 EN VO narration blocks.\n"
            "- Every EN VO block must contain 25-50 words.\n"
            "- Each EN VO block MUST have matching Indonesian subtitle and director note.\n"
            "- Hook creates immediate curiosity in first 5 seconds.\n"
            "- Use real data, statistics, surprising facts.\n"
            "- Expand every act with detailed explanations, examples, evidence and storytelling.\n"
            "- Never summarize sections.\n"
            "- Do not shorten the script.\n"
            "TOPIC: {title}\n"
            "DURATION: {duration} minutes\n"
            "TONE: {tone}\n"
            "LANGUAGE: {lang}"
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

            if section == "script":
                vo_blocks = re.findall(
                    r'\*\*EN VO:\*\*(?:.*?)"([^"]+)"',
                    result,
                    re.S
                )

                vo_words = sum(
                    len(x.split())
                    for x in vo_blocks
                )

                if vo_words < 30:
                    raise RuntimeError(f"Script kosong ({vo_words} words).")


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
