"""
API Server v1 - REST API dengan authentication
"""

import json
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

sys.path.insert(0, '/home/dibs/agentjw')
sys.path.insert(0, '/home/dibs/agentjw/core')

from sicuan.platform.api_gateway import get_api_gateway
from sicuan.platform.auth import get_auth
from sicuan.platform.workspace import get_workspace
from sicuan.platform.project_manager import get_project_manager
from sicuan.platform.job_queue import get_job_queue
from sicuan.chat import SiCuanChat

app = FastAPI(title="SiCuan API", version="v1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatRequest(BaseModel):
    message: str
    workspace_id: str
    user_id: Optional[int] = None

class ProjectRequest(BaseModel):
    name: str
    workspace_id: str

class WebhookRequest(BaseModel):
    url: str
    events: List[str]
    workspace_id: str


# Middleware: Auth
async def authenticate(request: Request):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    gateway = get_api_gateway()
    result = gateway.authenticate({"X-API-Key": api_key})
    if not result["success"]:
        raise HTTPException(status_code=result.get("status", 401), detail=result.get("error"))
    
    return result["workspace_id"]


# Routes
@app.get("/")
def root():
    return {"name": "SiCuan API", "version": "v1.0.0", "status": "ok"}

@app.post("/v1/chat")
async def chat(request: ChatRequest, api_key: str = Header(...)):
    """Chat dengan SiCuan"""
    gateway = get_api_gateway()
    result = gateway.authenticate({"X-API-Key": api_key})
    if not result["success"]:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    workspace_id = result["workspace_id"]
    if request.workspace_id and request.workspace_id != workspace_id:
        raise HTTPException(status_code=403, detail="Workspace mismatch")
    
    chat = SiCuanChat()
    chat.brain._current_workspace_id = workspace_id
    response = chat.chat(request.message, user_id=request.user_id or 0, workspace_id=workspace_id)
    
    return {"response": response, "workspace_id": workspace_id}

@app.get("/v1/workspace/{workspace_id}/projects")
async def list_projects(workspace_id: str, api_key: str = Header(...)):
    """List projects di workspace"""
    gateway = get_api_gateway()
    result = gateway.authenticate({"X-API-Key": api_key})
    if not result["success"]:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if workspace_id != result["workspace_id"]:
        raise HTTPException(status_code=403, detail="Workspace mismatch")
    
    pm = get_project_manager()
    projects = pm.list_projects(workspace_id)
    return {"projects": projects, "workspace_id": workspace_id}

@app.post("/v1/project")
async def create_project(request: ProjectRequest, api_key: str = Header(...)):
    """Create project"""
    gateway = get_api_gateway()
    result = gateway.authenticate({"X-API-Key": api_key})
    if not result["success"]:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if request.workspace_id != result["workspace_id"]:
        raise HTTPException(status_code=403, detail="Workspace mismatch")
    
    pm = get_project_manager()
    project = pm.create_project(request.workspace_id, request.name)
    return {"project": project, "workspace_id": request.workspace_id}

@app.get("/v1/workspace/{workspace_id}/jobs")
async def list_jobs(workspace_id: str, api_key: str = Header(...)):
    """List jobs di workspace"""
    gateway = get_api_gateway()
    result = gateway.authenticate({"X-API-Key": api_key})
    if not result["success"]:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if workspace_id != result["workspace_id"]:
        raise HTTPException(status_code=403, detail="Workspace mismatch")
    
    queue = get_job_queue()
    jobs = queue.get_jobs(workspace_id, limit=20)
    return {"jobs": jobs, "workspace_id": workspace_id}

@app.get("/v1/workspace/{workspace_id}/billing")
async def get_billing(workspace_id: str, api_key: str = Header(...)):
    """Get billing info"""
    gateway = get_api_gateway()
    result = gateway.authenticate({"X-API-Key": api_key})
    if not result["success"]:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if workspace_id != result["workspace_id"]:
        raise HTTPException(status_code=403, detail="Workspace mismatch")
    
    from sicuan.platform.billing import get_billing
    billing = get_billing()
    usage = billing.get_usage(workspace_id)
    return {"usage": usage, "workspace_id": workspace_id}

@app.post("/v1/webhook")
async def register_webhook(request: WebhookRequest, api_key: str = Header(...)):
    """Register webhook"""
    gateway = get_api_gateway()
    result = gateway.authenticate({"X-API-Key": api_key})
    if not result["success"]:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if request.workspace_id != result["workspace_id"]:
        raise HTTPException(status_code=403, detail="Workspace mismatch")
    
    from sicuan.platform.webhook import get_webhook_engine
    webhook = get_webhook_engine()
    result = webhook.register(request.workspace_id, request.url, request.events)
    return {"webhook": result}
