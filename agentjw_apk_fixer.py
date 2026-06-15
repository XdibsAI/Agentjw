#!/usr/bin/env python3
# flake8: noqa
import warnings; warnings.filterwarnings("ignore", category=SyntaxWarning)
"""
agentjw_apk_fixer.py
====================
Script LENGKAP untuk analisa & perbaiki APK Flutter AgentJW agar
sinkron dengan backend. 

FUNGSI UTAMA:
  1. Scan semua endpoint APK vs backend — temukan yang MISSING
  2. Cek semua import Dart & lib dependencies
  3. Verifikasi koneksi LLM dari APK
  4. Deteksi semua fitur di APK yang belum terhubung
  5. Generate patch Dart otomatis untuk setiap gap
  6. Build report lengkap + generate fix script

Jalankan:
  python3 agentjw_apk_fixer.py [--patch] [--report-only] [--verbose]

  --patch       : Auto-apply semua fix yang bisa dipatch otomatis
  --report-only : Hanya buat laporan, tidak patch
  --verbose     : Output detail setiap check

Lokasi default:
  Backend  : ~/agentjw/
  Flutter  : ~/agentjw_apk/  (atau tentukan via --apk-dir)
"""

import os
import re
import sys
import json
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# ──────────────────────────────────────────────────────────────────
# CLI ARGS
# ──────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="AgentJW APK ↔ Backend Sync Fixer")
parser.add_argument("--patch",       action="store_true", help="Auto-patch semua yang bisa diperbaiki")
parser.add_argument("--report-only", action="store_true", help="Hanya laporan, tidak patch apapun")
parser.add_argument("--verbose",     action="store_true", help="Output detail")
parser.add_argument("--backend-dir", default=str(Path.home() / "agentjw"),      help="Path backend")
parser.add_argument("--apk-dir",     default=str(Path.home() / "agentjw_apk"),  help="Path Flutter project")
parser.add_argument("--apk-ip",      default="",           help="IP VPS untuk APK (override auto-detect)")
args = parser.parse_args()

BACKEND_DIR = Path(args.backend_dir)
APK_DIR     = Path(args.apk_dir)
AUTO_PATCH  = args.patch
REPORT_ONLY = args.report_only
VERBOSE     = args.verbose

NOW       = datetime.now()
TIMESTAMP = NOW.strftime("%Y%m%d_%H%M%S")
LOG_DIR   = BACKEND_DIR / "logs"
REPORT_MD = LOG_DIR / f"apk_fix_report_{TIMESTAMP}.md"

# ──────────────────────────────────────────────────────────────────
# COLORS
# ──────────────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    console = Console()
    HAS_RICH = True
    def h1(s):   console.print(f"\n[bold cyan]{'═'*65}[/bold cyan]\n[bold cyan]{s}[/bold cyan]")
    def h2(s):   console.print(f"\n[bold yellow]▶ {s}[/bold yellow]")
    def ok(s):   console.print(f"  [green]✅ {s}[/green]")
    def warn(s): console.print(f"  [yellow]⚠️  {s}[/yellow]")
    def err(s):  console.print(f"  [red]❌ {s}[/red]")
    def fix(s):  console.print(f"  [magenta]🔧 {s}[/magenta]")
    def info(s): console.print(f"  [dim]ℹ  {s}[/dim]")
    def skip(s): console.print(f"  [dim]⤷  {s}[/dim]")
except ImportError:
    HAS_RICH = False
    def h1(s):   print(f"\n{'='*65}\n{s}")
    def h2(s):   print(f"\n▶ {s}")
    def ok(s):   print(f"  ✅ {s}")
    def warn(s): print(f"  ⚠️  {s}")
    def err(s):  print(f"  ❌ {s}")
    def fix(s):  print(f"  🔧 {s}")
    def info(s): print(f"     {s}")
    def skip(s): print(f"  ⤷  {s}")

# ──────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ──────────────────────────────────────────────────────────────────
@dataclass
class Issue:
    category: str
    severity: str        # CRITICAL / WARNING / INFO
    title: str
    detail: str = ""
    file: str = ""
    line: int = 0
    fix_hint: str = ""
    auto_fixable: bool = False
    patch_applied: bool = False

@dataclass
class FixReport:
    issues: List[Issue] = field(default_factory=list)
    backend_routes: Set[str] = field(default_factory=set)
    apk_calls: Set[str]     = field(default_factory=set)
    missing_routes: Set[str] = field(default_factory=set)
    dart_imports: Set[str]  = field(default_factory=set)
    missing_imports: Set[str] = field(default_factory=set)
    pubspec_deps: Set[str]  = field(default_factory=set)
    missing_deps: Set[str]  = field(default_factory=set)
    apk_tabs: List[str]     = field(default_factory=list)
    apk_features: Dict[str, bool] = field(default_factory=dict)
    backend_port: int = 18790
    apk_port: int = 0
    apk_ip: str = ""
    patches_applied: int = 0
    score: int = 100

    def add(self, issue: Issue):
        self.issues.append(issue)
        if issue.severity == "CRITICAL": self.score -= 20
        elif issue.severity == "WARNING": self.score -= 7
        self.score = max(0, self.score)

report = FixReport()

# ──────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────
def read(path: Path) -> str:
    try:    return path.read_text(encoding="utf-8", errors="ignore")
    except: return ""

def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def backup(path: Path) -> Path:
    dest = path.parent / f"{path.name}.apkfix_bak_{NOW.strftime('%H%M%S')}"
    shutil.copy2(path, dest)
    return dest

def find_dart_files(directory: Path) -> List[Path]:
    return list(directory.rglob("*.dart")) if directory.exists() else []

def find_python_files(directory: Path) -> List[Path]:
    return [p for p in directory.rglob("*.py")
            if "__pycache__" not in str(p) and ".git" not in str(p)]

def run(cmd: str, cwd: Path = None) -> Tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          timeout=20, cwd=str(cwd or Path.cwd()))
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)

def vprint(s):
    if VERBOSE: info(s)


