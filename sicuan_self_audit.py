#!/usr/bin/env python3
"""
sicuan_self_audit.py
=====================
SiCuan menganalisis kodenya sendiri.

Tahap 1 (mekanis/AST)   : scan sicuan/, agents/, core/, mcp/ untuk duplikat
                           logic, broken import, orphan file, class divergen,
                           endpoint collision — sama persis logic-nya dengan
                           codebase_audit.py, tapi dipersempit & dipakai
                           sebagai INPUT untuk tahap 2.

Tahap 2 (penalaran LLM) : kirim temuan tahap 1 (per kategori, dibatch supaya
                           tidak kepanjangan) ke OpenRouter. LLM diminta:
                             - menilai severity yang REALISTIS (bukan
                               semua "broken import" itu fatal — tergantung
                               apakah file itu kepake di runtime)
                             - membedakan "orphan karena emang mati" vs
                               "orphan karena dynamic import / belum
                               disambung ke pipeline utama"
                             - kasih rekomendasi aksi konkret per temuan
                           LLM TIDAK diberi akses untuk mengubah file apapun.
                           Ini murni read+reason, bukan auto-fix.

Tahap 3 (output)         : hasil gabungan (temuan mentah + interpretasi LLM)
                           ditulis sebagai JSON terstruktur ke
                           sicuan/knowledge/self_audit.json, supaya bisa
                           dibaca SiCuan sendiri lewat knowledge base-nya
                           di percakapan berikutnya — termasuk kalau brain
                           LLM-nya nanti diganti (Claude/GPT/Kimi/dll),
                           karena ini hanya data JSON biasa, bukan terikat
                           ke satu model tertentu.

PENTING — TIDAK ADA FILE YANG DIUBAH/DIHAPUS OLEH SCRIPT INI.
Ini murni read-only analysis + report generation. Keputusan eksekusi
(hapus/refactor/gabung file) tetap di tangan Mas, bukan otomatis.

Environment yang dibutuhkan (taruh di .env atau export manual):
    OPENROUTER_API_KEY=sk-or-...
    OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct   (default; bisa diganti)

Penggunaan:
    python3 sicuan_self_audit.py [project_root]

    project_root default: direktori tempat script ini berada (asumsinya
    ditaruh di ~/agentjw/sicuan_self_audit.py)

Output:
    <project_root>/sicuan/knowledge/self_audit.json   (machine-readable)
    <project_root>/sicuan/knowledge/self_audit.md      (human-readable)
"""

import ast
import hashlib
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

SCOPE_PREFIXES = ["sicuan", "agents", "core", "mcp"]

DEFAULT_EXCLUDES = {
    "venv", ".venv", "__pycache__", ".git", "node_modules",
    "backups", "backup_video_patch", "archive", "archive_for_review",
    "sicuan_audit_report", "reports", "logs", ".pytest_cache",
    "projects", "agentjw_upgrade", "uploads",
}

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "qwen/qwen-2.5-72b-instruct"

# Fallback chain: kalau model utama gagal (rate-limited, provider bermasalah,
# dst), coba model berikutnya di daftar ini secara berurutan. Ini membantu
# karena beberapa model di OpenRouter di-routing ke banyak provider upstream
# yang reliabilitasnya bisa naik-turun (terutama model gratis/murah).
FALLBACK_MODELS = [
    "qwen/qwen-2.5-72b-instruct",
    "qwen/qwen-2.5-32b-instruct",
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-haiku",
]

ROUTE_DECORATOR_RE = re.compile(r"(route|get|post|put|delete|patch|websocket)$", re.IGNORECASE)


def load_env_file(root: Path):
    """Minimal .env loader (no external dependency on python-dotenv)."""
    env_path = root / ".env"
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val
    except Exception as e:
        print(f"[!] Gagal membaca .env: {e}", file=sys.stderr)


# --------------------------------------------------------------------------
# Data structures (subset of codebase_audit.py, kept self-contained)
# --------------------------------------------------------------------------

@dataclass
class FuncInfo:
    file: str
    qualname: str
    name: str
    lineno: int
    end_lineno: int
    is_method: bool
    body_hash: str
    body_hash_strict: str
    source_lines: int


