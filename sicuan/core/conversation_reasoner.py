"""
Conversation Reasoner - Memahami maksud pertanyaan berdasarkan state
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class IntentType(Enum):
    EXPLANATION = "explanation"
    PROGRESS = "progress"
    SUMMARY = "summary"
    CONTINUATION = "continuation"
    REFERENCE = "reference"
    CLARIFICATION = "clarification"
    ACTION = "action"
    FALLBACK = "fallback"


@dataclass
class IntentResult:
    intent: IntentType
    confidence: float
    data: Dict


class ConversationReasoner:
    """Memahami maksud pertanyaan berdasarkan state"""
    
    # Pattern untuk setiap intent
    PATTERNS = {
        IntentType.EXPLANATION: [
            "kenapa", "mengapa", "alasan", "kenapa", "kok", "jelaskan", 
            "maksudnya", "artinya", "apa maksud", "apa arti"
        ],
        IntentType.PROGRESS: [
            "sampai mana", "progress", "sejauh mana", "berapa", 
            "sudah berapa", "status", "perkembangan"
        ],
        IntentType.SUMMARY: [
            "ringkas", "rangkum", "summary", "resume", "intisari",
            "kesimpulan", "simpulkan"
        ],
        IntentType.CONTINUATION: [
            "lanjut", "terus", "next", "continue", "gas", "ayo", "oke"
        ],
        IntentType.REFERENCE: [
            "yang tadi", "tadi", "itu", "kemarin", "sebelumnya",
            "barusan", "yang lalu"
        ],
        IntentType.CLARIFICATION: [
            "maksudnya", "apa itu", "apa maksud", "maksud kamu",
            "yang mana", "contoh"
        ],
    }
    
    def __init__(self, conversation_state=None, execution_state=None, knowledge_state=None):
        self.conversation_state = conversation_state
        self.execution_state = execution_state
        self.knowledge_state = knowledge_state
    
    def classify(self, user_message: str) -> IntentResult:
        """Klasifikasikan intent dari pesan user"""
        message_lower = user_message.lower()
        
        # Cek pattern satu per satu dengan prioritas
        for intent, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return IntentResult(
                        intent=intent,
                        confidence=0.9,
                        data={"matched_pattern": pattern}
                    )
        
        # Jika tidak ada pattern yang cocok, cek context
        if self.conversation_state and self.conversation_state.last_action:
            # Ada state aktif, mungkin continuation
            if len(message_lower.split()) <= 2:
                return IntentResult(
                    intent=IntentType.CONTINUATION,
                    confidence=0.6,
                    data={"reason": "short message with active state"}
                )
        
        return IntentResult(
            intent=IntentType.FALLBACK,
            confidence=0.3,
            data={"reason": "no pattern matched"}
        )
    
    def generate_response(self, intent: IntentResult, user_message: str) -> Optional[str]:
        """Generate response berdasarkan intent dan state"""
        
        if intent.intent == IntentType.EXPLANATION:
            return self._explain()
        
        if intent.intent == IntentType.PROGRESS:
            return self._show_progress()
        
        if intent.intent == IntentType.SUMMARY:
            return self._summarize()
        
        if intent.intent == IntentType.REFERENCE:
            return self._reference()
        
        return None
    
    def _explain(self) -> str:
        """Jelaskan alasan langkah saat ini"""
        if not self.conversation_state or not self.conversation_state.last_action:
            return "Belum ada tindakan yang saya lakukan sebelumnya."
        
        action = self.conversation_state.last_action
        pending = self.conversation_state.pending_tasks
        
        reasons = {
            "scan_project": "Saya perlu memastikan struktur project valid sebelum menganalisis strategi.",
            "analyze_project": "Setelah scan, saya perlu menganalisis kode untuk menemukan potensi masalah.",
            "repair_project": "Saya memperbaiki masalah yang ditemukan saat analisis.",
            "modify_logic": "Saya mengubah logika untuk meningkatkan performa.",
            "run_bot": "Saya menjalankan bot untuk melihat hasil perubahan."
        }
        
        reason = reasons.get(action, f"Langkah ini adalah bagian dari alur kerja yang sudah direncanakan.")
        
        next_steps = ", ".join(pending[:2]) if pending else "Tidak ada"
        
        return f"""
Alasan saya memilih {action}:

{reason}

📋 Selanjutnya: {next_steps}

💡 Berdasarkan state saat ini, ini adalah langkah yang paling sesuai untuk mencapai tujuan.
"""
    
    def _show_progress(self) -> str:
        """Tampilkan progress"""
        if not self.conversation_state:
            return "Belum ada pekerjaan yang dimulai."
        
        completed = self.conversation_state.completed_tasks
        pending = self.conversation_state.pending_tasks
        current = self.conversation_state.current_task
        
        total = len(completed) + len(pending)
        done = len(completed)
        percent = (done / total * 100) if total > 0 else 0
        
        bar = self._progress_bar(percent)
        
        return f"""
📊 PROGRESS {bar} {percent:.0f}%

✅ Selesai ({done}/{total}): {', '.join(completed) if completed else 'Belum ada'}

📋 Sedang: {current or 'Tidak ada task aktif'}

📌 Tersisa: {', '.join(pending) if pending else 'Tidak ada'}
"""
    
    def _summarize(self) -> str:
        """Ringkasan pekerjaan"""
        if not self.conversation_state:
            return "Belum ada pekerjaan yang bisa diringkas."
        
        project = self.conversation_state.project or "Tidak ada"
        completed = self.conversation_state.completed_tasks
        pending = self.conversation_state.pending_tasks
        last_result = self.conversation_state.last_result or "Belum ada hasil"
        
        return f"""
📋 RINGKASAN PEKERJAAN

Project: {project}

✅ Selesai:
{self._format_list(completed) if completed else '  - Belum ada'}

📌 Tersisa:
{self._format_list(pending) if pending else '  - Tidak ada'}

📝 Hasil terakhir:
{last_result[:200]}...
"""
    
    def _reference(self) -> str:
        """Referensi ke hasil sebelumnya"""
        if self.conversation_state and self.conversation_state.last_result:
            return f"Hasil terakhir: {self.conversation_state.last_result[:300]}"
        return "Belum ada hasil terakhir yang tersimpan."
    
    def _progress_bar(self, percent: float, width: int = 20) -> str:
        """Buat progress bar"""
        filled = int((percent / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return bar
    
    def _format_list(self, items: List[str]) -> str:
        """Format list untuk ringkasan"""
        if not items:
            return "  - Tidak ada"
        return "\n".join([f"  ✓ {item}" for item in items])
