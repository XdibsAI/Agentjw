"""
Response Composer Final - Mengubah data internal menjadi jawaban natural
"""

from typing import Dict, List, Optional, Any


class ResponseComposerFinal:
    """Mengubah data query menjadi jawaban natural"""
    
    @staticmethod
    def compose_decision(action: str, decision: Dict, context: str = "") -> str:
        """Compose decision query menjadi jawaban natural"""
        if not decision:
            return f"Belum ada keputusan tentang {action}."
        
        reason_code = decision.get("reason", "")
        confidence = decision.get("confidence", 0)
        candidates = decision.get("candidates", [])
        
        # Natural explanations berdasarkan reason_code
        if reason_code == "PROJECT_NOT_SCANNED":
            if action == "scan_project":
                return f"Aku memilih melakukan scan terlebih dahulu karena project belum memiliki hasil scan yang valid. Kalau langsung masuk ke tahap analisis, ada risiko analisis dilakukan berdasarkan struktur project yang belum diverifikasi.\n\nKeyakinan keputusan: {(confidence * 100):.0f}%."
            else:
                return f"Aku memilih {action} karena project belum memiliki hasil scan yang valid. Langkah ini diperlukan untuk memastikan struktur project diverifikasi terlebih dahulu.\n\nKeyakinan keputusan: {(confidence * 100):.0f}%."
        
        elif reason_code == "SCAN_COMPLETED":
            return f"Aku memilih {action} karena scan sudah selesai dan hasilnya valid. Langkah ini melanjutkan alur kerja yang sudah direncanakan.\n\nKeyakinan keputusan: {(confidence * 100):.0f}%."
        
        else:
            # Generic explanation
            candidate_text = f"Alternatif yang dipertimbangkan: {', '.join(candidates[:3])}" if candidates else ""
            return f"Aku memilih {action} berdasarkan alur kerja yang sudah direncanakan.\n\n{candidate_text}\nKeyakinan keputusan: {(confidence * 100):.0f}%."
    
    @staticmethod
    def compose_knowledge(entity: str, data: Dict, question: str = "") -> str:
        """Compose knowledge query menjadi jawaban natural"""
        if not data:
            return f"Belum ada pengetahuan tentang {entity}. Coba scan project dulu."
        
        files = data.get("total_files", {}).get("value")
        functions = data.get("functions", {}).get("value")
        confidence = data.get("confidence", {}).get("value")
        
        # Jika pertanyaan tentang risiko
        if "risiko" in question.lower() or "resiko" in question.lower():
            if files:
                return f"Kalau langsung melakukan analyze, risikonya adalah analisis dilakukan pada struktur project yang belum dipastikan valid. Pada scan terakhir ditemukan {files} file dalam kondisi valid, sehingga scan dipilih lebih dulu agar proses analyze menggunakan data yang sudah diverifikasi."
            return "Belum ada data scan yang cukup untuk menganalisis risiko."
        
        # Jika pertanyaan tentang jumlah file
        if "file" in question.lower() or "berapa" in question.lower():
            if files:
                return f"Dari scan terakhir, ditemukan {files} file dalam kondisi valid." + (f" Total fungsi: {functions}." if functions else "")
            return "Belum ada data scan yang cukup."
        
        # Jika pertanyaan tentang status
        if "status" in question.lower():
            if files:
                return f"Project {entity} telah di-scan dengan {files} file valid." + (f" Keyakinan: {(confidence * 100):.0f}%." if confidence else "")
            return f"Project {entity} belum di-scan."
        
        # Default: berikan ringkasan
        lines = [f"📚 Pengetahuan tentang {entity}:"]
        for attr, info in data.items():
            lines.append(f"  {attr}: {info['value']}")
        return "\n".join(lines)
    
    @staticmethod
    def compose_memory(state: Dict, question: str = "") -> str:
        """Compose memory query menjadi jawaban natural"""
        if not state:
            return "Belum ada pekerjaan yang tersimpan."
        
        project = state.get("project", "Tidak ada")
        current = state.get("current_task", "Tidak ada")
        completed = state.get("completed_tasks", [])
        pending = state.get("pending_tasks", [])
        
        # Jika pertanyaan tentang resume (besok lanjut)
        if "besok" in question.lower() or "nanti" in question.lower() or "lanjut dari" in question.lower():
            if pending:
                return f"Kalau kita lanjut besok, aku akan mulai dari {pending[0]}. Hari ini {project} sudah selesai dikerjakan untuk {current or 'task terkait'}. Task berikutnya adalah:\n1. {pending[0]}" + (f"\n2. {pending[1]}" if len(pending) > 1 else "")
            elif completed:
                return f"Progress terakhir berhenti setelah {completed[-1]}. Tidak ada task pending untuk {project}."
            return "Belum ada progress yang tersimpan."
        
        # Jika pertanyaan tentang memory (terakhir)
        if completed:
            last = completed[-1]
            lines = [f"Terakhir kita mengerjakan {last} pada project {project}."]
            if pending:
                lines.append(f"📌 Selanjutnya: {pending[0]}")
            if len(pending) > 1:
                lines.append(f"📋 Tersisa: {', '.join(pending[1:])}")
            return "\n".join(lines)
        
        return "Aku belum ingat ada pekerjaan terakhir. Ada yang mau kita kerjakan?"
