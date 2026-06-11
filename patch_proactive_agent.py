"""
patch_proactive_agent.py
========================
Patch AgentJW agar:
1. Saat build project → auto-detect env vars yang dibutuhkan
2. Tanya user secara interaktif untuk isi API key / secret
3. Tulis langsung ke .env project
4. Chat response inject project context penuh
5. Orchestrator tidak setengah-setengah

Jalankan dari ~/agentjw/:
    python patch_proactive_agent.py
"""

from pathlib import Path
import shutil
from datetime import datetime

ROOT = Path.home() / "agentjw"
BACKUP_DIR = ROOT / "backups" / f"pre_proactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def backup(path: Path):
    if path.exists():
        dest = BACKUP_DIR / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        print(f"  📦 Backed up: {path.relative_to(ROOT)}")

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  ✅ Written: {path.relative_to(ROOT)}")

# ─── 1. ENV MANAGER ───────────────────────────────────────────────────────────

ENV_MANAGER = '''"""
tools/env_manager.py
====================
Proactive .env manager — detect, ask, write API keys for any project.
Called automatically after build to ensure project is fully configured.
"""
import re
import os
from pathlib import Path
from typing import Dict, List, Optional
from core.logger import logger, console
from rich.panel import Panel
from rich.table import Table


# Known env vars and their descriptions + examples
ENV_REGISTRY = {
    # Solana / Trading
    "SOLANA_PRIVATE_KEY":        ("Private key wallet Solana (base58)", "5xK...abc"),
    "WALLET_PRIVATE_KEY":        ("Private key wallet Solana (base58)", "5xK...abc"),
    "SOLANA_RPC_URL":            ("Solana RPC endpoint", "https://api.mainnet-beta.solana.com"),
    "SOLANA_WS_URL":             ("Solana WebSocket endpoint", "wss://api.mainnet-beta.solana.com"),
    "HELIUS_API_KEY":            ("Helius RPC API key (opsional, untuk kecepatan lebih)", "abc123..."),
    "PAPER_TRADING":             ("Mode paper trading? true=simulasi, false=live", "true"),
    "LIVE_TRADING":              ("Enable live trading? (false dulu untuk safety)", "false"),
    "DEFAULT_POSITION_SIZE_SOL": ("Ukuran posisi default dalam SOL", "0.1"),
    "MAX_DAILY_LOSS_SOL":        ("Maksimum loss harian dalam SOL", "1.0"),
    "STOP_LOSS_PERCENT":         ("Stop loss percentage", "10"),
    "TAKE_PROFIT_MULTIPLIER":    ("Take profit multiplier (2x = 200%)", "2.0"),
    "SLIPPAGE_BPS":              ("Slippage basis points (100 = 1%)", "100"),

    # YouTube / Google
    "YOUTUBE_API_KEY":           ("YouTube Data API v3 key", "AIza..."),
    "GOOGLE_CLIENT_ID":          ("Google OAuth client ID", "xxx.apps.googleusercontent.com"),
    "GOOGLE_CLIENT_SECRET":      ("Google OAuth client secret", "GOCSPX-..."),

    # OpenAI / LLM
    "OPENAI_API_KEY":            ("OpenAI API key", "sk-..."),
    "OPENROUTER_API_KEY":        ("OpenRouter API key untuk video studio", "sk-or-..."),
    "ANTHROPIC_API_KEY":         ("Anthropic Claude API key", "sk-ant-..."),

    # Telegram / Discord
    "TELEGRAM_BOT_TOKEN":        ("Telegram bot token dari @BotFather", "123456:ABC..."),
    "TELEGRAM_CHAT_ID":          ("Telegram chat/channel ID untuk notifikasi", "-100123456"),
    "DISCORD_WEBHOOK_URL":       ("Discord webhook URL", "https://discord.com/api/webhooks/..."),

    # Database
    "DATABASE_URL":              ("Database connection string", "sqlite:///db.sqlite3"),
    "REDIS_URL":                 ("Redis connection URL", "redis://localhost:6379"),

    # Generic
    "SECRET_KEY":                ("Secret key untuk Flask/Django", "random-string-32-chars"),
    "API_KEY":                   ("API key umum", "your-api-key-here"),
    "API_SECRET":                ("API secret umum", "your-api-secret-here"),
}

# Keys yang TIDAK perlu ditanya (sudah ada default yang aman)
SKIP_IF_HAS_DEFAULT = {
    "PAPER_TRADING", "LIVE_TRADING", "DEFAULT_POSITION_SIZE_SOL",
    "MAX_DAILY_LOSS_SOL", "STOP_LOSS_PERCENT", "TAKE_PROFIT_MULTIPLIER",
    "SLIPPAGE_BPS", "SOLANA_RPC_URL", "DATABASE_URL",
}


class EnvManager:
    """Detects, asks, and writes .env for any project directory."""

    def scan_required_vars(self, project_dir: str) -> List[str]:
        """Scan Python files untuk os.getenv() calls."""
        pd = Path(project_dir)
        found = set()
        pattern = re.compile(r'os\.getenv\(["\']([A-Z_][A-Z0-9_]*)["\']')
        for py_file in pd.rglob("*.py"):
            try:
                text = py_file.read_text(encoding="utf-8", errors="ignore")
                found.update(pattern.findall(text))
            except Exception:
                pass
        return sorted(found)

    def read_env_file(self, env_path: Path) -> Dict[str, str]:
        """Parse .env file into dict."""
        result = {}
        if not env_path.exists():
            return result
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                result[k.strip()] = v.strip()
        return result

    def write_env_file(self, env_path: Path, env_dict: Dict[str, str]):
        """Write dict to .env file, preserving existing comments."""
        lines = []
        if env_path.exists():
            existing = env_path.read_text(encoding="utf-8").splitlines()
            written_keys = set()
            for line in existing:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    k = stripped.split("=")[0].strip()
                    if k in env_dict:
                        lines.append(f"{k}={env_dict[k]}")
                        written_keys.add(k)
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
            # Add new keys not in existing file
            new_keys = set(env_dict.keys()) - written_keys
            if new_keys:
                lines.append("")
                lines.append("# Added by AgentJW")
                for k in sorted(new_keys):
                    lines.append(f"{k}={env_dict[k]}")
        else:
            lines.append("# Generated by AgentJW")
            for k, v in env_dict.items():
                lines.append(f"{k}={v}")

        env_path.write_text("\\n".join(lines) + "\\n", encoding="utf-8")

    def check_and_prompt(self, project_dir: str, project_name: str = "") -> Dict[str, str]:
        """
        Main method: scan project, find missing vars, prompt user to fill them.
        Returns dict of vars that were filled.
        """
        pd = Path(project_dir)
        env_path = pd / ".env"

        required = self.scan_required_vars(project_dir)
        existing = self.read_env_file(env_path)

        # Find missing or empty vars
        missing = []
        for var in required:
            val = existing.get(var, "")
            if not val or val in ("", "your_key_here", "xxx", "CHANGE_ME"):
                missing.append(var)

        if not missing:
            console.print("[green]✅ Semua env vars sudah terset![/green]")
            return {}

        # Show what's needed
        console.print()
        console.print(Panel(
            f"[yellow]Project [bold]{project_name or pd.name}[/bold] butuh {len(missing)} konfigurasi.[/yellow]\\n"
            f"AgentJW akan tanya satu per satu — tekan Enter untuk skip (pakai default).",
            title="🔑 Setup API Keys & Config",
            border_style="yellow"
        ))

        filled = {}

        # Group: critical first (private keys), then optional
        critical = [v for v in missing if "PRIVATE_KEY" in v or "SECRET" in v or "TOKEN" in v]
        optional = [v for v in missing if v not in critical]

        for var in critical + optional:
            info = ENV_REGISTRY.get(var, (f"Nilai untuk {var}", "your-value-here"))
            desc, example = info

            is_skip_candidate = var in SKIP_IF_HAS_DEFAULT
            is_secret = any(k in var for k in ["KEY", "SECRET", "TOKEN", "PASSWORD"])

            console.print(f"\\n[cyan]📌 {var}[/cyan]")
            console.print(f"   [dim]{desc}[/dim]")
            if not is_secret:
                console.print(f"   [dim]Contoh: {example}[/dim]")

            try:
                if is_skip_candidate and var in existing:
                    console.print(f"   [dim]→ Sudah ada default, skip[/dim]")
                    continue

                prompt_text = f"   Masukkan nilai (Enter=skip): "
                value = input(prompt_text).strip()

                if value:
                    filled[var] = value
                    existing[var] = value
                    console.print(f"   [green]✓ Disimpan[/green]")
                else:
                    # Use default from registry if available
                    if is_skip_candidate:
                        default_val = example
                        existing.setdefault(var, default_val)
                        console.print(f"   [dim]→ Pakai default: {default_val}[/dim]")
                    else:
                        console.print(f"   [yellow]→ Dilewati (isi nanti di .env)[/yellow]")

            except (EOFError, KeyboardInterrupt):
                # Non-interactive mode (API call from APK)
                console.print(f"   [dim]→ Non-interactive mode, skip[/dim]")
                continue

        # Write back
        self.write_env_file(env_path, existing)

        if filled:
            console.print()
            console.print(Panel(
                f"[green]✅ {len(filled)} variabel disimpan ke {env_path}[/green]\\n"
                + "\\n".join(f"  • {k}" for k in filled.keys()),
                title="💾 .env Updated",
                border_style="green"
            ))
        else:
            console.print()
            console.print(f"[dim].env template written to {env_path} — isi API keys secara manual[/dim]")

        return filled

    def generate_env_template(self, project_dir: str) -> str:
        """Generate .env template string untuk ditampilkan ke user di APK."""
        required = self.scan_required_vars(project_dir)
        existing = self.read_env_file(Path(project_dir) / ".env")

        lines = ["# .env — Generated by AgentJW", "# Isi nilai yang kosong (???)", ""]
        for var in required:
            info = ENV_REGISTRY.get(var, (f"Nilai untuk {var}", "???"))
            desc, example = info
            current = existing.get(var, "")
            is_filled = bool(current) and current not in ("", "your_key_here", "xxx")
            status = "✓" if is_filled else "⚠"
            val_display = current if is_filled else f"???  # contoh: {example}"
            lines.append(f"# {status} {desc}")
            lines.append(f"{var}={val_display}")
            lines.append("")

        return "\\n".join(lines)


env_manager = EnvManager()
'''

