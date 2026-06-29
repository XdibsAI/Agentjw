"""
Long-term Memory - Menyimpan pengetahuan dan pelajaran jangka panjang
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class LongTermMemory:
    """Menyimpan pengetahuan dan pelajaran jangka panjang"""
    
    MEMORY_FILE = Path("/home/dibs/agentjw/memory/long_term.json")
    
    def __init__(self):
        self.memory: Dict = {
            "lessons": [],
            "facts": [],
            "preferences": [],
            "conversations": []
        }
        self._load()
    
    def add_lesson(self, topic: str, content: str, source: str = ""):
        """Tambahkan pelajaran"""
        self.memory["lessons"].append({
            "topic": topic,
            "content": content,
            "source": source,
            "timestamp": datetime.now().isoformat()
        })
        self._save()
    
    def get_lessons(self, topic: str = None) -> List[Dict]:
        """Dapatkan pelajaran berdasarkan topik"""
        if topic:
            return [l for l in self.memory["lessons"] if topic in l["topic"]]
        return self.memory["lessons"]
    
    def add_fact(self, entity: str, attribute: str, value: any):
        """Tambahkan fakta"""
        self.memory["facts"].append({
            "entity": entity,
            "attribute": attribute,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
        self._save()
    
    def get_facts(self, entity: str = None) -> List[Dict]:
        """Dapatkan fakta berdasarkan entity"""
        if entity:
            return [f for f in self.memory["facts"] if f["entity"] == entity]
        return self.memory["facts"]
    
    def add_preference(self, key: str, value: any):
        """Tambahkan preferensi"""
        self.memory["preferences"].append({
            "key": key,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
        self._save()
    
    def get_preferences(self, key: str = None) -> List[Dict]:
        """Dapatkan preferensi berdasarkan key"""
        if key:
            return [p for p in self.memory["preferences"] if p["key"] == key]
        return self.memory["preferences"]
    
    def add_conversation(self, summary: str, key_points: List[str]):
        """Tambahkan ringkasan percakapan"""
        self.memory["conversations"].append({
            "summary": summary,
            "key_points": key_points,
            "timestamp": datetime.now().isoformat()
        })
        self._save()
    
    def get_conversations(self, limit: int = 5) -> List[Dict]:
        """Dapatkan ringkasan percakapan terakhir"""
        return self.memory["conversations"][-limit:]
    
    def search(self, query: str) -> List[Dict]:
        """Cari di semua memory"""
        results = []
        query_lower = query.lower()
        for category, items in self.memory.items():
            for item in items:
                text = str(item).lower()
                if query_lower in text:
                    results.append({"category": category, "item": item})
        return results
    
    def get_summary(self) -> str:
        """Dapatkan ringkasan memory"""
        lines = ["📚 LONG-TERM MEMORY SUMMARY"]
        lines.append(f"  Lessons: {len(self.memory['lessons'])}")
        lines.append(f"  Facts: {len(self.memory['facts'])}")
        lines.append(f"  Preferences: {len(self.memory['preferences'])}")
        lines.append(f"  Conversations: {len(self.memory['conversations'])}")
        if self.memory["lessons"]:
            lines.append("\n📖 Recent Lessons:")
            for lesson in self.memory["lessons"][-3:]:
                lines.append(f"  • {lesson['topic']}: {lesson['content'][:100]}...")
        return "\n".join(lines)
    
    def _load(self):
        """Load dari file"""
        if self.MEMORY_FILE.exists():
            try:
                with open(self.MEMORY_FILE) as f:
                    self.memory = json.load(f)
            except Exception as e:
                print(f"[LTM] Error loading: {e}")
    
    def _save(self):
        """Save ke file"""
        try:
            self.MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.MEMORY_FILE, "w") as f:
                json.dump(self.memory, f, indent=2, default=str)
        except Exception as e:
            print(f"[LTM] Error saving: {e}")


def get_long_term_memory() -> LongTermMemory:
    """Singleton instance"""
    global _ltm
    if '_ltm' not in globals():
        _ltm = LongTermMemory()
    return _ltm
