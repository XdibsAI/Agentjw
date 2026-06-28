"""
SiCuan Integration Brain

Architecture awareness layer.

Purpose:
- Understand available capabilities
- Map tools <-> projects <-> runtime
- Detect disconnected components
- Provide context for planner

READ ONLY.
No source modification.
"""

import os
import json
import ast
from pathlib import Path
from collections import defaultdict


class IntegrationBrain:

    def __init__(self, root="/home/dibs/agentjw"):

        self.root = Path(root)

        self.capabilities = {}
        self.components = {}
        self.connections = []
        self.gaps = []

    # -----------------------------
    # Scan python files
    # -----------------------------

    def scan_python(self):

        result = []

        for path in self.root.rglob("*.py"):

            if "venv" in str(path):
                continue

            try:
                code = path.read_text(
                    errors="ignore"
                )

                tree = ast.parse(code)

                funcs = []
                classes = []
                imports = []

                for node in ast.walk(tree):

                    if isinstance(node, ast.FunctionDef):
                        funcs.append(node.name)

                    elif isinstance(
                        node,
                        ast.ClassDef
                    ):
                        classes.append(node.name)

                    elif isinstance(
                        node,
                        (ast.Import, ast.ImportFrom)
                    ):
                        imports.append(
                            getattr(
                                node,
                                "module",
                                ""
                            )
                        )

                result.append(
                    {
                        "file":str(path),
                        "functions":funcs,
                        "classes":classes,
                        "imports":imports
                    }
                )

            except Exception:
                pass


        return result


    # -----------------------------
    # Detect tools
    # -----------------------------

    def detect_capabilities(self, files):

        keywords = {
            "trading":[
                "trade",
                "swap",
                "token",
                "position",
                "pnl"
            ],

            "memory":[
                "memory",
                "database",
                "sqlite"
            ],

            "mcp":[
                "mcp",
                "openclaw"
            ],

            "planner":[
                "plan",
                "planner"
            ],

            "video":[
                "video",
                "render",
                "youtube"
            ]
        }


        caps = defaultdict(list)


        for item in files:

            text = (
                item["file"]
                +
                " "
                +
                " ".join(
                    item["functions"]
                )
            ).lower()


            for cap,words in keywords.items():

                for w in words:

                    if w in text:

                        caps[cap].append(
                            item["file"]
                        )

                        break


        self.capabilities = dict(caps)

        return self.capabilities


    # -----------------------------
    # Detect missing links
    # -----------------------------

    def analyze_connections(self):

        caps = self.capabilities


        checks = [
            (
                "trading",
                "memory",
                "Trading without memory"
            ),

            (
                "mcp",
                "planner",
                "Tools unavailable to planner"
            ),

            (
                "planner",
                "memory",
                "Planner cannot learn"
            )
        ]


        gaps=[]


        for a,b,msg in checks:

            if a in caps and b not in caps:

                gaps.append(
                    {
                        "type":"missing_connection",
                        "from":a,
                        "to":b,
                        "problem":msg
                    }
                )


        self.gaps=gaps

        return gaps


    # -----------------------------
    # Export context
    # -----------------------------

    def build_context(self):

        files=self.scan_python()

        self.detect_capabilities(files)

        self.analyze_connections()


        return {

            "system":{
                "files":len(files)
            },

            "capabilities":
                self.capabilities,

            "gaps":
                self.gaps
        }


    def save(self):

        data=self.build_context()


        out=self.root / \
        "sicuan_audit_report" / \
        "integration_context.json"


        out.parent.mkdir(
            exist_ok=True
        )


        out.write_text(
            json.dumps(
                data,
                indent=2
            )
        )


        return out



if __name__=="__main__":

    brain=IntegrationBrain()

    result=brain.save()

    print(
        "Integration context saved:"
    )

    print(result)