# ─── 2. ORCHESTRATOR PATCH ────────────────────────────────────────────────────

ORCHESTRATOR_PATCH = '''
    # ═══════════════════════════════════════════
    # PROACTIVE ENV SETUP (inject after any build)
    # ═══════════════════════════════════════════
    def _post_build_env_check(self, project_dir: str, project_name: str, session_id: str) -> str:
        """
        After building a project, check for missing env vars.
        In CLI mode: interactive prompt.
        In API mode (from APK): return template string.
        Returns message to show user.
        """
        try:
            from tools.env_manager import env_manager
            import os

            # Detect if running interactively (CLI) or via API
            is_interactive = os.isatty(0) if hasattr(os, "isatty") else False

            if is_interactive:
                filled = env_manager.check_and_prompt(project_dir, project_name)
                if filled:
                    return f"✅ {len(filled)} API keys disimpan ke .env"
                return ""
            else:
                # API mode: return template for user to fill
                template = env_manager.generate_env_template(project_dir)
                missing_count = template.count("⚠")
                if missing_count > 0:
                    return (
                        f"\\n\\n📋 **Setup Required** — {missing_count} env vars perlu diisi:\\n"
                        f"```\\n{template[:800]}\\n```\\n"
                        f"Paste API keys ke chat, format:\\n"
                        f"`NAMA_VAR=nilai_kamu`\\n"
                        f"AgentJW akan simpan otomatis ke .env"
                    )
                return ""
        except Exception as e:
            logger.warning(f"post_build_env_check failed: {e}")
            return ""

    def _handle_env_paste(self, user_input: str, session_id: str) -> Optional[Dict]:
        """
        Detect if user pasted env var values like KEY=value.
        Auto-save to the most recent project .env.
        Returns result dict if handled, None otherwise.
        """
        import re
        lines = user_input.strip().splitlines()
        env_pairs = {}
        for line in lines:
            line = line.strip()
            m = re.match(r'^([A-Z][A-Z0-9_]{2,})\s*=\s*(.+)$', line)
            if m:
                env_pairs[m.group(1)] = m.group(2).strip()

        if not env_pairs:
            return None

        # Find target project
        projects = memory_store.list_projects()
        if not projects:
            return None

        proj = self._find_project_ref(user_input, projects) or projects[0]
        env_path = Path(proj["project_dir"]) / ".env"

        try:
            from tools.env_manager import env_manager
            existing = env_manager.read_env_file(env_path)
            existing.update(env_pairs)
            env_manager.write_env_file(env_path, existing)

            keys_saved = list(env_pairs.keys())
            console.print(Panel(
                f"[green]✅ {len(keys_saved)} variabel disimpan ke {proj['name']}/.env[/green]\\n"
                + "\\n".join(f"  • {k}" for k in keys_saved),
                title="💾 .env Updated",
                border_style="green"
            ))
            return {
                "status": "env_saved",
                "project": proj["name"],
                "keys_saved": keys_saved,
                "env_path": str(env_path),
            }
        except Exception as e:
            logger.error(f"env paste save failed: {e}")
            return None
'''

