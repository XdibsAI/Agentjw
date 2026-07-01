"""
Context Manager - Mengingat konteks percakapan
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


class ContextManager:
    """Mengelola konteks percakapan"""
    
    def __init__(self):
        self.contexts: Dict[str, Dict] = {}
        self.current_context: Optional[str] = None
    
    def start_context(self, context_id: str, topic: str, data: Dict = None):
        """Mulai konteks baru"""
        self.contexts[context_id] = {
            "topic": topic,
            "data": data or {},
            "started": datetime.now(),
            "last_activity": datetime.now(),
            "history": []
        }
        self.current_context = context_id
    
    def update_context(self, context_id: str, update: Dict):
        """Update konteks"""
        if context_id in self.contexts:
            self.contexts[context_id]["data"].update(update)
            self.contexts[context_id]["last_activity"] = datetime.now()
    
    def add_to_history(self, context_id: str, entry: Dict):
        """Tambahkan ke history"""
        if context_id in self.contexts:
            self.contexts[context_id]["history"].append(entry)
    
    def get_context(self, context_id: str) -> Optional[Dict]:
        """Dapatkan konteks"""
        return self.contexts.get(context_id)
    
    def get_current_context(self) -> Optional[Dict]:
        """Dapatkan konteks saat ini"""
        if self.current_context:
            return self.get_context(self.current_context)
        return None
    
    def get_recent_contexts(self, limit: int = 5) -> List[Dict]:
        """Dapatkan konteks terbaru"""
        sorted_contexts = sorted(
            self.contexts.items(),
            key=lambda x: x[1]["last_activity"],
            reverse=True
        )
        return [ctx for _, ctx in sorted_contexts[:limit]]
    
    def summarize_context(self, context_id: str) -> str:
        """Ringkasan konteks"""
        ctx = self.get_context(context_id)
        if not ctx:
            return "Tidak ada konteks"
        
        return f"""
Topik: {ctx['topic']}
Total interaksi: {len(ctx['history'])}
Terakhir: {ctx['last_activity'].strftime('%H:%M')}

Ringkasan history:
{self._format_history(ctx['history'])}
"""
    
    def _format_history(self, history: List) -> str:
        """Format history untuk ringkasan"""
        if not history:
            return "Belum ada interaksi"
        
        lines = []
        for h in history[-5:]:
            lines.append(f"- {h.get('user', '')[:50]}... → {h.get('response', '')[:50]}...")
        return "\n".join(lines)


    # === PERSISTENCE ===
    def save(self, memory_dir: str = "memory") -> bool:
        """Save semua konteks ke disk"""
        from pathlib import Path
        import json
        from datetime import datetime
        
        path = Path(memory_dir)
        path.mkdir(exist_ok=True)
        file_path = path / "contexts.json"
        
        # Konversi datetime ke string
        data = {
            "current_context": self.current_context,
            "contexts": {}
        }
        
        for ctx_id, ctx in self.contexts.items():
            data["contexts"][ctx_id] = {
                "topic": ctx["topic"],
                "data": ctx["data"],
                "started": ctx["started"].isoformat() if isinstance(ctx["started"], datetime) else ctx["started"],
                "last_activity": ctx["last_activity"].isoformat() if isinstance(ctx["last_activity"], datetime) else ctx["last_activity"],
                "history": ctx["history"]
            }
        
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"[CONTEXT] ✅ Saved {len(self.contexts)} contexts to {file_path}")
        return True
    
    def load(self, memory_dir: str = "memory") -> bool:
        """Load semua konteks dari disk"""
        from pathlib import Path
        import json
        from datetime import datetime
        
        file_path = Path(memory_dir) / "contexts.json"
        if not file_path.exists():
            print(f"[CONTEXT] ℹ️ No context file at {file_path}")
            return False
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            # Restore contexts
            for ctx_id, ctx_data in data.get("contexts", {}).items():
                self.contexts[ctx_id] = {
                    "topic": ctx_data["topic"],
                    "data": ctx_data["data"],
                    "started": datetime.fromisoformat(ctx_data["started"]) if isinstance(ctx_data["started"], str) else ctx_data["started"],
                    "last_activity": datetime.fromisoformat(ctx_data["last_activity"]) if isinstance(ctx_data["last_activity"], str) else ctx_data["last_activity"],
                    "history": ctx_data["history"]
                }
            
            self.current_context = data.get("current_context")
            print(f"[CONTEXT] ✅ Loaded {len(self.contexts)} contexts from {file_path}")
            return True
        except Exception as e:
            print(f"[CONTEXT] ❌ Failed to load: {e}")
            return False
