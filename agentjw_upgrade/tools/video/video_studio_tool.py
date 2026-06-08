"""
tools/video/video_studio_tool.py - AgentJW Video Studio Tool
Generates full AI video production packages: script, scenes, voice, sound, editing, thumbnails
Uses OpenRouter as LLM backend (configurable model)
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
from rich.progress import Progress, SpinnerColumn, TextColumn


VIDEO_SECTIONS = ["script", "scenes", "voice", "sound", "editing", "thumbnails"]

SECTION_PROMPTS = {
    "script": {
        "system": (
            "You are an expert YouTube documentary scriptwriter. "
            "Write viral, high-retention scripts. "
            "Format: [HOOK], [MAIN CONTENT - Act I, II, III], [ENDING]. "
            "For bilingual: each line = English VO | Indonesian subtitle | Director note. "
            "Sentences tight and impactful. Contractions throughout. No fluff."
        ),
        "user": (
            "Write a complete viral documentary script.\n"
            "Requirements:\n"
            "- Format: [HOOK] [MAIN CONTENT - Act I, II, III] [ENDING]\n"
            "- Each segment: English VO line, then Indonesian subtitle, then director's delivery note\n"
            "- Hook must create immediate curiosity in first 5 seconds\n"
            "- Use data, statistics, surprising facts\n"
            "- Sentences tight and impactful\n"
            "TOPIC: {title}\nDURATION: {duration} minutes\nTONE: {tone}\nLANGUAGE: {lang}"
        ),
    },
    "scenes": {
        "system": (
            "You are a cinematic director specializing in AI-generated video (Higgsfield AI). "
            "Create extremely detailed visual prompts. Be specific about every visual element."
        ),
        "user": (
            "Create 9-12 cinematic scenes with Higgsfield AI prompts.\n"
            "For EACH scene provide:\n"
            "1. SCENE NUMBER & SECTION (Hook/Act I/Act II/Act III/Ending)\n"
            "2. SCRIPT REF: which VO line it covers\n"
            "3. HIGGSFIELD PROMPT: 80-120 words, ultra detailed cinematic description\n"
            "4. CAMERA: movement type (drone/macro/handheld/dolly/static)\n"
            "5. LIGHTING: mood and color palette\n"
            "6. STYLE REF: film director or movie reference\n"
            "Make visuals: cinematic, high contrast, emotionally engaging, no dead moments.\n"
            "TOPIC: {title}\nSTYLE: {style}\nTONE: {tone}"
        ),
    },
    "voice": {
        "system": (
            "You are an ElevenLabs voice director. "
            "Provide precise voice casting and emotional delivery cues for documentary narration."
        ),
        "user": (
            "Create complete ElevenLabs voice direction for this video.\n"
            "Include:\n"
            "- Voice recommendation (name, voice ID type, characteristics)\n"
            "- Global pacing rules\n"
            "- Per key-line emotional cues: SLOW/FAST/PAUSE/EMPHASIS/WHISPER\n"
            "- Dramatic moments with silence\n"
            "- Breathing and pacing marks\n"
            "Recommend: deep British or American male, authoritative, calm with escalating urgency.\n"
            "TOPIC: {title}\nTONE: {tone}\nDURATION: {duration} minutes"
        ),
    },
    "sound": {
        "system": (
            "You are a professional sound designer for documentary films. "
            "Create timestamp-accurate sound design plans."
        ),
        "user": (
            "Create full sound design plan for this video.\n"
            "For each timestamp section:\n"
            "- Background music style & specific reference track/artist\n"
            "- Music dynamics (rise/drop/swell/silence)\n"
            "- SFX (whooshes, hits, ambience, notification sounds)\n"
            "- Strategic silence moments for impact\n"
            "Overall music direction: Hans Zimmer cinematic tension + industrial electronic.\n"
            "TOPIC: {title}\nDURATION: {duration} minutes\nSTYLE: {style}"
        ),
    },
    "editing": {
        "system": (
            "You are a YouTube video editor with expertise in documentary pacing. "
            "Create precise editing plans that maximize retention."
        ),
        "user": (
            "Create detailed editing plan for this video.\n"
            "For each timestamp range:\n"
            "- Cut style (hard cut / jump cut / match cut / L-cut / J-cut)\n"
            "- Transition type\n"
            "- Text overlay design (font style, size, animation, position)\n"
            "- Pacing rhythm and B-roll notes\n"
            "- Retention hooks placement\n"
            "Editing style: Cold Fusion × Kurzgesagt × Johnny Harris.\n"
            "TOPIC: {title}\nDURATION: {duration} minutes\nSTYLE: {style}"
        ),
    },
    "thumbnails": {
        "system": (
            "You are a YouTube thumbnail strategist. "
            "Create 3 high-CTR thumbnail concepts with specific design directions."
        ),
        "user": (
            "Create 3 YouTube thumbnail variants (1280×720px, 16:9).\n"
            "For each variant:\n"
            "- VARIANT NAME & CONCEPT\n"
            "- BACKGROUND: detailed visual description\n"
            "- HEADLINE: max 4 bold words\n"
            "- SUBTEXT: supporting text\n"
            "- DOMINANT VISUAL: main image/graphic element\n"
            "- EMOTION TRIGGER: psychological hook\n"
            "- HEX COLORS: background, text, accent\n"
            "- LAYOUT NOTES: for Canva/Nano Banana\n"
            "Make them high contrast, emotionally triggering, curiosity-gap driven.\n"
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
            self._llm = self._get_llm()
        return self._llm

    def _get_llm(self):
        """Get LLM client - prefer OpenRouter if configured, else fall back to default"""
        if config.OPENROUTER_API_KEY:
            from tools.video.openrouter_client import OpenRouterClient
            return OpenRouterClient(
                api_key=config.OPENROUTER_API_KEY,
                model=config.VIDEO_STUDIO_MODEL,
            )
        # Fall back to standard LLM
        from core.llm_client import llm
        return llm

    def detect_video_intent(self, user_request: str) -> Dict:
        """Detect video studio intent and extract parameters"""
        req = user_request.lower()
        intent = {
            "action": "full_package",
            "title": "",
            "duration": "12-15",
            "lang": "bilingual",
            "style": "cinematic documentary",
            "tone": "confident, urgent, no fluff",
        }

        # Extract title - everything after keywords
        for kw in ["buat video", "generate video", "video studio", "bikin video", "create video"]:
            if kw in req:
                idx = req.find(kw) + len(kw)
                title_part = user_request[idx:].strip().strip(":").strip()
                if title_part:
                    intent["title"] = title_part[:200]
                break

        if not intent["title"]:
            intent["title"] = user_request[:200]

        # Duration detection
        if "3 menit" in req or "3 min" in req or "short" in req:
            intent["duration"] = "3-5"
        elif "7 menit" in req or "10 menit" in req or "medium" in req:
            intent["duration"] = "7-10"
        elif "20 menit" in req or "deep dive" in req or "long" in req:
            intent["duration"] = "20+"
        else:
            intent["duration"] = "12-15"

        # Language
        if "english only" in req or "bahasa inggris" in req:
            intent["lang"] = "english"
        elif "indonesia" in req or "bahasa" in req:
            intent["lang"] = "indonesian"
        else:
            intent["lang"] = "bilingual"

        # Section-only generation
        for section in VIDEO_SECTIONS:
            if f"generate {section}" in req or f"buat {section}" in req:
                intent["action"] = f"section_{section}"
                break

        return intent

    def generate_section(self, section: str, intent: Dict) -> str:
        """Generate a single section using LLM"""
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
                    temperature=0.75,
                    max_tokens=4096,
                )
            else:
                result = self.llm.chat(
                    messages=[{"role": "user", "content": user_prompt}],
                    system=cfg["system"],
                    temperature=0.75,
                    max_tokens=4096,
                )
            logger.info(f"Section '{section}' generated: {len(result)} chars")
            return result
        except Exception as e:
            logger.error(f"Failed to generate section '{section}': {e}")
            raise

    def build_video_package(self, user_request: str, sections: Optional[List[str]] = None) -> Dict:
        """
        Build a full video production package.
        Returns dict with all generated sections.
        """
        intent = self.detect_video_intent(user_request)
        sections = sections or VIDEO_SECTIONS

        console.print(Panel(
            f"[cyan]Title:[/cyan] {intent['title']}\n"
            f"[cyan]Duration:[/cyan] {intent['duration']} min\n"
            f"[cyan]Style:[/cyan] {intent['style']}\n"
            f"[cyan]Lang:[/cyan] {intent['lang']}\n"
            f"[cyan]Sections:[/cyan] {', '.join(sections)}\n"
            f"[cyan]Model:[/cyan] {config.VIDEO_STUDIO_MODEL}",
            title="🎬 VIDEO STUDIO - Generating Package",
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
        """Save all generated sections to disk"""
        project_dir.mkdir(parents=True, exist_ok=True)
        saved = []

        # Save each section as .txt
        for section, content in package["sections"].items():
            fpath = project_dir / f"{section}.txt"
            fpath.write_text(content, encoding="utf-8")
            saved.append(fpath)
            console.print(f"  [dim]saved: {fpath.name}[/dim]")

        # Save full JSON package
        json_path = project_dir / "video_package.json"
        json_path.write_text(
            json.dumps(package, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        saved.append(json_path)

        # Save README
        readme_path = project_dir / "README.md"
        readme_content = self._generate_readme(package)
        readme_path.write_text(readme_content, encoding="utf-8")
        saved.append(readme_path)

        return saved

    def _generate_readme(self, package: Dict) -> str:
        intent = package["intent"]
        sections_done = [s for s, c in package["sections"].items() if not c.startswith("ERROR")]
        return f"""# 🎬 Video Production Package

