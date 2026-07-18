"""
Semantic Router - LLM-based intent classification & routing
"""
import json
from typing import Dict, Optional, List


class SemanticRouter:
    """Router berbasis LLM untuk intent classification"""

    def __init__(self):
        self.actions = [
            "analyze_project", "analyze_trading_data", "analyze_url",
            "autonomous_project", "build_project", "build_task_queue",
            "business_analysis", "gallery", "get_file", "godmeme_status",
            "list_projects", "modify_logic", "modify_project",
            "project_summary", "repair_project", "run_bot", "scan_project",
            "shadow_mode_report", "show_log", "trace_code", "video_info",
            "search", "diagnostic", "summarize_context"
        ]

    def route(self, user_message: str, context: str = "", history: list = None) -> Dict:
        """
        Route user message ke action yang tepat menggunakan LLM
        """
        from core.llm_client import llm
        
        history_text = ""
        if history:
            recent = history[-5:] if len(history) > 5 else history
            history_text = "\n".join([f"- {h.get('topic', '')}" for h in recent])
        
        prompt = f"""
Anda adalah router SiCuan. Tentukan action yang tepat untuk user message.

KONTEKS PERCAKAPAN TERAKHIR:
{context}

HISTORY (5 terakhir):
{history_text}

USER MESSAGE: {user_message}

ACTION YANG TERSEDIA:
{', '.join(self.actions)}

Kembalikan JSON:
{{"action": "nama_action", "reason": "alasan", "confidence": 0-100}}

WAJIB:
- Jika user menyebut "gmgn" → action = "search"
- Jika user menyebut "godmeme" → action = "godmeme_status"  
- Jika user menyebut "project" → action = "list_projects"
- Jika user menyebut "bukan" → gunakan konteks sebelumnya
- Jika user hanya menyapa → action = "null"
"""
        try:
                        # Format messages dengan benar (List[Dict])
            messages = [
                {"role": "user", "content": prompt}
            ]
            response = llm._nvidia_nim_chat(messages, max_tokens=200)
            import re
            if isinstance(response, str):
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        if isinstance(result, dict):
                            return result
                    except:
                        pass
            return {"action": "null", "reason": "parse_failed", "confidence": 0}
        except Exception as e:
            print(f"[SemanticRouter] Error: {e}")
        
        return {"action": "null", "reason": "fallback", "confidence": 0}

_router = None


def get_semantic_router() -> SemanticRouter:
    global _router
    if _router is None:
        _router = SemanticRouter()
    return _router
