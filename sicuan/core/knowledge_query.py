"""
Knowledge Query - Query layer untuk knowledge store
"""

from typing import Dict, List, Optional, Any
from sicuan.core.knowledge_index import KnowledgeIndex


class KnowledgeQuery:
    """Query knowledge store tanpa harus scan ulang"""
    
    def __init__(self):
        self.index = KnowledgeIndex()
    
    def get_entity(self, entity: str) -> Dict[str, Any]:
        """Dapatkan semua knowledge untuk entity"""
        facts = self.index.get(entity)
        result = {}
        for fact in facts:
            # Parse fact: "attribute: value"
            if ": " in fact.fact:
                attr, value = fact.fact.split(": ", 1)
                result[attr] = {
                    "value": value,
                    "confidence": fact.confidence,
                    "source": fact.source,
                    "timestamp": fact.timestamp
                }
        return result
    
    def get_attribute(self, entity: str, attribute: str) -> Optional[Dict]:
        """Dapatkan attribute spesifik dari entity"""
        facts = self.index.get(entity)
        for fact in facts:
            if fact.fact.startswith(f"{attribute}: "):
                value = fact.fact.split(": ", 1)[1]
                return {
                    "value": value,
                    "confidence": fact.confidence,
                    "source": fact.source,
                    "timestamp": fact.timestamp
                }
        return None
    
    def search(self, query: str) -> List[Dict]:
        """Cari knowledge berdasarkan query"""
        results = []
        for entity, facts in self.index.facts.items():
            for fact in facts:
                if query.lower() in fact.fact.lower() or query.lower() in entity.lower():
                    results.append({
                        "entity": entity,
                        "fact": fact.fact,
                        "confidence": fact.confidence,
                        "source": fact.source,
                        "timestamp": fact.timestamp
                    })
        return results
    
    def explain(self, entity: str) -> str:
        """Jelaskan pengetahuan tentang entity"""
        data = self.get_entity(entity)
        if not data:
            return f"Tidak ada pengetahuan tentang {entity}"
        
        lines = [f"📚 Pengetahuan tentang {entity}:"]
        for attr, info in data.items():
            lines.append(f"  • {attr}: {info['value']} (confidence: {info['confidence']:.0%}, source: {info['source']})")
        return "\n".join(lines)
    
    def get_summary(self, entity: str) -> str:
        """Dapatkan ringkasan pengetahuan"""
        data = self.get_entity(entity)
        if not data:
            return f"Tidak ada pengetahuan tentang {entity}"
        
        lines = [f"📊 Summary untuk {entity}:"]
        for attr, info in data.items():
            lines.append(f"  {attr}: {info['value']}")
        return "\n".join(lines)
