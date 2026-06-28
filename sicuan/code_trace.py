
import hashlib
import json
from functools import lru_cache
from pathlib import Path

# Cache untuk AST parsing
_ast_cache = {}
_cache_file = Path("/home/dibs/agentjw/memory/ast_cache.json")

def _load_cache():
    """Load AST cache dari file"""
    global _ast_cache
    if _cache_file.exists():
        try:
            with open(_cache_file) as f:
                _ast_cache = json.load(f)
        except:
            _ast_cache = {}
    else:
        _ast_cache = {}

def _save_cache():
    """Save AST cache ke file"""
    try:
        with open(_cache_file, "w") as f:
            json.dump(_ast_cache, f)
    except:
        pass

def _get_file_hash(filepath: Path) -> str:
    """Dapatkan hash file untuk cache key"""
    try:
        content = filepath.read_bytes()
        return hashlib.md5(content).hexdigest()
    except:
        return ""

# Load cache di awal
_load_cache()

# Decorator untuk caching trace result
def cached_trace(func):
    def wrapper(symbol):
        # Cek cache memory
        cache_key = f"trace_{symbol}"
        if cache_key in _ast_cache:
            return _ast_cache[cache_key]
        
        result = func(symbol)
        
        # Simpan ke cache
        _ast_cache[cache_key] = result
        _save_cache()
        
        return result
    return wrapper


def trace_before_patch(symbol: str, max_depth: int = 3, timeout: int = 5):
    """
    Trace symbol dengan timeout dan batasan depth.
    - max_depth: batas kedalaman dependency (default 3)
    - timeout: maksimal detik (default 5)
    """
    import time
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Trace timeout")
    
    start_time = time.time()
    
    # Cek symbol kosong
    if not symbol or not symbol.strip():
        return R(symbol, [], "Symbol kosong")
    
    # Log untuk debugging
    print(f"Tracing symbol: {symbol} (max_depth={max_depth}, timeout={timeout}s)")
    
    try:
        # Set timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        # Panggil trace asli (dengan batasan depth)
        result = _trace_implementation(symbol, max_depth)
        
        # Batalkan alarm
        signal.alarm(0)
        
        duration = time.time() - start_time
        print(f"Trace completed: {duration:.2f}s")
        return result
        
    except TimeoutError:
        print(f"Trace timeout for {symbol} after {timeout}s")
        return R(symbol, [], f"Timeout after {timeout}s")
    except Exception as e:
        print(f"Trace error: {e}")
        return R(symbol, [], str(e))

def _trace_implementation(symbol: str, max_depth: int = 3):
    """
    Implementasi trace dengan batasan depth.
    """
    # ... existing code with depth limit ...

"""
Code trace v3
Supports:
- symbol trace
- project trace
- natural language trace
"""

from sicuan.project_trace import audit_report
from pathlib import Path
import ast
import warnings
import re


def _clean_symbol(symbol: str):
    """
    Bersihkan input user sebelum AST lookup.
    """

    if not symbol:
        return ""

    symbol = symbol.strip()

    # ambil bagian sebelum instruksi panjang
    if ":" in symbol:
        left, right = symbol.split(":", 1)

        # project:function
        if len(right.split()) <= 2:
            return right.strip()

        return left.strip()

    # hapus kalimat natural language
    blacklist = [
        "lihat",
        "cek",
        "function",
        "yang",
        "handle",
        "posisi",
        "dan",
        "jual",
        "beli",
        "implementasikan",
        "trailing",
        "stop",
        "buffer",
    ]

    words = symbol.replace("-", " ").split()

    clean = [
        w for w in words
        if w.lower() not in blacklist
    ]

    if len(clean) == 1:
        return clean[0]

    return symbol