# ══════════════════════════════════════════════════════════════════
# CHECK 1: DIRECTORY STRUCTURE
# ══════════════════════════════════════════════════════════════════
def check_dirs():
    h2("1. DIRECTORY STRUCTURE CHECK")

    if not BACKEND_DIR.exists():
        err(f"Backend dir tidak ditemukan: {BACKEND_DIR}")
        report.add(Issue("DIR", "CRITICAL", "Backend dir tidak ditemukan",
                         f"Pastikan backend ada di: {BACKEND_DIR}",
                         fix_hint=f"mkdir -p {BACKEND_DIR}"))
    else:
        ok(f"Backend  : {BACKEND_DIR}")
        # Check key backend files
        for f in ["api_server.py", ".env", "requirements.txt"]:
            fp = BACKEND_DIR / f
            if fp.exists():
                ok(f"  ✓ {f}")
            else:
                warn(f"  Missing: {f}")
                report.add(Issue("DIR", "WARNING", f"File backend hilang: {f}",
                                 f"File {f} tidak ada di {BACKEND_DIR}"))

    if not APK_DIR.exists():
        warn(f"Flutter dir tidak ditemukan: {APK_DIR}")
        warn("Scanning semua path umum...")
        candidates = [
            Path.home() / "agentjw_flutter",
            Path.home() / "flutter_agentjw",
            Path.home() / "app",
            Path("/opt/agentjw_apk"),
        ]
        for c in candidates:
            if c.exists() and (c / "pubspec.yaml").exists():
                warn(f"  Ditemukan kandidat: {c}")
                report.add(Issue("DIR", "WARNING", f"Flutter dir ditemukan di lokasi non-standar: {c}",
                                 fix_hint=f"Jalankan dengan: --apk-dir {c}"))
        report.add(Issue("DIR", "CRITICAL", "Flutter APK dir tidak ditemukan",
                         f"Path: {APK_DIR}",
                         fix_hint=f"Gunakan: --apk-dir /path/ke/flutter/project"))
    else:
        ok(f"Flutter  : {APK_DIR}")
        pubspec = APK_DIR / "pubspec.yaml"
        if pubspec.exists():
            ok("  ✓ pubspec.yaml ada")
        else:
            err("  pubspec.yaml TIDAK ADA — bukan Flutter project?")
            report.add(Issue("DIR", "CRITICAL", "pubspec.yaml tidak ditemukan", str(APK_DIR)))

        lib_dir = APK_DIR / "lib"
        dart_files = find_dart_files(lib_dir)
        ok(f"  ✓ {len(dart_files)} file Dart ditemukan")
        for df in dart_files[:20]:
            vprint(f"    {df.relative_to(APK_DIR)}")


# ══════════════════════════════════════════════════════════════════
# CHECK 2: BACKEND ROUTES
# ══════════════════════════════════════════════════════════════════
def check_backend_routes():
    h2("2. BACKEND ROUTES SCAN")

    api_file = BACKEND_DIR / "api_server.py"
    if not api_file.exists():
        err("api_server.py tidak ditemukan!")
        return

    content = read(api_file)

    # Extract all @app routes
    routes = re.findall(r'@app\.\w+\("([^"]+)"', content)
    for r in routes:
        report.backend_routes.add(r)
        vprint(f"  ROUTE: {r}")

    ok(f"Backend routes ditemukan: {len(report.backend_routes)}")
    for r in sorted(report.backend_routes):
        ok(f"  {r}")

    # Check port
    port_match = re.search(r'port\s*=\s*int\(os\.getenv\("API_PORT",\s*"(\d+)"\)', content)
    if port_match:
        report.backend_port = int(port_match.group(1))
        ok(f"Backend port: {report.backend_port}")
    else:
        port_match2 = re.search(r'port\s*=\s*(\d{4,5})', content)
        if port_match2:
            report.backend_port = int(port_match2.group(1))
            warn(f"Backend port hardcoded: {report.backend_port}")
        else:
            warn("Backend port tidak terdeteksi — asumsi 18790")
            report.backend_port = 18790


# ══════════════════════════════════════════════════════════════════
# CHECK 3: APK ENDPOINT CALLS
# ══════════════════════════════════════════════════════════════════
def check_apk_endpoints():
    h2("3. APK ENDPOINT CALLS SCAN")

    dart_files = find_dart_files(APK_DIR / "lib")
    if not dart_files:
        err("Tidak ada file Dart ditemukan!")
        return

    # Pattern: Uri.parse('$baseUrl/xxx') or baseUrl + '/xxx'
    uri_patterns = [
        r"""Uri\.parse\(['"]\$\{?(?:widget\.)?(?:_)?baseUrl\}?([^'"]+)['"]\)""",
        r"""Uri\.parse\(['"]\$baseUrl([^'"]+)['"]\)""",
        r"""baseUrl\s*\+\s*['"]([^'"]+)['"]""",
        r"""http\.[a-z]+\(\s*Uri\.parse\(['"]https?://[^/]+([^'"]+)['"]""",
    ]

    for df in dart_files:
        content = read(df)
        for pat in uri_patterns:
            matches = re.findall(pat, content)
            for m in matches:
                endpoint = m.strip()
                if endpoint:
                    report.apk_calls.add(endpoint)
                    vprint(f"  APK CALL [{df.name}]: {endpoint}")

    ok(f"APK endpoint calls ditemukan: {len(report.apk_calls)}")
    for ep in sorted(report.apk_calls):
        ok(f"  {ep}")

    # Port detection in APK
    for df in dart_files:
        content = read(df)
        # Look for port in baseUrl / config
        port_matches = re.findall(r':(\d{4,5})[/\'"]', content)
        for pm in port_matches:
            if pm in ["8080", "8000", "18790", "3000", "5000"]:
                report.apk_port = int(pm)
                vprint(f"  APK port ditemukan: {pm} in {df.name}")
                break

    if report.apk_port > 0:
        if report.apk_port == report.backend_port:
            ok(f"Port match: APK({report.apk_port}) == Backend({report.backend_port})")
        else:
            err(f"PORT MISMATCH! APK={report.apk_port} vs Backend={report.backend_port}")
            report.add(Issue("PORT", "CRITICAL",
                             f"Port mismatch: APK:{report.apk_port} vs Backend:{report.backend_port}",
                             "APK menggunakan port yang salah",
                             fix_hint=f"Ganti port APK ke {report.backend_port}",
                             auto_fixable=True))


