"""
Context Compression — Auto-summarize long conversations
"""
from typing import List, Dict, Optional
from datetime import datetime


class ContextCompressor:
    """Kompres context percakapan yang panjang"""

    def __init__(self, max_tokens: int = 8000, max_messages: int = 20):
        self.max_tokens = max_tokens
        self.max_messages = max_messages

    def should_compress(self, history: List[Dict]) -> bool:
        """Cek apakah perlu kompresi"""
        if not history:
            return False
        return len(history) > self.max_messages

    def compress(self, history: List[Dict], llm_client=None) -> List[Dict]:
        """Kompres history menjadi ringkasan"""
        if not self.should_compress(history):
            return history

        # Ambil bagian yang paling penting
        recent = history[-10:]  # Keep last 10 messages
        older = history[:-10]   # Older messages untuk di-ringkas

        if not older:
            return recent

        # Buat ringkasan dari older messages
        summary = self._summarize(older, llm_client)

        # Gabungkan ringkasan dengan recent messages
        compressed = [
            {"role": "system", "content": f"=== RINGKASAN PERCAKAPAN SEBELUMNYA ===\n{summary}"}
        ] + recent

        return compressed

    def _summarize(self, messages: List[Dict], llm_client=None) -> str:
        """Ringkasan percakapan"""
        if not messages:
            return "Tidak ada percakapan sebelumnya."

        # Format pesan
        text = "\n".join([
            f"{m.get('role', 'user')}: {m.get('content', '')[:100]}"
            for m in messages[-10:]
        ])

        if llm_client:
            try:
                prompt = f"Ringkas percakapan berikut dalam 3-5 kalimat:\n\n{text}"
                result = llm_client.chat([{"role": "user", "content": prompt}], max_tokens=300)
                return result
            except:
                pass

        # Fallback: manual summary
        return f"Percakapan sebelumnya ({len(messages)} pesan)"


_compressor = None


def get_context_compressor() -> ContextCompressor:
    global _compressor
    if _compressor is None:
        _compressor = ContextCompressor()
    return _compressor
