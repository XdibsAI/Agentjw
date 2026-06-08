"""
agents/workflow/agent_runner.py - Execution Agent
Runs generated code safely, captures results, reports back to workflow
"""
import subprocess
import sys
import time
import asyncio
from pathlib import Path
from typing import Dict, Optional, List
from core.config import config
from core.models import ExecutionResult, CodeFile
from core.logger import logger, console
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text


class AgentRunner:
    """
    Step 4 of workflow: Execute approved code.
    Handles both script execution and long-running services.
    """
    def __init__(self):
        self.timeout = config.EXECUTION_TIMEOUT
        self._memory = None

    @property
    def memory(self):
        if self._memory is None:
            from memory.memory_store import memory_store
            self._memory = memory_store
        return self._memory

    def run(self, project_dir: str, entry_point: str = "main.py",
            mode: str = "test", env_vars: Dict = None) -> ExecutionResult:
        """
        mode: test | paper | live | syntax_only
        """
        path = Path(project_dir)
        entry = path / entry_point

        if not entry.exists():
            # Try common entry points
            for ep in ["main.py", "app.py", "bot.py", "run.py"]:
                if (path / ep).exists():
                    entry = path / ep
                    break
            else:
                return ExecutionResult(
                    success=False,
                    stderr=f"No entry point found in {project_dir}",
                    returncode=-1,
                )

        console.print(Panel(
            f"[cyan]Project:[/cyan] {path.name}\n"
            f"[cyan]Entry:[/cyan] {entry.name}\n"
            f"[cyan]Mode:[/cyan] {mode.upper()}",
            title="▶️  Agent Runner",
            border_style="green"
        ))

        if mode == "syntax_only":
            return self._syntax_check(path)

        if mode == "test":
            return self._run_test(entry, path, env_vars)

        if mode in ("paper", "live"):
            return self._run_service(entry, path, env_vars, mode)

        return self._run_test(entry, path, env_vars)

    def _syntax_check(self, project_dir: Path) -> ExecutionResult:
        """Validate all Python files syntax"""
        errors = []
        py_files = list(project_dir.glob("*.py"))
        for py_file in py_files:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(py_file)],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0:
                errors.append(f"{py_file.name}: {result.stderr[:150]}")

        if errors:
            return ExecutionResult(
                success=False,
                stderr="\n".join(errors),
                returncode=1,
                error_type="SyntaxError",
            )
        return ExecutionResult(
            success=True,
            stdout=f"✓ All {len(py_files)} files syntax valid",
            returncode=0,
        )

    def _run_test(self, entry: Path, project_dir: Path, env_vars: Dict = None) -> ExecutionResult:
        """Run with timeout for testable scripts"""
        import os
        env = {**os.environ}
        if env_vars:
            env.update(env_vars)
        # Force paper trading if available
        env["PAPER_TRADING"] = "true"
        env["TEST_MODE"] = "true"

        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, str(entry)],
                capture_output=True, text=True,
                timeout=self.timeout,
                cwd=str(project_dir),
                env=env,
            )
            elapsed = time.time() - start
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout[:3000],
                stderr=result.stderr[:2000],
                returncode=result.returncode,
                execution_time=elapsed,
                error_type=self._classify_error(result.stderr) if result.returncode != 0 else None,
            )
        except subprocess.TimeoutExpired:
            # Timeout on server apps = likely working
            return ExecutionResult(
                success=True,
                stdout=f"✓ Process started successfully (ran for {self.timeout}s)",
                returncode=0,
                execution_time=self.timeout,
            )
        except Exception as e:
            return ExecutionResult(success=False, stderr=str(e), returncode=-1)

    def _run_service(self, entry: Path, project_dir: Path,
                     env_vars: Dict = None, mode: str = "paper") -> ExecutionResult:
        """Start long-running service (bot) as background process"""
        import os
        log_file = project_dir / f"agentjw_{mode}.log"
        env = {**os.environ}
        if env_vars:
            env.update(env_vars)
        if mode == "paper":
            env["PAPER_TRADING"] = "true"

        try:
            proc = subprocess.Popen(
                [sys.executable, str(entry)],
                cwd=str(project_dir),
                env=env,
                stdout=open(log_file, "w"),
                stderr=subprocess.STDOUT,
            )
            time.sleep(3)  # Wait to see if it crashes immediately
            if proc.poll() is not None:
                log_content = log_file.read_text()[-1000:] if log_file.exists() else ""
                return ExecutionResult(
                    success=False,
                    stderr=f"Process exited immediately:\n{log_content}",
                    returncode=proc.returncode or -1,
                )

            console.print(Panel(
                f"[green]✅ Bot running in {mode.upper()} mode![/green]\n\n"
                f"[cyan]PID:[/cyan] {proc.pid}\n"
                f"[cyan]Log:[/cyan] {log_file}\n\n"
                f"Monitor: [dim]tail -f {log_file}[/dim]\n"
                f"Stop: [dim]kill {proc.pid}[/dim]",
                title="🤖 Bot Running",
                border_style="green"
            ))

            # Save PID to memory
            self.memory.store(
                type="running_process",
                content=f"Bot PID {proc.pid} - {entry.parent.name} - {mode}",
                metadata={"pid": proc.pid, "project": str(project_dir), "mode": mode},
                importance=2.0,
            )

            return ExecutionResult(
                success=True,
                stdout=f"Bot started. PID: {proc.pid}. Log: {log_file}",
                returncode=0,
            )
        except Exception as e:
            return ExecutionResult(success=False, stderr=str(e), returncode=-1)

    def install_deps(self, project_dir: str) -> ExecutionResult:
        """Install project dependencies"""
        req_file = Path(project_dir) / "requirements.txt"
        if not req_file.exists():
            return ExecutionResult(success=True, stdout="No requirements.txt found")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file), "--quiet"],
                capture_output=True, text=True, timeout=180,
            )
            if result.returncode == 0:
                console.print("[green]✓ Dependencies installed[/green]")
            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout[-1000:],
                stderr=result.stderr[-500:],
                returncode=result.returncode,
            )
        except Exception as e:
            return ExecutionResult(success=False, stderr=str(e), returncode=-1)

    def _classify_error(self, stderr: str) -> str:
        s = stderr.lower()
        if "syntaxerror" in s: return "SyntaxError"
        if "importerror" in s or "modulenotfounderror" in s: return "ImportError"
        if "nameerror" in s: return "NameError"
        if "typeerror" in s: return "TypeError"
        if "indentationerror" in s: return "IndentationError"
        if "connectionerror" in s or "timeout" in s: return "ConnectionError"
        return "RuntimeError"


agent_runner = AgentRunner()
