"""
tools/youtube/youtube_tool.py - YouTube channel toolset builder
Builds automation tools for YouTube channels
"""
import re
from typing import List, Dict
from core.logger import logger, console
from core.models import CodeFile
from rich.panel import Panel


YOUTUBE_TEMPLATES = {
    "auto_upload": {
        "description": "Auto upload videos to YouTube channel",
        "files": ["uploader.py", "auth.py", "video_processor.py", "config.py", "main.py"],
        "deps": ["google-api-python-client", "google-auth-oauthlib", "google-auth-httplib2", "python-dotenv", "moviepy"],
    },
    "thumbnail_gen": {
        "description": "AI thumbnail generator for YouTube",
        "files": ["thumbnail_gen.py", "image_processor.py", "templates.py", "config.py", "main.py"],
        "deps": ["pillow", "requests", "python-dotenv", "openai"],
    },
    "seo_optimizer": {
        "description": "YouTube SEO title/description/tag optimizer",
        "files": ["seo_optimizer.py", "keyword_analyzer.py", "youtube_api.py", "config.py", "main.py"],
        "deps": ["google-api-python-client", "google-auth-oauthlib", "python-dotenv", "requests"],
    },
    "analytics_tracker": {
        "description": "YouTube channel analytics tracker & reporter",
        "files": ["analytics.py", "reporter.py", "youtube_api.py", "config.py", "main.py"],
        "deps": ["google-api-python-client", "google-auth-oauthlib", "pandas", "matplotlib", "python-dotenv"],
    },
    "comment_manager": {
        "description": "Auto comment moderation and reply bot",
        "files": ["comment_bot.py", "moderator.py", "youtube_api.py", "config.py", "main.py"],
        "deps": ["google-api-python-client", "google-auth-oauthlib", "python-dotenv"],
    },
    "content_planner": {
        "description": "AI-powered content calendar and idea generator",
        "files": ["content_planner.py", "idea_generator.py", "scheduler.py", "config.py", "main.py"],
        "deps": ["openai", "python-dotenv", "schedule", "pandas"],
    },
    "clip_extractor": {
        "description": "Auto extract viral clips from long videos",
        "files": ["clip_extractor.py", "analyzer.py", "video_editor.py", "config.py", "main.py"],
        "deps": ["moviepy", "whisper", "python-dotenv", "openai"],
    },
    "full_suite": {
        "description": "Complete YouTube channel automation suite",
        "files": ["main.py", "uploader.py", "seo.py", "analytics.py",
                  "thumbnail_gen.py", "comment_bot.py", "scheduler.py",
                  "youtube_api.py", "config.py", "README.md"],
        "deps": ["google-api-python-client", "google-auth-oauthlib", "google-auth-httplib2",
                 "openai", "pillow", "pandas", "schedule", "python-dotenv", "requests"],
    },
}


class YouTubeTool:
    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from core.llm_client import llm
            self._llm = llm
        return self._llm

    def detect_youtube_intent(self, user_request: str) -> Dict:
        req = user_request.lower()
        detected = {"template": "full_suite", "features": []}

        if "upload" in req or "auto upload" in req:
            detected["template"] = "auto_upload"
        elif "thumbnail" in req:
            detected["template"] = "thumbnail_gen"
        elif "seo" in req or "keyword" in req or "tag" in req:
            detected["template"] = "seo_optimizer"
        elif "analytic" in req or "statistic" in req or "report" in req:
            detected["template"] = "analytics_tracker"
        elif "comment" in req or "reply" in req or "moderat" in req:
            detected["template"] = "comment_manager"
        elif "content" in req or "plan" in req or "idea" in req or "calendar" in req:
            detected["template"] = "content_planner"
        elif "clip" in req or "highlight" in req or "extract" in req:
            detected["template"] = "clip_extractor"
        elif "full" in req or "semua" in req or "all" in req or "suite" in req:
            detected["template"] = "full_suite"

        return detected

    def build_youtube_tools(self, user_request: str) -> List[CodeFile]:
        intent = self.detect_youtube_intent(user_request)
        template = YOUTUBE_TEMPLATES.get(intent["template"], YOUTUBE_TEMPLATES["full_suite"])

        console.print(Panel(
            f"[cyan]YouTube Tool:[/cyan] {intent['template']}\n"
            f"[cyan]Description:[/cyan] {template['description']}\n"
            f"[cyan]Files:[/cyan] {len(template['files'])}\n"
            f"[cyan]Dependencies:[/cyan] {', '.join(template['deps'][:5])}...",
            title="🎬 YouTube Tool Builder",
            border_style="red"
        ))

        system_prompt = """You are an expert YouTube automation developer.
Write complete, production-ready Python code for YouTube channel tools.

RULES:
1. Use YouTube Data API v3 properly
2. Handle OAuth2 authentication correctly
3. Include rate limiting and quota management
4. Complete implementations - no placeholders
5. Include clear setup instructions in config.py
6. Handle errors gracefully
7. Output ONLY raw Python code, no markdown fences
"""
        generated_files = []
        file_contexts = {}

        for file_name in template["files"]:
            if file_name.endswith(".md"):
                # Generate README specially
                readme = self._generate_readme(user_request, template, intent)
                generated_files.append(CodeFile(path=file_name, content=readme, language="markdown"))
                continue

            console.print(f"[agent.coder]  🎬 Writing: {file_name}[/agent.coder]")
            other_ctx = "\n".join(f"--- {k} ---\n{v[:300]}" for k, v in file_contexts.items())

            prompt = f"""Generate complete Python code for YouTube tool file: {file_name}

USER REQUEST: {user_request}
TOOL TYPE: {intent['template']} - {template['description']}
ALL FILES IN PROJECT: {', '.join(template['files'])}
DEPENDENCIES: {', '.join(template['deps'])}

PREVIOUSLY GENERATED:
{other_ctx}

Write COMPLETE code for {file_name}. Raw Python only."""

            try:
                code = self.llm.chat(
                    messages=[{"role": "user", "content": prompt}],
                    system=system_prompt,
                    temperature=0.2,
                    max_tokens=16000,
                )
                code = re.sub(r'^```(?:python|py|markdown)?\n?', '', code, flags=re.MULTILINE)
                code = re.sub(r'\n?```$', '', code, flags=re.MULTILINE)
                code = code.strip()

                generated_files.append(CodeFile(path=file_name, content=code, language="python"))
                file_contexts[file_name] = code[:400]
            except Exception as e:
                logger.error(f"Failed to generate {file_name}: {e}")

        return generated_files

    def _generate_readme(self, request: str, template: Dict, intent: Dict) -> str:
        prompt = f"""Generate a comprehensive README.md for this YouTube tool:
Request: {request}
Type: {intent['template']} - {template['description']}
Dependencies: {', '.join(template['deps'])}

Include: Overview, Setup, Configuration, Usage, Features"""
        try:
            return self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3, max_tokens=16000,
            )
        except Exception:
            return f"# YouTube Tool: {intent['template']}\n\n{template['description']}\n\n## Install\n```\npip install {' '.join(template['deps'])}\n```"


youtube_tool = YouTubeTool()