@dataclass
class ClassInfo:
    file: str
    name: str
    lineno: int
    methods: list = field(default_factory=list)


@dataclass
class ImportInfo:
    file: str
    lineno: int
    module: Optional[str]
    names: list
    is_relative: bool
    raw: str


@dataclass
class RouteInfo:
    file: str
    lineno: int
    method_name: str
    path: Optional[str]
    func_name: str


# --------------------------------------------------------------------------
# AST normalization for structural hashing
# --------------------------------------------------------------------------

class Normalizer(ast.NodeTransformer):
    def __init__(self, blank_literals: bool):
        self.blank_literals = blank_literals
        self.name_map = {}
        self.counter = 0

    def _g(self, original):
        if original not in self.name_map:
            self.name_map[original] = f"_v{self.counter}"
            self.counter += 1
        return self.name_map[original]

    def visit_Name(self, node):
        node.id = self._g(node.id)
        return node

    def visit_arg(self, node):
        node.arg = self._g(node.arg)
        return node

    def visit_FunctionDef(self, node):
        node.name = "_fn"
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node):
        node.name = "_fn"
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        self.generic_visit(node)
        node.attr = self._g(node.attr)
        return node

    def visit_Constant(self, node):
        if self.blank_literals:
            if isinstance(node.value, str):
                node.value = "_STR_"
            elif isinstance(node.value, (int, float)):
                node.value = 0
        return node


def hash_function_body(node, blank_literals: bool) -> str:
    try:
        body_copy = ast.parse(ast.unparse(node))
    except Exception:
        return ""
    Normalizer(blank_literals=blank_literals).visit(body_copy)
    try:
        dumped = ast.dump(body_copy, annotate_fields=False)
    except Exception:
        return ""
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# File discovery & parsing
# --------------------------------------------------------------------------

def discover_py_files(root: Path, excludes: set) -> list:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in excludes and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".py"):
                files.append(Path(dirpath) / fn)
    return files


def module_dotted_path(file: Path, root: Path) -> str:
    rel = file.relative_to(root).with_suffix("")
    parts = rel.parts
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def in_scope(relpath: str, scope_prefixes) -> bool:
    return any(relpath == p or relpath.startswith(p.rstrip("/") + "/") for p in scope_prefixes)


def parse_file(file: Path, root: Path):
    functions, classes, imports, routes = [], [], [], []
    try:
        src = file.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src, filename=str(file))
    except Exception as e:
        return functions, classes, imports, routes, str(e)

    relfile = str(file.relative_to(root))

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.class_stack = []

        def visit_ClassDef(self, node):
            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes.append(ClassInfo(file=relfile, name=node.name, lineno=node.lineno, methods=methods))
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

        def _handle_func(self, node):
            qualname = f"{self.class_stack[-1]}.{node.name}" if self.class_stack else node.name
            end_lineno = getattr(node, "end_lineno", node.lineno)
            functions.append(FuncInfo(
                file=relfile, qualname=qualname, name=node.name,
                lineno=node.lineno, end_lineno=end_lineno,
                is_method=bool(self.class_stack),
                body_hash=hash_function_body(node, blank_literals=True),
                body_hash_strict=hash_function_body(node, blank_literals=False),
                source_lines=end_lineno - node.lineno + 1,
            ))
            for dec in node.decorator_list:
                dec_func = dec.func if isinstance(dec, ast.Call) else dec
                attr_name = dec_func.attr if isinstance(dec_func, ast.Attribute) else (
                    dec_func.id if isinstance(dec_func, ast.Name) else None)
                if attr_name and ROUTE_DECORATOR_RE.search(attr_name):
                    path_arg = None
                    if isinstance(dec, ast.Call) and dec.args:
                        first = dec.args[0]
                        if isinstance(first, ast.Constant) and isinstance(first.value, str):
                            path_arg = first.value
                    routes.append(RouteInfo(file=relfile, lineno=node.lineno,
                                             method_name=attr_name, path=path_arg, func_name=node.name))
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            self._handle_func(node)

        def visit_AsyncFunctionDef(self, node):
            self._handle_func(node)

        def visit_Import(self, node):
            for alias in node.names:
                imports.append(ImportInfo(file=relfile, lineno=node.lineno, module=None,
                                           names=[alias.name], is_relative=False,
                                           raw=f"import {alias.name}"))

        def visit_ImportFrom(self, node):
            mod = node.module or ""
            names = [a.name for a in node.names]
            imports.append(ImportInfo(file=relfile, lineno=node.lineno, module=mod, names=names,
                                       is_relative=(node.level or 0) > 0,
                                       raw=f"from {'.' * (node.level or 0)}{mod} import {', '.join(names)}"))

    Visitor().visit(tree)
    return functions, classes, imports, routes, None