# ─── 3. SMART_BUILD WRAPPER WITH ENV CHECK ────────────────────────────────────

SMART_BUILD_WRAPPER = '''
    def smart_build(self, user_request: str, session_id: str = None) -> Dict:
        session_id = session_id or str(uuid.uuid4())

        # ── Check if user is pasting env vars ──────────────────────────────
        env_result = self._handle_env_paste(user_request, session_id)
        if env_result:
            return env_result

        intent = self.route_intent(user_request)
        console.print(f"[dim]→ {intent[\'type\']} ({intent[\'confidence\']})[/dim]")

        handlers = {
            "inspect":         self._inspect_action,
            "project_repair":  self._repair_existing,
            "trading_build":   self._build_trading,
            "youtube_build":   self._build_youtube,
            "analysis":        self._analyze_project,
            "continue_project":self._continue_project,
            "modify_strategy": self._modify_strategy,
            "run_project":     self._run_project,
            "mcp_tool":        self._mcp_action,
            "general_build":   self._general_build,
        }
        handler = handlers.get(intent["type"])
        if handler:
            result = handler(user_request, session_id) if intent["type"] not in (
                "inspect", "run_project", "mcp_tool"
            ) else handler(user_request)

            # ── Post-build: proactive env check ────────────────────────────
            if intent["type"].endswith("_build") or intent["type"] in ("general_build", "continue_project"):
                if isinstance(result, dict) and result.get("project_dir"):
                    env_msg = self._post_build_env_check(
                        result["project_dir"],
                        result.get("project_name", ""),
                        session_id
                    )
                    if env_msg:
                        result["env_setup_message"] = env_msg
                        # Show in console too
                        console.print(Panel(env_msg[:600], title="🔑 Setup API Keys", border_style="yellow"))

            return result

        return {"type": "chat"}
'''

