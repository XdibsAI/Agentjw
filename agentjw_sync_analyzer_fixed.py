#!/usr/bin/env python3
"""
agentjw_sync_analyzer.py
========================
Analisa LENGKAP dan AUTO-PATCH AgentJW:

1. Port mismatch (api_server, APK config, .env)
2. Endpoint mismatch (route di api_server vs yang dipanggil APK/CLI)
3. Brain/Intent mismatch (intent type vs handler yang tersedia)
4. Tool registry (semua tools yang ada vs yang diketahui Brain)
5. AI model mismatch (config LLM vs yang benar-benar dipakai router)
6. ENV mismatch (vars di kode vs yang ada di .env)
7. Import chain (circular, missing modules)
8. Orchestrator completeness (semua intent punya handler?)
9. Workflow sync (brain -> orchestrator -> tool -> project)
10. Auto-patch semua yang bisa diperbaiki otomatis
11. Simpan catatan harian ke logs/sync_report_YYYYMMDD.md

Jalankan: python3 agentjw_sync_analyzer.py [--patch] [--full]
"""

import os
import re
import sys
import ast
import json
import shutil
import hashlib
import subprocess
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field

ROOT = Path.home() / "agentjw"
REPORT_DIR = ROOT / "logs"
NOW = datetime.now()
REPORT_FILE = REPORT_DIR / f"sync_report_{NOW.strftime('%Y%m%d_%H%M%S')}.md"
DAILY_LOG = REPORT_DIR / f"daily_{NOW.strftime('%Y%m%d')}.md"

AUTO_PATCH = "--patch" in sys.argv or "--auto" in sys.argv
FULL_SCAN = "--full" in sys.argv

# ─── COLORS (rich if available, else plain) ───────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import print as rprint
    console = Console()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    class Console:
        def print(self, *a, **kw): print(*a)
    console = Console()

def h1(s): console.print(f"\n[bold cyan]{'═'*60}[/bold cyan]\n[bold cyan]{s}[/bold cyan]") if HAS_RICH else print(f"\n{'='*60}\n{s}")
def h2(s): console.print(f"\n[bold yellow]▶ {s}[/bold yellow]") if HAS_RICH else print(f"\n▶ {s}")
def ok(s): console.print(f"  [green]✅ {s}[/green]") if HAS_RICH else print(f"  ✅ {s}")
def warn(s): console.print(f"  [yellow]⚠️  {s}[/yellow]") if HAS_RICH else print(f"  ⚠️  {s}")
def err(s): console.print(f"  [red]❌ {s}[/red]") if HAS_RICH else print(f"  ❌ {s}")
def info(s): console.print(f"  [dim]{s}[/dim]") if HAS_RICH else print(f"     {s}")
def patch_msg(s): console.print(f"  [magenta]🔧 PATCH: {s}[/magenta]") if HAS_RICH else print(f"  🔧 PATCH: {s}")


# ─── DATA STRUCTURES ──────────────────────────────────────────────────────────

@dataclass
class Issue:
    category: str
    severity: str  # CRITICAL / WARNING / INFO
    description: str
    file: str = ""
    line: int = 0
    fix: str = ""
    auto_fixable: bool = False
    patch_applied: bool = False

@dataclass
class SyncReport:
    timestamp: str = ""
    issues: List[Issue] = field(default_factory=list)
    tools_found: List[str] = field(default_factory=list)
    tools_registered: List[str] = field(default_factory=list)
    intents_defined: List[str] = field(default_factory=list)
    intents_handled: List[str] = field(default_factory=list)
    endpoints: Dict[str, str] = field(default_factory=dict)
    env_status: Dict[str, str] = field(default_factory=dict)
    patches_applied: int = 0
    score: int = 100

    def add(self, issue: Issue):
        self.issues.append(issue)
        if issue.severity == "CRITICAL":
            self.score -= 15
        elif issue.severity == "WARNING":
            self.score -= 5
        self.score = max(0, self.score)


report = SyncReport(timestamp=NOW.isoformat())


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

def find_all_py(directory: Path) -> List[Path]:
    return [p for p in directory.rglob("*.py")
            if "__pycache__" not in str(p) and ".git" not in str(p)]

def parse_ast_safe(path: Path):
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError as e:
        report.add(Issue("SYNTAX", "CRITICAL", f"SyntaxError in {path.name}: {e}",
                         str(path), e.lineno or 0))
        return None

def run_cmd(cmd: str, cwd: Path = ROOT) -> Tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          timeout=15, cwd=str(cwd))
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)

def backup(path: Path):
    dest = path.parent / f"{path.name}.sync_bak_{NOW.strftime('%H%M%S')}"
    shutil.copy2(path, dest)
    return dest


