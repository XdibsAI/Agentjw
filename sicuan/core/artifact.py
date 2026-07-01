"""
Artifact System - Setiap task menghasilkan artifact yang lengkap
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


@dataclass
class KnowledgeArtifact:
    """Pengetahuan yang ditemukan"""
    entity: str
    fact: str
    confidence: float = 1.0
    source: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class DecisionArtifact:
    """Keputusan yang diambil"""
    action: str
    reason: str
    reason_code: str
    alternatives: List[str] = field(default_factory=list)
    confidence: float = 1.0
    metadata: Dict = field(default_factory=dict)


@dataclass
class OutcomeArtifact:
    """Hasil pelaksanaan"""
    success: bool
    result: str
    duration: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ReflectionArtifact:
    """Evaluasi internal"""
    confidence: float = 0.0
    learnings: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


@dataclass
class TaskArtifact:
    """Artifact lengkap dari satu task"""
    task_id: str
    action: str
    target: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    knowledge: List[KnowledgeArtifact] = field(default_factory=list)
    decisions: List[DecisionArtifact] = field(default_factory=list)
    outcome: Optional[OutcomeArtifact] = None
    reflection: Optional[ReflectionArtifact] = None
    
    def to_dict(self) -> Dict:
        """Convert ke dictionary"""
        return {
            "task_id": self.task_id,
            "action": self.action,
            "target": self.target,
            "timestamp": self.timestamp,
            "knowledge": [
                {
                    "entity": k.entity,
                    "fact": k.fact,
                    "confidence": k.confidence,
                    "source": k.source,
                    "metadata": k.metadata
                }
                for k in self.knowledge
            ],
            "decisions": [
                {
                    "action": d.action,
                    "reason": d.reason,
                    "reason_code": d.reason_code,
                    "alternatives": d.alternatives,
                    "confidence": d.confidence,
                    "metadata": d.metadata
                }
                for d in self.decisions
            ],
            "outcome": {
                "success": self.outcome.success,
                "result": self.outcome.result,
                "duration": self.outcome.duration,
                "errors": self.outcome.errors,
                "metadata": self.outcome.metadata
            } if self.outcome else None,
            "reflection": {
                "confidence": self.reflection.confidence,
                "learnings": self.reflection.learnings,
                "next_actions": self.reflection.next_actions,
                "concerns": self.reflection.concerns,
                "metadata": self.reflection.metadata
            } if self.reflection else None
        }
    
    def save(self, directory: Path = Path("/home/dibs/agentjw/memory/artifacts")):
        """Simpan artifact ke file"""
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{self.task_id}.json"
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, task_id: str, directory: Path = Path("/home/dibs/agentjw/memory/artifacts")):
        """Load artifact dari file"""
        file_path = directory / f"{task_id}.json"
        if not file_path.exists():
            return None
        with open(file_path) as f:
            data = json.load(f)
        # TODO: reconstruct from data
        return None
