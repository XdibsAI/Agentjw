import ast
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path("/home/dibs/agentjw")

EXCLUDE = {
    "venv",
    "__pycache__",
    ".git",
    "backups",
    "sicuan_audit_report",
    "archive_for_review",
    "refactor_backup",
    ".pytest_cache"
}


def ignored(path: Path):
    parts = set(path.parts)
    return bool(parts & EXCLUDE)


def python_files():
    files = []
    for f in ROOT.rglob("*.py"):
        if ignored(f):
            continue
        files.append(f)
    return files


def build_graph():
    graph = {
        "nodes": {},
        "imports": defaultdict(list),
        "calls": defaultdict(list),
        "entrypoints": []
    }

    files = python_files()

    for file in files:
        try:
            source = file.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            tree = ast.parse(source)

            graph["nodes"][str(file)] = {
                "functions": [],
                "classes": []
            }

            for node in ast.walk(tree):

                if isinstance(node, ast.FunctionDef):
                    graph["nodes"][str(file)]["functions"].append(
                        node.name
                    )

                    if node.name in (
                        "run",
                        "execute",
                        "main",
                        "start"
                    ):
                        graph["entrypoints"].append({
                            "file": str(file),
                            "function": node.name
                        })

                elif isinstance(node, ast.ClassDef):
                    graph["nodes"][str(file)]["classes"].append(
                        node.name
                    )

                elif isinstance(node, ast.Import):
                    for n in node.names:
                        graph["imports"][str(file)].append(
                            n.name
                        )

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        graph["imports"][str(file)].append(
                            node.module
                        )

                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        graph["calls"][str(file)].append(
                            node.func.id
                        )

                    elif isinstance(node.func, ast.Attribute):
                        graph["calls"][str(file)].append(
                            node.func.attr
                        )

        except Exception:
            pass

    return graph


def save():
    graph = build_graph()

    out = ROOT / "sicuan_audit_report"
    out.mkdir(exist_ok=True)

    target = out / "runtime_graph.json"

    with open(target, "w") as f:
        json.dump(
            graph,
            f,
            indent=2
        )

    print(f"Saved: {target}")

    print(f"Files: {len(graph['nodes'])}")
    print(f"Entrypoints: {len(graph['entrypoints'])}")


if __name__ == "__main__":
    save()
