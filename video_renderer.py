"""
tools/video/video_renderer.py - AgentJW Video Renderer
Turns a generated video_package (script + scenes text) into an actual
final_video.mp4 using:
  - OpenAI TTS (tts-1) for narration audio per segment
  - Pillow for static captioned background images per segment
  - moviepy + ffmpeg for assembly (image+audio per segment, concatenated)

No external image/video-gen API required (per project decision: skip
Higgsfield/Replicate for now, static images + TTS + ffmpeg only).
"""
import re
import textwrap
import requests
from pathlib import Path
from typing import List, Dict

from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

from core.config import config
from core.logger import logger, console

OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"
DEFAULT_VOICE = "onyx"          # deep, documentary-style voice
VIDEO_SIZE = (1280, 720)
BG_COLORS = [
    (20, 24, 38), (35, 20, 45), (15, 35, 40),
    (40, 25, 20), (22, 30, 50), (30, 30, 30),
]


class VideoRendererTool:
    """Renders a video_package dict (from VideoStudioTool) into final_video.mp4"""

    def __init__(self):
        self.api_key = config.OPENAI_API_KEY

    # ── 1. PARSE SCRIPT INTO NARRATION SEGMENTS ────────────────────────────
    def extract_segments(self, package: Dict, max_segments: int = 12) -> List[str]:
        """
        Extract narration lines from package['sections']['script'].
        Script format is lines like: "English VO | Indonesian subtitle | note"
        Falls back to splitting by sentences if that pattern isn't found.
        """
        script = package.get("sections", {}).get("script", "")
        segments: List[str] = []

        for line in script.splitlines():
            line = line.strip().lstrip("-•* ").strip()
            if not line or line.startswith("["):
                continue
            if "|" in line:
                vo = line.split("|")[0].strip()
                vo = re.sub(r'^["\'\d.\)\s]+', "", vo).strip()
                if len(vo) > 5:
                    segments.append(vo)

        if not segments:
            # Fallback: split whole script into sentences
            text = re.sub(r'\[.*?\]', ' ', script)
            sentences = re.split(r'(?<=[.!?])\s+', text)
            segments = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not segments:
            segments = [package.get("intent", {}).get("title", "Untitled video")]

        return segments[:max_segments]

    # ── 2. TTS via OpenAI ───────────────────────────────────────────────────
    def generate_audio(self, text: str, out_path: Path, voice: str = DEFAULT_VOICE) -> Path:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set in .env — required for TTS")

        resp = requests.post(
            OPENAI_TTS_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": "tts-1", "input": text, "voice": voice},
            timeout=120,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"TTS failed ({resp.status_code}): {resp.text[:300]}")

        out_path.write_bytes(resp.content)
        return out_path

    # ── 3. CAPTIONED BACKGROUND IMAGE ───────────────────────────────────────
    def generate_scene_image(self, text: str, index: int, out_path: Path) -> Path:
        color = BG_COLORS[index % len(BG_COLORS)]
        img = Image.new("RGB", VIDEO_SIZE, color)
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48
            )
        except Exception:
            font = ImageFont.load_default()

        wrapped = textwrap.fill(text, width=32)
        bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=12)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = (VIDEO_SIZE[0] - w) / 2, (VIDEO_SIZE[1] - h) / 2

        draw.multiline_text(
            (x, y), wrapped, font=font, fill=(255, 255, 255),
            align="center", spacing=12,
        )

        img.save(out_path)
        return out_path

    # ── 4. RENDER FULL VIDEO ─────────────────────────────────────────────────
    def render(self, package: Dict, project_dir: Path, voice: str = DEFAULT_VOICE) -> Path:
        project_dir = Path(project_dir)
        assets_dir = project_dir / "render_assets"
        assets_dir.mkdir(parents=True, exist_ok=True)

        segments = self.extract_segments(package)
        if not segments:
            raise RuntimeError("No narration segments found in package script")

        clips = []
        console.print(f"[cyan]Rendering {len(segments)} segments...[/cyan]")

        for i, text in enumerate(segments):
            audio_path = assets_dir / f"seg_{i:02d}.mp3"
            image_path = assets_dir / f"seg_{i:02d}.png"

            try:
                self.generate_audio(text, audio_path, voice=voice)
            except Exception as e:
                logger.error(f"TTS failed for segment {i}: {e}")
                continue

            self.generate_scene_image(text, i, image_path)

            audio_clip = AudioFileClip(str(audio_path))
            duration = max(audio_clip.duration, 1.5)
            image_clip = (
                ImageClip(str(image_path))
                .set_duration(duration)
                .set_audio(audio_clip)
            )
            clips.append(image_clip)
            console.print(f"  [green]✓[/green] segment {i+1}/{len(segments)} "
                          f"({duration:.1f}s)")

        if not clips:
            raise RuntimeError("No segments rendered successfully (check OPENAI_API_KEY)")

        final = concatenate_videoclips(clips, method="compose")
        out_path = project_dir / "final_video.mp4"
        final.write_videofile(
            str(out_path), fps=24, codec="libx264", audio_codec="aac",
            verbose=False, logger=None,
        )

        for c in clips:
            c.close()
        final.close()

        console.print(f"[bold green]✅ Video rendered: {out_path}[/bold green]")
        return out_path


video_renderer_tool = VideoRendererTool()
