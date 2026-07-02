"""
mcp/servers/gusmcp_server.py - Gusmcp Server
Rebuilds the Gusmcp MCP server as a proper FastAPI-based MCP server
Exposes tools for AgentJW and external MCP clients
"""
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


# ── Tool Definitions ──────────────────────────────────────────
GUSMCP_TOOLS = [
    {
        "name": "analyze_trading_strategy",
        "description": "Deeply analyze a trading strategy and return structured insights",
        "parameters": {
            "code": {"type": "string", "description": "Trading strategy code"},
            "context": {"type": "string", "description": "Additional context"},
        },
    },
    {
        "name": "generate_trading_signal",
        "description": "Generate buy/sell signal based on market data",
        "parameters": {
            "token": {"type": "string"},
            "price_data": {"type": "object"},
            "strategy": {"type": "string"},
        },
    },
    {
        "name": "check_token_safety",
        "description": "Check if a Solana token is safe to trade (rug pull detection)",
        "parameters": {
            "token_address": {"type": "string"},
            "chain": {"type": "string", "default": "solana"},
        },
    },
    {
        "name": "get_market_sentiment",
        "description": "Get market sentiment for a token from social/on-chain data",
        "parameters": {
            "token": {"type": "string"},
            "timeframe": {"type": "string", "default": "1h"},
        },
    },
    {
        "name": "optimize_entry_point",
        "description": "Calculate optimal entry price and size for a trade",
        "parameters": {
            "token": {"type": "string"},
            "capital": {"type": "number"},
            "risk_percent": {"type": "number"},
            "strategy": {"type": "string"},
        },
    },
    {
        "name": "build_project_tool",
        "description": "Build a software project using AgentJW",
        "parameters": {
            "description": {"type": "string"},
            "category": {"type": "string"},
        },
    },
    {
        "name": "memory_recall",
        "description": "Recall information from AgentJW persistent memory",
        "parameters": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 5},
        },
    },
]


