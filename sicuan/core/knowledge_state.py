"""
Knowledge State - Menyimpan hasil analisis untuk referensi masa depan
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class KnowledgeEntry:
    """Satu entri pengetahuan"""
    topic: str
    content: str
    source: str  # project, file, analysis
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 1.0
    tags: List[str] = field(default_factory=list)


class KnowledgeState:
    """Menyimpan pengetahuan dari hasil analisis"""
    
    KNOWLEDGE_FILE = Path("/home/dibs/agentjw/memory/knowledge.json")
    
    def __init__(self):
        self.knowledge: Dict[str, List[KnowledgeEntry]] = {}
        self._load()
    
    def add(self, topic: str, content: str, source: str, confidence: float = 1.0, tags: List[str] = None):
        """Tambahkan pengetahuan"""
        entry = KnowledgeEntry(
            topic=topic,
            content=content,
            source=source,
            confidence=confidence,
            tags=tags or []
        )
        if topic not in self.knowledge:
            self.knowledge[topic] = []
        self.knowledge[topic].append(entry)
        self._save()
    
    def get(self, topic: str, limit: int = 5) -> List[KnowledgeEntry]:
        """Dapatkan pengetahuan berdasarkan topik"""
        return self.knowledge.get(topic, [])[:limit]
    
    def search(self, query: str) -> List[KnowledgeEntry]:
        """Cari pengetahuan berdasarkan query"""
        results = []
        query_lower = query.lower()
        for topic, entries in self.knowledge.items():
            for entry in entries:
                if query_lower in topic.lower() or query_lower in entry.content.lower():
                    results.append(entry)
        return results
    
    def get_by_source(self, source: str) -> List[KnowledgeEntry]:
        """Dapatkan pengetahuan berdasarkan sumber"""
        results = []
        for topic, entries in self.knowledge.items():
            for entry in entries:
                if entry.source == source:
                    results.append(entry)
        return results
    
    def _save(self):
        """Simpan ke file"""
        try:
            data = {}
            for topic, entries in self.knowledge.items():
                data[topic] = [
                    {
                        "topic": e.topic,
                        "content": e.content,
                        "source": e.source,
                        "created_at": e.created_at,
                        "confidence": e.confidence,
                        "tags": e.tags
                    }
                    for e in entries
                ]
            self.KNOWLEDGE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.KNOWLEDGE_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[KNOWLEDGE] Error saving: {e}")
    
    def _load(self):
        """Load dari file"""
        if not self.KNOWLEDGE_FILE.exists():
            return
        try:
            with open(self.KNOWLEDGE_FILE) as f:
                data = json.load(f)
            for topic, entries in data.items():
                self.knowledge[topic] = [
                    KnowledgeEntry(
                        topic=e["topic"],
                        content=e["content"],
                        source=e["source"],
                        created_at=e["created_at"],
                        confidence=e.get("confidence", 1.0),
                        tags=e.get("tags", [])
                    )
                    for e in entries
                ]
        except Exception as e:
            print(f"[KNOWLEDGE] Error loading: {e}")
    
    def get_summary(self) -> str:
        """Dapatkan ringkasan pengetahuan"""
        topics = list(self.knowledge.keys())
        if not topics:
            return "No knowledge stored"
        lines = ["📚 KNOWLEDGE SUMMARY", "=" * 40]
        for topic in topics[:10]:
            count = len(self.knowledge[topic])
            lines.append(f"  {topic}: {count} entries")
        return "\n".join(lines)