# ═══════════════════════════════════════════════════════════════════════════════
# 1. PORT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_ports():
    h2("1. PORT ANALYSIS")

    ports_found = {}

    # api_server.py
    api_path = ROOT / "api_server.py"
    if api_path.exists():
        content = read_file(api_path)
        for m in re.finditer(r'port[=:\s]+(\d{4,5})', content, re.IGNORECASE):
            ports_found[f"api_server.py:{m.start()}"] = int(m.group(1))
        # Check uvicorn run line
        for line in content.splitlines():
            if "uvicorn" in line.lower() and "port" in line.lower():
                m = re.search(r'--port\s+(\d+)', line)
                if m:
                    ports_found[f"api_server comment"] = int(m.group(1))

    # .env
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in read_file(env_path).splitlines():
            if "PORT" in line.upper() and "=" in line:
                k, _, v = line.partition("=")
                try:
                    ports_found[f".env:{k.strip()}"] = int(v.strip())
                except ValueError:
                    pass

    # core/config.py
    cfg_path = ROOT / "core" / "config.py"
    if cfg_path.exists():
        content = read_file(cfg_path)
        for m in re.finditer(r'PORT.*?=.*?(\d{4,5})', content, re.IGNORECASE):
            ports_found[f"core/config.py"] = int(m.group(1))

    # Check actual listening ports
    _, listening, _ = run_cmd("ss -ltnp | grep python")
    actual_ports = set()
    for m in re.finditer(r':(\d{4,5})\s', listening):
        actual_ports.add(int(m.group(1)))

    # APK target (from README or known config)
    apk_port = 18790  # Known from APK

    info(f"APK target port: {apk_port}")
    info(f"Ports in code: {ports_found}")
    info(f"Actually listening: {actual_ports}")

    if apk_port in actual_ports:
        ok(f"API server listening on correct port {apk_port}")
    else:
        issue_desc = f"API server NOT listening on port {apk_port} (APK target)"
        fix_cmd = f"nohup uvicorn api_server:app --host 0.0.0.0 --port {apk_port} > api.log 2>&1 &"
        report.add(Issue("PORT", "CRITICAL", issue_desc, "api_server.py",
                         fix=fix_cmd, auto_fixable=False))
        err(issue_desc)
        info(f"Fix: {fix_cmd}")

    # Check for port 8000 hardcode conflict
    api_content = read_file(api_path)
    if "8000" in api_content and "18790" not in api_content:
        report.add(Issue("PORT", "WARNING",
                         "api_server.py may hardcode port 8000, not 18790",
                         "api_server.py",
                         fix="Add PORT env var or set uvicorn port=18790",
                         auto_fixable=True))
        warn("Port 8000 found in api_server.py without 18790 override")


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ENDPOINT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_endpoints():
    h2("2. ENDPOINT ANALYSIS")

    api_path = ROOT / "api_server.py"
    if not api_path.exists():
        err("api_server.py not found!")
        return

    content = read_file(api_path)

    # Find all defined routes
    defined_routes = {}
    for m in re.finditer(r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content):
        method = m.group(1).upper()
        path = m.group(2)
        defined_routes[path] = method
        report.endpoints[path] = method

    info(f"Defined endpoints: {list(defined_routes.keys())}")

    # Required endpoints (from APK usage patterns)
    required_endpoints = {
        "/api/agent": "POST",
        "/api/status": "GET",
        "/api/projects": "GET",
        "/api/logs": "GET",
        "/health": "GET",
    }

    for endpoint, method in required_endpoints.items():
        if endpoint in defined_routes:
            if defined_routes[endpoint] == method:
                ok(f"{method} {endpoint}")
            else:
                warn(f"{endpoint} exists but method is {defined_routes[endpoint]}, expected {method}")
        else:
            report.add(Issue("ENDPOINT", "CRITICAL",
                             f"Missing endpoint: {method} {endpoint}",
                             "api_server.py",
                             fix=f"Add @app.{method.lower()}('{endpoint}') handler",
                             auto_fixable=True))
            err(f"Missing: {method} {endpoint}")

    # Check /api/agent request/response schema
    agent_schema_ok = True
    if '"response"' not in content and "'response'" not in content:
        agent_schema_ok = False
        report.add(Issue("ENDPOINT", "WARNING",
                         "/api/agent response missing 'response' field",
                         "api_server.py",
                         fix="Ensure response dict has 'response' key"))

    if '"session_id"' not in content and "'session_id'" not in content:
        report.add(Issue("ENDPOINT", "WARNING",
                         "/api/agent response missing 'session_id' field",
                         "api_server.py"))

    # Check CORS
    if "CORSMiddleware" in content:
        ok("CORS middleware configured")
    else:
        report.add(Issue("ENDPOINT", "WARNING",
                         "No CORS middleware — APK may get blocked",
                         "api_server.py",
                         fix="Add app.add_middleware(CORSMiddleware, allow_origins=['*'])",
                         auto_fixable=True))
        warn("No CORS middleware found")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. BRAIN / INTENT ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_brain_intent():
    h2("3. BRAIN / INTENT SYNC ANALYSIS")

    brain_path = ROOT / "agents" / "brain.py"
    orch_path = ROOT / "agents" / "orchestrator.py"

    # Get intents from brain.py
    brain_intents = set()
    if brain_path.exists():
        content = read_file(brain_path)
        # Only look for decide()/route()-style return values, e.g. return "video"
        # or return {"type": "video", ...}. The old regex matched ANY
        # quoted lowercase string in the file (docstrings, log messages,
        # dict keys, etc.) producing huge amounts of noise/false positives.
        for m in re.finditer(r'return\s+["\']([a-z_]{2,30})["\']', content):
            brain_intents.add(m.group(1))
        for m in re.finditer(r'["\']type["\']\s*:\s*["\']([a-z_]{2,30})["\']', content):
            brain_intents.add(m.group(1))
        info(f"Brain intents: {sorted(brain_intents)}")
    else:
        warn("brain.py not found — brain is defined elsewhere")

    # Get intents from orchestrator route_intent()
    orch_intents_defined = set()
    orch_handlers = set()
    if orch_path.exists():
        content = read_file(orch_path)
        # Extract intent types from route_intent return statements
        for m in re.finditer(r'"type":\s*"([a-z_]+)"', content):
            orch_intents_defined.add(m.group(1))
        # Extract handler keys from handlers dict
        for m in re.finditer(r'"([a-z_]+)":\s*self\.(_\w+)', content):
            orch_handlers.add(m.group(1))
            report.intents_handled.append(m.group(1))
        info(f"Orchestrator intents defined: {sorted(orch_intents_defined)}")
        info(f"Orchestrator handlers: {sorted(orch_handlers)}")

    report.intents_defined = sorted(orch_intents_defined)

    # Find intents without handlers
    for intent in orch_intents_defined:
        if intent not in orch_handlers and intent != "chat":
            report.add(Issue("BRAIN", "CRITICAL",
                             f"Intent '{intent}' defined but NO handler in orchestrator",
                             "agents/orchestrator.py",
                             fix=f"Add handler for '{intent}' or map to existing handler",
                             auto_fixable=False))
            err(f"Intent '{intent}' has no handler!")
        elif intent != "chat":
            ok(f"Intent '{intent}' → handler exists")

    # Check brain.py "decide" function
    if brain_path.exists():
        content = read_file(brain_path)
        if "def decide" in content:
            ok("brain.decide() function exists")
            # Check if decide returns all orchestrator intents
            for intent in orch_intents_defined:
                if not re.search(r'\b' + re.escape(intent) + r'\b', content) and intent != "chat":
                    report.add(Issue("BRAIN", "WARNING",
                                     f"Orchestrator intent '{intent}' not in brain.decide()",
                                     "agents/brain.py",
                                     fix=f"Add '{intent}' to brain.decide() routing",
                                     auto_fixable=True))
                    warn(f"brain.decide() missing intent: '{intent}'")
        else:
            report.add(Issue("BRAIN", "CRITICAL",
                             "brain.py missing decide() function",
                             "agents/brain.py",
                             fix="Add def decide(user_input) function",
                             auto_fixable=True))
            err("brain.py missing decide() function!")

    # Check API server uses brain or orchestrator
    api_content = read_file(ROOT / "api_server.py")
    if "orchestrator" in api_content or "brain" in api_content:
        ok("api_server.py calls orchestrator/brain")
    else:
        report.add(Issue("BRAIN", "CRITICAL",
                         "api_server.py does not call orchestrator or brain",
                         "api_server.py"))
        err("api_server.py not connected to brain/orchestrator!")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TOOLS REGISTRY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_tools():
    h2("4. TOOLS REGISTRY ANALYSIS")

    tools_dir = ROOT / "tools"
    mcp_dir = ROOT / "mcp" / "tools"

    # Discover all tool files
    all_tool_files = []
    for d in [tools_dir, mcp_dir]:
        if d.exists():
            all_tool_files.extend([f for f in d.rglob("*_tool.py")])
            all_tool_files.extend([f for f in d.rglob("*tool*.py")])

    tool_classes = {}
    tool_instances = {}
    tool_methods = {}

    for tf in set(all_tool_files):
        if "__pycache__" in str(tf):
            continue
        content = read_file(tf)
        rel = str(tf.relative_to(ROOT))

        # Find class definitions
        for m in re.finditer(r'^class\s+(\w+)', content, re.MULTILINE):
            cls = m.group(1)
            if "Tool" in cls or "tool" in cls.lower():
                tool_classes[cls] = rel

        # Find singleton instances — only count assignments that instantiate
        # something whose class name looks like a tool (e.g. `video_tool =
        # VideoTool(...)`). The previous regex matched ANY top-level
        # lowercase assignment (constants, configs, helper objects, etc.)
        # and reported them all as "tools", causing massive false positives.
        for m in re.finditer(r'^(\w+)\s*=\s*(\w*[Tt]ool\w*)\s*\(', content, re.MULTILINE):
            inst = m.group(1)
            if not inst.startswith("_"):
                tool_instances[inst] = rel

        # Find public methods
        methods = []
        for m in re.finditer(r'^\s+def\s+([a-z]\w+)\(', content, re.MULTILINE):
            methods.append(m.group(1))
        if methods:
            tool_methods[rel] = methods

        report.tools_found.append(rel)
        ok(f"Tool: {rel} ({len(methods)} methods)")

    # Check if orchestrator knows all tools
    orch_content = read_file(ROOT / "agents" / "orchestrator.py")
    for tool_name, tool_file in tool_instances.items():
        if tool_name in orch_content:
            ok(f"Orchestrator knows: {tool_name}")
            report.tools_registered.append(tool_name)
        else:
            report.add(Issue("TOOLS", "WARNING",
                             f"Tool '{tool_name}' ({tool_file}) not used in orchestrator",
                             "agents/orchestrator.py",
                             fix=f"Import and use {tool_name} in relevant handler",
                             auto_fixable=False))
            warn(f"Tool '{tool_name}' not referenced in orchestrator")

    # Check brain/chat system prompt mentions tools
    chat_system = ""
    for m in re.finditer(r'system\s*=\s*f?"""(.*?)"""', orch_content, re.DOTALL):
        chat_system += m.group(1)

    missing_from_prompt = []
    for tool_name in report.tools_registered:
        if tool_name not in chat_system:
            missing_from_prompt.append(tool_name)

    if missing_from_prompt:
        report.add(Issue("TOOLS", "WARNING",
                         f"Tools not mentioned in AI system prompt: {missing_from_prompt}",
                         "agents/orchestrator.py",
                         fix="Add tool descriptions to chat() system prompt",
                         auto_fixable=True))
        warn(f"Tools not in AI prompt: {missing_from_prompt}")

    return tool_instances, tool_methods


