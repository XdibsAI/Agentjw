"""
Artifact Validator - Memastikan artifact valid sebelum dipublish
"""

from typing import Dict, List, Optional
from datetime import datetime
from sicuan.core.artifact_event import ArtifactEvent


class ArtifactValidator:
    """Validator untuk artifact events"""
    
    SUPPORTED_SCHEMA_VERSIONS = ["1.0", "1.1", "2.0"]
    
    @classmethod
    def validate(cls, event: ArtifactEvent) -> Dict:
        """Validasi artifact event"""
        errors = []
        warnings = []
        
        # 1. Cek schema version
        if not hasattr(event, 'schema_version') or not event.schema_version:
            errors.append("schema_version is required")
        elif event.schema_version not in cls.SUPPORTED_SCHEMA_VERSIONS:
            errors.append(f"schema_version {event.schema_version} not supported")
        
        # 2. Cek artifact_id
        if not event.artifact_id:
            errors.append("artifact_id is required")
        
        # 3. Cek action
        if not event.action:
            errors.append("action is required")
        
        # 4. Cek timestamp
        if event.timestamp:
            try:
                datetime.fromisoformat(event.timestamp)
            except ValueError:
                errors.append(f"invalid timestamp: {event.timestamp}")
        
        # 5. Cek outcome (jika ada)
        if event.outcome:
            if not hasattr(event.outcome, 'success'):
                errors.append("outcome.success is required")
        
        # 6. Cek knowledge (jika ada)
        if event.knowledge:
            for k in event.knowledge:
                if not k.entity:
                    warnings.append("knowledge.entity is empty")
                if not k.attribute:
                    warnings.append("knowledge.attribute is empty")
                if k.value is None:
                    warnings.append("knowledge.value is None")
        
        # 7. Cek decision (jika ada)
        if event.decision:
            if not event.decision.selected_action:
                errors.append("decision.selected_action is required")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @classmethod
    def validate_and_raise(cls, event: ArtifactEvent):
        """Validasi dan raise exception jika tidak valid"""
        result = cls.validate(event)
        if not result["valid"]:
            raise ValueError(f"Invalid artifact: {result['errors']}")
        return result
