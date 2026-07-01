#!/usr/bin/env python3
"""
codebase_audit.py
==================
Audit komprehensif untuk codebase Python (SiCuan/AgentJW/JOWO style projects).

Mendeteksi:
  1. DUPLICATE LOGIC   - fungsi/method dengan body identik atau hampir identik
                          (nama beda ATAU sama), via AST normalization + hashing.
  2. DUPLICATE NAMES   - class/function dengan nama sama di file berbeda
                          (signature dibandingkan, bukan cuma nama).
  3. BROKEN IMPORTS    - `from x import y` / `import x` yang tidak resolve
                          ke file yang benar-benar ada di project.
  4. ORPHAN FILES      - file .py yang tidak pernah di-import oleh file lain
                          (kandidat dead code, kecuali entrypoint/script).
  5. ENDPOINT COLLISION- route Flask/FastAPI (@app.route, @app.get, dst) yang
                          path-nya sama tapi didefinisikan di file berbeda,
                          atau method handler beda tapi path sama-persis.
  6. SYNC ISSUES       - class yang punya nama sama di >1 file tapi dengan
                          method-set yang BERBEDA (indikasi file "kembar"
                          yang sudah divergen / out-of-sync).

Penggunaan:
    python3 codebase_audit.py [root_dir] [--exclude pattern1,pattern2,...]

Contoh:
    python3 codebase_audit.py . --exclude venv,backups,archive,__pycache__

Output: laporan teks ke stdout + JSON detail ke audit_report.json
"""

import ast
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


DEFAULT_EXCLUDES = {
    "venv", ".venv", "__pycache__", ".git", "node_modules",
    "backups", "backup_video_patch", "archive", "archive_for_review",
    "sicuan_audit_report", "reports", "logs", ".pytest_cache",
}

ROUTE_DECORATOR_RE = re.compile(
    r"(route|get|post|put|delete|patch|websocket)$", re.IGNORECASE
)


# --------------------------------------------------------------------------
# Data structures
# --------------------------------------------------------------------------

@dataclass
class FuncInfo:
    file: str
    qualname: str          # ClassName.method or just func_name
    name: str
    lineno: int
    end_lineno: int
    arg_count: int
    is_method: bool
    body_hash: str          # hash of normalized AST (structure, ignores names)
    body_hash_strict: str   # hash of normalized AST (ignores var names, keeps literals)
    source_lines: int


@dataclass
class ClassInfo:
    file: str
    name: str
    lineno: int
    methods: list = field(default_factory=list)  # list of method names


@dataclass
class ImportInfo:
    file: str
    lineno: int
    module: Optional[str]   # for "from X import Y" -> X ; for "import X" -> None
    names: list              # imported names (or the module itself for `import x`)
    is_relative: bool
    raw: str


@dataclass
class RouteInfo:
    file: str
    lineno: int
    method_name: str        # e.g. 'route', 'get', 'post'
    path: Optional[str]
    func_name: str


# --------------------------------------------------------------------------
# AST normalization for structural similarity hashing
# --------------------------------------------------------------------------

class Normalizer(ast.NodeTransformer):
    """Replaces identifiers with generic placeholders so that two functions
    with the same logical structure but different variable/arg names will
    hash identically. Literals (numbers/strings) are kept for the 'strict'
    hash but blanked for the 'loose' structural hash."""

    def __init__(self, blank_literals: bool):
        self.blank_literals = blank_literals
        self.name_map = {}
        self.counter = 0

    def _generic_name(self, original):
        if original not in self.name_map:
            self.name_map[original] = f"_v{self.counter}"
            self.counter += 1
        return self.name_map[original]

    def visit_Name(self, node):
        node.id = self._generic_name(node.id)
        return node

    def visit_arg(self, node):
        node.arg = self._generic_name(node.arg)
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
        node.attr = self._generic_name(node.attr)
        return node

    def visit_Constant(self, node):
        if self.blank_literals:
            if isinstance(node.value, str):
                node.value = "_STR_"
            elif isinstance(node.value, (int, float)):
                node.value = 0
        return node


