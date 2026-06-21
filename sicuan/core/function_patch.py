import ast


def replace_function(
    source: str,
    function_name: str,
    new_function: str
):
    """
    Replace satu function berdasarkan AST.
    Function lain tidak disentuh.
    """

    tree = ast.parse(source)

    lines = source.splitlines()

    target = None

    for node in ast.walk(tree):
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            if node.name == function_name:
                target = node
                break

    if not target:
        raise ValueError(
            f"Function {function_name} tidak ditemukan"
        )

    start = target.lineno - 1
    end = target.end_lineno

    new_lines = new_function.splitlines()

    result = (
        lines[:start]
        +
        new_lines
        +
        lines[end:]
    )

    return "\n".join(result)
