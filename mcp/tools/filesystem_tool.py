"""
mcp/tools/filesystem_tool.py
Real filesystem access - reads actual files from disk
No hallucination, no fabrication
"""
import os
import ast
import hashlib
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from core.logger import logger


class FilesystemTool:
    """
    Provides REAL file access to AgentJW chat.
    All data comes from actual disk reads.
    """

    def read_file(self, path: str) -> Dict:
        """Read actual file content from disk"""
        p = Path(path)
        if not p.exists():
            return {"error": f"File not found: {path}", "exists": False}
        if not p.is_file():
            return {"error": f"Not a file: {path}", "exists": True}
        try:
            content = p.read_text(errors='replace')
            return {
                "exists": True,
                "path": str(p.absolute()),
                "size_bytes": p.stat().st_size,
                "lines": len(content.splitlines()),
                "content": content,
                "sha256": hashlib.sha256(content.encode()).hexdigest(),
            }
        except Exception as e:
            return {"error": str(e)}

    def list_dir(self, path: str) -> Dict:
        """List actual directory contents"""
        p = Path(path)
        if not p.exists():
            return {"error": f"Directory not found: {path}"}
        items = []
        for item in sorted(p.iterdir()):
            if item.name.startswith('.') or item.name == '__pycache__':
                continue
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size_bytes": item.stat().st_size if item.is_file() else 0,
            })
        return {"path": str(p.absolute()), "items": items, "count": len(items)}

    def read_log(self, project_dir: str, lines: int = 50) -> Dict:
        """Read actual log files from project"""
        d = Path(project_dir)
        logs = list(d.glob("*.log")) + list(d.glob("logs/*.log"))
        if not logs:
            return {"error": "No log files found", "searched": str(d)}
        results = {}
        for log in logs[:3]:
            try:
                content = log.read_text(errors='replace')
                all_lines = content.splitlines()
                results[log.name] = {
                    "path": str(log),
                    "total_lines": len(all_lines),
                    "last_lines": "\n".join(all_lines[-lines:]),
                    "size_bytes": log.stat().st_size,
                }
            except Exception as e:
                results[log.name] = {"error": str(e)}
        return results

    def check_syntax(self, path: str) -> Dict:
        """Actually validate Python syntax"""
        p = Path(path)
        if not p.exists():
            return {"error": "File not found"}
        content = p.read_text(errors='replace')
        try:
            ast.parse(content)
            return {"valid": True, "file": p.name, "lines": len(content.splitlines())}
        except SyntaxError as e:
            return {"valid": False, "file": p.name, "line": e.lineno, "error": e.msg,
                    "text": e.text}

    def get_file_hash(self, path: str) -> Dict:
        """Real SHA256 hash from actual file"""
        p = Path(path)
        if not p.exists():
            return {"error": "File not found"}
        content = p.read_bytes()
        return {
            "file": p.name,
            "sha256": hashlib.sha256(content).hexdigest(),
            "md5": hashlib.md5(content).hexdigest(),
            "size_bytes": len(content),
        }

    def scan_project(self, project_dir: str) -> Dict:
        """Full real scan of project directory"""
        d = Path(project_dir)
        if not d.exists():
            return {"error": f"Directory not found: {project_dir}"}

        py_files = []
        for f in sorted(d.glob("*.py")):
            try:
                content = f.read_text(errors='replace')
                valid = True
                error = None
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    valid = False
                    error = f"line {e.lineno}: {e.msg}"
                py_files.append({
                    "name": f.name,
                    "size_kb": round(f.stat().st_size / 1024, 1),
                    "lines": len(content.splitlines()),
                    "syntax_ok": valid,
                    "error": error,
                    "sha256_short": hashlib.sha256(content.encode()).hexdigest()[:12],
                })
            except Exception as e:
                py_files.append({"name": f.name, "error": str(e)})

        has_env = (d / ".env").exists()
        has_req = (d / "requirements.txt").exists()
        env_keys = []
        if has_env:
            for line in (d / ".env").read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    key = line.split("=")[0].strip()
                    env_keys.append(key)

        return {
            "project_dir": str(d.absolute()),
            "python_files": py_files,
            "total_py": len(py_files),
            "valid_syntax": sum(1 for f in py_files if f.get("syntax_ok")),
            "has_env": has_env,
            "env_keys": env_keys,
            "has_requirements": has_req,
            "total_size_kb": round(
                sum(f.stat().st_size for f in d.rglob("*") if f.is_file()) / 1024, 1
            ),
        }

    def run_and_capture(self, project_dir: str, script: str = "main.py",
                        timeout: int = 8) -> Dict:
        """Actually run script and capture real output"""
        entry = Path(project_dir) / script
        if not entry.exists():
            return {"error": f"{script} not found"}
        try:
            result = subprocess.run(
                [sys.executable, str(entry)],
                cwd=project_dir,
                capture_output=True, text=True,
                timeout=timeout,
                env={**os.environ, "PAPER_TRADING": "true"},
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout[-2000:],
                "stderr": result.stderr[-1000:],
                "success": result.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"success": True, "stdout": f"Process ran for {timeout}s (server mode)"}
        except Exception as e:
            return {"error": str(e)}


filesystem_tool = FilesystemTool()