# ═══════════════════════════════════════════════════════════════════════════════
# 5. AI / LLM MODEL MISMATCH
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_ai_models():
    h2("5. AI / LLM MODEL MISMATCH")

    # Read .env
    env_path = ROOT / ".env"
    env_vars = {}
    if env_path.exists():
        for line in read_file(env_path).splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                env_vars[k.strip()] = v.strip()

    # Read config
    cfg_content = read_file(ROOT / "core" / "config.py")

    # Read router if exists
    router_path = ROOT / "core" / "router.py"
    router_content = read_file(router_path) if router_path.exists() else ""

    # Models mentioned across codebase
    models_found = {}
    model_pattern = re.compile(
        r'(gpt-[\w.-]+|claude-[\w.-]+|qwen[\w/.-]*|mistral[\w/.-]*|llama[\w/.-]*|'
        r'gemini[\w/.-]*|deepseek[\w/.-]*|grok[\w/.-]*|'
        r'openai/[\w.-]+|anthropic/[\w.-]+|google/[\w.-]+|deepseek/[\w.-]+|x-ai/[\w.-]+)'
    )

    for py_file in find_all_py(ROOT / "core") + find_all_py(ROOT / "agents"):
        content = read_file(py_file)
        for m in model_pattern.finditer(content):
            model = m.group(1)
            rel = str(py_file.relative_to(ROOT))
            models_found.setdefault(model, []).append(rel)

    info(f"Models found in code: {list(models_found.keys())}")

    # Check .env model settings
    llm_provider = env_vars.get("LLM_PROVIDER", "openai")
    openai_model = env_vars.get("OPENAI_MODEL", "gpt-4o")
    openrouter_key = env_vars.get("OPENROUTER_API_KEY", "")
    openai_key = env_vars.get("OPENAI_API_KEY", "")

    info(f"LLM_PROVIDER in .env: {llm_provider}")
    info(f"OPENAI_MODEL in .env: {openai_model}")
    info(f"OPENROUTER_API_KEY: {'set' if openrouter_key else 'NOT SET'}")
    info(f"OPENAI_API_KEY: {'set' if openai_key else 'NOT SET'}")

    # Check if using OpenRouter but key missing
    api_content = read_file(ROOT / "api_server.py")
    if "openrouter" in api_content.lower() or "openrouter" in cfg_content.lower():
        if not openrouter_key:
            report.add(Issue("AI_MODEL", "CRITICAL",
                             "Code uses OpenRouter but OPENROUTER_API_KEY not set in .env",
                             ".env",
                             fix="Add OPENROUTER_API_KEY=sk-or-... to .env",
                             auto_fixable=False))
            err("OPENROUTER_API_KEY missing but OpenRouter is used!")
        else:
            ok("OPENROUTER_API_KEY is set")

    # Check router.py for model selection logic
    if router_path.exists():
        if "gpt-5-mini" in router_content or "gpt-4o-mini" in router_content:
            warn("Router uses cheap model (gpt-5-mini/gpt-4o-mini) for complex tasks")
            report.add(Issue("AI_MODEL", "WARNING",
                             "Router may downgrade to gpt-5-mini for complex tasks",
                             "core/router.py",
                             fix="Review router model selection thresholds"))

    # Check if brain uses same model as chat
    brain_content = read_file(ROOT / "agents" / "brain.py")
    if "router" in brain_content.lower():
        ok("Brain uses router for model selection")
    else:
        info("Brain may not use router (may have hardcoded model)")

    # Check qwen model in session (from CLI output we saw qwen/qwen3-coder)
    if "qwen" in str(models_found) or "qwen" in cfg_content:
        ok("Qwen model configured (via OpenRouter)")
    elif not openai_key and not openrouter_key:
        report.add(Issue("AI_MODEL", "CRITICAL",
                         "No LLM API key configured — AI will not work",
                         ".env",
                         fix="Set OPENAI_API_KEY or OPENROUTER_API_KEY in .env"))
        err("No LLM API key found!")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. ENV VARIABLE COMPLETENESS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_env():
    h2("6. ENV VARIABLE COMPLETENESS")

    env_path = ROOT / ".env"
    existing_env = {}
    if env_path.exists():
        for line in read_file(env_path).splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                existing_env[k.strip()] = v.strip()
    else:
        report.add(Issue("ENV", "CRITICAL", "Root .env file missing!", ".env",
                         fix="Create .env from .env.example", auto_fixable=True))
        err("Root .env not found!")
        return

    # Scan all Python files in core, agents, interface
    required_vars = set()
    var_locations = {}
    pattern = re.compile(r'os\.getenv\(["\']([A-Z_][A-Z0-9_]*)["\']')
    for py_file in find_all_py(ROOT / "core") + find_all_py(ROOT / "agents") + [ROOT / "api_server.py"]:
        content = read_file(py_file)
        for m in pattern.finditer(content):
            var = m.group(1)
            required_vars.add(var)
            var_locations.setdefault(var, []).append(py_file.name)

    report.env_status["total_required"] = str(len(required_vars))
    report.env_status["total_set"] = str(len(existing_env))

    missing = []
    empty = []
    for var in sorted(required_vars):
        val = existing_env.get(var, None)
        if val is None:
            missing.append(var)
        elif not val or val in ("", "your_key_here", "xxx", "CHANGE_ME", "???"):
            empty.append(var)

    if missing:
        for v in missing:
            locs = var_locations.get(v, [])
            report.add(Issue("ENV", "WARNING",
                             f"Missing from .env: {v} (used in: {', '.join(locs[:2])})",
                             ".env",
                             fix=f"Add {v}=<value> to .env"))
        warn(f"{len(missing)} vars missing from .env: {missing}")
    if empty:
        warn(f"{len(empty)} vars empty in .env: {empty}")
    if not missing and not empty:
        ok("All required env vars set in root .env")

    # Per-project env check
    h2("  Per-Project .env Status")
    projects_dir = ROOT / "projects"
    if projects_dir.exists():
        for proj_dir in sorted(projects_dir.iterdir()):
            if not proj_dir.is_dir():
                continue
            proj_env = proj_dir / ".env"
            py_files = list(proj_dir.rglob("*.py"))
            proj_vars = set()
            for pf in py_files:
                for m in pattern.finditer(read_file(pf)):
                    proj_vars.add(m.group(1))

            proj_existing = {}
            if proj_env.exists():
                for line in read_file(proj_env).splitlines():
                    if "=" in line and not line.strip().startswith("#"):
                        k, _, v = line.partition("=")
                        proj_existing[k.strip()] = v.strip()

            proj_missing = [v for v in proj_vars if not proj_existing.get(v)]
            if proj_missing:
                warn(f"{proj_dir.name}: missing {len(proj_missing)} vars: {proj_missing[:4]}")
                report.add(Issue("ENV", "WARNING",
                                 f"Project {proj_dir.name} missing env vars: {proj_missing[:4]}",
                                 str(proj_env)))
            else:
                ok(f"{proj_dir.name}: .env complete ({len(proj_vars)} vars)")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. IMPORT CHAIN ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_imports():
    h2("7. IMPORT CHAIN ANALYSIS")

    critical_files = [
        ROOT / "api_server.py",
        ROOT / "agents" / "orchestrator.py",
        ROOT / "agents" / "brain.py",
        ROOT / "core" / "llm_client.py",
        ROOT / "core" / "config.py",
        ROOT / "mcp" / "tools" / "filesystem_tool.py",
        ROOT / "tools" / "env_manager.py",
    ]

    for fpath in critical_files:
        if not fpath.exists():
            report.add(Issue("IMPORT", "CRITICAL",
                             f"Critical file missing: {fpath.name}",
                             str(fpath),
                             auto_fixable=False))
            err(f"MISSING: {fpath.relative_to(ROOT)}")
            continue

        # Try py_compile
        rc, _, stderr = run_cmd(f"python3 -m py_compile {fpath}")
        if rc != 0:
            report.add(Issue("IMPORT", "CRITICAL",
                             f"Syntax error in {fpath.name}: {stderr[:100]}",
                             str(fpath)))
            err(f"Syntax error: {fpath.relative_to(ROOT)}")
            info(stderr[:100])
        else:
            ok(f"Syntax OK: {fpath.relative_to(ROOT)}")

    # Check circular imports (simple heuristic)
    h2("  Checking for circular imports")
    import_graph = {}
    for py_file in find_all_py(ROOT / "agents") + find_all_py(ROOT / "core"):
        content = read_file(py_file)
        imports = re.findall(r'from\s+([\w.]+)\s+import|import\s+([\w.]+)', content)
        rel = str(py_file.relative_to(ROOT)).replace("/", ".").replace(".py", "")
        local_imports = []
        for imp in imports:
            mod = imp[0] or imp[1]
            if mod.startswith(("agents.", "core.", "tools.", "mcp.", "memory.", "interface.")):
                local_imports.append(mod)
        import_graph[rel] = local_imports

    # Simple cycle detection
    def has_cycle(node, graph, visited=None, path=None):
        if visited is None: visited = set()
        if path is None: path = []
        visited.add(node)
        path.append(node)
        for neighbor in graph.get(node, []):
            neighbor_mod = neighbor.replace(".", "/")
            if neighbor_mod in graph:
                if neighbor_mod not in visited:
                    if has_cycle(neighbor_mod, graph, visited, path):
                        return True
                elif neighbor_mod in path:
                    return True
        path.pop()
        return False

    cycles_found = 0
    for node in import_graph:
        if has_cycle(node, import_graph):
            cycles_found += 1

    if cycles_found == 0:
        ok("No obvious circular imports detected")
    else:
        report.add(Issue("IMPORT", "WARNING",
                         f"Potential circular imports detected ({cycles_found} nodes)",
                         "agents/",
                         fix="Use lazy imports (import inside functions) to break cycles"))
        warn(f"Potential circular imports in {cycles_found} modules")