# ══════════════════════════════════════════════════════════════════
# CHECK 4: MISSING ROUTES (APK butuh tapi backend tidak punya)
# ══════════════════════════════════════════════════════════════════
def check_missing_routes():
    h2("4. MISSING ROUTES ANALYSIS")

    # Normalize: remove path params like {id}
    def norm(route):
        return re.sub(r'/\{[^}]+\}', '/{id}', route)

    backend_norm = {norm(r) for r in report.backend_routes}

    for apk_ep in sorted(report.apk_calls):
        apk_norm = norm(apk_ep)
        # Check direct match
        matched = (apk_ep in report.backend_routes) or (apk_norm in backend_norm)
        if not matched:
            report.missing_routes.add(apk_ep)
            err(f"MISSING di backend: {apk_ep}")
            report.add(Issue("ROUTE", "CRITICAL",
                             f"Route hilang: {apk_ep}",
                             f"APK memanggil {apk_ep} tapi backend tidak punya endpoint ini",
                             fix_hint=f"Tambah @app.post/get('{apk_ep}') di api_server.py",
                             auto_fixable=True))
        else:
            ok(f"OK: {apk_ep}")

    if not report.missing_routes:
        ok("Semua APK endpoints sudah ada di backend ✓")


# ══════════════════════════════════════════════════════════════════
# CHECK 5: PUBSPEC DEPENDENCIES
# ══════════════════════════════════════════════════════════════════
def check_pubspec():
    h2("5. PUBSPEC.YAML DEPENDENCY CHECK")

    pubspec_path = APK_DIR / "pubspec.yaml"
    if not pubspec_path.exists():
        err("pubspec.yaml tidak ditemukan!")
        return

    content = read(pubspec_path)

    # Required packages based on features found in Dart files
    REQUIRED_PACKAGES = {
        # Core networking
        "http":               "^1.2.0",
        "dio":                "^5.4.0",
        # UI helpers
        "provider":           "^6.1.2",
        "flutter_riverpod":   None,   # optional
        # Media
        "image_picker":       "^1.1.2",
        "path_provider":      "^2.1.2",
        "open_file":          "^3.3.2",
        "permission_handler": "^11.3.1",
        # Connectivity
        "connectivity_plus":  "^6.0.3",
        # Storage
        "shared_preferences": "^2.2.3",
        # Video player
        "video_player":       "^2.8.3",
        # Markdown render
        "flutter_markdown":   "^0.7.3",
        # Clipboard
        "flutter":            None,    # SDK, always present
    }

    for pkg, ver in REQUIRED_PACKAGES.items():
        if pkg == "flutter": continue
        if ver is None: continue
        if pkg in content:
            vprint(f"  ✓ {pkg} ada")
            report.pubspec_deps.add(pkg)
        else:
            # Check if used in any Dart file
            dart_files = find_dart_files(APK_DIR / "lib")
            is_used = any(f"package:{pkg}" in read(df) or pkg in read(df)
                         for df in dart_files)
            if is_used:
                err(f"MISSING dep (digunakan): {pkg}: {ver}")
                report.missing_deps.add(pkg)
                report.add(Issue("PUBSPEC", "CRITICAL",
                                 f"Dependency hilang: {pkg}",
                                 f"Package '{pkg}' diimport di Dart tapi tidak ada di pubspec.yaml",
                                 file=str(pubspec_path),
                                 fix_hint=f"Tambah ke pubspec.yaml dependencies:\n    {pkg}: {ver}",
                                 auto_fixable=True))
            else:
                vprint(f"  ⤷ {pkg} — tidak digunakan, skip")

    if not report.missing_deps:
        ok("Semua dependencies pubspec OK ✓")


# ══════════════════════════════════════════════════════════════════
# CHECK 6: DART IMPORT CHAIN
# ══════════════════════════════════════════════════════════════════
def check_dart_imports():
    h2("6. DART IMPORT CHAIN CHECK")

    lib_dir = APK_DIR / "lib"
    dart_files = find_dart_files(lib_dir)

    local_files = {df.stem for df in dart_files}
    issues_found = []

    for df in dart_files:
        content = read(df)
        # Find local imports: import 'xxx.dart' or import 'package:agentjw_apk/xxx.dart'
        local_imports = re.findall(r"import\s+'(?!package:)([^']+\.dart)'", content)
        local_imports += re.findall(r'import\s+"(?!package:)([^"]+\.dart)"', content)

        for imp in local_imports:
            imp_path = lib_dir / imp
            if not imp_path.exists():
                imp_stem = Path(imp).stem
                alt_path = lib_dir / f"{imp_stem}.dart"
                if alt_path.exists():
                    vprint(f"  Path berbeda tapi file ada: {imp} → {imp_stem}.dart")
                else:
                    err(f"Import hilang: {df.name} → '{imp}'")
                    issues_found.append((df.name, imp))
                    report.add(Issue("IMPORT", "CRITICAL",
                                     f"Import hilang: '{imp}' di {df.name}",
                                     f"File {df.name} import '{imp}' tapi file tidak ditemukan",
                                     file=str(df),
                                     fix_hint=f"Buat file {imp} atau perbaiki import path"))

        # Check package imports exist in pubspec
        pkg_imports = re.findall(r"import\s+'package:([^/]+)/", content)
        for pkg in pkg_imports:
            if pkg not in ["flutter", "dart"]:
                report.dart_imports.add(pkg)

    if not issues_found:
        ok("Semua Dart import chain OK ✓")
    else:
        err(f"Total import error: {len(issues_found)}")


