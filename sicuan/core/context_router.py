"""
Context Router - Routing berdasarkan konteks, bukan keyword
"""

from typing import Dict, List, Optional


class ContextRouter:
    """Router berdasarkan konteks percakapan"""

    def __init__(self, brain):
        self.brain = brain

    def route(self, user_message: str, history: List[Dict], state: Dict) -> Dict:
        """Route berdasarkan konteks, bukan keyword"""
        
        # 1. Cek apakah ada data di history
        if not history:
            return {"action": "chat", "confidence": 0.5}
        
        # 2. Cek apakah pertanyaan tentang data yang baru saja diberikan
        last_messages = history[-3:]
        has_recent_data = any("LOG FILE" in str(m) or "GODMEME STATUS" in str(m) for m in last_messages)
        
        if has_recent_data:
            # User bertanya tentang data yang baru saja diberikan
            return {
                "action": "analyze_context",
                "confidence": 0.9,
                "reason": "User bertanya tentang data yang baru saja diberikan"
            }
        
        # 3. Cek apakah ada project/status request
        if "status" in user_message.lower() or "performa" in user_message.lower():
            return {"action": "godmeme_status", "confidence": 0.8}
        
        # 4. Default: biarkan LLM decide
        return {"action": None, "confidence": 0.5}