def hash_function_body(node: ast.FunctionDef, blank_literals: bool) -> str:
    try:
        body_copy = ast.parse(ast.unparse(node))  # deep copy via round-trip
    except Exception:
        return ""
    normalizer = Normalizer(blank_literals=blank_literals)
    normalizer.visit(body_copy)
    try:
        dumped = ast.dump(body_copy, annotate_fields=False)
    except Exception:
        return ""
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------
# File discovery
# --------------------------------------------------------------------------

def discover_py_files(root: Path, excludes: set) -> list:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in excludes and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith(".py"):
                full = Path(dirpath) / fn
                files.append(full)
    return files


def module_dotted_path(file: Path, root: Path) -> str:
    rel = file.relative_to(root).with_suffix("")
    parts = rel.parts
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


# --------------------------------------------------------------------------
# Per-file parsing
# --------------------------------------------------------------------------

def parse_file(file: Path, root: Path):
    """Returns (functions, classes, imports, routes, parse_error)"""
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
            loose_hash = hash_function_body(node, blank_literals=True)
            strict_hash = hash_function_body(node, blank_literals=False)
            functions.append(FuncInfo(
                file=relfile,
                qualname=qualname,
                name=node.name,
                lineno=node.lineno,
                end_lineno=end_lineno,
                arg_count=len(node.args.args),
                is_method=bool(self.class_stack),
                body_hash=loose_hash,
                body_hash_strict=strict_hash,
                source_lines=end_lineno - node.lineno + 1,
            ))
            # check decorators for route registration
            for dec in node.decorator_list:
                dec_call = dec
                dec_func = None
                if isinstance(dec_call, ast.Call):
                    dec_func = dec_call.func
                else:
                    dec_func = dec_call
                attr_name = None
                if isinstance(dec_func, ast.Attribute):
                    attr_name = dec_func.attr
                elif isinstance(dec_func, ast.Name):
                    attr_name = dec_func.id
                if attr_name and ROUTE_DECORATOR_RE.search(attr_name):
                    path_arg = None
                    if isinstance(dec_call, ast.Call) and dec_call.args:
                        first = dec_call.args[0]
                        if isinstance(first, ast.Constant) and isinstance(first.value, str):
                            path_arg = first.value
                    routes.append(RouteInfo(
                        file=relfile, lineno=node.lineno,
                        method_name=attr_name, path=path_arg, func_name=node.name,
                    ))
            self.generic_visit(node)

        def visit_FunctionDef(self, node):
            self._handle_func(node)

        def visit_AsyncFunctionDef(self, node):
            self._handle_func(node)

        def visit_Import(self, node):
            for alias in node.names:
                imports.append(ImportInfo(
                    file=relfile, lineno=node.lineno, module=None,
                    names=[alias.name], is_relative=False,
                    raw=f"import {alias.name}",
                ))

        def visit_ImportFrom(self, node):
            mod = node.module or ""
            names = [a.name for a in node.names]
            imports.append(ImportInfo(
                file=relfile, lineno=node.lineno, module=mod,
                names=names, is_relative=(node.level or 0) > 0,
                raw=f"from {'.' * (node.level or 0)}{mod} import {', '.join(names)}",
            ))

    Visitor().visit(tree)
    return functions, classes, imports, routes, None


# --------------------------------------------------------------------------
# Analysis passes
# --------------------------------------------------------------------------

def find_duplicate_functions(all_funcs: list, min_lines: int = 3):
    """Group functions by structural hash; flag groups spanning >1 file
    or with different qualnames (different name, same logic)."""
    groups = defaultdict(list)
    for f in all_funcs:
        if f.source_lines < min_lines or not f.body_hash:
            continue
        groups[f.body_hash].append(f)

    exact_dupes = []      # identical logic incl. literals
    structural_dupes = [] # identical structure, different literals/names

    strict_groups = defaultdict(list)
    for f in all_funcs:
        if f.source_lines < min_lines or not f.body_hash_strict:
            continue
        strict_groups[f.body_hash_strict].append(f)

    for h, members in strict_groups.items():
        if len(members) > 1:
            files_involved = {m.file for m in members}
            names_involved = {m.qualname for m in members}
            if len(files_involved) > 1 or len(names_involved) > 1:
                exact_dupes.append(members)

    for h, members in groups.items():
        if len(members) > 1:
            files_involved = {m.file for m in members}
            names_involved = {m.qualname for m in members}
            # only report as "structural" if not already fully captured by exact dupes
            if len(files_involved) > 1 or len(names_involved) > 1:
                already = any(
                    {m.qualname for m in members} == {e.qualname for e in grp}
                    for grp in exact_dupes
                )
                if not already:
                    structural_dupes.append(members)

    return exact_dupes, structural_dupes


