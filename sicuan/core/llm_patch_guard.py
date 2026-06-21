import ast
from pathlib import Path
import shutil


def syntax_ok(code: str) -> bool:
    try:
        ast.parse(code)
        return True
    except Exception:
        return False


def safe_write(path: Path, original: str, new_code: str):

    backup = Path(str(path) + ".llm_backup")

    backup.write_text(original)

    if not syntax_ok(new_code):
        shutil.copy2(
            backup,
            path
        )
        return {
            "ok": False,
            "reason": "syntax gagal, rollback dilakukan"
        }

    if len(new_code) < len(original) * 0.75:
        shutil.copy2(
            backup,
            path
        )
        return {
            "ok": False,
            "reason": (
                "LLM menghapus terlalu banyak kode, "
                "rollback dilakukan"
            )
        }

    path.write_text(new_code)

    return {
        "ok": True,
        "reason": "patch diterapkan"
    }


def changed_functions(before: str, after: str) -> list:
    """
    Bandingkan AST sebelum dan sesudah patch.
    Return nama function yang body-nya berubah.
    """

    def extract_functions(code: str):
        result = {}

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef
                    )
                ):
                    result[node.name] = ast.dump(
                        node,
                        include_attributes=False
                    )

        except Exception:
            pass

        return result


    before_funcs = extract_functions(before)
    after_funcs = extract_functions(after)

    changed = []

    for name, body in after_funcs.items():
        if name not in before_funcs:
            changed.append(name)
            continue

        if before_funcs[name] != body:
            changed.append(name)

    return changed


def extract_functions(code: str):
    result = {}

    try:
        tree = ast.parse(code)

        lines = code.splitlines()

        for node in ast.walk(tree):
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef
                )
            ):
                result[node.name] = "\n".join(
                    lines[
                        node.lineno - 1:
                        node.end_lineno
                    ]
                )

    except Exception:
        pass

    return result



def normalize_code(code: str):
    return "\n".join(
        [
            line.strip()
            for line in code.splitlines()
            if line.strip()
        ]
    )


def changed_functions(before: str, after: str):

    old = extract_functions(before)
    new = extract_functions(after)

    changed = []

    for name in old:

        if name in new:

            old_norm = normalize_code(old[name])
            new_norm = normalize_code(new[name])

            if old_norm != new_norm:
                changed.append(name)

    return changed



def validate_function_patch(
    before: str,
    after: str,
    target_function: str
):

    old = extract_functions(before)
    new = extract_functions(after)


    if target_function not in old:
        return {
            "ok": False,
            "reason": (
                f"Target function {target_function} "
                "tidak ditemukan sebelum patch"
            )
        }


    if target_function not in new:
        return {
            "ok": False,
            "reason": (
                f"Target function {target_function} "
                "hilang setelah patch"
            )
        }


    changed = changed_functions(
        before,
        after
    )


    unexpected = [
        x for x in changed
        if x != target_function
    ]


    if unexpected:
        return {
            "ok": False,
            "reason": (
                "LLM mengubah function lain: "
                + ", ".join(unexpected)
            )
        }


    if target_function not in changed:
        return {
            "ok": False,
            "reason": (
                "Target function tidak berubah"
            )
        }


    return {
        "ok": True,
        "changed": changed
    }
