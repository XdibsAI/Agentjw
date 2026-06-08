"""
api_server.py - AgentJW REST API Server
FastAPI server exposing AgentJW capabilities including Video Studio
Run: uvicorn api_server:app --host 0.0.0.0 --port 8000
"""
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── App Init ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="AgentJW API",
    description="AgentJW GOD MODE - REST API with Video Studio",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request/Response Models ──────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    history: Optional[List[Dict]] = []

class BuildRequest(BaseModel):
    task: str
    session_id: Optional[str] = None

class VideoPackageRequest(BaseModel):
    title: str
    duration: Optional[str] = "12-15"
    lang: Optional[str] = "bilingual"
    style: Optional[str] = "cinematic documentary"
    tone: Optional[str] = "confident, urgent, no fluff"
    sections: Optional[List[str]] = None  # None = all sections
    model: Optional[str] = None  # override model per-request

class VideoSectionRequest(BaseModel):
    section: str  # script|scenes|voice|sound|editing|thumbnails
    title: str
    duration: Optional[str] = "12-15"
    lang: Optional[str] = "bilingual"
    style: Optional[str] = "cinematic documentary"
    tone: Optional[str] = "confident, urgent, no fluff"

class JSXParseRequest(BaseModel):
    jsx_content: str  # raw JSX string from Claude output
    title: Optional[str] = None

# ── Background job tracker ───────────────────────────────────────────────────
_jobs: Dict[str, Dict] = {}

def _set_job(job_id: str, status: str, result: Any = None, error: str = None):
    _jobs[job_id] = {
        "job_id": job_id,
        "status": status,
        "result": result,
        "error": error,
        "updated_at": datetime.now().isoformat(),
    }

# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    from core.config import config
    return {
        "status": "ok",
        "version": "2.0.0",
        "model": config.get_model(),
        "provider": config.LLM_PROVIDER,
        "video_studio": bool(config.OPENROUTER_API_KEY),
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/")
def root():
    return {
        "name": "AgentJW API",
        "version": "2.0.0",
        "endpoints": [
            "GET  /health",
            "POST /chat",
            "POST /build",
            "POST /video/package",
            "POST /video/section",
            "POST /video/parse-jsx",
            "GET  /video/jobs/{job_id}",
            "GET  /video/projects",
            "GET  /projects",
        ],
    }

# ── Chat ─────────────────────────────────────────────────────────────────────
@app.post("/chat")
def chat(req: ChatRequest):
    try:
        from agents.orchestrator import orchestrator
        session_id = req.session_id or str(uuid.uuid4())
        response = orchestrator.chat(req.message, req.history or [], session_id)
        return {"response": response, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Build ────────────────────────────────────────────────────────────────────
@app.post("/build")
def build(req: BuildRequest):
    try:
        from agents.orchestrator import orchestrator
        session_id = req.session_id or str(uuid.uuid4())
        result = orchestrator.smart_build(req.task, session_id)
        return {"status": "success", "result": result, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Video Studio ─────────────────────────────────────────────────────────────
@app.post("/video/package")
def video_package(req: VideoPackageRequest, background_tasks: BackgroundTasks):
    """
    Generate full video production package (async background job).
    Returns job_id immediately. Poll /video/jobs/{job_id} for result.
    """
    from core.config import config

    if not config.OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="OPENROUTER_API_KEY not set in .env"
        )

    job_id = str(uuid.uuid4())[:8]
    _set_job(job_id, "queued")

    def _run():
        try:
            _set_job(job_id, "running")
            from tools.video.video_studio_tool import video_studio_tool

            # Override model if specified
            if req.model:
                config.VIDEO_STUDIO_MODEL = req.model

            intent = {
                "title": req.title,
                "duration": req.duration,
                "lang": req.lang,
                "style": req.style,
                "tone": req.tone,
            }

            sections = req.sections or ["script", "scenes", "voice", "sound", "editing", "thumbnails"]
            package = video_studio_tool.build_video_package(req.title, sections)
            package["intent"] = intent

            # Save to projects dir
            project_name = f"video_{job_id}"
            project_dir = config.PROJECTS_DIR / project_name
            saved_files = video_studio_tool.save_package(package, project_dir)

            # Register in memory
            from tools.project_manager.manager import project_manager
            pid = project_manager.register_project(
                name=project_name,
                description=req.title,
                project_dir=str(project_dir),
                tool_type="youtube",
            )

            _set_job(job_id, "done", {
                "project_id": pid,
                "project_dir": str(project_dir),
                "package_id": package["id"],
                "sections_done": [s for s, v in package["sections"].items() if not v.startswith("ERROR")],
                "files": [str(f) for f in saved_files],
                "title": req.title,
            })
        except Exception as e:
            _set_job(job_id, "error", error=str(e))

    background_tasks.add_task(_run)
    return {"job_id": job_id, "status": "queued", "message": "Generating package in background..."}


@app.post("/video/section")
def video_section(req: VideoSectionRequest):
    """
    Generate a single section synchronously.
    Faster — good for testing individual sections.
    """
    from core.config import config
    if not config.OPENROUTER_API_KEY:
        raise HTTPException(status_code=400, detail="OPENROUTER_API_KEY not set in .env")

    try:
        from tools.video.video_studio_tool import video_studio_tool
        intent = {
            "title": req.title,
            "duration": req.duration,
            "lang": req.lang,
            "style": req.style,
            "tone": req.tone,
        }
        content = video_studio_tool.generate_section(req.section, intent)
        return {
            "section": req.section,
            "content": content,
            "chars": len(content),
            "title": req.title,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/video/parse-jsx")
def parse_jsx(req: JSXParseRequest):
    """
    Parse JSX production package from Claude output.
    Extracts: title, scene count, VO lines, Higgsfield prompts, thumbnail concepts.
    """
    jsx = req.jsx_content
    if not jsx.strip():
        raise HTTPException(status_code=400, detail="Empty JSX content")

    import re

    def count(pattern):
        return len(re.findall(pattern, jsx))

    # Extract title
    title_match = re.search(r'title(?:En)?:\s*["\']([^"\']+)["\']', jsx)
    title = title_match.group(1) if title_match else (req.title or "Unknown")

    # Extract Higgsfield prompts
    higgsfield_matches = re.findall(
        r'higgsfieldPrompt:\s*["\']([^"\']{20,})["\']', jsx, re.DOTALL
    )

    # Extract VO lines
    vo_matches = re.findall(r'\bvo:\s*["\']([^"\']+)["\']', jsx)

    # Extract subtitle lines
    sub_matches = re.findall(r'\bsub:\s*["\']([^"\']+)["\']', jsx)

    # Extract thumbnail concepts
    thumb_matches = re.findall(r'concept:\s*["\']([^"\']+)["\']', jsx)

    # Extract camera movements
    camera_matches = re.findall(r'camera:\s*["\']([^"\']+)["\']', jsx)

    # Extract style references
    style_matches = re.findall(r'style:\s*["\']([^"\']+)["\']', jsx)

    return {
        "parsed": True,
        "title": title,
        "stats": {
            "scenes": count(r'higgsfieldPrompt:'),
            "vo_lines": len(vo_matches),
            "subtitle_lines": len(sub_matches),
            "thumbnails": len(thumb_matches),
            "jsx_size_kb": round(len(jsx) / 1024, 1),
        },
        "higgsfield_prompts": higgsfield_matches[:12],
        "vo_lines": vo_matches[:20],
        "subtitle_lines": sub_matches[:20],
        "thumbnail_concepts": thumb_matches,
        "camera_movements": camera_matches[:12],
        "style_references": style_matches[:12],
    }


@app.get("/video/jobs/{job_id}")
def get_job(job_id: str):
    """Poll background job status"""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@app.get("/video/projects")
def list_video_projects():
    """List all video projects"""
    try:
        from memory.memory_store import memory_store
        projects = memory_store.list_projects(tool_type="youtube")
        return {"projects": projects, "total": len(projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/video/download/{project_id}")
def download_package(project_id: str):
    """Download video_package.json for a project"""
    try:
        from memory.memory_store import memory_store
        proj = memory_store.get_project(project_id)
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        json_path = Path(proj["project_dir"]) / "video_package.json"
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="Package file not found")
        return FileResponse(str(json_path), media_type="application/json",
                            filename=f"video_package_{project_id}.json")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Projects ─────────────────────────────────────────────────────────────────
@app.get("/projects")
def list_projects():
    try:
        from memory.memory_store import memory_store
        projects = memory_store.list_projects()
        return {"projects": projects, "total": len(projects)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}")
def get_project(project_id: str):
    try:
        from memory.memory_store import memory_store
        proj = memory_store.get_project(project_id)
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
        return proj
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=False)