# ═══════════════════════════════════════════════════════════════════════════════
# 8. ORCHESTRATOR COMPLETENESS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_orchestrator():
    h2("8. ORCHESTRATOR COMPLETENESS")

    orch_path = ROOT / "agents" / "orchestrator.py"
    if not orch_path.exists():
        err("orchestrator.py not found!")
        return

    content = read_file(orch_path)

    # Required methods
    required_methods = [
        "route_intent", "smart_build", "chat",
        "_build_trading", "_build_youtube", "_general_build",
        "_repair_existing", "_inspect_action", "_run_project",
        "_post_build_env_check", "_handle_env_paste",
        "_find_project_ref",
    ]

    for method in required_methods:
        if f"def {method}" in content:
            ok(f"Has method: {method}()")
        else:
            report.add(Issue("ORCHESTRATOR", "WARNING",
                             f"Missing method: {method}()",
                             "agents/orchestrator.py",
                             fix=f"Add def {method}() to OrchestratorAgent",
                             auto_fixable=False))
            warn(f"Missing: {method}()")

    # Check video studio integration
    if "video_studio_tool" in content or "VideoStudio" in content:
        ok("Video studio tool referenced")
    else:
        report.add(Issue("ORCHESTRATOR", "WARNING",
                         "Video studio tool not in orchestrator",
                         "agents/orchestrator.py",
                         fix="Add video_build intent and handler for video studio"))
        warn("Video studio not integrated in orchestrator")

    # Check MCP tools registered
    mcp_path = ROOT / "mcp" / "tools"
    if mcp_path.exists():
        mcp_tools = list(mcp_path.glob("*_tool.py"))
        for mt in mcp_tools:
            tool_name = mt.stem
            if tool_name in content:
                ok(f"MCP tool '{tool_name}' used in orchestrator")
            else:
                warn(f"MCP tool '{tool_name}' not referenced in orchestrator")

    # Check workflow engine integration
    workflow_path = ROOT / "agents" / "workflow" / "workflow_engine.py"
    if workflow_path.exists():
        if "workflow_engine" in content or "WorkflowEngine" in content:
            ok("WorkflowEngine integrated in orchestrator")
        else:
            report.add(Issue("ORCHESTRATOR", "INFO",
                             "WorkflowEngine exists but not used in orchestrator",
                             "agents/orchestrator.py",
                             fix="Consider using workflow_engine for complex multi-step builds"))
            info("WorkflowEngine not integrated (optional)")


