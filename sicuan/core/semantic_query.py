"""
Semantic Query Engine - Memahami maksud user dan mengambil data relevan
"""

import json
from typing import Dict, Any, Optional
from core.llm_client import llm
from core.logger import logger


class SemanticQuery:
    """
    Memahami maksud user secara semantic, bukan keyword matching.
    """
    
    @staticmethod
    def understand(user_message: str, context: Dict) -> Dict:
        """
        Pahami apa yang user minta dan ambil data yang relevan.
        """
        # 1. Klasifikasikan intent secara semantic
        intent = SemanticQuery._classify_intent(user_message)
        
        # 2. Tentukan data apa yang dibutuhkan
        data = SemanticQuery._fetch_data(intent, context)
        
        # 3. Buat response natural berdasarkan data
        response = SemanticQuery._compose_response(intent, data, user_message)
        
        return {
            "intent": intent,
            "entity": context.get("project", "godmeme_bot"),
            "data": data,
            "response": response
        }
    
    @staticmethod
    def _classify_intent(user_message: str) -> str:
        """Gunakan LLM untuk klasifikasi intent"""
        prompt = f"""
Klasifikasikan intent dari pesan user berikut:

Pesan: "{user_message}"

Pilihan intent:
- analysis: user ingin analisis mendalam (kenapa rugi, penyebab loss, dll)
- status: user ingin tahu kondisi saat ini (balance, running, dll)
- history: user ingin riwayat (trade history, log, dll)
- decision: user ingin tahu alasan keputusan
- summary: user ingin ringkasan
- task: user ingin melakukan sesuatu (scan, analyze, modify)
- small_talk: user hanya menyapa

Jawab HANYA dengan nama intent, tanpa penjelasan.
"""
        try:
            response = llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=20
            )
            intent = response.strip().lower()
            valid_intents = ["analysis", "status", "history", "decision", "summary", "task", "small_talk"]
            if intent in valid_intents:
                return intent
            return "status"
        except:
            return "status"
    
    @staticmethod
    def _fetch_data(intent: str, context: Dict) -> Dict:
        """Ambil data yang relevan berdasarkan intent"""
        try:
            from projects.godmeme_bot.status_sync_provider import get_godmeme_status
            data = get_godmeme_status()
            
            if intent in ["analysis", "status", "history", "decision"]:
                return {
                    "balance": data.get("balance", "N/A"),
                    "process": data.get("process", {}).get("status", "unknown"),
                    "trades": data.get("trades", 0),
                    "pnl": data.get("realized_pnl", 0),
                    "buy": data.get("buy", 0),
                    "sell": data.get("sell", 0),
                    "positions": data.get("positions", []),
                    "raw": str(data)[:500]
                }
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return {"error": str(e)}
    
    @staticmethod
    def _compose_response(intent: str, data: Dict, user_message: str) -> str:
        """Gunakan LLM untuk compose response natural"""
        
        if data.get("error"):
            return f"Maaf, aku tidak bisa mengakses data saat ini. Error: {data['error']}"
        
        context = f"""
User bertanya: "{user_message}"

Intent: {intent}

Data trading yang tersedia:
- Balance: {data.get('balance', 'N/A')} SOL
- Process: {data.get('process', 'unknown')}
- Trades: {data.get('trades', 0)}
- Realized PnL: {data.get('pnl', 0):.4f} SOL
- BUY: {data.get('buy', 0)}
- SELL: {data.get('sell', 0)}
- Positions: {len(data.get('positions', []))}

Buat jawaban yang natural, santai, dan langsung menjawab pertanyaan user.
Gunakan data di atas sebagai dasar jawaban.
JANGAN hardcode template atau jawaban tetap.
Jawab dalam bahasa Indonesia.
"""
        
        try:
            response = llm.chat(
                messages=[{"role": "user", "content": context}],
                temperature=0.5,
                max_tokens=500
            )
            return response
        except Exception as e:
            logger.error(f"Compose response error: {e}")
            # Fallback sederhana
            return f"Status bot: {data.get('process', 'unknown')}, Balance: {data.get('balance', 'N/A')} SOL, PnL: {data.get('pnl', 0):.4f} SOL"
