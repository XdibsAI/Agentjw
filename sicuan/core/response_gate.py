"""
Response Gate - Menentukan jenis respons yang tepat
"""

from typing import Dict, Optional
import re


class ResponseGate:
    """Menentukan apakah cukup jawab singkat atau perlu deep dive"""

    # Pola pertanyaan santai
    CASUAL_PATTERNS = [
        r"halo|hai|hey|hi",
        r"apa kabar|gimana|kondisi",
        r"kenapa kamu|kok kamu|kamu kenapa",
        r"woe|wow|buset|anjay",
        r"oke|ok|sip|mantap",
        r"makasih|thanks|terima kasih",
    ]

    # Pola yang butuh audit
    AUDIT_PATTERNS = [
        r"analisa|audit|cek|scan|review",
        r"trading|profit|pnl|status",
        r"bug|error|masalah|rusak",
        r"perbaiki|repair|fix",
    ]

    def classify(self, user_message: str, last_action: Optional[str] = None) -> Dict:
        """
        Klasifikasi jenis respons yang dibutuhkan
        Returns:
            {
                "type": "casual" | "diagnostic" | "audit" | "deep_dive",
                "reason": "penjelasan singkat",
                "needs_audit": bool,
                "needs_llm": bool,
                "response_style": "short" | "detailed" | "full"
            }
        """
        msg = user_message.lower()

        # 1. Cek apakah casual
        for pattern in self.CASUAL_PATTERNS:
            if re.search(pattern, msg):
                # Kecuali ada kata "error" atau "bug" - maka diagnostic
                if "error" in msg or "bug" in msg or "masalah" in msg:
                    return {
                        "type": "diagnostic",
                        "reason": "Pertanyaan tentang error, perlu diagnostic ringan",
                        "needs_audit": False,
                        "needs_llm": True,
                        "response_style": "short"
                    }
                return {
                    "type": "casual",
                    "reason": "Pertanyaan santai, cukup jawab singkat",
                    "needs_audit": False,
                    "needs_llm": True,
                    "response_style": "short"
                }

        # 2. Cek apakah butuh audit
        for pattern in self.AUDIT_PATTERNS:
            if re.search(pattern, msg):
                # Jika hanya "cek" tanpa target spesifik, cukup diagnostic
                if "cek" in msg and not any(w in msg for w in ["project", "trading", "status", "audit"]):
                    return {
                        "type": "diagnostic",
                        "reason": "Cek umum, cukup diagnostic ringan",
                        "needs_audit": False,
                        "needs_llm": True,
                        "response_style": "short"
                    }
                return {
                    "type": "audit",
                    "reason": "Minta analisa/audit spesifik",
                    "needs_audit": True,
                    "needs_llm": True,
                    "response_style": "full"
                }

        # 3. Default - LLM decide
        return {
            "type": "llm_decide",
            "reason": "LLM akan menentukan jenis respons",
            "needs_audit": False,
            "needs_llm": True,
            "response_style": "balanced"
        }


def get_response_gate() -> ResponseGate:
    _gate = None
    if _gate is None:
        _gate = ResponseGate()
    return _gate
