import os


class ModelRouter:

    def route(self, task: str) -> str:
        task = task.lower()

        # ── Coding tasks → qwen3-coder ────────────────────────────────────
        if any(k in task for k in [
            "code", "build", "coder", "write", "generate",
            "implement", "create", "general", "trading", "youtube",
            "script", "function", "class", "flask", "fastapi",
        ]):
            return os.getenv("CODE_MODEL", "qwen/qwen3-coder")

        # ── Debug / repair → deepseek ─────────────────────────────────────
        if any(k in task for k in [
            "debug", "repair", "fix", "error", "traceback", "broken"
        ]):
            return os.getenv("DEBUG_MODEL", "deepseek/deepseek-chat")

        # ── Review / critic → deepseek ────────────────────────────────────
        if any(k in task for k in [
            "review", "critic", "audit", "check", "analyze"
        ]):
            return os.getenv("REVIEW_MODEL", "deepseek/deepseek-chat")

        # ── Planning / intent parsing → deepseek ─────────────────────────
        if any(k in task for k in [
            "plan", "intent", "parse", "think", "reason"
        ]):
            return os.getenv("PLAN_MODEL", "deepseek/deepseek-chat")

        # ── Default: chat → deepseek ──────────────────────────────────────
        return os.getenv("DEFAULT_MODEL", "deepseek/deepseek-chat")


def select_model(task_type: str, complexity: int = 5) -> str:
    """Select model by task type. Coder tasks → qwen, rest → deepseek."""
    coder_tasks = {
        "general_build", "trading_build", "youtube_build",
        "build_general", "build_trading", "build_youtube",
        "code_generation",
    }
    chat_tasks = {
        "chat", "inspect", "scan_project", "show_log",
        "read_file", "analyze",
    }
    repair_tasks = {
        "project_repair", "repair", "continue_project",
        "modify_strategy", "modify", "run_project",
    }

    if task_type in coder_tasks:
        return os.getenv("CODE_MODEL", "qwen/qwen3-coder")
    if task_type in repair_tasks:
        return os.getenv("DEBUG_MODEL", "deepseek/deepseek-chat")
    if task_type in chat_tasks:
        return os.getenv("DEFAULT_MODEL", "deepseek/deepseek-chat")

    # Complexity tiebreaker
    if complexity >= 7:
        return os.getenv("CODE_MODEL", "qwen/qwen3-coder")

    return os.getenv("DEFAULT_MODEL", "deepseek/deepseek-chat")