def find_same_name_different_body(all_funcs: list):
    """Functions/methods sharing the same bare name across files, but with
    different structural hashes -> likely divergent 'twin' implementations."""
    by_name = defaultdict(list)
    for f in all_funcs:
        by_name[f.name].append(f)

    suspects = []
    for name, members in by_name.items():
        if name.startswith("__") and name.endswith("__"):
            continue  # skip dunder methods, too noisy
        files = {m.file for m in members}
        if len(files) < 2:
            continue
        hashes = {m.body_hash for m in members}
        if len(hashes) > 1:
            suspects.append((name, members))
    return suspects


def find_same_class_diverged(all_classes: list):
    by_name = defaultdict(list)
    for c in all_classes:
        by_name[c.name].append(c)

    diverged = []
    for name, members in by_name.items():
        files = {m.file for m in members}
        if len(files) < 2:
            continue
        method_sets = [frozenset(m.methods) for m in members]
        if len(set(method_sets)) > 1:
            diverged.append((name, members))
    return diverged


def build_module_index(files: list, root: Path):
    """Map dotted module path -> file, plus map of top-level package dirs
    that have __init__.py (so 'from sicuan.core import x' resolves)."""
    index = {}
    for f in files:
        dotted = module_dotted_path(f, root)
        index[dotted] = f
        # also index without leading package segments removed, to allow
        # partial matches like 'core.brain' resolving under 'sicuan.core.brain'
    return index


def resolve_import(imp: ImportInfo, file: Path, root: Path, module_index: dict):
    """Best-effort resolution. Returns True if likely resolvable, False if
    likely broken, None if external (3rd-party/stdlib, can't verify here)."""
    if imp.module is None:
        # plain `import x`
        target = imp.names[0]
    else:
        target = imp.module

    if imp.is_relative:
        # relative import - resolve based on file's package location
        base_parts = list(file.relative_to(root).parts[:-1])
        target_parts = target.split(".") if target else []
        candidate = ".".join(base_parts + target_parts) if target else ".".join(base_parts)
        if candidate in module_index:
            return True
        # try as package (dir with __init__)
        for mod_path in module_index:
            if mod_path == candidate or mod_path.startswith(candidate + "."):
                return True
        return False

    # absolute import: only check if it looks like an internal project import
    # heuristic: if the first segment matches a top-level dir in root
    top_level_dirs = {p.name for p in root.iterdir() if p.is_dir()}
    first_seg = target.split(".")[0]
    if first_seg not in top_level_dirs and first_seg not in {m.split(".")[0] for m in module_index}:
        return None  # external package, not our concern

    if target in module_index:
        return True
    for mod_path in module_index:
        if mod_path == target or mod_path.startswith(target + "."):
            return True
    # check if importing specific names from a package's __init__
    if target in module_index:
        return True
    return False


def find_broken_imports(all_imports: list, files: list, root: Path, module_index: dict):
    broken = []
    for imp in all_imports:
        file_path = root / imp.file
        result = resolve_import(imp, file_path, root, module_index)
        if result is False:
            broken.append(imp)
    return broken


def has_main_guard_or_cli_entry(file: Path) -> bool:
    """Heuristic: file likely run directly (not imported) if it has a
    `if __name__ == '__main__':` guard, or runs app.run()/uvicorn.run() etc."""
    try:
        src = file.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    if "__name__" in src and "__main__" in src:
        return True
    run_signals = (".run(", "uvicorn.run", "asyncio.run(", "app.run_polling", "Bot(token")
    return any(sig in src for sig in run_signals)