# ═══════════════════════════════════════════════════════════════════════════════
# 9. WORKFLOW / AGENT SYNC
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_workflow_sync():
    h2("9. WORKFLOW & AGENT SYNC")

    agents_dir = ROOT / "agents"
    agent_files = {
        "brain.py": "Decision making",
        "orchestrator.py": "Routing & coordination",
        "coder_agent.py": "Code generation",
        "reviewer_agent.py": "Code review",
        "repair_agent.py": "Auto-repair",
        "memory_agent.py": "Memory management",
        "planner_agent.py": "Task planning",
        "critic_agent.py": "Quality critique",
    }

    for fname, role in agent_files.items():
        fpath = agents_dir / fname
        if fpath.exists():
            # Check it has a run() or main method
            content = read_file(fpath)
            has_run = "def run(" in content or "def execute(" in content
            has_instance = re.search(r'^[a-z_]+ = \w+\(', content, re.MULTILINE)
            status = "✅" if (has_run or has_instance) else "⚠️"
            ok(f"{fname} ({role}) — {'callable' if has_run else 'instance only'}")
        else:
            report.add(Issue("WORKFLOW", "WARNING",
                             f"Agent file missing: {fname} ({role})",
                             str(fpath)))
            warn(f"Missing agent: {fname}")

    # Check memory store
    mem_path = ROOT / "memory" / "memory_store.py"
    if mem_path.exists():
        content = read_file(mem_path)
        required_methods = ["save_project", "list_projects", "save_chat",
                            "get_chat_history", "recall"]
        for m in required_methods:
            if f"def {m}" in content:
                ok(f"MemoryStore.{m}() exists")
            else:
                report.add(Issue("WORKFLOW", "WARNING",
                                 f"MemoryStore missing method: {m}()",
                                 "memory/memory_store.py"))
                warn(f"MemoryStore.{m}() missing")


