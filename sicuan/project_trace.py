"""
Project Trace Engine v2
AST based feature detection
"""

import ast
from pathlib import Path


FEATURE_RULES = {
    "stop_loss": [
        "stop_loss",
        "check_stop_loss",
        "execute_stop_loss"
    ],
    "take_profit": [
        "take_profit",
        "check_take_profit",
        "execute_take_profit"
    ],
    "trailing_stop": [
        "trailing_stop",
        "check_trailing_stop",
        "execute_trailing_stop"
    ],
    "wallet_restore": [
        "load_paper_balance",
        "load_wallet",
        "restore_wallet"
    ],
    "position_restore": [
        "_load_positions_from_db",
        "load_positions",
        "restore_position"
    ],
    "open_position": [
        "_open_position",
        "open_position",
        "execute_buy"
    ],
    "close_position": [
        "_close_position",
        "close_position",
        "execute_sell"
    ],
    "liquidity_filter": [
        "liquidity"
    ],
    "volume_filter": [
        "volume"
    ],
    "marketcap_filter": [
        "marketcap",
        "market_cap",
        "mcap"
    ]
}


def trace_project(project_dir):

    project_dir = Path(project_dir)

    functions = {}
    calls = {}
    features = {k: [] for k in FEATURE_RULES}

    for py in project_dir.rglob("*.py"):

        if "__pycache__" in str(py):
            continue

        try:

            src = py.read_text(errors="ignore")

            tree = ast.parse(src)

            file_functions = set()

            for node in ast.walk(tree):

                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

                    file_functions.add(node.name)

                    functions[node.name] = {
                        "file": str(py),
                        "line": node.lineno
                    }

                    called = []

                    for n in ast.walk(node):

                        if isinstance(n, ast.Call):

                            if isinstance(n.func, ast.Name):
                                called.append(n.func.id)

                            elif isinstance(n.func, ast.Attribute):
                                called.append(n.func.attr)

                    calls[node.name] = sorted(set(called))

            text_lower = src.lower()

            for feature, patterns in FEATURE_RULES.items():

                for p in patterns:

                    if (
                        p in file_functions
                        or p.lower() in text_lower
                    ):
                        features[feature].append(str(py))
                        break

        except Exception:
            pass

    score = 0

    total = len(features)

    for _, files in features.items():

        if files:
            score += 1

    confidence = round(
        (score / total) * 100,
        1
    )

    return {
        "confidence": confidence,
        "functions": functions,
        "calls": calls,
        "features": features
    }


# ───────────────────────────────────────────────────────────
# AUDIT LAYER — dibangun di atas trace_project()
# (digabung dari project_audit_engine.py supaya satu file utuh)
# ───────────────────────────────────────────────────────────

def audit_project(project_dir: str):
    """Bungkus trace_project() jadi format audit yang lebih ringkas."""
    trace = trace_project(project_dir)

    features = {}
    for feature, files in trace["features"].items():
        features[feature] = {
            "exists": bool(files),
            "files": files[:20]
        }

    return {
        "confidence": trace["confidence"],
        "feature_count": len(features),
        "features": features,
        "functions": len(trace["calls"]),
        "call_graph": trace["calls"]
    }


def build_audit_report(project_dir: str):
    """Format audit_project() jadi laporan teks yang enak dibaca."""
    data = audit_project(project_dir)

    out = []
    out.append(f"PROJECT TRACE: {project_dir}")
    out.append("")
    out.append("FEATURE CHECK")

    for feat, meta in sorted(data["features"].items()):
        if meta["exists"]:
            out.append(f"✅ {feat}: FOUND")
            for f in meta["files"]:
                out.append(f"   - {f}")
        else:
            out.append(f"❌ {feat}: MISSING")

    out.append("")
    out.append(f"TRACE CONFIDENCE : {data['confidence']}")
    out.append(f"FUNCTIONS        : {data['functions']}")

    return "\n".join(out)


# Alias — code_trace.py mengimport nama 'audit_report'
audit_report = build_audit_report
