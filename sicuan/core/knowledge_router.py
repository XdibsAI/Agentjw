"""
Knowledge Router — Auto-search jika memory tidak cukup dengan Decision Intelligence
"""

import time
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

@dataclass
class Decision:
    """Keputusan sumber informasi"""
    source: str  # memory, search, llm, hybrid
    reason: str
    confidence: float
    should_search: bool = False
    should_use_memory: bool = False
    should_use_llm: bool = False
    search_provider: Optional[str] = None
    memory_key: Optional[str] = None
    reasoning: str = ""

class KnowledgeRouter:
    """
    Router dengan Decision Intelligence — memilih sumber informasi terbaik
    """
    
    def __init__(self):
        self.search_providers = ["tavily", "hermes", "firecrawl"]
        self._last_search = {}
        
        # Pattern untuk pertanyaan yang TIDAK perlu search
        self.no_search_patterns = [
            r"^(halo|hai|hi|hey|selamat|pagi|siang|malam)",
            r"^(siapa|apa|bagaimana) (nama|kabar|kamu|anda|dirimu)",
            r"^(terima kasih|makasih|thanks|ok|oke|ya|tidak)",
            r"^(proyek|project) (kita|kami|yang|sedang)",
            r"^(memory|ingat|konteks|sebelumnya)"
        ]
        
        # Pattern untuk pertanyaan yang WAJIB search
        self.force_search_patterns = [
            r"(informasi|data|berita|update|terbaru|hari ini)",
            r"(ekonomi|politik|teknologi|bisnis|pasar|trading)",
            r"(tentang|apa itu|siapa itu|dimana|kapan|berapa)",
            r"(cari|temukan|lihat|cek|periksa)"
        ]
    
    def should_search(self, query: str, memory_context: str = "") -> Decision:
        """
        Membuat keputusan apakah perlu mencari
        """
        query_lower = query.lower().strip()
        
        # 1. Cek pola NO SEARCH (chatting, sapaan, konteks)
        for pattern in self.no_search_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return Decision(
                    source="memory",
                    reason="conversation_context",
                    confidence=0.95,
                    should_search=False,
                    should_use_memory=True,
                    reasoning="Pertanyaan bersifat percakapan atau kontekstual"
                )
        
        # 2. Cek pola FORCE SEARCH (informasi eksternal)
        for pattern in self.force_search_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return Decision(
                    source="search",
                    reason="external_information_needed",
                    confidence=0.92,
                    should_search=True,
                    should_use_memory=False,
                    search_provider="tavily",
                    reasoning="Pertanyaan membutuhkan informasi eksternal/terbaru"
                )
        
        # 3. Cek memory context
        if memory_context and len(memory_context) > 100:
            return Decision(
                source="memory",
                reason="sufficient_memory",
                confidence=0.85,
                should_search=False,
                should_use_memory=True,
                reasoning="Memory memiliki informasi yang cukup"
            )
        
        # 4. Fallback: hybrid (memory + search)
        return Decision(
            source="hybrid",
            reason="partial_memory",
            confidence=0.70,
            should_search=True,
            should_use_memory=True,
            search_provider="tavily",
            reasoning="Memory tidak cukup, perlu mencari informasi tambahan"
        )
    
    def route(self, query: str, memory_context: str = "", 
              search_executor=None, llm_executor=None) -> Dict:
        """
        Route query: decision → execute → response
        """
        # 1. Buat keputusan
        decision = self.should_search(query, memory_context)
        
        result = {
            "source": decision.source,
            "response": "",
            "search_performed": decision.should_search,
            "memory_used": decision.should_use_memory,
            "llm_used": decision.should_use_llm,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "decision": decision
        }
        
        # 2. Jika perlu search dan ada executor
        if decision.should_search and search_executor:
            search_result = search_executor(query)
            if search_result and search_result.get("status") == "success":
                result["response"] = search_result.get("result", "")
                result["search_performed"] = True
                result["search_provider"] = search_result.get("provider", "unknown")
                result["confidence"] = 0.92
                return result
        
        # 3. Jika memory cukup
        if decision.should_use_memory and memory_context:
            result["response"] = memory_context
            result["memory_used"] = True
            result["confidence"] = 0.80
            return result
        
        # 4. Fallback: gunakan LLM reasoning
        if llm_executor:
            llm_result = llm_executor(query)
            if llm_result and llm_result.get("status") == "success":
                result["response"] = llm_result.get("result", "")
                result["llm_used"] = True
                result["source"] = "llm"
                result["confidence"] = 0.70
                return result
        
        # 5. Final fallback
        result["response"] = "Maaf, saya tidak memiliki informasi tentang itu."
        result["confidence"] = 0.30
        return result

# Singleton
_router = None

def get_knowledge_router() -> KnowledgeRouter:
    global _router
    if _router is None:
        _router = KnowledgeRouter()
    return _router
