"""
Conversation Router - Menentukan jalur yang tepat untuk setiap pesan
"""

from typing import Dict, Optional, Tuple
from enum import Enum


class RouteType(Enum):
    MEMORY_QUERY = "memory_query"      # "masih ingat..."
    KNOWLEDGE_QUERY = "knowledge_query"  # "berapa file..."
    DECISION_QUERY = "decision_query"    # "kenapa..."
    ARTIFACT_QUERY = "artifact_query"    # "hasil scan..."
    PROGRESS_QUERY = "progress_query"    # "sampai mana..."
    PLANNING_QUERY = "planning_query"    # "langkah berikutnya..."
    EXECUTION = "execution"              # "scan project..."
    SMALL_TALK = "small_talk"            # "halo"
    FALLBACK = "fallback"                # unknown


class ConversationRouter:
    """Menentukan jalur yang tepat untuk setiap pesan"""
    
    def __init__(self, state=None):
        self.state = state
    
    def route(self, user_message: str) -> Tuple[RouteType, Dict]:
        """Tentukan jalur berdasarkan pesan"""
        message_lower = user_message.lower()
        
        # 1. Memory Query - "masih ingat", "terakhir", "sebelumnya"
        memory_keywords = ["masih ingat", "ingat", "terakhir", "kemarin", "sebelumnya", "yang tadi"]
        if any(k in message_lower for k in memory_keywords):
            return RouteType.MEMORY_QUERY, {"query": user_message}
        
        # 2. Decision Query - "kenapa", "mengapa", "alasan"
        decision_keywords = ["kenapa", "mengapa", "alasan", "kenapa memilih", "kok"]
        if any(k in message_lower for k in decision_keywords):
            return RouteType.DECISION_QUERY, {"query": user_message}
        
        # 3. Knowledge Query - "berapa", "jumlah", "total"
        knowledge_keywords = ["berapa", "jumlah", "total", "ada berapa", "sebanyak"]
        if any(k in message_lower for k in knowledge_keywords):
            return RouteType.KNOWLEDGE_QUERY, {"query": user_message}
        
        # 4. Artifact Query - "hasil", "kapan", "terakhir scan"
        artifact_keywords = ["hasil", "kapan terakhir", "timeline", "riwayat"]
        if any(k in message_lower for k in artifact_keywords):
            return RouteType.ARTIFACT_QUERY, {"query": user_message}
        
        # 5. Progress Query - "sampai mana", "progress", "pending"
        progress_keywords = ["sampai mana", "progress", "pending", "sejauh mana", "status"]
        if any(k in message_lower for k in progress_keywords):
            return RouteType.PROGRESS_QUERY, {"query": user_message}
        
        # 6. Planning Query - "langkah", "berikutnya", "rencana"
        planning_keywords = ["langkah berikutnya", "rencana", "selanjutnya", "next step"]
        if any(k in message_lower for k in planning_keywords):
            return RouteType.PLANNING_QUERY, {"query": user_message}
        
        # 7. Execution - "scan", "analyze", "repair", "build", "run"
        execution_keywords = ["scan", "analyze", "analisa", "repair", "build", "run", "perbaiki", "tampilkan", "cek"]
        if any(k in message_lower for k in execution_keywords):
            # Cek apakah ini pertanyaan atau perintah
            if any(k in message_lower for k in ["?", "apa", "bagaimana", "kenapa"]):
                return RouteType.KNOWLEDGE_QUERY, {"query": user_message}
            return RouteType.EXECUTION, {"query": user_message}
        
        # 8. Small Talk
        small_talk_keywords = ["halo", "hai", "hi", "apa kabar", "selamat", "terima kasih"]
        if any(k in message_lower for k in small_talk_keywords):
            return RouteType.SMALL_TALK, {"query": user_message}
        
        # 9. Continuation
        continuation_keywords = ["lanjut", "teruskan", "next", "continue", "gas"]
        if any(k in message_lower for k in continuation_keywords):
            return RouteType.EXECUTION, {"query": user_message, "is_continuation": True}
        
        return RouteType.FALLBACK, {"query": user_message}
    
    def should_use_query(self, route: RouteType) -> bool:
        """Apakah route ini harus menggunakan Query Layer?"""
        return route in [
            RouteType.MEMORY_QUERY,
            RouteType.KNOWLEDGE_QUERY,
            RouteType.DECISION_QUERY,
            RouteType.ARTIFACT_QUERY,
            RouteType.PROGRESS_QUERY,
            RouteType.PLANNING_QUERY
        ]
    
    def should_use_executor(self, route: RouteType) -> bool:
        """Apakah route ini harus menggunakan Executor?"""
        return route in [
            RouteType.EXECUTION
        ]
    
    def should_use_brain(self, route: RouteType) -> bool:
        """Apakah route ini harus menggunakan Brain?"""
        return route in [
            RouteType.EXECUTION,
            RouteType.PLANNING_QUERY
        ]
