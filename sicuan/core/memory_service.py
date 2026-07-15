"""
Memory Service - Long-term memory dengan Obsidian
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class MemoryService:
    """Service untuk menyimpan dan mengambil memory jangka panjang"""

    def __init__(self):
        self.obsidian_root = Path("/home/dibs/agentjw/obsidian")
        self.memory_file = self.obsidian_root / "02-Ideas" / "SiCuan_Memory.md"
        self.conversation_file = Path("/home/dibs/agentjw/memory/conversation_context.json")
        self.state_file = Path("/home/dibs/agentjw/memory/conversation_state.json")

    def get_timestamp(self) -> str:
        """Dapatkan timestamp lengkap"""
        now = datetime.now()
        return now.strftime("%A, %d %B %Y, %H:%M:%S WIB")

    def get_date(self) -> str:
        """Dapatkan tanggal saja"""
        return datetime.now().strftime("%Y-%m-%d")

    def get_weekday(self) -> str:
        """Dapatkan hari"""
        return datetime.now().strftime("%A")

    def save_conversation(self, user_message: str, response: str, context: Dict = None):
        """Simpan percakapan ke Obsidian"""
        try:
            timestamp = self.get_timestamp()
            date = self.get_date()
            
            # Format untuk Obsidian
            entry = f"""
### {timestamp}

**User:** {user_message}

**SiCuan:** {response}

**Context:** {json.dumps(context, indent=2) if context else '{}'}

---
"""
            # Simpan ke file
            if self.memory_file.exists():
                content = self.memory_file.read_text()
                # Tambahkan di awal (terbaru di atas)
                self.memory_file.write_text(entry + "\n" + content)
            else:
                self.memory_file.parent.mkdir(parents=True, exist_ok=True)
                self.memory_file.write_text(f"# SiCuan Memory\n\n{entry}")
            
            return True
        except Exception as e:
            print(f"[Memory] Error saving: {e}")
            return False

    def get_conversation_history(self, limit: int = 20) -> List[Dict]:
        """Dapatkan history percakapan dari conversation_context.json"""
        if not self.conversation_file.exists():
            return []
        
        try:
            data = json.loads(self.conversation_file.read_text())
            topics = data.get("topics", [])
            actions = data.get("actions", [])
            
            # Gabungkan topics dan actions
            history = []
            for i in range(min(len(topics), len(actions), limit)):
                history.append({
                    "topic": topics[i] if i < len(topics) else "",
                    "action": actions[i] if i < len(actions) else "",
                    "timestamp": data.get("updated_at", "")
                })
            
            return history
        except Exception as e:
            print(f"[Memory] Error loading history: {e}")
            return []

    def get_conversation_context(self) -> Dict:
        """Dapatkan konteks percakapan terakhir"""
        if not self.conversation_file.exists():
            return {}
        
        try:
            return json.loads(self.conversation_file.read_text())
        except Exception:
            return {}

    def search_memory(self, query: str) -> List[Dict]:
        """Cari memory berdasarkan keyword"""
        results = []
        if not self.memory_file.exists():
            return results
        
        try:
            content = self.memory_file.read_text()
            # Split berdasarkan "### "
            entries = content.split("### ")
            
            for entry in entries[1:]:  # Skip header
                if query.lower() in entry.lower():
                    # Extract timestamp dan pesan
                    lines = entry.split("\n")
                    timestamp = lines[0].strip() if lines else ""
                    user_line = ""
                    response_line = ""
                    
                    for line in lines:
                        if "**User:**" in line:
                            user_line = line.replace("**User:**", "").strip()
                        if "**SiCuan:**" in line:
                            response_line = line.replace("**SiCuan:**", "").strip()
                    
                    results.append({
                        "timestamp": timestamp,
                        "user": user_line,
                        "response": response_line
                    })
            
            return results[:10]  # Max 10 results
        except Exception as e:
            print(f"[Memory] Error searching: {e}")
            return results


_memory_service = None


def get_memory_service() -> MemoryService:
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