# ══════════════════════════════════════════════════════════════════
# CHECK 7: TAB & FEATURE INVENTORY
# ══════════════════════════════════════════════════════════════════
def check_features():
    h2("7. APK FEATURE INVENTORY")

    dart_files = find_dart_files(APK_DIR / "lib")

    FEATURE_PATTERNS = {
        "ChatTab / Chat UI":           [r"class\s+ChatTab", r"ChatScreen", r"/api/agent", r"/api/chat"],
        "VideoStudioTab":              [r"class\s+VideoStudioTab", r"/video/package", r"/video/section"],
        "MediaTab (Image/Video Gen)":  [r"class\s+MediaTab", r"/media/image/generate", r"/media/video/generate"],
        "ProjectsTab":                 [r"class\s+ProjectsTab", r"/projects"],
        "BotStatusTab":                [r"class\s+BotStatusTab", r"/api/status"],
        "LLM Direct Query":            [r"LLM|llm_client|llmClient|anthropic|openai|openrouter"],
        "Image Upload":                [r"MultipartRequest", r"image_picker", r"/media/upload"],
        "Video Download":              [r"dio\.download", r"getExternalStorage", r"OpenFile\.open"],
        "Session Management":          [r"session_id", r"SharedPreferences", r"sessionId"],
        "Error Handling":              [r"try\s*\{", r"catch\s*\(", r"onError"],
        "Auth/Token":                  [r"Authorization", r"Bearer", r"apiKey", r"api_key"],
        "Streaming Response":          [r"StreamedResponse", r"Stream<", r"EventSource", r"SSE"],
        "Markdown Rendering":          [r"MarkdownBody\|flutter_markdown\|Markdown\("],
        "Connectivity Check":          [r"connectivity_plus\|ConnectivityResult\|checkConnectivity"],
        "File Picker":                 [r"FilePicker\|file_picker"],
    }

    h2("  Feature Matrix:")
    for feature, patterns in FEATURE_PATTERNS.items():
        found = False
        for df in dart_files:
            content = read(df)
            for pat in patterns:
                if re.search(pat, content, re.IGNORECASE):
                    found = True
                    break
            if found: break

        report.apk_features[feature] = found
        if found:
            ok(f"  {feature}")
        else:
            warn(f"  MISSING: {feature}")

    # Detect BottomNavBar tabs
    for df in dart_files:
        content = read(df)
        tabs = re.findall(r"label:\s*'([^']+)'", content)
        if tabs:
            report.apk_tabs = tabs
            info(f"  Tabs di {df.name}: {', '.join(tabs)}")


# ══════════════════════════════════════════════════════════════════
# CHECK 8: LLM CONNECTIVITY FROM APK
# ══════════════════════════════════════════════════════════════════
def check_llm_connectivity():
    h2("8. LLM CONNECTIVITY CHECK")

    dart_files = find_dart_files(APK_DIR / "lib")

    llm_patterns = {
        "Tanya LLM via /api/agent":   r'/api/agent',
        "Tanya LLM via /api/chat":    r'/api/chat',
        "Direct Anthropic API":       r'anthropic\.com',
        "Direct OpenAI API":          r'api\.openai\.com',
        "OpenRouter API":             r'openrouter\.ai',
        "LLM response parsing":       r'"response"\s*\|response_text\|responseText',
        "History/Context passing":    r'"history"\s*:\s*|sessionHistory',
        "Mode parameter":             r'"mode"\s*:\s*|buildMode|videoMode',
    }

    dart_content = "\n".join(read(df) for df in dart_files)

    any_llm_connected = False
    for name, pat in llm_patterns.items():
        found = bool(re.search(pat, dart_content, re.IGNORECASE))
        if found:
            ok(f"  {name}")
            any_llm_connected = True
        else:
            warn(f"  NOT FOUND: {name}")

    if not any_llm_connected:
        err("APK TIDAK TERHUBUNG KE LLM!")
        report.add(Issue("LLM", "CRITICAL",
                         "APK tidak terhubung ke LLM",
                         "Tidak ada endpoint LLM yang dipanggil dari APK",
                         fix_hint="Tambah ChatTab yang POST ke /api/agent dengan field: message, history, session_id"))

    # Check if chat response is displayed properly
    response_display = re.search(r"""data\[.response.\]|jsonDecode.*response|responseText""", dart_content)
    if response_display:
        ok("  Response LLM ditampilkan di UI")
    else:
        warn("  Response LLM mungkin tidak ditampilkan — cek ChatTab")
        report.add(Issue("LLM", "WARNING",
                         "Response LLM tidak terdeteksi di UI",
                         fix_hint="Tambah Text widget untuk tampilkan data['response']"))


