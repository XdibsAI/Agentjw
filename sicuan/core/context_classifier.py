"""
Context Classifier - Bedakan pertanyaan tentang sistem vs project
"""

import re
from typing import Dict, List, Optional


class ContextClassifier:
    """Klasifikasi konteks pertanyaan user"""
    
    # Keywords untuk sistem SiCuan
    SYSTEM_KEYWORDS = [
        "struktur repair", "repair terbaru", "sistem repair", "repair pipeline",
        "sistem sicuan", "struktur sicuan", "struktur barumu", "repair engine",
        "kemampuanmu", "fitur barumu", "komponen repair", "auto repair",
        "pipeline repair", "error classifier", "semantic verifier",
        "git rollback", "syntax repair", "preflight"
    ]
    
    # Keywords untuk project
    PROJECT_KEYWORDS = [
        "project", "proyek", "godmeme", "flask", "bot", "trading",
        "status bot", "analisa project", "audit project"
    ]
    
    def classify(self, user_message: str) -> Dict:
        """
        Klasifikasi konteks pertanyaan
        Returns: {
            'context': 'system' | 'project' | 'general',
            'confidence': float,
            'matched_keywords': List[str]
        }
        """
        user_message_lower = user_message.lower()
        
        # Cek system keywords
        system_matches = []
        for kw in self.SYSTEM_KEYWORDS:
            if kw in user_message_lower:
                system_matches.append(kw)
        
        # Cek project keywords
        project_matches = []
        for kw in self.PROJECT_KEYWORDS:
            if kw in user_message_lower:
                project_matches.append(kw)
        
        # Jika ada kata kunci "repair" atau "struktur" - cenderung system
        if any(kw in user_message_lower for kw in ["repair", "struktur", "sistem"]):
            if system_matches or "repair" in user_message_lower:
                return {
                    "context": "system",
                    "confidence": 0.9 if system_matches else 0.7,
                    "matched_keywords": system_matches[:5]
                }
        
        # Jika ada kata kunci project
        if project_matches or any(kw in user_message_lower for kw in ["godmeme", "bot", "trading"]):
            return {
                "context": "project",
                "confidence": 0.9 if project_matches else 0.6,
                "matched_keywords": project_matches[:5]
            }
        
        # Default: general
        return {
            "context": "general",
            "confidence": 0.5,
            "matched_keywords": []
        }


# Singleton
_classifier = None

def get_context_classifier():
    global _classifier
    if _classifier is None:
        _classifier = ContextClassifier()
    return _classifier