# ═══════════════════════════════════════════════════════════════════════════════
# 10. AUTO-PATCH ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def apply_auto_patches():
    h2("10. AUTO-PATCH ENGINE")

    if not AUTO_PATCH:
        info("Auto-patch skipped. Run with --patch flag to apply patches.")
        fixable = [i for i in report.issues if i.auto_fixable and not i.patch_applied]
        if fixable:
            warn(f"{len(fixable)} auto-fixable issues found. Run: python3 agentjw_sync_analyzer.py --patch")
        return

    patched = 0

    for issue in report.issues:
        if not issue.auto_fixable or issue.patch_applied:
            continue

        # PATCH: Missing /health endpoint
        if issue.category == "ENDPOINT" and "/health" in issue.description:
            api_path = ROOT / "api_server.py"
            content = read_file(api_path)
            if "@app.get('/health')" not in content and '@app.get("/health")' not in content:
                health_endpoint = '''

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat(), "service": "agentjw"}
'''
                # Insert before last line
                backup(api_path)
                content = content.rstrip() + health_endpoint
                api_path.write_text(content)
                issue.patch_applied = True
                patched += 1
                patch_msg("Added /health endpoint to api_server.py")

        # PATCH: Missing CORS middleware
        elif issue.category == "ENDPOINT" and "CORS" in issue.description:
            api_path = ROOT / "api_server.py"
            content = read_file(api_path)
            if "CORSMiddleware" not in content:
                backup(api_path)
                cors_import = "from fastapi.middleware.cors import CORSMiddleware\n"
                cors_setup = '''
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
'''
                if "from fastapi" in content:
                    content = content.replace("from fastapi import", cors_import + "from fastapi import", 1)
                if "app = FastAPI(" in content:
                    idx = content.index("app = FastAPI(")
                    end = content.index("\n", content.index(")", idx)) + 1
                    content = content[:end] + cors_setup + content[end:]
                api_path.write_text(content)
                issue.patch_applied = True
                patched += 1
                patch_msg("Added CORS middleware to api_server.py")

        # PATCH: Missing brain.decide() with all intents
        elif issue.category == "BRAIN" and "brain.decide()" in issue.description:
            brain_path = ROOT / "agents" / "brain.py"
            content = read_file(brain_path)
            if "def decide" not in content:
                backup(brain_path)
                intents = report.intents_defined
                decide_fn = '''

def decide(user_input: str) -> dict:
    """
    Brain decision function — maps user input to orchestrator intent.
    Auto-generated by agentjw_sync_analyzer.
    """
    lower = user_input.lower()

    # Inspect / read files
    if any(k in lower for k in ["scan", "tampilkan", "lihat", "baca", "log", "jalankan", "run"]):
        return {"intent": "inspect", "confidence": 0.95}

    # Repair
    if any(k in lower for k in ["perbaiki", "fix", "repair", "debug", "error", "broken"]):
        return {"intent": "project_repair", "confidence": 0.9}

    # Trading
    if any(k in lower for k in ["trading", "bot trading", "solana", "dex", "sniper", "meme coin"]):
        return {"intent": "trading_build", "confidence": 0.9}

    # YouTube
    if any(k in lower for k in ["youtube", "thumbnail", "upload", "channel"]):
        return {"intent": "youtube_build", "confidence": 0.9}

    # Analysis
    if any(k in lower for k in ["analisa", "analyze", "evaluasi", "review strategi"]):
        return {"intent": "analysis", "confidence": 0.85}

    # Continue project
    if any(k in lower for k in ["lanjutkan", "continue", "resume", "teruskan"]):
        return {"intent": "continue_project", "confidence": 0.85}

    # Modify
    if any(k in lower for k in ["ubah", "modify", "ganti", "update strategi"]):
        return {"intent": "modify_strategy", "confidence": 0.85}

    # MCP tools
    if any(k in lower for k in ["check token", "cek token", "mcp tool"]):
        return {"intent": "mcp_tool", "confidence": 0.85}

    # General build
    if any(k in lower for k in ["buat", "build", "create", "buatkan", "bikin"]):
        return {"intent": "general_build", "confidence": 0.7}

    return {"intent": "chat", "confidence": 1.0}
'''
                content += decide_fn
                brain_path.write_text(content)
                issue.patch_applied = True
                patched += 1
                patch_msg("Added decide() function to brain.py")

        # PATCH: Missing tools in AI system prompt
        elif issue.category == "TOOLS" and "system prompt" in issue.description:
            orch_path = ROOT / "agents" / "orchestrator.py"
            content = read_file(orch_path)
            tools_list = "\n".join(f"  - {t}" for t in report.tools_registered)
            tool_section = f"""
AVAILABLE TOOLS (kamu bisa gunakan semua ini):
{tools_list}
Untuk pakai tool: panggil handler yang sesuai atau gunakan via orchestrator.
"""
            if "AVAILABLE TOOLS" not in content:
                # Find system prompt and inject
                old_system_end = 'RECENT CHAT:\n{chat_ctx}"'
                if old_system_end in content:
                    backup(orch_path)
                    content = content.replace(
                        old_system_end,
                        tool_section + '\nRECENT CHAT:\n{chat_ctx}"'
                    )
                    orch_path.write_text(content)
                    issue.patch_applied = True
                    patched += 1
                    patch_msg("Added tool registry to AI system prompt")

        # PATCH: Root .env missing
        elif issue.category == "ENV" and "Root .env file missing" in issue.description:
            env_example = ROOT / ".env.example"
            env_path = ROOT / ".env"
            if env_example.exists() and not env_path.exists():
                shutil.copy2(env_example, env_path)
                issue.patch_applied = True
                patched += 1
                patch_msg("Created .env from .env.example")

    report.patches_applied = patched
    if patched > 0:
        ok(f"Applied {patched} auto-patches")
    else:
        info("No auto-patches needed or applied")


