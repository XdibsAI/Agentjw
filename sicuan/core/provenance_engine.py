"""
Provenance Engine - Audit Trail & Sumber Data
Mencatat asal-usul setiap keputusan dan action
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class ProvenanceType(Enum):
    """Jenis sumber provenance"""
    LLM = "llm"
    LEGACY = "legacy"
    RULE = "rule"
    USER = "user"
    SYSTEM = "system"
    GOAL = "goal"
    CONTEXT = "context"
    MEMORY = "memory"
    SHADOW = "shadow"


@dataclass
class ProvenanceRecord:
    """Record provenance untuk satu keputusan/action"""
    id: str
    timestamp: str
    action: str
    target: str
    source_type: str  # ProvenanceType
    source_details: Dict[str, Any]
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    reasoning: List[str]
    confidence: float
    session_id: str
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "action": self.action,
            "target": self.target,
            "source_type": self.source_type,
            "source_details": self.source_details,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "session_id": self.session_id,
            "parent_id": self.parent_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProvenanceRecord':
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            action=data["action"],
            target=data["target"],
            source_type=data["source_type"],
            source_details=data["source_details"],
            input_data=data["input_data"],
            output_data=data["output_data"],
            reasoning=data["reasoning"],
            confidence=data["confidence"],
            session_id=data["session_id"],
            parent_id=data.get("parent_id"),
            metadata=data.get("metadata", {})
        )


class ProvenanceEngine:
    """
    Provenance Engine - Mencatat asal-usul setiap keputusan
    """
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.records_file = self.memory_dir / "provenance_records.json"
        self.records: List[ProvenanceRecord] = []
        self._load()
    
    def record_decision(
        self,
        action: str,
        target: str,
        source_type: str,
        source_details: Dict[str, Any],
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        reasoning: List[str],
        confidence: float,
        session_id: str,
        parent_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> ProvenanceRecord:
        """Catat keputusan/action dengan provenance"""
        
        record = ProvenanceRecord(
            id=f"prov_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now().isoformat(),
            action=action,
            target=target,
            source_type=source_type,
            source_details=source_details,
            input_data=input_data,
            output_data=output_data,
            reasoning=reasoning,
            confidence=confidence,
            session_id=session_id,
            parent_id=parent_id,
            metadata=metadata or {}
        )
        
        self.records.append(record)
        self._save()
        print(f"[PROVENANCE] Recorded: {action} -> {target} (source={source_type})")
        return record
    
    def record_llm_decision(
        self,
        action: str,
        target: str,
        llm_response: Dict[str, Any],
        user_message: str,
        context: Dict[str, Any],
        session_id: str,
        confidence: float = 1.0
    ) -> ProvenanceRecord:
        """Catat keputusan dari LLM"""
        return self.record_decision(
            action=action,
            target=target,
            source_type=ProvenanceType.LLM.value,
            source_details={
                "llm_model": llm_response.get("model", "unknown"),
                "llm_provider": llm_response.get("provider", "openrouter"),
                "raw_response": llm_response.get("raw", "")[:500]
            },
            input_data={
                "user_message": user_message,
                "context": context
            },
            output_data={
                "action": action,
                "target": target,
                "response": llm_response.get("response", "")[:500]
            },
            reasoning=llm_response.get("reasoning", ["LLM decision"]),
            confidence=confidence,
            session_id=session_id
        )
    
    def record_legacy_decision(
        self,
        action: str,
        target: str,
        matched_pattern: str,
        user_message: str,
        session_id: str
    ) -> ProvenanceRecord:
        """Catat keputusan dari Legacy (rule-based)"""
        return self.record_decision(
            action=action,
            target=target,
            source_type=ProvenanceType.LEGACY.value,
            source_details={
                "matched_pattern": matched_pattern,
                "rule_type": "if-elif"
            },
            input_data={
                "user_message": user_message
            },
            output_data={
                "action": action,
                "target": target
            },
            reasoning=[f"Matched pattern: {matched_pattern}"],
            confidence=0.8,
            session_id=session_id
        )
    
    def record_goal_decision(
        self,
        action: str,
        target: str,
        goal_id: str,
        goal_title: str,
        session_id: str
    ) -> ProvenanceRecord:
        """Catat keputusan dari Goal"""
        return self.record_decision(
            action=action,
            target=target,
            source_type=ProvenanceType.GOAL.value,
            source_details={
                "goal_id": goal_id,
                "goal_title": goal_title
            },
            input_data={},
            output_data={
                "action": action,
                "target": target
            },
            reasoning=[f"Goal-driven: {goal_title}"],
            confidence=0.9,
            session_id=session_id
        )
    
    def record_shadow_comparison(
        self,
        action: str,
        target: str,
        executive_result: Dict,
        legacy_result: Dict,
        match: bool,
        session_id: str
    ) -> ProvenanceRecord:
        """Catat hasil Shadow Mode comparison"""
        return self.record_decision(
            action=action,
            target=target,
            source_type=ProvenanceType.SHADOW.value,
            source_details={
                "match": match,
                "executive_success": executive_result.get("success", False),
                "legacy_success": legacy_result.get("success", False)
            },
            input_data={
                "executive_result": executive_result,
                "legacy_result": legacy_result
            },
            output_data={
                "match": match,
                "action": action
            },
            reasoning=[
                f"Executive: {executive_result.get('result', '')[:100]}",
                f"Legacy: {legacy_result.get('result', '')[:100]}",
                f"Match: {match}"
            ],
            confidence=1.0,
            session_id=session_id
        )
    
    def get_chain(self, record_id: str) -> List[ProvenanceRecord]:
        """Dapatkan chain of provenance untuk satu record"""
        chain = []
        current_id = record_id
        
        while current_id:
            record = self.get_record(current_id)
            if not record:
                break
            chain.append(record)
            current_id = record.parent_id
        
        return chain
    
    def get_record(self, record_id: str) -> Optional[ProvenanceRecord]:
        """Dapatkan record by ID"""
        for r in self.records:
            if r.id == record_id:
                return r
        return None
    
    def get_records_by_action(self, action: str, limit: int = 10) -> List[ProvenanceRecord]:
        """Dapatkan records by action"""
        return [r for r in self.records if r.action == action][-limit:]
    
    def get_records_by_session(self, session_id: str, limit: int = 20) -> List[ProvenanceRecord]:
        """Dapatkan records by session"""
        return [r for r in self.records if r.session_id == session_id][-limit:]
    
    def get_summary(self) -> Dict:
        """Dapatkan ringkasan provenance"""
        source_stats = {}
        action_stats = {}
        
        for r in self.records:
            # Source stats
            source = r.source_type
            source_stats[source] = source_stats.get(source, 0) + 1
            
            # Action stats
            action = r.action
            action_stats[action] = action_stats.get(action, 0) + 1
        
        return {
            "total_records": len(self.records),
            "source_stats": source_stats,
            "action_stats": action_stats,
            "last_record": self.records[-1].to_dict() if self.records else None
        }
    
    def print_summary(self):
        """Print ringkasan provenance"""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("📜 PROVENANCE SUMMARY")
        print("=" * 60)
        print(f"Total records: {summary['total_records']}")
        
        print("\n📊 Source Types:")
        for source, count in sorted(summary['source_stats'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {source}: {count}")
        
        print("\n📊 Top Actions:")
        for action, count in sorted(summary['action_stats'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {action}: {count}")
        
        if summary['last_record']:
            print(f"\n📋 Last Record:")
            last = summary['last_record']
            print(f"  Action: {last['action']} -> {last['target']}")
            print(f"  Source: {last['source_type']}")
            print(f"  Confidence: {last['confidence']}")
        
        print("=" * 60)
    
    def export_report(self) -> str:
        """Export semua records ke JSON"""
        return json.dumps(
            {
                "summary": self.get_summary(),
                "records": [r.to_dict() for r in self.records[-100:]]
            },
            indent=2,
            default=str
        )
    
    def _save(self):
        """Save records ke disk"""
        data = {
            "records": [r.to_dict() for r in self.records],
            "updated_at": datetime.now().isoformat()
        }
        with open(self.records_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        """Load records dari disk"""
        if not self.records_file.exists():
            return
        
        try:
            with open(self.records_file, "r") as f:
                data = json.load(f)
            
            self.records = [ProvenanceRecord.from_dict(r) for r in data.get("records", [])]
            print(f"[PROVENANCE] Loaded {len(self.records)} records")
        except Exception as e:
            print(f"[PROVENANCE] Failed to load: {e}")
