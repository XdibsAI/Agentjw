"""
Intent Engine - Context-Aware Intent Detection
Bukan keyword matching, tapi berdasarkan konteks dan metadata
"""

import re
from typing import Dict, List, Optional
from pathlib import Path


class IntentEngine:
    """Deteksi intent berdasarkan konteks dan metadata"""

    def __init__(self):
        self.context_file = Path("/home/dibs/agentjw/memory/conversation_context.json")
        self.state_file = Path("/home/dibs/agentjw/memory/conversation_state.json")
        self._load_context()

    def _load_context(self):
        """Load context dan state"""
        self.context = {}
        self.state = {}
        
        if self.context_file.exists():
            try:
                import json
                self.context = json.loads(self.context_file.read_text())
            except:
                pass
        
        if self.state_file.exists():
            try:
                import json
                self.state = json.loads(self.state_file.read_text())
            except:
                pass

    def detect_intent(self, user_message: str, history: List[Dict] = None) -> Dict:
        """
        Deteksi intent berdasarkan:
        1. Kata kunci (fallback)
        2. Konteks percakapan
        3. State user
        4. History
        """
        msg_lower = user_message.lower()
        
        # === 1. CEK KONTEKS PERCAKAPAN ===
        # Jika user bilang "review", cek apakah sebelumnya ada pembahasan kode
        if "review" in msg_lower or "cek" in msg_lower or "analisis" in msg_lower:
            # Cek apakah ada file Python yang disebutkan
            if any(kw in msg_lower for kw in [".py", "kode", "code", "strategi", "sniper", "strategy"]):
                return {
                    "intent": "review",
                    "action": "reviewer",
                    "confidence": 0.95,
                    "reason": "User wants code review"
                }
            # Cek apakah ini lanjutan dari review sebelumnya
            if history and len(history) > 0:
                last_topic = self.context.get("last_topic", "")
                if "review" in last_topic or "kode" in last_topic:
                    return {
                        "intent": "review_continue",
                        "action": "reviewer",
                        "confidence": 0.85,
                        "reason": "Continuation of previous review"
                    }
        
        # === 2. CEK STATE USER ===
        # Jika user bilang "jalankan bot" atau "start"
        if any(kw in msg_lower for kw in ["jalankan", "start", "run", "jalan"]):
            if "bot" in msg_lower or "trading" in msg_lower:
                return {
                    "intent": "run_bot",
                    "action": "analyzer",
                    "confidence": 0.95,
                    "reason": "User wants to run bot"
                }
        
        # === 3. CEK PERMINTAAN KODE ===
        if any(kw in msg_lower for kw in ["kode", "code", "fungsi", "function", "script"]):
            if any(kw in msg_lower for kw in ["buat", "tulis", "generate", "create", "tambah", "tuliskan"]):
                return {
                    "intent": "generate_code",
                    "action": "coder",
                    "confidence": 0.95,
                    "reason": "User wants code generation"
                }
            # Jika user minta "tampilkan kode" atau "lihat kode"
            if any(kw in msg_lower for kw in ["tampilkan", "lihat", "show", "display"]):
                return {
                    "intent": "show_code",
                    "action": "reviewer",
                    "confidence": 0.9,
                    "reason": "User wants to see code"
                }
        
        # === 4. CEK PERBAIKAN ===
        if any(kw in msg_lower for kw in ["perbaiki", "fix", "repair", "error", "syntax error"]):
            if any(kw in msg_lower for kw in ["strategy", "kode", "code", "file"]):
                return {
                    "intent": "repair_code",
                    "action": "coder",
                    "confidence": 0.95,
                    "reason": "User wants code repair"
                }
        
        # === 5. CEK ANALISIS DATA ===
        if any(kw in msg_lower for kw in ["analisis", "analyze", "trading", "pnl", "profit", "loss", "trade", "db", "database", "trading.db"]):
            if any(kw in msg_lower for kw in ["analisis", "analyze", "statistik", "data", "lihat"]):
                return {
                    "intent": "analyze_data",
                    "action": "analyzer",
                    "confidence": 0.95,
                    "reason": "User wants data analysis"
                }
        
        # === 5. FALLBACK: General chat ===
        return {
            "intent": "chat",
            "action": "chat",
            "confidence": 0.5,
            "reason": "General conversation"
        }


def get_intent_engine():
    _engine = None
    if _engine is None:
        _engine = IntentEngine()
    return _engine
