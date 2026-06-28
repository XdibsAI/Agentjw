"""
SiCuan Integration Brain V2

Architecture awareness engine.

READ ONLY.

Detect:
- capabilities
- imports graph
- runtime entry points
- tool visibility
- broken integrations

Output:
sicuan_audit_report/integration_v2.json
"""

import ast
import json
from pathlib import Path
from collections import defaultdict


class IntegrationBrainV2:

    def __init__(self, root="/home/dibs/agentjw"):

        self.root = Path(root)

        self.files = []
        self.import_graph = defaultdict(list)
        self.capabilities = defaultdict(list)
        self.entrypoints = []
        self.gaps = []


    def scan_files(self):

        for path in self.root.rglob("*.py"):

            if "venv" in str(path):
                continue

            try:

                code = path.read_text(
                    errors="ignore"
                )

                tree = ast.parse(code)

                data = {
                    "file": str(path),
                    "functions": [],
                    "classes": [],
                    "imports": []
                }


                for node in ast.walk(tree):

                    if isinstance(
                        node,
                        ast.FunctionDef
                    ):
                        data["functions"].append(
                            node.name
                        )


                    elif isinstance(
                        node,
                        ast.ClassDef
                    ):
                        data["classes"].append(
                            node.name
                        )


                    elif isinstance(
                        node,
                        ast.ImportFrom
                    ):

                        if node.module:

                            data["imports"].append(
                                node.module
                            )


                    elif isinstance(
                        node,
                        ast.Import
                    ):

                        for n in node.names:

                            data["imports"].append(
                                n.name
                            )


                self.files.append(data)


            except Exception:
                continue



    def build_import_graph(self):

        for item in self.files:

            src = Path(
                item["file"]
            ).stem


            for imp in item["imports"]:

                self.import_graph[src].append(
                    imp
                )



    def detect_capabilities(self):

        rules = {

            "trading":[
                "trade",
                "swap",
                "position",
                "pnl",
                "token"
            ],

            "memory":[
                "memory",
                "database",
                "sqlite"
            ],

            "planner":[
                "planner",
                "plan",
                "brain"
            ],

            "executor":[
                "executor",
                "runtime",
                "execute"
            ],

            "mcp":[
                "mcp",
                "openclaw"
            ],

            "video":[
                "video",
                "render",
                "youtube"
            ]
        }


        for item in self.files:

            text = (
                item["file"]
                +
                " "
                +
                " ".join(
                    item["functions"]
                )
            ).lower()


            for cap,keys in rules.items():

                if any(
                    k in text
                    for k in keys
                ):

                    self.capabilities[cap].append(
                        item["file"]
                    )



    def detect_entrypoints(self):

        for item in self.files:

            for fn in item["functions"]:

                if fn in [
                    "main",
                    "run",
                    "execute",
                    "start"
                ]:

                    self.entrypoints.append(
                        {
                            "file":item["file"],
                            "function":fn
                        }
                    )



    def analyze_gaps(self):

        caps=self.capabilities


        checks=[

            (
                "planner",
                "executor",
                "Planner tidak menemukan executor"
            ),

            (
                "trading",
                "memory",
                "Trading belum terhubung memory"
            ),

            (
                "mcp",
                "planner",
                "MCP belum terlihat planner"
            )

        ]


        for a,b,msg in checks:

            if a in caps and b not in caps:

                self.gaps.append(
                    {
                        "severity":"HIGH",
                        "type":"missing_link",
                        "from":a,
                        "to":b,
                        "reason":msg
                    }
                )


        # file terlalu banyak tapi tidak ada entry
        if len(self.files)>100 and not self.entrypoints:

            self.gaps.append(
                {
                    "severity":"MEDIUM",
                    "type":"runtime_unknown",
                    "reason":
                    "Tidak ditemukan entrypoint"
                }
            )



    def export(self):

        self.scan_files()

        self.build_import_graph()

        self.detect_capabilities()

        self.detect_entrypoints()

        self.analyze_gaps()


        result={

            "system":{

                "files":
                len(self.files)

            },


            "capabilities":
            dict(self.capabilities),


            "entrypoints":
            self.entrypoints,


            "import_graph":
            dict(self.import_graph),


            "gaps":
            self.gaps

        }


        out = (
            self.root /
            "sicuan_audit_report" /
            "integration_v2.json"
        )


        out.parent.mkdir(
            exist_ok=True
        )


        out.write_text(
            json.dumps(
                result,
                indent=2
            )
        )


        return out



if __name__=="__main__":

    brain=IntegrationBrainV2()

    print(
        "Integration Brain V2"
    )

    print(
        "Saved:",
        brain.export()
    )
