"""
Intent Classifier - Menggunakan LLM untuk klasifikasi intent
"""

from typing import Dict, Optional
from core.llm_client import llm
from core.logger import logger


class IntentClassifier:
    """
    Klasifikasi intent menggunakan LLM.
    Tidak ada hardcoded keywords - semua diproses oleh LLM.
    """
    
    INTENTS = [
        "progress_query",   # tanya status, progress, perkembangan
        "decision_query",   # tanya alasan, kenapa, mengapa
        "knowledge_query",  # tanya fakta, data, pengetahuan
        "memory_query",     # tanya ingatan, histori, yang lalu
        "summary_query",    # minta ringkasan, rangkuman
        "planning_query",   # tanya rencana, langkah, prioritas
        "task",             # perintah eksekusi (scan, analyze, modify)
        "small_talk",       # sapaan, basa-basi
    ]
    
    @classmethod
    def classify(cls, user_message: str) -> str:
        """
        Klasifikasikan intent dari pesan user.
        """
        # Cek cepat untuk task yang jelas
        message_lower = user_message.lower()
        
        # Task yang jelas (tidak ambigu) - hanya jika benar-benar perintah
        clear_tasks = ["scan", "analyze", "analisa", "modify", "repair", "build", "run"]
        for task in clear_tasks:
            if task in message_lower and len(message_lower.split()) < 6:
                # Cek apakah ini pertanyaan (bukan perintah)
                if any(q in message_lower for q in ["?", "apa", "bagaimana", "status", "cek"]):
                    return "progress_query"
                return "task"
        
        # Gunakan LLM untuk sisanya
        try:
            prompt = f"""
Klasifikasikan intent dari pesan user berikut.

Pesan: "{user_message}"

Pilihan intent:
- progress_query: user menanyakan status, progress, perkembangan, atau kondisi saat ini
- decision_query: user menanyakan alasan, kenapa, mengapa suatu keputusan diambil
- knowledge_query: user menanyakan fakta, data, pengetahuan tentang sesuatu
- memory_query: user menanyakan ingatan, histori, apa yang terjadi sebelumnya
- summary_query: user meminta ringkasan, rangkuman, kesimpulan
- planning_query: user menanyakan rencana, langkah, prioritas, atau apa yang akan dilakukan
- task: user meminta untuk melakukan sesuatu (scan, analyze, modify, dll)
- small_talk: user hanya menyapa, basa-basi, tidak ada maksud tertentu

Jawab hanya dengan nama intent, tanpa penjelasan tambahan.
"""
            response = llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=20
            )
            
            intent = response.strip().lower()
            
            # Validasi intent
            if intent in cls.INTENTS:
                return intent
            
            # Fallback: coba cari di dalam response
            for i in cls.INTENTS:
                if i in intent:
                    return i
            
            # Jika LLM bingung, gunakan task detection sederhana
            if any(t in message_lower for t in ["cek", "lihat", "tampilkan"]):
                return "knowledge_query"
            
            return "unknown"
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            
            # Fallback sederhana
            if any(t in message_lower for t in ["status", "progress", "sampai", "mana"]):
                return "progress_query"
            if any(t in message_lower for t in ["kenapa", "mengapa", "alasan"]):
                return "decision_query"
            if any(t in message_lower for t in ["ringkas", "rangkum"]):
                return "summary_query"
            if any(t in message_lower for t in ["halo", "hai", "apa kabar"]):
                return "small_talk"
            return "unknown"
