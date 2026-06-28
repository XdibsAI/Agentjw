"""
Artifact Event System - Setiap task menghasilkan event yang dipublish ke semua subscriber
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import json
from pathlib import Path
import uuid


@dataclass
class Evidence:
    """Bukti untuk outcome"""
    files: List[str] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)


@dataclass
class CandidateAction:
    """Kandidat action dengan skor"""
    action: str
    score: float
    reason: str


@dataclass
class KnowledgeEvent:
    """Pengetahuan dengan atribut"""
    entity: str
    attribute: str
    value: Any
    confidence: float = 1.0
    source: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass
class DecisionEvent:
    """Keputusan dengan alternatif"""
    selected_action: str
    candidate_actions: List[CandidateAction] = field(default_factory=list)
    reason_code: str = ""
    evidence: Dict = field(default_factory=dict)
    confidence: float = 1.0
    constraints: List[str] = field(default_factory=list)


@dataclass
class OutcomeEvent:
    """Hasil dengan evidence"""
    success: bool
    result: str
    duration: float = 0.0
    evidence: Evidence = field(default_factory=Evidence)
    errors: List[str] = field(default_factory=list)


@dataclass
class ReflectionEvent:
    """Refleksi (hanya jika valuable)"""
    confidence: float = 0.0
    learnings: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    concerns: List[str] = field(default_factory=list)
    should_learn: bool = True


@dataclass
class ArtifactEvent:
    """Event dari satu task - dipublish ke semua subscriber"""
    artifact_id: str = field(default_factory=lambda: f"art_{uuid.uuid4().hex[:8]}")
    parent_artifact_id: Optional[str] = None
    schema_version: str = "2.0"
    session_id: str = ""
    project: str = ""
    action: str = ""
    target: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    executor_version: str = "2.0.0"
    planner_version: str = "2.0.0"
    brain_version: str = "2.0.0"
    
    knowledge: List[KnowledgeEvent] = field(default_factory=list)
    decision: Optional[DecisionEvent] = None
    outcome: Optional[OutcomeEvent] = None
    reflection: Optional[ReflectionEvent] = None
    
    def publish(self):
        """Publish event ke semua subscriber"""
        # Save dulu ke disk
        try:
            self.save()
            print(f"[ARTIFACT] Saved to disk: {self.artifact_id}")
        except Exception as e:
            print(f"[ARTIFACT] Save error: {e}")
        # Baru publish ke subscriber
        from sicuan.core.artifact_subscribers import ArtifactSubscriberRegistry
        registry = ArtifactSubscriberRegistry()
        registry.publish(self)
    
    def save(self, directory: Path = Path("/home/dibs/agentjw/memory/artifacts")):
        """Simpan ke file"""
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / f"{self.artifact_id}.json"
        with open(file_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    def to_dict(self) -> Dict:
        """Convert ke dictionary"""
        return {
            "artifact_id": self.artifact_id,
            "parent_artifact_id": self.parent_artifact_id,
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "project": self.project,
            "action": self.action,
            "target": self.target,
            "timestamp": self.timestamp,
            "executor_version": self.executor_version,
            "planner_version": self.planner_version,
            "brain_version": self.brain_version,
            "knowledge": [
                {
                    "entity": k.entity,
                    "attribute": k.attribute,
                    "value": k.value,
                    "confidence": k.confidence,
                    "source": k.source,
                    "metadata": k.metadata
                }
                for k in self.knowledge
            ],
            "decision": {
                "selected_action": self.decision.selected_action,
                "candidate_actions": [
                    {"action": c.action, "score": c.score, "reason": c.reason}
                    for c in self.decision.candidate_actions
                ],
                "reason_code": self.decision.reason_code,
                "evidence": self.decision.evidence,
                "confidence": self.decision.confidence,
                "constraints": self.decision.constraints
            } if self.decision else None,
            "outcome": {
                "success": self.outcome.success,
                "result": self.outcome.result,
                "duration": self.outcome.duration,
                "evidence": {
                    "files": self.outcome.evidence.files,
                    "logs": self.outcome.evidence.logs,
                    "metrics": self.outcome.evidence.metrics,
                    "artifacts": self.outcome.evidence.artifacts
                },
                "errors": self.outcome.errors
            } if self.outcome else None,
            "reflection": {
                "confidence": self.reflection.confidence,
                "learnings": self.reflection.learnings,
                "next_actions": self.reflection.next_actions,
                "concerns": self.reflection.concerns,
                "should_learn": self.reflection.should_learn
            } if self.reflection else None
        }
