"""
SiCuan System Auditor
Read-only architecture mapper.

Detect:
- python files
- classes/functions
- imports
- agents
- tools
- MCP/OpenClaw
- capability exposure
- orphan functions
- dependency gaps

Usage:
python -m sicuan.tools.system_auditor.run_audit
"""

import ast
import json
import os
from pathlib import Path
from collections import defaultdict


ROOT = Path.cwd()

OUTPUT = ROOT / "sicuan_audit_report"

OUTPUT.mkdir(exist_ok=True)


class PythonScanner:

    def __init__(self, root):
        self.root = Path(root)

        self.files = []
        self.functions = []
        self.classes = []
        self.imports = []

        self.calls = defaultdict(list)

        self.capabilities = []

    def scan(self):

        for file in self.root.rglob("*.py"):

            if any(
                x in file.parts
                for x in [
                    "venv",
                    "__pycache__",
                    ".git"
                ]
            ):
                continue

            self.files.append(str(file))

            self.scan_file(file)


    def scan_file(self, filepath):

        try:
            code = filepath.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            tree = ast.parse(code)

        except Exception:
            return


        module = str(filepath)


        for node in ast.walk(tree):

            if isinstance(node, ast.FunctionDef):

                item = {
                    "file": module,
                    "function": node.name,
                    "line": node.lineno
                }

                self.functions.append(item)


                if any(
                    x in node.name.lower()
                    for x in [
                        "tool",
                        "execute",
                        "run",
                        "create",
                        "modify",
                        "repair",
                        "agent",
                    ]
                ):
                    self.capabilities.append(item)


            elif isinstance(node, ast.AsyncFunctionDef):

                self.functions.append(
                    {
                        "file": module,
                        "function": node.name,
                        "line": node.lineno,
                        "async": True
                    }
                )


            elif isinstance(node, ast.ClassDef):

                self.classes.append(
                    {
                        "file": module,
                        "class": node.name,
                        "line": node.lineno
                    }
                )


            elif isinstance(node, ast.Import):

                for n in node.names:
                    self.imports.append(
                        {
                            "file":module,
                            "import":n.name
                        }
                    )


            elif isinstance(node, ast.ImportFrom):

                self.imports.append(
                    {
                        "file":module,
                        "import":node.module
                    }
                )


        self.detect_calls(tree, module)


    def detect_calls(self, tree, module):

        for node in ast.walk(tree):

            if isinstance(node, ast.Call):

                if isinstance(node.func, ast.Name):

                    self.calls[
                        node.func.id
                    ].append(module)



class GapAnalyzer:


    def __init__(self, scanner):

        self.s = scanner


    def analyze(self):

        gaps=[]


        # function tidak pernah dipanggil

        called=set(
            self.s.calls.keys()
        )


        for fn in self.s.functions:

            if (
                fn["function"]
                not in called
                and not fn["function"].startswith("_")
            ):

                gaps.append(
                    {
                        "type":"orphan_function",
                        **fn
                    }
                )


        # capability

        for cap in self.s.capabilities:

            name=cap["function"]

            if name not in called:

                gaps.append(
                    {
                        "type":"unused_capability",
                        **cap
                    }
                )


        return gaps



def detect_special_components(scanner):

    result={

        "agents":[],
        "mcp":[],
        "tools":[]

    }


    for f in scanner.files:

        low=f.lower()

        if "agent" in low:
            result["agents"].append(f)

        if (
            "mcp" in low
            or "openclaw" in low
        ):
            result["mcp"].append(f)

        if "tool" in low:
            result["tools"].append(f)


    return result



def save(name,data):

    path=OUTPUT/name

    path.write_text(
        json.dumps(
            data,
            indent=2
        ),
        encoding="utf-8"
    )



def generate_markdown(data):

    md=[]

    md.append(
        "# SiCuan System Audit\n"
    )


    for k,v in data.items():

        if isinstance(v,list):

            md.append(
                f"\n## {k}\n"
            )

            for item in v[:20]:

                md.append(
                    f"- {item}\n"
                )

        else:

            md.append(
                f"\n{k}: {v}\n"
            )


    return "".join(md)



def main():

    print("""
====================================
 SiCuan System Auditor
 READ ONLY ARCHITECTURE SCAN
====================================
""")


    scanner=PythonScanner(ROOT)

    scanner.scan()


    gaps=GapAnalyzer(
        scanner
    ).analyze()


    components=detect_special_components(
        scanner
    )


    report={

        "root":str(ROOT),

        "python_files":
            len(scanner.files),

        "functions":
            len(scanner.functions),

        "classes":
            len(scanner.classes),

        "imports":
            len(scanner.imports),

        "capabilities":
            scanner.capabilities,

        "components":
            components,

        "gaps":
            gaps

    }


    save(
        "architecture.json",
        report
    )


    save(
        "functions.json",
        scanner.functions
    )


    save(
        "imports.json",
        scanner.imports
    )


    save(
        "gaps.json",
        gaps
    )


    (OUTPUT/"FINAL_REPORT.md").write_text(
        generate_markdown(report),
        encoding="utf-8"
    )


    print(
        "\nAudit selesai."
    )

    print(
        f"Files scanned : {len(scanner.files)}"
    )

    print(
        f"Functions     : {len(scanner.functions)}"
    )

    print(
        f"Classes       : {len(scanner.classes)}"
    )

    print(
        f"Capabilities  : {len(scanner.capabilities)}"
    )

    print(
        f"Gaps found    : {len(gaps)}"
    )

    print(
        f"\nReport: {OUTPUT}"
    )


if __name__=="__main__":
    main()
