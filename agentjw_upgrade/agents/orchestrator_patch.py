# ─────────────────────────────────────────────────────────────────────────────
# PATCH untuk agents/orchestrator.py
# Tambahkan 3 hal:
#   1. video_keywords di route_intent()
#   2. "video_build" di smart_build()
#   3. method _build_video() baru
# ─────────────────────────────────────────────────────────────────────────────

# STEP 1 — Tambahkan di route_intent(), setelah blok youtube_keywords:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
VIDEO_ROUTE_PATCH = '''
        video_keywords = [
            "video studio", "buat video", "generate video", "bikin video",
            "production package", "higgsfield", "elevenlabs script",
            "video package", "script youtube", "scenes video",
            "thumbnail video", "sound design", "editing plan",
            "create video", "video documentary", "video ai",
        ]
        if any(k in lower for k in video_keywords):
            return {"type": "video_build", "confidence": 0.92}
'''

# STEP 2 — Tambahkan di smart_build(), setelah elif youtube_build:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SMART_BUILD_PATCH = '''
        elif intent["type"] == "video_build":
            return self._build_video(user_request, session_id)
'''

# STEP 3 — Tambahkan sebagai method baru di class OrchestratorAgent:
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
BUILD_VIDEO_METHOD = '''
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

        # Build the package
        package = video_studio_tool.build_video_package(user_request)

        # Save to projects dir
        project_name = f"video_{session_id[:6]}"
        project_dir = config.PROJECTS_DIR / project_name
        saved_files = video_studio_tool.save_package(package, project_dir)

        # Register in memory
        pid = project_manager.register_project(
            name=project_name,
            description=user_request[:200],
            project_dir=str(project_dir),
            tool_type="youtube",
            tasks=["Review script", "Generate Higgsfield visuals",
                   "Record ElevenLabs VO", "Edit video", "Upload to YouTube"],
            metadata={"package_id": package["id"], "video_studio": True},
        )
        project_manager.save_files(
            pid,
            [__import__("core.models", fromlist=["CodeFile"]).CodeFile(
                path=f.name, content=f.read_text(encoding="utf-8"),
                language="text", description=f"Video studio: {f.stem}"
            ) for f in saved_files if f.suffix in (".txt", ".json", ".md")]
        )
        project_manager.set_status(pid, "success")
        video_studio_tool.display_package_summary(package, project_dir)

        return {
            "status": "success",
            "project_id": pid,
            "project_dir": str(project_dir),
            "package_id": package["id"],
            "sections_done": list(package["sections"].keys()),
        }
'''
