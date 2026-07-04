"""
Response Composer - Mengubah data internal menjadi jawaban natural
"""

from typing import Dict, List, Optional, Any


class ResponseComposer:
    """Mengubah data query menjadi jawaban natural"""
    
    @staticmethod
    def compose_knowledge(entity: str, data: Dict) -> str:
        """Compose knowledge query response"""
        if not data:
            return f"Belum ada pengetahuan tentang {entity}."
        
        lines = []
        
        # Cari informasi penting
        files = data.get("total_files", {}).get("value")
        functions = data.get("functions", {}).get("value")
        confidence = data.get("confidence", {}).get("value")
        
        if files:
            lines.append(f"Dari scan terakhir, ditemukan {files} file dalam kondisi valid.")
        if functions:
            lines.append(f"Total fungsi yang terdeteksi: {functions}.")
        if confidence:
            lines.append(f"Keyakinan terhadap hasil scan: {confidence}%.")
        
        if lines:
            return "\n".join(lines)
        
        # Fallback: tampilkan semua data
        fallback = [f"📚 Pengetahuan tentang {entity}:"]
        for attr, info in data.items():
            fallback.append(f"  {attr}: {info['value']}")
        return "\n".join(fallback)
    
    @staticmethod
    def compose_decision(action: str, decision: Dict) -> str:
        """Compose decision query response"""
        if not decision:
            return f"Belum ada keputusan tentang {action}."
        
        reason_code = decision.get("reason", "")
        confidence = decision.get("confidence", 0)
        candidates = decision.get("candidates", [])
        
        # Map reason_code ke penjelasan natural
        reason_map = {
            "PROJECT_NOT_SCANNED": "Project belum memiliki hasil scan yang valid. Analisis berikutnya berisiko menggunakan informasi yang belum lengkap.",
            "SCAN_COMPLETED": "Scan sudah selesai dan hasilnya valid. Langkah selanjutnya adalah menganalisis project berdasarkan data yang sudah diverifikasi.",
            "TASK_EXECUTED": "Task ini dipilih karena sesuai dengan alur kerja yang sudah direncanakan.",
        }
        
        reason = reason_map.get(reason_code, f"Alasan: {reason_code}")
        
        if candidates:
            candidate_text = ", ".join(candidates[:3])
            return f"Keputusan: {action}\nAlasan: {reason}\nKeyakinan: {confidence:.0%}\nAlternatif: {candidate_text}"
        
        return f"Keputusan: {action}\nAlasan: {reason}\nKeyakinan: {confidence:.0%}"
    
    @staticmethod
    def compose_summary(state: Dict) -> str:
        """Compose summary query response"""
        if not state:
            return "Belum ada pekerjaan yang bisa diringkas."
        
        project = state.get("project", "Tidak ada")
        current = state.get("current_task", "Tidak ada")
        completed = state.get("completed_tasks", [])
        pending = state.get("pending_tasks", [])
        
        lines = []
        lines.append(f"📋 Ringkasan Pekerjaan")
        lines.append(f"Project: {project}")
        lines.append("")
        
        if completed:
            lines.append(f"✅ Selesai: {', '.join(completed)}")
        
        if current and current not in completed:
            lines.append(f"🔄 Sedang: {current}")
        
        if pending:
            lines.append(f"📌 Tersisa: {', '.join(pending)}")
        
        return "\n".join(lines)
    
    @staticmethod
    def compose_memory(state: Dict, artifact: Dict = None) -> str:
        """Compose memory query response"""
        if not state:
            return "Belum ada pekerjaan yang tersimpan."
        
        project = state.get("project", "Tidak ada")
        current = state.get("current_task", "Tidak ada")
        completed = state.get("completed_tasks", [])
        pending = state.get("pending_tasks", [])
        
        lines = []
        
        if completed:
            last = completed[-1]
            lines.append(f"Terakhir kita menyelesaikan {last}.")
            lines.append("")
        
        lines.append(f"📋 Status saat ini:")
        lines.append(f"  Project: {project}")
        
        if current:
            lines.append(f"  Sedang: {current}")
        
        if pending:
            lines.append(f"  Selanjutnya: {pending[0]}")
        
        if len(pending) > 1:
            lines.append(f"  Tersisa: {', '.join(pending[1:])}")
        
        return "\n".join(lines)
    
    @staticmethod
    def compose_resume(state: Dict) -> str:
        """Compose resume query response (besok lanjut dari mana)"""
        if not state:
            return "Belum ada pekerjaan yang dimulai."
        
        current = state.get("current_task", "Tidak ada")
        completed = state.get("completed_tasks", [])
        pending = state.get("pending_tasks", [])
        project = state.get("project", "Tidak ada")
        
        lines = []
        
        if completed:
            lines.append(f"Terakhir kita menyelesaikan {completed[-1]}.")
        elif current:
            lines.append(f"Kita sedang mengerjakan {current}.")
        else:
            lines.append("Belum ada pekerjaan yang dimulai.")
        
        lines.append("")
        
        if pending:
            lines.append(f"📌 Besok akan dilanjutkan dengan: {pending[0]}")
            if len(pending) > 1:
                lines.append(f"Setelah itu: {', '.join(pending[1:])}")
        else:
            lines.append("✅ Tidak ada task pending. Semua selesai.")
        
        return "\n".join(lines)
