"""
Reflection Engine - Reflection adaptif yang bisa memberi rekomendasi
"""

from typing import Dict, Any, Optional
from datetime import datetime


class ReflectionEngine:
    """
    Reflection Engine - menganalisis hasil eksekusi dan memberi rekomendasi.
    
    Rekomendasi:
    - continue: lanjut ke step berikutnya
    - retry: ulangi step yang sama
    - skip: lewati step berikutnya
    - replan: buat ulang plan
    - escalate: butuh intervensi manual
    - stop: hentikan workflow
    """
    
    RECOMMENDATIONS = {
        "continue": "Lanjut ke step berikutnya",
        "retry": "Ulangi step yang sama",
        "skip": "Lewati step berikutnya",
        "replan": "Buat ulang rencana",
        "escalate": "Butuh intervensi manual",
        "stop": "Hentikan workflow"
    }
    
    def __init__(self):
        self.confidence_threshold = 0.7
        self.retry_limit = 3
    
    def analyze(self, task: dict, result: dict, validation: dict, step_context: dict = None) -> dict:
        """
        Analyze execution result and provide recommendation.
        
        Returns:
        {
            "confidence": float,
            "should_retry": bool,
            "next_action": str,  # continue, retry, skip, replan, escalate, stop
            "reason": str,
            "learnings": list,
            "retry_count": int
        }
        """
        step_context = step_context or {}
        
        # Extract info
        action = task.get("action", "unknown")
        target = task.get("target", "")
        success = result.get("success", False)
        
        # Start with basic reflection
        reflection = {
            "confidence": 0.0,
            "should_retry": False,
            "next_action": "continue",
            "reason": "",
            "learnings": [],
            "retry_count": step_context.get("retry_count", 0)
        }
        
        if success:
            # Success case
            reflection["confidence"] = 0.9
            
            # Cek apakah ada data yang berguna
            data = result.get("data")
            if data:
                reflection["confidence"] = 0.95
                reflection["learnings"].append("Data returned successfully")
            
            if result.get("summary"):
                reflection["learnings"].append(f"Summary: {result.get('summary')[:100]}")
            
            # Jika confidence > threshold, lanjut
            if reflection["confidence"] >= self.confidence_threshold:
                reflection["next_action"] = "continue"
                reflection["reason"] = "Execution successful with high confidence"
            else:
                reflection["next_action"] = "retry"
                reflection["reason"] = f"Confidence ({reflection['confidence']}) below threshold"
                
        else:
            # Failure case
            errors = result.get("errors", [])
            error_msg = result.get("error", "Unknown error")
            
            reflection["confidence"] = 0.2
            reflection["reason"] = error_msg
            
            if errors:
                reflection["learnings"].append(f"Errors: {', '.join(errors[:3])}")
            
            # Check retry count
            if step_context.get("retry_count", 0) < self.retry_limit:
                reflection["should_retry"] = True
                reflection["next_action"] = "retry"
                reflection["reason"] = f"Retry {step_context.get('retry_count', 0) + 1}/{self.retry_limit}"
            else:
                reflection["next_action"] = "replan"
                reflection["reason"] = f"Max retries ({self.retry_limit}) exceeded"
        
        # Special cases based on action type
        if action == "analyze_project":
            # Analyze action: if confidence < 70, perlu audit ulang
            data = result.get("data", {})
            audit_confidence = data.get("confidence", 0)
            if audit_confidence < 70 and success:
                reflection["confidence"] = 0.4
                reflection["next_action"] = "replan"
                reflection["reason"] = f"Audit confidence too low ({audit_confidence}%)"
                reflection["learnings"].append(f"Audit confidence: {audit_confidence}%")
        
        elif action == "repair_project":
            # Repair action: cek apakah ada yang berubah
            if success:
                files = result.get("data", {}).get("repaired", [])
                if not files:
                    reflection["confidence"] = 0.6
                    reflection["next_action"] = "skip"
                    reflection["reason"] = "No files were repaired"
                    reflection["learnings"].append("No changes made")
        
        elif action == "modify_logic":
            # Modify logic: cek apakah target berhasil dimodifikasi
            if success:
                modified = result.get("data", {}).get("modified", [])
                if not modified:
                    reflection["confidence"] = 0.5
                    reflection["next_action"] = "replan"
                    reflection["reason"] = "No logic was modified"
                    reflection["learnings"].append("Modification did not apply")
        
        return reflection
    
    def should_continue(self, reflection: dict) -> bool:
        """Cek apakah workflow harus lanjut"""
        return reflection.get("next_action") in ["continue", "skip"]
    
    def should_retry(self, reflection: dict) -> bool:
        """Cek apakah harus retry"""
        return reflection.get("next_action") == "retry"
    
    def should_replan(self, reflection: dict) -> bool:
        """Cek apakah harus replan"""
        return reflection.get("next_action") == "replan"
    
    def get_recommendation(self, reflection: dict) -> str:
        """Dapatkan rekomendasi dalam bentuk string"""
        action = reflection.get("next_action", "continue")
        return self.RECOMMENDATIONS.get(action, f"Unknown: {action}")