# --------------------------------------------------------------------------
# Analysis passes
# --------------------------------------------------------------------------

def find_duplicate_functions(all_funcs, min_lines=3):
    strict_groups = defaultdict(list)
    for f in all_funcs:
        if f.source_lines >= min_lines and f.body_hash_strict:
            strict_groups[f.body_hash_strict].append(f)
    exact = [m for m in strict_groups.values() if len(m) > 1 and
             (len({x.file for x in m}) > 1 or len({x.qualname for x in m}) > 1)]

    loose_groups = defaultdict(list)
    for f in all_funcs:
        if f.source_lines >= min_lines and f.body_hash:
            loose_groups[f.body_hash].append(f)
    structural = []
    for m in loose_groups.values():
        if len(m) > 1 and (len({x.file for x in m}) > 1 or len({x.qualname for x in m}) > 1):
            already = any({x.qualname for x in m} == {e.qualname for e in g} for g in exact)
            if not already:
                structural.append(m)
    return exact, structural


def find_same_name_different_body(all_funcs):
    by_name = defaultdict(list)
    for f in all_funcs:
        by_name[f.name].append(f)
    out = []
    for name, members in by_name.items():
        if name.startswith("__") and name.endswith("__"):
            continue
        if len({m.file for m in members}) < 2:
            continue
        if len({m.body_hash for m in members}) > 1:
            out.append((name, members))
    return out


def find_same_class_diverged(all_classes):
    by_name = defaultdict(list)
    for c in all_classes:
        by_name[c.name].append(c)
    out = []
    for name, members in by_name.items():
        if len({m.file for m in members}) < 2:
            continue
        if len({frozenset(m.methods) for m in members}) > 1:
            out.append((name, members))
    return out


def build_module_index(files, root):
    return {module_dotted_path(f, root): f for f in files}


def resolve_import(imp, file, root, module_index):
    target = imp.names[0] if imp.module is None else imp.module
    if imp.is_relative:
        base_parts = list(file.relative_to(root).parts[:-1])
        target_parts = target.split(".") if target else []
        candidate = ".".join(base_parts + target_parts) if target else ".".join(base_parts)
        if candidate in module_index:
            return True
        return any(mp == candidate or mp.startswith(candidate + ".") for mp in module_index)
    top_level_dirs = {p.name for p in root.iterdir() if p.is_dir()}
    first_seg = target.split(".")[0]
    if first_seg not in top_level_dirs and first_seg not in {m.split(".")[0] for m in module_index}:
        return None
    if target in module_index:
        return True
    return any(mp == target or mp.startswith(target + ".") for mp in module_index)


def find_broken_imports(all_imports, root, module_index):
    out = []
    for imp in all_imports:
        if resolve_import(imp, root / imp.file, root, module_index) is False:
            out.append(imp)
    return out


def has_main_guard_or_cli_entry(file: Path) -> bool:
    try:
        src = file.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    if "__name__" in src and "__main__" in src:
        return True
    return any(sig in src for sig in (".run(", "uvicorn.run", "asyncio.run(", "app.run_polling", "Bot(token"))


