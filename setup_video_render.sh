#!/bin/bash
# setup_video_render.sh
# Adds tools/video/video_renderer.py and a "render_video" intent to orchestrator.py
set -e
cd ~/agentjw

echo "▶ 1. Copying video_renderer.py..."
cp video_renderer.py tools/video/video_renderer.py

ORCH=agents/orchestrator.py
cp "$ORCH" "${ORCH}.bak_$(date +%H%M%S)"

echo "▶ 2. Patching route_intent() — adding render_video keywords..."
python3 - "$ORCH" <<'PYEOF'
import re, sys
path = sys.argv[1]
src = open(path, encoding="utf-8").read()

# 1) Add routing for render_video, placed before the video_build keyword block
ROUTE_PATCH = '''
        render_keywords = [
            "render video", "jadikan video", "generate video file",
            "buatkan videonya", "render videonya", "convert ke video",
            "render final video", "lanjut render",
        ]
        if any(k in lower for k in render_keywords):
            return {"type": "render_video", "confidence": 0.92}
'''

if "render_video" not in src:
    marker = '        if any(k in lower for k in video_keywords):'
    idx = src.find(marker)
    if idx == -1:
        raise SystemExit("ERROR: video_keywords block not found in orchestrator.py")
    src = src[:idx] + ROUTE_PATCH.lstrip("\n") + "\n" + src[idx:]

# 2) Add dispatch in smart_build()
if '"render_video"' not in src.split("def _build_video")[0]:
    marker2 = '        elif intent["type"] == "video_build":'
    idx2 = src.find(marker2)
    if idx2 == -1:
        raise SystemExit("ERROR: video_build dispatch not found in orchestrator.py")
    DISPATCH_PATCH = (
        '        elif intent["type"] == "render_video":\n'
        '            return self._render_video(user_request, session_id)\n'
    )
    src = src[:idx2] + DISPATCH_PATCH + src[idx2:]

# 3) Append _render_video method after _build_video method
if "_render_video" not in src.split("class")[-1] or src.count("_render_video") < 2:
    METHOD = '''
    def _render_video(self, user_request: str, session_id: str) -> Dict:
        """Render final_video.mp4 from a previously generated video package."""
        import json
        from tools.video.video_renderer import video_renderer_tool
        from core.config import config

        # Find target project: explicit id mentioned, else most recent video_* project
        ref = self._find_project_ref(user_request)
        if ref:
            project = ref
        else:
            projects = [p for p in project_manager.list_projects()
                        if p.get("name", "").startswith("video_")]
            if not projects:
                return {"status": "error", "reason": "No video project found. Generate a video package first."}
            project = sorted(projects, key=lambda p: p.get("created_at", ""))[-1]

        project_dir = Path(project["project_dir"])
        package_path = project_dir / "video_package.json"
        if not package_path.exists():
            return {"status": "error", "reason": f"video_package.json not found in {project_dir}"}

        package = json.loads(package_path.read_text(encoding="utf-8"))

        console.print(Panel(f"🎬 RENDERING VIDEO: {project['name']}", border_style="magenta"))
        try:
            out_path = video_renderer_tool.render(package, project_dir)
        except Exception as e:
            return {"status": "error", "reason": f"Render failed: {e}"}

        project_manager.set_status(project["id"], "success")
        return {
            "status": "success",
            "project_id": project["id"],
            "project_dir": str(project_dir),
            "video_path": str(out_path),
        }
'''
    # insert right after the end of _build_video method (before next "    def ")
    bv_idx = src.find("def _build_video")
    if bv_idx == -1:
        # _build_video not present yet — append at end of class instead
        src = src.rstrip() + "\n" + METHOD
    else:
        next_def = src.find("\n    def ", bv_idx + 10)
        if next_def == -1:
            src = src.rstrip() + "\n" + METHOD
        else:
            src = src[:next_def] + "\n" + METHOD + src[next_def:]

open(path, "w", encoding="utf-8").write(src)
print("OK: orchestrator.py patched")
PYEOF

echo "▶ 3. Checking syntax..."
python3 -m py_compile "$ORCH" tools/video/video_renderer.py
echo "✅ Done. Restart api_server to apply:"
echo "   pkill -f 'uvicorn api_server' && nohup venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 18790 > api.log 2>&1 &"
