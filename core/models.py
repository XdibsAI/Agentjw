"""
core/models.py - Shared Pydantic data models (GOD MODE)
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class AgentRole(str, Enum):
    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"
    CODER = "coder"
    REVIEWER = "reviewer"
    REPAIR = "repair"
    MEMORY = "memory"
    CRITIC = "critic"
    TRADING = "trading"
    YOUTUBE = "youtube"
    PROJECT_MANAGER = "project_manager"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    REPAIR_NEEDED = "repair_needed"
    PAUSED = "paused"
    PARTIAL = "partial"


class ToolType(str, Enum):
    TRADING = "trading"
    YOUTUBE = "youtube"
    CODE_REPAIR = "code_repair"
    PROJECT_BUILD = "project_build"
    ANALYSIS = "analysis"
    GENERAL = "general"


class ExecutionResult(BaseModel):
    success: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    files_created: List[str] = Field(default_factory=list)
    execution_time: float = 0.0
    error_type: Optional[str] = None


class Task(BaseModel):
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    subtasks: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProjectPlan(BaseModel):
    project_name: str
    description: str
    tech_stack: List[str] = Field(default_factory=list)
    directory_structure: Dict[str, Any] = Field(default_factory=dict)
    files_to_create: List[Dict[str, str]] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    entry_point: str = "main.py"
    tasks: List[str] = Field(default_factory=list)


class CodeFile(BaseModel):
    path: str
    content: str
    language: str = "python"
    description: str = ""


class AgentMessage(BaseModel):
    role: AgentRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BuildSession(BaseModel):
    session_id: str
    user_request: str
    plan: Optional[ProjectPlan] = None
    generated_files: List[CodeFile] = Field(default_factory=list)
    execution_results: List[ExecutionResult] = Field(default_factory=list)
    repair_attempts: int = 0
    status: TaskStatus = TaskStatus.PENDING
    final_output: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class ManagedProject(BaseModel):
    """Persistent project tracked by AgentJW"""
    id: str
    name: str
    description: str
    project_dir: str
    status: TaskStatus = TaskStatus.PENDING
    tool_type: ToolType = ToolType.GENERAL
    files: List[str] = Field(default_factory=list)
    tasks_completed: List[str] = Field(default_factory=list)
    tasks_pending: List[str] = Field(default_factory=list)
    errors_history: List[str] = Field(default_factory=list)
    notes: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryEntry(BaseModel):
    id: str
    type: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: datetime = Field(default_factory=datetime.now)
    importance: float = 1.0