def detect_dynamic_loading(file: Path) -> list:
    """Detect signals of dynamic import (importlib, __import__, getattr on
    sys.modules, plugin-style registries) — these make a file LOOK orphan
    to static AST analysis even though it's actually used at runtime."""
    try:
        src = file.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    signals = []
    patterns = {
        "importlib.import_module": r"importlib\.import_module",
        "__import__()": r"__import__\(",
        "getattr(sys.modules": r"getattr\(\s*sys\.modules",
        "pkgutil dynamic discovery": r"pkgutil\.(iter_modules|walk_packages)",
        "exec()/eval() dynamic exec": r"\b(exec|eval)\(",
    }
    for label, pat in patterns.items():
        if re.search(pat, src):
            signals.append(label)
    return signals


def find_orphan_files(files, all_imports, root):
    imported_modules = set()
    for imp in all_imports:
        if imp.module:
            imported_modules.add(imp.module)
            parts = imp.module.split(".")
            for i in range(1, len(parts) + 1):
                imported_modules.add(".".join(parts[:i]))
        for n in imp.names:
            imported_modules.add(n)

    orphans, likely_entrypoints = [], []
    entrypoint_hints = {"main", "app", "server", "manage", "wsgi", "asgi", "setup",
                         "run", "cli", "telegram_bot", "bot", "start_sicuan"}
    for f in files:
        dotted = module_dotted_path(f, root)
        base_name = f.stem
        if base_name.startswith("test_") or base_name.startswith("__init__"):
            continue
        if dotted in imported_modules or base_name in imported_modules:
            continue
        if any(dotted == m or dotted.endswith("." + m) or m.endswith("." + dotted) for m in imported_modules):
            continue
        if base_name in entrypoint_hints or has_main_guard_or_cli_entry(f):
            likely_entrypoints.append(f)
            continue
        orphans.append(f)
    return orphans, likely_entrypoints


def find_endpoint_collisions(all_routes):
    by_path = defaultdict(list)
    for r in all_routes:
        if r.path:
            by_path[r.path].append(r)
    return {p: rs for p, rs in by_path.items() if len({(r.file, r.func_name) for r in rs}) > 1}


# --------------------------------------------------------------------------
# Run full AST analysis, filtered to scope
# --------------------------------------------------------------------------

def run_static_analysis(root: Path):
    files = discover_py_files(root, DEFAULT_EXCLUDES)
    all_funcs, all_classes, all_imports, all_routes = [], [], [], []
    parse_errors = []
    for f in files:
        funcs, classes, imports, routes, err = parse_file(f, root)
        if err:
            parse_errors.append((str(f.relative_to(root)), err))
            continue
        all_funcs.extend(funcs)
        all_classes.extend(classes)
        all_imports.extend(imports)
        all_routes.extend(routes)

    module_index = build_module_index(files, root)
    exact_dupes, structural_dupes = find_duplicate_functions(all_funcs)
    name_clashes = find_same_name_different_body(all_funcs)
    class_diverged = find_same_class_diverged(all_classes)
    broken_imports = find_broken_imports(all_imports, root, module_index)
    orphans, likely_entrypoints = find_orphan_files(files, all_imports, root)
    endpoint_collisions = find_endpoint_collisions(all_routes)

    def keep(member_list):
        return any(in_scope(m.file, SCOPE_PREFIXES) for m in member_list)

    exact_dupes = [g for g in exact_dupes if keep(g)]
    structural_dupes = [g for g in structural_dupes if keep(g)]
    name_clashes = [(n, m) for n, m in name_clashes if keep(m)]
    class_diverged = [(n, m) for n, m in class_diverged if keep(m)]
    broken_imports = [i for i in broken_imports if in_scope(i.file, SCOPE_PREFIXES)]
    orphans = [f for f in orphans if in_scope(str(f.relative_to(root)), SCOPE_PREFIXES)]
    likely_entrypoints = [f for f in likely_entrypoints if in_scope(str(f.relative_to(root)), SCOPE_PREFIXES)]
    endpoint_collisions = {p: rs for p, rs in endpoint_collisions.items()
                            if any(in_scope(r.file, SCOPE_PREFIXES) for r in rs)}

    # Detect project-wide dynamic-loading usage. This matters because a file
    # can look "orphan" to static AST analysis while actually being loaded
    # at runtime via importlib/getattr/plugin-registry patterns elsewhere.
    # We report this as PROJECT-WIDE CONTEXT (not per-file), since static
    # analysis can't reliably trace which dynamic call targets which file.
    dynamic_loaders = []
    for f in files:
        if in_scope(str(f.relative_to(root)), SCOPE_PREFIXES):
            signals = detect_dynamic_loading(f)
            if signals:
                dynamic_loaders.append({"file": str(f.relative_to(root)), "signals": signals})

    orphan_details = []
    for f in orphans:
        orphan_details.append({"file": str(f.relative_to(root))})

    return {
        "scanned_files": len(files),
        "scanned_functions": len(all_funcs),
        "parse_errors": parse_errors,
        "exact_duplicates": [[asdict(m) for m in g] for g in exact_dupes],
        "structural_duplicates": [[asdict(m) for m in g] for g in structural_dupes],
        "name_clashes": [{"name": n, "members": [asdict(m) for m in m]} for n, m in name_clashes],
        "class_diverged": [{"name": n, "members": [asdict(m) for m in m]} for n, m in class_diverged],
        "broken_imports": [asdict(i) for i in broken_imports],
        "orphan_files": orphan_details,
        "dynamic_loading_context": dynamic_loaders,
        "likely_entrypoints": [str(f.relative_to(root)) for f in likely_entrypoints],
        "endpoint_collisions": {p: [asdict(r) for r in rs] for p, rs in endpoint_collisions.items()},
    }


