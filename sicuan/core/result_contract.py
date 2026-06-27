"""
AgentJW Result Contract V1 - Kontrak standar untuk semua action
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
import json


@dataclass
class ResultContract:
    """Kontrak standar untuk hasil semua action"""
    
    # Wajib
    success: bool
    action: str
    entity: str
    display: str
    
    # Opsional
    metrics: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    duration: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    contract_version: str = "1.0"
    
    def to_dict(self) -> Dict:
        """Convert ke dictionary"""
        return {
            "success": self.success,
            "action": self.action,
            "entity": self.entity,
            "display": self.display,
            "metrics": self.metrics,
            "confidence": self.confidence,
            "duration": self.duration,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
            "contract_version": self.contract_version
        }
    
    def to_json(self) -> str:
        """Convert ke JSON"""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ResultContract':
        """Create dari dictionary"""
        return cls(
            success=data.get("success", False),
            action=data.get("action", ""),
            entity=data.get("entity", ""),
            display=data.get("display", ""),
            metrics=data.get("metrics", {}),
            confidence=data.get("confidence", 0.5),
            duration=data.get("duration", 0.0),
            data=data.get("data", {}),
            errors=data.get("errors", []),
            warnings=data.get("warnings", []),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            contract_version=data.get("contract_version", "1.0")
        )
    
    @classmethod
    def from_raw(cls, action: str, entity: str, result: Dict, duration: float = 0) -> 'ResultContract':
        """Create contract dari raw result"""
        success = result.get("success", False)
        
        # Extract display
        display = result.get("display") or result.get("summary") or ""
        if not display:
            if success:
                display = f"✅ {action.replace('_', ' ').title()} selesai"
            else:
                display = f"❌ {action.replace('_', ' ').title()} gagal"
        
        # Extract metrics dari result
        metrics = result.get("metrics", {})
        if not metrics:
            # Try to extract from data
            data = result.get("data", {})
            if action == "scan_project":
                metrics = {
                    "total_files": data.get("total_py", 0),
                    "valid_files": data.get("valid_syntax", 0)
                }
            elif action == "analyze_project":
                metrics = {
                    "functions": data.get("functions", 0),
                    "confidence": data.get("confidence", 0)
                }
            elif action == "trace_code":
                metrics = {
                    "symbol": entity,
                    "found": bool(data.get("trace"))
                }
        
        # Extract confidence
        confidence = result.get("confidence", 0.5)
        if not confidence:
            if success:
                confidence = 0.9
            else:
                confidence = 0.2
        
        # Extract errors
        errors = result.get("errors", [])
        if result.get("error"):
            errors.append(result.get("error"))
        
        return cls(
            success=success,
            action=action,
            entity=entity,
            display=display,
            metrics=metrics,
            confidence=confidence,
            duration=duration,
            data=result.get("data", {}),
            errors=errors,
            warnings=result.get("warnings", [])
        )
    
    def compare(self, other: 'ResultContract') -> Dict:
        """
        Bandingkan dengan contract lain.
        
        Returns:
        {
            "match": bool,
            "success_match": bool,
            "action_match": bool,
            "entity_match": bool,
            "metrics_match": bool,
            "differences": [...]
        }
        """
        differences = []
        
        # 1. Success
        success_match = self.success == other.success
        if not success_match:
            differences.append(f"success: {self.success} vs {other.success}")
        
        # 2. Action
        action_match = self.action == other.action
        if not action_match:
            differences.append(f"action: {self.action} vs {other.action}")
        
        # 3. Entity (flexible match)
        entity_match = self._entity_match(self.entity, other.entity)
        if not entity_match:
            differences.append(f"entity: {self.entity} vs {other.entity}")
        
        # 4. Metrics
        metrics_match = self._metrics_match(self.metrics, other.metrics)
        if not metrics_match:
            differences.append(f"metrics: {self.metrics} vs {other.metrics}")
        
        # Overall match
        is_match = success_match and action_match and entity_match and metrics_match
        
        return {
            "match": is_match,
            "success_match": success_match,
            "action_match": action_match,
            "entity_match": entity_match,
            "metrics_match": metrics_match,
            "differences": differences
        }
    
    def _entity_match(self, entity1: str, entity2: str) -> bool:
        """Flexible entity matching"""
        if entity1 == entity2:
            return True
        if not entity1 or not entity2:
            return True
        # Case insensitive
        if entity1.lower() == entity2.lower():
            return True
        # Substring match
        if entity1.lower() in entity2.lower() or entity2.lower() in entity1.lower():
            return True
        return False
    
    def _metrics_match(self, m1: Dict, m2: Dict) -> bool:
        """Flexible metrics matching"""
        if not m1 and not m2:
            return True
        if not m1 or not m2:
            return True
        
        # Check key presence
        m1_keys = set(m1.keys())
        m2_keys = set(m2.keys())
        
        # If keys are completely different, maybe still match
        if not m1_keys & m2_keys:
            return True
        
        # Check common keys
        for key in m1_keys & m2_keys:
            if m1.get(key) != m2.get(key):
                # Allow numeric tolerance
                if isinstance(m1.get(key), (int, float)) and isinstance(m2.get(key), (int, float)):
                    if abs(m1.get(key, 0) - m2.get(key, 0)) > 1:
                        return False
                else:
                    return False
        
        return True


# Helper function
def create_contract(action: str, entity: str, result: Dict, duration: float = 0) -> ResultContract:
    """Create result contract dari raw result"""
    return ResultContract.from_raw(action, entity, result, duration)
# Helper function
def create_contract(action: str, entity: str, result: Dict, duration: float = 0) -> ResultContract:
    """Create result contract dari raw result"""
    return ResultContract.from_raw(action, entity, result, duration)