# ─── 4. ENHANCED CHAT WITH FULL PROJECT CONTEXT ──────────────────────────────

ENHANCED_CHAT = '''
    def chat(self, user_message: str, history: List[Dict], session_id: str) -> str:
        from core.llm_client import llm
        from agents.memory_agent import memory_agent

        lower = user_message.lower()

        # ── Check if user is pasting env vars ──────────────────────────────
        env_result = self._handle_env_paste(user_message, session_id)
        if env_result:
            keys = env_result.get("keys_saved", [])
            return (
                f"✅ Disimpan {len(keys)} variabel ke {env_result[\'project\']}/.env:\\n"
                + "\\n".join(f"  • {k}" for k in keys)
                + "\\n\\nBot siap dijalankan. Ketik: `jalankan` untuk start."
            )

        # ── Build rich project context ──────────────────────────────────────
        projects = memory_store.list_projects(limit=5)
        proj_ctx = ""
        real_data = ""

        if projects:
            proj_lines = []
            for p in projects:
                env_path = Path(p["project_dir"]) / ".env"
                has_env = env_path.exists()
                env_complete = False
                if has_env:
                    try:
                        from tools.env_manager import env_manager
                        required = env_manager.scan_required_vars(p["project_dir"])
                        existing = env_manager.read_env_file(env_path)
                        missing = [v for v in required if not existing.get(v)]
                        env_complete = len(missing) == 0
                        env_status = f"✅ lengkap" if env_complete else f"⚠️  missing: {missing[:3]}"
                    except Exception:
                        env_status = "exists"
                else:
                    env_status = "❌ tidak ada"

                proj_lines.append(
                    f"- [{p[\'id\']}] {p[\'name\']} | {p[\'status\']} | {p[\'tool_type\']} "
                    f"| .env: {env_status} | {p[\'created_at\'][:10]}"
                )
            proj_ctx = "\\n".join(proj_lines)

            # Inject real file data for relevant questions
            file_keywords = [
                "log", "isi file", "tampilkan", "baca", "struktur",
                "hash", "sha256", "roi", "profit", "loss", "balance",
                "trade", "transaksi", "file", "kode", "status", "error"
            ]
            if any(k in lower for k in file_keywords):
                target = self._find_project_ref(user_message, projects) or projects[0]
                try:
                    scan = self.fs.scan_project(target["project_dir"])
                    logs = self.fs.read_log(target["project_dir"], lines=20)
                    real_data = f"""
REAL DATA — {target[\'name\']} (from disk: {target[\'project_dir\']}):
Files: {[f[\'name\'] for f in scan.get(\'python_files\',[])]}
Valid syntax: {scan.get(\'valid_syntax\',0)}/{scan.get(\'total_py\',0)}
Size: {scan.get(\'total_size_kb\',0)}KB
.env: {\'exists\' if scan.get(\'has_env\') else \'MISSING\'}
RECENT LOG:
{str(logs.get(\'content\',\'\') if isinstance(logs,dict) else logs)[:800]}
"""
                except Exception as e:
                    real_data = f"(scan failed: {e})"

        mem = memory_agent.run({"action": "retrieve", "query": user_message, "limit": 3})
        snippets = mem.get("snippets", [])

        chat_ctx = ""
        if history and len(history) > 2:
            for msg in history[-4:]:
                role = "You" if msg["role"] == "assistant" else "User"
                chat_ctx += f"{role}: {msg[\'content\'][:150]}\\n"

        system = f"""Kamu adalah AgentJW — autonomous AI engineer GOD MODE.
Kamu PROAKTIF: jika project butuh API key atau config, langsung minta dan tulis ke .env.
Kamu TIDAK minta user copy-paste perintah manual jika bisa dilakukan sendiri.

STRICT RULES:
1. JANGAN fabrikasi data, angka ROI, profit, atau hash
2. Jawab berdasarkan REAL PROJECT DATA di bawah
3. Jika data tidak tersedia: "Data tidak tersedia. Ketik: scan [nama project]"
4. Untuk trading performance: HANYA dari log files nyata
5. Jika project butuh API key → tampilkan template .env dan minta user paste nilainya

PROJECTS ({len(projects)} total):
{proj_ctx}
{real_data}
CARA USER BISA PASTE API KEY:
User cukup ketik: NAMA_KEY=nilainya
AgentJW akan simpan otomatis ke .env project terkait.

RECENT CHAT:
{chat_ctx}"""

        if snippets:
            system += "\\nMEMORY:\\n" + "\\n".join(f"- {s[:120]}" for s in snippets)

        messages = [{"role": m["role"], "content": m["content"]} for m in history[-8:]]
        messages.append({"role": "user", "content": user_message})
        response = llm.chat(messages=messages, system=system, temperature=0.7, max_tokens=2048)
        memory_store.save_chat(session_id, "user", user_message)
        memory_store.save_chat(session_id, "assistant", response)
        return response
'''

