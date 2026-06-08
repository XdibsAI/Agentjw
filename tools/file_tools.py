"""
tools/file_tools.py - File system utilities
"""
import shutil
import os
from pathlib import Path
from typing import List, Dict, Optional


def read_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_file(path: str | Path, content: str) -> bool:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return True


def list_files(directory: str | Path, pattern: str = "**/*") -> List[str]:
    d = Path(directory)
    if not d.exists():
        return []
    return [str(f.relative_to(d)) for f in d.glob(pattern) if f.is_file()]


def copy_file(src: str | Path, dst: str | Path) -> bool:
    shutil.copy2(str(src), str(dst))
    return True


def delete_file(path: str | Path) -> bool:
    p = Path(path)
    if p.exists():
        p.unlink()
        return True
    return False


def make_dirs(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_directory_tree(path: str | Path, indent: int = 0) -> str:
    p = Path(path)
    tree = ""
    prefix = "  " * indent
    if p.is_file():
        return f"{prefix}📄 {p.name}\n"
    tree += f"{prefix}📁 {p.name}/\n"
    try:
        for item in sorted(p.iterdir()):
            if item.name.startswith(".") or item.name == "__pycache__":
                continue
            tree += get_directory_tree(item, indent + 1)
    except PermissionError:
        pass
    return tree