**ID:** {package['id']}
**Created:** {package['created_at']}
**Title:** {intent['title']}
**Duration:** {intent['duration']} minutes
**Style:** {intent['style']}
**Language:** {intent['lang']}

## Generated Sections ({len(sections_done)}/{len(VIDEO_SECTIONS)})

{chr(10).join(f'- ✅ {s}' for s in sections_done)}
{chr(10).join(f'- ❌ {s}' for s in VIDEO_SECTIONS if s not in sections_done)}

## Files
- `script.txt` — Full bilingual script (VO + subtitle + director notes)
- `scenes.txt` — Scene-by-scene Higgsfield AI prompts
- `voice.txt` — ElevenLabs voice direction
- `sound.txt` — Sound design plan with timestamps
- `editing.txt` — Cut timing, transitions, text overlays
- `thumbnails.txt` — 3 thumbnail concepts (1280×720)
- `video_package.json` — Full machine-readable package

## Next Steps
1. Copy Higgsfield prompts from `scenes.txt` → generate visuals
2. Copy VO lines from `script.txt` → paste to ElevenLabs
3. Use `thumbnails.txt` concepts → build in Canva/Nano Banana
4. Follow `sound.txt` for music & SFX
5. Follow `editing.txt` for final edit

---
*Generated by AgentJW Video Studio*
"""

    def display_package_summary(self, package: Dict, project_dir: Path):
        """Display rich summary after generation"""
        intent = package["intent"]
        sections = package["sections"]
        done = sum(1 for v in sections.values() if not v.startswith("ERROR"))

        console.print(Panel(
            f"[green]✅ Package Complete![/green]\n\n"
            f"📁 Location: {project_dir}\n"
            f"🆔 Package ID: {package['id']}\n"
            f"📝 Title: {intent['title'][:60]}...\n"
            f"✓ Sections: {done}/{len(VIDEO_SECTIONS)}\n\n"
            f"[cyan]Files:[/cyan]\n"
            + "\n".join(f"  • {s}.txt" for s in sections.keys()),
            title="🎬 VIDEO STUDIO DONE",
            border_style="green",
        ))


video_studio_tool = VideoStudioTool()
