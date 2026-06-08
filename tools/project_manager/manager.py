"""
tools/project_manager/manager.py - Persistent project manager
Tracks all projects, tasks, repairs, and work history under AgentJW
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from core.config import config
from core.logger import logger, console
from core.models import CodeFile, TaskStatus
from memory.memory_store import memory_store
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree


class ProjectManager:
    """
    Central manager for all AgentJW projects.
    Maintains full memory of what was built, current state, and pending work.
    """

    def register_project(self, name: str, description: str, project_dir: str,
                          tool_type: str = "general", tasks: List[str] = None,
                          metadata: Dict = None) -> str:
        pid = memory_store.create_project(
            name=name, description=description,
            project_dir=project_dir, tool_type=tool_type,
            tasks=tasks or [], metadata=metadata or {}
        )
        console.print(f"[agent.memory]📋 Project registered: [{pid}] {name}[/agent.memory]")
        return pid

    def complete_task(self, project_id: str, task: str):
        proj = memory_store.get_project(project_id)
        if not proj:
            return
        completed = proj["tasks_completed"]
        pending = proj["tasks_pending"]
        if task in pending:
            pending.remove(task)
        completed.append(f"[{datetime.now().strftime('%H:%M')}] {task}")
        memory_store.update_project(project_id, tasks_completed=completed, tasks_pending=pending)
        memory_store.log_work(project_id, proj["name"], "task_completed", task)

    def add_task(self, project_id: str, task: str):
        proj = memory_store.get_project(project_id)
        if not proj:
            return
        pending = proj["tasks_pending"]
        pending.append(task)
        memory_store.update_project(project_id, tasks_pending=pending)
        memory_store.log_work(project_id, proj["name"], "task_added", task)

    def log_error(self, project_id: str, error: str):
        proj = memory_store.get_project(project_id)
        if not proj:
            return
        errors = proj["errors_history"]
        errors.append(f"[{datetime.now().strftime('%H:%M')}] {error[:200]}")
        if len(errors) > 20:
            errors = errors[-20:]
        memory_store.update_project(project_id, errors_history=errors)

    def set_status(self, project_id: str, status: str, note: str = ""):
        proj = memory_store.get_project(project_id)
        if proj:
            memory_store.update_project(project_id, status=status,
                                         notes=f"{proj.get('notes','')} | {note}" if note else proj.get("notes",""))
            memory_store.log_work(project_id, proj["name"], "status_changed", f"→ {status}: {note}")

    def save_files(self, project_id: str, files: List[CodeFile]):
        proj = memory_store.get_project(project_id)
        if not proj:
            return
        file_paths = []
        for f in files:
            memory_store.save_project_file(project_id, f.path, f.content, f.language)
            file_paths.append(f.path)
        existing = proj.get("files", [])
        all_files = list(set(existing + file_paths))
        memory_store.update_project(project_id, files=all_files)

    def get_project_context(self, project_id: str) -> str:
        """Build full context string for AI agents"""
        proj = memory_store.get_project(project_id)
        if not proj:
            return ""
        files = memory_store.get_project_files(project_id)
        ctx = f"""PROJECT: {proj['name']} [{project_id}]
Description: {proj['description']}
Status: {proj['status']}
Type: {proj['tool_type']}
Directory: {proj['project_dir']}

COMPLETED TASKS:
{chr(10).join('✓ ' + t for t in proj['tasks_completed'][-10:]) or 'None yet'}

PENDING TASKS:
{chr(10).join('• ' + t for t in proj['tasks_pending']) or 'None'}

RECENT ERRORS:
{chr(10).join(proj['errors_history'][-5:]) or 'None'}

FILES IN MEMORY: {', '.join(f['path'] for f in files) or 'None'}
NOTES: {proj.get('notes','') or 'None'}
"""
        return ctx

    def scan_project_dir(self, project_id: str) -> Dict:
        """Scan actual files on disk and sync with memory"""
        proj = memory_store.get_project(project_id)
        if not proj:
            return {}
        project_dir = Path(proj["project_dir"])
        if not project_dir.exists():
            return {"error": f"Directory not found: {project_dir}"}
        py_files = list(project_dir.rglob("*.py"))
        all_files = list(project_dir.rglob("*"))
        result = {
            "total_files": len([f for f in all_files if f.is_file()]),
            "python_files": len(py_files),
            "file_list": [str(f.relative_to(project_dir)) for f in all_files if f.is_file()],
        }
        # Update memory with actual files
        memory_store.update_project(project_id, files=result["file_list"])
        return result

    def display_project(self, project_id: str):
        proj = memory_store.get_project(project_id)
        if not proj:
            console.print(f"[red]Project {project_id} not found[/red]")
            return
        status_color = {"success": "green", "failed": "red", "in_progress": "yellow",
                        "pending": "white", "paused": "blue"}.get(proj["status"], "white")
        panel_content = f"""[cyan]ID:[/cyan] {proj['id']}
[cyan]Type:[/cyan] {proj['tool_type']}
[cyan]Directory:[/cyan] {proj['project_dir']}
[cyan]Status:[/cyan] [{status_color}]{proj['status']}[/{status_color}]
[cyan]Created:[/cyan] {proj['created_at'][:16]}
[cyan]Updated:[/cyan] {proj['updated_at'][:16]}

[green]✓ Completed Tasks ({len(proj['tasks_completed'])}):[/green]
{chr(10).join('  ' + t for t in proj['tasks_completed'][-5:]) or '  None'}

[yellow]• Pending Tasks ({len(proj['tasks_pending'])}):[/yellow]
{chr(10).join('  ' + t for t in proj['tasks_pending']) or '  None'}

[red]⚠ Recent Errors ({len(proj['errors_history'])}):[/red]
{chr(10).join('  ' + e for e in proj['errors_history'][-3:]) or '  None'}

[cyan]Files:[/cyan] {len(proj['files'])} tracked
[cyan]Notes:[/cyan] {proj.get('notes','')[:100] or 'None'}"""

        console.print(Panel(panel_content, title=f"📁 {proj['name']}", border_style="cyan"))

    def display_all_projects(self):
        projects = memory_store.list_projects()
        if not projects:
            console.print("[dim]No projects yet. Use 'build <task>' to create one.[/dim]")
            return
        table = Table(title="📁 AgentJW Managed Projects", border_style="cyan")
        table.add_column("ID", style="dim", width=10)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Status", style="yellow")
        table.add_column("Tasks ✓/⏳", style="green")
        table.add_column("Updated", style="dim")
        for p in projects:
            status_style = {"success": "green", "failed": "red", "in_progress": "yellow"}.get(p["status"], "white")
            table.add_row(
                p["id"],
                p["name"][:25],
                p["tool_type"],
                f"[{status_style}]{p['status']}[/{status_style}]",
                f"{len(p['tasks_completed'])}/{len(p['tasks_pending'])}",
                p["updated_at"][:16],
            )
        console.print(table)

    def display_work_log(self, project_id: str = None, limit: int = 20):
        logs = memory_store.get_work_log(project_id, limit)
        if not logs:
            console.print("[dim]No work log entries.[/dim]")
            return
        table = Table(title="📝 Work Log", border_style="magenta")
        table.add_column("Project", style="cyan", width=20)
        table.add_column("Action", style="green")
        table.add_column("Detail", style="white")
        table.add_column("Time", style="dim")
        for log in logs:
            table.add_row(log["project"][:20], log["action"], log["detail"][:50], log["timestamp"][11:16])
        console.print(table)


project_manager = ProjectManager()
