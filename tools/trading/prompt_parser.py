"""
tools/trading/prompt_parser.py
Extracts structured trading requirements from long detailed prompts
"""
import json
from core.logger import logger


class TradingPromptParser:
    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from core.llm_client import llm
            self._llm = llm
        return self._llm

    def parse(self, user_prompt: str) -> dict:
        """Extract all trading requirements from a detailed prompt"""
        system = """You are a trading system requirements analyst.
Extract ALL trading requirements from the user's prompt into structured JSON.
Be thorough - capture every detail mentioned."""

        messages = [{
            "role": "user",
            "content": f"""Extract ALL trading requirements from this prompt into JSON:

{user_prompt}

Return ONLY JSON with these fields:
{{
  "exchange_type": "cex|dex|both",
  "exchanges": ["binance", "okx", etc],
  "pairs": ["BTC/USDT", etc],
  "strategy_name": "name of strategy",
  "strategy_type": "scalping|swing|grid|arbitrage|trend|mean_reversion|custom",
  "timeframes": ["1m", "5m", "1h", etc],
  "indicators": ["RSI", "MACD", "EMA", etc with params if specified],
  "entry_conditions": ["condition 1", "condition 2"],
  "exit_conditions": ["condition 1", "condition 2"],
  "stop_loss": "description or percentage",
  "take_profit": "description or percentage",
  "position_sizing": "fixed|percentage|kelly|description",
  "risk_per_trade": "percentage or amount",
  "max_open_trades": number or null,
  "leverage": "1x or description",
  "capital": "amount or description",
  "features": ["paper trading", "telegram alerts", "auto restart", etc],
  "blockchain": "ethereum|bsc|solana|etc if DEX",
  "special_requirements": ["any other specific requirements"],
  "files_needed": ["suggested file structure"]
}}"""
        }]

        try:
            response = self.llm.chat(
                messages=messages,
                system=system,
                temperature=0.1,
                max_tokens=16000,
                json_mode=True,
            )
            parsed = json.loads(response)
            logger.info(f"Parsed trading requirements: {len(parsed)} fields")
            return parsed
        except Exception as e:
            logger.error(f"Prompt parsing failed: {e}")
            return {"raw_prompt": user_prompt, "strategy_type": "custom"}

    def build_system_prompt(self, parsed: dict, user_prompt: str) -> str:
        """Build rich system prompt for coder from parsed requirements"""
        return f"""You are an elite algorithmic trading developer.

FULL USER REQUIREMENTS:
{user_prompt}

PARSED REQUIREMENTS:
- Exchange: {parsed.get('exchange_type','cex').upper()} - {', '.join(parsed.get('exchanges', ['binance']))}
- Pairs: {', '.join(parsed.get('pairs', ['BTC/USDT']))}
- Strategy: {parsed.get('strategy_name', 'Custom')} ({parsed.get('strategy_type','custom')})
- Timeframes: {', '.join(parsed.get('timeframes', ['1h']))}
- Indicators: {', '.join(parsed.get('indicators', []))}
- Entry: {'; '.join(parsed.get('entry_conditions', []))}
- Exit: {'; '.join(parsed.get('exit_conditions', []))}
- Stop Loss: {parsed.get('stop_loss', 'configurable')}
- Take Profit: {parsed.get('take_profit', 'configurable')}
- Risk/Trade: {parsed.get('risk_per_trade', '1-2%')}
- Leverage: {parsed.get('leverage', '1x')}
- Features: {', '.join(parsed.get('features', []))}
- Special: {'; '.join(parsed.get('special_requirements', []))}

RULES:
1. Implement EVERY requirement above - no shortcuts
2. Complete code - zero placeholders or TODOs
3. All entry/exit conditions must be coded exactly as specified
4. Include all indicators with correct parameters
5. Risk management must match specifications exactly
6. Raw Python only - no markdown fences
"""


trading_prompt_parser = TradingPromptParser()