class GusmcpServer:
    """
    Gusmcp - AgentJW MCP Server
    Can run as standalone HTTP server or be imported directly
    """
    def __init__(self):
        self.tools = {t["name"]: t for t in GUSMCP_TOOLS}
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from core.llm_client import llm
            self._llm = llm
        return self._llm

    def list_tools(self) -> List[Dict]:
        return GUSMCP_TOOLS

    def execute_tool(self, tool_name: str, parameters: Dict) -> Dict:
        """Execute a Gusmcp tool"""
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}

        handler = getattr(self, f"_tool_{tool_name}", None)
        if handler:
            try:
                result = handler(parameters)
                return {"status": "ok", "result": result, "tool": tool_name}
            except Exception as e:
                return {"status": "error", "message": str(e), "tool": tool_name}

        return {"status": "not_implemented", "tool": tool_name}

    def _tool_analyze_trading_strategy(self, params: Dict) -> Dict:
        code = params.get("code", "")
        context = params.get("context", "")
        prompt = f"""Analyze this trading strategy in detail:

CODE:
{code}

CONTEXT: {context}

Return JSON with:
{{
  "strategy_type": "...",
  "entry_logic": ["..."],
  "exit_logic": ["..."],
  "risk_score": 1-10,
  "profit_potential": "low|medium|high",
  "weaknesses": ["..."],
  "improvements": ["..."],
  "recommended_pairs": ["..."],
  "recommended_timeframe": "..."
}}"""
        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system="You are a quantitative trading analyst.",
            temperature=0.2, max_tokens=16000, json_mode=True,
        )
        return json.loads(response)

    def _tool_check_token_safety(self, params: Dict) -> Dict:
        import requests
        token = params.get("token_address", "")
        try:
            r = requests.get(
                f"https://api.dexscreener.com/latest/dex/tokens/{token}",
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                pairs = data.get("pairs", [])
                if not pairs:
                    return {"safe": False, "reason": "No liquidity pairs found", "risk": "high"}
                p = pairs[0]
                liquidity = p.get("liquidity", {}).get("usd", 0) or 0
                volume = p.get("volume", {}).get("h24", 0) or 0
                risk = "low" if liquidity > 50000 else ("medium" if liquidity > 10000 else "high")
                return {
                    "safe": liquidity > 10000,
                    "risk": risk,
                    "liquidity_usd": liquidity,
                    "volume_24h": volume,
                    "symbol": p.get("baseToken", {}).get("symbol", "?"),
                    "dex": p.get("dexId"),
                }
        except Exception as e:
            return {"safe": False, "reason": str(e), "risk": "unknown"}

    def _tool_get_market_sentiment(self, params: Dict) -> Dict:
        import requests
        token = params.get("token", "")
        try:
            r = requests.get(
                f"https://api.dexscreener.com/latest/dex/search?q={token}",
                timeout=10,
            )
            if r.status_code == 200:
                pairs = r.json().get("pairs", [])
                if pairs:
                    p = pairs[0]
                    changes = p.get("priceChange", {})
                    m5 = float(changes.get("m5", 0) or 0)
                    h1 = float(changes.get("h1", 0) or 0)
                    h24 = float(changes.get("h24", 0) or 0)
                    sentiment = "bullish" if h1 > 5 else ("bearish" if h1 < -5 else "neutral")
                    return {
                        "sentiment": sentiment,
                        "momentum_5m": m5,
                        "momentum_1h": h1,
                        "momentum_24h": h24,
                        "volume_24h": p.get("volume", {}).get("h24"),
                        "price_usd": p.get("priceUsd"),
                    }
        except Exception as e:
            return {"sentiment": "unknown", "error": str(e)}

    def _tool_generate_trading_signal(self, params: Dict) -> Dict:
        token = params.get("token", "")
        price_data = params.get("price_data", {})
        strategy = params.get("strategy", "momentum")
        prompt = f"""Generate a trading signal for:
Token: {token}
Strategy: {strategy}
Price Data: {json.dumps(price_data)[:500]}

Return JSON:
{{
  "signal": "buy|sell|hold",
  "confidence": 0.0-1.0,
  "entry_price": number_or_null,
  "stop_loss": number_or_null,
  "take_profit": number_or_null,
  "reasoning": "brief reason",
  "risk_reward": number
}}"""
        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system="You are an algorithmic trading signal generator.",
            temperature=0.1, max_tokens=16000, json_mode=True,
        )
        return json.loads(response)

    def _tool_optimize_entry_point(self, params: Dict) -> Dict:
        capital = float(params.get("capital", 0.1))
        risk_pct = float(params.get("risk_percent", 1.0))
        token = params.get("token", "")
        strategy = params.get("strategy", "")
        risk_amount = capital * (risk_pct / 100)
        position_size = min(capital * 0.1, risk_amount * 10)
        return {
            "recommended_position_size": round(position_size, 4),
            "risk_amount": round(risk_amount, 4),
            "capital": capital,
            "risk_percent": risk_pct,
            "token": token,
            "strategy": strategy,
            "notes": "Adjust based on current market volatility",
        }

    def _tool_build_project_tool(self, params: Dict) -> Dict:
        description = params.get("description", "")
        category = params.get("category", "general")
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from agents.workflow.workflow_engine import workflow_engine
        result = workflow_engine.run(
            user_request=description,
            skip_dialog=True,
        )
        return result

    def _tool_memory_recall(self, params: Dict) -> Dict:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from memory.memory_store import memory_store
        results = memory_store.search_memories(
            params.get("query", ""),
            limit=int(params.get("limit", 5)),
        )
        return {"memories": results, "count": len(results)}

    def run_http_server(self, host: str = "0.0.0.0", port: int = 8765):
        """Run as HTTP server for external MCP clients"""
        try:
            from fastapi import FastAPI, HTTPException
            from pydantic import BaseModel
            import uvicorn

            app = FastAPI(title="Gusmcp - AgentJW MCP Server", version="2.0.0")

            class ToolRequest(BaseModel):
                parameters: Dict = {}

            @app.get("/")
            def root():
                return {"name": "Gusmcp", "version": "2.0.0", "tools": len(self.tools)}

            @app.get("/tools")
            def list_tools():
                return {"tools": self.list_tools()}

            @app.post("/tools/{tool_name}")
            def execute_tool(tool_name: str, request: ToolRequest):
                return self.execute_tool(tool_name, request.parameters)

            @app.get("/health")
            def health():
                return {"status": "ok", "timestamp": datetime.now().isoformat()}

            print(f"\n🚀 Gusmcp MCP Server running on http://{host}:{port}")
            print(f"📚 Tools: {len(self.tools)}")
            print(f"🔗 Docs: http://{host}:{port}/docs\n")
            uvicorn.run(app, host=host, port=port)

        except ImportError:
            print("Install fastapi+uvicorn: pip install fastapi uvicorn")


gusmcp_server = GusmcpServer()

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    gusmcp_server.run_http_server(port=port)
