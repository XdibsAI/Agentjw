"""
Conversation Context Manager - Mengelola konteks percakapan
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationContext:
    """Konteks percakapan yang sedang berlangsung"""
    
    # Topik terakhir
    last_topic: Optional[str] = None
    last_action: Optional[str] = None
    last_entity: Optional[str] = None
    last_intent: Optional[str] = None
    last_result: Optional[str] = None
    
    # History
    topics: list = field(default_factory=list)
    actions: list = field(default_factory=list)
    entities: list = field(default_factory=list)
    
    # Metadata
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def update(self, topic: str = None, action: str = None, entity: str = None, intent: str = None, result: str = None):
        """Update konteks"""
        if topic:
            self.last_topic = topic
            self.topics.append(topic)
        if action:
            self.last_action = action
            self.actions.append(action)
        if entity:
            self.last_entity = entity
            self.entities.append(entity)
        if intent:
            self.last_intent = intent
        if result:
            self.last_result = result
        self.updated_at = datetime.now().isoformat()
    
    def get_context(self) -> Dict:
        """Dapatkan konteks saat ini"""
        return {
            "last_topic": self.last_topic,
            "last_action": self.last_action,
            "last_entity": self.last_entity,
            "last_intent": self.last_intent,
            "last_result": self.last_result,
            "topics": self.topics[-5:],
            "actions": self.actions[-5:],
            "entities": self.entities[-5:]
        }
    
    def get_summary(self) -> str:
        """Dapatkan ringkasan konteks"""
        lines = []
        if self.last_topic:
            lines.append(f"Topik: {self.last_topic}")
        if self.last_action:
            lines.append(f"Aksi terakhir: {self.last_action}")
        if self.last_entity:
            lines.append(f"Entity: {self.last_entity}")
        if self.last_result:
            lines.append(f"Hasil: {self.last_result[:100]}...")
        return "\n".join(lines) if lines else "Tidak ada konteks"
    
    def is_related(self, message: str) -> bool:
        """Cek apakah pesan terkait dengan konteks"""
        if not self.last_topic:
            return False
        
        # Cek kata kunci
        keywords = ["hasil", "review", "strategi", "lanjut", "tadi", "itu", "yang"]
        return any(k in message.lower() for k in keywords)


    def save(self, memory_dir: str = "memory") -> bool:
        """Save conversation context ke disk"""
        from pathlib import Path
        import json
        from datetime import datetime
        
        path = Path(memory_dir)
        path.mkdir(exist_ok=True)
        file_path = path / "conversation_context.json"
        
        # Convert ke dict (handle semua atribut)
        data = {
            "last_topic": self.last_topic,
            "last_action": self.last_action,
            "last_entity": self.last_entity,
            "last_intent": self.last_intent,
            "last_result": self.last_result,
            "topics": self.topics[-20:],  # Simpan 20 terakhir
            "actions": self.actions[-20:],
            "entities": self.entities[-20:],
            "updated_at": self.updated_at
        }
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"[CONTEXT] ✅ Saved conversation to {file_path}")
        return True
    
    def load(self, memory_dir: str = "memory") -> bool:
        """Load conversation context dari disk"""
        from pathlib import Path
        import json
        from datetime import datetime
        
        file_path = Path(memory_dir) / "conversation_context.json"
        if not file_path.exists():
            print(f"[CONTEXT] ℹ️ No conversation file at {file_path}")
            return False
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Restore atribut
            self.last_topic = data.get("last_topic")
            self.last_action = data.get("last_action")
            self.last_entity = data.get("last_entity")
            self.last_intent = data.get("last_intent")
            self.last_result = data.get("last_result")
            self.topics = data.get("topics", [])
            self.actions = data.get("actions", [])
            self.entities = data.get("entities", [])
            self.updated_at = data.get("updated_at", datetime.now().isoformat())
            
            print(f"[CONTEXT] ✅ Loaded conversation from {file_path}")
            print(f"[CONTEXT]   Last topic: {self.last_topic}")
            print(f"[CONTEXT]   History: {len(self.topics)} topics, {len(self.actions)} actions")
            return True
        except Exception as e:
            print(f"[CONTEXT] ❌ Failed to load: {e}")
            return False
