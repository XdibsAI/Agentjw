"""
Knowledge Index - Menyimpan dan mengambil pengetahuan dari hasil task
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class KnowledgeFact:
    """Satu fakta pengetahuan"""
    entity: str
    fact: str
    source: str  # action yang menghasilkan
    confidence: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)


class KnowledgeIndex:
    """Index pengetahuan dari hasil task"""
    
    INDEX_FILE = Path("/home/dibs/agentjw/memory/knowledge_index.json")
    
    def __init__(self):
        self.facts: Dict[str, List[KnowledgeFact]] = {}
        self._load()
    
    def add(self, entity: str, fact: str, source: str, confidence: float = 1.0, metadata: Dict = None):
        """Tambahkan fakta"""
        entry = KnowledgeFact(
            entity=entity,
            fact=fact,
            source=source,
            confidence=confidence,
            metadata=metadata or {}
        )
        if entity not in self.facts:
            self.facts[entity] = []
        self.facts[entity].append(entry)
        self._save()
    
    def get(self, entity: str, limit: int = 10) -> List[KnowledgeFact]:
        """Dapatkan fakta untuk entity"""
        return self.facts.get(entity, [])[:limit]
    
    def search(self, query: str) -> List[KnowledgeFact]:
        """Cari fakta berdasarkan query"""
        results = []
        query_lower = query.lower()
        for entity, facts in self.facts.items():
            for fact in facts:
                if query_lower in fact.fact.lower() or query_lower in entity.lower():
                    results.append(fact)
        return results
    
    def get_latest(self, entity: str) -> Optional[KnowledgeFact]:
        """Dapatkan fakta terbaru untuk entity"""
        facts = self.facts.get(entity, [])
        if facts:
            return facts[-1]
        return None
    
    def get_summary(self, entity: str) -> str:
        """Dapatkan ringkasan pengetahuan untuk entity"""
        facts = self.get(entity)
        if not facts:
            return f"Tidak ada pengetahuan tentang {entity}"
        
        lines = [f"📚 Pengetahuan tentang {entity}:"]
        for fact in facts:
            lines.append(f"  • {fact.fact} (source: {fact.source}, confidence: {fact.confidence:.0%})")
        return "\n".join(lines)
    
    def _save(self):
        """Simpan ke file"""
        try:
            data = {}
            for entity, facts in self.facts.items():
                data[entity] = [
                    {
                        "entity": f.entity,
                        "fact": f.fact,
                        "source": f.source,
                        "confidence": f.confidence,
                        "timestamp": f.timestamp,
                        "metadata": f.metadata
                    }
                    for f in facts
                ]
            self.INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.INDEX_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[KNOWLEDGE] Error saving: {e}")
    
    def _load(self):
        """Load dari file"""
        if not self.INDEX_FILE.exists():
            return
        try:
            with open(self.INDEX_FILE) as f:
                data = json.load(f)
            for entity, facts in data.items():
                self.facts[entity] = [
                    KnowledgeFact(
                        entity=f["entity"],
                        fact=f["fact"],
                        source=f["source"],
                        confidence=f.get("confidence", 1.0),
                        timestamp=f.get("timestamp", datetime.now().isoformat()),
                        metadata=f.get("metadata", {})
                    )
                    for f in facts
                ]
        except Exception as e:
            print(f"[KNOWLEDGE] Error loading: {e}")