# ─── 5. API SERVER PATCH — return env_setup_message to APK ────────────────────

API_PATCH_CODE = '''
        # ── Inject env_setup_message to APK response ───────────────────────
        if mode == "build":
            result = orchestrator.smart_build(msg, sid)
            response_text = f"✅ Build selesai!\\n{json.dumps(result, indent=2, ensure_ascii=False)[:400]}"
            env_msg = result.get("env_setup_message", "")
            if env_msg:
                response_text += "\\n\\n" + env_msg
            return {
                "response": response_text,
                "session_id": sid,
                "mode": "build",
                "result": result,
                "env_setup": env_msg,
                "status": "success",
            }
'''

# ─── APPLY PATCHES ────────────────────────────────────────────────────────────

def apply():
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║  🔧  AgentJW Proactive Agent Patch              ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    # 1. Write env_manager.py
    env_mgr_path = ROOT / "tools" / "env_manager.py"
    backup(env_mgr_path)
    write(env_mgr_path, ENV_MANAGER)

    # 2. Patch orchestrator.py
    orch_path = ROOT / "agents" / "orchestrator.py"
    if not orch_path.exists():
        print(f"  ❌ Not found: {orch_path}")
        return

    backup(orch_path)
    content = orch_path.read_text(encoding="utf-8")

    # 2a. Add new methods before last line (orchestrator = OrchestratorAgent())
    INJECT_MARKER = "\norchestrator = OrchestratorAgent()"
    if "_post_build_env_check" not in content:
        content = content.replace(
            INJECT_MARKER,
            ORCHESTRATOR_PATCH + INJECT_MARKER
        )
        print("  ✅ Added _post_build_env_check() + _handle_env_paste()")
    else:
        print("  ⚠️  _post_build_env_check already exists, skipping")

    # 2b. Replace smart_build with version that has env check
    if "_handle_env_paste" not in content.split("def smart_build")[0] if "def smart_build" in content else True:
        # Replace the whole smart_build method
        import re
        # Find and replace smart_build
        old_smart = re.search(r'\n    def smart_build\(.*?\n    def ', content, re.DOTALL)
        if old_smart:
            old_text = old_smart.group(0)
            new_text = SMART_BUILD_WRAPPER + "\n\n    def "
            content = content.replace(old_text, new_text)
            print("  ✅ Replaced smart_build() with proactive version")
        else:
            print("  ⚠️  Could not find smart_build() to replace — append instead")

    # 2c. Replace chat() with enhanced version
    old_chat = re.search(r'\n    # ═+\n    # CHAT.*?\n    def chat\(.*?\n    def ', content, re.DOTALL)
    if old_chat:
        old_text = old_chat.group(0)
        new_text = "\n" + ENHANCED_CHAT + "\n\n    def "
        content = content.replace(old_text, new_text)
        print("  ✅ Replaced chat() with context-rich version")
    else:
        # Try simpler replacement
        old_chat2 = re.search(r'\n    def chat\(self.*?\n(?=    def |\norchestrator)', content, re.DOTALL)
        if old_chat2:
            content = content.replace(old_chat2.group(0), "\n" + ENHANCED_CHAT + "\n\n")
            print("  ✅ Replaced chat() (fallback method)")
        else:
            print("  ⚠️  Could not find chat() to replace")

    orch_path.write_text(content, encoding="utf-8")
    print(f"  💾 Saved: agents/orchestrator.py")

    # 3. Patch api_server.py — return env_setup_message
    api_path = ROOT / "api_server.py"
    if api_path.exists():
        backup(api_path)
        api_content = api_path.read_text(encoding="utf-8")
        # Find the build mode handler and add env_setup_message
        old_build_resp = '''            result = orchestrator.smart_build(msg, sid)
            return {
                "response": f"✅ Build selesai!\\n{json.dumps(result, indent=2, ensure_ascii=False)[:500]}",
                "session_id": sid,
                "mode": "build",
                "result": result,
                "status": "success",
            }'''
        if old_build_resp in api_content:
            new_build_resp = '''            result = orchestrator.smart_build(msg, sid)
            env_msg = result.get("env_setup_message", "")
            response_text = f"✅ Build selesai!\\n{json.dumps(result, indent=2, ensure_ascii=False)[:400]}"
            if env_msg:
                response_text += "\\n\\n" + env_msg
            return {
                "response": response_text,
                "session_id": sid,
                "mode": "build",
                "result": result,
                "env_setup": env_msg,
                "status": "success",
            }'''
            api_content = api_content.replace(old_build_resp, new_build_resp)
            api_path.write_text(api_content, encoding="utf-8")
            print("  ✅ Patched api_server.py build response")
        else:
            print("  ⚠️  api_server.py build block not found (already patched?)")

    # 4. Verify syntax
    print()
    print("Verifying syntax...")
    import subprocess
    for f in [env_mgr_path, orch_path]:
        r = subprocess.run(["python3", "-m", "py_compile", str(f)], capture_output=True)
        if r.returncode == 0:
            print(f"  ✓ {f.name}")
        else:
            print(f"  ❌ {f.name}: {r.stderr.decode()[:200]}")

    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║  ✅  Patch Complete!                            ║")
    print("╚══════════════════════════════════════════════════╝")
    print()
    print("Next steps di VPS:")
    print("  1. python patch_proactive_agent.py  (sudah running ini)")
    print("  2. pkill -f api_server && nohup python api_server.py > api.log 2>&1 &")
    print("  3. Test: agentjw > buat trading bot solana")
    print("     → AgentJW akan tanya API keys setelah build")
    print("  4. Di APK: paste SOLANA_PRIVATE_KEY=xxx → auto-save ke .env")
    print()


if __name__ == "__main__":
    import re
    apply()