def find_orphan_files(files: list, all_imports: list, root: Path, module_index: dict):
    imported_modules = set()
    for imp in all_imports:
        if imp.module:
            imported_modules.add(imp.module)
            # also add prefixes (from a.b.c import x -> a.b.c, a.b, a)
            parts = imp.module.split(".")
            for i in range(1, len(parts) + 1):
                imported_modules.add(".".join(parts[:i]))
        for n in imp.names:
            imported_modules.add(n)

    orphans = []
    likely_entrypoints = []
    entrypoint_hints = {
        "main", "app", "server", "manage", "wsgi", "asgi", "setup", "run", "cli",
        "telegram_bot", "bot", "start_sicuan",
    }
    for f in files:
        dotted = module_dotted_path(f, root)
        base_name = f.stem
        if base_name.startswith("test_") or base_name.startswith("__init__"):
            continue
        if dotted in imported_modules or base_name in imported_modules:
            continue
        hit = any(dotted == m or dotted.endswith("." + m) or m.endswith("." + dotted) for m in imported_modules)
        if hit:
            continue
        if base_name in entrypoint_hints or has_main_guard_or_cli_entry(f):
            likely_entrypoints.append(f)
            continue
        orphans.append(f)
    return orphans, likely_entrypoints


def find_endpoint_collisions(all_routes: list):
    by_path = defaultdict(list)
    for r in all_routes:
        if r.path:
            by_path[r.path].append(r)
    collisions = {p: rs for p, rs in by_path.items() if len({(r.file, r.func_name) for r in rs}) > 1}
    return collisions


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------

def fmt_func_loc(f: FuncInfo) -> str:
    return f"{f.file}:{f.lineno} [{f.qualname}] ({f.source_lines} lines)"