# --------------------------------------------------------------------------
# OpenRouter call
# --------------------------------------------------------------------------

def _single_model_request(prompt: str, api_key: str, model: str, timeout: int = 120):
    """One HTTP call attempt against a specific model. Raises on failure."""
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": (
                "Kamu adalah code auditor senior yang membantu SiCuan (AI software "
                "engineering assistant) menganalisis kodenya SENDIRI. Tugasmu: baca "
                "temuan static-analysis mentah (AST-based) dan beri penilaian yang "
                "REALISTIS, bukan alarmis. Bedakan dead code sungguhan vs modul yang "
                "'orphan' karena dynamic import/belum disambung ke pipeline utama. "
                "Jawab HANYA dalam format JSON valid, tanpa markdown fences, tanpa "
                "teks pembuka/penutup."
            )},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_URL, data=body, method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://sicuan.local/self-audit",
            "X-Title": "SiCuan Self Audit",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]


def call_openrouter(prompt: str, api_key: str, model: str, max_retries: int = 2) -> str:
    """Try `model` first (with max_retries attempts + backoff). If it keeps
    failing, fall back to the next model in FALLBACK_MODELS (skipping the
    one we already tried), so a single flaky/overloaded provider doesn't
    abort the whole audit. Returns the raw text content from whichever
    model succeeded first."""
    # Build the ordered list of models to try: requested model first,
    # then any FALLBACK_MODELS not already equal to it.
    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]

    last_err = None
    for m_idx, current_model in enumerate(models_to_try):
        attempts_for_this_model = max_retries if m_idx == 0 else 1
        for attempt in range(1, attempts_for_this_model + 1):
            try:
                result = _single_model_request(prompt, api_key, current_model)
                if m_idx > 0:
                    print(f"[*] Berhasil pakai model fallback: {current_model}", file=sys.stderr)
                return result
            except urllib.error.HTTPError as e:
                last_err = f"HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}"
            except Exception as e:
                last_err = str(e)
            print(f"[!] Model '{current_model}' gagal (percobaan {attempt}/{attempts_for_this_model}): {last_err}",
                  file=sys.stderr)
            if attempt < attempts_for_this_model:
                time.sleep(2 * attempt)
        if m_idx < len(models_to_try) - 1:
            print(f"[*] Beralih ke model fallback berikutnya...", file=sys.stderr)

    raise RuntimeError(
        f"Semua model gagal ({', '.join(models_to_try)}). Error terakhir: {last_err}"
    )


