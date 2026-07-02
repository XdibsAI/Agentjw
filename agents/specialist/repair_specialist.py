"""
agents/specialist/repair_specialist.py - Deep project repair specialist
"""
import re
import ast
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional
from core.logger import logger, console
from core.models import CodeFile
from rich.panel import Panel
from rich.table import Table


class RepairSpecialist:
    def __init__(self):
        self._llm = None
        self._memory = None

    @property
    def llm(self):
        if self._llm is None:
            from core.llm_client import llm
            self._llm = llm
        return self._llm

    @property
    def memory(self):
        if self._memory is None:
            from memory.memory_store import memory_store
            self._memory = memory_store
        return self._memory

    def _clean(self, code: str) -> str:
        from runtime.ast_validator import ast_validator
        return ast_validator.clean_code(code)

    def _parse_ok(self, code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def diagnose_project(self, project_dir: str) -> Dict:
        path = Path(project_dir)
        if not path.exists():
            return {"error": f"Not found: {project_dir}"}

        console.print(f"[agent.repair]🔍 Diagnosing: {path.name}[/agent.repair]")
        issues = []
        py_files = list(path.rglob("*.py"))

        for py_file in py_files:
            try:
                raw = py_file.read_text(errors='replace')
                cleaned = self._clean(raw)

                if '<think>' in raw:
                    issues.append({"file": py_file.name, "issue": "Contains <think> tags",
                                   "severity": "thinking_tag", "auto_fixable": True})

                if raw.strip().startswith('```'):
                    issues.append({"file": py_file.name, "issue": "Starts with markdown fence",
                                   "severity": "markdown", "auto_fixable": True})

                try:
                    ast.parse(cleaned)
                except SyntaxError as e:
                    issues.append({"file": py_file.name,
                                   "issue": f"SyntaxError line {e.lineno}: {e.msg}",
                                   "severity": "syntax_error", "auto_fixable": False})

                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(py_file)],
                    capture_output=True, text=True, timeout=10,
                )
                if result.returncode != 0:
                    err = result.stderr.strip()[:200]
                    if not any(i["file"] == py_file.name and "syntax" in i["severity"].lower()
                               for i in issues):
                        issues.append({"file": py_file.name, "issue": err,
                                       "severity": "compile_error", "auto_fixable": False})
            except Exception as e:
                issues.append({"file": py_file.name, "issue": str(e),
                                "severity": "read_error", "auto_fixable": False})

        req_file = path / "requirements.txt"
        missing_pkgs = self._check_missing_packages(req_file) if req_file.exists() else []
        health = "healthy" if not issues else ("needs_repair" if len(issues) <= 4 else "critical")

        result = {
            "project_dir": str(path),
            "total_files": len(py_files),
            "issues": issues,
            "missing_packages": missing_pkgs,
            "health": health,
        }
        self._display_diagnosis(result)
        return result

    def auto_repair_project(self, project_id: str, deep: bool = False) -> Dict:
        proj = self.memory.get_project(project_id)
        if not proj:
            return {"error": "Project not found"}

        project_dir = Path(proj["project_dir"])
        if not project_dir.exists():
            return {"error": f"Directory not found: {project_dir}"}

        console.print(Panel(
            f"[cyan]Project:[/cyan] {proj['name']}\n"
            f"[cyan]Path:[/cyan] {project_dir}",
            title="🔧 Auto-Repair", border_style="red"
        ))

        # PASS 1: Auto-clean all files
        console.print("\n[yellow]Pass 1: Cleaning AI artifacts...[/yellow]")
        cleaned_count = 0
        for py_file in project_dir.rglob("*.py"):
            raw = py_file.read_text(errors='replace')
            cleaned = self._clean(raw)
            if cleaned != raw:
                py_file.write_text(cleaned)
                cleaned_count += 1
                console.print(f"  ✓ Cleaned: {py_file.name}")
        if cleaned_count == 0:
            console.print("  [dim]No artifacts found[/dim]")

        # PASS 2: Install missing packages
        req_file = project_dir / "requirements.txt"
        if req_file.exists():
            missing = self._check_missing_packages(req_file)
            real_missing = [p for p in missing if p not in [
                "wallet","trading_bot","scheduler","health_check",
                "config","database","notifier","dashboard","strategy",
                "sniper","jupiter_client","raydium_client","risk_manager"
            ]]
            if real_missing:
                console.print(f"\n[yellow]Pass 2: Installing {real_missing}...[/yellow]")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install"] + real_missing,
                    capture_output=True, timeout=120,
                )

        # PASS 3: Find and AI-repair broken files
        console.print("\n[yellow]Pass 3: AI repair for broken files...[/yellow]")
        repaired = []
        failed = []
        project_context = self._get_context(project_dir)

        for py_file in sorted(project_dir.glob("*.py")):
            raw = py_file.read_text(errors='replace')
            if self._parse_ok(raw):
                continue

            console.print(f"  🔧 Repairing: {py_file.name}")
            try:
                err_info = ""
                try:
                    ast.parse(raw)
                except SyntaxError as e:
                    err_info = f"SyntaxError at line {e.lineno}: {e.msg}"

                fixed = self._ai_repair(py_file.name, raw, err_info, project_context)
                if fixed and self._parse_ok(fixed):
                    py_file.write_text(fixed)
                    self.memory.save_project_file(project_id, py_file.name, fixed)
                    self.memory.log_work(project_id, proj["name"], "repaired", py_file.name)
                    repaired.append(py_file.name)
                    console.print(f"  [green]✓ Fixed: {py_file.name}[/green]")
                else:
                    failed.append(py_file.name)
                    console.print(f"  [red]✗ Failed: {py_file.name}[/red]")
            except Exception as e:
                failed.append(py_file.name)
                console.print(f"  [red]✗ Error: {py_file.name} - {e}[/red]")

        # Final verify
        console.print("\n[cyan]Final verify...[/cyan]")
        ok = 0
        total = 0
        for py_file in sorted(project_dir.glob("*.py")):
            total += 1
            if self._parse_ok(py_file.read_text()):
                console.print(f"  ✓ {py_file.name}")
                ok += 1
            else:
                console.print(f"  [red]✗ {py_file.name}[/red]")

        status = "success" if ok == total else ("partial" if ok > 0 else "failed")
        self.memory.update_project(project_id, status=status)
        self.memory.log_work(project_id, proj["name"], "repair_complete", f"{ok}/{total}")

        console.print(Panel(
            f"[{'green' if status=='success' else 'yellow'}]"
            f"{'✅' if status=='success' else '⚠️'} {ok}/{total} files valid[/]\n"
            f"Repaired: {repaired}\nFailed: {failed}",
            title="🔧 Repair Complete",
            border_style="green" if status == "success" else "yellow"
        ))
        return {"repaired": repaired, "failed": failed, "status": status, "valid": ok, "total": total}

    def continue_project(self, project_id: str, instruction: str = "") -> List[CodeFile]:
        proj = self.memory.get_project(project_id)
        if not proj:
            return []
        project_dir = Path(proj["project_dir"])
        pending = proj.get("tasks_pending", [])
        task = instruction or (pending[0] if pending else "Complete remaining implementation")

        console.print(Panel(
            f"[cyan]Project:[/cyan] {proj['name']}\n"
            f"[cyan]Task:[/cyan] {task[:100]}",
            title="⏩ Continue", border_style="cyan"
        ))

        existing = self._get_context(project_dir)
        prompt = (
            f"Continue this project.\n\n"
            f"PROJECT: {proj['name']}\n"
            f"TASK: {task}\n\n"
            f"EXISTING CODE:\n{existing}\n\n"
            f"Generate needed files. Format:\n"
            f"===FILE: filename.py===\n(code)\n===END===\n\n"
            f"Raw Python only."
        )
        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system="Expert developer. Complete the project task.",
            temperature=0.2, max_tokens=16000,
        )
        new_files = self._parse_blocks(response)
        for cf in new_files:
            out = project_dir / cf.path
            out.parent.mkdir(parents=True, exist_ok=True)
            cleaned = self._clean(cf.content)
            out.write_text(cleaned)
            self.memory.save_project_file(project_id, cf.path, cleaned)

        if instruction and instruction in pending:
            pending.remove(instruction)
            completed = proj.get("tasks_completed", [])
            completed.append(instruction)
            self.memory.update_project(project_id, tasks_pending=pending, tasks_completed=completed)
        self.memory.log_work(project_id, proj["name"], "continued", task[:100])
        return new_files

    def _ai_repair(self, filename: str, code: str, error: str, context: str) -> str:
        prompt = (
            f"Fix ALL errors in this Python file.\n\n"
            f"FILE: {filename}\n"
            f"ERROR: {error}\n\n"
            f"CODE:\n{code}\n\n"
            f"PROJECT CONTEXT:\n{context[:600]}\n\n"
            f"Output ONLY the complete fixed Python code. No markdown."
        )
        try:
            fixed = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system="Expert Python debugger. Fix all errors. Raw code only.",
                temperature=0.1, max_tokens=16000,
            )
            return self._clean(fixed)
        except Exception as e:
            logger.error(f"AI repair failed: {e}")
            return code

    def _check_missing_packages(self, req_file: Path) -> List[str]:
        missing = []
        for line in req_file.read_text().splitlines():
            pkg = line.strip().split(">=")[0].split("==")[0].split("[")[0].strip()
            if pkg and not pkg.startswith("#"):
                try:
                    __import__(pkg.replace("-", "_").replace("-", "_"))
                except ImportError:
                    missing.append(pkg)
        return missing

    def _get_context(self, project_dir: Path) -> str:
        ctx = []
        for f in list(project_dir.glob("*.py"))[:4]:
            try:
                ctx.append(f"=== {f.name} ===\n{f.read_text()[:400]}")
            except Exception:
                pass
        return "\n\n".join(ctx)

    def _parse_blocks(self, text: str) -> List[CodeFile]:
        files = []
        pattern = r'===FILE:\s*(.+?)===\n(.*?)===END==='
        for fname, content in re.findall(pattern, text, re.DOTALL):
            files.append(CodeFile(
                path=fname.strip(),
                content=self._clean(content),
                language="python"
            ))
        if not files:
            cleaned = self._clean(text)
            if 'def ' in cleaned or 'import ' in cleaned:
                files.append(CodeFile(path="patch.py", content=cleaned, language="python"))
        return files

    def _display_diagnosis(self, result: Dict):
        color = {"healthy": "green", "needs_repair": "yellow", "critical": "red"}.get(
            result["health"], "white")
        console.print(f"\n[{color}]🏥 Health: {result['health'].upper()}[/{color}]")
        if result["issues"]:
            table = Table(title="Issues", border_style="red")
            table.add_column("File", style="yellow", width=22)
            table.add_column("Issue", style="red")
            table.add_column("Type", style="white", width=14)
            table.add_column("Auto?", style="green", width=5)
            for issue in result["issues"][:10]:
                table.add_row(
                    issue["file"][:22], issue["issue"][:55],
                    issue["severity"], "✓" if issue.get("auto_fixable") else "✗"
                )
            console.print(table)
        console.print(f"[dim]Scanned {result['total_files']} files[/dim]")


repair_specialist = RepairSpecialist()
