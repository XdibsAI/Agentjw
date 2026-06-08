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