def _find_related_functions(text, root):
    """
    Cari function berdasarkan:
    - nama function
    - isi function
    - attribute yang disentuh
    - call yang dilakukan
    """

    keywords = [
        x.lower()
        for x in re.findall(r"[a-zA-Z_]+", text)
        if len(x) > 3
    ]

    found = []

    for py in Path(root).rglob("*.py"):

        if "__pycache__" in str(py):
            continue

        try:
            source = py.read_text(errors="ignore")
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', SyntaxWarning)
                tree = ast.parse(source)

            for node in ast.walk(tree):

                if not isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef
                    )
                ):
                    continue


                lines = source.splitlines()

                body = "\n".join(
                    lines[
                        node.lineno - 1:
                        node.end_lineno
                    ]
                ).lower()


                score = 0

                fname_lower = node.name.lower()


                # nama function exact lebih kuat
                for k in keywords:
                    if k in fname_lower:
                        score += 10


                # trailing stop sangat spesifik
                text_lower = text.lower()



                # isi logic
                for k in keywords:
                    if k in body:
                        score += 2


                # trading related bonus
                trading_words = [
                    "position",
                    "sell",
                    "buy",
                    "balance",
                    "entry",
                    "exit",
                    "stop",
                    "profit",
                    "pnl",
                    "price",
                    "token",
                ]

                for w in trading_words:
                    if w in body:
                        score += 1


                if "trailing" in text_lower:
                    if "_update_trailing_stop" in fname_lower:
                        score += 500

                    if "risk_manager" in str(py).lower():
                        score += 200

                    if "trailing" in fname_lower:
                        score += 200

                    if "trailing" in body:
                        score += 50

                if "stop" in text_lower:
                    if "stop" in fname_lower:
                        score += 100

                if "buffer" in text_lower:
                    if "buffer" in body:
                        score += 30


                if score:

                    # hard filter untuk request spesifik
                    if "trailing_stop" in text_lower or (
                        "trailing" in text_lower and "stop" in text_lower
                    ):
                        if (
                            "trailing" not in fname_lower
                            and "trailing" not in body
                            and "trailing" not in body
                        ):
                            continue

                    found.append(
                        (
                            score,
                            f"{py}:{node.name}:{node.lineno}"
                        )
                    )


        except Exception:
            continue


    found.sort(
        reverse=True,
        key=lambda x:x[0]
    )

    # Request sangat spesifik: trailing stop
    # Jangan lempar banyak kandidat karena LLM bisa salah pilih.
    if (
        "trailing_stop" in text_lower
        or (
            "trailing" in text_lower
            and "stop" in text_lower
        )
    ):
        return [
            x[1]
            for x in found[:3]
        ]

    return [
        x[1]
        for x in found[:10]
    ]


def trace_before_patch(
    symbol,
    root="/home/dibs/agentjw"
):

    raw_symbol = symbol

    cleaned = _clean_symbol(symbol)


    # project trace
    if (
        "/" in cleaned
        or cleaned.endswith("_bot")
    ):

        project = Path(cleaned)

        if not project.exists():

            project = (
                Path("/home/dibs/agentjw/projects")
                /
                cleaned
            )

        if project.exists():

            class R:

                def to_report(self):
                    return audit_report(
                        str(project)
                    )

            return R()


    # AUTO PROJECT DISCOVERY
    # Jika request bukan nama project/file,
    # cari project paling relevan berdasarkan isi kode.

    root_path = Path(root)

    projects = [
        x for x in (root_path / "projects").iterdir()
        if x.is_dir()
    ] if (root_path / "projects").exists() else []

    if projects:
        best_project = None
        best_score = 0

        query = cleaned.lower()

        for project in projects:
            score = 0

            for py in project.rglob("*.py"):
                try:
                    content = py.read_text(errors="ignore").lower()

                    for word in [
                        "position",
                        "sell",
                        "buy",
                        "trailing",
                        "stop",
                        "pnl",
                        "token",
                        "risk"
                    ]:
                        if word in query and word in content:
                            score += 1

                except Exception:
                    pass

            if score > best_score:
                best_score = score
                best_project = project


        if best_project:
            root = str(best_project)


    # request biasa: trace berdasarkan keyword/function relation
    related = _find_related_functions(
        raw_symbol,
        root
    )

    if related:

        class R:
            def to_report(self):
                return "\n".join(
                    str(x)
                    for x in related
                )

        return R()


    # fallback semantic trace dari request user
    semantic_matches = _find_related_functions(
        raw_symbol,
        root
    )

    if semantic_matches:
        class R:
            def to_report(self):
                return "\n".join(
                    str(item)
                    for item in semantic_matches[:3]
                )

        return R()


    matches = []


    for py in Path(root).rglob("*.py"):

        if "__pycache__" in str(py):
            continue

        try:

            tree = ast.parse(
                py.read_text(errors="ignore")
            )


            for node in ast.walk(tree):

                if isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef
                    )
                ):

                    if node.name == cleaned:

                        matches.append(
                            f"{py}:{node.name}:{node.lineno}"
                        )


        except Exception:
            pass


    # fallback natural language
    if not matches:

        matches = _find_related_functions(
            raw_symbol,
            root
        )


    class Result:

        def to_report(self):

            if matches:
                return "\n".join(matches)

            semantic = _find_related_functions(
                raw_symbol,
                root
            )

            if semantic:
                return "\n".join(
                    [
                        item[1]
                        for item in semantic
                    ]
                )

            return (
                f"Symbol '{raw_symbol}' tidak ditemukan"
            )


    return Result()
