"""
tools/trading/trading_tool.py - Trading project builder & analyzer
Handles: DEX/CEX bots, strategy analysis, logic modification, backtesting
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from core.logger import logger, console
from core.models import CodeFile, ToolType
from core.config import config
from rich.panel import Panel
from rich.table import Table


TRADING_TEMPLATES = {
    "cex_bot": {
        "description": "CEX trading bot (Binance/OKX/Bybit)",
        "files": ["bot.py", "strategy.py", "risk_manager.py", "exchange.py", "config.py", "main.py"],
        "deps": ["ccxt", "pandas", "numpy", "python-dotenv", "schedule"],
    },
    "dex_bot": {
        "description": "DEX trading bot (Uniswap/PancakeSwap)",
        "files": ["bot.py", "dex_client.py", "strategy.py", "wallet.py", "config.py", "main.py"],
        "deps": ["web3", "pandas", "numpy", "python-dotenv", "requests"],
    },
    "arbitrage": {
        "description": "Cross-exchange arbitrage bot",
        "files": ["arbitrage.py", "scanner.py", "executor.py", "config.py", "main.py"],
        "deps": ["ccxt", "pandas", "numpy", "asyncio", "python-dotenv"],
    },
    "grid_bot": {
        "description": "Grid trading strategy bot",
        "files": ["grid_bot.py", "grid_strategy.py", "order_manager.py", "config.py", "main.py"],
        "deps": ["ccxt", "pandas", "numpy", "python-dotenv"],
    },
    "backtest": {
        "description": "Strategy backtesting framework",
        "files": ["backtest.py", "strategy.py", "data_loader.py", "report.py", "main.py"],
        "deps": ["pandas", "numpy", "matplotlib", "python-dotenv"],
    },
    "signal_bot": {
        "description": "Trading signal generator with indicators",
        "files": ["signal_generator.py", "indicators.py", "notifier.py", "config.py", "main.py"],
        "deps": ["pandas", "numpy", "ta", "requests", "python-dotenv"],
    },
}


class TradingTool:
    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from core.llm_client import llm
            self._llm = llm
        return self._llm

    def detect_trading_intent(self, user_request: str) -> Dict:
        """Detect what kind of trading project is needed"""
        req = user_request.lower()
        detected = {
            "type": "custom",
            "exchange_type": "cex",
            "template": None,
            "exchanges": [],
            "strategy": "",
            "pairs": [],
        }

        # Exchange type
        dex_keywords = ["dex", "uniswap", "pancakeswap", "web3", "defi", "solana", "ethereum", "evm", "blockchain"]
        cex_keywords = ["cex", "binance", "okx", "bybit", "kucoin", "coinbase", "kraken", "bitmex"]
        if any(k in req for k in dex_keywords):
            detected["exchange_type"] = "dex"
        if any(k in req for k in cex_keywords):
            for k in cex_keywords:
                if k in req:
                    detected["exchanges"].append(k)

        # Template matching
        if "arbitrage" in req:
            detected["template"] = "arbitrage"
        elif "grid" in req:
            detected["template"] = "grid_bot"
        elif "backtest" in req or "backtesting" in req:
            detected["template"] = "backtest"
        elif "signal" in req:
            detected["template"] = "signal_bot"
        elif detected["exchange_type"] == "dex":
            detected["template"] = "dex_bot"
        else:
            detected["template"] = "cex_bot"

        # Strategy keywords
        strategies = ["scalping", "swing", "trend following", "mean reversion", "momentum",
                      "rsi", "macd", "bollinger", "ema", "sma", "ichimoku"]
        for s in strategies:
            if s in req:
                detected["strategy"] = s
                break

        # Trading pairs
        pairs = ["btc", "eth", "bnb", "sol", "xrp", "usdt", "usdc"]
        for p in pairs:
            if p in req:
                detected["pairs"].append(p.upper())

        return detected

    def build_trading_project(self, user_request: str, project_id: str = None) -> List[CodeFile]:
        """Generate complete trading project files"""
        intent = self.detect_trading_intent(user_request)
        template = TRADING_TEMPLATES.get(intent["template"], TRADING_TEMPLATES["cex_bot"])

        console.print(Panel(
            f"[cyan]Trading Type:[/cyan] {intent['exchange_type'].upper()}\n"
            f"[cyan]Template:[/cyan] {intent['template']}\n"
            f"[cyan]Strategy:[/cyan] {intent.get('strategy', 'custom')}\n"
            f"[cyan]Exchanges:[/cyan] {', '.join(intent['exchanges']) or 'auto-detect'}\n"
            f"[cyan]Pairs:[/cyan] {', '.join(intent['pairs']) or 'configurable'}",
            title="🤖 Trading Tool Detected",
            border_style="yellow"
        ))

        system_prompt = f"""You are an elite algorithmic trading developer specializing in {'DEX/DeFi' if intent['exchange_type'] == 'dex' else 'CEX'} trading bots.

Write production-quality, immediately runnable Python trading code.