# ═══════════════════════════════════════════════════════════════════════════════
# 11. DAILY LOG & REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def write_report():
    h2("11. GENERATING REPORT")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    criticals = [i for i in report.issues if i.severity == "CRITICAL"]
    warnings = [i for i in report.issues if i.severity == "WARNING"]
    infos = [i for i in report.issues if i.severity == "INFO"]

    md = f"""# AgentJW Sync Report
**Generated:** {NOW.strftime('%Y-%m-%d %H:%M:%S')}
**Health Score:** {report.score}/100
**Auto-Patches Applied:** {report.patches_applied}

---

## Summary
| Metric | Value |
|--------|-------|
| Critical Issues | {len(criticals)} |
| Warnings | {len(warnings)} |
| Info | {len(infos)} |
| Tools Found | {len(report.tools_found)} |
| Tools in Orchestrator | {len(report.tools_registered)} |
| Intents Defined | {len(report.intents_defined)} |
| Intents Handled | {len(report.intents_handled)} |
| Endpoints | {len(report.endpoints)} |

## Endpoints
"""
    for path, method in sorted(report.endpoints.items()):
        md += f"- `{method} {path}`\n"

    md += "\n## Critical Issues\n"
    for i in criticals:
        md += f"### ❌ [{i.category}] {i.description}\n"
        if i.file:
            md += f"- **File:** `{i.file}`\n"
        if i.fix:
            md += f"- **Fix:** {i.fix}\n"
        if i.patch_applied:
            md += f"- **Status:** ✅ Auto-patched\n"
        md += "\n"

    md += "\n## Warnings\n"
    for i in warnings:
        md += f"### ⚠️ [{i.category}] {i.description}\n"
        if i.fix:
            md += f"- **Fix:** {i.fix}\n"
        if i.patch_applied:
            md += f"- **Status:** ✅ Auto-patched\n"
        md += "\n"

    md += "\n## Tools Inventory\n"
    for t in sorted(report.tools_found):
        in_orch = "✅" if any(t in tr for tr in report.tools_registered) else "⚠️"
        md += f"- {in_orch} `{t}`\n"

    md += "\n## Intents → Handlers\n"
    for intent in sorted(set(report.intents_defined)):
        handled = "✅" if intent in report.intents_handled else "❌"
        md += f"- {handled} `{intent}`\n"

    md += f"\n---\n*Report by agentjw_sync_analyzer.py | Score: {report.score}/100*\n"

    # Write timestamped report
    REPORT_FILE.write_text(md, encoding="utf-8")
    ok(f"Report written: {REPORT_FILE.relative_to(ROOT)}")

    # Append to daily log
    daily_entry = f"\n## {NOW.strftime('%H:%M:%S')} — Score: {report.score}/100\n"
    daily_entry += f"- Critical: {len(criticals)}, Warnings: {len(warnings)}\n"
    daily_entry += f"- Patches applied: {report.patches_applied}\n"
    daily_entry += f"- Issues: {'; '.join(i.description[:50] for i in criticals[:3])}\n"

    if DAILY_LOG.exists():
        existing = read_file(DAILY_LOG)
    else:
        existing = f"# AgentJW Daily Log — {NOW.strftime('%Y-%m-%d')}\n"

    DAILY_LOG.write_text(existing + daily_entry, encoding="utf-8")
    ok(f"Daily log updated: {DAILY_LOG.relative_to(ROOT)}")