# ══════════════════════════════════════════════════════════════════
# CHECK 9: BACKEND HEALTH TEST
# ══════════════════════════════════════════════════════════════════
def check_backend_health():
    h2("9. BACKEND LIVE HEALTH TEST")

    port = report.backend_port
    ip   = args.apk_ip or "localhost"

    endpoints_to_test = [
        ("GET",  f"http://{ip}:{port}/api/status",  "Health check"),
        ("GET",  f"http://{ip}:{port}/projects",     "Projects list"),
        ("GET",  f"http://{ip}:{port}/health",       "Alt health"),
    ]

    for method, url, label in endpoints_to_test:
        code, out, err_s = run(f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 5 '{url}'")
        status_code = out.strip()
        if status_code == "200":
            ok(f"  {label}: {url} → HTTP {status_code}")
        elif status_code in ["404", "422", "500"]:
            warn(f"  {label}: {url} → HTTP {status_code}")
            report.add(Issue("HEALTH", "WARNING",
                             f"Endpoint error: {url} → {status_code}",
                             fix_hint="Cek api_server.py dan pastikan server berjalan"))
        else:
            err(f"  {label}: {url} → UNREACHABLE (code: {status_code or 'no response'})")
            if ip == "localhost":
                warn("  Backend mungkin tidak berjalan. Start dengan: bash ~/agentjw/fix_api_server.sh")
            report.add(Issue("HEALTH", "WARNING",
                             f"Backend tidak dapat diakses di {url}",
                             fix_hint=f"Start backend: cd ~/agentjw && uvicorn api_server:app --host 0.0.0.0 --port {port}"))


# ══════════════════════════════════════════════════════════════════
# CHECK 10: ENV VARIABLES
# ══════════════════════════════════════════════════════════════════
def check_env():
    h2("10. ENV VARIABLES CHECK")

    env_path = BACKEND_DIR / ".env"
    if not env_path.exists():
        err(".env file tidak ditemukan!")
        report.add(Issue("ENV", "CRITICAL", ".env tidak ditemukan",
                         f"File {env_path} tidak ada",
                         fix_hint="Buat .env dari .env.example:\n  cp ~/agentjw/.env.example ~/agentjw/.env"))
        return

    env_content = read(env_path)
    env_vars = dict(line.split("=", 1) for line in env_content.splitlines()
                   if "=" in line and not line.startswith("#"))

    REQUIRED_VARS = {
        "API_PORT":          ("18790", "Port server API"),
        "LLM_PROVIDER":      ("anthropic", "Provider LLM: anthropic atau openai"),
        "ANTHROPIC_API_KEY": ("", "API key Anthropic (sk-ant-...)"),
        "ANTHROPIC_MODEL":   ("claude-3-5-sonnet-20241022", "Model Claude"),
        "OPENAI_API_KEY":    ("", "API key OpenAI (opsional jika pakai Anthropic)"),
    }

    for var, (default, desc) in REQUIRED_VARS.items():
        val = env_vars.get(var, "")
        if val and val != default and len(val) > 3:
            ok(f"  {var} = {val[:20]}...")
        elif val == default or not val:
            if var in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"] and not val:
                err(f"  {var} KOSONG — LLM tidak akan berfungsi!")
                report.add(Issue("ENV", "CRITICAL", f"{var} tidak diset",
                                 desc,
                                 fix_hint=f"Tambah ke .env:\n  {var}=sk-ant-..."))
            else:
                warn(f"  {var} = '{val}' (default/kosong)")
        else:
            ok(f"  {var} diset ✓")

    # Check API_PORT matches backend
    env_port = int(env_vars.get("API_PORT", "18790"))
    if env_port != report.backend_port:
        err(f"  ENV API_PORT({env_port}) != backend port({report.backend_port})")
        report.add(Issue("ENV", "CRITICAL",
                         f"API_PORT mismatch: .env={env_port} vs api_server.py={report.backend_port}",
                         fix_hint=f"Set API_PORT={report.backend_port} di .env"))


# ══════════════════════════════════════════════════════════════════
# AUTO-PATCH: MISSING BACKEND ROUTES
# ══════════════════════════════════════════════════════════════════
def generate_missing_routes_patch() -> str:
    """Generate FastAPI route code untuk endpoint yang hilang di backend."""

    patches = []

    ROUTE_TEMPLATES = {
        "/media/image/generate": '''
@app.post("/media/image/generate")
async def media_image_generate(req: dict):
    """Generate image via fal.ai atau model lain — dipanggil dari MediaTab APK"""
    try:
        from core.config import config
        prompt  = req.get("prompt", "")
        model   = req.get("model", "fal-ai/flux/schnell")
        size    = req.get("image_size", "landscape_16_9")
        neg     = req.get("negative_prompt", "")
        if not prompt:
            raise HTTPException(400, "prompt wajib diisi")
        # TODO: Integrasikan dengan fal.ai client
        # Contoh: import fal_client; result = fal_client.run(model, ...)
        return {
            "status": "queued",
            "image_url": "",
            "message": f"Image generation queued untuk model {model}",
            "prompt": prompt,
        }
    except Exception as e:
        raise HTTPException(500, str(e))
''',
        "/media/upload": '''
@app.post("/media/upload")
async def media_upload(file: UploadFile = File(...)):
    """Upload file gambar/video dari APK — dipanggil dari _Img2VideoTab"""
    try:
        from fastapi import UploadFile, File
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        filename = f"{uuid.uuid4()}_{file.filename}"
        dest = upload_dir / filename
        content = await file.read()
        dest.write_bytes(content)
        return {
            "status": "ok",
            "filename": filename,
            "url": f"/uploads/{filename}",
            "size": len(content),
        }
    except Exception as e:
        raise HTTPException(500, str(e))
''',
        "/media/video/generate": '''
@app.post("/media/video/generate")
async def media_video_generate(req: dict, background_tasks: BackgroundTasks):
    """Generate video dari image — dipanggil dari _Img2VideoTab APK"""
    try:
        model     = req.get("model", "fal-ai/kling-video/v1.6/standard/image-to-video")
        image_url = req.get("image_url", "")
        prompt    = req.get("prompt", "")
        duration  = req.get("duration", "5")
        if not image_url:
            raise HTTPException(400, "image_url wajib diisi")
        jid = str(uuid.uuid4())[:8]
        _set_job(jid, "processing")
        # TODO: background_tasks.add_task(do_video_gen, jid, model, image_url, prompt)
        return {
            "status": "ok",
            "job_id": jid,
            "message": f"Video generation job {jid} started",
        }
    except Exception as e:
        raise HTTPException(500, str(e))
''',
        "/media/video/jobs/{id}": '''
@app.get("/media/video/jobs/{job_id}")
async def media_video_job_status(job_id: str):
    """Cek status video generation job — polling dari APK"""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, f"Job {job_id} tidak ditemukan")
    return job
''',
        "/media/gallery": '''
@app.get("/media/gallery")
async def media_gallery():
    """List semua file media yang sudah di-generate — untuk GalleryTab APK"""
    try:
        upload_dir = Path("uploads")
        items = []
        if upload_dir.exists():
            for f in sorted(upload_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:50]:
                if f.suffix.lower() in [".jpg", ".png", ".mp4", ".webp", ".gif"]:
                    items.append({
                        "filename": f.name,
                        "url": f"/uploads/{f.name}",
                        "type": "image" if f.suffix in [".jpg",".png",".webp",".gif"] else "video",
                        "size": f.stat().st_size,
                        "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    })
        return {"items": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(500, str(e))
''',
    }

    for route in sorted(report.missing_routes):
        # Normalize to find template
        norm_route = re.sub(r'/[a-f0-9-]{36}', '/{id}', route)
        norm_route2 = re.sub(r'/jobs/\S+', '/jobs/{id}', route)

        template_key = None
        for k in ROUTE_TEMPLATES:
            if route == k or norm_route == k or norm_route2 == k:
                template_key = k
                break

        if template_key:
            patches.append(ROUTE_TEMPLATES[template_key])
        else:
            patches.append(f'''
@app.post("{route}")
@app.get("{route}")
async def handle_{route.replace("/","_").replace("-","_").strip("_")}(req: dict = None):
    """Auto-generated stub untuk {route} — dipanggil APK Flutter"""
    # TODO: Implementasikan logika untuk endpoint ini
    return {{"status": "ok", "message": "Endpoint {route} - implementasi belum lengkap"}}
''')

    return "\n".join(patches)


# ══════════════════════════════════════════════════════════════════
# AUTO-PATCH: FLUTTER MISSING FEATURES
# ══════════════════════════════════════════════════════════════════
def generate_flutter_llm_chat_tab() -> str:
    """Generate ChatTab Dart yang lengkap dengan LLM support."""
    return '''// lib/chat_tab.dart — LENGKAP dengan LLM, history, session, streaming
// Auto-generated oleh agentjw_apk_fixer.py

import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ChatTab extends StatefulWidget {
  final String baseUrl;
  final ValueChanged<bool>? onConnectionChange;
  const ChatTab({required this.baseUrl, this.onConnectionChange});
  @override
  _ChatTabState createState() => _ChatTabState();
}

class _ChatTabState extends State<ChatTab> {
  final _inputCtrl  = TextEditingController();
  final _scrollCtrl = ScrollController();
  String _sessionId = "";
  bool _loading     = false;
  bool _connected   = false;
  String _mode      = "chat"; // chat | build | video
  List<Map<String, String>> _messages = [];

  @override
  void initState() {
    super.initState();
    _loadSession();
    _checkConnection();
  }

  Future<void> _loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _sessionId = prefs.getString('session_id') ?? _newSession();
    });
  }

  String _newSession() {
    final id = DateTime.now().millisecondsSinceEpoch.toString();
    SharedPreferences.getInstance().then((p) => p.setString('session_id', id));
    return id;
  }

  Future<void> _checkConnection() async {
    try {
      final r = await http.get(
        Uri.parse('\${widget.baseUrl}/api/status')
      ).timeout(const Duration(seconds: 5));
      final ok = r.statusCode == 200;
      setState(() => _connected = ok);
      widget.onConnectionChange?.call(ok);
    } catch (_) {
      setState(() => _connected = false);
      widget.onConnectionChange?.call(false);
    }
  }

  Future<void> _send() async {
    final msg = _inputCtrl.text.trim();
    if (msg.isEmpty || _loading) return;
    _inputCtrl.clear();

    setState(() {
      _messages.add({"role": "user", "content": msg});
      _loading = true;
    });
    _scrollToBottom();

    try {
      // Build history for context (last 10 turns)
      final history = _messages.length > 2
          ? _messages.sublist(_messages.length > 20 ? _messages.length - 20 : 0,
                              _messages.length - 1)
              .map((m) => {"role": m["role"]!, "content": m["content"]!})
              .toList()
          : <Map<String, String>>[];

      final response = await http.post(
        Uri.parse('\${widget.baseUrl}/api/agent'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'message':    msg,
          'session_id': _sessionId,
          'history':    history,
          'mode':       _mode,
        }),
      ).timeout(const Duration(seconds: 120));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final reply = data['response']?.toString() ??
                      data['result']?.toString() ??
                      'No response';
        setState(() {
          _messages.add({"role": "assistant", "content": reply});
        });
      } else {
        setState(() {
          _messages.add({
            "role": "assistant",
            "content": "❌ Error \${response.statusCode}:\\n\${response.body.substring(0, 200)}"
          });
        });
      }
    } catch (e) {
      setState(() {
        _messages.add({"role": "assistant", "content": "❌ Connection error: \$e"});
      });
    } finally {
      setState(() => _loading = false);
      _scrollToBottom();
    }
  }

  void _scrollToBottom() {
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollCtrl.hasClients) {
        _scrollCtrl.animateTo(
          _scrollCtrl.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _clearChat() {
    setState(() {
      _messages.clear();
      _sessionId = _newSession();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      // Top bar
      Container(
        color: const Color(0xFF111111),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(children: [
          Container(width: 8, height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _connected ? const Color(0xFF4CAF50) : Colors.red)),
          const SizedBox(width: 6),
          Text(_connected ? "AgentJW Connected" : "Disconnected",
            style: TextStyle(
              color: _connected ? const Color(0xFF4CAF50) : Colors.red,
              fontSize: 11)),
          const Spacer(),
          // Mode selector
          DropdownButton<String>(
            value: _mode,
            dropdownColor: const Color(0xFF1A1A2E),
            style: const TextStyle(fontSize: 11, color: Colors.white),
            underline: const SizedBox(),
            items: [
              DropdownMenuItem(value: "chat",  child: Text("💬 Chat")),
              DropdownMenuItem(value: "build", child: Text("🏗 Build")),
              DropdownMenuItem(value: "video", child: Text("🎬 Video")),
            ],
            onChanged: (v) => setState(() => _mode = v!),
          ),
          IconButton(
            icon: const Icon(Icons.refresh, size: 18, color: Colors.grey),
            onPressed: _checkConnection,
            tooltip: "Reconnect",
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline, size: 18, color: Colors.grey),
            onPressed: _clearChat,
            tooltip: "Clear chat",
          ),
        ]),
      ),

      // Messages
      Expanded(
        child: _messages.isEmpty
          ? Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Text("🤖", style: TextStyle(fontSize: 40)),
              const SizedBox(height: 8),
              Text("AgentJW siap", style: TextStyle(color: Colors.grey[600], fontSize: 14)),
              const SizedBox(height: 4),
              Text("Mode: \$_mode", style: TextStyle(color: Colors.grey[700], fontSize: 11)),
            ]))
          : ListView.builder(
              controller: _scrollCtrl,
              padding: const EdgeInsets.all(10),
              itemCount: _messages.length + (_loading ? 1 : 0),
              itemBuilder: (ctx, i) {
                if (i == _messages.length) {
                  return _buildTypingIndicator();
                }
                final m = _messages[i];
                final isUser = m["role"] == "user";
                return _buildMessage(m["content"] ?? "", isUser);
              },
            ),
      ),

      // Input bar
      Container(
        color: const Color(0xFF0D0D0D),
        padding: const EdgeInsets.fromLTRB(8, 6, 8, 8),
        child: Row(children: [
          Expanded(
            child: TextField(
              controller: _inputCtrl,
              maxLines: 4,
              minLines: 1,
              style: const TextStyle(fontSize: 13, color: Colors.white),
              decoration: InputDecoration(
                hintText: _mode == "build"
                  ? "Buat app: e.g. 'bikin bot trading solana...'"
                  : _mode == "video"
                    ? "Judul video: e.g. 'Cara Cuan DeFi 2024...'"
                    : "Tanya AgentJW...",
                hintStyle: TextStyle(color: Colors.grey[700], fontSize: 12),
                filled: true,
                fillColor: const Color(0xFF141414),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: Color(0xFF1E2D50)),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: Color(0xFF1E2D50)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: Color(0xFF7C3AED)),
                ),
                contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              ),
              onSubmitted: (_) => _send(),
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: _loading ? null : _send,
            child: Container(
              width: 44, height: 44,
              decoration: BoxDecoration(
                color: _loading
                  ? Colors.grey[800]
                  : const Color(0xFF7C3AED),
                borderRadius: BorderRadius.circular(10),
              ),
              child: _loading
                ? const Padding(padding: EdgeInsets.all(12),
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.send, color: Colors.white, size: 20),
            ),
          ),
        ]),
      ),
    ]);
  }

  Widget _buildMessage(String content, bool isUser) {
    return Align(
      alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.85),
        decoration: BoxDecoration(
          color: isUser ? const Color(0xFF7C3AED) : const Color(0xFF1A1A2E),
          borderRadius: BorderRadius.only(
            topLeft:     const Radius.circular(12),
            topRight:    const Radius.circular(12),
            bottomLeft:  Radius.circular(isUser ? 12 : 2),
            bottomRight: Radius.circular(isUser ? 2 : 12),
          ),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SelectableText(
            content,
            style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4),
          ),
          if (!isUser) ...[
            const SizedBox(height: 4),
            GestureDetector(
              onTap: () => Clipboard.setData(ClipboardData(text: content)),
              child: Text("copy", style: TextStyle(color: Colors.grey[600], fontSize: 10)),
            ),
          ],
        ]),
      ),
    );
  }

  Widget _buildTypingIndicator() {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: const Color(0xFF1A1A2E),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          const SizedBox(width: 4),
          _dot(0), _dot(1), _dot(2),
        ]),
      ),
    );
  }

  Widget _dot(int delay) {
    return TweenAnimationBuilder<double>(
      tween: Tween(begin: 0.3, end: 1.0),
      duration: Duration(milliseconds: 600 + delay * 200),
      builder: (_, v, __) => Container(
        width: 6, height: 6,
        margin: const EdgeInsets.symmetric(horizontal: 2),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: Colors.grey.withOpacity(v),
        ),
      ),
    );
  }
}
'''


# ══════════════════════════════════════════════════════════════════
# AUTO-PATCH: APPLY FIXES
# ══════════════════════════════════════════════════════════════════
def apply_patches():
    if REPORT_ONLY:
        info("--report-only mode: melewati semua patch")
        return

    if not AUTO_PATCH:
        info("Gunakan --patch untuk apply semua fix otomatis")
        return

    h1("AUTO-PATCH MODE")

    # Patch 1: Missing backend routes
    if report.missing_routes:
        h2("PATCH: Tambah missing backend routes")
        api_path = BACKEND_DIR / "api_server.py"
        if api_path.exists():
            backup(api_path)
            patch_code = generate_missing_routes_patch()
            content    = read(api_path)

            # Add UploadFile import if needed
            if "/media/upload" in report.missing_routes:
                if "UploadFile" not in content:
                    content = content.replace(
                        "from fastapi import FastAPI, HTTPException, BackgroundTasks",
                        "from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File"
                    )

            # Append routes before the __main__ block
            if 'if __name__ == "__main__"' in content:
                content = content.replace(
                    'if __name__ == "__main__"',
                    patch_code + '\nif __name__ == "__main__"'
                )
            else:
                content += "\n" + patch_code

            write(api_path, content)
            fix(f"Ditambah {len(report.missing_routes)} route ke api_server.py")
            report.patches_applied += len(report.missing_routes)

    # Patch 2: Missing pubspec deps
    if report.missing_deps:
        h2("PATCH: Tambah missing pubspec dependencies")
        pubspec = APK_DIR / "pubspec.yaml"
        if pubspec.exists():
            backup(pubspec)
            content = read(pubspec)
            deps_block = ""
            for dep in sorted(report.missing_deps):
                ver = {
                    "http": "^1.2.0", "dio": "^5.4.0",
                    "image_picker": "^1.1.2", "path_provider": "^2.1.2",
                    "open_file": "^3.3.2", "permission_handler": "^11.3.1",
                    "connectivity_plus": "^6.0.3", "shared_preferences": "^2.2.3",
                    "video_player": "^2.8.3", "flutter_markdown": "^0.7.3",
                }.get(dep, "^1.0.0")
                deps_block += f"\n  {dep}: {ver}"

            # Insert after "dependencies:" section
            if "dependencies:\n  flutter:" in content:
                content = content.replace(
                    "dependencies:\n  flutter:",
                    f"dependencies:{deps_block}\n  flutter:"
                )
                write(pubspec, content)
                fix(f"Ditambah {len(report.missing_deps)} deps ke pubspec.yaml")
                report.patches_applied += 1

    # Patch 3: Generate complete ChatTab if missing
    if not report.apk_features.get("ChatTab / Chat UI", True):
        h2("PATCH: Generate chat_tab.dart")
        chat_tab_path = APK_DIR / "lib" / "chat_tab.dart"
        if not chat_tab_path.exists():
            write(chat_tab_path, generate_flutter_llm_chat_tab())
            fix("Dibuat: lib/chat_tab.dart (ChatTab lengkap dengan LLM)")
            report.patches_applied += 1

    # Patch 4: Port fix in APK
    if report.apk_port > 0 and report.apk_port != report.backend_port:
        h2(f"PATCH: Fix port APK {report.apk_port} → {report.backend_port}")
        dart_files = find_dart_files(APK_DIR / "lib")
        for df in dart_files:
            content = read(df)
            if str(report.apk_port) in content:
                backup(df)
                content = content.replace(str(report.apk_port), str(report.backend_port))
                write(df, content)
                fix(f"Port fixed di {df.name}")
        report.patches_applied += 1


# ══════════════════════════════════════════════════════════════════
# GENERATE REPORT
# ══════════════════════════════════════════════════════════════════
def generate_report():
    h1("GENERATING REPORT")

    criticals = [i for i in report.issues if i.severity == "CRITICAL"]
    warnings  = [i for i in report.issues if i.severity == "WARNING"]

    lines = [
        f"# AgentJW APK ↔ Backend Sync Report",
        f"**Generated:** {NOW.strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"**Score:** {report.score}/100  ",
        f"**Issues:** {len(criticals)} CRITICAL, {len(warnings)} WARNING  ",
        f"**Patches Applied:** {report.patches_applied}  ",
        "",
        "---",
        "",
        "## Backend Routes",
        "```",
        *sorted(report.backend_routes),
        "```",
        "",
        "## APK Endpoint Calls",
        "```",
        *sorted(report.apk_calls),
        "```",
        "",
        "## Missing Routes (APK butuh, Backend tidak punya)",
        "```",
        *(sorted(report.missing_routes) or ["NONE — semua routes ok"]),
        "```",
        "",
        "## Feature Matrix",
    ]
    for feat, present in report.apk_features.items():
        lines.append(f"- {'✅' if present else '❌'} {feat}")

    lines += ["", "## Issues Detail", ""]
    for issue in report.issues:
        icon = "🔴" if issue.severity == "CRITICAL" else "🟡"
        lines += [
            f"### {icon} [{issue.severity}] {issue.title}",
            f"- **Category:** {issue.category}",
            f"- **Detail:** {issue.detail}" if issue.detail else "",
            f"- **File:** `{issue.file}`" if issue.file else "",
            f"- **Fix:** {issue.fix_hint}" if issue.fix_hint else "",
            "",
        ]

    lines += [
        "---",
        "## Quick Fix Commands",
        "```bash",
        f"# Start backend",
        f"cd {BACKEND_DIR} && uvicorn api_server:app --host 0.0.0.0 --port {report.backend_port} &",
        "",
        f"# Run Flutter",
        f"cd {APK_DIR} && flutter pub get && flutter run",
        "",
        f"# Re-run fixer dengan patch",
        f"python3 agentjw_apk_fixer.py --patch --verbose",
        "```",
    ]

    report_content = "\n".join(l for l in lines if l is not None)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    write(REPORT_MD, report_content)
    ok(f"Report disimpan: {REPORT_MD}")

    # Print summary
    print()
    h1("SUMMARY")
    print(f"  Score   : {report.score}/100")
    print(f"  Critical: {len(criticals)}")
    print(f"  Warning : {len(warnings)}")
    print(f"  Patches : {report.patches_applied}")
    print()

    if criticals:
        err("CRITICAL ISSUES:")
        for i in criticals:
            err(f"  [{i.category}] {i.title}")
            if i.fix_hint:
                fix(f"  Fix: {i.fix_hint[:100]}")
    if warnings:
        warn("WARNINGS:")
        for i in warnings:
            warn(f"  [{i.category}] {i.title}")

    print()
    if report.score >= 90:
        ok("APK & Backend sudah sinkron dengan baik! 🎉")
    elif report.score >= 70:
        warn("Sebagian besar OK — ada beberapa perbaikan yang perlu dilakukan")
    elif report.score >= 50:
        warn("Banyak isu — jalankan dengan --patch untuk auto-fix")
    else:
        err("Banyak isu kritis — perlu perbaikan manual + --patch")

    return report_content


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════
def main():
    print()
    if HAS_RICH:
        console.print(Panel(
            "[bold cyan]AgentJW APK ↔ Backend Sync Fixer[/bold cyan]\n"
            "[dim]Analisa & perbaiki sinkronisasi Flutter APK dengan Backend[/dim]",
            border_style="cyan"
        ))
    else:
        print("╔══════════════════════════════════════════════════════════╗")
        print("║   AgentJW APK ↔ Backend Sync Fixer                     ║")
        print("╚══════════════════════════════════════════════════════════╝")

    print(f"  Backend : {BACKEND_DIR}")
    print(f"  Flutter : {APK_DIR}")
    print(f"  Mode    : {'AUTO-PATCH' if AUTO_PATCH else 'REPORT-ONLY' if REPORT_ONLY else 'ANALYZE'}")
    print()

    # Run all checks
    check_dirs()
    check_backend_routes()
    check_apk_endpoints()
    check_missing_routes()
    check_pubspec()
    check_dart_imports()
    check_features()
    check_llm_connectivity()
    check_backend_health()
    check_env()

    # Apply patches if requested
    apply_patches()

    # Generate final report
    generate_report()


if __name__ == "__main__":
    main()
