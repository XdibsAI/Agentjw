"""
mcp/mcp_client.py - MCP Client Layer
Connects AgentJW to MCP servers (Solana, Market Data, FileSystem, Custom)
"""
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional
from core.logger import logger, console
from core.config import config
from rich.panel import Panel
from rich.table import Table


class MCPTool:
    def __init__(self, name: str, description: str, server: str, parameters: Dict):
        self.name = name
        self.description = description
        self.server = server
        self.parameters = parameters

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "server": self.server,
            "parameters": self.parameters,
        }


class MCPClient:
    """
    MCP Client that connects to multiple MCP servers.
    Acts as a tool registry and executor for AgentJW agents.
    """
    def __init__(self):
        self.servers: Dict[str, Dict] = {}
        self.tools: Dict[str, MCPTool] = {}
        self._llm = None
        self._register_builtin_servers()

    @property
    def llm(self):
        if self._llm is None:
            from core.llm_client import llm
            self._llm = llm
        return self._llm

    def _register_builtin_servers(self):
        """Register default MCP servers"""
        # Solana/DeFi tools
        self._register_tool(MCPTool(
            name="solana_get_token_info",
            description="Get Solana token info: price, market cap, liquidity, holders",
            server="solana",
            parameters={"token_address": "string", "include_holders": "bool"},
        ))
        self._register_tool(MCPTool(
            name="solana_check_rug",
            description="Check if Solana token is a rug pull risk",
            server="solana",
            parameters={"token_address": "string"},
        ))
        self._register_tool(MCPTool(
            name="solana_get_new_tokens",
            description="Get newly launched Solana tokens from Raydium/Pump.fun",
            server="solana",
            parameters={"limit": "int", "min_liquidity": "float"},
        ))
        self._register_tool(MCPTool(
            name="solana_wallet_balance",
            description="Get SOL and token balances for a wallet",
            server="solana",
            parameters={"wallet_address": "string"},
        ))
        self._register_tool(MCPTool(
            name="solana_swap_quote",
            description="Get swap quote from Jupiter aggregator",
            server="solana",
            parameters={"input_mint": "string", "output_mint": "string", "amount": "float"},
        ))

        # Market data tools
        self._register_tool(MCPTool(
            name="market_get_price",
            description="Get current crypto price from multiple sources",
            server="market",
            parameters={"symbol": "string", "currency": "string"},
        ))
        self._register_tool(MCPTool(
            name="market_get_trending",
            description="Get trending tokens on DEX by volume/momentum",
            server="market",
            parameters={"chain": "string", "timeframe": "string", "limit": "int"},
        ))
        self._register_tool(MCPTool(
            name="market_get_whale_activity",
            description="Get recent whale wallet transactions",
            server="market",
            parameters={"chain": "string", "min_value_usd": "float"},
        ))

        # File system tools
        self._register_tool(MCPTool(
            name="fs_read_file",
            description="Read a project file",
            server="filesystem",
            parameters={"path": "string"},
        ))
        self._register_tool(MCPTool(
            name="fs_write_file",
            description="Write/update a project file",
            server="filesystem",
            parameters={"path": "string", "content": "string"},
        ))
        self._register_tool(MCPTool(
            name="fs_list_project",
            description="List all files in a project directory",
            server="filesystem",
            parameters={"project_id": "string"},
        ))
        self._register_tool(MCPTool(
            name="fs_run_script",
            description="Execute a Python script from a project",
            server="filesystem",
            parameters={"project_id": "string", "script": "string"},
        ))

        # Memory tools
        self._register_tool(MCPTool(
            name="memory_search",
            description="Search AgentJW memory for relevant information",
            server="memory",
            parameters={"query": "string", "type": "string", "limit": "int"},
        ))
        self._register_tool(MCPTool(
            name="memory_store",
            description="Store important information in AgentJW memory",
            server="memory",
            parameters={"content": "string", "type": "string", "importance": "float"},
        ))
        self._register_tool(MCPTool(
            name="memory_get_project",
            description="Get full project details from memory",
            server="memory",
            parameters={"project_id": "string"},
        ))

        # Code tools
        self._register_tool(MCPTool(
            name="code_validate",
            description="Validate Python code syntax and imports",
            server="code",
            parameters={"code": "string"},
        ))
        self._register_tool(MCPTool(
            name="code_fix",
            description="Auto-fix Python code errors",
            server="code",
            parameters={"code": "string", "error": "string"},
        ))
        self._register_tool(MCPTool(
            name="code_explain",
            description="Explain what a piece of code does",
            server="code",
            parameters={"code": "string"},
        ))

        logger.info(f"MCP Client: {len(self.tools)} tools registered")

    def _register_tool(self, tool: MCPTool):
        self.tools[tool.name] = tool

    def register_external_server(self, name: str, url: str, api_key: str = ""):
        """Register an external MCP server (e.g. Gusmcp)"""
        self.servers[name] = {"url": url, "api_key": api_key, "status": "registered"}
        console.print(f"[agent.memory]🔌 MCP Server registered: {name} → {url}[/agent.memory]")

    def get_tools_for_agent(self, category: str = None) -> List[Dict]:
        """Get tools formatted for LLM function calling"""
        tools = list(self.tools.values())
        if category:
            tools = [t for t in tools if t.server == category or category in t.name]
        return [t.to_dict() for t in tools]

    def execute(self, intent: Dict, user_request: str) -> Dict:
        """Execute MCP tool based on AI-selected tool"""
        tool_name = intent.get("tool_name", "")
        params = intent.get("parameters", {})

        if tool_name and tool_name in self.tools:
            return self._execute_tool(tool_name, params)

        # Let AI select the right tool
        selected = self._ai_select_tool(user_request)
        if selected:
            return self._execute_tool(selected["tool"], selected["params"])

        return {"status": "no_tool_found", "request": user_request}

    def _ai_select_tool(self, user_request: str) -> Optional[Dict]:
        """Use AI to select the right MCP tool"""
        tools_desc = "\n".join(
            f"- {t.name}: {t.description}" for t in self.tools.values()
        )
        prompt = f"""Select the best MCP tool for this request:

REQUEST: {user_request}

AVAILABLE TOOLS:
{tools_desc}

Respond ONLY with JSON:
{{"tool": "tool_name", "params": {{"param": "value"}}, "reason": "why"}}"""

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system="You are a tool selector. Pick the most appropriate tool.",
                temperature=0.1,
                max_tokens=300,
                json_mode=True,
            )
            return json.loads(response)
        except Exception:
            return None

    def _execute_tool(self, tool_name: str, params: Dict) -> Dict:
        """Execute a specific tool"""
        tool = self.tools.get(tool_name)
        if not tool:
            return {"status": "error", "message": f"Tool not found: {tool_name}"}

        console.print(f"[agent.memory]🔧 MCP Tool: {tool_name}[/agent.memory]")

        # Route to server handler
        handler = getattr(self, f"_handle_{tool.server}", None)
        if handler:
            return handler(tool_name, params)

        # Try external server
        if tool.server in self.servers:
            return self._call_external_server(tool.server, tool_name, params)

        return {"status": "not_implemented", "tool": tool_name}

    def _handle_filesystem(self, tool_name: str, params: Dict) -> Dict:
        """Handle filesystem MCP tools"""
        from pathlib import Path

        if tool_name == "fs_read_file":
            try:
                content = Path(params["path"]).read_text()
                return {"status": "ok", "content": content}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        elif tool_name == "fs_write_file":
            try:
                p = Path(params["path"])
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(params["content"])
                return {"status": "ok", "path": str(p)}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        elif tool_name == "fs_list_project":
            from memory.memory_store import memory_store
            proj = memory_store.get_project(params.get("project_id", ""))
            if not proj:
                return {"status": "error", "message": "Project not found"}
            files = list(Path(proj["project_dir"]).rglob("*.py"))
            return {"status": "ok", "files": [str(f.name) for f in files]}

        elif tool_name == "fs_run_script":
            from agents.workflow.agent_runner import agent_runner
            from memory.memory_store import memory_store
            proj = memory_store.get_project(params.get("project_id", ""))
            if proj:
                result = agent_runner.run(proj["project_dir"], mode="test")
                return {"status": "ok" if result.success else "error",
                        "stdout": result.stdout, "stderr": result.stderr}
            return {"status": "error", "message": "Project not found"}

        return {"status": "not_implemented"}

    def _handle_memory(self, tool_name: str, params: Dict) -> Dict:
        """Handle memory MCP tools"""
        from memory.memory_store import memory_store

        if tool_name == "memory_search":
            results = memory_store.search_memories(
                params.get("query", ""),
                type=params.get("type"),
                limit=int(params.get("limit", 5)),
            )
            return {"status": "ok", "results": results}

        elif tool_name == "memory_store":
            mid = memory_store.store(
                type=params.get("type", "fact"),
                content=params.get("content", ""),
                importance=float(params.get("importance", 1.0)),
            )
            return {"status": "ok", "id": mid}

        elif tool_name == "memory_get_project":
            proj = memory_store.get_project(params.get("project_id", ""))
            return {"status": "ok", "project": proj} if proj else {"status": "not_found"}

        return {"status": "not_implemented"}

    def _handle_code(self, tool_name: str, params: Dict) -> Dict:
        """Handle code MCP tools"""
        from runtime.ast_validator import ast_validator

        if tool_name == "code_validate":
            valid, errors = ast_validator.validate_python(params.get("code", ""))
            return {"status": "ok", "valid": valid, "errors": errors}

        elif tool_name == "code_fix":
            import re
            code = params.get("code", "")
            error = params.get("error", "")
            prompt = f"Fix this Python code:\nERROR: {error}\nCODE:\n{code}\nOutput ONLY fixed code."
            try:
                fixed = self.llm.chat(
                    messages=[{"role": "user", "content": prompt}],
                    system="Expert Python debugger.",
                    temperature=0.1, max_tokens=4096,
                )
                fixed = re.sub(r'<think>.*?</think>', '', fixed, flags=re.DOTALL)
                fixed = re.sub(r'^```(?:python|py)?\n?', '', fixed, flags=re.MULTILINE)
                fixed = re.sub(r'\n?```$', '', fixed, flags=re.MULTILINE)
                return {"status": "ok", "fixed_code": fixed.strip()}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        elif tool_name == "code_explain":
            try:
                explanation = self.llm.chat(
                    messages=[{"role": "user", "content": f"Explain this code:\n{params.get('code','')}"}],
                    temperature=0.3, max_tokens=1000,
                )
                return {"status": "ok", "explanation": explanation}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "not_implemented"}

    def _handle_solana(self, tool_name: str, params: Dict) -> Dict:
        """Handle Solana MCP tools via REST APIs"""
        import requests

        if tool_name == "solana_get_token_info":
            addr = params.get("token_address", "")
            try:
                # DexScreener API
                r = requests.get(
                    f"https://api.dexscreener.com/latest/dex/tokens/{addr}",
                    timeout=10,
                )
                if r.status_code == 200:
                    data = r.json()
                    pairs = data.get("pairs", [])
                    if pairs:
                        p = pairs[0]
                        return {
                            "status": "ok",
                            "symbol": p.get("baseToken", {}).get("symbol"),
                            "price_usd": p.get("priceUsd"),
                            "market_cap": p.get("marketCap"),
                            "volume_24h": p.get("volume", {}).get("h24"),
                            "liquidity": p.get("liquidity", {}).get("usd"),
                            "price_change_5m": p.get("priceChange", {}).get("m5"),
                            "price_change_1h": p.get("priceChange", {}).get("h1"),
                            "dex": p.get("dexId"),
                        }
            except Exception as e:
                return {"status": "error", "message": str(e)}

        elif tool_name == "solana_get_new_tokens":
            try:
                # Pump.fun new tokens
                r = requests.get(
                    "https://frontend-api.pump.fun/coins?offset=0&limit=20&sort=created_timestamp&order=DESC&includeNsfw=false",
                    timeout=10,
                )
                if r.status_code == 200:
                    tokens = r.json()[:params.get("limit", 10)]
                    return {"status": "ok", "tokens": tokens}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        elif tool_name == "market_get_trending":
            try:
                chain = params.get("chain", "solana")
                r = requests.get(
                    f"https://api.dexscreener.com/latest/dex/search?q={chain}",
                    timeout=10,
                )
                if r.status_code == 200:
                    pairs = r.json().get("pairs", [])[:params.get("limit", 10)]
                    return {"status": "ok", "pairs": pairs}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        return {"status": "api_not_configured", "tool": tool_name}

    def _handle_market(self, tool_name: str, params: Dict) -> Dict:
        return self._handle_solana(tool_name, params)

    def _call_external_server(self, server_name: str, tool_name: str, params: Dict) -> Dict:
        """Call external MCP server (Gusmcp etc)"""
        server = self.servers.get(server_name, {})
        url = server.get("url", "")
        if not url:
            return {"status": "error", "message": f"Server {server_name} not configured"}

        import requests
        try:
            r = requests.post(
                f"{url}/tools/{tool_name}",
                json={"parameters": params},
                headers={"Authorization": f"Bearer {server.get('api_key','')}"},
                timeout=30,
            )
            return r.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def display_tools(self, server: str = None):
        """Display available MCP tools"""
        tools = [t for t in self.tools.values() if not server or t.server == server]
        table = Table(title="🔧 MCP Tools", border_style="cyan")
        table.add_column("Tool", style="green", width=30)
        table.add_column("Server", style="cyan", width=12)
        table.add_column("Description", style="white")
        for t in tools:
            table.add_row(t.name, t.server, t.description[:60])
        console.print(table)

    def display_servers(self):
        """Display registered external servers"""
        if not self.servers:
            console.print("[dim]No external MCP servers registered[/dim]")
            return
        table = Table(title="🌐 MCP Servers", border_style="cyan")
        table.add_column("Name", style="cyan")
        table.add_column("URL", style="white")
        table.add_column("Status", style="green")
        for name, info in self.servers.items():
            table.add_row(name, info["url"], info["status"])
        console.print(table)


mcp_client = MCPClient()
