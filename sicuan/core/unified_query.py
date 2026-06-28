"""
Unified Query Engine - Satu pintu untuk semua query
"""

from typing import Dict, List, Optional, Any
from sicuan.core.knowledge_query import KnowledgeQuery
from sicuan.core.decision_query import DecisionQuery
from sicuan.core.artifact_query import ArtifactQuery
from sicuan.core.reflection_query import ReflectionQuery


class UnifiedQuery:
    """Satu pintu untuk semua query"""
    
    def __init__(self):
        self.knowledge = KnowledgeQuery()
        self.decision = DecisionQuery()
        self.artifact = ArtifactQuery()
        self.reflection = ReflectionQuery()
    
    def ask(self, question: str, context: Dict = None) -> str:
        """Jawab pertanyaan berdasarkan konteks"""
        question_lower = question.lower()
        context = context or {}
        entity = context.get("entity", "godmeme_bot")
        action = context.get("action", "")
        
        # 1. Pertanyaan tentang fakta
        if any(k in question_lower for k in ["berapa", "jumlah", "total", "ada berapa"]):
            return self._answer_fact(question, entity)
        
        # 2. Pertanyaan tentang keputusan
        if any(k in question_lower for k in ["kenapa", "mengapa", "alasan", "kenapa memilih"]):
            return self._answer_decision(question, action or entity)
        
        # 3. Pertanyaan tentang riwayat
        if any(k in question_lower for k in ["kapan", "sejak", "terakhir", "kemarin"]):
            return self._answer_history(question, action or entity)
        
        # 4. Pertanyaan tentang risiko
        if any(k in question_lower for k in ["risiko", "resiko", "bahaya", "kelemahan"]):
            return self._answer_risk(question, action or entity)
        
        # 5. Ringkasan umum
        if any(k in question_lower for k in ["ringkas", "rangkum", "summary"]):
            return self._answer_summary(entity)
        
        return "Maaf, aku belum bisa menjawab pertanyaan itu. Coba lebih spesifik."
    
    def _answer_fact(self, question: str, entity: str) -> str:
        """Jawab pertanyaan fakta"""
        # Coba extract attribute dari pertanyaan
        attributes = ["files", "functions", "confidence", "status", "project"]
        for attr in attributes:
            if attr in question.lower():
                result = self.knowledge.get_attribute(entity, attr)
                if result:
                    return f"{attr}: {result['value']} (confidence: {result['confidence']:.0%})"
        
        # Jika tidak ditemukan, tampilkan semua knowledge
        data = self.knowledge.get_entity(entity)
        if data:
            lines = [f"📚 Pengetahuan tentang {entity}:"]
            for attr, info in data.items():
                lines.append(f"  {attr}: {info['value']}")
            return "\n".join(lines)
        
        return f"Tidak ada pengetahuan tentang {entity}"
    
    def _answer_decision(self, question: str, action: str) -> str:
        """Jawab pertanyaan tentang keputusan"""
        if action:
            return self.decision.explain(action)
        return "Tidak ada keputusan yang disebutkan"
    
    def _answer_history(self, question: str, action: str) -> str:
        """Jawab pertanyaan tentang riwayat"""
        if action:
            return self.artifact.get_timeline(action)
        return "Tidak ada riwayat yang disebutkan"
    
    def _answer_risk(self, question: str, action: str) -> str:
        """Jawab pertanyaan tentang risiko"""
        if action:
            return self.reflection.explain(action)
        return "Tidak ada risiko yang ditemukan"
    
    def _answer_summary(self, entity: str) -> str:
        """Jawab pertanyaan ringkasan"""
        lines = []
        
        # Knowledge
        knowledge = self.knowledge.get_entity(entity)
        if knowledge:
            lines.append("📚 Pengetahuan:")
            for attr, info in knowledge.items():
                lines.append(f"  {attr}: {info['value']}")
        
        # Decisions
        decisions = self.decision.get_by_project(entity)
        if decisions:
            lines.append("\n📋 Keputusan terakhir:")
            for d in decisions[-3:]:
                lines.append(f"  {d['action']} - {d['reason']}")
        
        # Artifacts
        artifacts = self.artifact.get_by_project(entity)
        if artifacts:
            lines.append(f"\n📁 Total artifact: {len(artifacts)}")
        
        return "\n".join(lines) if lines else f"Tidak ada informasi tentang {entity}"