def print_report(root, exact_dupes, structural_dupes, name_clashes,
                  class_diverged, broken_imports, orphans, likely_entrypoints, endpoint_collisions,
                  total_files, total_funcs, parse_errors):
    W = 78
    def header(title):
        print("\n" + "=" * W)
        print(title)
        print("=" * W)

    print("=" * W)
    print(f"CODEBASE AUDIT REPORT  —  root: {root}")
    print(f"Files scanned: {total_files}  |  Functions/methods indexed: {total_funcs}")
    print("=" * W)

    if parse_errors:
        header(f"⚠️  PARSE ERRORS ({len(parse_errors)}) — file ini DILEWATI dari analisis")
        for f, err in parse_errors:
            print(f"  - {f}: {err}")

    # 1. Exact duplicate logic
    header(f"1️⃣  DUPLICATE LOGIC — IDENTIK (termasuk literal) ({len(exact_dupes)} grup)")
    if not exact_dupes:
        print("  ✅ Tidak ada fungsi dengan logic identik 100% di file berbeda.")
    for grp in exact_dupes:
        names = sorted({m.qualname for m in grp})
        print(f"\n  🔴 {len(grp)} salinan identik — nama: {names}")
        for m in grp:
            print(f"      {fmt_func_loc(m)}")

    # 2. Structural duplicates (same logic shape, different literals/names)
    header(f"2️⃣  DUPLICATE LOGIC — STRUKTUR SAMA, detail beda ({len(structural_dupes)} grup)")
    if not structural_dupes:
        print("  ✅ Tidak ada fungsi dengan struktur logic yang sama tapi beda nama/literal.")
    for grp in structural_dupes:
        names = sorted({m.qualname for m in grp})
        print(f"\n  🟡 {len(grp)} fungsi struktur identik — nama: {names}")
        for m in grp:
            print(f"      {fmt_func_loc(m)}")

    # 3. Same name, different body (divergent twins)
    header(f"3️⃣  NAMA SAMA, LOGIC BEDA — kemungkinan 'kembar' yang sudah divergen ({len(name_clashes)})")
    if not name_clashes:
        print("  ✅ Tidak ada fungsi dengan nama sama tapi implementasi berbeda.")
    for name, members in name_clashes:
        print(f"\n  🟠 def/method '{name}()' — {len(members)} implementasi berbeda:")
        for m in members:
            print(f"      {fmt_func_loc(m)}")

    # 4. Diverged classes
    header(f"4️⃣  CLASS NAMA SAMA, METHOD-SET BEDA ({len(class_diverged)})")
    if not class_diverged:
        print("  ✅ Tidak ada class dengan nama sama yang method-nya berbeda antar file.")
    for name, members in class_diverged:
        print(f"\n  🟠 class {name} — {len(members)} versi:")
        for m in members:
            print(f"      {m.file}:{m.lineno}  methods={sorted(m.methods)}")

    # 5. Broken imports
    header(f"5️⃣  BROKEN / TIDAK TERESOLVE IMPORTS ({len(broken_imports)})")
    if not broken_imports:
        print("  ✅ Semua import internal teresolve ke file yang ada.")
    for imp in broken_imports:
        print(f"  🔴 {imp.file}:{imp.lineno}  ->  {imp.raw}")

    # 6. Orphan files
    header(f"6️⃣  ORPHAN FILES — tidak pernah di-import file lain ({len(orphans)})")
    print("  (File entrypoint/CLI/bot dengan __main__ guard otomatis dikecualikan -> lihat bagian 6b)")
    if not orphans:
        print("  ✅ Tidak ada file orphan terdeteksi.")
    for f in sorted(orphans):
        print(f"  ⚪ {f}")

    header(f"6b️⃣  KEMUNGKINAN ENTRYPOINT (tidak di-import, tapi punya __main__/run guard) ({len(likely_entrypoints)})")
    print("  (Ini WAJAR jika file dijalankan langsung, misal: python3 server.py)")
    for f in sorted(likely_entrypoints):
        print(f"  🔵 {f}")

    # 7. Endpoint collisions
    header(f"7️⃣  ENDPOINT/ROUTE COLLISIONS ({len(endpoint_collisions)})")
    if not endpoint_collisions:
        print("  ✅ Tidak ada path route yang didefinisikan ganda.")
    for path, rs in endpoint_collisions.items():
        print(f"\n  🔴 path '{path}' didefinisikan {len(rs)}x:")
        for r in rs:
            print(f"      {r.file}:{r.lineno}  @{r.method_name}  -> def {r.func_name}()")

    header("RINGKASAN")
    print(f"  Duplicate identik       : {len(exact_dupes)} grup")
    print(f"  Duplicate struktural     : {len(structural_dupes)} grup")
    print(f"  Nama sama / logic beda   : {len(name_clashes)}")
    print(f"  Class divergen           : {len(class_diverged)}")
    print(f"  Broken imports           : {len(broken_imports)}")
    print(f"  Orphan files             : {len(orphans)}")
    print(f"  Endpoint collisions      : {len(endpoint_collisions)}")
    print("=" * W)
    print("Detail lengkap (JSON) disimpan di: audit_report.json")
    print("=" * W)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def in_scope(relpath: str, scope_prefixes: list) -> bool:
    if not scope_prefixes:
        return True
    return any(relpath == p or relpath.startswith(p.rstrip("/") + "/") for p in scope_prefixes)


def filter_to_scope(exact_dupes, structural_dupes, name_clashes, class_diverged,
                     broken_imports, orphans, likely_entrypoints, endpoint_collisions,
                     scope_prefixes):
    """Keep a finding only if AT LEAST ONE file involved is inside scope.
    This way we still catch 'sicuan/x.py duplicates logic with agents/y.py'
    even though the focus is sicuan/."""
    if not scope_prefixes:
        return (exact_dupes, structural_dupes, name_clashes, class_diverged,
                broken_imports, orphans, likely_entrypoints, endpoint_collisions)

    def grp_in_scope(members):
        return any(in_scope(m.file, scope_prefixes) for m in members)

    exact_dupes = [g for g in exact_dupes if grp_in_scope(g)]
    structural_dupes = [g for g in structural_dupes if grp_in_scope(g)]
    name_clashes = [(n, m) for n, m in name_clashes if grp_in_scope(m)]
    class_diverged = [(n, m) for n, m in class_diverged if grp_in_scope(m)]
    broken_imports = [i for i in broken_imports if in_scope(i.file, scope_prefixes)]
    endpoint_collisions = {
        p: rs for p, rs in endpoint_collisions.items()
        if any(in_scope(r.file, scope_prefixes) for r in rs)
    }
    return (exact_dupes, structural_dupes, name_clashes, class_diverged,
            broken_imports, orphans, likely_entrypoints, endpoint_collisions)


