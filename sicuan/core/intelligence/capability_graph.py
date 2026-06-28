import ast
import json
from pathlib import Path


class CapabilityGraph:

    def __init__(self, root):
        self.root = Path(root)
        self.graph = {
            "files": [],
            "functions": [],
            "classes": [],
            "imports": [],
            "capabilities": {}
        }


    def scan(self):

        for file in self.root.rglob("*.py"):

            if "__pycache__" in str(file):
                continue

            try:
                source = file.read_text(errors="ignore")
                tree = ast.parse(source)

                self.graph["files"].append(str(file))

                for node in ast.walk(tree):

                    if isinstance(node, ast.FunctionDef):
                        self.graph["functions"].append({
                            "file": str(file),
                            "name": node.name,
                            "line": node.lineno
                        })

                    elif isinstance(node, ast.ClassDef):
                        self.graph["classes"].append({
                            "file": str(file),
                            "name": node.name,
                            "line": node.lineno
                        })

                    elif isinstance(node, ast.Import):
                        for n in node.names:
                            self.graph["imports"].append(n.name)

                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self.graph["imports"].append(node.module)

            except Exception:
                continue

        return self.graph


    def save(self, path):

        Path(path).write_text(
            json.dumps(
                self.graph,
                indent=2
            )
        )