def safe_json_parse(text: str):
    """LLM kadang masih bungkus jawaban dengan ```json fences walau diminta
    tidak. Strip itu sebelum parse."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        return {"_parse_error": str(e), "_raw_response": text[:2000]}


def llm_analyze_category(category_name: str, payload: dict, api_key: str, model: str) -> dict:
    prompt = f"""Berikut temuan static-analysis (AST-based) untuk kategori "{category_name}"
dari codebase SiCuan (folder: sicuan/, agents/, core/, mcp/).

DATA TEMUAN (JSON):
{json.dumps(payload, indent=2, ensure_ascii=False)[:12000]}

Untuk SETIAP temuan, beri penilaian dalam format JSON seperti ini:
{{
  "category": "{category_name}",
  "findings": [
    {{
      "ref": "<identifier singkat temuan, misal nama fungsi/file>",
      "severity": "critical|high|medium|low|non_issue",
      "is_likely_dead_code": true/false/null,
      "reasoning": "<1-3 kalimat, jelaskan KENAPA severity ini, termasuk jika ada dynamic_loading_signals yang membuat status orphan meragukan>",
      "recommended_action": "<aksi konkret: misal 'hapus file X', 'gabungkan jadi base class', 'cek manual: apakah dipanggil via importlib', 'biarkan, ini wajar'>"
    }}
  ],
  "category_summary": "<2-4 kalimat ringkasan keseluruhan kategori ini>"
}}

Aturan penting:
- JANGAN anggap semua "broken import" itu critical — cek apakah modul tujuan
  kemungkinan besar memang belum pernah ditulis (fitur direncanakan tapi
  belum selesai) vs pernah ada lalu hilang (kemungkinan bug serius).
- JANGAN anggap semua "orphan file" itu dead code — kalau ada
  dynamic_loading_signals pada file lain di project, beri severity lebih
  rendah dan catat itu di reasoning.
- Untuk duplicate logic singkat (property/getter sederhana, __init__ pendek,
  __new__ singleton pattern), severity biasanya "low" — itu pola umum, bukan
  bug. Severity "high"/"critical" untuk duplikat fungsi besar dan kompleks
  (banyak baris, logic bisnis penting).