RULES:
1. Complete implementation - no placeholders, no TODO
2. Include proper risk management (stop loss, position sizing)
3. Include error handling and reconnection logic
4. Add clear configuration via .env or config.py
5. Include logging for all trades and errors
6. Code must be safe - never hardcode API keys
7. Include paper trading mode for testing
8. Output ONLY raw Python code, no markdown fences
"""
        generated_files = []
        file_contexts = {}

        for file_name in template["files"]:
            console.print(f"[agent.coder]  📈 Writing: {file_name}[/agent.coder]")
            other_ctx = "\n".join(f"--- {k} ---\n{v[:300]}" for k, v in file_contexts.items())
            prompt = f"""Generate complete Python code for: {file_name}

USER REQUEST: {user_request}
TRADING TYPE: {intent['exchange_type'].upper()} - {intent['template']}
STRATEGY: {intent.get('strategy', 'configurable')}
EXCHANGES: {', '.join(intent['exchanges']) or 'binance (default)'}
PAIRS: {', '.join(intent['pairs']) or 'BTC/USDT (configurable)'}
DEPENDENCIES: {', '.join(template['deps'])}
ALL FILES: {', '.join(template['files'])}

PREVIOUSLY GENERATED:
{other_ctx}

Write COMPLETE code for {file_name}. Raw Python only, no markdown."""

            try:
                code = self.llm.chat(
                    messages=[{"role": "user", "content": prompt}],
                    system=system_prompt,
                    temperature=0.2,
                    max_tokens=8192,
                )
                # Clean markdown
                import re
                code = re.sub(r'^```(?:python|py)?\n?', '', code, flags=re.MULTILINE)
                code = re.sub(r'\n?```$', '', code, flags=re.MULTILINE)
                code = code.strip()

                generated_files.append(CodeFile(path=file_name, content=code, language="python", description=f"Trading: {file_name}"))
                file_contexts[file_name] = code[:400]
            except Exception as e:
                logger.error(f"Failed to generate {file_name}: {e}")

        return generated_files

    def analyze_strategy(self, project_id: str, analysis_request: str = "") -> str:
        """Analyze trading strategy of an existing project"""
        from memory.memory_store import memory_store
        proj = memory_store.get_project(project_id)
        if not proj:
            return "Project not found"

        files = memory_store.get_project_files(project_id)
        if not files:
            # Try reading from disk
            project_dir = Path(proj["project_dir"])
            files = []
            for py_file in project_dir.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    files.append({"path": str(py_file.name), "content": content})
                except Exception:
                    pass

        if not files:
            return "No files found to analyze"

        code_text = ""
        for f in files[:6]:
            code_text += f"\n=== {f['path']} ===\n{f['content'][:2000]}\n"

        prompt = f"""Analyze this trading bot's strategy and logic:

{code_text}

ANALYSIS REQUEST: {analysis_request or 'Full strategy analysis'}

Provide:
1. Strategy Summary (what it does)
2. Entry/Exit Logic Analysis
3. Risk Management Assessment
4. Potential Weaknesses
5. Improvement Recommendations
6. Estimated Performance Profile

Be specific and technical."""

        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system="You are a quant analyst and algorithmic trading expert.",
            temperature=0.3,
            max_tokens=3000,
        )
        return response

    def modify_strategy(self, project_id: str, modification_request: str) -> List[CodeFile]:
        """Modify trading logic based on user request"""
        from memory.memory_store import memory_store
        proj = memory_store.get_project(project_id)
        if not proj:
            return []

        files_db = memory_store.get_project_files(project_id)
        project_dir = Path(proj["project_dir"])

        # Load files from disk if not in DB
        if not files_db:
            files_db = []
            for py_file in project_dir.rglob("*.py"):
                try:
                    files_db.append({"path": py_file.name, "content": py_file.read_text()})
                except Exception:
                    pass

        modified_files = []
        strategy_file = next((f for f in files_db if "strategy" in f["path"].lower()), None)
        target_files = [strategy_file] if strategy_file else files_db[:3]

        for file_info in target_files:
            console.print(f"[agent.repair]🔧 Modifying: {file_info['path']}[/agent.repair]")

            prompt = f"""Modify this trading code based on the request:

FILE: {file_info['path']}
CURRENT CODE:
{file_info['content']}

MODIFICATION REQUEST: {modification_request}

Provide the COMPLETE modified file. Raw Python only."""

            try:
                new_code = self.llm.chat(
                    messages=[{"role": "user", "content": prompt}],
                    system="You are an expert algorithmic trading developer. Modify code precisely as requested.",
                    temperature=0.2,
                    max_tokens=8192,
                )
                import re
                new_code = re.sub(r'^```(?:python|py)?\n?', '', new_code, flags=re.MULTILINE)
                new_code = re.sub(r'\n?```$', '', new_code, flags=re.MULTILINE)
                new_code = new_code.strip()

                cf = CodeFile(path=file_info["path"], content=new_code, language="python")
                modified_files.append(cf)

                # Write to disk
                out_path = project_dir / file_info["path"]
                out_path.write_text(new_code)
                memory_store.save_project_file(project_id, file_info["path"], new_code)
                memory_store.log_work(project_id, proj["name"], "strategy_modified", modification_request[:100])

            except Exception as e:
                logger.error(f"Modification failed for {file_info['path']}: {e}")

        return modified_files


trading_tool = TradingTool()
