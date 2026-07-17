"""Data Models for AgentJW"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

@dataclass
class Message:
    """Chat message model"""
    role: str  # user, assistant, system
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp
        }

@dataclass
class WorkflowStep:
    """Workflow step model"""
    id: str
    name: str
    agent: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: Optional[Dict] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

@dataclass
class Workflow:
    """Workflow model"""
    id: str
    goal: str
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    status: str = "created"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "goal": self.goal,
            "description": self.description,
            "steps": [s.to_dict() if hasattr(s, 'to_dict') else vars(s) for s in self.steps],
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }

@dataclass
class Decision:
    """CEO Decision model"""
    id: str
    context: str
    options: List[str]
    choice: str
    reasoning: str
    confidence: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "context": self.context,
            "options": self.options,
            "choice": self.choice,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "timestamp": self.timestamp
        }

@dataclass
class Capability:
    """Agent capability model"""
    name: str
    description: str
    agent: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)

@dataclass
class Customer:
    """Customer model"""
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    status: str = "active"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Ticket:
    """Support ticket model"""
    id: str
    customer_id: str
    subject: str
    description: str
    status: str = "open"  # open, in_progress, resolved, closed
    priority: str = "medium"
    assigned_to: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    resolved_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at
        }