def main():
    args = sys.argv[1:]
    root_arg = "."
    excludes = set(DEFAULT_EXCLUDES)
    scope_prefixes = []
    i = 0
    while i < len(args):
        if args[i] == "--exclude" and i + 1 < len(args):
            excludes |= set(args[i + 1].split(","))
            i += 2
        elif args[i] == "--scope" and i + 1 < len(args):
            scope_prefixes = [s.strip().rstrip("/") for s in args[i + 1].split(",") if s.strip()]
            i += 2
        elif not args[i].startswith("--"):
            root_arg = args[i]
            i += 1
        else:
            i += 1

    root = Path(root_arg).resolve()
    print(f"[*] Scanning {root} (excluding: {sorted(excludes)})", file=sys.stderr)
    if scope_prefixes:
        print(f"[*] Scope filter active — only reporting findings touching: {scope_prefixes}", file=sys.stderr)
        print("[*] (Full project is still scanned so cross-folder imports resolve correctly)", file=sys.stderr)

    files = discover_py_files(root, excludes)
    print(f"[*] Found {len(files)} .py files", file=sys.stderr)

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
    broken_imports = find_broken_imports(all_imports, files, root, module_index)
    orphans, likely_entrypoints = find_orphan_files(files, all_imports, root, module_index)
    endpoint_collisions = find_endpoint_collisions(all_routes)

    if scope_prefixes:
        orphans = [f for f in orphans if in_scope(str(f.relative_to(root)), scope_prefixes)]
        likely_entrypoints = [f for f in likely_entrypoints if in_scope(str(f.relative_to(root)), scope_prefixes)]
        (exact_dupes, structural_dupes, name_clashes, class_diverged,
         broken_imports, _, _, endpoint_collisions) = filter_to_scope(
            exact_dupes, structural_dupes, name_clashes, class_diverged,
            broken_imports, orphans, likely_entrypoints, endpoint_collisions,
            scope_prefixes,
        )

    print_report(
        root, exact_dupes, structural_dupes, name_clashes, class_diverged,
        broken_imports, orphans, likely_entrypoints, endpoint_collisions,
        total_files=len(files), total_funcs=len(all_funcs),
        parse_errors=parse_errors,
    )

    json_path = root / "audit_report.json" if (root / "audit_report.json").parent.exists() else Path("audit_report.json")
    try:
        with open("audit_report.json", "w", encoding="utf-8") as fh:
            json.dump({
                "root": str(root),
                "total_files": len(files),
                "total_functions": len(all_funcs),
                "parse_errors": parse_errors,
                "exact_duplicate_groups": [
                    [asdict(m) for m in grp] for grp in exact_dupes
                ],
                "structural_duplicate_groups": [
                    [asdict(m) for m in grp] for grp in structural_dupes
                ],
                "name_clashes": [
                    {"name": n, "members": [asdict(m) for m in members]}
                    for n, members in name_clashes
                ],
                "class_diverged": [
                    {"name": n, "members": [asdict(m) for m in members]}
                    for n, members in class_diverged
                ],
                "broken_imports": [asdict(i) for i in broken_imports],
                "orphan_files": [str(f) for f in orphans],
                "likely_entrypoints": [str(f) for f in likely_entrypoints],
                "endpoint_collisions": {
                    path: [asdict(r) for r in rs] for path, rs in endpoint_collisions.items()
                },
            }, fh, indent=2)
    except Exception as e:
        print(f"[!] Gagal menulis JSON: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