- Jawab HANYA JSON valid sesuai skema di atas, tanpa teks lain."""

    raw = call_openrouter(prompt, api_key, model)
    return safe_json_parse(raw)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    project_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
    print(f"[*] SiCuan Self-Audit — project root: {project_root}", file=sys.stderr)

    load_env_file(project_root)
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    model = os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL).strip()

    if not api_key:
        print("[!] OPENROUTER_API_KEY tidak ditemukan di environment atau .env", file=sys.stderr)
        print("[!] Set dulu: export OPENROUTER_API_KEY=sk-or-... atau taruh di .env project", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Model: {model}", file=sys.stderr)
    print("[*] Tahap 1/3: analisis statis (AST)...", file=sys.stderr)
    static = run_static_analysis(project_root)
    print(f"[*] Selesai. {static['scanned_files']} file, {static['scanned_functions']} fungsi diindeks "
          f"(dalam scope: {SCOPE_PREFIXES})", file=sys.stderr)

    categories = {
        "exact_duplicates": static["exact_duplicates"],
        "structural_duplicates": static["structural_duplicates"],
        "class_diverged": static["class_diverged"],
        "broken_imports": static["broken_imports"],
        "orphan_files": {
            "orphans": static["orphan_files"],
            "dynamic_loading_context": static["dynamic_loading_context"],
        },
        "endpoint_collisions": static["endpoint_collisions"],
    }

    print("[*] Tahap 2/3: penalaran LLM per kategori (via OpenRouter)...", file=sys.stderr)
    llm_results = {}
    for cat_name, cat_data in categories.items():
        if cat_name == "orphan_files":
            is_empty = not cat_data.get("orphans")
        else:
            is_empty = (not cat_data) or (isinstance(cat_data, list) and len(cat_data) == 0) or \
                       (isinstance(cat_data, dict) and len(cat_data) == 0)
        if is_empty:
            print(f"    - {cat_name}: kosong, skip LLM call", file=sys.stderr)
            llm_results[cat_name] = {"category": cat_name, "findings": [], "category_summary": "Tidak ada temuan."}
            continue
        print(f"    - {cat_name}: mengirim ke LLM...", file=sys.stderr)
        try:
            llm_results[cat_name] = llm_analyze_category(cat_name, cat_data, api_key, model)
        except Exception as e:
            print(f"    ⚠️  {cat_name}: gagal dianalisis LLM ({e}), simpan data mentah saja", file=sys.stderr)
            llm_results[cat_name] = {"category": cat_name, "findings": [], "category_summary": f"LLM call gagal: {e}", "error": str(e)}

    print("[*] Tahap 3/3: menulis laporan...", file=sys.stderr)

    timestamp = datetime.now(timezone.utc).isoformat()
    full_report = {
        "audit_type": "sicuan_self_audit",
        "generated_at": timestamp,
        "model_used": model,
        "scope": SCOPE_PREFIXES,
        "static_analysis_summary": {
            "scanned_files": static["scanned_files"],
            "scanned_functions": static["scanned_functions"],
            "exact_duplicate_groups": len(static["exact_duplicates"]),
            "structural_duplicate_groups": len(static["structural_duplicates"]),
            "class_diverged_count": len(static["class_diverged"]),
            "broken_imports_count": len(static["broken_imports"]),
            "orphan_files_count": len(static["orphan_files"]),
            "endpoint_collisions_count": len(static["endpoint_collisions"]),
        },
        "raw_static_findings": static,
        "llm_analysis": llm_results,
    }

    knowledge_dir = project_root / "sicuan" / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    json_path = knowledge_dir / "self_audit.json"
    md_path = knowledge_dir / "self_audit.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2, ensure_ascii=False)

    # Human-readable markdown companion
    lines = [
        f"# SiCuan Self-Audit Report",
        f"",
        f"Dibuat: {timestamp}",
        f"Model analisis: {model}",
        f"Scope: {', '.join(SCOPE_PREFIXES)}",
        f"",
        f"## Ringkasan",
        f"",
        f"- File dipindai: {static['scanned_files']}",
        f"- Fungsi/method diindeks: {static['scanned_functions']}",
        f"- Grup duplikat identik: {len(static['exact_duplicates'])}",
        f"- Grup duplikat struktural: {len(static['structural_duplicates'])}",
        f"- Class divergen: {len(static['class_diverged'])}",
        f"- Broken imports: {len(static['broken_imports'])}",
        f"- Orphan files: {len(static['orphan_files'])}",
        f"- Endpoint collisions: {len(static['endpoint_collisions'])}",
        f"",
    ]

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "non_issue": 4}
    for cat_name, result in llm_results.items():
        lines.append(f"## {cat_name}")
        lines.append("")
        summary = result.get("category_summary", "(tidak ada ringkasan)")
        lines.append(f"_{summary}_")
        lines.append("")
        findings = result.get("findings", [])
        findings_sorted = sorted(findings, key=lambda x: severity_order.get(x.get("severity", "low"), 5))
        for f in findings_sorted:
            sev = f.get("severity", "?")
            badge = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "non_issue": "⚪"}.get(sev, "❓")
            lines.append(f"- {badge} **{f.get('ref', '?')}** ({sev}): {f.get('reasoning', '')}")
            action = f.get("recommended_action")
            if action:
                lines.append(f"  - ➡️ {action}")
        lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[✓] Selesai.", file=sys.stderr)
    print(f"[✓] JSON: {json_path}", file=sys.stderr)
    print(f"[✓] Markdown: {md_path}", file=sys.stderr)
    print("", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print("RINGKASAN ANALISIS LLM (per kategori):", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    for cat_name, result in llm_results.items():
        n_findings = len(result.get("findings", []))
        critical = sum(1 for x in result.get("findings", []) if x.get("severity") == "critical")
        high = sum(1 for x in result.get("findings", []) if x.get("severity") == "high")
        print(f"  {cat_name}: {n_findings} temuan dinilai LLM ({critical} critical, {high} high)", file=sys.stderr)


if __name__ == "__main__":
    main()
