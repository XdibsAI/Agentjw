import ast
from pathlib import Path


class EndpointRegistry:

    def __init__(self, root):
        self.root = Path(root)


    def scan(self):

        result=[]

        for f in self.root.rglob("*.py"):

            try:
                tree=ast.parse(
                    f.read_text(errors="ignore")
                )

                for n in ast.walk(tree):

                    if isinstance(n,ast.FunctionDef):

                        name=n.name.lower()

                        if any(
                            x in name
                            for x in [
                                "api",
                                "endpoint",
                                "route",
                                "health",
                                "chat",
                                "status"
                            ]
                        ):

                            result.append({
                                "file":str(f),
                                "function":n.name
                            })

            except:
                pass

        return result
