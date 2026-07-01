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