# ═══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def print_summary():
    h1("FINAL SYNC SUMMARY")

    criticals = [i for i in report.issues if i.severity == "CRITICAL"]
    warnings = [i for i in report.issues if i.severity == "WARNING"]

    if HAS_RICH:
        color = "green" if report.score >= 80 else "yellow" if report.score >= 60 else "red"
        console.print(f"\n[bold {color}]Health Score: {report.score}/100[/bold {color}]")
    else:
        print(f"\nHealth Score: {report.score}/100")

    console.print(f"  Critical issues: {len(criticals)}")
    console.print(f"  Warnings: {len(warnings)}")
    console.print(f"  Auto-patches applied: {report.patches_applied}")
    console.print(f"  Report: {REPORT_FILE.relative_to(ROOT)}")

    if criticals:
        console.print("\n[bold red]CRITICAL — Fix These First:[/bold red]" if HAS_RICH
                      else "\nCRITICAL — Fix These First:")
        for i in criticals[:5]:
            console.print(f"  ❌ [{i.category}] {i.description}")
            if i.fix:
                console.print(f"     → {i.fix}")

    console.print("\n[bold cyan]Next Actions:[/bold cyan]" if HAS_RICH else "\nNext Actions:")
    if not AUTO_PATCH and any(i.auto_fixable for i in report.issues if not i.patch_applied):
        console.print("  1. Run: python3 agentjw_sync_analyzer.py --patch  (apply auto-fixes)")
    console.print("  2. Run this script daily: it saves to logs/daily_YYYYMMDD.md")
    console.print("  3. Fix critical issues manually that can't be auto-patched")
    console.print("  4. Re-run to verify: python3 agentjw_sync_analyzer.py")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    h1("AgentJW SYNC ANALYZER" + (" [AUTO-PATCH MODE]" if AUTO_PATCH else ""))
    console.print(f"[dim]Root: {ROOT}[/dim]" if HAS_RICH else f"Root: {ROOT}")
    console.print(f"[dim]Time: {NOW.strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n" if HAS_RICH
                  else f"Time: {NOW.strftime('%Y-%m-%d %H:%M:%S')}\n")

    if not ROOT.exists():
        print(f"ERROR: {ROOT} not found!")
        sys.exit(1)

    analyze_ports()
    analyze_endpoints()
    analyze_brain_intent()
    tool_instances, tool_methods = analyze_tools()
    analyze_ai_models()
    analyze_env()
    analyze_imports()
    analyze_orchestrator()
    analyze_workflow_sync()
    apply_auto_patches()
    write_report()
    print_summary()


if __name__ == "__main__":
    main()
