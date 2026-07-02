"""
agents/workflow/workflow_engine.py - Main Workflow Engine
Implements the full pipeline:
User → Dialog → Coder → Reviewer → [Fix Loop] → Runner → Memory
"""
import uuid
from typing import Dict, List, Optional, Tuple
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from core.config import config
from core.models import CodeFile, ExecutionResult, TaskStatus
from core.logger import logger, console
from agents.workflow.agent_dialog import agent_dialog
from agents.workflow.agent_runner import agent_runner
from memory.memory_store import memory_store
from tools.project_manager.manager import project_manager


class WorkflowEngine:
    """
    The main pipeline engine that coordinates all agents.

    Flow:
    User Request
        │
        ▼
    AgentDialog (parse intent, clarify if needed)
        │
        ▼
    AgentCoder (generate code)
        │
        ▼
    AgentReviewer (check quality)
        │
        ├── ✅ Approved ──► AgentRunner (execute)
        │                        │
        └── ❌ Issues ──► AgentCoder (fix) ──► Loop (max N times)
                                                    │
                                                    ▼
                                               Memory Update
    """

    MAX_REVIEW_LOOPS = 3
    MAX_REPAIR_LOOPS = 5

    def __init__(self):
        self._coder = None
        self._reviewer = None
        self._repair = None
        self._memory_agent = None
        self._critic = None

    @property
    def coder(self):
        if self._coder is None:
            from agents.coder_agent import coder_agent
            self._coder = coder_agent
        return self._coder

    @property
    def reviewer(self):
        if self._reviewer is None:
            from agents.reviewer_agent import reviewer_agent
            self._reviewer = reviewer_agent
        return self._reviewer

    @property
    def repair(self):
        if self._repair is None:
            from agents.repair_agent import repair_agent
            self._repair = repair_agent
        return self._repair

    @property
    def memory_agent(self):
        if self._memory_agent is None:
            from agents.memory_agent import memory_agent
            self._memory_agent = memory_agent
        return self._memory_agent

    @property
    def critic(self):
        if self._critic is None:
            from agents.critic_agent import critic_agent
            self._critic = critic_agent
        return self._critic

    def run(self, user_request: str, chat_history: List[Dict] = None,
            session_id: str = None, skip_dialog: bool = False) -> Dict:
        """
        Execute full workflow pipeline
        """
        session_id = session_id or str(uuid.uuid4())
        chat_history = chat_history or []

        self._display_workflow_start(user_request)

        # ══════════════════════════════════════════
        # STEP 1: AGENT DIALOG - Parse Intent
        # ══════════════════════════════════════════
        console.print("\n[bold cyan]━━━ STEP 1: AGENT DIALOG ━━━[/bold cyan]")
        if skip_dialog:
            intent = {"intent": "build", "category": "general",
                      "action": user_request, "complexity": "medium",
                      "requirements": [], "needs_clarification": False,
                      "context_summary": user_request}
        else:
            with Progress(SpinnerColumn(), TextColumn("[cyan]Parsing intent..."), TimeElapsedColumn()) as p:
                t = p.add_task("", total=None)
                intent = agent_dialog.parse(user_request, chat_history)

        self._display_intent(intent)

        # Ask for clarification if needed
        if intent.get("needs_clarification") and intent.get("clarification_question"):
            return {
                "status": "needs_clarification",
                "question": intent["clarification_question"],
                "intent": intent,
            }

        # Route based on intent
        intent_type = intent.get("intent", "chat")
        category = intent.get("category", "general")

        # Non-build intents
        if intent_type == "chat":
            return {"status": "chat", "intent": intent}

        if intent_type in ("repair", "analyze", "modify", "continue"):
            return self._handle_project_action(intent, user_request)

        if intent_type == "run":
            return self._handle_run(intent, user_request)

        if intent_type == "mcp_tool":
            return self._handle_mcp(intent, user_request)

        # ══════════════════════════════════════════
        # STEP 2: AGENT CODER - Generate Code
        # ══════════════════════════════════════════
        console.print("\n[bold green]━━━ STEP 2: AGENT CODER ━━━[/bold green]")
        files, plan, pid = self._generate_code(user_request, intent, category)

        if not files:
            return {"status": "failed", "reason": "Code generation failed"}

        # ══════════════════════════════════════════
        # STEP 3: AGENT REVIEWER → FIX LOOP
        # ══════════════════════════════════════════
        console.print("\n[bold blue]━━━ STEP 3: AGENT REVIEWER ━━━[/bold blue]")
        files, review_passed, review = self._review_loop(
            files=files,
            user_request=user_request,
            pid=pid,
        )

        # Write final files to disk
        if plan:
            project_dir = config.PROJECTS_DIR / plan.project_name
        else:
            name = intent.get("action", "project")[:30].replace(" ", "_").lower()
            project_dir = config.PROJECTS_DIR / name
        project_dir.mkdir(parents=True, exist_ok=True)

        for f in files:
            fp = project_dir / f.path
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(f.content)

        if pid:
            project_manager.save_files(pid, files)

        # ══════════════════════════════════════════
        # STEP 4: AGENT RUNNER - Execute
        # ══════════════════════════════════════════
        console.print("\n[bold green]━━━ STEP 4: AGENT RUNNER ━━━[/bold green]")

        # Install deps first
        agent_runner.install_deps(str(project_dir))

        # Run syntax check + test
        exec_result = agent_runner.run(
            str(project_dir),
            entry_point=plan.entry_point if plan else "main.py",
            mode="test",
        )

        # If execution fails, do repair loop
        if not exec_result.success:
            files, exec_result = self._repair_loop(
                files=files,
                exec_result=exec_result,
                user_request=user_request,
                project_dir=project_dir,
                pid=pid,
            )

        # ══════════════════════════════════════════
        # STEP 5: MEMORY UPDATE
        # ══════════════════════════════════════════
        self._update_memory(
            user_request=user_request,
            files=files,
            exec_result=exec_result,
            pid=pid,
            review=review,
        )

        status = "success" if exec_result.success else "partial"
        if pid:
            project_manager.set_status(pid, status)

        self._display_final(project_dir, pid, files, exec_result, review)

        return {
            "status": status,
            "project_id": pid,
            "project_dir": str(project_dir),
            "files": len(files),
            "exec_result": exec_result,
            "review": review,
        }

    # ══════════════════════════════════════════════════════
    # INTERNAL STEPS
    # ══════════════════════════════════════════════════════

    def _generate_code(self, user_request: str, intent: Dict, category: str) -> Tuple:
        """Generate code based on category"""
        pid = None
        plan = None

        if category == "trading" or "solana" in intent.get("action", "").lower():
            from tools.trading.trading_tool import trading_tool
            use_detailed = len(user_request) > 300
            files = (trading_tool.build_trading_project_detailed(user_request)
                     if use_detailed else trading_tool.build_trading_project(user_request))

            name = f"trading_{intent.get('category','bot')}_{uuid.uuid4().hex[:4]}"
            project_dir = str(config.PROJECTS_DIR / name)
            pid = project_manager.register_project(
                name=name, description=user_request,
                project_dir=project_dir, tool_type="trading",
                tasks=["Configure API keys", "Paper trading test", "Enable live trading"],
            )

        elif category == "youtube":
            from tools.youtube.youtube_tool import youtube_tool
            files = youtube_tool.build_youtube_tools(user_request)
            name = f"youtube_{uuid.uuid4().hex[:4]}"
            project_dir = str(config.PROJECTS_DIR / name)
            pid = project_manager.register_project(
                name=name, description=user_request,
                project_dir=project_dir, tool_type="youtube",
            )

        else:
            # General build via planner + coder
            from agents.planner_agent import planner_agent
            with Progress(SpinnerColumn(), TextColumn("[green]Planning..."), TimeElapsedColumn()) as p:
                t = p.add_task("", total=None)
                plan = planner_agent.run(user_request)

            files = self.coder.run({"plan": plan})
            pid = project_manager.register_project(
                name=plan.project_name,
                description=user_request,
                project_dir=str(config.PROJECTS_DIR / plan.project_name),
                tool_type="general",
                tasks=plan.tasks,
            )

        console.print(f"[green]✓ Generated {len(files)} files[/green]")
        return files, plan, pid

    def _review_loop(self, files: List[CodeFile], user_request: str,
                     pid: str = None) -> Tuple[List[CodeFile], bool, Dict]:
        """Review → Fix → Loop until approved or max attempts"""
        review = {}
        for attempt in range(self.MAX_REVIEW_LOOPS):
            console.print(f"[blue]  Review attempt {attempt + 1}/{self.MAX_REVIEW_LOOPS}[/blue]")

            review = self.reviewer.run({
                "files": files,
                "original_request": user_request,
            })

            passed = review.get("passed", False)
            score = review.get("score", 0)
            issues = review.get("issues", [])

            console.print(f"  Score: [cyan]{score}/100[/cyan] | "
                          f"{'[green]✅ APPROVED[/green]' if passed else '[red]❌ ISSUES[/red]'}")

            if issues:
                for issue in issues[:3]:
                    console.print(f"  [red]• {issue}[/red]")

            if passed or score >= 70:
                console.print("[green]✅ Code approved by Reviewer[/green]")
                return files, True, review

            # Fix issues
            if attempt < self.MAX_REVIEW_LOOPS - 1:
                console.print(f"[yellow]  → Sending back to Coder for fixes...[/yellow]")
                files = self._fix_review_issues(files, issues, user_request)
                if pid:
                    project_manager.save_files(pid, files)

        console.print("[yellow]⚠️  Max review loops reached, proceeding...[/yellow]")
        return files, False, review

    def _fix_review_issues(self, files: List[CodeFile],
                            issues: List[str], user_request: str) -> List[CodeFile]:
        """Ask coder to fix review issues"""
        from core.llm_client import llm
        import re

        issues_text = "\n".join(f"- {i}" for i in issues)
        fixed_files = []

        for f in files:
            if not any(issue_hint in f.path for issue_hint in ["main", "strategy", "bot"]):
                fixed_files.append(f)
                continue

            prompt = (
                f"Fix these issues in {f.path}:\n\n"
                f"ISSUES:\n{issues_text}\n\n"
                f"CURRENT CODE:\n{f.content}\n\n"
                f"REQUIREMENT: {user_request}\n\n"
                "Output ONLY the complete fixed code. No markdown."
            )
            try:
                fixed_code = llm.chat(
                    messages=[{"role": "user", "content": prompt}],
                    system="Expert Python developer. Fix all issues precisely.",
                    temperature=0.1, max_tokens=16000,
                )
                fixed_code = re.sub(r'<think>.*?</think>', '', fixed_code, flags=re.DOTALL)
                fixed_code = re.sub(r'^```(?:python|py)?\n?', '', fixed_code, flags=re.MULTILINE)
                fixed_code = re.sub(r'\n?```$', '', fixed_code, flags=re.MULTILINE)
                fixed_files.append(CodeFile(
                    path=f.path, content=fixed_code.strip(),
                    language=f.language, description=f.description
                ))
            except Exception as e:
                logger.error(f"Fix failed for {f.path}: {e}")
                fixed_files.append(f)

        return fixed_files

    def _repair_loop(self, files: List[CodeFile], exec_result: ExecutionResult,
                     user_request: str, project_dir, pid: str = None) -> Tuple:
        """Repair loop after execution failure"""
        for attempt in range(self.MAX_REPAIR_LOOPS):
            console.print(f"\n[red]  🔧 Repair {attempt+1}/{self.MAX_REPAIR_LOOPS}: "
                          f"{exec_result.error_type}[/red]")
            console.print(f"  [dim]{exec_result.stderr[:150]}[/dim]")

            files = self.repair.run({
                "files": files,
                "execution_result": exec_result,
                "original_request": user_request,
                "attempt": attempt + 1,
            })

            # Rewrite
            for f in files:
                fp = project_dir / f.path
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(f.content)

            if pid:
                project_manager.save_files(pid, files)
                project_manager.log_error(pid, exec_result.stderr[:200])

            exec_result = agent_runner.run(str(project_dir), mode="test")

            if exec_result.success:
                console.print(f"[green]  ✅ Fixed on attempt {attempt+1}![/green]")
                return files, exec_result

        console.print("[yellow]  ⚠️ Max repairs reached[/yellow]")
        return files, exec_result

    def _handle_project_action(self, intent: Dict, user_request: str) -> Dict:
        """Handle repair/analyze/modify/continue"""
        target = intent.get("target", "")
        projects = memory_store.list_projects()

        # Find target project
        proj = None
        for p in projects:
            if target and (target in p["id"] or target.lower() in p["name"].lower()):
                proj = p
                break
        if not proj and projects:
            proj = projects[0]  # Default to most recent

        if not proj:
            return {"status": "no_project"}

        intent_type = intent.get("intent")
        if intent_type == "repair":
            from agents.specialist.repair_specialist import repair_specialist
            result = repair_specialist.auto_repair_project(proj["id"], deep=True)
            return {"status": "done", "action": "repair", "result": result}

        elif intent_type == "analyze":
            from tools.trading.trading_tool import trading_tool
            analysis = trading_tool.analyze_strategy(proj["id"], user_request)
            console.print(Panel(analysis, title="📊 Analysis", border_style="cyan"))
            return {"status": "done", "action": "analyze"}

        elif intent_type == "modify":
            from tools.trading.trading_tool import trading_tool
            modified = trading_tool.modify_strategy(proj["id"], user_request)
            return {"status": "done", "action": "modify", "files": len(modified)}

        elif intent_type == "continue":
            from agents.specialist.repair_specialist import repair_specialist
            new_files = repair_specialist.continue_project(proj["id"], user_request)
            return {"status": "done", "action": "continue", "files": len(new_files)}

        return {"status": "unknown_action"}

    def _handle_run(self, intent: Dict, user_request: str) -> Dict:
        """Handle run/start bot request"""
        target = intent.get("target", "")
        projects = memory_store.list_projects()

        proj = None
        for p in projects:
            if target and (target in p["id"] or target.lower() in p["name"].lower()):
                proj = p
                break
        if not proj and projects:
            proj = projects[0]

        if not proj:
            return {"status": "no_project"}

        console.print(f"[cyan]▶️  Running: {proj['name']}[/cyan]")
        result = agent_runner.run(proj["project_dir"], mode="paper")
        return {"status": "running" if result.success else "failed", "project_id": proj["id"]}

    def _handle_mcp(self, intent: Dict, user_request: str) -> Dict:
        """Route to MCP tool"""
        from mcp.mcp_client import mcp_client
        return mcp_client.execute(intent, user_request)

    def _update_memory(self, user_request, files, exec_result, pid, review):
        """Update all memory systems"""
        try:
            self.memory_agent.run({
                "action": "extract_and_store",
                "session_summary": (
                    f"Built project for: {user_request[:200]}. "
                    f"Files: {len(files)}. "
                    f"Success: {exec_result.success}. "
                    f"Score: {review.get('score', 0)}"
                ),
                "success": exec_result.success,
                "project_name": pid or "unknown",
            })
        except Exception as e:
            logger.warning(f"Memory update failed: {e}")

    def _display_workflow_start(self, request: str):
        console.print(Panel(
            f"[bold cyan]⚡ WORKFLOW ENGINE ACTIVATED[/bold cyan]\n\n"
            f"[white]{request[:200]}[/white]\n\n"
            f"[dim]Pipeline: Dialog → Coder → Reviewer → [Fix Loop] → Runner → Memory[/dim]",
            title="🤖 AgentJW Workflow",
            border_style="cyan"
        ))

    def _display_intent(self, intent: Dict):
        table = Table(border_style="dim", show_header=False)
        table.add_column("Key", style="cyan", width=18)
        table.add_column("Value", style="white")
        table.add_row("Intent", intent.get("intent", "?"))
        table.add_row("Category", intent.get("category", "?"))
        table.add_row("Complexity", intent.get("complexity", "?"))
        table.add_row("Action", intent.get("action", "?")[:60])
        if intent.get("requirements"):
            table.add_row("Requirements", str(len(intent["requirements"])) + " detected")
        console.print(table)

    def _display_final(self, project_dir, pid, files, exec_result, review):
        ok = exec_result.success
        color = "green" if ok else "yellow"
        console.print(Panel(
            f"[{color}]{'✅' if ok else '⚠️'} WORKFLOW COMPLETE[/{color}]\n\n"
            f"📁 [cyan]{project_dir}[/cyan]\n"
            f"🆔 ID: [yellow]{pid}[/yellow]\n"
            f"📄 Files: {len(files)}\n"
            f"📊 Review: {review.get('score', 'N/A')}/100\n"
            f"⚡ Exec: {'✅ OK' if ok else '⚠️ Partial'}\n\n"
            f"[dim]repair {pid} | analyze {pid} | continue {pid}[/dim]",
            title="🤖 AgentJW Report",
            border_style=color
        ))


workflow_engine = WorkflowEngine()
