"""
Conversation Dispatcher - Menentukan jalur yang tepat untuk setiap pesan
"""

from typing import Dict, Optional, Tuple, Any
from enum import Enum
import re


class DispatchType(Enum):
    MEMORY_QUERY = "memory_query"        # "masih ingat..."
    PROGRESS_QUERY = "progress_query"    # "sampai mana..."
    SUMMARY_QUERY = "summary_query"      # "ringkas..."
    DECISION_QUERY = "decision_query"    # "kenapa..."
    KNOWLEDGE_QUERY = "knowledge_query"  # "berapa file..."
    ARTIFACT_QUERY = "artifact_query"    # "hasil scan..."
    PLANNING_QUERY = "planning_query"    # "langkah berikutnya..."
    EXECUTION = "execution"              # "scan project..."
    SMALL_TALK = "small_talk"            # "halo"
    FALLBACK = "fallback"                # unknown


class ConversationDispatcher:
    """Menentukan jalur yang tepat untuk setiap pesan"""
    
    def __init__(self, state=None, execution=None, knowledge=None):
        self.state = state
        self.execution = execution
        self.knowledge = knowledge
    
    def dispatch(self, user_message: str) -> Tuple[DispatchType, Dict]:
        """Tentukan jalur berdasarkan pesan"""
        message_lower = user_message.lower()
        
        # 1. Memory Query - "masih ingat", "terakhir", "sebelumnya"
        memory_patterns = [
            "masih ingat", "ingat", "terakhir", "kemarin", 
            "sebelumnya", "yang tadi", "waktu itu"
        ]
        if any(p in message_lower for p in memory_patterns):
            return DispatchType.MEMORY_QUERY, {"query": user_message}
        
        # 2. Progress Query - "sampai mana", "progress", "pending"
        progress_patterns = [
            "sampai mana", "progress", "pending", "sejauh mana", 
            "status", "perkembangan"
        ]
        if any(p in message_lower for p in progress_patterns):
            return DispatchType.PROGRESS_QUERY, {"query": user_message}
        
        # 3. Summary Query - "ringkas", "rangkum", "resume"
        summary_patterns = ["ringkas", "rangkum", "resume", "intisari", "kesimpulan"]
        if any(p in message_lower for p in summary_patterns):
            return DispatchType.SUMMARY_QUERY, {"query": user_message}
        
        # 4. Decision Query - "kenapa", "mengapa", "alasan"
        decision_patterns = ["kenapa", "mengapa", "alasan", "kok", "kenapa memilih"]
        if any(p in message_lower for p in decision_patterns):
            return DispatchType.DECISION_QUERY, {"query": user_message}
        
        # 5. Knowledge Query - "berapa", "jumlah", "total"
        knowledge_patterns = ["berapa", "jumlah", "total", "ada berapa", "sebanyak"]
        if any(p in message_lower for p in knowledge_patterns):
            return DispatchType.KNOWLEDGE_QUERY, {"query": user_message}
        
        # 6. Artifact Query - "hasil", "kapan", "terakhir scan"
        artifact_patterns = ["hasil", "kapan terakhir", "timeline", "riwayat", "terakhir kali"]
        if any(p in message_lower for p in artifact_patterns):
            return DispatchType.ARTIFACT_QUERY, {"query": user_message}
        
        # 7. Planning Query - "langkah", "berikutnya", "rencana"
        planning_patterns = ["langkah berikutnya", "rencana", "selanjutnya", "next step", "apa yang akan"]
        if any(p in message_lower for p in planning_patterns):
            return DispatchType.PLANNING_QUERY, {"query": user_message}
        
        # 8. Execution - "scan", "analyze", "repair", "build", "run"
        execution_patterns = ["scan", "analyze", "analisa", "repair", "build", "run", "perbaiki"]
        if any(p in message_lower for p in execution_patterns):
            # Cek apakah ini pertanyaan atau perintah
            if "?" in user_message or any(p in message_lower for p in ["apa", "bagaimana", "kenapa"]):
                return DispatchType.KNOWLEDGE_QUERY, {"query": user_message}
            return DispatchType.EXECUTION, {"query": user_message}
        
        # 9. Continuation
        continuation_patterns = ["lanjut", "teruskan", "next", "continue", "gas", "ayo"]
        if any(p in message_lower for p in continuation_patterns):
            return DispatchType.EXECUTION, {"query": user_message, "is_continuation": True}
        
        # 10. Small Talk
        small_talk_patterns = ["halo", "hai", "hi", "apa kabar", "selamat", "terima kasih"]
        if any(p in message_lower for p in small_talk_patterns):
            return DispatchType.SMALL_TALK, {"query": user_message}
        
        return DispatchType.FALLBACK, {"query": user_message}
    
    def should_use_query(self, dispatch_type: DispatchType) -> bool:
        """Apakah dispatch type ini harus menggunakan Query Layer?"""
        return dispatch_type in [
            DispatchType.MEMORY_QUERY,
            DispatchType.PROGRESS_QUERY,
            DispatchType.SUMMARY_QUERY,
            DispatchType.KNOWLEDGE_QUERY,
            DispatchType.DECISION_QUERY,
            DispatchType.ARTIFACT_QUERY,
            DispatchType.PLANNING_QUERY
        ]
    
    def should_use_executor(self, dispatch_type: DispatchType) -> bool:
        """Apakah dispatch type ini harus menggunakan Executor?"""
        return dispatch_type in [
            DispatchType.EXECUTION
        ]
    
    def should_use_brain(self, dispatch_type: DispatchType) -> bool:
        """Apakah dispatch type ini harus menggunakan Brain?"""
        return dispatch_type in [
            DispatchType.EXECUTION,
            DispatchType.PLANNING_QUERY
        ]
    
    def build_response(self, dispatch_type: DispatchType, state=None, execution=None, knowledge=None) -> str:
        """Bangun response berdasarkan dispatch type"""
        
        if dispatch_type == DispatchType.MEMORY_QUERY:
            if state and state.last_action:
                return f"Terakhir kita mengerjakan {state.last_action}. Progress: {state.get_summary()}"
            return "Aku belum ingat ada pekerjaan terakhir. Ada yang mau kita kerjakan?"
        
        if dispatch_type == DispatchType.PROGRESS_QUERY:
            if state:
                return state.get_summary()
            return "Belum ada pekerjaan yang dimulai."
        
        if dispatch_type == DispatchType.SUMMARY_QUERY:
            if state:
                return f"Ringkasan pekerjaan:\n{state.get_summary()}"
            return "Belum ada pekerjaan yang bisa diringkas."
        
        if dispatch_type == DispatchType.KNOWLEDGE_QUERY:
            return "Aku cek knowledge store dulu ya."
        
        if dispatch_type == DispatchType.DECISION_QUERY:
            return "Aku cek decision history dulu ya."
        
        if dispatch_type == DispatchType.ARTIFACT_QUERY:
            return "Aku cek artifact store dulu ya."
        
        return None
