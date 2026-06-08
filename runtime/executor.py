"""
runtime/executor.py - Safe sandbox execution engine
"""
import subprocess
import tempfile
import shutil
import os
import time
import sys
from pathlib import Path
from typing import Optional, List, Dict
from core.config import config
from core.models import ExecutionResult
from core.logger import logger


class SandboxExecutor:
    def __init__(self):
        self.sandbox_dir = config.SANDBOX_DIR
        self.sandbox_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = config.EXECUTION_TIMEOUT

    def execute_code(
        self,
        code: str,
        language: str = "python",
        working_dir: Optional[Path] = None,
        files: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """Execute code in a temp sandbox directory"""
        exec_dir = working_dir or (self.sandbox_dir / f"exec_{int(time.time())}")
        exec_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Write additional files
            if files:
                for fname, fcontent in files.items():
                    fpath = exec_dir / fname
                    fpath.parent.mkdir(parents=True, exist_ok=True)
                    fpath.write_text(fcontent)

            # Write main code file
            if language == "python":
                code_file = exec_dir / "main.py"
                code_file.write_text(code)
                cmd = [sys.executable, str(code_file)]
            elif language == "bash":
                code_file = exec_dir / "script.sh"
                code_file.write_text(code)
                cmd = ["bash", str(code_file)]
            else:
                return ExecutionResult(
                    success=False,
                    stderr=f"Unsupported language: {language}",
                    returncode=-1
                )

            start = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(exec_dir),
                env={**os.environ, "PYTHONPATH": str(config.BASE_DIR)},
            )
            elapsed = time.time() - start

            files_created = [str(f.relative_to(exec_dir)) for f in exec_dir.rglob("*") if f.is_file() and f.name != "main.py"]

            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout[:5000],
                stderr=result.stderr[:3000],
                returncode=result.returncode,
                files_created=files_created,
                execution_time=elapsed,
                error_type=self._classify_error(result.stderr) if result.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            logger.warning(f"Execution timed out after {self.timeout}s")
            return ExecutionResult(
                success=False,
                stderr=f"Execution timed out after {self.timeout} seconds",
                returncode=-1,
                error_type="TimeoutError",
            )
        except Exception as e:
            logger.error(f"Executor error: {e}")
            return ExecutionResult(
                success=False,
                stderr=str(e),
                returncode=-1,
                error_type=type(e).__name__,
            )

    def execute_project(self, project_dir: Path, entry_point: str = "main.py") -> ExecutionResult:
        """Run a full project from its directory"""
        entry = project_dir / entry_point
        if not entry.exists():
            return ExecutionResult(
                success=False,
                stderr=f"Entry point not found: {entry_point}",
                returncode=-1,
            )

        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, str(entry)],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(project_dir),
            )
            elapsed = time.time() - start
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout[:5000],
                stderr=result.stderr[:3000],
                returncode=result.returncode,
                execution_time=elapsed,
                error_type=self._classify_error(result.stderr) if result.returncode != 0 else None,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(success=False, stderr="Timeout", returncode=-1, error_type="TimeoutError")

    def _classify_error(self, stderr: str) -> str:
        stderr_lower = stderr.lower()
        if "syntaxerror" in stderr_lower:
            return "SyntaxError"
        elif "importerror" in stderr_lower or "modulenotfounderror" in stderr_lower:
            return "ImportError"
        elif "nameerror" in stderr_lower:
            return "NameError"
        elif "typeerror" in stderr_lower:
            return "TypeError"
        elif "valueerror" in stderr_lower:
            return "ValueError"
        elif "attributeerror" in stderr_lower:
            return "AttributeError"
        elif "indentationerror" in stderr_lower:
            return "IndentationError"
        elif "timeout" in stderr_lower:
            return "TimeoutError"
        else:
            return "RuntimeError"

    def install_requirements(self, requirements: List[str], project_dir: Optional[Path] = None) -> ExecutionResult:
        """Install pip packages for a project"""
        if not requirements:
            return ExecutionResult(success=True, stdout="No requirements to install")

        req_str = " ".join(requirements)
        cmd = [sys.executable, "-m", "pip", "install"] + requirements

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout[-2000:],
                stderr=result.stderr[-1000:],
                returncode=result.returncode,
            )
        except Exception as e:
            return ExecutionResult(success=False, stderr=str(e), returncode=-1)


executor = SandboxExecutor()
